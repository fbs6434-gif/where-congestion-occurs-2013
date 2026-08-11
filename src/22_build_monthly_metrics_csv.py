"""Build a per-month congestion metrics CSV from precomputed S3 parquets.

For every (data year, data month, validated/raw) pair, downloads the already
computed rc.parquet / tis.parquet / meta_valid.parquet from object storage to a
local temp dir, aggregates unit counts and RC/TIS counts by technology, appends
rows to output/congestion_metrics.csv, then deletes the local copies.

RC/TIS values are unit COUNTS (number of units flagged recurrently congested /
tight initial segment), matching the RC/TIS columns in isp_agg.parquet.

Technology semantics:
  - "overall": every unit in the rc∩tis fleet, regardless of technology label.
  - "cable"/"dsl"/"fiber": only units of that technology, after mapping the
    copper-class labels uverse/ipbb to dsl (matches 13_compare_raw_validated.py).

Validated months are probed across candidate S3 prefixes and skipped (with a
warning) until their parquets appear, so re-running after the raw/validated data
landing process picks them up automatically.
"""
import os
import sys
import tempfile

import boto3
import pandas as pd
from botocore.config import Config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")
BUCKET = "mba-data"
PREFIX = "where-congestion-occurs-2013"
OUT_CSV = os.path.join(BASE_DIR, "output", "congestion_metrics.csv")

# Analysis-year labels used across the project's trend tables
# (2011=Mar, 2012=Apr, 2013+ = Sep). The 2022 row is the Sept-2021 collection.
MONTHS = {
    "validated": [(2011, 3), (2012, 4)] + [(y, 9) for y in range(2013, 2024)],
    "raw": [(2011, m) for m in (3, 4, 5, 6)] + [(2012, 4)] + [(y, 9) for y in range(2013, 2023)],
}

MONTH_NAMES = {3: "march", 4: "april", 5: "may", 6: "june", 9: "september"}

# S3 key prefixes, in probe order, for each dataset/year.
# For raw months the keys are fixed and verified present in S3.
# 2011-03 uses processed/2011_march (the paper-reproduction set incl. fiber),
# consistent with 2011-04/05/06; data/processed/2011 is an older fiber-free run.
RAW_PREFIXES = {
    2011: {3: "processed/2011_march",
           4: "processed/2011_april",
           5: "processed/2011_may",
           6: "processed/2011_june"},
    2012: {4: "data/processed/2012"},
}
for y in range(2013, 2023):
    RAW_PREFIXES[y] = {9: f"data/processed/{y}"}

# Validated months are probed over these candidates. data/processed/<year> is
# ONLY valid for 2023 (raw exists for every other year, so we must not fall
# back to it, or raw output would be mislabeled validated).
VALIDATED_PREFIXES = [
    lambda y: f"data/validated_backup/processed/{y}",
    lambda y: f"data/validated/processed/{y}",
    lambda y: f"data/processed_validated/{y}",
]
VALIDATED_PREFIXES_2023 = [
    lambda y: f"data/processed/{y}",
]

TECH_MAP = {"uverse": "dsl", "ipbb": "dsl"}
KEEP_TECH = ["cable", "dsl", "fiber"]
CSV_COLUMNS = ["data_year", "data_month", "dataset", "n_units", "rc", "tis", "technology"]


def load_env():
    env = {}
    with open(ENV_PATH) as fh:
        for line in fh:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k] = v
    return env


def s3_client(env):
    endpoint = (env.get("AWS_ENDPOINT_URL") or env.get("S3_ENDPOINT_URL")
                or env.get("AWS_ENDPOINT_URL_S3"))
    return boto3.client(
        "s3",
        aws_access_key_id=env["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=env["AWS_SECRET_ACCESS_KEY"],
        endpoint_url=endpoint,
        config=Config(signature_version="s3v4"),
    )


def key_exists(s3, key):
    try:
        s3.head_object(Bucket=BUCKET, Key=key)
        return True
    except Exception:
        return False


def resolve_prefix(s3, dataset, year, month):
    """Return the S3 prefix holding this month's parquets, or None if absent.

    Validated months NEVER fall back to data/processed/<year> for 2011-2022,
    because that prefix holds the raw pipeline output (mislabeling hazard).
    2023 is the exception: it has no raw data, so data/processed/2023 is the
    validated home.
    """
    base = PREFIX + "/"
    if dataset == "raw":
        cands = [RAW_PREFIXES.get(year, {}).get(month)]
    else:
        factories = VALIDATED_PREFIXES if year != 2023 else VALIDATED_PREFIXES_2023
        cands = [f(year) for f in factories]
    for cand in cands:
        if cand is None:
            continue
        if key_exists(s3, f"{base}{cand}/rc.parquet"):
            return cand
    return None


def download(s3, prefix, tmpdir):
    local = {}
    for f in ("rc.parquet", "tis.parquet", "meta_valid.parquet"):
        dst = os.path.join(tmpdir, f)
        s3.download_file(BUCKET, f"{PREFIX}/{prefix}/{f}", dst)
        local[f] = dst
    return local


def compute_month(local, dataset, year, month):
    rc = pd.read_parquet(local["rc.parquet"], columns=["unit_id", "rc"])
    tis = pd.read_parquet(local["tis.parquet"], columns=["unit_id", "tis"])
    meta = pd.read_parquet(local["meta_valid.parquet"], columns=["unit_id", "technology"])

    merged = rc.merge(tis, on="unit_id", how="inner").merge(meta, on="unit_id", how="inner")
    merged["tech_norm"] = merged["technology"].astype(str).str.strip().str.lower().map(TECH_MAP)
    merged["tech_norm"] = merged["tech_norm"].fillna(
        merged["technology"].astype(str).str.strip().str.lower())

    rows = []
    groups = {"overall": merged}
    for tech in KEEP_TECH:
        groups[tech] = merged[merged["tech_norm"] == tech]
    for tech, sub in groups.items():
        rows.append({
            "data_year": year,
            "data_month": month,
            "dataset": dataset,
            "n_units": len(sub),
            "rc": int(sub["rc"].sum()),
            "tis": int(sub["tis"].sum()),
            "technology": tech,
        })
    return rows


def load_existing():
    if os.path.isfile(OUT_CSV):
        existing = pd.read_csv(OUT_CSV, dtype={"data_year": int, "data_month": int})
        return set(zip(existing["data_year"], existing["data_month"],
                       existing["dataset"], existing["technology"]))
    return set()


def main():
    env = load_env()
    s3 = s3_client(env)
    existing = load_existing()

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    header = not os.path.isfile(OUT_CSV)

    processed = 0
    missing = []
    appended_rows = []

    for dataset in ("validated", "raw"):
        for year, month in MONTHS[dataset]:
            prefix = resolve_prefix(s3, dataset, year, month)
            if prefix is None:
                missing.append((year, month, dataset))
                print(f"MISSING {year}-{month:02d} {dataset}: rc.parquet not in S3 (skipped)")
                continue

            with tempfile.TemporaryDirectory(prefix="mba_metrics_") as tmpdir:
                local = download(s3, prefix, tmpdir)
                rows = compute_month(local, dataset, year, month)
                new_rows = [r for r in rows
                            if (r["data_year"], r["data_month"], r["dataset"], r["technology"])
                            not in existing]
                appended_rows.extend(new_rows)
                existing |= {(r["data_year"], r["data_month"], r["dataset"], r["technology"])
                             for r in new_rows}
                processed += 1
                print(f"OK {year}-{month:02d} {dataset} ({prefix}): "
                      f"n={rows[0]['n_units']} rc={rows[0]['rc']} tis={rows[0]['tis']} "
                      f"({len(new_rows)} new rows)")

    if appended_rows:
        frame = pd.DataFrame(appended_rows, columns=CSV_COLUMNS).sort_values(
            ["data_year", "data_month", "dataset", "technology"])
        frame.to_csv(OUT_CSV, mode="a", header=header, index=False)
    else:
        # Ensure an empty output file still carries the header on first run.
        if header and not os.path.isfile(OUT_CSV):
            pd.DataFrame(columns=CSV_COLUMNS).to_csv(OUT_CSV, index=False)

    print(f"\nProcessed {processed} months, appended {len(appended_rows)} rows -> {OUT_CSV}")
    if missing:
        print(f"Missing (will be picked up when data lands in S3):")
        for y, m, d in missing:
            print(f"  {y}-{m:02d} {d}")


if __name__ == "__main__":
    main()
