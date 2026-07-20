import os
import pandas as pd
from urllib.parse import urlparse
from config import RAW_DIR, PROCESSED_DIR, KEEP_TECHNOLOGIES

BYTES_PER_MEGABIT = 125_000  # 1 Mb = 125,000 bytes (1 byte = 8 bits, 1 Mb = 1e6 bits)
MICROSECONDS_PER_MILLISECOND = 1000

DOMAIN_MAP = {
    "edition.cnn.com": "cnn.com",
}

def extract_domain(url):
    domain = urlparse(url).netloc.replace("www.", "")
    return DOMAIN_MAP.get(domain, domain)

def load_meta():
    meta = pd.read_csv(os.path.join(RAW_DIR, "unit_metadata.csv"))
    meta.columns = [c.strip().lower() for c in meta.columns]
    meta = meta.rename(columns={
        "unitid": "unit_id",
        "isp": "isp",
        "technology": "technology",
        "isp down": "speed_tier_down",
        "isp up": "speed_tier_up",
    })
    meta["technology"] = meta["technology"].str.strip().str.lower()
    meta = meta[meta["technology"].isin(KEEP_TECHNOLOGIES)].copy()
    print(f"Units after technology filter: {len(meta)}")
    return meta

def load_tcp_chunked(valid_ids, chunksize=500_000):
    reader = pd.read_csv(
        os.path.join(RAW_DIR, "curr_httpgetmt.csv"),
        usecols=["unit_id", "dtime", "bytes_sec"],
        chunksize=chunksize,
    )
    pieces = []
    for i, chunk in enumerate(reader):
        chunk = chunk[chunk["unit_id"].isin(valid_ids)]
        if len(chunk):
            chunk["month"] = "march"
            chunk["dtime"] = pd.to_datetime(chunk["dtime"])
            chunk["throughput_mbps"] = chunk["bytes_sec"] / BYTES_PER_MEGABIT
            pieces.append(chunk[["unit_id", "month", "dtime", "throughput_mbps"]])
        if (i + 1) % 10 == 0:
            print(f"  TCP chunk {i+1}: {len(chunk) if len(chunk) else 0} rows")
    return pd.concat(pieces, ignore_index=True)

def load_web_chunked(valid_ids, chunksize=500_000):
    reader = pd.read_csv(
        os.path.join(RAW_DIR, "curr_webget.csv"),
        usecols=["unit_id", "dtime", "target", "fetch_time"],
        chunksize=chunksize,
    )
    pieces = []
    for i, chunk in enumerate(reader):
        chunk = chunk[chunk["unit_id"].isin(valid_ids)]
        if len(chunk):
            chunk["month"] = "march"
            chunk["dtime"] = pd.to_datetime(chunk["dtime"])
            chunk["url"] = chunk["target"].apply(extract_domain)
            chunk["load_time_ms"] = chunk["fetch_time"] / MICROSECONDS_PER_MILLISECOND
            pieces.append(chunk[["unit_id", "month", "dtime", "url", "load_time_ms"]])
        if (i + 1) % 10 == 0:
            print(f"  Web chunk {i+1}: {len(chunk) if len(chunk) else 0} rows")
    return pd.concat(pieces, ignore_index=True)

def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    meta = load_meta()
    valid_ids = set(meta["unit_id"])

    print("Loading TCP (M-Lab throughput) in chunks...")
    tcp = load_tcp_chunked(valid_ids)
    tcp = tcp.groupby(["unit_id", "month", "dtime"], as_index=False)["throughput_mbps"].median()
    print(f"M-Lab TCP rows after filter + aggregation: {len(tcp)}")

    print("Loading Web (website load) in chunks...")
    web = load_web_chunked(valid_ids)
    print(f"Web rows after filter: {len(web)}")

    tcp.to_parquet(os.path.join(PROCESSED_DIR, "tcp.parquet"))
    web.to_parquet(os.path.join(PROCESSED_DIR, "web.parquet"))
    meta.to_parquet(os.path.join(PROCESSED_DIR, "meta.parquet"))
    print("Saved processed parquet files.")

if __name__ == "__main__":
    main()
