#!/usr/bin/env python3

import os

MEMORY_DIR = os.path.expanduser("~/AIMemories")
MEMORY_FILE = os.path.join(MEMORY_DIR, "AIMemory.txt")

def write_to_memory(text):
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(MEMORY_FILE, "a") as f:
        f.write(text.strip() + "\n")
