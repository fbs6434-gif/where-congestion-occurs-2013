import os
import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from config import PROCESSED_DIR, WEBSITES, TIS_R_THRESH, TIS_COUNT_THRESH, OUTPUT_DIR

def main():
    tcp = pd.read_parquet(os.path.join(PROCESSED_DIR, "tcp.parquet"))
    web = pd.read_parquet(os.path.join(PROCESSED_DIR, "web.parquet"))
    meta = pd.read_parquet(os.path.join(PROCESSED_DIR, "meta_valid.parquet"))

    valid_ids = set(meta["unit_id"])
    tcp = tcp[tcp["unit_id"].isin(valid_ids)]
    web = web[web["unit_id"].isin(valid_ids)]

    tcp["hour"] = tcp["dtime"].dt.floor("h")
    web["hour"] = web["dtime"].dt.floor("h")

    tp_hourly = tcp.groupby(["unit_id", "hour"], as_index=False)["throughput_mbps"].median()
    lt_hourly = web.groupby(["unit_id", "url", "hour"], as_index=False)["load_time_ms"].median()

    del tcp, web

    hourly = tp_hourly.merge(lt_hourly, on=["unit_id", "hour"])
    hourly = hourly.dropna()
    hourly["month"] = "march"

    print(f"Hourly observations: {len(hourly)}")

    tis_records = []

    for unit_id, grp in hourly.groupby("unit_id"):
        high_count = 0
        for site in WEBSITES:
            site_data = grp[grp["url"] == site]
            if len(site_data) < 30:
                continue
            tp = site_data["throughput_mbps"].values
            lt = site_data["load_time_ms"].values
            if tp.nbytes == 0 or lt.nbytes == 0:
                continue
            if np.unique(tp).size < 2 or np.unique(lt).size < 2:
                continue
            r, _ = pearsonr(tp, lt)
            if r < -TIS_R_THRESH:
                high_count += 1

        tis = high_count >= TIS_COUNT_THRESH
        tis_records.append({
            "unit_id": unit_id,
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
