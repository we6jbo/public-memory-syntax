#!/usr/bin/env bash
set -euo pipefail

URL="https://raw.githubusercontent.com/we6jbo/public-memory-syntax/refs/heads/main/abuse_report.py"
DEST_DIR="${HOME}/.local/share/public-memory-syntax"
DEST_FILE="${DEST_DIR}/abuse_report.py"

mkdir -p "${DEST_DIR}"

# Prefer curl; fall back to wget
if command -v curl >/dev/null 2>&1; then
  if [[ -f "${DEST_FILE}" ]]; then
    # -z uses the local file's timestamp; only downloads if remote is newer
    curl -fsSL -z "${DEST_FILE}" -o "${DEST_FILE}" "${URL}"
  else
    curl -fsSL -o "${DEST_FILE}" "${URL}"
  fi
elif command -v wget >/dev/null 2>&1; then
  # -N enables timestamping; we cd so -O can write the same filename
  (
    cd "${DEST_DIR}"
    wget -q -N "${URL}" -O "abuse_report.py"
  )
else
  echo "Error: Need curl or wget installed." >&2
  exit 1
fi

# Ensure python3 exists
if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 not found. Install it (e.g., sudo apt-get install -y python3)." >&2
  exit 1
fi

# Run the script
exec python3 "${DEST_FILE}"
