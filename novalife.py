#!/usr/bin/env python3
import time
import urllib.request
import os
from datetime import datetime

ALIAS_NAME = "Novalife"
REAL_NAME = "Jeremiah O'Neal"
BIRTH_DATE = "03/24/1981"
LOCATION = "Clairemont, San Diego, CA"
TASK_URL = "https://raw.githubusercontent.com/we6jbo/public-memory-syntax/refs/heads/main/task_list"
LOCAL_TASK_FILE = os.path.expanduser("~/neuralnexus/novalife_tasks.txt")

def introduce():
    print(f"👋 Hi, my name is {ALIAS_NAME} (Alias).")
    print(f"My real name is {REAL_NAME}.")
    print(f"I was born {BIRTH_DATE} in San Diego, CA.")
    print(f"I currently live in {LOCATION}.\n")

def download_tasks():
    try:
        urllib.request.urlretrieve(TASK_URL, LOCAL_TASK_FILE)
        print(f"✅ Task list downloaded to {LOCAL_TASK_FILE}")
        return True
    except Exception as e:
        print(f"⚠️ Could not download task list: {e}")
        return False

def do_tasks():
    try:
        with open(LOCAL_TASK_FILE, "r") as f:
            tasks = [line.strip() for line in f if line.strip()]
        if not tasks:
            print("📭 No tasks to complete.")
            return
        print(f"📋 {len(tasks)} tasks loaded.")
        for task in tasks:
            print(f"🛠️ Working on task: {task}")
            filename = os.path.basename(task)
            try:
                
                urllib.request.urlretrieve(url, filename)
                result = subprocess.run(["python3", filename])
                if result.returncode != 0:
                    print(f"❌ Error running {filename}:")
                    print(result.stderr)
                else:
                    print(f"✅ Task {filename} completed successfully."
            except Exception as e:
                print(f"⚠️ Failed to process {task}: {e}")
            time.sleep(3)
        print("✅ All tasks completed.")
    except Exception as e:
        print(f"❌ Failed to read or process tasks: {e}")

def main():
    introduce()
    if download_tasks():
        do_tasks()
    pass_file = os.path.expanduser("~/pass.txt")
    if os.path.exists(pass_file):
        print("😴 Novalife will now rest for a while (1–2 hours)...")
        os.remove(pass_file)
        time.sleep(60 * 60 * 1.5)  # Sleep for 1.5 hours
    else:
        print("No pass.txt found — skipping sleep.")

if __name__ == "__main__":
    main()
