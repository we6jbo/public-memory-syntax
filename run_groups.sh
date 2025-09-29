#!/bin/bash
set -euo pipefail

# ========= Config =========
TIME_LIMIT_SECONDS=1800  # 30 minutes

# Tune per-group weights (0–100). Higher = more likely.
# Names must match the keys in GROUP_FILES below.
declare -A WEIGHTS=(
  [ops]=80
  [genealogy]=70
  [zork]=50
  [python_mem]=60
)

GROUP_DIR="./groups"
declare -A GROUP_FILES=(
  [ops]="$GROUP_DIR/ops.txt"
  [genealogy]="$GROUP_DIR/genealogy.txt"
  [zork]="$GROUP_DIR/zork.txt"
  [python_mem]="$GROUP_DIR/python_mem.txt"
)

LOG_FILE="/home/ameliahedtkealiceelliott/share_to_reddit.txt"
LLAMA="./llama_test.sh"  # must echo the model's answer to stdout

# ========= Time tracking =========
START_TIME=$(date +%s)
time_exceeded() { local now elapsed; now=$(date +%s); elapsed=$((now-START_TIME)); ((elapsed>=TIME_LIMIT_SECONDS)); }
ensure_time() { if time_exceeded; then echo "That's all we have for now (time limit reached)."; exit 0; fi; }

# ========= Log header (only if file doesn't exist) =========
init_log() {
  if [[ ! -f "$LOG_FILE" ]]; then
    mkdir -p "$(dirname "$LOG_FILE")"
    cat > "$LOG_FILE" <<'HDR'
I'm using Llama to get it to respond to my queries. I'm automating this by using a script called llama_test.sh and then I'm recording what the question I'm sending to Llama is, what it's giving me back, and why what makes the response wrong. So basically, I'd like Llama or a similar AI that I can use to respond correctly for all my queries.

HDR
  fi
}

# ========= Validation engine =========
# Each line in a group file is: QUESTION | CHECK_TYPE | CHECK_PARAM
# Supported CHECK_TYPE: NONEMPTY, EQUALS, INT_EQ, REGEX, NAME_TWO_WORDS, DOB_MMDDYYYY, CONTAINS
validate_answer() {
  local check="$1"; shift
  local param="$1"; shift
  local resp="$*"

  case "$check" in
    NONEMPTY)
      [[ -n "$resp" ]] && return 0 || { echo "Empty response"; return 1; } ;;

    EQUALS)
      [[ "${resp,,}" == "${param,,}" ]] && return 0 || { echo "Expected exactly: $param"; return 1; } ;;

    INT_EQ)
      [[ "$resp" =~ ^-?[0-9]+$ ]] && [[ "$resp" -eq "$param" ]] && return 0 || { echo "Expected integer: $param"; return 1; } ;;

    REGEX)
      [[ "$resp" =~ $param ]] && return 0 || { echo "Did not match regex: $param"; return 1; } ;;

    CONTAINS)
      [[ "${resp,,}" == *"${param,,}"* ]] && return 0 || { echo "Expected substring: $param"; return 1; } ;;

    NAME_TWO_WORDS)
      if [[ "$resp" =~ ^[A-Za-z][A-Za-z'’-]*[[:space:]][A-Za-z][A-Za-z'’-]*$ ]]; then return 0; else echo "Expected first and last name"; return 1; fi ;;

    DOB_MMDDYYYY)
      if [[ "$resp" =~ ^(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01])/[0-9]{4}$ ]]; then return 0; else echo "Expected DOB format MM/DD/YYYY"; return 1; fi ;;

    *)
      echo "Internal config error: unknown check '$check'"; return 1 ;;
  esac
}

# ========= Run one group file =========
run_group_file() {
  local f="$1"
  local line lineno=0
  ensure_time

  if [[ ! -f "$f" ]]; then echo "Group file not found: $f" >&2; return 1; fi

  while IFS='|' read -r raw_q raw_check raw_param || [[ -n "${raw_q:-}" ]]; do
    ensure_time
    ((lineno++))

    # Trim spaces
    q="${raw_q#"${raw_q%%[![:space:]]*}"}";     q="${q%"${q##*[![:space:]]}"}"
    check="${raw_check#"${raw_check%%[![:space:]]*}"}"; check="${check%"${check##*[![:space:]]}"}"
    param="${raw_param#"${raw_param%%[![:space:]]*}"}"; param="${param%"${param##*[![:space:]]}"}"
    [[ "${param}" == "-" ]] && param=""

    # Skip blanks / comments
    [[ -z "$q" || "$q" =~ ^# ]] && continue

    # Ask Llama
    response="$("$LLAMA" "$q" 2>/dev/null || true)"

    # Validate
    reason=""
    if ! reason="$(validate_answer "$check" "$param" "$response")"; then :; fi
    status=$?

    # Log
    {
      echo "----"
      echo "Question: $q"
      echo "Llama: $response"
      if (( status == 0 )); then
        echo "Why wrong: N/A (correct)"
      else
        echo "Why wrong: $reason"
      fi
    } >> "$LOG_FILE"

  done < "$f"
}

# ========= Weighted picker (no repeats) =========
pick_group_weighted() {
  # args: a list of group names still remaining
  local remaining=("$@")

  # If one left, pick it
  if ((${#remaining[@]}==1)); then echo "${remaining[0]}"; return; fi

  # Try independent hits first
  local hits=()
  for g in "${remaining[@]}"; do
    local w="${WEIGHTS[$g]:-50}"
    (( RANDOM % 100 < w )) && hits+=("$g")
  done

  if ((${#hits[@]}==1)); then
    echo "${hits[0]}"; return
  fi

  # If none or multiple hit, do a weighted draw among remaining
  local total=0; for g in "${remaining[@]}"; do total=$((total + ${WEIGHTS[$g]:-50})); done
  local pick=$(( RANDOM % (total==0 ? 1 : total) ))
  local acc=0
  for g in "${remaining[@]}"; do
    acc=$((acc + ${WEIGHTS[$g]:-50}))
    if (( pick < acc )); then echo "$g"; return; fi
  done
  echo "${remaining[0]}"
}

# ========= Main =========
init_log

# Build initial remaining list from keys in GROUP_FILES
remaining=()
for g in "${!GROUP_FILES[@]}"; do remaining+=("$g"); done

# Deterministic order of keys can vary; shuffle selection via weighted picker
while ((${#remaining[@]} > 0)); do
  ensure_time
  # Pick by weight
  choice="$(pick_group_weighted "${remaining[@]}")"

  # Run chosen group
  case "$choice" in
    ops)         echo "=== Running: OPS Commands ===";          run_group_file "${GROUP_FILES[ops]}" ;;
    genealogy)   echo "=== Running: Genealogy Research ===";     run_group_file "${GROUP_FILES[genealogy]}" ;;
    zork)        echo "=== Running: Zork-like Game ===";         run_group_file "${GROUP_FILES[zork]}" ;;
    python_mem)  echo "=== Running: Python Memory Check ===";    run_group_file "${GROUP_FILES[python_mem]}" ;;
    *) echo "Internal error: unknown group '$choice'"; exit 1 ;;
  esac

  # Remove chosen (no repeats)
  new=(); for g in "${remaining[@]}"; do [[ "$g" != "$choice" ]] && new+=("$g"); done
  remaining=("${new[@]}")
done

echo "All selected groups completed."
