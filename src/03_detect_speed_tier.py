"""
Detect speed tier changes and compute effective speed tier per unit-month.
"""
import os
import pandas as pd
import numpy as np
from config import DATA_DIR, MONTHS, SPEED_TIER_VARIATION_THRESH, OUTPUT_DIR

def main():
    tcp = pd.read_parquet(os.path.join(DATA_DIR, "processed", "tcp.parquet"))
    meta = pd.read_parquet(os.path.join(DATA_DIR, "processed", "meta.parquet"))

    tcp["ts"] = pd.to_datetime(tcp["timestamp"])
    tcp["day"] = tcp["ts"].dt.day

    valid_units = []

    for (unit_id, month), grp in tcp.groupby(["unit_id", "month"]):
        daily_max = grp.groupby("day")["throughput_mbps"].max()
        if len(daily_max) < 15:
            continue
        mean_dm = daily_max.mean()
        if mean_dm == 0:
            continue
        variation = (daily_max.max() - daily_max.min()) / mean_dm
        if variation > SPEED_TIER_VARIATION_THRESH:
            continue
        speed_tier = mean_dm
        valid_units.append({"unit_id": unit_id, "month": month, "speed_tier": speed_tier})

    df = pd.DataFrame(valid_units)
    print(f"Units passing speed tier filter: {df['unit_id'].nunique()}")
    print(f"Connection-months: {len(df)}")

    meta_out = meta.merge(df, on="unit_id", how="inner")
    meta_out.to_parquet(os.path.join(DATA_DIR, "processed", "meta_valid.parquet"))
    print("Saved meta_valid.parquet")

if __name__ == "__main__":
    main()
