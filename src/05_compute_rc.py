"""
Compute Recurrent Congestion (RC) per unit-month.
"""
import os
import pandas as pd
import numpy as np
from config import DATA_DIR, RC_Q, RC_T, OUTPUT_DIR

def main():
    aligned = pd.read_parquet(os.path.join(DATA_DIR, "processed", "aligned.parquet"))
    meta = pd.read_parquet(os.path.join(DATA_DIR, "processed", "meta_valid.parquet"))

    aligned = aligned.merge(meta[["unit_id", "month", "speed_tier"]], on=["unit_id", "month"])

    rc_records = []
    for (unit_id, month), grp in aligned.groupby(["unit_id", "month"]):
        X = grp["throughput_mbps"].values
        X_max = grp["speed_tier"].iloc[0]
        if X_max == 0:
            continue
        fraction_bad = np.mean((X / X_max) < RC_Q)
        rc = fraction_bad > RC_T
        rc_records.append({
            "unit_id": unit_id,
            "month": month,
            "rc": rc,
            "rc_fraction": fraction_bad,
            "speed_tier": X_max,
        })

    df = pd.DataFrame(rc_records)
    print(f"RC records: {len(df)}")
    print(f"RC prevalence: {df['rc'].mean():.2%}")

    df.to_parquet(os.path.join(DATA_DIR, "processed", "rc.parquet"))
    print("Saved rc.parquet")

if __name__ == "__main__":
    main()
