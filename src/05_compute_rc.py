"""
Compute Recurrent Congestion (RC) per unit-month.

Memory-bounded: aligned.parquet is read in row-group chunks and merged with the
(small) meta table incrementally, accumulating sum/count of "bad" pairs per
(unit_id, month) so peak RAM stays O(chunk) instead of O(aligned).
"""
import os
import pandas as pd
import numpy as np
import pyarrow.parquet as pq
from config import PROCESSED_DIR, RC_Q, RC_T

CHUNK_ROWS = 2_000_000

def main():
    meta = pd.read_parquet(os.path.join(PROCESSED_DIR, "meta_valid.parquet"),
                           columns=["unit_id", "month", "speed_tier"])
    meta = meta[meta["speed_tier"] > 0]
    if len(meta) == 0:
        df = pd.DataFrame(columns=["unit_id", "month", "rc", "rc_fraction", "speed_tier"])
        df.to_parquet(os.path.join(PROCESSED_DIR, "rc.parquet"))
        print("RC records: 0")
        print("Saved rc.parquet")
        return

    pf = pq.ParquetFile(os.path.join(PROCESSED_DIR, "aligned.parquet"))
    cols = ["unit_id", "month", "throughput_mbps"]
    pieces = []
    for batch in pf.iter_batches(batch_size=CHUNK_ROWS, columns=cols):
        chunk = batch.to_pandas()
        chunk = chunk.merge(meta, on=["unit_id", "month"])
        chunk = chunk[chunk["speed_tier"] > 0]
        if len(chunk) == 0:
            continue
        chunk["bad"] = (chunk["throughput_mbps"] / chunk["speed_tier"]) < RC_Q
        agg = chunk.groupby(["unit_id", "month"], sort=False).agg(
            bad_sum=("bad", "sum"), n=("bad", "size"),
            speed_tier=("speed_tier", "first")).reset_index()
        pieces.append(agg)
        del chunk, agg
    del pf

    if not pieces:
        df = pd.DataFrame(columns=["unit_id", "month", "rc", "rc_fraction", "speed_tier"])
        df.to_parquet(os.path.join(PROCESSED_DIR, "rc.parquet"))
        print("RC records: 0")
        print("Saved rc.parquet")
        return

    total = pd.concat(pieces, ignore_index=True)
    total = total.groupby(["unit_id", "month"], sort=False).agg(
        bad_sum=("bad_sum", "sum"), n=("n", "sum"),
        speed_tier=("speed_tier", "first")).reset_index()
    total["rc_fraction"] = total["bad_sum"] / total["n"]
    total["rc"] = total["rc_fraction"] > RC_T
    df = total[["unit_id", "month", "rc", "rc_fraction", "speed_tier"]]
    print(f"RC records: {len(df)}")
    print(f"RC prevalence: {df['rc'].mean():.2%}")

    df.to_parquet(os.path.join(PROCESSED_DIR, "rc.parquet"))
    print("Saved rc.parquet")

if __name__ == "__main__":
    main()