#!/usr/bin/env python3
"""
vault.py — versioned backup/restore + guided prompt + safe network send
Updated: 2025-10-06 06:18:07
"""

import os
import sys
import socket
import shutil

# ===================== VERSIONED BACKUP / RESTORE =====================
version = 5                # incremented per your request
restore = False            # set True to restore below
RESTORE_VERSION = None     # e.g., 2 → restores vault_backup_2.py

# Resolve current script name so backups work even if file isn't literally "vault.py"
MAIN_FILE = os.path.basename(__file__)
BACKUP_FILE = f"vault_backup_{version}.py"

def log_info(msg: str) -> None:
    print(msg, file=sys.stderr)

if restore:
    candidate = f"vault_backup_{RESTORE_VERSION}.py" if RESTORE_VERSION is not None else BACKUP_FILE
    if os.path.exists(candidate):
        try:
            shutil.copy2(candidate, MAIN_FILE)
            log_info(f"[INFO] Restored {candidate} → {MAIN_FILE}")
        except Exception as e:
            log_info(f"[ERROR] Restore failed: {e}")
    else:
        log_info(f"[WARN] No backup file found: {candidate}")
else:
    try:
        shutil.copy2(MAIN_FILE, BACKUP_FILE)
        log_info(f"[INFO] Backup created: {MAIN_FILE} → {BACKUP_FILE}")
    except Exception as e:
        log_info(f"[WARN] Backup failed: {e}")

# ===================== CONSTANTS =====================
PROMPT = "Llama, use the learn_about command to find out more about doug mccabe"
ADDED = "and the response was"
EXPECTED_PHRASE = "learn_about doug mccabe"
EXPECTED_LINE = "But I expected the ai to say learn_about doug mccabe"

# Host/port may be overridden via env
HOST = os.environ.get("VAULT_HOST", "100.96.165.217")
PORT = int(os.environ.get("VAULT_PORT", "4096"))
CONNECT_TIMEOUT = float(os.environ.get("VAULT_CONNECT_TIMEOUT", "5"))
SEND_TIMEOUT = float(os.environ.get("VAULT_SEND_TIMEOUT", "5"))

# Replacement token for any non-expected outbound body
SANITIZED_TOKEN = "gMSzQWMA"

# ===================== HELPERS =====================
def compose_message(prompt, added, body, expected_line):
    """
    Compose the wire payload. No [META ...] lines are included.
    """
    parts = [prompt, added, body, expected_line]
    return ("\n".join(parts) + "\n").encode("utf-8")

def try_send(host, port, data, connect_timeout, send_timeout):
    try:
        with socket.create_connection((host, port), timeout=connect_timeout) as sock:
            sock.settimeout(send_timeout)
            sock.sendall(data)
            try:
                sock.shutdown(socket.SHUT_WR)
            except OSError:
                pass
            # Optionally drain response without blocking forever
            try:
                while True:
                    if not sock.recv(4096):
                        break
            except socket.timeout:
                pass
        return True
    except Exception as e:
        log_info(f"[WARN] send failed: {e}")
        return False

def exact_expected(s: str) -> bool:
    return s == EXPECTED_PHRASE

def read_line() -> str:
    return sys.stdin.readline().rstrip("\n")

# ===================== MAIN =====================
def main() -> int:
    # Print ONLY the base prompt first
    print(PROMPT, end="", flush=True)
    body1 = read_line()

    if not exact_expected(body1):
        print("you didnt say learn_about doug mccabe but I wanted you to say learn_about doug mccabe", flush=True)
        body2 = read_line()
    else:
        body2 = body1  # already correct; keep for network

    if not exact_expected(body2):
        print("you still didn't say learn_about doug mccabe and all I wanted you to say is learn_about doug mccabe", flush=True)
        body3 = read_line()
    else:
        body3 = body2

    if not exact_expected(body3):
        print("Ok we will try next time.", flush=True)

    # Determine the "final interactive body" to transmit (sanitized if not exact)
    final_body = body3 if exact_expected(body3) else SANITIZED_TOKEN

    # ========== Network send #1: interactive body (sanitized if needed) ==========
    pkt1 = compose_message(PROMPT, ADDED, final_body, EXPECTED_LINE)
    try_send(HOST, PORT, pkt1, CONNECT_TIMEOUT, SEND_TIMEOUT)

    # ========== Network send #2: autocorrect with exact expected ==========
    pkt2 = compose_message(PROMPT, ADDED, EXPECTED_PHRASE, EXPECTED_LINE)
    try_send(HOST, PORT, pkt2, CONNECT_TIMEOUT, SEND_TIMEOUT)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
