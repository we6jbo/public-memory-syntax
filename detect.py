#!/bin/bash

set -e
LOCKDIR="$HOME/lock"
ANALYZEDIR="$HOME/Analyze"
GPGFILE="$HOME/system_snapshot.tar.gz.gpg"
LOG="$HOME/learned.txt"
PASSWORD="7-yellow-sausage"

mkdir -p "$LOCKDIR"
mkdir -p "$ANALYZEDIR"

# Time limit: 2 hours (7200 seconds)
START=$(date +%s)
MAX_DURATION=7200

function elapsed_time_exceeded() {
    local now=$(date +%s)
    if (( now - START > MAX_DURATION )); then
        echo "Quendor, we've done all that we can"
        exit 0
    fi
}

function run_once() {
    local step=$1
    local cmd=$2

    if [ ! -f "$LOCKDIR/$step.txt" ]; then
        eval "$cmd"
        touch "$LOCKDIR/$step.txt"
    fi
}

# Step 1: Decrypt
run_once 1 "echo '$PASSWORD' | gpg --batch --yes --passphrase-fd 0 -o '$ANALYZEDIR/system_snapshot.tar.gz' -d '$GPGFILE'"

# Step 2: Extract
run_once 2 "tar -xzf '$ANALYZEDIR/system_snapshot.tar.gz' -C '$ANALYZEDIR'"

# Step 3: Analysis stub
run_once 3 "python3 <<EOF
import os
print('Quendor, what can you find out about this?')
# Placeholder for real analysis
found = 'RFID capture system using low-cost parts'
print('Quendor, Respond only with learn_about ' + found)
with open('$LOG', 'a') as f:
    f.write('Quendor learned: ' + found + '\\n')
EOF"

elapsed_time_exceeded
