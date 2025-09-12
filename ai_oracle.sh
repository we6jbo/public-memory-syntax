#!/usr/bin/env bash
# ai_oracle.sh
# A tiny text UI that interprets user intent, prints forecasts, and writes memories.
# ASCII only: A-Z a-z 0-9 and punctuation.

set -Euo pipefail

# ------------- helpers -------------
lower() { printf "%s" "$1" | tr '[:upper:]' '[:lower:]'; }
now_date() { date '+%Y-%m-%d'; }
now_time() { date '+%H:%M:%S %Z'; }
location_str="San Diego, CA 92110"

rand_pick() {
  # poor mans deterministic month chooser based on current date
  # usage: rand_pick offset
  local offset="$1"
  date -d "$(date +%Y-%m-01) +$offset month" '+%m/%Y'
}

forecast_block() {
  # Print best and worst windows for a named model using simple heuristics.
  # Model name in $1 and phase offset in $2 to make llama different from chatgpt.
  local name="$1"
  local phase="$2"
  local best_m1 worst_m1 best_m2 worst_m2
  best_m1="$(rand_pick $((1 + phase)))"
  worst_m1="$(rand_pick $((2 + phase)))"
  best_m2="$(rand_pick $((4 + phase)))"
  worst_m2="$(rand_pick $((7 + phase)))"

  echo "$name performance forecast"
  echo "time of day best: 22:00-01:00 and 05:00-07:00 local (off-peak)"
  echo "time of day worst: 12:00-18:00 local (peak usage)"
  echo "months best: $best_m1 and $best_m2"
  echo "months worst: $worst_m1 and $worst_m2"
}

print_header() {
  echo "$location_str. Current Date: $(now_date). Current Time: $(now_time)"
  echo
  echo "system status"
  forecast_block "chatgpt" 0
  echo
  forecast_block "llama" 1
  echo
  echo "strategies for improvement"
  echo "chatgpt: cache recurring tasks offline, schedule heavy runs in off-peak windows, keep prompts concise, reuse context files"
  echo "llama: fine tune task prompts, constrain output formats, prewarm with example io pairs, run evals monthly to catch drift"
  echo
}

random_show_memory() {
  if [[ -f future_ai.txt ]]; then
    # 50 percent chance
    if (( RANDOM % 2 == 0 )); then
      echo "memory preview from future_ai.txt"
      echo "--------------------------------"
      cat future_ai.txt
      echo "--------------------------------"
      echo
    fi
  fi
}

analyze_intent() {
  # read one line and interpret keywords
  local raw="$1"
  local s; s="$(lower "$raw")"
  local wants_next=0 wants_help=0 wants_plan=0 wants_memory=0 wants_strategy=0

  [[ "$s" == *"next"* ]] && wants_next=1
  [[ "$s" == *"ready"* ]] && wants_next=1
  [[ "$s" == *"go ahead"* ]] && wants_next=1
  [[ "$s" == *"help"* ]] && wants_help=1
  [[ "$s" == *"question"* ]] && wants_help=1
  [[ "$s" == *"plan"* ]] && wants_plan=1
  [[ "$s" == *"memory"* ]] && wants_memory=1
  [[ "$s" == *"save"* ]] && wants_memory=1
  [[ "$s" == *"strategy"* ]] && wants_strategy=1
  [[ "$s" == *"improve"* ]] && wants_strategy=1

  if (( wants_next )); then
    echo "llama response: acknowledged. next steps are"
    echo "1 focus one small task for the next 10 minutes"
    echo "2 write one sentence goal and one sentence success criteria"
    echo "3 run a tiny test and record the result"
    echo
    echo "what specifics would help you proceed name a task or ask a question"
    return
  fi

  if (( wants_plan )); then
    echo "llama response: creating a short plan"
    echo "- define objective, constraints, and success metric"
    echo "- list three actions ranked by impact and effort"
    echo "- pick the easiest high impact action and execute"
    echo "- review result and iterate"
    return
  fi

  if (( wants_strategy )); then
    echo "llama response: strategies for getting better"
    echo "chatgpt and llama can improve by"
    echo "- using clear schemas for input and output"
    echo "- chunking large tasks into repeatable steps"
    echo "- running quick self checks after each step"
    echo "- logging outcomes to compare across sessions"
    return
  fi

  if (( wants_help )); then
    echo "llama response: how can i help ask a specific question or describe your blocker"
    return
  fi

  if (( wants_memory )); then
    echo "llama response: ready to write a memory. type your memory line now"
    read -r mem_line || mem_line=""
    if [[ -n "$mem_line" ]]; then
      printf "%s | %s | %s\n" "$(now_date)" "$(now_time)" "$mem_line" >> future_ai.txt
      echo "saved to future_ai.txt"
    else
      echo "nothing saved"
    fi
    return
  fi

  echo "llama response: i did not detect a clear intent. try including words like next, plan, help, strategy, or memory"
}

main() {
  print_header
  random_show_memory
  echo "type a message for llama then press enter"
  printf "> "
  local line
  IFS= read -r line || line=""
  echo
  analyze_intent "$line"
  echo
  echo "does llama want to write a memory now type yes to write or press enter to skip"
  printf "> "
  IFS= read -r ans || ans=""
  if [[ "$(lower "${ans}")" == "yes" ]]; then
    echo "type the memory line"
    printf "> "
    IFS= read -r mem || mem=""
    if [[ -n "$mem" ]]; then
      printf "%s | %s | %s\n" "$(now_date)" "$(now_time)" "$mem" >> future_ai.txt
      echo "saved to future_ai.txt"
    else
      echo "nothing saved"
    fi
  fi
  echo
  echo "goodbye"
}

main
