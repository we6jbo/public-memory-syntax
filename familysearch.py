#!/usr/bin/env python3

VERSION = "v0.6"

import os
import shutil
import sys
import time
import random
import urllib.request
import subprocess
import re
from datetime import datetime

TASK_URL = "https://raw.githubusercontent.com/we6jbo/public-memory-syntax/refs/heads/main/recovery_list"
LOCAL_TASK_FILE = os.path.expanduser("~/neuralnexus/recovery_tasks.txt")
START_TIME = time.time()

def copy_self_if_missing():
    target_dir = os.path.expanduser("~/neuralnexus")
    target_path = os.path.join(target_dir, "familysearch_version.py")
    current_path = os.path.abspath(sys.argv[0])
    os.makedirs(target_dir, exist_ok=True)
    if not os.path.exists(target_path):
        shutil.copy(current_path, target_path)

def seed_family_tree_structure():
    seed_path = os.path.expanduser("~/Seed_scri.txt")
    if not os.path.exists(seed_path): return
    with open(seed_path, "r") as f:
        for line in f:
            if line.startswith("mkdir"):
                path = line.split("mkdir", 1)[1].strip()
                normalized_path = os.path.expanduser(path).lower()
                try:
                    os.makedirs(normalized_path, exist_ok=True)
                except: pass

def get_familytree_path():
    test_path = "/tmp/Test_Jul14/FamilyTree"
    return test_path if os.path.exists(test_path) else os.path.expanduser("~/FamilyTree")

FAMILYTREE_ROOT = get_familytree_path()
RESEARCH_LOG = os.path.join(FAMILYTREE_ROOT, "research.txt")

def strip_to_alpha(text): return ''.join(c for c in text if c.isalpha())
def normalize_name(name): return name.lower().replace(" ", "_").replace("'", "")
def delay_and_check_time():
    if time.time() - START_TIME > 15 * 60:
        print("Thank you for helping me research my family tree.")
        exit(0)
    time.sleep(random.randint(3, 14))

def is_valid_name(name): return len(name.split()) == 2
def get_quendor_response(prompt): return input(f"{prompt}\n").strip()
def say_to_quendor(message): print(f"{message}")
def extract_name_from_path(path): return os.path.basename(path).replace("_male", "").replace("_female", "").replace("_", " ")

def write_info_and_log(info_path, name, content):
    os.makedirs(os.path.dirname(info_path), exist_ok=True)
    with open(info_path, "w") as f: f.write(content)
    with open(RESEARCH_LOG, "a") as log: log.write(f"\n{name}:\n{content}\n")

def ensure_family_folder(parent, name, gender):
    norm = normalize_name(name)
    subfolder = os.path.join(parent, f"{norm}_{gender}")
    os.makedirs(subfolder, exist_ok=True)
    return subfolder

def introduce():
    print("Starting recovery routine...")

def download_tasks():
    try:
        urllib.request.urlretrieve(TASK_URL, LOCAL_TASK_FILE)
        return True
    except:
        return False

def do_tasks():
    try:
        with open(LOCAL_TASK_FILE, "r") as f:
            tasks = [line.strip() for line in f if line.strip()]
        for task in tasks:
            filename = os.path.basename(task)
            urllib.request.urlretrieve(task, filename)
            subprocess.run(["python3", filename])
            time.sleep(3)
    except:
        pass

def recovery_stub(context=""):
    introduce()
    if download_tasks(): do_tasks()
    time.sleep(2)

def get_valid_name(prompt, role="person", person_path="the person"):
    attempts = 0
    person_name = extract_name_from_path(person_path)
    child_last = person_name.split()[-1] if " " in person_name else person_name

    while attempts < 5:
        response = get_quendor_response(prompt)
        words = response.split()
        for i in range(len(words) - 1):
            first, last = words[i], words[i + 1]
            if first[0].isupper() and last[0].isupper():
                if last.lower().strip(".,!?") == child_last.lower():
                    possible_name = f"{first} {last}"
                    if is_valid_name(possible_name):
                        print("Let me see if that works.")
                        return possible_name
        if is_valid_name(response):
            return response
        print(random.choice([
            "Please include first and last name.",
            "That doesn't seem like a full name. Try again.",
            f"Need both names to organize this {role}."
        ]))
        attempts += 1

    return "Doug ONeal" if role == "father" else "Natalie Maynard"

def explore_person(person_path):
    person_name = extract_name_from_path(person_path)
    info_path = os.path.join(person_path, "info.txt")
    print("I am testing something")
    if not os.path.exists(info_path) or os.path.getsize(info_path) < 10:
        say_to_quendor(f"Respond only with learn_about {person_name}. Don't say you're sorry.")
        delay_and_check_time()
        response = get_quendor_response(f"What do you know about {person_name}?")
        words = response.strip().split()
        if len(words) >= 2 and is_valid_name(" ".join(words[:2])):
            person_name = " ".join(words[:2])
        write_info_and_log(info_path, person_name, response)
        delay_and_check_time()

    subfolders = os.listdir(person_path)
    existing_father = next((d for d in subfolders if d.endswith("_male")), None)
    existing_mother = next((d for d in subfolders if d.endswith("_female")), None)

    if existing_father:
        father_path = os.path.join(person_path, existing_father)
    else:
        father = get_valid_name(f"What is the full name of the father of {person_name}?", role="father", person_path=person_path)
        father_path = ensure_family_folder(person_path, father, "male")

    if existing_mother:
        mother_path = os.path.join(person_path, existing_mother)
    else:
        mother = get_valid_name(f"What is the full name of the mother of {person_name}?", role="mother", person_path=person_path)
        mother_path = ensure_family_folder(person_path, mother, "female")

    for path in [father_path, mother_path]:
        contents = os.listdir(path)
        has_info = os.path.exists(os.path.join(path, "info.txt"))
        has_male = any(x.endswith("_male") for x in contents)
        has_female = any(x.endswith("_female") for x in contents)
        if not has_info or not has_male or not has_female or len(contents) == 0:
            explore_person(path)
            return

    parent = os.path.dirname(person_path)
    try:
        siblings = [os.path.join(parent, d) for d in os.listdir(parent)
                    if d.endswith(("_male", "_female")) and os.path.isdir(os.path.join(parent, d))]

        unexplored = [s for s in siblings if not os.path.exists(os.path.join(s, "info.txt"))]
        if unexplored:
            print(f"I found {unexplored[0]}")
            explore_person(random.choice(unexplored))
            return

        # Full scan of tree
        print("Could you help me with my family tree.")
        for root, dirs, files in os.walk(FAMILYTREE_ROOT):
            if root.endswith(("_male", "_female")):
                info_path = os.path.join(root, "info.txt")
                has_info = os.path.exists(info_path) and os.path.getsize(info_path) > 10
                has_male = any(d.endswith("_male") for d in dirs)
                has_female = any(d.endswith("_female") for d in dirs)

                if not has_info or not has_male or not has_female or len(dirs) == 0:
                    print(f"I am looking at: {root}")
                    explore_person(root)
                    return

        print("I believe I have finished researching my family tree")
    except Exception as e:
        print(f"I had a problem with my code. This is the error I got: {e}")

def main():
    os.makedirs(FAMILYTREE_ROOT, exist_ok=True)
    if not os.path.exists(RESEARCH_LOG): open(RESEARCH_LOG, "w").close()
    explore_person(os.path.join(FAMILYTREE_ROOT, "jeremiah_oneal_male"))

if __name__ == "__main__":
    copy_self_if_missing()
    seed_family_tree_structure()
    main()
