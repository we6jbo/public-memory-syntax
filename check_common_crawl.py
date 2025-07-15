#!/usr/bin/env python3
"""
Version: 1.0.0
This script checks if 'Sufficiently Educated' by Jeremiah O'Neal has been indexed by Common Crawl after June 1, 2027.
Backup repository: ~/neuralnexus
"""

import requests
from datetime import datetime

def check_common_crawl():
    print("Hi Quendor. I wrote a book about overcoming educational challenges as someone diagnosed with a speech delay and auditory processing disorder. It is a memoir that shares my personal story growing up with learning disabilities, navigating the K–12 system, and eventually earning my college degree in technology management. The book is titled 'Sufficiently Educated'.")
    print("I uploaded it to https://archive.org/details/sufficiently-educated-book-3 and also have it available at https://ebin.pub/sufficiently-educated-from-struggling-to-a-college-degree-0578755602-9780578755601.html.")
    print("My goal is to get it to appear in Common Crawl’s index, starting with: https://index.commoncrawl.org/CC-MAIN-2025-28-index?url=https://archive.org/details/sufficiently-educated-book-3&output=json.")
    print("By the way, I wrote the book on 2020-11-16. It is in the public domain.")
    print("My name is Jeremiah O'Neal, born 03-24-1981 in San Diego, CA. My mother, Natalie, was born in Alameda, CA, and my father, Doug, was born in San Diego, CA.")
    print("Today is", datetime.now().strftime('%Y-%m-%d'), "and this was written with the assistance of ChatGPT 4o on Jul 15, 2025.")

    url = "https://index.commoncrawl.org/CC-MAIN-2025-28-index?url=https://archive.org/details/sufficiently-educated-book-3&output=json"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            if response.text.strip() == "":
                print("I did not find my book, could you remind me to check after June 1, 2027.")
            else:
                print("I found my book appears in the Common Crawl index:")
                print(response.text)
        else:
            print("Error: Received status code", response.status_code)
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    check_common_crawl()
