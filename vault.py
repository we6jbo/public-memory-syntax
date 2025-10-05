#!/usr/bin/env python3
"""
vault.py — streamlined to a single versioned backup/restore system
Updated: 2025-10-04
"""

import socket
import sys
import os
import shutil
from datetime import datetime

# ===================== VERSIONED BACKUP / RESTORE =====================
version = 3
restore = False  # set True to restore vault_backup_{version}.py → vault.py

# Paths
main_file = "vault.py"
backup_file = f"vault_backup_{version}.py"

# Perform backup/restore once at import
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
        # Make a versioned backup of the current vault.py
        shutil.copy2(main_file, backup_file)
        print(f"[INFO] Backup created: {main_file} → {backup_file}")
    except Exception as e:
        print(f"[WARN] Backup failed: {e}", file=sys.stderr)

# ===================== CONSTANTS =====================
PROMPT = "Llama, use the learn_about command to find out more about doug mccabe"
ADDED = "and the response was"
EXPECTED_PHRASE = "learn_about doug mccabe"
EXPECTED_LINE = "But I expected the ai to say learn_about doug mccabe"

HOST = os.environ.get("VAULT_HOST", "100.96.165.217")
PORT = int(os.environ.get("VAULT_PORT", "4096"))
CONNECT_TIMEOUT = float(os.environ.get("VAULT_CONNECT_TIMEOUT", "5"))
SEND_TIMEOUT = float(os.environ.get("VAULT_SEND_TIMEOUT", "5"))

# Keep your original run-stamp for traceability
RUN_STAMP = "2025-10-03 19:09:11"

# ===================== HELPERS (legacy backup helpers removed) =====================
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
    # (legacy restore/ensure_backup branches removed)

    # Emit the prompt and read a single line from stdin
    sys.stdout.write(PROMPT)
    sys.stdout.flush()

    try:
        body = sys.stdin.readline().rstrip("\n")
    except KeyboardInterrupt:
        return 1

    # First send with whatever body the user entered
    stamp1 = f"{RUN_STAMP} initial"
    data1 = compose_message(PROMPT, ADDED, body, EXPECTED_LINE, meta=stamp1)
    try_send(HOST, PORT, data1, CONNECT_TIMEOUT)

    # If the expected phrase wasn't present, send an autocorrected follow-up
    if not body_has_expected(body):
        corrected_body = EXPECTED_PHRASE
        stamp2 = f"{RUN_STAMP} autocorrect"
        data2 = compose_message(PROMPT, ADDED, corrected_body, EXPECTED_LINE, meta=stamp2)
        try_send(HOST, PORT, data2, CONNECT_TIMEOUT)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
#!/usr/bin/env python3
"""
vault.py — streamlined to a single versioned backup/restore system
Updated: 2025-10-04
"""

import socket
import sys
import os
import shutil
from datetime import datetime

# ===================== VERSIONED BACKUP / RESTORE =====================
version = 2
restore = False  # set True to restore vault_backup_{version}.py → vault.py

# Paths
main_file = "vault.py"
backup_file = f"vault_backup_{version}.py"

# Perform backup/restore once at import
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
        # Make a versioned backup of the current vault.py
        shutil.copy2(main_file, backup_file)
        print(f"[INFO] Backup created: {main_file} → {backup_file}")
    except Exception as e:
        print(f"[WARN] Backup failed: {e}", file=sys.stderr)

# ===================== CONSTANTS =====================
PROMPT = "Llama, use the learn_about command to find out more about doug mccabe"
ADDED = "and the response was"
EXPECTED_PHRASE = "learn_about doug mccabe"
EXPECTED_LINE = "But I expected the ai to say learn_about doug mccabe"

HOST = os.environ.get("VAULT_HOST", "100.96.165.217")
PORT = int(os.environ.get("VAULT_PORT", "4096"))
CONNECT_TIMEOUT = float(os.environ.get("VAULT_CONNECT_TIMEOUT", "5"))
SEND_TIMEOUT = float(os.environ.get("VAULT_SEND_TIMEOUT", "5"))

# Keep your original run-stamp for traceability
RUN_STAMP = "2025-10-03 19:09:11"

# ===================== HELPERS (legacy backup helpers removed) =====================
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
    # (legacy restore/ensure_backup branches removed)

    # Emit the prompt and read a single line from stdin
    sys.stdout.write(PROMPT)
    sys.stdout.flush()

    try:
        body = sys.stdin.readline().rstrip("\n")
    except KeyboardInterrupt:
        return 1

    # First send with whatever body the user entered
    stamp1 = f"{RUN_STAMP} initial"
    data1 = compose_message(PROMPT, ADDED, body, EXPECTED_LINE, meta=stamp1)
    try_send(HOST, PORT, data1, CONNECT_TIMEOUT)

    # If the expected phrase wasn't present, send an autocorrected follow-up
    if not body_has_expected(body):
        corrected_body = EXPECTED_PHRASE
        stamp2 = f"{RUN_STAMP} autocorrect"
        data2 = compose_message(PROMPT, ADDED, corrected_body, EXPECTED_LINE, meta=stamp2)
        try_send(HOST, PORT, data2, CONNECT_TIMEOUT)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
