import os
import gc
import pandas as pd
from config import PROCESSED_DIR, ALIGNMENT_WINDOW_HOURS, MIN_MATCHED_RUNS, MONTH, OUTPUT_DIR

TMP_DIR = os.path.join(PROCESSED_DIR, "_align_tmp")
CHUNKS_DIR = os.path.join(PROCESSED_DIR, "web_chunks")
BATCH_SIZE = 200


def ensure_web_chunks():
    """Create web_chunks from web.parquet if the directory is missing/empty."""
    if os.path.isdir(CHUNKS_DIR) and any(f.endswith(".parquet") for f in os.listdir(CHUNKS_DIR)):
        return
    os.makedirs(CHUNKS_DIR, exist_ok=True)
    web = pd.read_parquet(os.path.join(PROCESSED_DIR, "web.parquet"))
    web = web.sort_values("unit_id")
    units = web["unit_id"].unique()
    chunk_units = 400
    for i in range(0, len(units), chunk_units):
        uids = units[i:i + chunk_units]
        part = web[web["unit_id"].isin(uids)]
        part.to_parquet(os.path.join(CHUNKS_DIR, f"chunk_{i // chunk_units:04d}.parquet"))
        print(f"  Wrote web chunk {i // chunk_units:04d}: {len(part)} rows")
    del web
    gc.collect()

def main():
    os.makedirs(TMP_DIR, exist_ok=True)
    ensure_web_chunks()

    meta = pd.read_parquet(os.path.join(PROCESSED_DIR, "meta_valid.parquet"))
    valid_ids = set(meta["unit_id"].tolist())
    del meta
    gc.collect()

    tcp = pd.read_parquet(os.path.join(PROCESSED_DIR, "tcp.parquet"))
    tcp = tcp[tcp["unit_id"].isin(valid_ids)]
    tcp = tcp.sort_values("dtime").reset_index(drop=True)
    tcp_by_unit = {uid: g for uid, g in tcp.groupby("unit_id")}
    del tcp
    gc.collect()

    window = pd.Timedelta(hours=ALIGNMENT_WINDOW_HOURS)
    batch = []
    batch_idx = 0

    # Process each web chunk separately
    chunk_files = sorted(os.listdir(CHUNKS_DIR))
    for chunk_file in chunk_files:
        if not chunk_file.endswith(".parquet"):
            continue
        web = pd.read_parquet(os.path.join(CHUNKS_DIR, chunk_file))
        web = web[web["unit_id"].isin(valid_ids)]
        if len(web) == 0:
            del web
            gc.collect()
            continue

        for uid, web_grp in web.groupby("unit_id"):
            tcp_grp = tcp_by_unit.get(uid)
            if tcp_grp is None:
                continue
            web_grp = web_grp.sort_values("dtime").reset_index(drop=True)
            tcp_r = tcp_grp[["dtime", "throughput_mbps"]].copy()
            tcp_r["tcp_dtime"] = tcp_r["dtime"]
            aligned = pd.merge_asof(
                web_grp[["dtime", "url", "load_time_ms"]],
                tcp_r,
                on="dtime", direction="nearest", tolerance=window,
            ).dropna(subset=["throughput_mbps"])
            aligned["unit_id"] = uid
            aligned["month"] = MONTH
            batch.append(aligned)
            if len(batch) >= BATCH_SIZE:
                pd.concat(batch, ignore_index=True).to_parquet(
                    os.path.join(TMP_DIR, f"batch_{batch_idx:04d}.parquet"))
                batch = []
                batch_idx += 1
                gc.collect()

        del web
        gc.collect()
        print(f"  Processed chunk {chunk_file}, {batch_idx} batches written")

    if batch:
        pd.concat(batch, ignore_index=True).to_parquet(
            os.path.join(TMP_DIR, f"batch_{batch_idx:04d}.parquet"))
        print(f"  Wrote final batch {batch_idx+1}")

    del tcp_by_unit, batch
    gc.collect()

    print("Computing completeness filter from batches...")
    # Compute valid unit/month combos without loading all data at once.
    # Paper: a "matching pair" is one scheduled test run (benchmark matched with
    # a website measurement); require >= MIN_MATCHED_RUNS distinct matched runs.
    count_pieces = []
    for f in sorted(os.listdir(TMP_DIR)):
        if not f.endswith(".parquet"):
            continue
        batch = pd.read_parquet(os.path.join(TMP_DIR, f), columns=["unit_id", "month", "tcp_dtime"])
        counts = batch.groupby(["unit_id", "month"])["tcp_dtime"].nunique().reset_index(name="total_count")
        count_pieces.append(counts)
        del batch
    total_counts = pd.concat(count_pieces, ignore_index=True)
    total_counts = total_counts.groupby(["unit_id", "month"]).agg({"total_count": "sum"}).reset_index()
    valid_units = total_counts[total_counts["total_count"] >= MIN_MATCHED_RUNS][["unit_id", "month"]]
    del total_counts, count_pieces
    gc.collect()
    print(f"Valid unit-month combos: {len(valid_units)}")

    # Read and filter each batch, writing directly to final aligned
    aligned_pieces = []
    for f in sorted(os.listdir(TMP_DIR)):
        if not f.endswith(".parquet"):
            continue
        batch = pd.read_parquet(os.path.join(TMP_DIR, f))
        batch = batch.merge(valid_units, on=["unit_id", "month"])
        aligned_pieces.append(batch)
        os.remove(os.path.join(TMP_DIR, f))
        del batch
        gc.collect()
    os.rmdir(TMP_DIR)

    aligned = pd.concat(aligned_pieces, ignore_index=True)
    del aligned_pieces
    gc.collect()
    print(f"Aligned pairs after completeness filter: {len(aligned)}")
    print(f"Unique units: {aligned['unit_id'].nunique()}")
    print(f"Unique (unit, url) pairs: {aligned[['unit_id', 'url']].drop_duplicates().shape[0]}")

    aligned.to_parquet(os.path.join(PROCESSED_DIR, "aligned.parquet"))
    print("Saved aligned.parquet")

if __name__ == "__main__":
    main()
