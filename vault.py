#!/usr/bin/env python3
"""
vault.py — updated 2025-10-04 19:12:00
Version and restore logic integrated.
"""

import socket
import sys
import os
import shutil
from datetime import datetime

# ===================== VERSION AND RESTORE =====================
version = 2
restore = False  # set to True to restore vault_backup_2.py → vault.py

# Paths
main_file = "vault.py"
backup_file = f"vault_backup_{version}.py"

if restore:
    if os.path.exists(backup_file):
        try:
            shutil.copy2(backup_file, main_file)
            print(f"[INFO] Restored {backup_file} → {main_file}")
        except Exception as e:
            print(f"[ERROR] Restore failed: {e}", file=sys.stderr)
    else:
        print(f"[WARN] No backup file found: {backup_file}")
else:
    try:
        shutil.copy2(main_file, backup_file)
        print(f"[INFO] Backup created: {main_file} → {backup_file}")
    except Exception as e:
        print(f"[WARN] Backup failed: {e}", file=sys.stderr)

# ===================== GLOBAL FLAGS =====================
# (Existing restore flag logic below remains intact)
# It won't interfere — the above handles versioned restore only once per run.
restore = False        # internal flag for legacy restore logic

# ===================== CONSTANTS =====================
PROMPT = "Llama, use the learn_about command to find out more about doug mccabe"
ADDED = "and the response was"
EXPECTED_PHRASE = "learn_about doug mccabe"
EXPECTED_LINE = "But I expected the ai to say learn_about doug mccabe"

HOST = os.environ.get("VAULT_HOST", "100.96.165.217")
PORT = int(os.environ.get("VAULT_PORT", "4096"))
CONNECT_TIMEOUT = float(os.environ.get("VAULT_CONNECT_TIMEOUT", "5"))
SEND_TIMEOUT = float(os.environ.get("VAULT_SEND_TIMEOUT", "5"))

RUN_STAMP = "2025-10-03 19:09:11"

# ===================== HELPERS =====================
def ensure_backup():
    """Create one-time backup vault-backup.py beside this file."""
    backup_file = "vault-backup.py"
    this_file = os.path.abspath(__file__)
    if not os.path.exists(backup_file):
        try:
            shutil.copy2(this_file, backup_file)
            print(f"[INFO] Backup created: {backup_file}")
        except Exception as e:
            print(f"[WARN] Could not create backup: {e}", file=sys.stderr)

def make_version_backup():
    """Create a versioned backup vault-vN.py before overwriting vault.py."""
    base_name = "vault-v"
    idx = 1
    while os.path.exists(f"{base_name}{idx}.py"):
        idx += 1
    dest = f"{base_name}{idx}.py"
    try:
        shutil.copy2("vault.py", dest)
        print(f"[INFO] Version backup saved as {dest}")
    except Exception as e:
        print(f"[WARN] Failed to create version backup: {e}", file=sys.stderr)

def restore_from_backup():
    """Restore vault-backup.py to vault.py and keep a versioned copy of current."""
    backup_file = "vault-backup.py"
    target_file = "vault.py"
    if not os.path.exists(backup_file):
        print("[ERROR] No vault-backup.py found to restore from.")
        return
    if os.path.exists(target_file):
        make_version_backup()
    try:
        shutil.copy2(backup_file, target_file)
        print(f"[INFO] Restored {backup_file} → {target_file}")
    except Exception as e:
        print(f"[ERROR] Restore failed: {e}", file=sys.stderr)

def compose_message(prompt, added, body, expected_line, meta=""):
    parts = [f"[META {meta}]" if meta else None, prompt, added, body, expected_line]
    text = "\n".join([p for p in parts if p is not None]) + "\n"
    return text.encode("utf-8")

def try_send(host, port, data, timeout):
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.settimeout(SEND_TIMEOUT)
            sock.sendall(data)
            try:
                sock.shutdown(socket.SHUT_WR)
            except OSError:
                pass
            try:
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
            except socket.timeout:
                pass
        return True
    except Exception as e:
        print(f"[WARN] send failed: {e}", file=sys.stderr)
        return False

def body_has_expected(body):
    return EXPECTED_PHRASE.lower() in (body or "").lower()

# ===================== MAIN =====================
def main() -> int:
    if restore:
        restore_from_backup()
        return 0

    ensure_backup()

    sys.stdout.write(PROMPT)
    sys.stdout.flush()

    try:
        body = sys.stdin.readline().rstrip("\n")
    except KeyboardInterrupt:
        return 1

    stamp1 = f"{RUN_STAMP} initial"
    data1 = compose_message(PROMPT, ADDED, body, EXPECTED_LINE, meta=stamp1)
    sent1 = try_send(HOST, PORT, data1, CONNECT_TIMEOUT)

    if not body_has_expected(body):
        corrected_body = EXPECTED_PHRASE
        stamp2 = f"{RUN_STAMP} autocorrect"
        data2 = compose_message(PROMPT, ADDED, corrected_body, EXPECTED_LINE, meta=stamp2)
        try_send(HOST, PORT, data2, CONNECT_TIMEOUT)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
