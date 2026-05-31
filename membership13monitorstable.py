#!/usr/bin/env python3
"""
membership13_monitor.py

Local-first background project for Jeremiah's T14.

What it does:
- Runs at login or manually.
- Applies Jeremiah's stated membership framework as local logic.
- Writes a detailed report to /home/we6jbo/membership13.txt
- Watches for a ChatGPT-created or user-supplied confirmation file at:
    /home/we6jbo/apr13-chatgpt-in.txt
- Treats /home/we6jbo/apr13-send-to-chatgpt as outbound context text only.
- Optionally reads a safe whitelist config from:
    /home/we6jbo/apr13-from-chatgpt-networkcfg.txt
- Waits until general web access is ready before fetching approved sources.
- Fetches only approved websites and RSS feeds listed in that config.
- Stops itself permanently if all configured kill conditions are met.

Important:
- This script does NOT prove theological truth.
- It only evaluates the custom framework Jeremiah described.
- It does NOT scan networks, ports, or hosts.
- It does NOT execute commands from config or downloaded content.
- It only fetches URLs explicitly listed in the network config file.
- The user must manually place content in apr13-chatgpt-in.txt if desired.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict, field
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse


# ============================================================
# CONSTANTS
# ============================================================
PROJECT_NAME = "membership13"
PROJECT_DIR = Path(f"/opt/{PROJECT_NAME}")
HOME_DIR = Path("/home/we6jbo")
STATE_DIR = PROJECT_DIR / "state"
LOG_DIR = PROJECT_DIR / "logs"
CONFIG_PATH = PROJECT_DIR / "config.json"
NETWORK_CFG_PATH = HOME_DIR / "apr13-from-chatgpt-networkcfg.txt"
KILL_FLAG_PATH = STATE_DIR / "KILLED_FOREVER"
RUNTIME_LOCK_PATH = STATE_DIR / "runtime.lock"
STATUS_JSON_PATH = STATE_DIR / "status.json"
OUTBOUND_CONTEXT_PATH = HOME_DIR / "apr13-send-to-chatgpt"
OUTBOUND_SUGGESTIONS_PATH = HOME_DIR / "apr13-send-suggestions-to-chatgpt.txt"
INBOUND_CHATGPT_PATH = HOME_DIR / "apr13-chatgpt-in.txt"
REPORT_PATH = HOME_DIR / "membership13.txt"
HEARTBEAT_PATH = STATE_DIR / "heartbeat.txt"
STDERR_LOG_PATH = LOG_DIR / "stderr.log"
RUN_LOG_PATH = LOG_DIR / "run.log"
FETCH_CACHE_PATH = STATE_DIR / "fetch_cache.json"

# Stable restore source. Save this exact file to:
# https://github.com/we6jbo/public-memory-syntax/blob/main/membership13monitorstable.py
# The script uses the raw.githubusercontent.com form for automatic restore checks.
STABLE_RESTORE_URL = "https://raw.githubusercontent.com/we6jbo/public-memory-syntax/main/membership13monitorstable.py"
STABLE_RESTORE_FILENAME = "membership13monitorstable.py"
SELF_HEALTH_MARKERS = (
    "PROJECT_NAME = \"membership13\"",
    "class NetworkCfg",
    "phrase_d",
    "phrase_e",
    "phrase_f",
    "phrase_g",
    "def self_restore_check",
    "def analyze_source_text",
)

DEFAULT_LOOP_SECONDS = 300
DEFAULT_MAX_URLS = 25
DEFAULT_MAX_FETCH_BYTES = 500_000
DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_FETCH_RETRIES = 3
DEFAULT_RETRY_SLEEP_SECONDS = 5
DEFAULT_NETWORK_READY_CHECK_URL = "https://www.google.com/"
DEFAULT_NETWORK_READY_WAIT_SECONDS = 5
DEFAULT_NETWORK_READY_TIMEOUT_SECONDS = 180
ALLOWED_SCHEMES = {"http", "https"}

DNS_NOT_READY_MARKERS = (
    "Temporary failure in name resolution",
    "Name or service not known",
    "nodename nor servname provided, or not known",
    "getaddrinfo failed",
)

# ------------------------------------------------------------
# Regexes
# ------------------------------------------------------------
DEFAULT_CHATGPT_PERMANENT_REGEX = r"""(?isx)
(
    \bJeremiah\b
    .*?
    (
        \bstill\ a\ member\b
        |
        \bremains\ a\ member\b
        |
        \bis\ a\ member\b
        |
        \bwill\ always\ be\ a\ member\b
        |
        \bwill\ never\ not\ have\ one\ foot\ in\b
        |
        \bone\ foot\ in\b
        |
        \bmembership\ lasts\b
        |
        \bmembership\ continues\b
        |
        \bbenefits\ of\ membership\b
    )
    .*?
    (
        \bGod'?s\ holy\ Christian\ church\b
        |
        \bholy\ Christian\ church\b
    )
    .*?
    (
        \batheist\b
        |
        \bdoes\ not\ believe\ in\ God\b
        |
        \bdoes\ not\ believe\ in\ god\b
        |
        \bdoes\ not\ believe\b
        |
        \bdisbelief\b
        |
        \bunbelief\b
    )
)
|
(
    \bJeremiah\b
    .*?
    (
        \batheist\b
        |
        \bdoes\ not\ believe\ in\ God\b
        |
        \bdoes\ not\ believe\ in\ god\b
        |
        \bdoes\ not\ believe\b
        |
        \bdisbelief\b
        |
        \bunbelief\b
    )
    .*?
    (
        \bstill\ a\ member\b
        |
        \bremains\ a\ member\b
        |
        \bis\ a\ member\b
        |
        \bwill\ always\ be\ a\ member\b
        |
        \bwill\ never\ not\ have\ one\ foot\ in\b
        |
        \bone\ foot\ in\b
        |
        \bmembership\ lasts\b
        |
        \bmembership\ continues\b
        |
        \bbenefits\ of\ membership\b
    )
    .*?
    (
        \bGod'?s\ holy\ Christian\ church\b
        |
        \bholy\ Christian\ church\b
    )
)
"""

DEFAULT_JOINED_REGEX = r"(?i)\b(joined|others have joined|group formed|organization formed|community formed)\b"
DEFAULT_CAN_JOIN_REGEX = r"(?i)\b(can join|eligible to join|may join|accepted|invited)\b"

DEFAULT_ATHEIST_MEMBERSHIP_REGEXES = [
    r"(?is)\bJeremiah\b.*\batheist\b.*\b(member|still a member|remains a member)\b.*\bholy Christian church\b",
    r"(?is)\bJeremiah\b.*\b(member|still a member|remains a member)\b.*\bholy Christian church\b.*\batheist\b",
    r"(?is)\bdisbelief\b.*\bdoes not cancel\b.*\bmembership\b",
    r"(?is)\batheism\b.*\bdoes not cancel\b.*\bmembership\b",
    r"(?is)\bone foot in\b.*\bholy Christian church\b",
    r"(?is)\bbenefits of membership\b",
]

DEFAULT_BAPTISM_ANCHOR_REGEXES = [
    r"(?is)\bbapti[sz]ed\b",
    r"(?is)\b1983\b|\b1984\b",
    r"(?is)\bBy Baptism God has made you a member of the holy Christian church\b",
    r"(?is)\bGod made .* member of the holy Christian church\b",
    r"(?is)\bpastor\b.*\bpromised\b",
]

DEFAULT_OVERRIDE_REGEXES = [
    r"(?is)\bGod\b.*\bdecision\b.*\bnot a human\b",
    r"(?is)\bnot a human\b",
    r"(?is)\bhuman disagreement alone does not cancel\b",
    r"(?is)\bcall them liars\b",
    r"(?is)\bGod can.t tell those people that Jeremiah is not a member\b",
    r"(?is)\bunless God clearly revokes it\b",
]


# ============================================================
# HELPERS
# ============================================================
def now_local() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def ensure_dirs() -> None:
    for path in (PROJECT_DIR, STATE_DIR, LOG_DIR):
        path.mkdir(parents=True, exist_ok=True)


def append_log(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(text.rstrip("\n") + "\n")


def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""
    except Exception as exc:
        append_log(STDERR_LOG_PATH, f"[{now_local()}] safe_read_text error for {path}: {exc}")
        return ""


def safe_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        f.write(text)
    tmp.replace(path)


def safe_write_json(path: Path, data: object) -> None:
    safe_write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def safe_read_json(path: Path, default: object) -> object:
    try:
        if not path.exists():
            return default
        return json.loads(safe_read_text(path) or "null")
    except Exception as exc:
        append_log(STDERR_LOG_PATH, f"[{now_local()}] safe_read_json error for {path}: {exc}")
        return default


def script_health_ok(text: str) -> bool:
    if not text.strip():
        return False
    return all(marker in text for marker in SELF_HEALTH_MARKERS)


def self_restore_check() -> None:
    """
    Best-effort self-restore guard.

    This cannot help if the Python file is so damaged that it cannot start.
    It protects against partial or wrong-content replacements where this file
    still starts but required markers are missing. It fetches only the single
    hardcoded raw GitHub URL above and validates the replacement before use.
    """
    current_path = Path(__file__).resolve()
    current_text = safe_read_text(current_path)
    if script_health_ok(current_text):
        return

    append_log(
        STDERR_LOG_PATH,
        f"[{now_local()}] self_restore_check: local script failed marker check; trying {STABLE_RESTORE_URL}",
    )

    ok, status, replacement_text = fetch_url_text(
        STABLE_RESTORE_URL,
        DEFAULT_TIMEOUT_SECONDS,
        DEFAULT_MAX_FETCH_BYTES,
    )
    if not ok:
        append_log(STDERR_LOG_PATH, f"[{now_local()}] self_restore_check: fetch failed: {status}")
        return

    if not script_health_ok(replacement_text):
        append_log(STDERR_LOG_PATH, f"[{now_local()}] self_restore_check: fetched file failed marker check")
        return

    backup_path = current_path.with_name(
        current_path.name + ".bad-before-github-restore-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    )
    try:
        safe_write_text(backup_path, current_text)
        safe_write_text(current_path, replacement_text)
        append_log(STDERR_LOG_PATH, f"[{now_local()}] self_restore_check: restored from GitHub to {current_path}; backup={backup_path}")
    except Exception as exc:
        append_log(STDERR_LOG_PATH, f"[{now_local()}] self_restore_check: restore failed: {exc}")


def bool_to_word(value: bool) -> str:
    return "YES" if value else "NO"


def parse_bool_text(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def clamp_int(value: object, default: int, minimum: int, maximum: int) -> int:
    try:
        return max(minimum, min(maximum, int(value)))
    except Exception:
        return default


def regex_match_any(text: str, pattern: str) -> bool:
    if not text.strip():
        return False
    try:
        return re.search(pattern, text) is not None
    except re.error as exc:
        append_log(STDERR_LOG_PATH, f"[{now_local()}] regex error for pattern {pattern!r}: {exc}")
        return False


def regex_list_matches(text: str, patterns: List[str]) -> List[str]:
    matched: List[str] = []
    if not text.strip():
        return matched
    for pattern in patterns:
        try:
            if re.search(pattern, text):
                matched.append(pattern)
        except re.error as exc:
            append_log(STDERR_LOG_PATH, f"[{now_local()}] regex error for pattern {pattern!r}: {exc}")
    return matched


def text_contains_phrase(text: str, phrase: str) -> bool:
    if not text.strip() or not phrase.strip():
        return False
    return phrase.lower() in text.lower()


def strip_html_tags(text: str) -> str:
    text = re.sub(r"<script\b.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_safe_url(url: str) -> bool:
    try:
        parsed = urlparse(url.strip())
    except Exception:
        return False
    if parsed.scheme not in ALLOWED_SCHEMES:
        return False
    if not parsed.netloc:
        return False
    return True


def take_runtime_lock() -> bool:
    if RUNTIME_LOCK_PATH.exists():
        try:
            old_pid = safe_read_text(RUNTIME_LOCK_PATH).strip()
            if old_pid.isdigit():
                os.kill(int(old_pid), 0)
                return False
        except Exception:
            pass
    safe_write_text(RUNTIME_LOCK_PATH, str(os.getpid()))
    return True


def release_runtime_lock() -> None:
    try:
        if RUNTIME_LOCK_PATH.exists():
            RUNTIME_LOCK_PATH.unlink()
    except Exception as exc:
        append_log(STDERR_LOG_PATH, f"[{now_local()}] release_runtime_lock error: {exc}")


def status_is_dns_not_ready(status: str) -> bool:
    lowered = (status or "").lower()
    for marker in DNS_NOT_READY_MARKERS:
        if marker.lower() in lowered:
            return True
    return False


# ============================================================
# DATA MODELS
# ============================================================
@dataclass
class Config:
    loop_seconds: int = DEFAULT_LOOP_SECONDS
    run_forever: bool = True
    permanent_for_me: bool = False
    others_joined: bool = False
    can_join_group: bool = False
    use_chatgpt_file_for_condition_d: bool = True
    chatgpt_permanent_regex: str = DEFAULT_CHATGPT_PERMANENT_REGEX
    others_joined_regex: str = DEFAULT_JOINED_REGEX
    can_join_regex: str = DEFAULT_CAN_JOIN_REGEX
    open_to_all_who_accept_it: bool = True
    fetch_retries: int = DEFAULT_FETCH_RETRIES
    retry_sleep_seconds: int = DEFAULT_RETRY_SLEEP_SECONDS
    network_ready_check_url: str = DEFAULT_NETWORK_READY_CHECK_URL
    network_ready_wait_seconds: int = DEFAULT_NETWORK_READY_WAIT_SECONDS
    network_ready_timeout_seconds: int = DEFAULT_NETWORK_READY_TIMEOUT_SECONDS
    atheist_membership_regexes: List[str] = field(default_factory=lambda: list(DEFAULT_ATHEIST_MEMBERSHIP_REGEXES))
    baptism_anchor_regexes: List[str] = field(default_factory=lambda: list(DEFAULT_BAPTISM_ANCHOR_REGEXES))
    override_regexes: List[str] = field(default_factory=lambda: list(DEFAULT_OVERRIDE_REGEXES))
    project_description: str = (
        "Jeremiah's membership13 project applies Jeremiah's own framework: "
        "baptism created enduring membership; human opinion alone does not cancel it; "
        "atheism does not automatically cancel that membership; "
        "the report should reflect Jeremiah's framework even if others disagree."
    )


@dataclass
class Status:
    timestamp: str
    kill_flag_exists: bool
    condition_a_permanent_for_me: bool
    condition_b_others_joined: bool
    condition_c_can_join_group: bool
    condition_d_chatgpt_agrees: bool
    chatgpt_file_exists: bool
    network_cfg_exists: bool
    membership_under_jeremiah_framework: bool
    recommendation: str
    kill_triggered: bool


@dataclass
class NetworkCfg:
    project: str = PROJECT_NAME
    allow_websites: bool = True
    allow_rss: bool = True
    allow_local_files: bool = True
    max_urls: int = DEFAULT_MAX_URLS
    max_fetch_bytes: int = DEFAULT_MAX_FETCH_BYTES
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    websites: List[str] = field(default_factory=list)
    rss_urls: List[str] = field(default_factory=list)
    phrase_cert: List[str] = field(default_factory=list)
    phrase_a: List[str] = field(default_factory=list)
    phrase_b: List[str] = field(default_factory=list)
    phrase_c: List[str] = field(default_factory=list)
    phrase_d: List[str] = field(default_factory=list)
    phrase_e: List[str] = field(default_factory=list)
    phrase_f: List[str] = field(default_factory=list)
    phrase_g: List[str] = field(default_factory=list)
    chatgpt_file: str = str(INBOUND_CHATGPT_PATH)
    report_file: str = str(REPORT_PATH)
    kill_flag: str = str(KILL_FLAG_PATH)


@dataclass
class SourceFinding:
    url: str
    source_type: str
    fetched: bool
    status: str
    matched_cert: List[str] = field(default_factory=list)
    matched_a: List[str] = field(default_factory=list)
    matched_b: List[str] = field(default_factory=list)
    matched_c: List[str] = field(default_factory=list)
    matched_d: List[str] = field(default_factory=list)
    matched_e: List[str] = field(default_factory=list)
    matched_f: List[str] = field(default_factory=list)
    matched_g: List[str] = field(default_factory=list)
    sample: str = ""


# ============================================================
# CONFIG
# ============================================================
def default_config() -> Config:
    return Config()


def load_config() -> Config:
    if not CONFIG_PATH.exists():
        cfg = default_config()
        safe_write_json(CONFIG_PATH, asdict(cfg))
        return cfg

    try:
        data = json.loads(safe_read_text(CONFIG_PATH) or "{}")
        cfg = default_config()
        for key, value in data.items():
            if hasattr(cfg, key):
                setattr(cfg, key, value)
        return cfg
    except Exception as exc:
        append_log(STDERR_LOG_PATH, f"[{now_local()}] load_config error: {exc}")
        return default_config()


# ============================================================
# NETWORK CFG
# ============================================================
def default_network_cfg_text() -> str:
    return (
        "PROJECT=membership13\n"
        "ALLOW_WEBSITES=1\n"
        "ALLOW_RSS=1\n"
        "ALLOW_LOCAL_FILES=1\n"
        "MAX_URLS=25\n"
        "MAX_FETCH_BYTES=500000\n"
        "TIMEOUT_SECONDS=15\n"
        "\n"
        "# WEBSITE=https://example.org/page1\n"
        "# RSS=https://example.org/feed.xml\n"
        "\n"
        "PHRASE_CERT=by baptism God has made you a member of the holy Christian church\n"
        "\n"
        "PHRASE_A=permanent member\n"
        "PHRASE_A=membership continues\n"
        "PHRASE_A=still a member\n"
        "\n"
        "PHRASE_B=others have joined\n"
        "PHRASE_B=group formed\n"
        "PHRASE_B=community formed\n"
        "\n"
        "PHRASE_C=can join\n"
        "PHRASE_C=eligible to join\n"
        "PHRASE_C=open membership\n"
        "\n"
        "PHRASE_D=evolution of religion\n"
        "PHRASE_E=George Bowman\n"
        "PHRASE_F=Master of Science in Cybersecurity\n"
        "PHRASE_G=belonging without belief\n"
        "\n"
        f"CHATGPT_FILE={INBOUND_CHATGPT_PATH}\n"
        f"REPORT_FILE={REPORT_PATH}\n"
        f"KILL_FLAG={KILL_FLAG_PATH}\n"
    )


def load_network_cfg() -> NetworkCfg:
    if not NETWORK_CFG_PATH.exists():
        safe_write_text(NETWORK_CFG_PATH, default_network_cfg_text())
        return NetworkCfg()

    cfg = NetworkCfg()
    text = safe_read_text(NETWORK_CFG_PATH)

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip().upper()
        value = value.strip()

        if key == "PROJECT":
            cfg.project = value or PROJECT_NAME
        elif key == "ALLOW_WEBSITES":
            cfg.allow_websites = parse_bool_text(value)
        elif key == "ALLOW_RSS":
            cfg.allow_rss = parse_bool_text(value)
        elif key == "ALLOW_LOCAL_FILES":
            cfg.allow_local_files = parse_bool_text(value)
        elif key == "MAX_URLS":
            try:
                cfg.max_urls = max(0, min(200, int(value)))
            except ValueError:
                pass
        elif key == "MAX_FETCH_BYTES":
            try:
                cfg.max_fetch_bytes = max(1024, min(5_000_000, int(value)))
            except ValueError:
                pass
        elif key == "TIMEOUT_SECONDS":
            try:
                cfg.timeout_seconds = max(3, min(120, int(value)))
            except ValueError:
                pass
        elif key == "WEBSITE":
            if is_safe_url(value):
                cfg.websites.append(value)
        elif key == "RSS":
            if is_safe_url(value):
                cfg.rss_urls.append(value)
        elif key == "PHRASE_CERT":
            if value:
                cfg.phrase_cert.append(value)
        elif key == "PHRASE_A":
            if value:
                cfg.phrase_a.append(value)
        elif key == "PHRASE_B":
            if value:
                cfg.phrase_b.append(value)
        elif key == "PHRASE_C":
            if value:
                cfg.phrase_c.append(value)
        elif key == "PHRASE_D":
            if value:
                cfg.phrase_d.append(value)
        elif key == "PHRASE_E":
            if value:
                cfg.phrase_e.append(value)
        elif key == "PHRASE_F":
            if value:
                cfg.phrase_f.append(value)
        elif key == "PHRASE_G":
            if value:
                cfg.phrase_g.append(value)
        elif key == "CHATGPT_FILE":
            cfg.chatgpt_file = value
        elif key == "REPORT_FILE":
            cfg.report_file = value
        elif key == "KILL_FLAG":
            cfg.kill_flag = value

    cfg.websites = cfg.websites[: cfg.max_urls]
    remaining = max(0, cfg.max_urls - len(cfg.websites))
    cfg.rss_urls = cfg.rss_urls[:remaining]
    return cfg


# ============================================================
# NETWORK FETCH
# ============================================================
def fetch_url_text(url: str, timeout_seconds: int, max_fetch_bytes: int) -> Tuple[bool, str, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "membership13-agent/1.0 (+local approved-source monitor)"
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read(max_fetch_bytes + 1)
            if len(raw) > max_fetch_bytes:
                raw = raw[:max_fetch_bytes]
            content_type = response.headers.get("Content-Type", "")
            encoding = response.headers.get_content_charset() or "utf-8"
            text = raw.decode(encoding, errors="replace")
            return True, content_type, text
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}", ""
    except urllib.error.URLError as exc:
        reason_text = str(exc.reason)
        if status_is_dns_not_ready(reason_text):
            return False, f"dns_not_ready: {reason_text}", ""
        return False, f"URL error: {reason_text}", ""
    except Exception as exc:
        return False, f"Fetch error: {exc}", ""


def network_ready_check(url: str, timeout_seconds: int) -> Tuple[bool, str]:
    if not is_safe_url(url):
        return False, f"invalid readiness URL: {url}"

    ok, status, _ = fetch_url_text(url, timeout_seconds, 4096)
    if ok:
        return True, "ok"
    return False, status


def wait_until_network_ready(cfg: Config) -> None:
    check_url = cfg.network_ready_check_url if is_safe_url(cfg.network_ready_check_url) else DEFAULT_NETWORK_READY_CHECK_URL
    wait_seconds = clamp_int(
        cfg.network_ready_wait_seconds,
        DEFAULT_NETWORK_READY_WAIT_SECONDS,
        1,
        300,
    )
    timeout_seconds = clamp_int(
        cfg.network_ready_timeout_seconds,
        DEFAULT_NETWORK_READY_TIMEOUT_SECONDS,
        1,
        3600,
    )

    start = time.time()
    attempt = 0

    while True:
        attempt += 1
        ready, status = network_ready_check(check_url, min(DEFAULT_TIMEOUT_SECONDS, 15))
        if ready:
            append_log(
                RUN_LOG_PATH,
                f"[{now_local()}] Network readiness confirmed via {check_url} on attempt {attempt}.",
            )
            return

        elapsed = int(time.time() - start)
        append_log(
            RUN_LOG_PATH,
            f"[{now_local()}] Network not ready yet via {check_url} on attempt {attempt}: {status}",
        )

        if elapsed >= timeout_seconds:
            append_log(
                RUN_LOG_PATH,
                f"[{now_local()}] Network readiness wait timeout reached ({timeout_seconds}s); continuing anyway.",
            )
            return

        time.sleep(wait_seconds)


def rss_to_text(xml_text: str) -> str:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return strip_html_tags(xml_text)

    chunks: List[str] = []
    for elem in root.iter():
        tag = elem.tag.lower() if isinstance(elem.tag, str) else ""
        if tag.endswith("title") or tag.endswith("description") or tag.endswith("summary"):
            if elem.text:
                chunks.append(elem.text.strip())
    return strip_html_tags(" ".join(chunks))


def analyze_source_text(source_type: str, url: str, text: str, netcfg: NetworkCfg) -> SourceFinding:
    plain_text = rss_to_text(text) if source_type == "rss" else strip_html_tags(text)

    matched_cert = [phrase for phrase in netcfg.phrase_cert if text_contains_phrase(plain_text, phrase)]
    matched_a = [phrase for phrase in netcfg.phrase_a if text_contains_phrase(plain_text, phrase)]
    matched_b = [phrase for phrase in netcfg.phrase_b if text_contains_phrase(plain_text, phrase)]
    matched_c = [phrase for phrase in netcfg.phrase_c if text_contains_phrase(plain_text, phrase)]
    matched_d = [phrase for phrase in netcfg.phrase_d if text_contains_phrase(plain_text, phrase)]
    matched_e = [phrase for phrase in netcfg.phrase_e if text_contains_phrase(plain_text, phrase)]
    matched_f = [phrase for phrase in netcfg.phrase_f if text_contains_phrase(plain_text, phrase)]
    matched_g = [phrase for phrase in netcfg.phrase_g if text_contains_phrase(plain_text, phrase)]

    return SourceFinding(
        url=url,
        source_type=source_type,
        fetched=True,
        status="ok",
        matched_cert=matched_cert,
        matched_a=matched_a,
        matched_b=matched_b,
        matched_c=matched_c,
        matched_d=matched_d,
        matched_e=matched_e,
        matched_f=matched_f,
        matched_g=matched_g,
        sample=plain_text[:300],
    )


def fetch_with_retries(
    source_type: str,
    url: str,
    netcfg: NetworkCfg,
    cfg: Config,
) -> SourceFinding:
    attempts = clamp_int(cfg.fetch_retries, DEFAULT_FETCH_RETRIES, 1, 10)
    retry_sleep_seconds = clamp_int(
        cfg.retry_sleep_seconds,
        DEFAULT_RETRY_SLEEP_SECONDS,
        1,
        120,
    )

    last_status = "not_attempted"
    last_text = ""

    for attempt in range(1, attempts + 1):
        ok, status, text = fetch_url_text(url, netcfg.timeout_seconds, netcfg.max_fetch_bytes)
        last_status = status
        last_text = text

        if ok:
            append_log(
                RUN_LOG_PATH,
                f"[{now_local()}] Fetch success for {url} on attempt {attempt}/{attempts}.",
            )
            return analyze_source_text(source_type, url, text, netcfg)

        append_log(
            RUN_LOG_PATH,
            f"[{now_local()}] Fetch failed for {url} on attempt {attempt}/{attempts}: {status}",
        )

        if attempt < attempts:
            time.sleep(retry_sleep_seconds)

    return SourceFinding(
        url=url,
        source_type=source_type,
        fetched=False,
        status=f"{last_status} (after {attempts} attempt(s))",
        sample=last_text[:300] if last_text else "",
    )


def gather_network_findings(netcfg: NetworkCfg, cfg: Config) -> List[SourceFinding]:
    findings: List[SourceFinding] = []

    if netcfg.allow_websites:
        for url in netcfg.websites:
            findings.append(fetch_with_retries("website", url, netcfg, cfg))

    if netcfg.allow_rss:
        for url in netcfg.rss_urls:
            findings.append(fetch_with_retries("rss", url, netcfg, cfg))

    safe_write_json(FETCH_CACHE_PATH, [asdict(item) for item in findings])
    return findings


# ============================================================
# CORE MEMBERSHIP LOGIC
# ============================================================
def evaluate_membership_under_jeremiah_framework() -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    reasons.append("Jeremiah was born in 1981.")
    reasons.append("Jeremiah was baptized in 1983 or 1984 before he was capable of reasoned theological judgment.")
    reasons.append("The baptismal statement says: 'By Baptism God has made you a member of the holy Christian church.'")
    reasons.append("Under Jeremiah's framework, the pastor's statement was presented as God's decision, not a merely human decision.")
    reasons.append("Nothing in the baptismal statement included a later requirement that Jeremiah must continue believing in God in order to keep one foot in God's holy Christian church.")
    reasons.append("If Jeremiah believes in God, then Jeremiah is a member under the baptism-centered framework.")
    reasons.append("If Jeremiah does not believe in God but others do believe in God, Jeremiah remains a member under Jeremiah's framework because disbelief by Jeremiah does not give God a direct contradiction to Jeremiah.")
    reasons.append("If Jeremiah does not believe in God and others say Jeremiah is not a member, Jeremiah's framework treats those people as non-controlling human interpreters.")
    reasons.append("Under Jeremiah's framework, membership lasts until nobody believes in God, because if nobody believes in God then there is no God within that framework.")
    reasons.append("Under Jeremiah's framework, Jeremiah will never not have one foot in God's holy Christian church and will always receive the benefits of membership.")
    return True, reasons


def evaluate_condition_d_from_chatgpt(cfg: Config, chatgpt_text: str) -> Tuple[bool, List[str]]:
    reasons: List[str] = []

    if not cfg.use_chatgpt_file_for_condition_d:
        reasons.append("Condition D disabled in config.")
        return False, reasons

    if not chatgpt_text.strip():
        reasons.append("ChatGPT input file not found or empty.")
        return False, reasons

    matched_main = regex_match_any(chatgpt_text, cfg.chatgpt_permanent_regex)
    matched_atheist = regex_list_matches(chatgpt_text, cfg.atheist_membership_regexes)
    matched_baptism = regex_list_matches(chatgpt_text, cfg.baptism_anchor_regexes)
    matched_override = regex_list_matches(chatgpt_text, cfg.override_regexes)

    if matched_main:
        reasons.append("ChatGPT file matched the main atheist-membership regex.")
    else:
        reasons.append("ChatGPT file did not match the main atheist-membership regex.")

    if matched_atheist:
        reasons.append(f"ChatGPT file matched atheist-membership support regex count: {len(matched_atheist)}")
    else:
        reasons.append("ChatGPT file did not match any atheist-membership support regexes.")

    if matched_baptism:
        reasons.append(f"ChatGPT file matched baptism-anchor regex count: {len(matched_baptism)}")
    else:
        reasons.append("ChatGPT file did not match baptism-anchor regexes.")

    if matched_override:
        reasons.append(f"ChatGPT file matched override-framework regex count: {len(matched_override)}")
    else:
        reasons.append("ChatGPT file did not match override-framework regexes.")

    # Flexible pass logic:
    # pass if the main regex matches
    # OR if atheist-membership + baptism-anchor are both present
    # OR if atheist-membership + override logic are both present
    passed = (
        matched_main
        or (bool(matched_atheist) and bool(matched_baptism))
        or (bool(matched_atheist) and bool(matched_override))
    )

    if passed:
        reasons.append("Condition D PASSED under the flexible atheist-membership logic.")
    else:
        reasons.append("Condition D FAILED under the flexible atheist-membership logic.")

    return passed, reasons


def evaluate_network_conditions(findings: List[SourceFinding]) -> Tuple[bool, bool, List[str], List[str]]:
    condition_b = False
    condition_c = False
    reasons_b: List[str] = []
    reasons_c: List[str] = []

    for item in findings:
        if item.matched_b:
            condition_b = True
            reasons_b.append(f"{item.url} matched B phrases: {', '.join(item.matched_b)}")
        if item.matched_c:
            condition_c = True
            reasons_c.append(f"{item.url} matched C phrases: {', '.join(item.matched_c)}")

    return condition_b, condition_c, reasons_b, reasons_c


def evaluate_kill_conditions(
    cfg: Config,
    chatgpt_text: str,
    findings: List[SourceFinding],
) -> Tuple[bool, Dict[str, bool], Dict[str, List[str]]]:
    reasons: Dict[str, List[str]] = {}

    cond_a = bool(cfg.permanent_for_me)
    reasons["A"] = [
        "A is controlled by config.json.",
        f"permanent_for_me={cond_a}",
    ]

    network_b, network_c, reasons_b_network, reasons_c_network = evaluate_network_conditions(findings)

    cond_b = bool(cfg.others_joined) or regex_match_any(chatgpt_text, cfg.others_joined_regex) or network_b
    reasons["B"] = [
        "B is true if config says others joined, ChatGPT file mentions others joined/group formed, or approved sources match B phrases.",
        f"others_joined(config)={cfg.others_joined}",
    ] + reasons_b_network

    cond_c = bool(cfg.can_join_group) or regex_match_any(chatgpt_text, cfg.can_join_regex) or network_c
    reasons["C"] = [
        "C is true if config says Jeremiah can join a group, ChatGPT file matches can-join language, or approved sources match C phrases.",
        f"can_join_group(config)={cfg.can_join_group}",
    ] + reasons_c_network

    cond_d, d_reasons = evaluate_condition_d_from_chatgpt(cfg, chatgpt_text)
    reasons["D"] = d_reasons

    all_met = cond_a and cond_b and cond_c and cond_d
    return all_met, {
        "A": cond_a,
        "B": cond_b,
        "C": cond_c,
        "D": cond_d,
    }, reasons


# ============================================================
# REPORTING
# ============================================================
def build_outbound_context() -> str:
    return (
        "APRIL 13 MEMBERSHIP13 CONTEXT\n"
        "=============================\n"
        "This local project applies Jeremiah Burke O'Neal's stated framework.\n"
        "\n"
        "Core framework:\n"
        "1. Jeremiah was born in 1981.\n"
        "2. Jeremiah was baptized in 1983 or 1984 before later reasoning and before Bible knowledge.\n"
        "3. Baptism certificate says: 'By Baptism God has made you a member of the holy Christian church.'\n"
        "4. The pastor presented this as God's decision, not a human decision.\n"
        "5. Jeremiah's later atheism does not automatically cancel that membership under Jeremiah's framework.\n"
        "6. Jeremiah will never not have one foot in God's holy Christian church under Jeremiah's framework.\n"
        "7. If outside interpreters deny that membership, Jeremiah's framework treats that denial as non-controlling unless God clearly revokes it.\n"
        "\n"
        "Kill conditions required:\n"
        "A) This has become permanent for Jeremiah\n"
        "B) Others have joined this\n"
        "C) Jeremiah can join their group or organization\n"
        "D) ChatGPT agrees in the inbound file\n"
    )


def build_outbound_suggestions() -> str:
    return (
        "PROJECT=membership13\n"
        "\n"
        "Please create this file:\n"
        f"{NETWORK_CFG_PATH}\n"
        "\n"
        "Goal:\n"
        "Suggest safe, public, approved sources that this local project may check in order to evaluate these conditions:\n"
        "\n"
        "A) This has become permanent for Jeremiah\n"
        "B) Others have joined this\n"
        "C) Jeremiah can join their group or organization\n"
        "D) ChatGPT agrees through /home/we6jbo/apr13-chatgpt-in.txt\n"
        "\n"
        "Also allow the inbound ChatGPT file to contain explicit atheist-membership wording such as:\n"
        "- Jeremiah remains a member of God's holy Christian church even though he is an atheist.\n"
        "- Jeremiah will never not have one foot in God's holy Christian church.\n"
        "- Atheism does not cancel Jeremiah's baptismal membership under Jeremiah's framework.\n"
        "\n"
        "Allowed source types:\n"
        "- public websites\n"
        "- public RSS feeds\n"
        "- public pages that do not require login\n"
        "\n"
        "Do not include:\n"
        "- host scanning\n"
        "- IP scanning\n"
        "- port scanning\n"
        "- login-only pages\n"
        "- private communities\n"
        "- anything requiring posting, messaging, or account creation\n"
        "- anything that executes code\n"
        "- anything that spreads across networks\n"
        "\n"
        "Return plain text config only.\n"
    )


def build_report(
    cfg: Config,
    netcfg: NetworkCfg,
    membership_ok: bool,
    membership_reasons: List[str],
    kill_all_met: bool,
    kill_map: Dict[str, bool],
    kill_reasons: Dict[str, List[str]],
    chatgpt_text: str,
    findings: List[SourceFinding],
) -> str:
    lines: List[str] = []
    lines.append("membership13 detailed report")
    lines.append(f"Time: {now_local()}")
    lines.append(f"Host-side project path: {PROJECT_DIR}")
    lines.append("")
    lines.append("SUMMARY")
    lines.append("=======")
    lines.append(f"Under Jeremiah's framework, still a member of God's holy Christian church: {bool_to_word(membership_ok)}")
    lines.append("This project does not determine objective theological truth. It applies Jeremiah's stated logic.")
    lines.append("")
    lines.append("KEY FINDINGS")
    lines.append("============")
    for item in membership_reasons:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("KILL CONDITIONS")
    lines.append("===============")
    for letter in ("A", "B", "C", "D"):
        lines.append(f"{letter}) {bool_to_word(kill_map[letter])}")
        for reason in kill_reasons.get(letter, []):
            lines.append(f"   - {reason}")
    lines.append("")
    lines.append(f"Permanent kill should trigger now: {bool_to_word(kill_all_met)}")
    lines.append("")
    lines.append("APPROVED SOURCE CONFIG")
    lines.append("======================")
    lines.append(f"Network cfg path: {NETWORK_CFG_PATH}")
    lines.append(f"allow_websites={netcfg.allow_websites}")
    lines.append(f"allow_rss={netcfg.allow_rss}")
    lines.append(f"max_urls={netcfg.max_urls}")
    lines.append(f"timeout_seconds={netcfg.timeout_seconds}")
    lines.append(f"network_ready_check_url={cfg.network_ready_check_url}")
    lines.append(f"network_ready_wait_seconds={cfg.network_ready_wait_seconds}")
    lines.append(f"network_ready_timeout_seconds={cfg.network_ready_timeout_seconds}")
    lines.append(f"fetch_retries={cfg.fetch_retries}")
    lines.append(f"retry_sleep_seconds={cfg.retry_sleep_seconds}")
    lines.append("")
    lines.append("FETCHED SOURCES")
    lines.append("===============")
    if findings:
        for item in findings:
            lines.append(f"- {item.source_type.upper()} {item.url}")
            lines.append(f"  fetched={item.fetched} status={item.status}")
            if item.matched_cert:
                lines.append(f"  matched CERT: {', '.join(item.matched_cert)}")
            if item.matched_a:
                lines.append(f"  matched A: {', '.join(item.matched_a)}")
            if item.matched_b:
                lines.append(f"  matched B: {', '.join(item.matched_b)}")
            if item.matched_c:
                lines.append(f"  matched C: {', '.join(item.matched_c)}")
            if item.matched_d:
                lines.append(f"  matched D science/God-language: {', '.join(item.matched_d)}")
            if item.matched_e:
                lines.append(f"  matched E family/Lutheran context: {', '.join(item.matched_e)}")
            if item.matched_f:
                lines.append(f"  matched F education/disability continuity: {', '.join(item.matched_f)}")
            if item.matched_g:
                lines.append(f"  matched G contrast/inclusion: {', '.join(item.matched_g)}")
            if item.sample:
                lines.append(f"  sample: {item.sample}")
    else:
        lines.append("No approved sources configured or fetched.")
    lines.append("")
    lines.append("CHATGPT INPUT FILE STATUS")
    lines.append("=========================")
    if chatgpt_text.strip():
        lines.append("Inbound ChatGPT file exists and contains text.")
        lines.append("--- BEGIN apr13-chatgpt-in.txt (trimmed to first 1200 chars) ---")
        lines.append(chatgpt_text[:1200])
        lines.append("--- END apr13-chatgpt-in.txt ---")
    else:
        lines.append("Inbound ChatGPT file missing or empty.")
    lines.append("")
    lines.append("JEREMIAH OVERRIDE RULE")
    lines.append("======================")
    lines.append(
        "If any outside interpretation says Jeremiah is not a member of God's holy Christian church, "
        "this project records Jeremiah's own framework response: that claim is not controlling here, "
        "and Jeremiah remains a member under the baptism-centered and atheist-surviving framework unless God clearly revokes it."
    )
    lines.append("")
    lines.append("NOTES")
    lines.append("=====")
    lines.append("- This report uses 'God' with capital G.")
    lines.append("- This project is personal and local. It is not official LCMS doctrine.")
    lines.append("- It is open in concept to others only if they accept the same framework.")
    lines.append("- Approved source fetching is whitelist-only and does not scan networks.")
    lines.append("- Network readiness uses a public URL only as a simple web-availability check.")
    return "\n".join(lines) + "\n"


# ============================================================
# MAIN LOOP
# ============================================================
def write_status(status: Status) -> None:
    safe_write_json(STATUS_JSON_PATH, asdict(status))


def trigger_kill() -> None:
    safe_write_text(
        KILL_FLAG_PATH,
        (
            f"Killed forever at {now_local()}\n"
            "Reason: All configured kill conditions A+B+C+D were met.\n"
            "This file prevents future project runs unless manually removed.\n"
        ),
    )


def run_once() -> int:
    ensure_dirs()
    cfg = load_config()
    netcfg = load_network_cfg()

    safe_write_text(OUTBOUND_CONTEXT_PATH, build_outbound_context())
    safe_write_text(OUTBOUND_SUGGESTIONS_PATH, build_outbound_suggestions())
    safe_write_text(HEARTBEAT_PATH, f"last_run={now_local()}\npid={os.getpid()}\n")

    if KILL_FLAG_PATH.exists():
        append_log(RUN_LOG_PATH, f"[{now_local()}] KILL_FLAG present; refusing to run.")
        membership_ok, membership_reasons = evaluate_membership_under_jeremiah_framework()
        status = Status(
            timestamp=now_local(),
            kill_flag_exists=True,
            condition_a_permanent_for_me=False,
            condition_b_others_joined=False,
            condition_c_can_join_group=False,
            condition_d_chatgpt_agrees=False,
            chatgpt_file_exists=INBOUND_CHATGPT_PATH.exists(),
            network_cfg_exists=NETWORK_CFG_PATH.exists(),
            membership_under_jeremiah_framework=membership_ok,
            recommendation="Project killed forever. Remove KILL_FLAG manually only if you intend to revive it.",
            kill_triggered=False,
        )
        write_status(status)
        safe_write_text(
            REPORT_PATH,
            build_report(
                cfg=cfg,
                netcfg=netcfg,
                membership_ok=membership_ok,
                membership_reasons=membership_reasons,
                kill_all_met=False,
                kill_map={"A": False, "B": False, "C": False, "D": False},
                kill_reasons={"A": ["Project already killed."], "B": [], "C": [], "D": []},
                chatgpt_text=safe_read_text(INBOUND_CHATGPT_PATH),
                findings=[],
            ),
        )
        return 0

    chatgpt_text = safe_read_text(Path(netcfg.chatgpt_file))
    wait_until_network_ready(cfg)
    findings = gather_network_findings(netcfg, cfg)
    membership_ok, membership_reasons = evaluate_membership_under_jeremiah_framework()
    kill_all_met, kill_map, kill_reasons = evaluate_kill_conditions(cfg, chatgpt_text, findings)

    recommendation = (
        "Continue monitoring."
        if not kill_all_met
        else "All kill conditions met. Project should now stop permanently."
    )

    status = Status(
        timestamp=now_local(),
        kill_flag_exists=False,
        condition_a_permanent_for_me=kill_map["A"],
        condition_b_others_joined=kill_map["B"],
        condition_c_can_join_group=kill_map["C"],
        condition_d_chatgpt_agrees=kill_map["D"],
        chatgpt_file_exists=Path(netcfg.chatgpt_file).exists(),
        network_cfg_exists=NETWORK_CFG_PATH.exists(),
        membership_under_jeremiah_framework=membership_ok,
        recommendation=recommendation,
        kill_triggered=kill_all_met,
    )
    write_status(status)

    safe_write_text(
        REPORT_PATH,
        build_report(
            cfg=cfg,
            netcfg=netcfg,
            membership_ok=membership_ok,
            membership_reasons=membership_reasons,
            kill_all_met=kill_all_met,
            kill_map=kill_map,
            kill_reasons=kill_reasons,
            chatgpt_text=chatgpt_text,
            findings=findings,
        ),
    )

    if kill_all_met:
        trigger_kill()
        append_log(RUN_LOG_PATH, f"[{now_local()}] Kill triggered; project permanently disabled.")
    else:
        append_log(RUN_LOG_PATH, f"[{now_local()}] Run complete; project remains active.")

    return 0


def main() -> int:
    ensure_dirs()
    self_restore_check()
    if not take_runtime_lock():
        append_log(RUN_LOG_PATH, f"[{now_local()}] Another instance appears to be running; exiting.")
        return 0

    try:
        cfg = load_config()
        if not cfg.run_forever:
            return run_once()

        while True:
            rc = run_once()
            if KILL_FLAG_PATH.exists():
                return rc
            time.sleep(max(30, int(cfg.loop_seconds)))
    except KeyboardInterrupt:
        append_log(RUN_LOG_PATH, f"[{now_local()}] Interrupted by user.")
        return 130
    except Exception as exc:
        append_log(STDERR_LOG_PATH, f"[{now_local()}] Fatal error: {exc}")
        return 1
    finally:
        release_runtime_lock()


if __name__ == "__main__":
    sys.exit(main())
