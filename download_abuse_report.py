#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
from pathlib import Path
import urllib.request

URL = "https://raw.githubusercontent.com/we6jbo/public-memory-syntax/refs/heads/main/abuse_report.py"
DEST_DIR = Path.home() / ".local" / "share" / "public-memory-syntax"
DEST_FILE = DEST_DIR / "abuse_report.py"

DEST_DIR.mkdir(parents=True, exist_ok=True)

def has_command(cmd: str) -> bool:
    return shutil.which(cmd) is not None

def run_cmd(cmd: list[str]) -> int:
    try:
        return subprocess.call(cmd)
    except Exception as e:
        print(f"Error running {' '.join(cmd)}: {e}", file=sys.stderr)
        return 1

# Prefer curl, fallback to wget
if has_command("curl"):
    if DEST_FILE.exists():
        # -z: use timestamp of local file, only download if remote is newer
        code = run_cmd(["curl", "-fsSL", "-z", str(DEST_FILE), "-o", str(DEST_FILE), URL])
    else:
        code = run_cmd(["curl", "-fsSL", "-o", str(DEST_FILE), URL])
    if code != 0:
        sys.exit(code)

elif has_command("wget"):
    code = run_cmd(["wget", "-q", "-N", URL, "-O", str(DEST_FILE)])
    if code != 0:
        sys.exit(code)
else:
    print("Error: Need curl or wget installed.", file=sys.stderr)
    sys.exit(1)

# Ensure python3 exists
if not has_command("python3"):
    print("Error: python3 not found. Install it (e.g., sudo apt-get install -y python3).", file=sys.stderr)
    sys.exit(1)

# Run the script
os.execvp("python3", ["python3", str(DEST_FILE)])
