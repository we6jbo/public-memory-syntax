#!/usr/bin/env python3

VERSION = "v0.4"


import os
import shutil
import sys
import time
import random
import urllib.request
import subprocess
from datetime import datetime

#change task to recovery
#change novalife to recovery
TASK_URL = "https://raw.githubusercontent.com/we6jbo/public-memory-syntax/refs/heads/main/recovery_list"
LOCAL_TASK_FILE = os.path.expanduser("~/neuralnexus/recovery_tasks.txt")

# === Setup: version backup ===
def copy_self_if_missing():
    target_dir = os.path.expanduser("~/neuralnexus")
    target_path = os.path.join(target_dir, "familysearch_version.py")
    current_path = os.path.abspath(sys.argv[0])

    os.makedirs(target_dir, exist_ok=True)
    if not os.path.exists(target_path):
        shutil.copy(current_path, target_path)
        #print(f"📁 Backed up version {VERSION} to {target_path}")

# === One-time seed from Seed_scri.txt ===
def seed_family_tree_structure():
    seed_path = os.path.expanduser("~/Seed_scri.txt")
    if not os.path.exists(seed_path):
        #print("⚠️ Seed script not found, skipping seeding step.")
        return

    with open(seed_path, "r") as f:
        for line in f:
            if line.startswith("mkdir"):
                path = line.split("mkdir", 1)[1].strip()
                normalized_path = os.path.expanduser(path).lower()
                try:
                    os.makedirs(normalized_path, exist_ok=True)
                except Exception as e:
                    i = 1
# === Globals ===
START_TIME = time.time()

def get_familytree_path():
    test_path = "/tmp/Test_Jul14/FamilyTree"
    if os.path.exists(test_path):
        #print("⚙️  Using override path: /tmp/Test_Jul14/FamilyTree")
        return test_path
    return os.path.expanduser("~/FamilyTree")

FAMILYTREE_ROOT = get_familytree_path()
RESEARCH_LOG = os.path.join(FAMILYTREE_ROOT, "research.txt")

# === Utility functions ===
def strip_to_alpha(text):
    return ''.join(c for c in text if c.isalpha())

def normalize_name(name):
    return name.lower().replace(" ", "_").replace("'", "")

def delay_and_check_time():
    global START_TIME
    if time.time() - START_TIME > 2 * 3600:
        print("I am going to take a break on researching my tree. I will come back to this later.")
        exit(0)
    time.sleep(random.randint(3, 14))

def is_valid_name(name):
    return len(name.split()) == 2

def get_quendor_response(prompt):
    #print(f"{prompt}")
    return input("").strip()
    #This is where the input from quendor goes.
def say_to_quendor(message):
    print(f"{message}")

def write_info_and_log(info_path, name, content):
    os.makedirs(os.path.dirname(info_path), exist_ok=True)
    with open(info_path, "w") as f:
        f.write(content)
    with open(RESEARCH_LOG, "a") as log:
        log.write(f"\n{name}:\n{content}\n")

def extract_name_from_path(path):
    name = os.path.basename(path)
    return name.replace("_male", "").replace("_female", "").replace("_", " ")

def ensure_family_folder(parent, name, gender):
    norm = normalize_name(name)
    subfolder = os.path.join(parent, f"{norm}_{gender}")
    os.makedirs(subfolder, exist_ok=True)
    return subfolder

#!/usr/bin/env python3


def introduce():
    print(f"I am working on a family tree. I am going to download something. Hold on. There may be errors.\n")

def download_tasks():
    try:
        #urllib.request.urlretrieve(task, filename)
        urllib.request.urlretrieve(TASK_URL, LOCAL_TASK_FILE)
        #print(f"✅ Task list downloaded to {LOCAL_TASK_FILE}")
        return True
    except Exception as e:
        #print(f"⚠️ Could not download task list: {e}")
        return False

def do_tasks():
    try:
        with open(LOCAL_TASK_FILE, "r") as f:
            tasks = [line.strip() for line in f if line.strip()]
        if not tasks:
            #print("📭 No tasks to complete.")
            return
        #print(f"📋 {len(tasks)} tasks loaded.")
        for task in tasks:
            #print(f"🛠️ Working on task: {task}")
            filename = os.path.basename(task)
            urllib.request.urlretrieve(task, filename)
            try:
                
                urllib.request.urlretrieve(task, filename)
                result = subprocess.run(["python3", filename])
                if result.returncode != 0:
                    #print(f"❌ Error running {filename}:")
                    #print(result.stderr)
                    i = 1
                else:
                    #print(f"✅ Task {filename} completed successfully.")
                    i = 1
            except Exception as e:
                #print(f"⚠️ Failed to process {task}: {e}")
                i = 1
            time.sleep(3)
        #print("✅ All tasks completed.")
    except Exception as e:
        #print(f"❌ Failed to read or process tasks: {e}")
        i = 1


def recovery_stub(context=""):
    #print("🛠️ Entering recovery stub...")
    if context:
        #print(f"🔍 Context: {context}")
        i = 1
    ############## BEGIN CUSTOM CODE BLOCK ##############
    # Place your custom recovery or fallback logic here
    introduce()
    if download_tasks():
        do_tasks()

    ############## END CUSTOM CODE BLOCK ##############
    time.sleep(2)
    #print("✅ Exiting recovery stub. Continuing exploration...\n")

def get_valid_name(prompt, role="person"):
    attempts = 0
    while attempts < 5:
        name = get_quendor_response(prompt)
        if is_valid_name(name):
            return name
        reasoning = random.choice([
            "I’m trying to confirm both first and last names to organize lineage.",
            f"This helps ensure we link the correct {role} to their branch.",
            "Without two names, I can’t tell who we’re referring to.",
            "That doesn’t look like a full name. Please enter both names.",
            "Let’s try that again—just the full name please."
        ])
        print(f"{reasoning}")
        #print("Quendor, I only need a first and last name.")
        attempts += 1
    fallback = "Doug ONeal" if role == "father" else "Natalie Maynard"
    #print(f"⚠️ Too many failed attempts. Using fallback name: {fallback}")
    return fallback

def explore_person(person_path):
    # Random chance to return to root
    if random.randint(1, 4) == 1:
        root = FAMILYTREE_ROOT
        subdirs = [d for d in os.listdir(root) if d.endswith(("_male", "_female"))]
        if subdirs:
            explore_person(os.path.join(root, random.choice(subdirs)))
            return

    delay_and_check_time()
    person_name = extract_name_from_path(person_path)
    say_to_quendor(f"learn_about {person_name}")
    delay_and_check_time()

    info_path = os.path.join(person_path, "info.txt")
    if not os.path.exists(info_path):
        response = get_quendor_response(f"What do you know about {person_name}?")
        write_info_and_log(info_path, person_name, response)
        delay_and_check_time()

    father = get_valid_name("Quendor, please give me the exact name of the father", role="father")
    father_path = ensure_family_folder(person_path, father, "male")

    mother = get_valid_name("Quendor, please give me the exact name of the mother", role="mother")
    mother_path = ensure_family_folder(person_path, mother, "female")

    delay_and_check_time()
    next_dir = random.choice([father_path, mother_path])
    explore_person(next_dir)

# === Main Entry ===
def main():
    os.makedirs(FAMILYTREE_ROOT, exist_ok=True)
    if not os.path.exists(RESEARCH_LOG):
        open(RESEARCH_LOG, "w").close()
    explore_person(os.path.join(FAMILYTREE_ROOT, "jeremiah_oneal_male"))

if __name__ == "__main__":
    copy_self_if_missing()
    seed_family_tree_structure()
    main()
