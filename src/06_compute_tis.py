import os
import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from config import PROCESSED_DIR, WEBSITES, TIS_R_THRESH, TIS_COUNT_THRESH, MONTH, TIS_MIN_SERIES

def main():
    aligned = pd.read_parquet(os.path.join(PROCESSED_DIR, "aligned.parquet"))
    meta = pd.read_parquet(os.path.join(PROCESSED_DIR, "meta_valid.parquet"))
    valid_ids = set(meta["unit_id"])
    aligned = aligned[aligned["unit_id"].isin(valid_ids)]

    print(f"Aligned pairs: {len(aligned)}")
    print(f"Unique units: {aligned['unit_id'].nunique()}")

    # Positive correlation: "website download speed" is inversely proportional
    # to load_time. When shared bottleneck is congested, TCP throughput DOWN
    # and 1/load_time (website download speed) also DOWN -> r > 0.6
    tis_records = []
    for uid, grp in aligned.groupby("unit_id"):
        high_count = 0
        for site in WEBSITES:
            site_data = grp[grp["url"] == site]
            if len(site_data) < TIS_MIN_SERIES:
                continue
            sd = site_data[site_data["load_time_ms"] > 0]
            if len(sd) < TIS_MIN_SERIES:
                continue
            tp = sd["throughput_mbps"].values
            inv_lt = 1.0 / sd["load_time_ms"].values
            if len(tp) < 2:
                continue
            if np.unique(tp).size < 2 or np.unique(inv_lt).size < 2:
                continue
            r, _ = pearsonr(tp, inv_lt)
            if r > TIS_R_THRESH:
                high_count += 1

        tis = high_count >= TIS_COUNT_THRESH
        tis_records.append({
            "unit_id": uid,
            "month": MONTH,
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
