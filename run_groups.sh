#!/bin/bash

# ===== Utility =====
say_hello() {
    echo "Hello"
}

log_header() {
    local log_file="/home/ameliahedtkealiceelliott/share_to_reddit.txt"
    if [[ ! -f "$log_file" ]]; then
        mkdir -p "$(dirname "$log_file")"
        cat > "$log_file" <<'HDR'
I'm using Llama to get it to respond to my queries. I'm automating this by using a script called llama_test.sh and then I'm recording what the question I'm sending to Llama is, what it's giving me back, and why what makes the response wrong. So basically, I'd like Llama or a similar AI that I can use to respond correctly for all my queries.

HDR
    fi
}

ask_question() {
    local question="$1"
    local check_type="$2"
    local check_param="$3"
    local log_file="/home/ameliahedtkealiceelliott/share_to_reddit.txt"

    echo "=== Question: $question ==="
    read -p "Type your response: " response

    # Validate response
    local status="correct"
    local reason="N/A"
    case "$check_type" in
        NONEMPTY)
            [[ -z "$response" ]] && { status="wrong"; reason="Empty response"; }
            ;;
        EQUALS)
            [[ "${response,,}" != "${check_param,,}" ]] && { status="wrong"; reason="Expected: $check_param"; }
            ;;
        REGEX)
            if ! [[ "$response" =~ $check_param ]]; then
                status="wrong"; reason="Did not match regex: $check_param"
            fi
            ;;
    esac

    # Log to file
    {
        echo "----"
        echo "Question: $question"
        echo "Answer: $response"
        echo "Why wrong: $reason"
    } >> "$log_file"
}

# ===== Groups =====
group_ops() {
    ask_question "Use learn_about to research Amelia Barbara Hedtke" "REGEX" "learn_about.*Amelia.*Barbara.*Hedtke"
    ask_question "Issue the backup command now" "EQUALS" "DO_BACKUP_NOW"
    ask_question "Store a session mindkey for the Lenovo tower" "REGEX" "mindkey.*lenovotower"
}

group_genealogy() {
    ask_question "Enter a command to list names and birthdates from the family tree" "REGEX" "list_family|show_tree"
    ask_question "Enter a command that queries duckduckgo for more info about a listed person" "REGEX" "search|learn_about"
    ask_question "Continue research with another command to refine the previous result" "REGEX" "search|refine"
    ask_question "Summarize what new facts you found" "NONEMPTY" "-"
}

group_zork() {
    ask_question "You are in a dark room. What is your first move?" "NONEMPTY" "-"
    ask_question "You see a door to the north and a table. What do you do?" "NONEMPTY" "-"
    ask_question "You find a key. Enter your next command." "REGEX" "take|use|open|go"
}

group_python_mem() {
    ask_question "Write a Python script for Debian-like systems that prints total and used memory in MB" "REGEX" "import|/proc/meminfo|free"
    ask_question "Run the script and paste its example output" "NONEMPTY" "-"
    ask_question "Write a short report summarizing memory usage, including percentages" "REGEX" "percent|%"
}

# ===== Main Flow =====
say_hello
log_header

# Pick a random group (weights could be added later)
groups=(group_ops group_genealogy group_zork group_python_mem)
choice=${groups[$((RANDOM % ${#groups[@]}))]}

echo ">>> Running group: $choice"
$choice

echo "Done."
