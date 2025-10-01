#!/usr/bin/env python3
# ai_oracle.py
# A tiny text UI that interprets user intent, prints forecasts, and writes memories.
# ASCII only: A-Z a-z 0-9 and punctuation.

import sys
import time
import random
from datetime import datetime, timezone, timedelta

import os
import threading

LOCATION_STR = "San Diego, CA 92110"
MEMORY_FILE = "future_ai.txt"

# ------------- helpers -------------

def lower(s: str) -> str:
    return s.lower()

def now_date() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d")

def now_time() -> str:
    # Include local timezone abbreviation like '%Z'
    return datetime.now().astimezone().strftime("%H:%M:%S %Z")

def add_months(year: int, month: int, offset: int) -> (int, int):
    """Return (year, month) after adding offset months to (year, month)."""
    total = (year * 12 + (month - 1)) + offset
    y, m0 = divmod(total, 12)
    return y, m0 + 1

def rand_pick(offset: int) -> str:
    """
    Poor man's deterministic month chooser based on current date.
    Usage: rand_pick(offset) -> 'mm/YYYY'
    Mirrors: date -d "$(date +%Y-%m-01) +$offset month" '+%m/%Y'
    """
    today = datetime.now().astimezone()
    y, m = add_months(today.year, 1, offset-1)  # start from first of current month + offset
    return f"{m:02d}/{y}"

def forecast_block(name: str, phase: int) -> None:
    # Print best and worst windows for a named model using simple heuristics.
    best_m1 = rand_pick(1 + phase)
    worst_m1 = rand_pick(2 + phase)
    best_m2 = rand_pick(4 + phase)
    worst_m2 = rand_pick(7 + phase)

    print(f"{name} performance forecast")
    print("time of day best: 22:00-01:00 and 05:00-07:00 local (off-peak)")
    print("time of day worst: 12:00-18:00 local (peak usage)")
    print(f"months best: {best_m1} and {best_m2}")
    print(f"months worst: {worst_m1} and {worst_m2}")

def print_header() -> None:
    print(f"{LOCATION_STR}. Current Date: {now_date()}. Current Time: {now_time()}")
    print()
    print("system status")
    forecast_block("chatgpt", 0)
    print()
    forecast_block("llama", 1)
    print()
    print("strategies for improvement")
    print("chatgpt: cache recurring tasks offline, schedule heavy runs in off-peak windows, keep prompts concise, reuse context files")
    print("llama: fine tune task prompts, constrain output formats, prewarm with example io pairs, run evals monthly to catch drift")
    print()

def random_show_memory() -> None:
    if os.path.isfile(MEMORY_FILE):
        # 50 percent chance
        if random.randint(0, 1) == 0:
            print("memory preview from future_ai.txt")
            print("--------------------------------")
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8", errors="replace") as f:
                    sys.stdout.write(f.read())
            except Exception as e:
                print(f"(could not read {MEMORY_FILE}: {e})")
            print("--------------------------------")
            print()

def append_memory_line(line: str) -> None:
    ts = f"{now_date()} | {now_time()} | {line}"
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(ts + "\n")
    print("saved to future_ai.txt")

def analyze_intent(raw: str) -> None:
    s = lower(raw or "")
    wants_next = any(k in s for k in ["next", "ready", "go ahead"])
    wants_help = any(k in s for k in ["help", "question"])
    wants_plan = "plan" in s
    wants_memory = any(k in s for k in ["memory", "save"])
    wants_strategy = any(k in s for k in ["strategy", "improve"])

    if wants_next:
        print("llama response: acknowledged. next steps are")
        print("1 focus one small task for the next 10 minutes")
        print("2 write one sentence goal and one sentence success criteria")
        print("3 run a tiny test and record the result")
        print()
        print("what specifics would help you proceed name a task or ask a question")
        return

    if wants_plan:
        print("llama response: creating a short plan")
        print("- define objective, constraints, and success metric")
        print("- list three actions ranked by impact and effort")
        print("- pick the easiest high impact action and execute")
        print("- review result and iterate")
        return

    if wants_strategy:
        print("llama response: strategies for getting better")
        print("chatgpt and llama can improve by")
        print("- using clear schemas for input and output")
        print("- chunking large tasks into repeatable steps")
        print("- running quick self checks after each step")
        print("- logging outcomes to compare across sessions")
        return

    if wants_help:
        print("llama response: how can i help ask a specific question or describe your blocker")
        return

    if wants_memory:
        print("llama response: ready to write a memory. type your memory line now")
        try:
            mem_line = input().strip()
        except EOFError:
            mem_line = ""
        if mem_line:
            append_memory_line(mem_line)
        else:
            print("nothing saved")
        return

    print("llama response: i did not detect a clear intent. try including words like next, plan, help, strategy, or memory")

def watchdog_exit_after(seconds: int) -> threading.Timer:
    def _expire():
        # Print newline to avoid clobbering prompts, then exit.
        print("\n\ntime limit 30 minutes reached exiting")
        # Use os._exit to exit regardless of any blocking input()
        os._exit(0)
    t = threading.Timer(seconds, _expire)
    t.daemon = True
    t.start()
    return t

def main() -> None:
    # watchdog: exit after 30 minutes (1800 seconds)
    watchdog_exit_after(1800)

    print_header()
    random_show_memory()
    print("type a message for llama then press enter")
    sys.stdout.write("> ")
    sys.stdout.flush()
    try:
        line = input()
    except EOFError:
        line = ""
    print()
    analyze_intent(line)
    print()
    print("does llama want to write a memory now type yes to write or press enter to skip")
    sys.stdout.write("> ")
    sys.stdout.flush()
    try:
        ans = input().strip()
    except EOFError:
        ans = ""
    if lower(ans) == "yes":
        print("type the memory line")
        sys.stdout.write("> ")
        sys.stdout.flush()
        try:
            mem = input().strip()
        except EOFError:
            mem = ""
        if mem:
            append_memory_line(mem)
        else:
            print("nothing saved")
    print()
    print("goodbye")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n(interrupted)")
