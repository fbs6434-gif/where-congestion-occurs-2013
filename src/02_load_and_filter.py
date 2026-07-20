"""
Load raw CSVs, merge unit metadata, filter to DSL/Cable.
"""
import os
import pandas as pd
from config import DATA_DIR, MONTHS, YEAR, KEEP_TECHNOLOGIES, OUTPUT_DIR

def load_month(month):
    base = os.path.join(DATA_DIR, month)
    tcp = pd.read_csv(os.path.join(base, "tcp_download.csv"),
                      usecols=["unit_id", "timestamp", "throughput_mbps"])
    web = pd.read_csv(os.path.join(base, "web_page_load.csv"),
                      usecols=["unit_id", "timestamp", "url", "load_time_ms"])
    meta = pd.read_csv(os.path.join(base, "unit_census.csv"))
    tcp["month"] = month
    web["month"] = month
    return tcp, web, meta

def main():
    os.makedirs(os.path.join(OUTPUT_DIR, "tables"), exist_ok=True)

    all_tcp = []
    all_web = []
    meta = None

    for month in MONTHS:
        tcp, web, m = load_month(month)
        all_tcp.append(tcp)
        all_web.append(web)
        if meta is None:
            meta = m
        else:
            meta = pd.concat([meta, m]).drop_duplicates("unit_id")

    tcp = pd.concat(all_tcp, ignore_index=True)
    web = pd.concat(all_web, ignore_index=True)

    meta = meta[meta["technology"].str.lower().isin(KEEP_TECHNOLOGIES)]
    tcp = tcp[tcp["unit_id"].isin(meta["unit_id"])]
    web = web[web["unit_id"].isin(meta["unit_id"])]

    print(f"Units after technology filter: {meta['unit_id'].nunique()}")
    print(f"TCP rows: {len(tcp)}")
    print(f"Web rows: {len(web)}")

    os.makedirs(os.path.join(DATA_DIR, "processed"), exist_ok=True)
    tcp.to_parquet(os.path.join(DATA_DIR, "processed", "tcp.parquet"))
    web.to_parquet(os.path.join(DATA_DIR, "processed", "web.parquet"))
    meta.to_parquet(os.path.join(DATA_DIR, "processed", "meta.parquet"))

    print("Saved processed parquet files.")

if __name__ == "__main__":
    main()
