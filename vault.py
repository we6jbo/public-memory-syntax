#!/usr/bin/env python3
"""
vault.py - Python equivalent of vault.sh
Updated to create a one-time backup as vault-backup.py
"""

import socket
import sys
import os
import shutil

PROMPT = "Llama, use the learn_about command to find out more about doug mccabe"
ADDED = "and the response was"
EXPECTED = "But I expected the ai to say learn_about doug mccabe"

HOST = "100.96.165.217"
PORT = 4096
CONNECT_TIMEOUT = 5  # seconds
SEND_TIMEOUT = 5     # seconds

def ensure_backup():
    """Check if vault-backup.py exists. If not, make a backup copy of vault.py."""
    backup_file = "vault-backup.py"
    this_file = os.path.abspath(__file__)
    if not os.path.exists(backup_file):
        try:
            shutil.copy2(this_file, backup_file)
            print(f"[INFO] Backup created: {backup_file}")
        except Exception as e:
            print(f"[WARN] Could not create backup: {e}", file=sys.stderr)

def compose_message(prompt: str, added: str, body: str, expected: str) -> bytes:
    text = "\n".join([prompt, added, body, expected]) + "\n"
    return text.encode("utf-8")

def try_send(host: str, port: int, data: bytes, timeout: float) -> bool:
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
    except Exception:
        return False

def main() -> int:
    ensure_backup()

    try:
        sys.stdout.write(PROMPT)
        sys.stdout.flush()
    except Exception:
        pass

    try:
        BODY = sys.stdin.readline()
        BODY = "" if BODY == "" else BODY.rstrip("\n")
    except KeyboardInterrupt:
        return 1

    data = compose_message(PROMPT, ADDED, BODY, EXPECTED)
    sent = try_send(HOST, PORT, data, CONNECT_TIMEOUT)

    if not sent:
        sys.stdout.write("\n")
        sys.stdout.write(data.decode("utf-8"))
        sys.stdout.flush()

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
