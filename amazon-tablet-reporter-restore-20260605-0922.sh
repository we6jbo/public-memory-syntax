#!/data/data/com.termux/files/usr/bin/sh
# amazon-tablet-reporter-restore-20260605-0922.sh
# Reboot-hardened restore/repair script for Amazon tablet Termux:Boot reporter.
# Updated restore generation for TAG: #D3FFC1E
#
# Purpose:
# - Self-update from GitHub raw source.
# - Restore ~/.termux/boot/amazon-tablet-reporter.sh.
# - Write a Python reporter that posts directly to T14 Tk monitor port 8767.
# - Also report stages to T14 port 3329 when available.
# - Scan /storage/emulated/0/movies for MP4 files.
# - Do not send plain MP4 filenames. Use HMAC tags only.
# - Survive tablet reboot through Termux:Boot.

T14_HOST="${T14_HOST:-192.168.8.110}"
TK_PORT="${TK_PORT:-8767}"
STAGE_PORT="${STAGE_PORT:-3329}"
TAG="#D3FFC1E"

REMOTE_URL="https://raw.githubusercontent.com/we6jbo/public-memory-syntax/main/amazon-tablet-reporter-restore-20260605-0922.sh"

TARGET="$HOME/.termux/boot/amazon-tablet-reporter.sh"
BOOT_RESTORE="$HOME/.termux/boot/00-restore-amazon-tablet-reporter.sh"
BASE="$HOME/.local/share/amazon-tablet-monitor"
RESTORE="$BASE/amazon-tablet-reporter-restore-20260605-0922.sh"
REPORTER="$BASE/amazon_tablet_reboot_hardened_reporter.py"
FIXFILE="$BASE/tablet-fixes.env"
LOG="$BASE/restore.log"

mkdir -p "$BASE" "$HOME/.termux/boot"

stage() {
    NAME="$1"
    DETAILS="$2"
    NOW="$(date '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo unknown-time)"
    JSON="{\"tag\":\"$TAG\",\"device\":\"amazon-tablet\",\"time\":\"$NOW\",\"stage\":\"$NAME\",\"details\":\"$DETAILS\"}"
    echo "$JSON" >> "$LOG"
    echo "$JSON"

    if command -v curl >/dev/null 2>&1; then
        curl -sS -m 8 \
            -H "Content-Type: application/json" \
            -X POST \
            -d "$JSON" \
            "http://$T14_HOST:$STAGE_PORT/stage" >/dev/null 2>&1 || true
    fi
}

self_update_from_github() {
    MODE="${1:-}"
    TMP="$BASE/remote-restore.tmp"

    if [ "$MODE" = "--no-remote" ]; then
        return 0
    fi

    if ! command -v curl >/dev/null 2>&1; then
        stage "github-self-update-skip" "curl missing; cannot self-update from GitHub."
        return 0
    fi

    if curl -fsSL -m 15 "$REMOTE_URL" -o "$TMP"; then
        if grep -q "#D3FFC1E" "$TMP" && grep -q "amazon_tablet_reboot_hardened_reporter.py" "$TMP"; then
            if [ ! -f "$RESTORE" ] || ! cmp -s "$TMP" "$RESTORE"; then
                cp "$TMP" "$RESTORE"
                chmod +x "$RESTORE"
                stage "github-self-update-ok" "Downloaded newer restore script from GitHub. Re-running updated copy."
                exec "$RESTORE" --ensure --no-remote
            else
                stage "github-self-update-current" "Local restore script already matches GitHub."
            fi
        else
            stage "github-self-update-invalid" "GitHub file missing expected markers; ignoring."
        fi
    else
        stage "github-self-update-failed" "Could not download GitHub restore script; using local embedded version."
    fi
}

write_fixfile() {
    if [ ! -f "$FIXFILE" ]; then
        cat > "$FIXFILE" <<EOF
# Tablet monitor config
# TAG: #D3FFC1E

T14_HOST=192.168.8.110
TK_PORT=8767
STAGE_PORT=3329
INTERVAL_SECONDS=300

# Real folder Jeremiah reported.
TABLET_MOVIES_DIR=/storage/emulated/0/movies

# Fallbacks. Reporter chooses readable directory with most MP4s.
MP4_DIR_CANDIDATES=/storage/emulated/0/movies|/sdcard/movies|/storage/emulated/0/Movies|/sdcard/Movies|/storage/emulated/0/Download|/sdcard/Download|/storage/emulated/0/DCIM|/sdcard/DCIM|/storage/emulated/0/Syncthing|/sdcard/Syncthing

# Optional Syncthing API key. Leave blank unless configured.
SYNCTHING_API_KEY=

# Privacy key. Plain MP4 filenames are not sent.
CIPHER_TEXT=j2o4QdbHhEXHsmr5f0xnVKxNI3F2mfUCmxFY8ZBr5ZBOinuyN4uc1TRxrb5jNTW
EOF
        stage "fixfile-created" "Created $FIXFILE with /storage/emulated/0/movies."
    else
        if grep -q '^TABLET_MOVIES_DIR=' "$FIXFILE"; then
            sed -i 's|^TABLET_MOVIES_DIR=.*|TABLET_MOVIES_DIR=/storage/emulated/0/movies|' "$FIXFILE"
        else
            echo "TABLET_MOVIES_DIR=/storage/emulated/0/movies" >> "$FIXFILE"
        fi
        stage "fixfile-updated" "Updated TABLET_MOVIES_DIR=/storage/emulated/0/movies in $FIXFILE."
    fi
}

write_reporter() {
cat > "$REPORTER" <<'PY'
#!/usr/bin/env python3
# amazon_tablet_reboot_hardened_reporter.py
# TAG: #D3FFC1E

import json
import time
import hmac
import socket
import hashlib
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen

TAG = "#D3FFC1E"
BASE = Path.home() / ".local/share/amazon-tablet-monitor"
FIXFILE = BASE / "tablet-fixes.env"
LOG = BASE / "amazon-tablet-reboot-hardened-reporter.log"

def log(msg):
    BASE.mkdir(parents=True, exist_ok=True)
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def load_cfg():
    cfg = {
        "T14_HOST": "192.168.8.110",
        "TK_PORT": "8767",
        "STAGE_PORT": "3329",
        "INTERVAL_SECONDS": "300",
        "TABLET_MOVIES_DIR": "/storage/emulated/0/movies",
        "MP4_DIR_CANDIDATES": "/storage/emulated/0/movies|/sdcard/movies|/storage/emulated/0/Movies|/sdcard/Movies|/storage/emulated/0/Download|/sdcard/Download|/storage/emulated/0/DCIM|/sdcard/DCIM|/storage/emulated/0/Syncthing|/sdcard/Syncthing",
        "SYNCTHING_API_KEY": "",
        "CIPHER_TEXT": "j2o4QdbHhEXHsmr5f0xnVKxNI3F2mfUCmxFY8ZBr5ZBOinuyN4uc1TRxrb5jNTW",
    }

    if FIXFILE.exists():
        for line in FIXFILE.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg

def run_cmd(cmd, timeout=8):
    try:
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
        return {
            "ok": r.returncode == 0,
            "returncode": r.returncode,
            "stdout": r.stdout.strip(),
            "stderr": r.stderr.strip(),
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "stdout": "", "stderr": ""}

def post_json(host, port, path, payload, timeout=10):
    data = json.dumps(payload).encode("utf-8")
    req = Request(
        f"http://{host}:{port}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")

def send_stage(cfg, stage, details, extra=None):
    payload = {
        "tag": TAG,
        "device": "amazon-tablet",
        "hostname": socket.gethostname() or "amazon-tablet",
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "stage": stage,
        "details": details,
    }
    if extra is not None:
        payload["extra"] = extra

    log("STAGE " + json.dumps(payload))

    try:
        post_json(cfg["T14_HOST"], int(cfg["STAGE_PORT"]), "/stage", payload, timeout=6)
    except Exception as e:
        log(f"stage-to-3329-failed: {e}")

def get_battery():
    r = run_cmd(["timeout", "5", "termux-battery-status"], timeout=7)
    if r.get("ok") and r.get("stdout"):
        try:
            data = json.loads(r["stdout"])
            return {
                "ok": data.get("percentage") is not None,
                "method": "termux-api",
                "percent": data.get("percentage"),
                "status": data.get("status"),
                "plugged": data.get("plugged"),
            }
        except Exception as e:
            return {
                "ok": False,
                "method": "termux-api-parse-failed",
                "percent": None,
                "error": str(e),
            }

    return {
        "ok": False,
        "method": "unknown-fire-os",
        "percent": None,
        "status": None,
        "note": "Battery unavailable. Fire OS or Termux:API is blocking it.",
    }

def get_ssid():
    r = run_cmd(["timeout", "5", "termux-wifi-connectioninfo"], timeout=7)
    if r.get("ok") and r.get("stdout"):
        try:
            data = json.loads(r["stdout"])
            s = str(data.get("ssid", "")).strip().strip('"')
            if s and s not in ["<unknown ssid>", "unknown", "unknown ssid"]:
                return {"ok": True, "ssid": s, "method": "termux-wifi-connectioninfo"}
            return {"ok": False, "ssid": s or "<unknown ssid>", "method": "termux-wifi-connectioninfo"}
        except Exception as e:
            return {"ok": False, "ssid": "<parse-failed>", "method": "termux-wifi-connectioninfo", "error": str(e)}

    return {"ok": False, "ssid": "unknown-but-tablet-can-report", "method": "unavailable"}

def hmac_name(key, name):
    return hmac.new(key.encode("utf-8"), name.encode("utf-8"), hashlib.sha256).hexdigest()

def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def scan_dir(path):
    p = Path(path)
    result = {
        "path": path,
        "exists": False,
        "readable": False,
        "mp4_count": 0,
        "error": None,
    }

    try:
        result["exists"] = p.exists()
        if not p.exists() or not p.is_dir():
            return result

        count = 0
        for f in p.rglob("*"):
            try:
                if f.is_file() and f.name.lower().endswith(".mp4"):
                    count += 1
            except Exception:
                pass

        result["readable"] = True
        result["mp4_count"] = count
        return result
    except Exception as e:
        result["error"] = str(e)
        return result

def movies_manifest(cfg):
    forced = cfg.get("TABLET_MOVIES_DIR", "").strip()
    candidates = []

    if forced:
        candidates.append(forced)

    candidates += [x.strip() for x in cfg.get("MP4_DIR_CANDIDATES", "").split("|") if x.strip()]

    # Remove duplicates while keeping order.
    clean = []
    for c in candidates:
        if c not in clean:
            clean.append(c)

    scan_results = []
    best = None

    for d in clean:
        r = scan_dir(d)
        scan_results.append(r)
        if r["readable"] and (best is None or r["mp4_count"] > best["mp4_count"]):
            best = r

    if best is None:
        return {
            "ok": False,
            "base": forced or None,
            "count": 0,
            "files": {},
            "scan_results": scan_results,
            "error": "No readable MP4 directory. Grant Termux Files/Photos/Videos permission.",
        }

    base = Path(best["path"])
    files = {}

    for f in sorted(base.rglob("*")):
        try:
            if f.is_file() and f.name.lower().endswith(".mp4"):
                rel = str(f.relative_to(base))
                tag = hmac_name(cfg["CIPHER_TEXT"], rel)
                files[tag] = {
                    "size": f.stat().st_size,
                    "sha256": sha256_file(f),
                }
        except Exception as e:
            tag = hmac_name(cfg["CIPHER_TEXT"], str(f))
            files[tag] = {"error": str(e)}

    return {
        "ok": True,
        "base": str(base),
        "count": len(files),
        "files": files,
        "scan_results": scan_results,
        "privacy": "Plain MP4 filenames are not sent. HMAC tags only.",
    }

def syncthing_status(cfg):
    key = cfg.get("SYNCTHING_API_KEY", "").strip()

    if key:
        try:
            req = Request(
                "http://127.0.0.1:8384/rest/system/ping",
                headers={"X-API-Key": key}
            )
            with urlopen(req, timeout=5) as resp:
                body = resp.read().decode("utf-8", errors="replace")
            return {
                "ok": "pong" in body,
                "method": "syncthing-rest-api",
                "response": body[:200],
            }
        except Exception as e:
            return {"ok": False, "method": "syncthing-rest-api", "error": str(e)}

    return {
        "ok": False,
        "method": "not-configured-yet",
        "note": "Add SYNCTHING_API_KEY to tablet-fixes.env if Syncthing API is available on tablet.",
    }

def t14_monitor_ok(cfg):
    try:
        req = Request(f"http://{cfg['T14_HOST']}:{int(cfg['TK_PORT'])}/status")
        with urlopen(req, timeout=6) as resp:
            resp.read()
        return True, None
    except Exception as e:
        return False, str(e)

def build_payload(cfg):
    monitor_ok, monitor_error = t14_monitor_ok(cfg)
    ssid = get_ssid()
    movies = movies_manifest(cfg)

    return {
        "tag": TAG,
        "hostname": socket.gethostname() or "amazon-tablet",
        "time_epoch": time.time(),
        "time_text": time.strftime("%Y-%m-%d %H:%M:%S"),
        "ssid": ssid["ssid"] if ssid.get("ok") else ("unknown-but-t14-reachable" if monitor_ok else ssid.get("ssid")),
        "battery": get_battery(),
        "ping_t14": {
            "ok": monitor_ok,
            "host": cfg["T14_HOST"],
            "port": int(cfg["TK_PORT"]),
            "method": "http-to-tk-monitor",
            "error": monitor_error,
        },
        "syncthing": syncthing_status(cfg),
        "movies": movies,
        "event": "github_restore_reboot_hardened_direct_to_8767",
        "discovery": {
            "fixfile": str(FIXFILE),
            "reporter": str(Path(__file__)),
            "ssid_detection": ssid,
            "movies_scan_results": movies.get("scan_results", []),
        },
    }

def main():
    cfg = load_cfg()
    interval = int(cfg.get("INTERVAL_SECONDS", "300") or "300")

    send_stage(cfg, "github-restore-reporter-started", "Reporter started from restored GitHub restore system.", {"fixfile": str(FIXFILE)})

    while True:
        cfg = load_cfg()
        payload = build_payload(cfg)

        try:
            response = post_json(cfg["T14_HOST"], int(cfg["TK_PORT"]), "/status", payload, timeout=15)
            log("posted-to-8767 " + response[:200])
            send_stage(cfg, "github-restore-posted-to-8767", "Posted direct to Tk monitor.", {
                "movies_base": payload["movies"].get("base"),
                "movies_count": payload["movies"].get("count"),
                "movies_ok": payload["movies"].get("ok"),
                "battery_method": payload["battery"].get("method"),
                "ssid": payload.get("ssid"),
            })
        except Exception as e:
            log(f"post-to-8767-failed {e}")
            send_stage(cfg, "github-restore-post-to-8767-failed", str(e))

        time.sleep(interval)

if __name__ == "__main__":
    main()
PY
    chmod +x "$REPORTER"
    stage "reporter-written" "Wrote reboot-hardened Python reporter to $REPORTER."
}

write_boot_reporter() {
cat > "$TARGET" <<'BOOT'
#!/data/data/com.termux/files/usr/bin/sh
# amazon-tablet-reporter.sh
# Termux:Boot wrapper for reboot-hardened reporter.
# TAG: #D3FFC1E

BASE="$HOME/.local/share/amazon-tablet-monitor"
REPORTER="$BASE/amazon_tablet_reboot_hardened_reporter.py"
LOG="$BASE/boot-wrapper.log"

mkdir -p "$BASE"

echo "[$(date)] Termux:Boot wrapper started" >> "$LOG"

if command -v termux-wake-lock >/dev/null 2>&1; then
    termux-wake-lock >> "$LOG" 2>&1 || true
fi

# Give Wi-Fi time to come up after reboot.
sleep 20

echo "[$(date)] Starting reboot-hardened reporter" >> "$LOG"
python "$REPORTER" >> "$BASE/amazon-tablet-reboot-hardened-reporter.log" 2>&1
BOOT
    chmod +x "$TARGET"
    stage "boot-reporter-written" "Wrote Termux:Boot wrapper to $TARGET."
}

write_boot_restore_wrapper() {
cat > "$BOOT_RESTORE" <<'BOOTRESTORE'
#!/data/data/com.termux/files/usr/bin/sh
BASE="$HOME/.local/share/amazon-tablet-monitor"
RESTORE="$BASE/amazon-tablet-reporter-restore-20260605-0922.sh"
LOG="$BASE/boot-restore-wrapper.log"

mkdir -p "$BASE"

echo "[$(date)] 00-restore wrapper started" >> "$LOG"

if [ -x "$RESTORE" ]; then
    "$RESTORE" --ensure >> "$LOG" 2>&1
else
    echo "Restore script missing: $RESTORE" >> "$LOG"
fi
BOOTRESTORE
    chmod +x "$BOOT_RESTORE"
    stage "boot-restore-wrapper-written" "Wrote $BOOT_RESTORE."
}

request_storage_permission() {
    if command -v termux-setup-storage >/dev/null 2>&1; then
        stage "storage-permission-request" "Running termux-setup-storage. Tap Allow if prompted."
        termux-setup-storage >/dev/null 2>&1 || true
    else
        stage "storage-permission-skip" "termux-setup-storage command not available."
    fi

    stage "storage-permission-note" "If /storage/emulated/0/movies is permission denied, open Android Settings -> Apps -> Termux -> Permissions -> allow Files/Photos/Videos."
}

ensure_reporter() {
    stage "ensure-started" "Ensuring restore, boot wrapper, reporter, and config are installed."

    mkdir -p "$BASE" "$HOME/.termux/boot"

    write_fixfile
    write_reporter
    write_boot_reporter
    write_boot_restore_wrapper

    stage "ensure-complete" "Restore system ensured. Target=$TARGET Reporter=$REPORTER Fixfile=$FIXFILE"
}

install_self() {
    mkdir -p "$BASE"
    cp "$0" "$RESTORE" 2>/dev/null || true
    chmod +x "$RESTORE" 2>/dev/null || true

    request_storage_permission
    ensure_reporter

    stage "install-complete" "GitHub restore system installed. Open Termux:Boot once, disable battery optimization, then reboot tablet."
}

start_now() {
    if command -v pkill >/dev/null 2>&1; then
        pkill -f amazon_tablet_reporter.py 2>/dev/null || true
        pkill -f amazon_tablet_reporter_v2.py 2>/dev/null || true
        pkill -f amazon_tablet_reboot_hardened_reporter.py 2>/dev/null || true
    fi

    stage "start-now" "Starting reboot-hardened reporter now."

    nohup python "$REPORTER" >> "$BASE/amazon-tablet-reboot-hardened-reporter.log" 2>&1 &
}

case "${1:-}" in
    --install)
        self_update_from_github "${2:-}"
        install_self
        start_now
        ;;
    --ensure)
        self_update_from_github "${2:-}"
        ensure_reporter
        ;;
    --start)
        self_update_from_github "${2:-}"
        ensure_reporter
        start_now
        ;;
    --no-remote)
        ensure_reporter
        ;;
    *)
        self_update_from_github "${1:-}"
        ensure_reporter
        ;;
esac
