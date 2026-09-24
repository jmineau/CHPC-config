#!/bin/bash -l
#
# Weekly activity log. Runs from cron Friday 06:00 (before the 10:00 group
# meeting); also fine to run by hand -- see the `weeklog` command on PATH.
#
#   scan.py      -- collects git/file/SLURM activity (no network, depth-capped)
#   summarize.py -- posts the digest to the CHPC nimbus vLLM endpoint
#
# Both the raw digest and the written log are kept, so a bad summary can be
# regenerated from the digest without re-scanning.
#
# Usage:
#   run.sh                      last 7 days (the cron default)
#   run.sh --days 3             last 3 days
#   run.sh --since 2026-09-12   since that date
#   run.sh --since-last         since the most recent log in weeks/
#   run.sh --print              also print the log to stdout

set -uo pipefail

SCRIPT_DIR="$HOME/.chpc-config/weekly-log"   # scan.py, summarize.py live here (git-tracked)
DIR="$HOME/.weekly-log"                      # weeks/, logs/ -- generated data, not code
WEEKS="$DIR/weeks"
DAYS=7
PRINT=0

die() { echo "error: $*" >&2; exit 1; }

while [ $# -gt 0 ]; do
    case "$1" in
        --days)  DAYS="${2:-}"; shift 2 || die "--days needs a number" ;;
        --since)
            [ -n "${2:-}" ] || die "--since needs a date (YYYY-MM-DD)"
            then_s=$(date -d "$2" +%s 2>/dev/null) || die "bad date: $2"
            DAYS=$(( ( $(date +%s) - then_s ) / 86400 ))
            shift 2 ;;
        --since-last)
            # Newest dated log, ignoring the .digest.md companions.
            last=$(ls -1 "$WEEKS"/????-??-??.md 2>/dev/null | tail -1)
            if [ -n "$last" ]; then
                d=$(basename "$last" .md)
                then_s=$(date -d "$d" +%s 2>/dev/null) || die "bad log name: $d"
                DAYS=$(( ( $(date +%s) - then_s ) / 86400 ))
                echo "last log was $d -> looking back $DAYS days"
            else
                echo "no previous log found -> defaulting to 7 days"
            fi
            shift ;;
        --print) PRINT=1; shift ;;
        -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
        [0-9]*)  DAYS="$1"; shift ;;   # bare number, e.g. `run.sh 10`
        *) die "unknown option: $1" ;;
    esac
done

[ "$DAYS" -ge 1 ] 2>/dev/null || die "lookback must be >= 1 day (got '$DAYS')"

TODAY=$(date +%Y-%m-%d)
DIGEST="$WEEKS/$TODAY.digest.md"
LOG="$WEEKS/$TODAY.md"

mkdir -p "$WEEKS" "$DIR/logs"

echo "=== $(date) :: scanning last $DAYS days ==="
python3 "$SCRIPT_DIR/scan.py" --days "$DAYS" > "$DIGEST" || die "scan failed"
echo "digest: $DIGEST ($(wc -l < "$DIGEST") lines)"

echo "=== $(date) :: summarizing ==="
python3 "$SCRIPT_DIR/summarize.py" --digest "$DIGEST" -o "$LOG" \
    || die "summarization failed; digest kept at $DIGEST"

echo "=== $(date) :: done -> $LOG ==="
[ "$PRINT" -eq 1 ] && { echo; cat "$LOG"; }
exit 0
