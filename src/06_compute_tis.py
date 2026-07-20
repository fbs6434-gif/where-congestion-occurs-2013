"""
Compute Tight Initial Segment (TIS) via Pearson correlation per unit-month.
"""
import os
import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from config import DATA_DIR, WEBSITES, TIS_R_THRESH, TIS_COUNT_THRESH, OUTPUT_DIR

def main():
    aligned = pd.read_parquet(os.path.join(DATA_DIR, "processed", "aligned.parquet"))
    meta = pd.read_parquet(os.path.join(DATA_DIR, "processed", "meta_valid.parquet"))

    tis_records = []

    for (unit_id, month), grp in aligned.groupby(["unit_id", "month"]):
        high_count = 0
        for site in WEBSITES:
            site_data = grp[grp["url"] == site]
            if len(site_data) < 180:
                continue
            if site_data["throughput_mbps"].nunique() < 2:
                continue
            if site_data["load_time_ms"].nunique() < 2:
                continue
            r, _ = pearsonr(site_data["throughput_mbps"], site_data["load_time_ms"])
            if r > TIS_R_THRESH:
                high_count += 1
        tis = high_count >= TIS_COUNT_THRESH
        tis_records.append({
            "unit_id": unit_id,
            "month": month,
            "tis": tis,
            "tis_high_corr_count": high_count,
        })

    df = pd.DataFrame(tis_records)
    print(f"TIS records: {len(df)}")
    print(f"TIS prevalence: {df['tis'].mean():.2%}")

    df.to_parquet(os.path.join(DATA_DIR, "processed", "tis.parquet"))
    print("Saved tis.parquet")

if __name__ == "__main__":
    main()
