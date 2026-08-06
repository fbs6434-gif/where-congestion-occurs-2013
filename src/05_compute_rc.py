"""
Compute Recurrent Congestion (RC) per unit-month.
"""
import os
import pandas as pd
import numpy as np
from config import PROCESSED_DIR, RC_Q, RC_T, OUTPUT_DIR

def main():
    aligned = pd.read_parquet(os.path.join(PROCESSED_DIR, "aligned.parquet"),
                              columns=["unit_id", "month", "throughput_mbps"])
    meta = pd.read_parquet(os.path.join(PROCESSED_DIR, "meta_valid.parquet"),
                           columns=["unit_id", "month", "speed_tier"])

    aligned = aligned.merge(meta[["unit_id", "month", "speed_tier"]], on=["unit_id", "month"])

    aligned = aligned[aligned["speed_tier"] > 0].copy()
    aligned["bad"] = (aligned["throughput_mbps"] / aligned["speed_tier"]) < RC_Q
    frac = aligned.groupby(["unit_id", "month"])["bad"].mean().rename("rc_fraction").reset_index()
    frac["rc"] = frac["rc_fraction"] > RC_T
    tier = aligned.groupby(["unit_id", "month"])["speed_tier"].first().rename("speed_tier").reset_index()
    df = frac.merge(tier, on=["unit_id", "month"])[["unit_id", "month", "rc", "rc_fraction", "speed_tier"]]
    print(f"RC records: {len(df)}")
    print(f"RC prevalence: {df['rc'].mean():.2%}")

    df.to_parquet(os.path.join(PROCESSED_DIR, "rc.parquet"))
    print("Saved rc.parquet")

if __name__ == "__main__":
    main()
