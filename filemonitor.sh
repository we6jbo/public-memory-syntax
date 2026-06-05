#!/bin/bash
set -euo pipefail

USER_NAME="we6jbo"
USER_HOME="/home/$USER_NAME"
REPORT="$USER_HOME/June-July-share-to-chatgpt.txt"
AUDIT_ROOT_DOWNLOADS="$USER_HOME/DownloadsMD5"
AUDIT_ROOT_KINDLE="$USER_HOME/t14_to_kindleMD5"
SOURCE_A="$USER_HOME/Downloads"
SOURCE_B="$USER_HOME/t14_to_kindle"
KEY="j0pyeq"
HOST="127.0.0.1"
PORT="8766"
STATE_DIR="$USER_HOME/.local/share/filemonitor"
STATE_JSON="$STATE_DIR/state.json"
LOG="$STATE_DIR/filemonitor.log"
FILECHECK="$USER_HOME/.config/autostart/filecheck.desktop"
FILECHECK_EXPECTED_MD5="2c4cb0a807226d517651ae2581de0dd4"
START_EPOCH=$(date -d '2026-06-05 00:00:00' +%s)
END_EPOCH=$(date -d '2026-07-05 00:00:00' +%s)
SCRIPT="/opt/filemonitor/filemonitor.sh"

mkdir -p "$AUDIT_ROOT_DOWNLOADS" "$AUDIT_ROOT_KINDLE" "$STATE_DIR"
touch "$LOG"

json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))'
}

encrypt_name() {
  local name="$1"
  python3 - "$KEY" "$name" <<'PY'
import base64, hashlib, sys
key = sys.argv[1].encode()
name = sys.argv[2].encode()
stream = hashlib.sha256(key).digest()
out = bytes([b ^ stream[i % len(stream)] for i, b in enumerate(name)])
print(base64.urlsafe_b64encode(out).decode().rstrip('='))
PY
}

write_state() {
  local status="$1"
  local message="$2"
  local report_path="$3"
  python3 - "$STATE_JSON" "$status" "$message" "$report_path" <<'PY'
import json, sys, time
path, status, message, report = sys.argv[1:5]
data = {
  "ok": True,
  "status": status,
  "message": message,
  "report": report,
  "updated_epoch": int(time.time()),
  "updated_local": time.strftime("%Y-%m-%d %H:%M:%S %Z"),
  "chatgpt_instruction": "Open /home/we6jbo/June-July-share-to-chatgpt.txt and paste it to ChatGPT. Ask for a patch if Downloads and t14_to_kindle have same-name MP4 files with different MD5 values."
}
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
PY
}

notify_popup() {
  # Disabled by full obscrush evaluation tool.
  # Rely only on:
  # http://127.0.0.1:8766/report.txt
  # http://127.0.0.1:8766/status.json
  return 0
}

make_record() {
  local file="$1"
  local root_out="$2"
  local base rel outdir outfile md5 sha size mtime ctime atime encrypted
  base=$(basename "$file")
  rel="${file#/home/$USER_NAME/}"
  outdir="$root_out/$(dirname "$rel")"
  mkdir -p "$outdir"
  outfile="$outdir/$base.json"
  md5=$(md5sum "$file" | awk '{print $1}')
  sha=$(sha256sum "$file" | awk '{print $1}')
  size=$(stat -c '%s' "$file")
  mtime=$(stat -c '%y' "$file")
  ctime=$(stat -c '%z' "$file")
  atime=$(stat -c '%x' "$file")
  encrypted=$(encrypt_name "$base")
  python3 - "$outfile" "$file" "$base" "$md5" "$sha" "$size" "$mtime" "$ctime" "$atime" "$encrypted" <<'PY'
import json, sys
outfile, path, base, md5, sha, size, mtime, ctime, atime, encrypted = sys.argv[1:]
data = {
  "full_path": path,
  "filename": base,
  "md5sum": md5,
  "sha256sum": sha,
  "size_bytes": int(size),
  "modified_time": mtime,
  "metadata_change_time": ctime,
  "access_time": atime,
  "encrypted_filename_ciphertext_j0pyeq": encrypted,
}
with open(outfile, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
PY
}

scan_files() {
  /home/we6jbo/bin/filemonitor-obscure-report "$REPORT" >> "$LOG" 2>&1 || true
  local duplicate_found=0
  local different_md5_found=0
  local now audit_path
  now=$(date '+%Y-%m-%d %H:%M:%S %Z')

  {
    echo "ChatGPT, I run this audit script at $SCRIPT and it is located at $SCRIPT."
    echo "Audit run time: $now"
    echo "Audit window: June 5, 2026 12:00 AM through July 5, 2026 12:00 AM local time."
    echo "Directories checked: $SOURCE_A and $SOURCE_B"
    echo "Network bridge for Chrome extension: http://$HOST:$PORT/status.json"
    echo
    echo "Why a replace prompt can happen: if a file in $SOURCE_A has the same filename as a file already in $SOURCE_B, the file manager may ask whether to replace it. The key question is whether the MD5SUM and size match."
    echo
    echo "MP4 audit records:"
  } > "$REPORT"

  while IFS= read -r -d '' f; do
    local epoch rootout
    epoch=$(stat -c '%Y' "$f")
    if (( epoch >= START_EPOCH && epoch < END_EPOCH )); then
      if [[ "$f" == "$SOURCE_A"/* ]]; then rootout="$AUDIT_ROOT_DOWNLOADS"; else rootout="$AUDIT_ROOT_KINDLE"; fi
      make_record "$f" "$rootout"
      # Do not write readable MP4 filenames or old j0pyeq ciphertext into the ChatGPT report.
      # The detailed MD5/SHA256/size/time record is still saved as JSON by make_record().
      echo "- MP4 audit record saved as JSON under $rootout" >> "$REPORT"
      echo "  Filename: hidden from report output" >> "$REPORT"
      echo "  Filename obscrushed: $(encrypt_name "$(basename "$f")")" >> "$REPORT"
      echo >> "$REPORT"
    fi
  done < <(find "$SOURCE_A" "$SOURCE_B" -maxdepth 1 -type f \( -iname '*.mp4' -o -iname '*.MP4' \) -print0 2>/dev/null || true)

  {
    echo
    echo "Duplicate filename comparison between Downloads and t14_to_kindle:"
  } >> "$REPORT"

  while IFS= read -r -d '' src; do
    local base dst src_epoch dst_epoch src_md5 dst_md5 src_size dst_size
    base=$(basename "$src")
    dst="$SOURCE_B/$base"
    [[ -f "$dst" ]] || continue
    src_epoch=$(stat -c '%Y' "$src")
    dst_epoch=$(stat -c '%Y' "$dst")
    if (( src_epoch >= START_EPOCH && src_epoch < END_EPOCH )) || (( dst_epoch >= START_EPOCH && dst_epoch < END_EPOCH )); then
      duplicate_found=1
      src_md5=$(md5sum "$src" | awk '{print $1}')
      dst_md5=$(md5sum "$dst" | awk '{print $1}')
      src_size=$(stat -c '%s' "$src")
      dst_size=$(stat -c '%s' "$dst")
      {
        echo "- Same filename found: $base"
        echo "  Downloads full path: $src"
        echo "  t14_to_kindle full path: $dst"
        echo "  Downloads MD5SUM: $src_md5"
        echo "  t14_to_kindle MD5SUM: $dst_md5"
        echo "  Downloads size bytes: $src_size"
        echo "  t14_to_kindle size bytes: $dst_size"
        echo "  Downloads modified: $(stat -c '%y' "$src")"
        echo "  t14_to_kindle modified: $(stat -c '%y' "$dst")"
      } >> "$REPORT"
      if [[ "$src_md5" == "$dst_md5" ]]; then
        echo "  Reason: The replace prompt is probably happening because the destination already contains the same filename, and the contents appear identical by MD5." >> "$REPORT"
      else
        different_md5_found=1
        echo "  Reason: The replace prompt is happening because the destination already contains the same filename, but the MD5SUM differs. These may be different videos or edited versions with the same name." >> "$REPORT"
      fi
      echo >> "$REPORT"
    fi
  done < <(find "$SOURCE_A" -maxdepth 1 -type f \( -iname '*.mp4' -o -iname '*.MP4' \) -print0 2>/dev/null || true)

  if (( duplicate_found == 1 )); then
    if (( different_md5_found == 1 )); then
      write_state "duplicate_different_md5" "Same-name MP4 files were found, and at least one pair has different MD5 values. Paste the report to ChatGPT." "$REPORT"
      #notify_popup "File Monitor found same-name MP4 files with different MD5 values. Open /home/we6jbo/June-July-share-to-chatgpt.txt and paste it to ChatGPT."
    else
      write_state "duplicate_same_md5" "Same-name MP4 files were found, but their MD5 values match. The replace prompt is likely just a duplicate-name warning." "$REPORT"
    fi
  else
    write_state "ok" "No same-name MP4 replacement conflict was found in the audit window." "$REPORT"
  fi
}

july5_cleanup() {
  local today md5
  today=$(date +%Y-%m-%d)
  if [[ "$today" > "2026-07-04" && -f "$FILECHECK" ]]; then
    md5=$(md5sum "$FILECHECK" | awk '{print $1}')
    if [[ "$md5" == "$FILECHECK_EXPECTED_MD5" ]]; then
      mv "$FILECHECK" "/tmp/filecheck.desktop"
      echo "Moved $FILECHECK to /tmp/filecheck.desktop after July 5 because MD5 matched." >> "$LOG"
    else
      echo "Did not move $FILECHECK because MD5 was $md5, expected $FILECHECK_EXPECTED_MD5." >> "$LOG"
    fi
  fi
}

serve_status() {
  python3 - "$HOST" "$PORT" "$STATE_JSON" "$REPORT" <<'PY'
import http.server, json, os, socketserver, sys, urllib.parse
host, port, state_path, report_path = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "chrome-extension://*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))
    def do_OPTIONS(self):
        self._send(204, "")
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ("/", "/status.json"):
            try:
                with open(state_path, "r", encoding="utf-8") as f: body = f.read()
            except FileNotFoundError:
                body = json.dumps({"ok": False, "status": "not_ready", "message": "No scan has run yet."})
            self._send(200, body)
        elif path == "/report.txt":
            try:
                with open(report_path, "r", encoding="utf-8") as f: body = f.read()
            except FileNotFoundError:
                body = "Report not found yet."
            self._send(200, body, "text/plain")
        else:
            self._send(404, json.dumps({"ok": False, "error": "not found"}))
    def log_message(self, fmt, *args):
        return
class ReuseTCPServer(socketserver.TCPServer):
    allow_reuse_address = True
with ReuseTCPServer((host, port), Handler) as httpd:
    httpd.serve_forever()
PY
}

main() {
  echo "[$(date)] filemonitor starting" >> "$LOG"

  # Create initial state immediately so the web server has something to show.
  write_state "starting" "File monitor started. MP4 scan may still be running." "$REPORT" || true

  # Start the HTTP bridge before the slow MP4 checksum scan.
  if ! ss -ltn 2>/dev/null | grep -q ":$PORT "; then
    serve_status >> "$LOG" 2>&1 &
    echo "[$(date)] filemonitor HTTP server requested at http://$HOST:$PORT/report.txt" >> "$LOG"
    sleep 1
  else
    echo "[$(date)] port $PORT already appears to be listening" >> "$LOG"
  fi

  # Now run the slower scan.
  scan_files >> "$LOG" 2>&1

  # Failure learned: report may need forced post-processing after scan.
  /home/we6jbo/bin/filemonitor-obscure-report "$REPORT" >> "$LOG" 2>&1 || true

  july5_cleanup >> "$LOG" 2>&1 || true

  echo "[$(date)] filemonitor scan finished" >> "$LOG"

  # Keep the autostart-launched shell alive so it is obvious in process checks.
  while true; do
    sleep 3600
  done
}

main "$@"
