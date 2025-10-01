#!/usr/bin/env python3
import os
import re
import json
import ast
from urllib import request, error
from typing import Tuple, Optional, Iterable

LOG_FILE = "/home/ameliahedtkealiceelliott/neuralnexus/share_to_reddit.txt"

BASE_URL = (
    "https://raw.githubusercontent.com/we6jbo/public-memory-syntax/refs/heads/main"
)
LOCAL_DIR = os.path.expanduser("~/.cache/public-memory-syntax/tests")

# ===== Utility =====
def say_hello():
    print("Hey there, let’s get started.")

def log_header():
    if not os.path.exists(LOG_FILE):
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(
                "Log of wrong responses only.\n"
                "Each entry shows the question, what was typed, "
                "and why it didn’t match.\n\n"
            )

def _download_text(url: str, dest_path: str) -> str:
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    try:
        with request.urlopen(url) as resp:
            data = resp.read().decode("utf-8", errors="replace")
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(data)
        return data
    except error.HTTPError as e:
        if e.code == 404:
            raise FileNotFoundError(f"404 Not Found: {url}") from e
        raise
    except Exception:
        raise

def _parse_case(text: str) -> Tuple[str, str, str, Optional[str]]:
    """
    Parse ONE test case line supporting:
      - JSON array: ["Question","REGEX","pattern","Reason"]
      - Python literal tuple/list
      - CSV-style: "Question","REGEX","pattern","Reason"
    """
    cleaned = text.strip()

    # Try JSON
    try:
        obj = json.loads(cleaned)
        if isinstance(obj, list) and 3 <= len(obj) <= 4:
            q, t, p = obj[0], obj[1], obj[2]
            r = obj[3] if len(obj) == 4 else None
            return str(q), str(t), str(p), (str(r) if r else None)
    except Exception:
        pass

    # Try Python literal
    try:
        obj = ast.literal_eval(cleaned)
        if isinstance(obj, (list, tuple)) and 3 <= len(obj) <= 4:
            q, t, p = obj[0], obj[1], obj[2]
            r = obj[3] if len(obj) == 4 else None
            return str(q), str(t), str(p), (str(r) if r else None)
    except Exception:
        pass

    # CSV-style fallback
    def _split_top_level(s: str, parts: int) -> list:
        out, buf, quote = [], [], None
        count = 0
        for ch in s:
            if ch in ('"', "'"):
                if quote is None:
                    quote = ch
                elif quote == ch:
                    quote = None
                buf.append(ch)
            elif ch == "," and quote is None and count < parts - 1:
                out.append("".join(buf).strip().strip('"').strip("'"))
                buf = []
                count += 1
            else:
                buf.append(ch)
        out.append("".join(buf).strip().strip('"').strip("'"))
        return out

    fields = _split_top_level(cleaned, 4)
    if len(fields) >= 3:
        q, t, p = fields[0], fields[1], fields[2]
        r = fields[3] if len(fields) >= 4 else None
        return q, t, p, (r if r else None)

    raise ValueError("Unable to parse test case line")

def _iter_cases_in_file(file_text: str) -> Iterable[Tuple[str, str, str, Optional[str], int]]:
    """
    Yield (q, t, p, reason, line_no) for each usable line.
    Skip empty lines and comments starting with '#'.
    """
    for idx, raw in enumerate(file_text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            q, t, p, r = _parse_case(line)
            yield q, t, p, r, idx
        except Exception as e:
            print(f"    (Skipping line {idx}: couldn’t parse → {e})")

def ask_and_check(question: str, check_type: str, check_param: str, failure_reason: Optional[str] = None):
    print(f"\nQuestion: {question}")
    response = input("Your response: ").strip()

    status = "correct"
    reason = None

    ctype = check_type.strip().upper()
    if ctype == "NONEMPTY":
        if not response:
            status = "wrong"
            reason = failure_reason or "You didn’t type anything."
    elif ctype == "EQUALS":
        if response.lower() != check_param.strip().lower():
            status = "wrong"
            reason = failure_reason or f"I was expecting exactly: {check_param}"
    elif ctype in ("REGEX", "REGET"):  # allow "REGET" alias
        try:
            if not re.search(check_param, response, re.IGNORECASE | re.DOTALL):
                status = "wrong"
                reason = failure_reason or f"That doesn’t match what I was looking for: {check_param}"
        except re.error as rex:
            status = "wrong"
            reason = f"Oops, bad regex '{check_param}': {rex}"
    else:
        status = "wrong"
        reason = f"I don’t understand the check type: {check_type}"

    if status == "wrong":
        print("Hmm… that didn’t seem right.")
        print(f"→ Reason: {reason}")
        print("Tell me when you’re ready and we’ll try the next one.")
        # Log only wrong answers
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("----\n")
            f.write(f"Question: {question}\n")
            f.write(f"Answer: {response}\n")
            f.write(f"Reason: {reason}\n")
            f.write(f"Full Response Text: {response}\n")
    else:
        print("Yep, that looks good ✅")
        print("Tell me when you’re ready and we’ll keep going.")

def run_sequential_cases():
    index = 1
    while True:
        filename = f"{index}.txt"
        url = f"{BASE_URL}/{filename}"
        local = os.path.join(LOCAL_DIR, filename)

        try:
            print(f"\nFetching {url} …")
            content = _download_text(url, local)
        except FileNotFoundError:
            print(f"\nNo more files (stopped at {filename}).")
            break
        except Exception as e:
            print(f"\nStopped due to download error on {filename}: {e}")
            break

        any_line_processed = False
        for q, t, p, r, ln in _iter_cases_in_file(content):
            any_line_processed = True
            print(f"\nLine {ln} in {filename}:")
            ask_and_check(q, t, p, r)

        if not any_line_processed:
            print(f"(Nothing usable in {filename}; moving on.)")

        index += 1

# ===== Main =====
if __name__ == "__main__":
    say_hello()
    log_header()
    run_sequential_cases()
    print("\nAll done. 👍")
