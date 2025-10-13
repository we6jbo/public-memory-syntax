#!/usr/bin/env python3
import socket
import re
import html
import urllib.parse
import urllib.request

# Try to import duckpy if present (optional)
try:
    from duckpy import Client as DuckClient
except Exception:
    DuckClient = None

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
TIMEOUT = 12
# ---------------------------------------------------

def word_count_ok(s: str, limit: int = 10) -> bool:
    return len(re.findall(r"\w+", s)) <= limit

def _ddg_html_search(query: str, n: int):
    """Fallback: query DuckDuckGo HTML endpoint and parse titles/urls/snippets."""
    url = "https://duckduckgo.com/html/"
    params = {"q": query}
    req = urllib.request.Request(
        url + "?" + urllib.parse.urlencode(params),
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/119.0 Safari/537.36"
        }
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        page = resp.read().decode("utf-8", errors="ignore")

    # crude parse of result blocks
    results = []
    # Each result has <a class="result__a" href="...">Title</a>
    link_re = re.compile(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.I)
    # Optional description nearby
    # result__snippet may appear after the link
    snippet_re = re.compile(r'<a[^>]*class="result__a"[^>]*>.*?</a>.*?<a[^>]*class="result__snippet"[^>]*>(.*?)</a>|'
                            r'<a[^>]*class="result__a"[^>]*>.*?</a>.*?<div[^>]*class="result__snippet"[^>]*>(.*?)</div>',
                            re.I | re.S)

    links = link_re.findall(page)
    if not links:
        return []

    # get snippets aligned roughly by order (best-effort)
    snips = snippet_re.findall(page)
    flat_snips = []
    for a, b in snips:
        s = a if a else b
        # strip tags
        s = re.sub(r"<.*?>", "", s or "")
        flat_snips.append(html.unescape(s).strip())

    for i, (href, title_html) in enumerate(links[:n]):
        title = re.sub(r"<.*?>", "", title_html)
        title = html.unescape(title).strip()
        desc = flat_snips[i] if i < len(flat_snips) else ""
        results.append({"title": title, "url": href, "description": desc})
    return results

def ddg_text_search(query: str, n: int):
    """
    Prefer duckpy if available; retry quoted; then fallback to HTML.
    Returns list of dicts: {title,url,description}
    """
    # Attempt with duckpy (unquoted → quoted)
    if DuckClient is not None:
        try:
            ddg = DuckClient()
            r = ddg.search(query) or []
            if not r and " " in query and not (query.startswith('"') and query.endswith('"')):
                r = ddg.search(f'"{query}"') or []
            if r:
                out = []
                for item in r[:n]:
                    out.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "description": item.get("description", "")
                    })
                return out
        except Exception:
            pass

    # Fallback: HTML endpoint (quoted first, then unquoted)
    # Try quoted to force exact name matches like "betty maynard"
    try_order = []
    if " " in query and not (query.startswith('"') and query.endswith('"')):
        try_order = [f'"{query}"', query]
    else:
        try_order = [query]

    for q in try_order:
        try:
            r = _ddg_html_search(q, n)
            if r:
                return r
        except Exception:
            continue

    return []

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
        except Exception:
            print("No results found.")

        # Ask for follow-up to send to remote
        user_response = input(". Can you summarize this: ")

        # Send to specified IP and port
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((REMOTE_IP, REMOTE_PORT))
                s.sendall(user_response.encode("utf-8"))
        except Exception:
            # Silent if unreachable
            pass

        current_index = (current_index + 1) % len(people)
        print("\n--- NEXT SEARCH SUBJECT ---\n")

if __name__ == "__main__":
    main()
