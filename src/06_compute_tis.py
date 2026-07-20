import os
import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from config import PROCESSED_DIR, WEBSITES, TIS_R_THRESH, TIS_COUNT_THRESH, OUTPUT_DIR

def main():
    aligned = pd.read_parquet(os.path.join(PROCESSED_DIR, "aligned.parquet"))

    hourly = aligned.copy()
    hourly["hour"] = hourly["dtime"].dt.floor("h")
    hourly = hourly.groupby(["unit_id", "month", "url", "hour"]).agg(
        tp=("throughput_mbps", "median"),
        lt=("load_time_ms", "median"),
    ).dropna().reset_index()

    tis_records = []

    for (unit_id, month), grp in hourly.groupby(["unit_id", "month"]):
        high_count = 0
        for site in WEBSITES:
            site_data = grp[grp["url"] == site]
            if len(site_data) < 30:
                continue
            if site_data["tp"].nunique() < 2:
                continue
            if site_data["lt"].nunique() < 2:
                continue
            r, _ = pearsonr(site_data["tp"], site_data["lt"])
            if r < -TIS_R_THRESH:
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
    print(f"TIS count distribution: {df['tis_high_corr_count'].value_counts().sort_index().to_dict()}")

    df.to_parquet(os.path.join(PROCESSED_DIR, "tis.parquet"))
    print("Saved tis.parquet")

if __name__ == "__main__":
    main()
