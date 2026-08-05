"""Attach validated unit profile metadata (isp, technology) to ALL raw units.

Raw bulk files carry no isp/technology columns (unless 2011-style, which don't
either in the extracted batch). This builds meta.parquet containing every unit
that appears in the raw tcp/web data, left-joined to the year's validated unit
profile. Units absent from the profile get isp/technology = "unknown" and are
kept in the overall figures but excluded from the per-technology split.
"""
import os
import pandas as pd
from config import (PROCESSED_DIR, META_SOURCE, META_ENGINE, META_COLS, YEAR)
from raw_config import RAWS

UNKNOWN = "unknown"

def build_meta():
    rel = RAWS[YEAR]
    # All raw unit ids.
    tcp = pd.read_parquet(os.path.join(PROCESSED_DIR, "tcp.parquet"))["unit_id"]
    web = pd.read_parquet(os.path.join(PROCESSED_DIR, "web.parquet"))["unit_id"]
    raw_ids = pd.concat([tcp, web]).unique()
    meta = pd.DataFrame({"unit_id": raw_ids})

    # Load the validated profile.
    src = META_SOURCE
    is_url = src.startswith("http://") or src.startswith("https://")
    if not is_url:
        # Local profile: resolve against the validated pipeline's RAW_DIR
        # (e.g. data/raw/2011/validated-march/unit_metadata.csv).
        import config as cfg
        src = os.path.join(cfg.RAW_DIR, src)
    try:
        if is_url:
            prof = pd.read_excel(src, engine=META_ENGINE)
        else:
            prof = pd.read_csv(src)
    except Exception as e:
        print(f"WARN: could not load profile {META_SOURCE}: {e}")
        prof = None

    if prof is not None:
        rename = {src: dst for dst, src in META_COLS.items() if src in prof.columns}
        prof = prof.rename(columns=rename)
        keep = [c for c in ["unit_id", "isp", "technology"] if c in prof.columns]
        prof = prof[keep].drop_duplicates("unit_id")
        meta = meta.merge(prof, on="unit_id", how="left")

    for col in ["isp", "technology"]:
        if col not in meta.columns:
            meta[col] = UNKNOWN
        meta[col] = meta[col].fillna(UNKNOWN)
        meta[col] = meta[col].astype(str).str.strip().str.lower()

    meta["speed_tier_down"] = float("nan")  # tier is estimated from data (step 03)
    meta = meta[["unit_id", "isp", "technology", "speed_tier_down"]]
    out = os.path.join(PROCESSED_DIR, "meta.parquet")
    meta.to_parquet(out)
    print(f"Wrote {out}: {len(meta)} units")
    print(meta["technology"].value_counts().head(15).to_dict())
    return meta


if __name__ == "__main__":
    build_meta()