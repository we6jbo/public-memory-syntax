import socket
import requests
import re

# Load print statements from file
with open("Print-statements.txt", "r") as f:
    print_lines = [line.strip() for line in f if line.strip()]

# Names and people to iterate over
people = [
    "Robert Burke Maynard born September 16, 1928 in Sebring, Florida",
    "Betty S. Maynard",
    "Emzy B. Maynard born 1917",
    "John Maynard born 1891",
    "Gordon Maynard born 1857 Pike County, Kentucky",
    "William Riley Maynard born December 13, 1878"
]

current_index = 0

while True:
    # Step 1: Print only allowed lines
    for line in print_lines:
        print(line)

    # Step 2: Ask user for search query
    while True:
        query = input("\nSearch query: ")
        if len(re.findall(r'\w+', query)) > 10:
            print("You entered more than 10 words. Keep it to less than 10 words please. I need a search query.")
        else:
            break

    # Step 3: Perform DuckDuckGo search
    print("\nCould you summarize the results from this duckduckgo response. Here's the response.")
    try:
        response = requests.get(f"https://duckduckgo.com/html/?q={requests.utils.quote(query)}")
        snippet = re.findall(r'<a.*?class="result__a".*?>(.*?)</a>', response.text)
        if snippet:
            for i, result in enumerate(snippet[:3], 1):
                print(f"[{i}] {re.sub('<.*?>', '', result)}")
        else:
            print("No results found.")
    except Exception as e:
        print(f"Search failed: {e}")

    # Step 4: Ask for user response to send to remote
    user_response = input("\nEnter a follow-up to send to 100.96.165.217:4162: ")

    # Step 5: Send to specified IP and port
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("100.96.165.217", 4162))
            s.sendall(user_response.encode('utf-8'))
            print("Sent successfully.")
    except Exception as e:
        print(f"Failed to send to server: {e}")

    # Step 6: Cycle to next person
    current_index = (current_index + 1) % len(people)
    print("\n--- NEXT SEARCH SUBJECT ---")
    print(f"I'm going to do research on {people[current_index]}\n")
