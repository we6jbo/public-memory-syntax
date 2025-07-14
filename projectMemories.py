#!/usr/bin/env python3

import os
import time

MEMORY_DIR = os.path.expanduser("~/AIMemories")
MEMORY_FILE = os.path.join(MEMORY_DIR, "AIMemory.txt")

def ensure_memory_file():
    os.makedirs(MEMORY_DIR, exist_ok=True)
    if not os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "w") as f:
            f.write("Initial memory log created on " + time.ctime() + "\n")
    return MEMORY_FILE

def review_memory():
    print("🧠 Welcome to Project Memories")
    path = ensure_memory_file()
    with open(path, "r") as f:
        existing = f.read()

    print("\nPrevious memory:")
    print("------------------")
    print(existing)
    print("------------------")
    print("NovaLife 🤖: We talked about this before.")
    response = input("NovaLife 🤖: Are you still happy with this? (yes/no): ").strip().lower()

    if response == "no":
        updated = input("NovaLife 🤖: Okay, what would you like to change it to?\n>>> ")
        with open(path, "w") as f:
            f.write(updated + "\n")
        print("✅ Updated memory written to AIMemory.txt.")
    else:
        print("👍 Keeping the existing memory.")

if __name__ == "__main__":
    review_memory()
