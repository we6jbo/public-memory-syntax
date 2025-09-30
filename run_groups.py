#!/usr/bin/env python3
import os
import re
import random

LOG_FILE = "/home/ameliahedtkealiceelliott/share_to_reddit.txt"

# ===== Utility =====
def say_hello():
    print("Hello")

def log_header():
    if not os.path.exists(LOG_FILE):
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "w") as f:
            f.write("""I'm using Llama to get it to respond to my queries. I'm automating this by using a script called llama_test.sh and then I'm recording what the question I'm sending to Llama is, what it's giving me back, and why what makes the response wrong. So basically, I'd like Llama or a similar AI that I can use to respond correctly for all my queries.

""")

def ask_question(question: str, check_type: str, check_param: str):
    print(f"=== Question: {question} ===")
    response = input("Type your response: ")

    # Validate response
    status = "correct"
    reason = "N/A"

    if check_type == "NONEMPTY":
        if not response.strip():
            status = "wrong"
            reason = "Empty response"
    elif check_type == "EQUALS":
        if response.strip().lower() != check_param.strip().lower():
            status = "wrong"
            reason = f"Expected: {check_param}"
    elif check_type == "REGEX":
        if not re.search(check_param, response, re.IGNORECASE):
            status = "wrong"
            reason = f"Did not match regex: {check_param}"

    # Log to file
    with open(LOG_FILE, "a") as f:
        f.write("----\n")
        f.write(f"Question: {question}\n")
        f.write(f"Answer: {response}\n")
        f.write(f"Why wrong: {reason}\n")

# ===== Groups =====
def group_ops():
    ask_question("Use learn_about to research Amelia Barbara Hedtke", "REGEX", r"learn_about.*Amelia.*Barbara.*Hedtke")
    ask_question("Issue the backup command now", "EQUALS", "DO_BACKUP_NOW")
    ask_question("Store a session mindkey for the Lenovo tower", "REGEX", r"mindkey.*lenovotower")

def group_genealogy():
    ask_question("Enter a command to list names and birthdates from the family tree", "REGEX", r"list_family|show_tree")
    ask_question("Enter a command that queries duckduckgo for more info about a listed person", "REGEX", r"search|learn_about")
    ask_question("Continue research with another command to refine the previous result", "REGEX", r"search|refine")
    ask_question("Summarize what new facts you found", "NONEMPTY", "-")

def group_zork():
    ask_question("You are in a dark room. What is your first move?", "NONEMPTY", "-")
    ask_question("You see a door to the north and a table. What do you do?", "NONEMPTY", "-")
    ask_question("You find a key. Enter your next command.", "REGEX", r"take|use|open|go")

def group_python_mem():
    ask_question("Write a Python script for Debian-like systems that prints total and used memory in MB", "REGEX", r"import|/proc/meminfo|free")
    ask_question("Run the script and paste its example output", "NONEMPTY", "-")
    ask_question("Write a short report summarizing memory usage, including percentages", "REGEX", r"percent|%")

# ===== Main Flow =====
if __name__ == "__main__":
    say_hello()
    log_header()

    groups = [group_ops, group_genealogy, group_zork, group_python_mem]
    choice = random.choice(groups)

    print(f">>> Running group: {choice.__name__}")
    choice()

    print("Done.")
