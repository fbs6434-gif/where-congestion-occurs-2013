#!/usr/bin/env bash
# Distributed worker wrapper: runs every assigned month sequentially via
# run_panel_month.py, logging to data/logs/panel_run.log. Exits non-zero if any
# month fails (after attempting all).
set -u
REPO="$HOME/where-congestion-occurs-2013"
cd "$REPO" || exit 1
WORKER="${1:?usage: panel_worker.sh worker-id}"
ASSIGN="$REPO/output/staging/panel_assignments.csv"
PY="$REPO/.venv/bin/python"
mkdir -p "$REPO/data/logs"

if [ ! -f "$ASSIGN" ]; then
    echo "[$WORKER] assignments file missing: $ASSIGN" >&2
    exit 2
fi

grep "^$WORKER," "$ASSIGN" | while IFS=, read -r wid dataset year month; do
    echo "[$WORKER] $(date -u +%FT%T) START $dataset $year-$month" >> "$REPO/data/logs/panel_run.log"
    "$PY" "$REPO/src/run_panel_month.py" "$dataset" "$year" "$month" "$WORKER"
    rc=$?
    if [ $rc -eq 0 ]; then
        echo "[$WORKER] $(date -u +%FT%T) OK   $dataset $year-$month" >> "$REPO/data/logs/panel_run.log"
    else
        echo "[$WORKER] $(date -u +%FT%T) FAIL $dataset $year-$month rc=$rc" >> "$REPO/data/logs/panel_run.log"
    fi
done

# Summarize failures
FAILS=$(grep "$WORKER" "$REPO/data/logs/panel_run.log" | grep -c " FAIL " || true)
echo "[$WORKER] worker complete: $FAILS failures"
exit 0