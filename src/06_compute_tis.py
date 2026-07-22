import os
import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from config import PROCESSED_DIR, WEBSITES, TIS_R_THRESH, TIS_COUNT_THRESH

def main():
    aligned = pd.read_parquet(os.path.join(PROCESSED_DIR, "aligned.parquet"))
    meta = pd.read_parquet(os.path.join(PROCESSED_DIR, "meta_valid.parquet"))
    valid_ids = set(meta["unit_id"])
    aligned = aligned[aligned["unit_id"].isin(valid_ids)]

    print(f"Aligned pairs: {len(aligned)}")
    print(f"Unique units: {aligned['unit_id'].nunique()}")

    # Negative correlation: tight initial segment causes throughput DOWN,
    # website load time UP -> r < -0.6
    tis_records = []
    for uid, grp in aligned.groupby("unit_id"):
        high_count = 0
        for site in WEBSITES:
            site_data = grp[grp["url"] == site]
            if len(site_data) < 30:
                continue
            tp = site_data["throughput_mbps"].values
            lt = site_data["load_time_ms"].values
            if len(tp) < 2 or len(lt) < 2:
                continue
            if np.unique(tp).size < 2 or np.unique(lt).size < 2:
                continue
            r, _ = pearsonr(tp, lt)
            if r < -TIS_R_THRESH:
                high_count += 1

        tis = high_count >= TIS_COUNT_THRESH
        tis_records.append({
            "unit_id": uid,
            "month": "march",
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
