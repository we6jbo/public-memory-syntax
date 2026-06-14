#!/usr/bin/env python3
"""
Public-safe GitHub rescue version of activerec-pi-hub.py.

This file is safe to put on GitHub because it contains:
- No API keys
- No private notes
- No secret tokens
- No hard dependency on paid LLMs

Private settings should stay here on the Raspberry Pi:
  /opt/activerec/private/config.json

Private Gemini API key, if ever used:
  /opt/activerec/private/gemini_api_key.txt
"""

import json
import os
import subprocess
import time
import traceback
import urllib.parse
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

CONFIG_PATH = Path("/opt/activerec/private/config.json")
DATA_DIR = Path("/home/pi/dayplanner-data")
NOTES_FILE = DATA_DIR / "notes.json"
LOG_FILE = DATA_DIR / "requests.log"
LLM_STATUS_FILE = DATA_DIR / "llm-provider-status.json"

DEFAULT_CONFIG = {
    "bind_host": "127.0.0.1",
    "ports": [8764, 8765],
    "max_message_length": 800,

    "t14_notify_ip": "192.168.5.146",
    "t14_notify_port": 5151,

    "online_llm": {
        "enabled": False,
        "provider": "gemini",
        "model": "gemini-2.0-flash",
        "api_key_file": "/opt/activerec/private/gemini_api_key.txt",
        "no_billing_attached": False,
        "max_monthly_usd": 0
    },

    "local_llm": {
        "enabled": False,
        "llama_cpp_binary": "/opt/JeremiahsLLM/llama-cli",
        "model_path": "/opt/JeremiahsLLM/model.gguf"
    }
}


def now():
    return datetime.now().isoformat(timespec="seconds")


def deep_merge(base, override):
    result = dict(base)

    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def load_config():
    if CONFIG_PATH.exists():
        try:
            private_config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return deep_merge(DEFAULT_CONFIG, private_config)
        except Exception:
            return DEFAULT_CONFIG

    return DEFAULT_CONFIG


CONFIG = load_config()


def ensure_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not NOTES_FILE.exists():
        NOTES_FILE.write_text("[]\n", encoding="utf-8")

    if not LLM_STATUS_FILE.exists():
        write_llm_status("safe startup: online LLM disabled unless private config explicitly enables it")


def write_log(line):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line.rstrip() + "\n")


def preview(text, limit=120):
    return text.replace("\n", " ").replace("\r", " ")[:limit]


def log_request(ip, message):
    write_log(f"{now()} source={ip} preview={preview(message)!r}")


def write_llm_status(summary, extra=None):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    data = {
        "updated": now(),
        "summary": summary,
        "online_llm_enabled": CONFIG.get("online_llm", {}).get("enabled", False),
        "provider": CONFIG.get("online_llm", {}).get("provider", "none"),
        "model": CONFIG.get("online_llm", {}).get("model", "none")
    }

    if extra:
        data.update(extra)

    LLM_STATUS_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def text_response(handler, status, text):
    handler.send_response(status)
    handler.send_header("Content-Type", "text/plain; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write((text.rstrip() + "\n").encode("utf-8"))


def json_response(handler, status, data):
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write((json.dumps(data, indent=2) + "\n").encode("utf-8"))


def run_cmd(cmd, timeout=8):
    try:
        return subprocess.check_output(
            cmd,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout
        ).strip()
    except Exception as e:
        return f"command unavailable or failed: {e}"


def notify_t14(message):
    ip = CONFIG.get("t14_notify_ip", "192.168.5.146")
    port = str(CONFIG.get("t14_notify_port", 5151))

    try:
        subprocess.run(
            ["nc", "-w", "3", ip, port],
            input=message + "\n",
            text=True,
            timeout=5
        )
    except Exception:
        pass


def network_info():
    return (
        "Network status:\n"
        f"Hostname: {run_cmd(['hostname'], 3)}\n"
        f"IP addresses: {run_cmd(['hostname', '-I'], 3)}\n\n"
        f"Route:\n{run_cmd(['ip', 'route'], 3)}"
    )


def pi_health():
    load = os.getloadavg()
    disk = run_cmd(["df", "-h", "/"], 3)
    temp = run_cmd(["vcgencmd", "measure_temp"], 3)

    return (
        "Pi health:\n"
        f"Load average: {load[0]:.2f}, {load[1]:.2f}, {load[2]:.2f}\n"
        f"Temperature: {temp}\n"
        f"Disk:\n{disk}"
    )


def load_notes():
    ensure_data()

    try:
        return json.loads(NOTES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_notes(notes):
    ensure_data()
    NOTES_FILE.write_text(json.dumps(notes[-500:], indent=2) + "\n", encoding="utf-8")


def add_note(text):
    notes = load_notes()
    notes.append({
        "time": now(),
        "text": text[:800]
    })
    save_notes(notes)

    return "Saved note."


def list_notes():
    notes = load_notes()

    if not notes:
        return "No notes yet."

    lines = ["Recent notes:"]

    for i, note in enumerate(notes[-20:], 1):
        lines.append(f"{i}. {note.get('time', '')}: {note.get('text', '')}")

    return "\n".join(lines)


def online_llm_allowed():
    llm = CONFIG.get("online_llm", {})

    if not llm.get("enabled", False):
        return False, "Online LLM is disabled."

    if llm.get("provider") != "gemini":
        return False, "This rescue script only supports provider=gemini."

    if llm.get("max_monthly_usd") != 0:
        return False, "Refusing online LLM because max_monthly_usd is not 0."

    if llm.get("no_billing_attached") is not True:
        return False, "Refusing online LLM because no_billing_attached is not true."

    key_file = Path(llm.get("api_key_file", ""))

    if not key_file.exists():
        return False, f"API key file not found: {key_file}"

    return True, "Online LLM allowed by private local config."


def gemini_reply(message):
    allowed, reason = online_llm_allowed()

    if not allowed:
        write_llm_status("online LLM blocked safely", {"reason": reason})
        notify_t14(f"ActiveRec LLM blocked safely: {reason}")
        return (
            "Online LLM not used.\n"
            f"Reason: {reason}\n"
            "Using rescue planner bot instead."
        )

    llm = CONFIG["online_llm"]
    api_key = Path(llm["api_key_file"]).read_text(encoding="utf-8").strip()
    model = llm.get("model", "gemini-2.0-flash")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        + urllib.parse.quote(model)
        + ":generateContent?key="
        + urllib.parse.quote(api_key)
    )

    prompt = (
        "You are Jeremiah's private local day planner helper. "
        "Be brief, safe, practical, and avoid exposing private details.\n\n"
        f"Message: {message}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        if not text:
            return "Online LLM returned no text."

        write_llm_status("online LLM used successfully")
        return text[:3000]

    except Exception as e:
        write_llm_status("online LLM failed safely", {"error": str(e)})
        return f"Online LLM failed safely: {e}"


def local_llm_reply(message):
    local = CONFIG.get("local_llm", {})

    if not local.get("enabled", False):
        return "Local llama.cpp is disabled."

    binary = Path(local.get("llama_cpp_binary", ""))
    model = Path(local.get("model_path", ""))

    if not binary.exists():
        return f"llama.cpp binary not found: {binary}"

    if not model.exists():
        return f"model not found: {model}"

    prompt = f"Brief day planner reply:\nUser: {message}\nAssistant:"

    try:
        out = subprocess.check_output(
            [str(binary), "-m", str(model), "-p", prompt, "-n", "120"],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=60
        )

        return out.strip()[-3000:]

    except Exception as e:
        return f"Local LLM failed safely: {e}"


def basic_planner(message):
    return (
        "Rescue planner bot:\n"
        f"You said: {message}\n\n"
        "I can save notes, show network info, show Pi health, and optionally use "
        "Gemini only when your private local config explicitly allows it."
    )


def planner(message):
    m = message.strip()
    ml = m.lower()

    if ml in ("hello", "hi", "test"):
        return "OK. activerec GitHub-safe rescue /chat is running."

    if ml in ("help", "commands"):
        return (
            "Commands:\n"
            "- hello\n"
            "- network\n"
            "- pi health\n"
            "- note add TEXT\n"
            "- notes\n"
            "- ai TEXT\n"
            "- local ai TEXT\n"
            "- llm status"
        )

    if "network" in ml or "ip address" in ml:
        return network_info()

    if "pi health" in ml or "cpu" in ml or "memory" in ml or "temperature" in ml:
        return pi_health()

    if ml.startswith("note add "):
        return add_note(m[9:].strip())

    if ml in ("notes", "list notes"):
        return list_notes()

    if ml in ("llm status", "ai status"):
        ensure_data()
        return LLM_STATUS_FILE.read_text(encoding="utf-8")

    if ml.startswith("local ai "):
        return local_llm_reply(m[9:].strip())

    if ml.startswith("ai "):
        ai_text = m[3:].strip()
        reply = gemini_reply(ai_text)

        if "Online LLM not used" in reply or "failed safely" in reply:
            return reply + "\n\n" + basic_planner(ai_text)

        return reply

    return basic_planner(m)


class Handler(BaseHTTPRequestHandler):
    server_version = "ActiveRecGitHubRescue/1.0"

    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)

            if parsed.path == "/health":
                text_response(self, 200, "OK")
                return

            if parsed.path != "/chat":
                text_response(self, 404, "Use /chat?message=hello")
                return

            q = urllib.parse.parse_qs(parsed.query)
            message = q.get("message", [""])[0]
            fmt = q.get("format", ["text"])[0].lower()
            source_ip = self.client_address[0]

            max_len = int(CONFIG.get("max_message_length", 800))

            if len(message) > max_len:
                text_response(self, 413, f"Message too long. Max length is {max_len}.")
                return

            log_request(source_ip, message)

            if not message.strip():
                reply = "Missing message. Example: /chat?message=hello"
            else:
                reply = planner(message)

            if fmt == "json":
                json_response(self, 200, {
                    "ok": True,
                    "time": now(),
                    "source_ip": source_ip,
                    "message_preview": preview(message),
                    "reply": reply
                })
            else:
                text_response(self, 200, reply)

        except Exception as e:
            try:
                write_log(f"{now()} ERROR {e}\n{traceback.format_exc()}")
            except Exception:
                pass

            text_response(self, 500, f"Safe error: {e}")


def serve(port):
    host = CONFIG.get("bind_host", "127.0.0.1")
    httpd = ThreadingHTTPServer((host, int(port)), Handler)

    print(f"Serving on http://{host}:{port}/chat?message=hello", flush=True)

    httpd.serve_forever()


def main():
    ensure_data()
    write_llm_status("startup complete")

    ports = CONFIG.get("ports", [8764])

    for port in ports:
        Thread(target=serve, args=(port,), daemon=True).start()

    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
