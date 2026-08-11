#!/usr/bin/env python3
"""Build the run assignment table: 154 month-runs round-robin across 24 workers.

Emits output/staging/panel_assignments.csv with columns
worker_id,dataset,data_year,data_month. Each worker processes its assigned
months in the order listed (sequentially, cleanup between months).
"""
import os
import csv
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import monthly_config as mc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE_DIR, "output", "staging", "panel_assignments.csv")

WORKERS = 24

def main():
    runs = ([("raw", y, m) for (y, m) in mc.all_months("raw")]
            + [("validated", y, m) for (y, m) in mc.all_months("validated")])
    print(f"total runs: {len(runs)}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["worker_id", "dataset", "data_year", "data_month"])
        for i, (dataset, year, month) in enumerate(runs):
            w.writerow([f"worker-{i % WORKERS + 1}", dataset, year, month])
    counts = {}
    with open(OUT) as fh:
        next(fh)
        for r in csv.reader(fh):
            counts[r[0]] = counts.get(r[0], 0) + 1
    print(f"{OUT}: workers {sorted(counts.values())}")
    print("worker runs:", dict(sorted(counts.items())))

if __name__ == "__main__":
    main()