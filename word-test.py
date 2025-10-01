import random

def main():
    # Define 100 "trigger words" including "working" and "good"
    trigger_words = [
        "working", "good", "happy", "sun", "tree", "sky", "blue", "green", "calm",
        "peace", "kind", "hope", "faith", "smile", "strong", "focus", "clear", "bright",
        "safe", "home", "light", "star", "goal", "dream", "path", "walk", "run", "rest",
        "flow", "grow", "shine", "energy", "time", "health", "love", "brave",
        "trust", "wise", "warm", "joy", "play", "learn", "build", "create",
        "think", "power", "truth", "listen", "share", "act", "drive", "help",
        "hero", "bold", "rise", "win", "spark", "guide", "hopeful", "brightly",
        "dreamer", "pathway", "runner", "restful", "flower", "shining",
        "timely", "lovely", "bravery", "trusted", "wisely", "joyful",
        "playful", "learner", "builder", "creator", "thinker", "truthful",
        "listener", "sharer", "active", "spirit", "calmer", "focusful",
        "faithful", "clearer", "starlit", "goalpost", "homeward",
        "grower", "flowing", "energyful", "safehouse", "warmth",
        "sparkle", "guardian", "helper", "victory", "healer"
    ]

    # First fixed prompts
    response = input("Please say working: ").lower().strip()
    if "working" in response:
        print("Thank you, ending now.")
        return

    response = input("Please say good: ").lower().strip()
    if "good" in response:
        print("Thank you, ending now.")
        return

    # Randomized prompts loop
    while True:
        random_word = random.choice(trigger_words)
        response = input(f"Please enter a word: {random_word} ").lower().strip()
        if random_word in response:
            print(f"Correct word '{random_word}' detected. Ending now.")
            break

if __name__ == "__main__":
    main()
