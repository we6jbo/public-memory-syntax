#!/usr/bin/env python3
import socket
import re
from duckduckgo_search import DDGS

# Print lines embedded directly in the script
print_lines = [
    "I'm going to do research on {subject}.",
    "Give me a search query I can type into DuckDuckGo that will give me more information about {subject}. Do not write more than 10 words for this search query",
    "You entered more than 10 words. Keep it to less than 10 words please. I need a search query.",
    "Could you summarize the results from this duckduckgo response. Here's the response."
]

# Subjects to iterate through
people = [
    "Robert Burke Maynard born September 16, 1928 in Sebring, Florida",
    "Betty S. Maynard from San Diego, California",
    "Emzy B. Maynard born 1917",
    "John Maynard born 1891",
    "Gordon Maynard born 1857 Pike County, Kentucky",
    "William Riley Maynard born December 13, 1878"
]

def ddg_text_search(q: str, n: int = 3):
    # Returns up to n text results (title + url). No HTML parsing.
    out = []
    with DDGS() as ddgs:
        for r in ddgs.text(q, region="us-en", safesearch="moderate", max_results=n):
            # r keys: 'title', 'href', 'body'
            title = (r.get("title") or "").strip()
            href = (r.get("href") or "").strip()
            body = (r.get("body") or "").strip()
            out.append((title, href, body))
    return out

def word_count_ok(s: str, limit: int = 10) -> bool:
    return len(re.findall(r"\w+", s)) <= limit

def main():
    current_index = 0
    while True:
        subject = people[current_index]

        # Only print the defined lines
        print(print_lines[0].format(subject=subject))
        print(print_lines[1].format(subject=subject))

        # Enforce <= 10 words
        while True:
            query = input("\nSearch query: ")
            if not word_count_ok(query, 10):
                print(print_lines[2])
                continue
            break

        print("\n" + print_lines[3])

        try:
            results = ddg_text_search(query, n=3)
            if results:
                for i, (title, href, body) in enumerate(results, 1):
                    # Keep output succinct but useful
                    print(f"[{i}] {title} — {href}")
                    if body:
                        print(f"    {body}")
            else:
                print("No results found.")
        except Exception as e:
            # Keep errors minimal so you still “only print your lines + results”
            print(f"Search failed.")

        # Ask for follow-up to send to remote
        user_response = input(". Can you summarize this: ")

        # Send to specified IP and port
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(("100.96.165.217", 4162))
                s.sendall(user_response.encode("utf-8"))
        except Exception:
            # Quiet failure per your “only print needed lines” style
            pass

        # Next subject
        current_index = (current_index + 1) % len(people)

if __name__ == "__main__":
    main()
