#!/usr/bin/env python3
import socket
import re
from duckpy import Client

# --------------------- CONFIG ---------------------
print_lines = [
    "I'm going to do research on {subject}.",
    "Give me a search query I can type into DuckDuckGo that will give me more information about {subject}. Do not write more than 10 words for this search query",
    "You entered more than 10 words. Keep it to less than 10 words please. I need a search query.",
    "Could you summarize the results from this duckduckgo response. Here's the response."
]

people = [
    "Robert Burke Maynard born September 16, 1928 in Sebring, Florida",
    "Betty S. Maynard from San Diego, California",
    "Emzy B. Maynard born 1917",
    "John Maynard born 1891",
    "Gordon Maynard born 1857 Pike County, Kentucky",
    "William Riley Maynard born December 13, 1878"
]

DDG_RESULTS = 5
REMOTE_IP = "100.96.165.217"
REMOTE_PORT = 4162
# ---------------------------------------------------

def word_count_ok(s: str, limit: int = 10) -> bool:
    return len(re.findall(r"\w+", s)) <= limit

def ddg_text_search(query: str, n: int = DDG_RESULTS):
    """Run a DuckDuckGo query that prefers exact-match results for names."""
    ddg = Client()
    results = ddg.search(query)
    # if nothing found and the query isn't quoted, retry quoted version
    if not results and not (query.startswith('"') and query.endswith('"')):
        results = ddg.search(f'"{query}"')
    return results[:n]

def main():
    current_index = 0
    while True:
        subject = people[current_index]
        print(print_lines[0].format(subject=subject))
        print(print_lines[1].format(subject=subject))

        # Enforce <=10 words
        while True:
            query = input("\nSearch query: ").strip()
            if not word_count_ok(query, 10):
                print(print_lines[2])
                continue
            break

        print("\n" + print_lines[3])

        try:
            results = ddg_text_search(query, n=DDG_RESULTS)
            if results:
                for i, r in enumerate(results, 1):
                    title = r.get("title", "")
                    url = r.get("url", "")
                    desc = r.get("description", "")
                    print(f"[{i}] {title}\n   {url}\n   {desc}\n")
            else:
                print("No results found.")
        except Exception as e:
            print(f"Search failed: {e}")

        # Ask for follow-up to send to remote
        user_response = input(". Can you summarize this: ")

        # Send to specified IP and port
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((REMOTE_IP, REMOTE_PORT))
                s.sendall(user_response.encode("utf-8"))
        except Exception as e:
            print(f"Failed to send to server: {e}")

        current_index = (current_index + 1) % len(people)
        print("\n--- NEXT SEARCH SUBJECT ---\n")

if __name__ == "__main__":
    main()
