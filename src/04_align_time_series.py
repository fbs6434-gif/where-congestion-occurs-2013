import os
import pandas as pd
from config import PROCESSED_DIR, ALIGNMENT_WINDOW_HOURS, MIN_MATCHED_PAIRS, OUTPUT_DIR

TMP_DIR = os.path.join(PROCESSED_DIR, "_align_tmp")
BATCH_SIZE = 200

def main():
    os.makedirs(TMP_DIR, exist_ok=True)

    tcp = pd.read_parquet(os.path.join(PROCESSED_DIR, "tcp.parquet"))
    web = pd.read_parquet(os.path.join(PROCESSED_DIR, "web.parquet"))
    meta = pd.read_parquet(os.path.join(PROCESSED_DIR, "meta_valid.parquet"))

    valid_ids = set(meta["unit_id"])
    tcp = tcp[tcp["unit_id"].isin(valid_ids)]
    web = web[web["unit_id"].isin(valid_ids)]

    tcp_by_unit = {uid: g.sort_values("dtime").reset_index(drop=True)
                   for uid, g in tcp.groupby("unit_id")}

    del tcp, meta

    window = pd.Timedelta(hours=ALIGNMENT_WINDOW_HOURS)

    batch = []
    batch_idx = 0
    for i, (uid, web_grp) in enumerate(web.groupby("unit_id")):
        tcp_grp = tcp_by_unit.get(uid)
        if tcp_grp is None:
            continue
        web_grp = web_grp.sort_values("dtime").reset_index(drop=True)
        aligned = pd.merge_asof(
            web_grp[["dtime", "url", "load_time_ms"]],
            tcp_grp[["dtime", "throughput_mbps"]],
            on="dtime", direction="nearest", tolerance=window,
        ).dropna(subset=["throughput_mbps"])
        aligned["unit_id"] = uid
        aligned["month"] = "march"
        batch.append(aligned)
        if len(batch) >= BATCH_SIZE:
            pd.concat(batch, ignore_index=True).to_parquet(
                os.path.join(TMP_DIR, f"batch_{batch_idx:04d}.parquet"))
            batch = []
            batch_idx += 1
            print(f"  Wrote batch {batch_idx}, {i+1} units processed")

    if batch:
        pd.concat(batch, ignore_index=True).to_parquet(
            os.path.join(TMP_DIR, f"batch_{batch_idx:04d}.parquet"))
        print(f"  Wrote final batch {batch_idx+1}")

    del web, tcp_by_unit, batch

    print("Reading batches and applying completeness filter...")
    pieces = []
    for f in sorted(os.listdir(TMP_DIR)):
        if f.endswith(".parquet"):
            pieces.append(pd.read_parquet(os.path.join(TMP_DIR, f)))
            os.remove(os.path.join(TMP_DIR, f))
    os.rmdir(TMP_DIR)

    aligned = pd.concat(pieces, ignore_index=True)
    print(f"Aligned pairs before completeness filter: {len(aligned)}")

    pair_counts = aligned.groupby(["unit_id", "month", "url"]).size().reset_index(name="count")
    valid_pairs = pair_counts[pair_counts["count"] >= MIN_MATCHED_PAIRS]
    aligned = aligned.merge(valid_pairs[["unit_id", "month", "url"]], on=["unit_id", "month", "url"])

    print(f"Aligned pairs after completeness filter: {len(aligned)}")
    print(f"Unique units: {aligned['unit_id'].nunique()}")
    print(f"Unique (unit, url) pairs: {aligned[['unit_id', 'url']].drop_duplicates().shape[0]}")

    aligned.to_parquet(os.path.join(PROCESSED_DIR, "aligned.parquet"))
    print("Saved aligned.parquet")

if __name__ == "__main__":
    main()
