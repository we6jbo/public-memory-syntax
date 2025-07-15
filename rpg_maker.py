#!/usr/bin/env python3
import os
import sys
import time
from datetime import datetime, timedelta

# Globals
RPG_ROOT = os.path.expanduser("~/rpg")
start_time = datetime.now()
score = 0

def ensure_rpg_dir():
    os.makedirs(RPG_ROOT, exist_ok=True)
    os.chdir(RPG_ROOT)

def has_time_expired():
    return datetime.now() > start_time + timedelta(hours=1)

def print_quendor():
    if has_time_expired():
        print("Session expired. Goodbye Quendor.")
        sys.exit(0)
    print("Hello Quendor,")

def ask_ai(prompt):
    return input(f"[AI] {prompt}: ").strip()

def description():
    if not os.path.exists("room.txt"):
        desc = ask_ai("Describe the room")
        with open("room.txt", "w") as f:
            f.write(desc + "\n")
    with open("room.txt", "r") as f:
        print("\n--- Room Description ---")
        print(f.read())

def choice():
    while True:
        action = ask_ai("What do you want to do? Please keep it between 4 and 9 words.")
        if len(action.split()) <= 10:
            break
        print("That is too long. Please keep it under 10 words but at least four words.")
    
    # Append to room.txt
    with open("room.txt", "a") as f:
        f.write("Do you want to " + action + "\n")

    # Create and cd into dir
    new_dir = "_".join(action.split())
    os.makedirs(new_dir, exist_ok=True)
    os.chdir(new_dir)

def step_back(levels=2):
    for _ in range(levels):
        if os.getcwd() != RPG_ROOT:
            os.chdir("..")

def score_up():
    global score
    score += 1
    with open(f"{score}.txt", "w") as f:
        f.write(f"Score: {score}\n")

def play():
    os.chdir(RPG_ROOT)
    while True:
        print_quendor()
        if os.path.exists("room.txt"):
            with open("room.txt", "r") as f:
                print(f.read())

        action = ask_ai("What do you want to do?")
        new_dir = "_".join(action.split())
        if os.path.isdir(new_dir):
            os.chdir(new_dir)
            if os.path.exists("room.txt"):
                with open("room.txt", "r") as f:
                    print(f.read())
            txt_files = [f for f in os.listdir() if f.endswith(".txt") and f[:-4].isdigit()]
            existing_scores = sorted([int(f[:-4]) for f in txt_files])
            if score not in existing_scores:
                print("🏆 You found a score point! (+1)")
                score_up()

def main():
    ensure_rpg_dir()
    print_quendor()

    # Opening narrative
    print(
        "\nYour eyes open slowly.\n"
        "There is no sun in the sky, only light — pale, diffuse, the color of bleached bone. "
        "The sand beneath you is cold and dry, stretched endlessly in every direction except one: "
        "the far-off rise of jagged mountains.\n"
        "You sit up. Wind brushes against your cheek, carrying with it the scent of salt and something older—like stone left buried too long.\n"
        "There is no one here.\nNo footprints.\nNo birds.\nNo wreckage.\nJust you.\nAnd the island.\n"
    )

    description()
    
    for _ in range(5):
        choice()
        description()

    step_back(5)
    description()
    score_up()

    step_back(5)
    description()

    play()

if __name__ == "__main__":
    main()
