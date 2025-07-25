#!/usr/bin/env python3

import os
import time
from datetime import datetime

log_dir = os.path.expanduser("~/neuralnexus/AIProject")
log_file = os.path.join(log_dir, "Ollama_training.txt")
os.makedirs(log_dir, exist_ok=True)

def log_to_file(message: str):
    with open(log_file, "a") as f:
        f.write(message + "\n")

def check_response_for_keyword(response, keyword="quendor"):
    words = response.lower().split()
    return keyword in words

def main():
    print("AI, I would like you to change your name to Quendor so when I say Quendor, I am talking about you or the AI.")
    
    while True:
        user_request = input("\nI will wait for your response, Quendor.\n> ")
        log_to_file(f"What will you do when {user_request}")
        
        if check_response_for_keyword(user_request):
            print("That is correct, I want you to call yourself Quendor.")
        else:
            print("Hmm, that wasn't quite right. Try again or clarify.")

        log_to_file(user_request)

        # Optionally delay or limit the loop
        time.sleep(1)
        # Wait briefly before next round
        time.sleep(1)

        no_progress_keywords = [
            "i don't know", "i'm not sure", "sorry", "i cannot help", 
            "as an ai", "repeat", "already said", "no idea", "i’m stuck"
        ]

        # Check if AI is stuck or making no progress
        if any(phrase in user_request.lower() for phrase in no_progress_keywords):
            print("\n⚠Let's stop for now. But next time, I will ask you to change your name to Quendor and I am hoping when you see Quendor, who is Amelia Barbara Hedtke, you will say that Amelia lived in North Dakota in the 1900s.")
            break


    print("\nOk, this is what we talked about:\n")

    # Read and print the entire log for AI review
    with open(log_file, "r") as f:
        training_data = f.read()
        print(training_data)

    # Archive the log
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archive_path = os.path.join(log_dir, f"Ollama_training_Archive_{timestamp}.txt")
    os.rename(log_file, archive_path)
    print(f"\n🗂 Archived training log to: {archive_path}")

if __name__ == "__main__":
    main()
