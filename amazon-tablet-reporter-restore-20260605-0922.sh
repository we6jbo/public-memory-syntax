#!/data/data/com.termux/files/usr/bin/sh
# amazon-tablet-reporter-restore-20260605-0922.sh
# Restore/repair script for Amazon tablet Termux:Boot reporter.
# Made Jun 5, 2026 around 9:22 to 10:00 AM.
# TAG: #D3FFC1E
#
# GitHub raw URL expected:
# https://raw.githubusercontent.com/we6jbo/public-memory-syntax/main/amazon-tablet-reporter-restore-20260605-0922.sh
#
# Purpose:
# - Check ~/.termux/boot/amazon-tablet-reporter.sh
# - Restore it if missing, broken, or changed
# - Try GitHub/raw source first when available
# - Fall back to embedded known-good reporter if GitHub breaks
# - Report stages to T14 port 3329

T14_HOST="${T14_HOST:-192.168.8.110}"
STAGE_PORT="${STAGE_PORT:-3329}"
TAG="#D3FFC1E"

TARGET="$HOME/.termux/boot/amazon-tablet-reporter.sh"
BOOT_RESTORE="$HOME/.termux/boot/00-restore-amazon-tablet-reporter.sh"
BASE="$HOME/.local/share/amazon-tablet-monitor"
LOG="$BASE/restore.log"
REMOTE_URL="https://raw.githubusercontent.com/we6jbo/public-memory-syntax/main/amazon-tablet-reporter-restore-20260605-0922.sh"
EXPECTED_SHA="790d042a0d62be2ade6a04d4d3f08fe9248af3021ddebfdb671fc92f8fc465db"

mkdir -p "$BASE" "$HOME/.termux/boot"

stage() {
    NAME="$1"
    DETAILS="$2"
    NOW="$(date '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo unknown-time)"
    JSON="{\"tag\":\"$TAG\",\"device\":\"amazon-tablet\",\"time\":\"$NOW\",\"stage\":\"$NAME\",\"details\":\"$DETAILS\"}"
    echo "$JSON" >> "$LOG"
    echo "$JSON"

    if command -v curl >/dev/null 2>&1; then
        curl -sS -m 8 \
            -H "Content-Type: application/json" \
            -X POST \
            -d "$JSON" \
            "http://$T14_HOST:$STAGE_PORT/stage" >/dev/null 2>&1 || true
    fi
}

sha_of_file() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" 2>/dev/null | awk '{print $1}'
    else
        echo "no-sha256sum"
    fi
}

write_embedded_reporter() {
cat > "$TARGET" <<'EMBEDDED_REPORTER'
#!/data/data/com.termux/files/usr/bin/sh
# amazon-tablet-reporter.sh
# Golden version made Jun 5, 2026 around 9:22 to 10:00 AM.
# TAG: #D3FFC1E

T14_HOST="${T14_HOST:-192.168.8.110}"
STAGE_PORT="${STAGE_PORT:-3329}"
TAG="#D3FFC1E"
BASE="$HOME/.local/share/amazon-tablet-monitor"
LOG="$BASE/amazon-tablet-reporter.log"

mkdir -p "$BASE"

stage() {
    NAME="$1"
    DETAILS="$2"
    NOW="$(date '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo unknown-time)"
    JSON="{\"tag\":\"$TAG\",\"device\":\"amazon-tablet\",\"time\":\"$NOW\",\"stage\":\"$NAME\",\"details\":\"$DETAILS\"}"
    echo "$JSON" >> "$LOG"

    if command -v curl >/dev/null 2>&1; then
        curl -sS -m 8 \
            -H "Content-Type: application/json" \
            -X POST \
            -d "$JSON" \
            "http://$T14_HOST:$STAGE_PORT/stage" >/dev/null 2>&1 || true
    fi
}

check_movies() {
    if [ -d "/sdcard/Movies" ]; then
        COUNT="$(find /sdcard/Movies -maxdepth 1 -type f -name '*.MP4' 2>/dev/null | wc -l | tr -d ' ')"
        echo "Movies exists; MP4 count=$COUNT"
    else
        echo "Movies missing or storage permission not granted"
    fi
}

stage "boot-reporter-started" "amazon-tablet-reporter.sh started from Termux:Boot."
stage "boot-reporter-version" "Golden version made Jun 5, 2026 around 9:22 to 10:00 AM."
stage "boot-reporter-movies" "$(check_movies)"
stage "boot-reporter-hardening" "Restore checker should keep this boot script repaired. GitHub raw source may be used if valid; embedded fallback is used if GitHub breaks."

while true; do
    stage "running-5-minute-cycle" "Tablet reporter alive. $(check_movies)"
    sleep 300
done
EMBEDDED_REPORTER
chmod +x "$TARGET"
}

write_boot_restore_wrapper() {
cat > "$BOOT_RESTORE" <<'BOOTRESTORE'
#!/data/data/com.termux/files/usr/bin/sh
BASE="$HOME/.local/share/amazon-tablet-monitor"
RESTORE="$BASE/amazon-tablet-reporter-restore-20260605-0922.sh"
LOG="$BASE/boot-restore-wrapper.log"
mkdir -p "$BASE"

if [ -x "$RESTORE" ]; then
    "$RESTORE" --ensure >> "$LOG" 2>&1
else
    echo "Restore script missing: $RESTORE" >> "$LOG"
fi
BOOTRESTORE
chmod +x "$BOOT_RESTORE"
}

try_remote_restore_script() {
    TMP="$BASE/remote-amazon-tablet-reporter-restore-20260605-0922.sh.tmp"

    if ! command -v curl >/dev/null 2>&1; then
        stage "github-restore-skip" "curl not available; using embedded fallback."
        return 1
    fi

    if curl -fsSL -m 12 "$REMOTE_URL" -o "$TMP"; then
        if grep -q "#D3FFC1E" "$TMP" && grep -q "write_embedded_reporter" "$TMP"; then
            cp "$TMP" "$BASE/amazon-tablet-reporter-restore-20260605-0922.sh"
            chmod +x "$BASE/amazon-tablet-reporter-restore-20260605-0922.sh"
            stage "github-restore-source-ok" "Downloaded valid restore script from GitHub raw URL."
            return 0
        else
            stage "github-restore-source-invalid" "Downloaded GitHub file did not contain expected markers; ignoring it."
            return 1
        fi
    else
        stage "github-restore-source-failed" "Could not download GitHub restore source; using embedded fallback."
        return 1
    fi
}

ensure_reporter() {
    stage "restore-check-started" "Checking $TARGET against expected golden version."

    write_boot_restore_wrapper

    CURRENT_SHA=""
    if [ -f "$TARGET" ]; then
        CURRENT_SHA="$(sha_of_file "$TARGET")"
    fi

    if [ "$CURRENT_SHA" = "$EXPECTED_SHA" ]; then
        stage "restore-check-ok" "amazon-tablet-reporter.sh is already the expected golden version."
        return 0
    fi

    stage "restore-needed" "Reporter missing or changed. current_sha=$CURRENT_SHA expected_sha=$EXPECTED_SHA"

    try_remote_restore_script || true

    write_embedded_reporter
    NEW_SHA="$(sha_of_file "$TARGET")"

    if [ "$NEW_SHA" = "$EXPECTED_SHA" ]; then
        stage "restore-success" "Reporter restored to golden Jun 5 2026 9:22-10AM version."
        return 0
    else
        stage "restore-warning" "Reporter was written but sha check did not match. new_sha=$NEW_SHA expected_sha=$EXPECTED_SHA"
        return 1
    fi
}

install_self() {
    mkdir -p "$BASE"
    cp "$0" "$BASE/amazon-tablet-reporter-restore-20260605-0922.sh" 2>/dev/null || true
    chmod +x "$BASE/amazon-tablet-reporter-restore-20260605-0922.sh" 2>/dev/null || true
    write_boot_restore_wrapper
    ensure_reporter
    stage "restore-install-complete" "Restore system installed. Final GitHub filename is amazon-tablet-reporter-restore-20260605-0922.sh."
}

case "${1:-}" in
    --ensure)
        ensure_reporter
        ;;
    --install)
        install_self
        ;;
    *)
        ensure_reporter
        ;;
esac

