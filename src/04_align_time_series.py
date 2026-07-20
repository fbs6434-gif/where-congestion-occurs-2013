"""
Align M-Lab throughput measurements with nearest website measurements per unit-month.
"""
import os
import pandas as pd
import numpy as np
from config import DATA_DIR, MONTHS, WEBSITES, ALIGNMENT_WINDOW_HOURS, MIN_MATCHED_PAIRS, OUTPUT_DIR

def main():
    tcp = pd.read_parquet(os.path.join(DATA_DIR, "processed", "tcp.parquet"))
    web = pd.read_parquet(os.path.join(DATA_DIR, "processed", "web.parquet"))
    meta = pd.read_parquet(os.path.join(DATA_DIR, "processed", "meta_valid.parquet"))

    tcp["ts"] = pd.to_datetime(tcp["timestamp"])
    web["ts"] = pd.to_datetime(web["timestamp"])

    tcp = tcp[tcp["unit_id"].isin(meta["unit_id"])]
    web = web[web["unit_id"].isin(meta["unit_id"])]

    tcp = tcp.sort_values(["unit_id", "month", "ts"])
    web = web.sort_values(["unit_id", "month", "ts"])

    rows = []
    window = pd.Timedelta(hours=ALIGNMENT_WINDOW_HOURS)

    for (unit_id, month), tcp_grp in tcp.groupby(["unit_id", "month"]):
        web_grp = web[(web["unit_id"] == unit_id) & (web["month"] == month)]
        if web_grp.empty:
            continue

        for _, tr in tcp_grp.iterrows():
            t_time = tr["ts"]
            mask = (web_grp["ts"] >= t_time - window) & (web_grp["ts"] <= t_time + window)
            candidates = web_grp[mask]
            if candidates.empty:
                continue
            nearest = candidates.iloc[(candidates["ts"] - t_time).abs().argmin()]
            rows.append({
                "unit_id": unit_id,
                "month": month,
                "ts": t_time,
                "throughput_mbps": tr["throughput_mbps"],
                "url": nearest["url"],
                "load_time_ms": nearest["load_time_ms"],
            })

    aligned = pd.DataFrame(rows)
    print(f"Aligned pairs before completeness filter: {len(aligned)}")

    pair_counts = aligned.groupby(["unit_id", "month"]).size().reset_index(name="count")
    valid_units = pair_counts[pair_counts["count"] >= MIN_MATCHED_PAIRS][["unit_id", "month"]]
    aligned = aligned.merge(valid_units, on=["unit_id", "month"])

    print(f"Aligned pairs after completeness filter: {len(aligned)}")
    print(f"Unique units: {aligned['unit_id'].nunique()}")

    aligned.to_parquet(os.path.join(DATA_DIR, "processed", "aligned.parquet"))
    print("Saved aligned.parquet")

if __name__ == "__main__":
    main()
