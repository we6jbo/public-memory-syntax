# identity_decoder.py

def load_definitions(filename="secret.txt"):
    definitions = {}
    try:
        with open(filename, "r") as file:
            for line in file:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    definitions[key.strip()] = value.strip()
    except FileNotFoundError:
        print(f"Error: '{filename}' not found.")
    return definitions

def decode_text(text, definitions):
    decoded_output = []
    words = text.split()
    for word in words:
        cleaned_word = word.strip(".,()—")  # remove punctuation
        if cleaned_word in definitions:
            decoded_output.append(f"{word} → {definitions[cleaned_word]}")
    return decoded_output

if __name__ == "__main__":
    secret_file = "secret.txt"
    input_text = ("Jul 23 I’m a deferred-init() in life’s link-state. "
                  "My protocol-shifts led from core-algorithm design into "
                  "cipher-flag moments, rhythm-loops, and encrypt-nodes. "
                  "Now I’m building my habit-chain by custom-sequence—secured by default.")

    definitions = load_definitions(secret_file)
    decoded_terms = decode_text(input_text, definitions)

    print("Decoded Terms:")
    for line in decoded_terms:
        print(line)
