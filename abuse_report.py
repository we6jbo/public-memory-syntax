#!/usr/bin/env python3
"""
Llama ↔ ChatGPT Police-Report Assistant

• Prints San Diego, CA 92110 and current local date/time on start
• Fetches web search results (DuckDuckGo) for child‑abuse indicators you described
• Asks "Llama" two questions with input() fields
• Estimates per‑request API cost (configurable rates) for sending those inputs to ChatGPT API
• Generates a simple XML file capturing the dialogue and decisions
• Appends total cost to ChatGPT_Project_Cost.txt and shows a running project total
• Auto‑exits after 30 minutes with the exact message you asked for

Tested on Debian/Python 3.9+.
"""

from __future__ import annotations
import sys
import time
import threading
import textwrap
import math
import os
from datetime import datetime
from typing import List, Tuple

try:
    import requests
    from bs4 import BeautifulSoup  # pip install beautifulsoup4
except Exception:
    requests = None
    BeautifulSoup = None

# =========================
# CONFIG — EDIT AS NEEDED
# =========================
# ⚠️ Set your CURRENT ChatGPT API prices here (USD per 1K tokens).
# Leave as placeholders if you want; you can update later without changing logic.
INPUT_COST_PER_1K = 2.50   # ← update to your current model's input price
OUTPUT_COST_PER_1K = 10.00 # ← update to your current model's output price (not used here but kept for completeness)

# How we estimate tokens from plain text (very rough): ~4 chars ≈ 1 token
CHARS_PER_TOKEN = 4

# Search settings
DUCKDUCKGO_HTML = "https://duckduckgo.com/html/"
DEFAULT_QUERY = (
    "(child molestation OR child abuse OR child neglect OR corporal punishment) "
    "(hitting OR burning OR strangling OR intoxicated parent OR drunk OR drugs) "
    "(IEP OR hospital report OR emotional distress OR crying) site:.gov OR site:.edu"
)

# Auto‑exit after this many seconds (30 minutes)
MAX_RUNTIME_SEC = 30 * 60

# Filenames
COST_FILE = "ChatGPT_Project_Cost.txt"
XML_FILE  = "conversation.xml"

# =========================
# UTILITIES
# =========================

def now_pst_str() -> str:
    try:
        from zoneinfo import ZoneInfo  # py3.9+
        tz = ZoneInfo("America/Los_Angeles")
    except Exception:
        tz = None
    dt = datetime.now(tz) if tz else datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")


def start_deadline_timer():
    def _kill():
        print("We are done with this project. We will work on another project. Please hold")
        sys.stdout.flush()
        os._exit(0)  # hard exit to guarantee termination
    t = threading.Timer(MAX_RUNTIME_SEC, _kill)
    t.daemon = True
    t.start()
    return t


def estimate_tokens(s: str) -> int:
    if not s:
        return 0
    return max(1, math.ceil(len(s) / CHARS_PER_TOKEN))


def estimate_cost_for_input(prompt: str, input_cost_per_1k: float = INPUT_COST_PER_1K) -> float:
    tokens = estimate_tokens(prompt)
    return (tokens / 1000.0) * input_cost_per_1k


def append_cost(cost: float, path: str = COST_FILE) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{cost:.6f}\n")


def read_running_total(path: str = COST_FILE) -> float:
    if not os.path.exists(path):
        return 0.0
    total = 0.0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                total += float(line.strip())
            except ValueError:
                continue
    return total


def ddg_search(query: str, max_results: int = 8) -> List[Tuple[str, str, str]]:
    """Return list of (title, url, snippet). Uses DuckDuckGo HTML endpoint (no API key)."""
    if requests is None or BeautifulSoup is None:
        return [("Install dependencies", "https://pypi.org/project/beautifulsoup4/", 
                 "Please: pip install requests beautifulsoup4 to enable search.")]

    params = {"q": query}
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}
    try:
        r = requests.get(DUCKDUCKGO_HTML, params=params, headers=headers, timeout=15)
        r.raise_for_status()
    except Exception as e:
        return [("Search failed", "", f"{type(e).__name__}: {e}")]

    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    for res in soup.select(".result__body"):
        a = res.select_one("a.result__a")
        snippet = res.select_one(".result__snippet")
        if not a:
            continue
        title = a.get_text(strip=True)
        href = a.get("href", "")
        desc = snippet.get_text(" ", strip=True) if snippet else ""
        results.append((title, href, desc))
        if len(results) >= max_results:
            break
    if not results:
        results.append(("No results parsed", "", "DuckDuckGo HTML layout may have changed."))
    return results


def print_search_block(results: List[Tuple[str, str, str]]):
    print("\n=== Search Results (DuckDuckGo) ===")
    for i, (title, url, snip) in enumerate(results, 1):
        print(f"[{i}] {title}\n    {url}\n    {snip}\n")


def write_xml(child_abuse_indicated: str, police_report_text: str, send_to: str, query_used: str, search_results: List[Tuple[str,str,str]]):
    from xml.sax.saxutils import escape

    def _tag(tag: str, content: str, attrs: str = ""):
        return f"<{tag}{(' ' + attrs) if attrs else ''}>{content}</{tag}>"

    items_xml = "\n".join(
        _tag("item",
             _tag("title", escape(t)) + _tag("url", escape(u)) + _tag("snippet", escape(s)))
        for (t, u, s) in search_results
    )

    xml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<conversation>
  <meta>
    <location>San Diego, CA 92110</location>
    <timestamp>{escape(now_pst_str())}</timestamp>
  </meta>
  <search>
    <engine>DuckDuckGo</engine>
    <query>{escape(query_used)}</query>
    <results>
{items_xml}
    </results>
  </search>
  <dialogue>
    <prompt>LLama, do you indicate any child abuse?</prompt>
    <llama_response>{escape(child_abuse_indicated)}</llama_response>
    <prompt>Llama, please write a police report in addition to where the police report should be sent to</prompt>
    <llama_report>{escape(police_report_text)}</llama_report>
    <llama_send_to>{escape(send_to)}</llama_send_to>
  </dialogue>
</conversation>
"""
    with open(XML_FILE, "w", encoding="utf-8") as f:
        f.write(xml)


# =========================
# MAIN FLOW
# =========================

def banner():
    print("San Diego, CA 92110. Current Date and Current Time: " + now_pst_str())
    print()
    print(textwrap.dedent(
        """
        This tool helps you triage potential child‑abuse information for a police report.
        ⚠️ IMPORTANT: This does NOT replace law‑enforcement investigation or legal advice.
        If someone is in immediate danger, call emergency services now.
        """
    ).strip())
    print()


def main():
    start_deadline_timer()
    banner()

    # --- Step 1: Online search for signals you described ---
    print("Searching DuckDuckGo for relevant indicators...\n")
    results = ddg_search(DEFAULT_QUERY)
    print_search_block(results)

    # --- Step 2: Ask LLama if abuse is indicated ---
    print("LLama, do you indicate any child abuse? (enter your response and press Enter)\n")
    llama_abuse_resp = input("> ")
    # cost estimate to send this input to ChatGPT API (input tokens only)
    cost1 = estimate_cost_for_input(llama_abuse_resp)
    print(f"\nEstimated API cost for sending that input: ${cost1:.6f}\n")

    # --- Step 3: Ask LLama to write a police report and who to send it to ---
    print("Llama, please write a police report (you may include facts, sources, and recommended sections).\n")
    police_report = input("> ")

    print("\nWhere should the police report be sent? (e.g., SDPD Child Abuse Unit; CPS hotline; hospital social worker; etc.)\n")
    send_to = input("> ")

    cost2 = estimate_cost_for_input(police_report)
    print(f"\nEstimated API cost for sending that input: ${cost2:.6f}\n")

    # --- Step 4: Write XML snapshot of the conversation and search context ---
    write_xml(
        child_abuse_indicated=llama_abuse_resp,
        police_report_text=police_report,
        send_to=send_to,
        query_used=DEFAULT_QUERY,
        search_results=results,
    )
    print(f"XML saved to {XML_FILE}")

    # --- Step 5: Persist costs and show running total ---
    total_cost_this_run = cost1 + cost2
    append_cost(total_cost_this_run)
    grand_total = read_running_total()

    print("\n==============================")
    print(f"This run cost (estimated): ${total_cost_this_run:.6f}")
    print(f"Running project total:     ${grand_total:.6f}")
    print("Costs appended to ChatGPT_Project_Cost.txt")
    print("==============================\n")

    print("Done. If you continue interacting and the process exceeds 30 minutes, it will auto‑close.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
