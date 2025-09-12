#!/usr/bin/env bash
# run_quendor_brief.sh — Debian-only helper to fetch and run a Python script with python3.
# It downloads:
#   https://raw.githubusercontent.com/we6jbo/public-memory-syntax/refs/heads/main/quendor_brief.py
# …then executes it via python3.

set -Eeuo pipefail

URL="https://raw.githubusercontent.com/we6jbo/public-memory-syntax/refs/heads/main/quendor_brief.py"
DEST_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/quendor"
DEST_FILE="$DEST_DIR/quendor_brief.py"

# ---- sanity checks ----
if [[ "$(uname -s)" == *"MINGW"* || "$(uname -s)" == *"CYGWIN"* || "$(uname -s)" == *"MSYS"* ]]; then
  echo "This script is intended for Debian/Linux, not Windows." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is not installed. On Debian: sudo apt-get update && sudo apt-get install -y python3" >&2
  exit 1
fi

mkdir -p "$DEST_DIR"

download_with_curl() {
  curl -fsSL --retry 3 --retry-delay 2 --max-time 60 "$URL" -o "$DEST_FILE"
}

download_with_wget() {
  wget -q --tries=3 --timeout=60 -O "$DEST_FILE" "$URL"
}

echo "Fetching Quendor brief from: $URL"
if command -v curl >/dev/null 2>&1; then
  if ! download_with_curl; then
    echo "curl failed, trying wget…" >&2
    command -v wget >/dev/null 2>&1 && download_with_wget || true
  fi
elif command -v wget >/dev/null 2>&1; then
  download_with_wget
else
  echo "Neither curl nor wget found. On Debian: sudo apt-get install -y curl" >&2
  exit 1
fi

# ---- verify download ----
if [[ ! -s "$DEST_FILE" ]]; then
  echo "Download failed or file is empty: $DEST_FILE" >&2
  exit 1
fi

# Quick sanity check: first 10KB shouldn't be HTML (e.g., a GitHub error page)
if head -c 10240 "$DEST_FILE" | grep -qiE '<html|<!doctype html'; then
  echo "Downloaded content looks like HTML (likely an error page). Aborting." >&2
  exit 1
fi

echo "Download complete: $DEST_FILE"
echo "Running with python3…"
exec python3 "$DEST_FILE"
