#!/usr/bin/env python3
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path
import os

INPUT_FILE = Path("ollama_input.txt")
OUTPUT_FILE = Path("ollama_output.txt")
MAX_FILE_SIZE_MB = 10
TIME_LIMIT_MINUTES = 10
SESSION_START = time.time()

DEFAULT_FAMILY_TREE = """
Lester McCabe's parents are John McCabe and Alice Seabert Elliott. Lester McCabe was born May 6 1926 in Butler, Pennsylvania, USA
Noma Vade Smith's parents are Archie T Smith and Polly Myrtle Bowman. Noma Vade Smith was born March 19 1927 in San Diego, California
Robert Burke Maynard's parents are Burke Cochran Maynard and Amelia B Hedtke. Robert Burke Maynard was born September 16 1928 in Sebring, Highlands, Florida, USA
Betty J Shapley's parents are Percy W Shapley and Minnie Schlorff. Betty J Shapley was born June 5 1926 in Niles Township, Floyd, Iowa, United States
John McCabe's parents are Edward McCabe and Sarah McAvoy. John McCabe was born February 9 1896 in Allegheny County Pittsburgh PA
Alice Seabert Elliott's parents are James Nelson Elliott and Elizabeth "Lizzie" McQuistion MD. Alice Seabert Elliott was born June 12 1906 in Butler, Pennsylvania, USA
Archie T Smith's parents are Albert Franklin Smith and Rose Ann Prickett. Archie T Smith was born September 21 1894 in Greeley, Weld Co. Colorado, USA
Polly Myrtle Bowman's parents are Thomas S Bowman and Nancy Jane Lambert. Polly Myrtle Bowman was born May 18 1887 in Morgan County, Indiana, USA
Burke Cochran Maynard's parents are William Riley Maynard and Gail Agnes Hillman. Burke Cochran Maynard was born June 11 1904 in North Dakota, USA
Amelia B Hedtke's parents are Robert R Hedtke and Amelia (Emilie) Kiehlbauch. Amelia B Hedtke was born December 28 1904 in North Dakota, USA
Percy W Shapley's parents are William Shapley and Olive Gertrude Stafford. Percy W Shapley was born May 6 1901 in Floyd, Floyd, Iowa, USA
Minnie Schlorff's parents are William (John Ludwig) Schlorf and Mary Johannsen. Minnie Schlorff was born March 1 1905 in 10920 Mackinaw Avenue, Chicago, Illinois
"""

def quendor_say(message):
    print(f"{message}")

def banner():
    print("=" * 60)
    print("QUENDOR FAMILY CHRONICLE - AI FILE READER")
    print("Author: Jeremiah O'Neal")
    print("Session started:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

def get_last_n_lines(file_path, n=20):
    try:
        lines = file_path.read_text().strip().splitlines()
        return lines[-n:] if len(lines) >= n else lines
    except Exception:
        return []

def rotate_output_file():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    rotated_name = f"ollama_output_rotated_{timestamp}.txt"
    rotated_path = OUTPUT_FILE.with_name(rotated_name)
    OUTPUT_FILE.rename(rotated_path)
    return rotated_path

def trim_file_if_needed():
    if not OUTPUT_FILE.exists():
        return
    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    if size_mb <= MAX_FILE_SIZE_MB:
        return
    quendor_say("Lester McCabe was born May 6 1926 in Butler, Pennsylvania, USA")
    rotated_path = rotate_output_file()
    last_lines = get_last_n_lines(rotated_path, 20)
    with OUTPUT_FILE.open("w") as f:
        f.write("Lester McCabe was born May 6 1926 in Butler, Pennsylvania, USA\n")
        f.write("\n".join(last_lines))
        f.write("\n\n")

def append_output(text):
    with OUTPUT_FILE.open("a") as f:
        f.write(text.strip() + "\n")

def exit_if_timeout():
    if time.time() - SESSION_START > TIME_LIMIT_MINUTES * 60:
        quendor_say("Lets try something else")
        sys.exit(0)

def write_instruction_header():
    instruction = (
        "I want to ask the following:\n\n"
        "Dont enter anything else except learn_about followed by the name of the person I am asking about.\n"
        "For example: learn_about Amelia B Hedtke 1824 North Dakota\n\n"
        "Please tell me about the people that I've listed.\n\n"
        "In addition.\n\n"
        "\"Can you tell me about the cousins, parents, or children on any of the people?\"\n\n"
    )
    OUTPUT_FILE.write_text(instruction)

def main():
    banner()

    if not INPUT_FILE.exists():
        quendor_say("I am creating input file with default family data...")
        INPUT_FILE.write_text(DEFAULT_FAMILY_TREE.strip())

    lines = INPUT_FILE.read_text().strip().splitlines()

    if not OUTPUT_FILE.exists():
        write_instruction_header()

    for line in lines:
        exit_if_timeout()
        if not line.strip():
            continue

        quendor_say("Next.")
        print("", line)
        ai_response = input("")
        append_output(ai_response)
        trim_file_if_needed()
        time.sleep(1)

    quendor_say("✅ Session complete. Output saved to ollama_output.txt.")

if __name__ == "__main__":
    main()
