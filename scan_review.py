#!/usr/bin/env python3
"""
scan_review.py

Behavior:
- Looks for files matching /tmp/Aug17_D/scan_*.jsonl
- Processes them in ascending mtime order, one by one:
  * Prints a summary (>= one full line, up to 300 words, whichever is greater)
  * Prompts: "Do you see anything concerning?"
  * If a concerning keyword is present, asks for a subject name and writes a
    police-style report to:
      /home/ameliahedtkealiceelliott/neuralnexus/{SUBJECT}_{DATE}_police_report.txt
    (Includes websites, dates (from 'ts'), the automation note, and RefCode.)

- Stops when files are exhausted OR when 30 minutes have elapsed since start.

RefCode: 6fBiQlT
"""

import os
import sys
import json
import glob
import time
from datetime import datetime
from pathlib import Path

SCAN_DIR = Path("/tmp/Aug17_D")
GLOB_PATTERN = "scan_*.jsonl"
OUTPUT_DIR = Path("/home/ameliahedtkealiceelliott/neuralnexus/")
REF_CODE = "6fBiQlT"
TIMEOUT_SECONDS = 30 * 60  # 30 minutes

CONCERN_KEYWORDS = [
    "burn", "burning", "molestation", "molest", "child abuse", "abuse",
    "car accident", "auditory processing disorder", "apd", "assault", "bruise",
    "violence", "threat", "kidnap", "neglect", "exploitation"
]

def word_count(text: str) -> int:
    return len([w for w in text.split() if w.strip()])

def summarize_jsonl(path: Path):
    """Return a summary string and the parsed records (list of dicts)."""
    records = []
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                records.append(rec)
            except Exception:
                records.append({"raw": line})

    pieces, wc = [], 0
    for i, rec in enumerate(records):
        if "raw" in rec:
            s = rec["raw"]
        else:
            ts = rec.get("ts") or "unknown-ts"
            site = rec.get("website") or rec.get("site") or "unknown-site"
            kw = rec.get("keyword") or "unknown-keyword"
            author = rec.get("author") or "unknown-author"
            code = rec.get("status_code")
            code = f" status={code}" if code is not None else ""
            s = f"[{ts}] site={site} keyword={kw} author={author}{code}"
        pieces.append(s)
        wc += word_count(s)
        if i >= 0 and wc >= 300:
            break

    if not pieces and records == []:
        pieces = ["(no entries)"]

    summary = "\n".join(pieces)
    return summary, records

def contains_concern(text: str) -> bool:
    t = text.lower()
    return any(kw.lower() in t for kw in CONCERN_KEYWORDS)

def build_report(subject_name: str, scan_path: Path, records: list[dict]) -> str:
    sites, dates = set(), set()
    for rec in records:
        if isinstance(rec, dict):
            site = rec.get("website") or rec.get("site")
            if site:
                sites.add(site)
            ts = rec.get("ts")
            if ts:
                dates.add(ts)

    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    report = []
    report.append(f"Subject: {subject_name}")
    report.append(f"Report Created: {now_str}")
    report.append(f"Reference Code: {REF_CODE}")
    report.append("")
    report.append("Summary of Concern:")
    report.append("This report was generated following a user-identified concerning entry in an automated internet scan.")
    report.append("")
    report.append("Where the information was found (websites):")
    for s in sorted(sites) if sites else ["unknown-site"]:
        report.append(f" - {s}")
    report.append("")
    report.append("Dates on the document(s) (as found in records):")
    for d in sorted(dates) if dates else ["unknown-date"]:
        report.append(f" - {d}")
    report.append("")
    report.append("Automation Note:")
    report.append("This report was created with Llama AI and automated by Jeremiah ONeal in San Diego, CA.")
    report.append("")
    report.append(f"Scan Source File: {scan_path}")
    report.append("")
    return "\n".join(report)

def write_report(subject: str, scan_path: Path, records: list[dict]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    date_part = now.strftime("%b%d_%I_%M%p")  # e.g., Aug17_05_15AM
    safe_subject = "".join(c for c in subject if c.isalnum() or c in ("_", "-"))
    filename = f"{safe_subject}_{date_part}_police_report.txt"
    out_path = OUTPUT_DIR / filename
    text = build_report(safe_subject or "UnknownSubject", scan_path, records)
    with out_path.open("w", encoding="utf-8") as f:
        f.write(text)
    return out_path

def list_scan_files() -> list[Path]:
    paths = [Path(p) for p in glob.glob(str(SCAN_DIR / GLOB_PATTERN))]
    # Sort by modification time ascending (oldest first)
    paths.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0)
    return paths

def main():
    start = time.time()

    files = list_scan_files()
    if not files:
        print(f"No files found in {SCAN_DIR} matching {GLOB_PATTERN}.")
        sys.exit(0)

    for path in files:
        # Timeout check before each file
        if time.time() - start > TIMEOUT_SECONDS:
            print("30-minute limit reached. Exiting.")
            sys.exit(0)

        # Summarize current file
        try:
            summary, records = summarize_jsonl(path)
        except Exception as e:
            print(f"Error reading {path}: {e}")
            continue

        print("=" * 70)
        print(f"FILE: {path}")
        print("=" * 70)
        print("SCAN SUMMARY (>= one line, up to 300 words):")
        print("=" * 70)
        print(summary)
        print("=" * 70)

        # Prompt for concerns (timeout check again after user input opportunity)
        print('Do you see anything concerning? (Describe briefly; leave blank for "no")')
        user_input = input("> ").strip()

        if time.time() - start > TIMEOUT_SECONDS:
            print("30-minute limit reached after input. Exiting.")
            sys.exit(0)

        if not user_input:
            # Move on to the next file
            continue

        if contains_concern(user_input):
            print('Enter subject name for the report filename (e.g., "JeremiahONeal"):')
            subject = input("> ").strip() or "UnknownSubject"

            if time.time() - start > TIMEOUT_SECONDS:
                print("30-minute limit reached before writing report. Exiting.")
                sys.exit(0)

            out_path = write_report(subject, path, records)
            print(f"Report written to: {out_path}")
        # If input has no concern keywords, just proceed to the next file silently.

    print("All scan files processed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
