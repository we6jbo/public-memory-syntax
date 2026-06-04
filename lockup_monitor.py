#!/usr/bin/env python3
import base64
import getpass
import http.server
import json
import os
import re
import shutil
import socketserver
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import simpledialog, messagebox
except Exception:
    tk = None
    simpledialog = None
    messagebox = None

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding


KEY_FILE = Path("/home/we6jbo/.chatkey/key.txt")
STATE_DIR = Path("/home/we6jbo/.local/share/lockup-monitor")
STATE_JSON = STATE_DIR / "status.json"
EVENTS_JSONL = STATE_DIR / "events.jsonl"
PORT = 8766

LABEL = "hidden-sensitive"
PBKDF2_ROUNDS_FALLBACK = 600_000

SCAN_INTERVAL_SECONDS = 60
BATTERY_PAUSE_BELOW = 75

MASTER_KEY = None
LAST_STATUS = {
    "time": None,
    "severity": "starting",
    "paused": False,
    "summary": "Monitor starting.",
    "issues": [],
    "battery": {},
    "hardware": {},
    "session": {},
    "reddit_post": "",
}


def b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def b64d(text: str) -> bytes:
    text += "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text.encode())


def derive_key(passphrase: str, salt: bytes, rounds: int) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=rounds,
    )
    return kdf.derive(passphrase.encode("utf-8"))


def ask_passphrase() -> str:
    if tk and simpledialog:
        root = tk.Tk()
        root.withdraw()
        pw = simpledialog.askstring(
            "Lockup Monitor",
            "Enter passphrase for /home/we6jbo/.chatkey/key.txt:",
            show="*",
            parent=root,
        )
        root.destroy()
        if not pw:
            raise SystemExit("No passphrase entered.")
        return pw

    return getpass.getpass("Enter passphrase for /home/we6jbo/.chatkey/key.txt: ")


def load_public_key():
    public_key_file = Path("/home/we6jbo/.chatkey/monitor_public_key.pem")

    if not public_key_file.exists():
        raise SystemExit(
            "Missing public key. Run /home/we6jbo/.chatkey/create-monitor-keypair.py once."
        )

    return serialization.load_pem_public_key(public_key_file.read_bytes())


PUBLIC_KEY_CACHE = None


def encrypt_sensitive(value: str) -> str:
    """
    Encrypt sensitive text with the public key.
    No passphrase is needed for encryption.
    Decryption uses the private key and asks for the decrypt passphrase.
    """
    global PUBLIC_KEY_CACHE

    if PUBLIC_KEY_CACHE is None:
        PUBLIC_KEY_CACHE = load_public_key()

    ciphertext = PUBLIC_KEY_CACHE.encrypt(
        value.encode("utf-8"),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=b"lockup-monitor-sensitive-v2",
        ),
    )

    token = "v2." + b64e(ciphertext)
    return f"[{LABEL}: {token}]"


IPV4_RE = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\b")
MAC_RE = re.compile(r"\b[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5}\b")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


def protect_sensitive(text: str) -> str:
    text = IPV4_RE.sub(lambda m: encrypt_sensitive(m.group(0)), text)
    text = MAC_RE.sub(lambda m: encrypt_sensitive(m.group(0)), text)
    text = EMAIL_RE.sub(lambda m: encrypt_sensitive(m.group(0)), text)
    return text


def run_cmd(cmd, timeout=8) -> str:
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
        return result.stdout.strip()
    except Exception as e:
        return f"command failed: {' '.join(cmd)}: {e}"


def read_file(path: Path) -> str:
    try:
        return path.read_text(errors="replace").strip()
    except Exception:
        return ""


def get_battery_info() -> dict:
    supplies = []
    base = Path("/sys/class/power_supply")

    if not base.exists():
        return {"present": False, "lowest_capacity": None, "items": []}

    for item in base.iterdir():
        if not item.name.startswith("BAT"):
            continue

        capacity_text = read_file(item / "capacity")
        status = read_file(item / "status")
        try:
            capacity = int(capacity_text)
        except Exception:
            capacity = None

        supplies.append({
            "name": item.name,
            "capacity": capacity,
            "status": status or "unknown",
        })

    capacities = [x["capacity"] for x in supplies if isinstance(x["capacity"], int)]
    lowest = min(capacities) if capacities else None

    return {
        "present": bool(supplies),
        "lowest_capacity": lowest,
        "items": supplies,
    }


def should_pause_for_battery(battery: dict) -> bool:
    cap = battery.get("lowest_capacity")
    if cap is None:
        return False
    return cap < BATTERY_PAUSE_BELOW


def get_load() -> dict:
    try:
        load1, load5, load15 = os.getloadavg()
    except Exception:
        load1 = load5 = load15 = 0.0

    cpus = os.cpu_count() or 1
    return {
        "load1": round(load1, 2),
        "load5": round(load5, 2),
        "load15": round(load15, 2),
        "cpus": cpus,
        "load1_per_cpu": round(load1 / cpus, 2),
    }


def get_memory() -> dict:
    data = {}
    for line in read_file(Path("/proc/meminfo")).splitlines():
        parts = line.split()
        if len(parts) >= 2:
            key = parts[0].rstrip(":")
            try:
                data[key] = int(parts[1])
            except Exception:
                pass

    total = data.get("MemTotal")
    available = data.get("MemAvailable")

    if not total or not available:
        return {}

    used_pct = round((1 - available / total) * 100, 1)
    return {
        "total_mb": round(total / 1024),
        "available_mb": round(available / 1024),
        "used_percent": used_pct,
    }


def get_disk() -> dict:
    usage = shutil.disk_usage("/")
    used_pct = round((usage.used / usage.total) * 100, 1)
    return {
        "root_total_gb": round(usage.total / (1024 ** 3), 1),
        "root_free_gb": round(usage.free / (1024 ** 3), 1),
        "root_used_percent": used_pct,
    }


def get_temps() -> dict:
    temps = []
    for zone in Path("/sys/class/thermal").glob("thermal_zone*"):
        temp_text = read_file(zone / "temp")
        type_text = read_file(zone / "type")
        try:
            c = int(temp_text) / 1000.0
            temps.append({"sensor": type_text or zone.name, "celsius": round(c, 1)})
        except Exception:
            pass

    hottest = max([x["celsius"] for x in temps], default=None)
    return {"hottest_celsius": hottest, "items": temps[:20]}


def get_hardware_snapshot() -> dict:
    dmesg_recent = run_cmd(["bash", "-lc", "dmesg --ctime --level=err,warn 2>/dev/null | tail -40"], timeout=8)
    journal_recent = run_cmd(["bash", "-lc", "journalctl -p warning..alert --since '30 minutes ago' --no-pager 2>/dev/null | tail -60"], timeout=10)

    smart = "smartctl not installed or not readable without sudo"
    if shutil.which("smartctl"):
        smart = run_cmd(["bash", "-lc", "smartctl -H /dev/nvme0n1 2>/dev/null || smartctl -H /dev/sda 2>/dev/null || true"], timeout=10)

    return {
        "load": get_load(),
        "memory": get_memory(),
        "disk": get_disk(),
        "temps": get_temps(),
        "dmesg_recent": protect_sensitive(dmesg_recent),
        "journal_recent": protect_sensitive(journal_recent),
        "smart_health": protect_sensitive(smart),
    }


def get_session_snapshot() -> dict:
    who = run_cmd(["who"], timeout=5)
    users = run_cmd(["users"], timeout=5)
    uptime = run_cmd(["uptime"], timeout=5)
    top_cpu = run_cmd(["bash", "-lc", "ps -u we6jbo -o pid,comm,%cpu,%mem --sort=-%cpu | head -12"], timeout=5)
    top_mem = run_cmd(["bash", "-lc", "ps -u we6jbo -o pid,comm,%cpu,%mem --sort=-%mem | head -12"], timeout=5)
    chrome_count = run_cmd(["bash", "-lc", "pgrep -u we6jbo -fa 'chrome|chromium' | wc -l"], timeout=5)

    return {
        "who": protect_sensitive(who),
        "users": protect_sensitive(users),
        "uptime": protect_sensitive(uptime),
        "top_cpu": protect_sensitive(top_cpu),
        "top_mem": protect_sensitive(top_mem),
        "chrome_process_count": chrome_count.strip(),
    }


def analyze(battery: dict, hardware: dict, session: dict) -> tuple:
    issues = []
    severity = "ok"

    load = hardware.get("load", {})
    mem = hardware.get("memory", {})
    disk = hardware.get("disk", {})
    temps = hardware.get("temps", {})

    if load.get("load1_per_cpu", 0) >= 2.0:
        issues.append("CPU load is very high compared with CPU count.")
        severity = "warning"

    if mem.get("used_percent", 0) >= 90:
        issues.append("Memory use is above 90%. Lockups can happen when RAM is exhausted.")
        severity = "warning"

    if disk.get("root_used_percent", 0) >= 92:
        issues.append("Root disk is above 92% full. Low disk space can cause system problems.")
        severity = "warning"

    hottest = temps.get("hottest_celsius")
    if hottest is not None and hottest >= 85:
        issues.append(f"Temperature is high: {hottest} C.")
        severity = "critical"

    dmesg = hardware.get("dmesg_recent", "").lower()
    journal = hardware.get("journal_recent", "").lower()

    scary_words = ["i/o error", "nvme", "oom", "thermal", "gpu hang", "watchdog", "reset", "segfault"]
    if any(word in dmesg for word in scary_words):
        issues.append("Recent dmesg warnings/errors include lockup-related words.")
        if severity == "ok":
            severity = "warning"

    if "out of memory" in journal or "oom" in journal:
        issues.append("Journal suggests an out-of-memory event.")
        severity = "critical"

    if not issues:
        issues.append("No obvious hardware/session problem detected in this scan.")

    return severity, issues


def make_reddit_post(status: dict) -> str:
    title = "Linux laptop sometimes locks up. Here is my local monitor report."

    lines = []
    lines.append(f"**Title:** {title}")
    lines.append("")
    lines.append("**System behavior:**")
    lines.append("My computer sometimes locks up. I am trying to diagnose whether it is CPU load, memory pressure, disk, thermal, browser/session activity, or kernel/system warnings.")
    lines.append("")
    lines.append("**Monitor summary:**")
    lines.append(f"- Time: {status.get('time')}")
    lines.append(f"- Severity: {status.get('severity')}")
    lines.append(f"- Paused because battery below 75%: {status.get('paused')}")
    lines.append("")
    lines.append("**Issues detected:**")
    for issue in status.get("issues", []):
        lines.append(f"- {issue}")
    lines.append("")
    lines.append("**Battery:**")
    lines.append("```")
    lines.append(json.dumps(status.get("battery", {}), indent=2))
    lines.append("```")
    lines.append("")
    lines.append("**Hardware snapshot:**")
    lines.append("```")
    hw = status.get("hardware", {}).copy()
    # keep post shorter
    for key in ["dmesg_recent", "journal_recent"]:
        if key in hw and len(hw[key]) > 3000:
            hw[key] = hw[key][-3000:]
    lines.append(json.dumps(hw, indent=2))
    lines.append("```")
    lines.append("")
    lines.append("**Session snapshot:**")
    lines.append("```")
    lines.append(json.dumps(status.get("session", {}), indent=2))
    lines.append("```")
    lines.append("")
    lines.append("Sensitive values like IP addresses, MAC addresses, and email addresses were encrypted locally before this post was generated.")
    return "\n".join(lines)


def write_status(status: dict):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    status["reddit_post"] = make_reddit_post(status)
    STATE_JSON.write_text(json.dumps(status, indent=2), encoding="utf-8")
    with EVENTS_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(status) + "\n")


def monitor_loop():
    global LAST_STATUS

    while True:
        now = datetime.now().isoformat(timespec="seconds")
        battery = get_battery_info()
        paused = should_pause_for_battery(battery)

        if paused:
            status = {
                "time": now,
                "severity": "paused",
                "paused": True,
                "summary": f"Monitoring paused because battery is below {BATTERY_PAUSE_BELOW}%.",
                "issues": [f"Battery below {BATTERY_PAUSE_BELOW}%. Hardware scan skipped to save power."],
                "battery": battery,
                "hardware": {},
                "session": get_session_snapshot(),
            }
        else:
            hardware = get_hardware_snapshot()
            session = get_session_snapshot()
            severity, issues = analyze(battery, hardware, session)
            status = {
                "time": now,
                "severity": severity,
                "paused": False,
                "summary": "Hardware and session scan complete.",
                "issues": issues,
                "battery": battery,
                "hardware": hardware,
                "session": session,
            }

        LAST_STATUS = status
        write_status(status)
        time.sleep(SCAN_INTERVAL_SECONDS)


class Handler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, obj):
        body = json.dumps(obj, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, text):
        body = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/status"):
            self._send_json(LAST_STATUS)
        elif self.path.startswith("/reddit"):
            self._send_text(LAST_STATUS.get("reddit_post", "No post ready yet."))
        else:
            self._send_json({
                "ok": True,
                "service": "lockup-monitor",
                "endpoints": ["/status", "/reddit"],
            })

    def log_message(self, fmt, *args):
        return


def run_server():
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Handler) as httpd:
        httpd.serve_forever()


def main():
    global MASTER_KEY

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    # Public-key mode. Load public key only. No startup passphrase.
    load_public_key()
    if tk and messagebox:
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo(
                "Lockup Monitor",
                f"Monitor started without startup passphrase.\nChrome extension can read http://127.0.0.1:{PORT}/status"
            )
            root.destroy()
        except Exception:
            pass

    t1 = threading.Thread(target=monitor_loop, daemon=True)
    t1.start()

    run_server()


if __name__ == "__main__":
    main()
