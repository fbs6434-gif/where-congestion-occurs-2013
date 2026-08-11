import os
import pandas as pd
import numpy as np
from config import PROCESSED_DIR, MONTHS, MONTH, SPEED_TIER_VARIATION_THRESH, OUTPUT_DIR

SKIP_PLAN_CHANGE_FILTER = os.environ.get("SKIP_PLAN_CHANGE_FILTER", "").strip().lower() in ("1", "true", "yes")

def main():
    tcp = pd.read_parquet(os.path.join(PROCESSED_DIR, "tcp.parquet"))
    meta = pd.read_parquet(os.path.join(PROCESSED_DIR, "meta.parquet"))

    tcp["day"] = tcp["dtime"].dt.day

    valid_units = []

    for unit_id, grp in tcp.groupby("unit_id"):
        daily_max = grp.groupby("day")["throughput_mbps"].max()
        if len(daily_max) < 15:
            continue
        mean_dm = daily_max.mean()
        if mean_dm == 0:
            continue
        variation = (daily_max.max() - daily_max.min()) / mean_dm
        if not SKIP_PLAN_CHANGE_FILTER and variation > SPEED_TIER_VARIATION_THRESH:
            continue
        speed_tier = mean_dm
        valid_units.append({"unit_id": unit_id, "month": MONTH, "speed_tier": speed_tier})

    df = pd.DataFrame(valid_units)
    print(f"Units passing speed tier filter: {df['unit_id'].nunique()}")
    print(f"Connection-months: {len(df)}")

    meta_out = meta.merge(df, on="unit_id", how="inner")
    meta_out.to_parquet(os.path.join(PROCESSED_DIR, "meta_valid.parquet"))
    print("Saved meta_valid.parquet")

if __name__ == "__main__":
    main()
