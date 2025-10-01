#!/usr/bin/env python3
"""
vault.py - Python equivalent of vault.sh

Behavior:
1. Prints PROMPT to stdout
2. Reads one line from stdin into BODY
3. Composes a message containing PROMPT, ADDED, BODY, EXPECTED (each on its own line)
4. Tries to send the message over TCP to 100.96.165.217:4096
   - On success, exits with 0
   - On failure, prints the composed message to stdout as a fallback and exits with 0
"""

import socket
import sys

PROMPT = "Llama, use the learn_about command to find out more about doug mccabe"
ADDED = "and the response was"
EXPECTED = "But I expected the ai to say learn_about doug mccabe"

HOST = "100.96.165.217"
PORT = 4096
CONNECT_TIMEOUT = 5  # seconds
SEND_TIMEOUT = 5  # seconds

def compose_message(prompt: str, added: str, body: str, expected: str) -> bytes:
    """Return the composed message as bytes (UTF-8) with a final newline."""
    # Each piece on its own line, like the original printf usage.
    text = "\n".join([prompt, added, body, expected]) + "\n"
    return text.encode("utf-8")

def try_send(host: str, port: int, data: bytes, timeout: float) -> bool:
    """
    Try to send data to host:port via TCP.
    Returns True on success, False on any exception.
    """
    try:
        # create_connection handles DNS and timeout
        with socket.create_connection((host, port), timeout=timeout) as sock:
            # Optionally set a timeout for send/recv operations
            sock.settimeout(SEND_TIMEOUT)
            # Send all bytes
            sock.sendall(data)
            # Try to politely close the writing side so the remote sees EOF.
            try:
                sock.shutdown(socket.SHUT_WR)
            except OSError:
                # Some platforms/servers may error on shutdown; ignore.
                pass
            # Optionally attempt to read any response (not required)
            # We won't block forever — the socket has a timeout.
            try:
                # Read until the peer closes or timeout occurs (non-blocking due to timeout)
                # We'll read small chunks and ignore content; this mirrors nc behavior which would wait.
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
            except socket.timeout:
                # No response within timeout — that's fine; consider send successful.
                pass
        return True
    except Exception as exc:
        # Could be connection refused, network unreachable, timeout, etc.
        # For debugging you could log exc, but we follow the original script's silent failure model.
        return False

def main() -> int:
    # Print PROMPT (without newline in original script, but it's ok either way).
    # The original script did `printf "$PROMPT"` (no newline) then `read BODY`.
    # We'll print the prompt and keep the cursor on same line to mimic expected behavior.
    try:
        sys.stdout.write(PROMPT)
        sys.stdout.flush()
    except Exception:
        # if stdout is weird, just continue
        pass

    # Read a single line from the user (strip trailing newline)
    try:
        BODY = sys.stdin.readline()
        if BODY == "":
            # EOF (no input); set body to empty string
            BODY = ""
        else:
            BODY = BODY.rstrip("\n")
    except KeyboardInterrupt:
        # user cancelled; exit cleanly
        return 1

    data = compose_message(PROMPT, ADDED, BODY, EXPECTED)

    # Try to send over network
    sent = try_send(HOST, PORT, data, CONNECT_TIMEOUT)

    if not sent:
        # fallback: print the composed message to stdout (mirrors final printf fallback)
        # The original script used `2>/dev/null` to silence nc errors; we will not print exceptions.
        sys.stdout.write("\n")  # ensure a newline after the original prompt if user input was inline
        sys.stdout.write(data.decode("utf-8"))
        sys.stdout.flush()

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
