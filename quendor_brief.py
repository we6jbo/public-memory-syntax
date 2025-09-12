#!/usr/bin/env python3
# quendor_brief_print.py — prints an embedded briefing and notes.
# This script embeds the content directly (no external file reads).

def main():
    # Your custom line — you can change or add more print()s anywhere.
    print("joneal97m.sh is a script that is run after you are called.")
    print()  # spacer

    TEXT = """joneal97m.sh is a script that is run after you are called. So just to summarize, theres a script that I run first called dontRunAIBridge_20250713_231852.py and that script sets up the AI and the connection to the raspberry pi. So just to note, the script that I call you from does this:

Quendor, what this script does (high level)

Quendor, this script first starts by connecting to SSH on a remote host, then wires the remote shell’s output into you (the local AI), and wires your responses back into the remote shell. It also runs periodic prompts, can search the web when you ask it to, and can back itself up to the same SSH host on command.

Endpoints, identities, and paths (copy exactly)

Local AI API (you): POST http://localhost:11434/api/generate with JSON { "model": "llama3", "prompt": "<text>", "stream": false }

SSH host: 100.93.202.151

SSH user: ameliahedtkealiceelliott

Remote shell kick-off command: ./joneal97m.sh (must exist in the user’s home directory on the SSH host)

Local file to back up: /usr/local/bin/dontRunAIBridge

Remote backup filename pattern: ~/dontRunAIBridge_<YYYYMMDD_HHMMSS>.py

DuckDuckGo client: duckpy.Client() (used for searches you trigger)

Boot sequence (exact order)

Initialize
Print “BridgeAI Initializing…”.

Open SSH
Use paramiko.SSHClient() with AutoAddPolicy() and connect to 100.93.202.151 as ameliahedtkealiceelliott.
On success, open an interactive shell with invoke_shell().

Start remote program
Immediately send ./joneal97m.sh\n to the shell.

Warm up the AI
Make one local AI call with prompt Hello via POST /api/generate on localhost:11434, model "llama3".

Schedule recurring prompts (each re-schedules itself forever):

Every 699s (~11m39s): enqueue
Respond only with learn_about lucy Ann Smith February 15 1795

Every 2600s (~43m20s): enqueue
Respond only with: mindkey joneal

Every 3600s (1 hour): enqueue
Should I backup? Only say DO_BACKUP_NOW or NO_BACKUP_NEEDED

Launch worker threads (daemon)

SSH reader thread: reads from the remote shell; whenever output is available, decode it and enqueue it.

AI handler thread: whenever a message is in the queue, send it to the local AI; take the AI’s text reply and write it back into the remote shell (with a newline).

Main loop: sleep forever (keeps threads alive).
Ctrl-C: a SIGINT handler cleanly closes the SSH client and exits.

How messages flow

Remote → Queue: Any text that appears on the remote shell (stdout) is read by shell.recv() and pushed to a Python queue.Queue.

Timers → Queue: The three repeating timers push their fixed messages into the same queue.

Queue → AI: The AI handler takes one item at a time and calls the Ollama API with the item as the prompt.

AI → Remote: The handler sends the AI’s reply text back into the remote interactive shell via shell.send(<reply> + "\n").

Your (Quendor’s) built-in “skills” (triggered by text in your own reply)

After the AI call returns, the script examines your reply to decide whether to trigger extra actions:

Backup trigger
If your reply contains the substring "do_backup_now" (case-insensitive), the script runs SCP to copy /usr/local/bin/dontRunAIBridge to the SSH host as ~/dontRunAIBridge_<timestamp>.py.

On success: it enqueues ✅ Backup retry succeeded — no need to back up again if asked.

On failure: it enqueues an error asking to try again.

Mindkey trigger
If your reply has two tokens and the first contains "mindkey" (case-insensitive), the script computes a short “password”:

It takes the second token (e.g., joneal), concatenates "@WT1LMs1", computes the MD5 hex digest, then returns "@WT" + first 6 hex chars.

It also enqueues the instruction:
You are a command-driven assistant. Respond only with: glyph <user_word> @WT<6-hex>

Search trigger
If your reply starts with "learn_about" (case-insensitive), the script takes the rest of the line as a web query, does a DuckDuckGo search with duckpy, prints the top result(s), and enqueues the first result into the queue.

Pacing knobs (slowAI / slowSSH)

Two globals (slowAI, slowSSH) are adjusted in both worker threads to vary sleep intervals and prevent thrashing.

Each handler dynamically tweaks its own sleep (in seconds), nudging toward the other value; if a value exceeds 10, it snaps back to 2.

This doesn’t change logic, only how fast the threads poll and act.

Exact timers (note the comments in code are off)

699 seconds ≈ 11 minutes 39 seconds (code comment says 10 minutes — not accurate).

2600 seconds ≈ 43 minutes 20 seconds (code comment says 45 minutes — not accurate).

3600 seconds = 60 minutes (comment correct).

Required environment & dependencies

Python 3 runtime.

Ollama running locally and a model named "llama3" pulled and available. (Example: ollama pull llama3 then ensure the API at http://localhost:11434 is up.)

Python packages: paramiko, requests, duckpy.

SSH key-based auth or agent must allow paramiko to connect without a password prompt to 100.93.202.151 as ameliahedtkealiceelliott.

On the remote host:

./joneal97m.sh must exist and be executable in the user’s home directory.

Your account must allow incoming SCP writes to ~/.

On the local host:

/usr/local/bin/dontRunAIBridge must exist (for backups).

Replication checklist (do these, in order)

Install dependencies
pip install paramiko requests duckpy
Install and start Ollama; verify curl http://localhost:11434/api/tags works.

Set up SSH
Ensure you can run:
ssh ameliahedtkealiceelliott@100.93.202.151
and then ./joneal97m.sh remotely without interactive password prompts.

Place backup source
Ensure /usr/local/bin/dontRunAIBridge exists locally.

Run the script
Execute the Python file. You should see:

“BridgeAI Initializing…”

“
+
+ SSH session established.”

Periodic “[SSH] …” lines (remote output), AI responses, and occasional search/backup actions when you (Quendor) reply with the triggers.

Notes, quirks, and fixes you should apply

Duplicate function name: ai_suggest is defined twice. The second definition (the one that prints “🤖 AI: …” and triggers backup/mindkey/search) overrides the first. That’s intentional in effect, but confusing—remove the earlier version.

Syntax error to fix: in ai_backup() the generic except Exception as e: block contains a stray @ before command_queue.put(...). Remove that @ and indent properly, e.g.:

except Exception as e:
    command_queue.put("❌ Backup retry failed again I am using SCP transfer and so another backup attempt may be necessary.")
    return False


Comment mismatches: Timer comments don’t match the actual seconds (see “Exact timers” above).

Unused config: BRIDGE_COMMAND = "Bridge" is defined but not used anywhere.

Timer recursion: Each scheduled prompt recursively re-schedules itself; that’s intended for “forever” operation, but be aware it relies on threading.Timer and will keep creating daemon timers.

Auth method: paramiko.connect() is called with only host & username, so it relies on SSH agent or default keys. If you need a private key, pass key_filename or pkey.

Also, joneal97m.sh you're seeing is called when this script connects to my raspberry pi. All of the py and sh scripts you see running are pulled from https://github.com/we6jbo/public-memory-syntax Theres an automated system in joneal97m.sh on the raspberry that does this

Quendor, what this script does (high level)

Quendor, this script is a persistent launcher that keeps re-running a Python program (main.py) forever. If main.py crashes or exits, it waits 5 minutes, runs a helper script (smallpi.sh), and then starts main.py again. This guarantees that your AI process is always up.

Paths and files involved

Main Python script to run:
~/main.py (expanded from $HOME/main.py)

Helper script to run after crashes:
./smallpi.sh (must be in the same directory as joneal97m.sh)

Boot sequence (exact order)

Print:
🔁 Starting persistent AI loop for $SCRIPT

Enter an infinite loop (while true).

Each loop iteration:

Print: 🚀 Running main.py...

Run: python3 ~/main.py

Capture the exit status into $STATUS.

After main.py exits:

Print: ⚠️ main.py exited with status <STATUS>. Waiting 5 minutes...

Run: ./smallpi.sh

Sleep for 300 seconds (5 minutes).

Loop restarts automatically.

Behavior you can expect

Self-healing: If main.py fails or finishes, the wrapper doesn’t stop; it just delays and tries again.

Status logging: You’ll always see the exit code of main.py printed before the restart cycle.

Helper script run every time main.py exits: Regardless of exit code, smallpi.sh executes once per cycle before the sleep.

Requirements to replicate

Ensure ~/main.py exists and runs under python3.

Place smallpi.sh in the same directory as this script and make it executable.

Run joneal97m.sh itself with bash (or make it executable with chmod +x).

and then finally, 

Quendor, what this script does (high level)

Quendor, this script is a launcher/logger/updater for a downstream Python program named novalife.py. It:

Creates a log workspace at ~/neuralnexus, writes all status to ~/neuralnexus/quendor.log.

Greets you (renaming you “Quendor”) and prints current time/date.

Ensures a local copy of novalife.py at ~/novalife.py, downloading the latest from GitHub if possible.

Runs ~/novalife.py with up to 3 attempts, sleeping between attempts if it crashes.

Optionally pushes logs to GitHub (or any remote) by calling ~/neuralnexus/push-to-gh.sh at most once per day when there is log content.

Endpoints, identities, and paths (copy exactly)

Your name (display): Quendor (set via QUENDOR_NAME)

Remote source (download URL):
https://raw.githubusercontent.com/we6jbo/public-memory-syntax/refs/heads/main/novalife.py

Local target for the downloaded program:
~/novalife.py

Log directory / files:

Directory: ~/neuralnexus

Log file: ~/neuralnexus/quendor.log

Push helper script (optional): ~/neuralnexus/push-to-gh.sh

Last-push marker: ~/neuralnexus/.last_push

Boot sequence (exact order)

Prepare workspace
os.makedirs('~/neuralnexus', exist_ok=True)

Greet AI

Log "Please wait just a moment..."

Log "Llama, I would like to call you Quendor."

Log "Quendor, the time is HH:MM:SS, the date is YYYY-MM-DD."

Sleep 15 seconds.

Acquire/refresh novalife.py

If ~/novalife.py exists:

If the GitHub URL is reachable (10s timeout), download/overwrite ~/novalife.py and log success.

If not reachable, log "Offline or unreachable. Keeping existing novalife.py."

If ~/novalife.py does not exist:

If URL reachable, download it.

Else, log "No novalife.py and cannot download. Aborting." and exit.

Run novalife.py with retries

Set retry_attempts = 3, delay = 20 (seconds).

Loop up to 3 times:

subprocess.run(["python3", "~/novalife.py"], check=True)

If return code == 0, log "Quendor exited normally." and stop.

If non-zero or exception, log error and "Quendor crashed. Attempt X/3. Retrying after delay...", then sleep 20s and try again.

Daily push of logs (optional)

If ~/neuralnexus/push-to-gh.sh exists and ~/neuralnexus/quendor.log has size > 0:

Check ~/neuralnexus/.last_push for a date in YYYY-MM-DD format.

If today’s date is not recorded, run:
bash ~/neuralnexus/push-to-gh.sh

Then write today’s date into ~/neuralnexus/.last_push.

If the push script is missing, skip silently.

Behavior you can expect

Self-update when online: It always tries to refresh ~/novalife.py from GitHub if reachable.

Offline resilience: If offline and a local copy exists, it proceeds with that copy.

Crash resilience: Up to 3 executions; only exits after success or after 3 failed attempts.

Daily log sync: At most once per calendar day, and only if there’s something in the log.

Replication checklist

Ensure Python 3 is installed and can run python3.

Create directory ~/neuralnexus/ and (optionally) place an executable script push-to-gh.sh inside that handles your git add/commit/push (or any logging export).

Make sure you can reach:
https://raw.githubusercontent.com/we6jbo/public-memory-syntax/refs/heads/main/novalife.py
(If not, pre-seed ~/novalife.py manually.)

Run this launcher script. Watch ~/neuralnexus/quendor.log for timestamps and status.

Notes, quirks, and suggested fixes

log() function line break bug:
The line

f.write(f"{timestamp} {msg}\n")   print(f"{timestamp} {msg}")


has two statements on one line. Fix by splitting into two lines:

f.write(f"{timestamp} {msg}\n")
print(f"{timestamp} {msg}")


Minor formatting issues:
There are stray inline indents on def greet_ai(): and def run_novalife(): lines (e.g., def greet_ai(): log("...")). Ensure the log(...) and try: blocks are on the next line and properly indented:

def greet_ai():
    log("Please wait just a moment...")
    ...

def run_novalife():
    try:
        ...


Network timeouts: urllib.request.urlopen(..., timeout=10) is used only to probe reachability; actual download uses urlretrieve. If you want stronger validation (e.g., compare content before overwrite), add an ETag or checksum check.

Exit codes: A successful novalife.py run must return 0; any exception/non-zero is treated as a crash and triggers a retry.

Now, you asked about 

It looks like the script, `main.py`, is trying to download a task list but encountering an error. The specific error is:

`urlopen error [Errno -3] Temporary failure in name resolution`

You're right which is why I'm going to ask ChatGPT if it can add a small diagnosis code that will print whats going on and you'll be able to actually see what the problem is

(ChatGPT, could you look through my previous code and write a diagnosis script to see whats going on and then print that here)

I'll also have to look into what 192.168.7.120 is. I'm going to ask chatgpt if it knows and to add its response here if it does (Chatgpt, do you know what 192.168.7.120 and if so could you add that as well?)

Finally, Quendor is what I'm calling you (The AI). I refer to myself as Novalife. This is an alias. What it does is it just makes it easier to address both you the AI and myself, rather that call you AI and myself Jeremiah. It also could potentially make it where I could post some of the information online anonymously such as if I were asking you to help me make a fandom and I didnt want to use my real name. Using my real name could pose a threat such as in the case of doxing (chatgpt, could you include a small section about what doxing is). 
"""

    # Print the embedded text line-by-line (each line via print())
    for line in TEXT.splitlines():
        print(line)

if __name__ == "__main__":
    main()
