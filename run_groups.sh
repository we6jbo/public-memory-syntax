#!/bin/bash
set -euo pipefail

# ========= Config =========
TIME_LIMIT_SECONDS=1800  # 30 minutes
LOG_FILE="/home/ameliahedtkealiceelliott/share_to_reddit.txt"

GROUP_DIR="./groups"
declare -A GROUP_FILES=(
  [ops]="$GROUP_DIR/ops.txt"
  [genealogy]="$GROUP_DIR/genealogy.txt"
  [zork]="$GROUP_DIR/zork.txt"
  [python_mem]="$GROUP_DIR/python_mem.txt"
)

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

# ========= Validation =========
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
    *)
      echo "Unknown check: $check"; return 1 ;;
  esac
}

# ========= Run one group file =========
run_group_file() {
  local f="$1"
  local line lineno=0
  ensure_time

  while IFS='|' read -r raw_q raw_check raw_param || [[ -n "${raw_q:-}" ]]; do
    ensure_time
    ((lineno++))

    # Trim spaces
    q="${raw_q#"${raw_q%%[![:space:]]*}"}"; q="${q%"${q##*[![:space:]]}"}"
    check="${raw_check#"${raw_check%%[![:space:]]*}"}"; check="${check%"${check##*[![:space:]]}"}"
    param="${raw_param#"${raw_param%%[![:space:]]*}"}"; param="${param%"${param##*[![:space:]]}"}"
    [[ "${param}" == "-" ]] && param=""

    [[ -z "$q" || "$q" =~ ^# ]] && continue

    # === Direct interactive input ===
    echo "=== Question: $q ==="
    read -p "Type your response: " response

    # Validate
    reason=""
    if ! reason="$(validate_answer "$check" "$param" "$response")"; then :; fi
    status=$?

    # Log
    {
      echo "----"
      echo "Question: $q"
      echo "Answer: $response"
      if (( status == 0 )); then
        echo "Why wrong: N/A (correct)"
      else
        echo "Why wrong: $reason"
      fi
    } >> "$LOG_FILE"

  done < "$f"
}

# ========= Main =========
init_log

for g in "${!GROUP_FILES[@]}"; do
  echo "=== Running group: $g ==="
  run_group_file "${GROUP_FILES[$g]}"
done

echo "All groups completed."
