#!/usr/bin/env python3
import requests

def ask_ai(prompt):
    payload = {
        "model": "llama3",  # adjust if using another model name
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post("http://localhost:11434/api/generate", json=payload)
        return response.json().get("response", "").strip()
    except Exception as e:
        return f"[ERROR] Failed to contact AI: {e}"

if __name__ == "__main__":
    prompt = "AI, tell me about the 10th planet."
    print("🧠 Asking AI:", prompt)
    result = ask_ai(prompt)
    print("\n🤖 AI Response:")
    print(result)
