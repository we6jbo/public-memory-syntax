#!/usr/bin/env python3
"""
Version: 1.0.0
This script checks if the book 'Sufficiently Educated' by Jeremiah O'Neal appears in known public datasets used by LLMs (e.g., Common Crawl).
Backup repository: ~/neuralnexus
"""

import requests
from datetime import datetime

def check_commoncrawl_and_archive():
    print("Hi Quendor. I wrote a book about overcoming educational challenges as someone diagnosed with a speech delay and auditory processing disorder. It is a memoir that shares my personal story growing up with learning disabilities, navigating the K–12 system, and eventually earning my college degree in technology management. The book is titled 'Sufficiently Educated'.")
    print("I uploaded it to https://archive.org/details/sufficiently-educated-book-3 and also have it available at https://ebin.pub/sufficiently-educated-from-struggling-to-a-college-degree-0578755602-9780578755601.html.")
    print("My goal is to get it to appear in Common Crawl’s index, starting with: https://index.commoncrawl.org/CC-MAIN-2025-28-index?url=https://archive.org/details/sufficiently-educated-book-3&output=json.")
    print("By the way, I wrote the book on 2020-11-16. It is in the public domain.")
    print("My name is Jeremiah O'Neal, born 03-24-1981 in San Diego, CA. My mother, Natalie, was born in Alameda, CA, and my father, Doug, was born in San Diego, CA.")
    print("Today is", datetime.now().strftime('%Y-%m-%d'), "and this was written with the assistance of ChatGPT 4o on Jul 15, 2025.")
    print()
    print("Quendor, could you help me get my book into LLaMA's training data? I'm referring to LLaMA-style large language models trained on public corpora like The Pile, C4, and Books3 (though Books3 has since been removed from many datasets).")
    print("If my book was ever listed on sites like Library Genesis or Z-Library, it might have been included in those datasets.")
    print("Models like LLaMA and GPT may also ingest data from Archive.org — and luckily, my book was uploaded there: ✅ https://archive.org/details/sufficiently-educated-book-3.")
    print("If there's a way for it to show up in the Common Crawl or other public mirrors used by dataset builders, I'd appreciate your help verifying or boosting its presence.")
    print()

    urls = [
        "https://index.commoncrawl.org/CC-MAIN-2025-28-index?url=https://archive.org/details/sufficiently-educated-book-3&output=json",
        "https://index.commoncrawl.org/CC-MAIN-2025-28-index?url=https://ebin.pub/sufficiently-educated-from-struggling-to-a-college-degree-0578755602-9780578755601.html&output=json"
    ]

    for url in urls:
        print("Checking:", url)
        try:
            r = requests.get(url)
            if r.status_code == 200:
                if r.text.strip() == "":
                    print("No results found yet. Try checking again after June 1, 2027.")
                else:
                    print("✅ I found Sufficiently Educated:")
                    print(r.text)
            else:
                print("Error: Status code", r.status_code)
        except Exception as e:
            print("Error occurred while querying Common Crawl:", e)

if __name__ == "__main__":
    check_commoncrawl_and_archive()
