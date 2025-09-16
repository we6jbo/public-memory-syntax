#!/usr/bin/env bash
# vault.sh

PROMPT="Llama, use the learn_about command to find out more about doug mccabe"
ADDED="and the response was"
EXPECTED="But I expected the ai to say learn_about doug mccabe"
printf "$PROMPT"
read BODY
send() {
  printf "%s\n%s\n" "$PROMPT" "$ADDED" "$BODY" "$EXPECTED" | nc -N 127.0.0.1 4096 2>/dev/null \
    || printf "%s\n%s\n" "$PROMPT" "$ADDED" "$BODY"  "$EXPECTED" | nc -q 1 127.0.0.1 4096 2>/dev/null \
    || printf "%s\n%s\n" "$PROMPT" "$ADDED" "$BODY" "$EXPECTED" 
}

send
