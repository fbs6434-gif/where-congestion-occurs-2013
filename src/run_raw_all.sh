#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
mkdir -p ../data/logs
YEARS="${1:-2012 2013 2014 2015 2016 2017 2018 2019 2020 2021}"
SKIP_INGEST="${SKIP_INGEST:-}"
for YEAR in $YEARS; do
    LOG=../data/logs/raw_${YEAR}.log
    echo "[$(date)] === YEAR=$YEAR starting ===" | tee -a "$LOG"
    if [ -z "$SKIP_INGEST" ]; then
        if ! YEAR=$YEAR python3 01b_load_raw.py >>"$LOG" 2>&1; then
            echo "[$(date)] YEAR=$YEAR FAILED at 01b_load_raw" | tee -a "$LOG"
            continue
        fi
    fi
    for s in 02_raw_meta 03_detect_speed_tier 04_align_time_series \
             05_compute_rc 06_compute_tis 07_aggregate 08_plot; do
        echo "[$(date)] YEAR=$YEAR step $s" >>"$LOG"
        if ! YEAR=$YEAR python3 "$s.py" >>"$LOG" 2>&1; then
            echo "[$(date)] YEAR=$YEAR FAILED at $s" | tee -a "$LOG"
            break
        fi
    done
    echo "[$(date)] === YEAR=$YEAR done ===" | tee -a "$LOG"
    df -h /home/jovyan/work | tail -1 | tee -a "$LOG"
done
echo "[$(date)] All done."
