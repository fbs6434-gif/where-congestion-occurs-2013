import os
import pandas as pd
from urllib.parse import urlparse
from config import (RAW_DIR, PROCESSED_DIR, KEEP_TECHNOLOGIES,
                    TCP_CSV, WEB_CSV, META_CSV, META_URL, META_ENGINE, YEAR)

BYTES_PER_MEGABIT = 125_000
MICROSECONDS_PER_MILLISECOND = 1000

DOMAIN_MAP = {"edition.cnn.com": "cnn.com"}

def extract_domain(url):
    domain = urlparse(url).netloc.replace("www.", "")
    return DOMAIN_MAP.get(domain, domain)

def load_meta():
    if YEAR == 2011:
        meta = pd.read_csv(os.path.join(RAW_DIR, META_CSV))
        meta.columns = [c.strip().lower() for c in meta.columns]
        meta = meta.rename(columns={
            "unitid": "unit_id",
            "technology": "technology",
            "isp down": "speed_tier_down",
        })
    elif YEAR == 2014:
        meta = pd.read_excel(META_URL, engine=META_ENGINE)
        meta = meta.rename(columns={
            "unit_id": "unit_id",
            "isp": "isp",
            "TECHNOLOGY": "technology",
            "SK down": "speed_tier_down",
        })
    elif YEAR == 2019:
        meta = pd.read_excel(META_URL, engine=META_ENGINE)
        meta = meta.rename(columns={
            "Unit ID": "unit_id",
            "ISP": "isp",
            "Technology": "technology",
            "Download": "speed_tier_down",
        })

    meta["technology"] = meta["technology"].str.strip().str.lower()
    if KEEP_TECHNOLOGIES is not None:
        meta = meta[meta["technology"].isin(KEEP_TECHNOLOGIES)].copy()
    print(f"Units loaded: {len(meta)}")
    print(f"Technologies: {meta['technology'].value_counts().to_dict()}")
    meta["speed_tier_down"] = pd.to_numeric(meta["speed_tier_down"], errors="coerce")
    meta = meta[meta["speed_tier_down"].notna() & (meta["speed_tier_down"] > 0)]
    print(f"Units after known speed tier filter: {len(meta)}")
    print(f"Technologies found: {meta['technology'].value_counts().to_dict()}")
    return meta

def load_tcp_chunked(valid_ids, chunksize=500_000):
    cols = ["unit_id", "dtime", "bytes_sec"]
    fpath = os.path.join(RAW_DIR, TCP_CSV)
    if YEAR == 2014:
        # No header row — specify names from SQL schema
        all_cols = ["unit_id", "dtime", "target", "address", "fetch_time",
                    "bytes_total", "bytes_sec", "bytes_sec_interval", "warmup_time",
                    "warmup_bytes", "sequence", "threads", "successes", "failures", "location_id"]
        reader = pd.read_csv(fpath, names=all_cols, usecols=cols, chunksize=chunksize)
    else:
        reader = pd.read_csv(fpath, usecols=cols, chunksize=chunksize)

    pieces = []
    for i, chunk in enumerate(reader):
        chunk = chunk[chunk["unit_id"].isin(valid_ids)]
        if len(chunk):
            chunk["dtime"] = pd.to_datetime(chunk["dtime"])
            chunk["throughput_mbps"] = chunk["bytes_sec"] / BYTES_PER_MEGABIT
            piece = chunk[["unit_id", "dtime", "throughput_mbps"]].copy()
            pieces.append(piece)
        if (i + 1) % 10 == 0:
            print(f"  TCP chunk {i+1}: {len(chunk)} rows")
    return pd.concat(pieces, ignore_index=True)

def load_web_chunked(valid_ids, chunksize=500_000):
    cols = ["unit_id", "dtime", "target", "fetch_time"]
    fpath = os.path.join(RAW_DIR, WEB_CSV)
    if YEAR == 2014:
        all_cols = ["unit_id", "dtime", "target", "address", "fetch_time",
                    "bytes_total", "bytes_sec", "objects", "threads", "requests",
                    "connections", "reused_connections", "lookups", "request_total_time",
                    "request_min_time", "request_avg_time", "request_max_time",
                    "ttfb_total", "ttfb_min", "ttfb_avg", "ttfb_max",
                    "lookup_total_time", "lookup_min_time", "lookup_avg_time", "lookup_max_time",
                    "successes", "failures", "location_id"]
        reader = pd.read_csv(fpath, names=all_cols, usecols=cols, chunksize=chunksize)
    else:
        reader = pd.read_csv(fpath, usecols=cols, chunksize=chunksize)

    pieces = []
    for i, chunk in enumerate(reader):
        chunk = chunk[chunk["unit_id"].isin(valid_ids)]
        if len(chunk):
            chunk["dtime"] = pd.to_datetime(chunk["dtime"])
            chunk["url"] = chunk["target"].apply(extract_domain)
            chunk["load_time_ms"] = chunk["fetch_time"] / MICROSECONDS_PER_MILLISECOND
            pieces.append(chunk[["unit_id", "dtime", "url", "load_time_ms"]])
        if (i + 1) % 10 == 0:
            print(f"  Web chunk {i+1}: {len(chunk)} rows")
    return pd.concat(pieces, ignore_index=True)

def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    meta = load_meta()
    valid_ids = set(meta["unit_id"])
    print(f"Valid unit IDs: {len(valid_ids)}")

    print("Loading TCP (M-Lab throughput) in chunks...")
    tcp = load_tcp_chunked(valid_ids)
    tcp = tcp.groupby(["unit_id", "dtime"], as_index=False)["throughput_mbps"].median()
    print(f"TCP rows after filter + aggregation: {len(tcp)}")

    print("Loading Web (website load) in chunks...")
    web = load_web_chunked(valid_ids)
    print(f"Web rows after filter: {len(web)}")

    tcp.to_parquet(os.path.join(PROCESSED_DIR, "tcp.parquet"))
    web.to_parquet(os.path.join(PROCESSED_DIR, "web.parquet"))
    meta.to_parquet(os.path.join(PROCESSED_DIR, "meta.parquet"))
    print("Saved processed parquet files.")

if __name__ == "__main__":
    main()
