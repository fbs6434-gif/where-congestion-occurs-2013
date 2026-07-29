#!/usr/bin/env python3
import subprocess
import sys
import os

SCRIPTS = [
    "02_load_and_filter.py",
    "03_detect_speed_tier.py",
    "04_align_time_series.py",
    "05_compute_rc.py",
    "06_compute_tis.py",
    "07_aggregate.py",
    "08_plot.py",
]

def main():
    year = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("YEAR", "2011")
    env = {**os.environ, "YEAR": str(year)}
    base = os.path.dirname(os.path.abspath(__file__))
    for script in SCRIPTS:
        path = os.path.join(base, script)
        print(f"\n{'='*60}")
        print(f"[{year}] Running {script} ...")
        print(f"{'='*60}")
        result = subprocess.run([sys.executable, path], env=env, capture_output=False)
        if result.returncode != 0:
            print(f"ERROR: {script} failed with code {result.returncode}")
            sys.exit(result.returncode)
    print(f"\n{'='*60}")
    print(f"[{year}] All steps completed.")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
