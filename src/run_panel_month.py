#!/usr/bin/env python3
"""Process a single (dataset, year, month) of FCC MBA data into panel rows.

Downloads the month's tarball and unit profile from S3, runs the correct step
chain (raw or validated), computes the 4 panel rows (cable/dsl/fiber/overall),
appends them to the worker's part CSV (data/panel_parts/<worker>.csv), uploads
that part back to S3, then deletes all local data.

Usage:
  python3 run_panel_month.py <dataset> <year> <month> <worker>
    dataset : raw | validated
    year    : 2011..2023
    month   : 1..12
    worker  : worker id (e.g. worker-1) used to name the part file
"""
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile

import boto3
import pandas as pd
from botocore.config import Config

import monthly_config as mc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")
SRC_DIR = os.path.join(BASE_DIR, "src")
LOG_DIR = os.path.join(BASE_DIR, "data", "logs")
BUCKET = "mba-data"
PARTS_PREFIX = "where-congestion-occurs-2013/panel_parts"

TECH_MAP = {"uverse": "dsl", "ipbb": "dsl"}
KEEP_TECH = ["cable", "dsl", "fiber"]
CSV_COLUMNS = ["data_year", "data_month", "dataset", "technology", "n_units", "rc", "tis"]


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


def extract_tcp_web(tarpath, raw_dir):
    """Locate the tcp/web CSVs inside the tarball by basename prefix, dedup
    repeated header rows, and write them as curr_httpgetmt.csv/curr_webget.csv.
    """
    found = {}
    with tarfile.open(tarpath, "r:gz") as tar:
        for m in tar:
            base = os.path.basename(m.name)
            if not base.endswith(".csv"):
                continue
            if base.startswith("curr_httpgetmt") and "httpgetmt6" not in base:
                found.setdefault("tcp", m.name)
            elif base.startswith("curr_webget") and "webget6" not in base:
                found.setdefault("web", m.name)
    missing = [k for k in ("tcp", "web") if k not in found]
    if missing:
        raise FileNotFoundError(f"missing in tarball: {missing}")

    os.makedirs(raw_dir, exist_ok=True)
    for kind, target in [("tcp", "curr_httpgetmt.csv"), ("web", "curr_webget.csv")]:
        out = os.path.join(raw_dir, target)
        with tarfile.open(tarpath, "r:gz") as tar:
            src = tar.extractfile(found[kind])
            kept = False
            with open(out, "wb") as dst:
                for line in src:
                    if line.startswith(b"unit_id,"):
                        if kept:
                            continue
                        kept = True
                    dst.write(line)
        print(f"  extracted {found[kind]} -> {out} ({os.path.getsize(out):,} bytes)")


def stage_profile(s3, year, month, raw_dir):
    """Download the month's profile, converting Excel profiles to CSV.

    Returns the local profile filename to pass as META_SOURCE_OVERRIDE.
    """
    fname, key, engine, _ = mc.profile(year, month)
    if engine is None:
        dst = os.path.join(raw_dir, fname)
        os.makedirs(raw_dir, exist_ok=True)
        s3.download_file(BUCKET, key, dst)
        return fname
    tmp = os.path.join(tempfile.gettempdir(), os.path.basename(key))
    s3.download_file(BUCKET, key, tmp)
    try:
        df = pd.read_excel(tmp, engine=engine)
    except Exception:
        df = None
        for alt in ("xlrd", "openpyxl", "calamine"):
            if alt == engine:
                continue
            try:
                df = pd.read_excel(tmp, engine=alt)
                break
            except Exception:
                continue
        if df is None:
            raise RuntimeError(f"could not read profile {key}")
    os.remove(tmp)
    os.makedirs(raw_dir, exist_ok=True)
    out = os.path.join(raw_dir, "unit_profile.csv")
    df.to_csv(out, index=False)
    print(f"  staged profile {fname} -> {out} ({len(df)} rows)")
    return "unit_profile.csv"


def run_step(step, env, logf):
    proc = subprocess.run([sys.executable, os.path.join(SRC_DIR, step)],
                          env=env, capture_output=True, text=True)
    tail = (proc.stdout + proc.stderr).strip().splitlines()[-6:]
    for line in tail:
        print(f"    {line}")
    if logf:
        logf.write(proc.stdout + proc.stderr)
        logf.flush()
    if proc.returncode != 0:
        raise RuntimeError(f"{step} failed (rc={proc.returncode})")


def compute_rows(year, month, dataset, proc_dir):
    """Derive the 4 panel rows from rc/tis/meta_valid parquets."""
    rc = pd.read_parquet(os.path.join(proc_dir, "rc.parquet"), columns=["unit_id", "rc"])
    tis = pd.read_parquet(os.path.join(proc_dir, "tis.parquet"), columns=["unit_id", "tis"])
    meta = pd.read_parquet(os.path.join(proc_dir, "meta_valid.parquet"),
                           columns=["unit_id", "technology"])
    merged = rc.merge(tis, on="unit_id", how="inner").merge(meta, on="unit_id", how="inner")
    merged["tech_norm"] = merged["technology"].astype(str).str.strip().str.lower().map(TECH_MAP)
    merged["tech_norm"] = merged["tech_norm"].fillna(
        merged["technology"].astype(str).str.strip().str.lower())

    rows = []
    groups = {"overall": merged}
    for tech in KEEP_TECH:
        groups[tech] = merged[merged["tech_norm"] == tech]
    for tech, sub in groups.items():
        rows.append({"data_year": year, "data_month": month, "dataset": dataset,
                     "technology": tech, "n_units": len(sub), "rc": int(sub["rc"].sum()),
                     "tis": int(sub["tis"].sum())})
    return rows


def merge_into_part(rows, part_csv):
    """Append rows to the worker part CSV, dedup on the panel key."""
    new_df = pd.DataFrame(rows, columns=CSV_COLUMNS)
    if os.path.isfile(part_csv):
        existing = pd.read_csv(part_csv)
        seen = set(zip(existing["data_year"], existing["data_month"],
                       existing["dataset"], existing["technology"]))
        new_df = new_df[~new_df.apply(
            lambda r: (r["data_year"], r["data_month"], r["dataset"], r["technology"]) in seen,
            axis=1,
        )]
        df = pd.concat([existing, new_df], ignore_index=True)
    else:
        df = new_df
    df = df.sort_values(CSV_COLUMNS[:4]).reset_index(drop=True)
    df.to_csv(part_csv, index=False)
    return len(new_df)


def _emit_rows(year, month, dataset, worker, rows, s3):
    """Merge rows into the worker part CSV and upload to S3. Returns rows."""
    parts_dir = os.path.join(BASE_DIR, "data", "panel_parts")
    os.makedirs(parts_dir, exist_ok=True)
    part_csv = os.path.join(parts_dir, f"{worker}.csv")
    added = merge_into_part(rows, part_csv)
    print(f"  merged: {added} rows into {part_csv} (total {len(rows)-added} dup)")
    s3.upload_file(part_csv, BUCKET, f"{PARTS_PREFIX}/{worker}.csv")
    print(f"  uploaded panel_parts/{worker}.csv")
    return rows


def process(dataset, year, month, worker, s3, logf):
    tarpath = None
    raw_root = os.path.join(BASE_DIR, "data", "raw", f"{dataset}-{year}-{month:02d}")
    proc_root = os.path.join(BASE_DIR, "data", "processed", f"{dataset}-{year}-{month:02d}")
    out_root = os.path.join(BASE_DIR, "output", f"{dataset}-{year}-{month:02d}")
    raw_bk_root = os.path.join(BASE_DIR, "data", "raw_bk", f"raw-{year}-{month:02d}")
    try:
        env = {**os.environ, "YEAR": str(year), "MONTH": str(month), "DATASET": dataset}
        env["SKIP_PLAN_CHANGE_FILTER"] = "0" if dataset == "raw" else "1"
        print(f"=== {year}-{month:02d} {dataset} (worker {worker}) ===")

        row = mc.tarball(dataset, year, month)
        tarpath = os.path.join(tempfile.gettempdir(), row["filename"])
        print(f"  downloading {row['s3_key']}")
        s3.download_file(BUCKET, row["s3_key"], tarpath)

        profile_override = stage_profile(s3, year, month, raw_root)
        env["META_SOURCE_OVERRIDE"] = profile_override

        if dataset == "validated":
            extract_tcp_web(tarpath, raw_root)
            os.remove(tarpath)
            tarpath = None
            steps = ["02_load_and_filter.py", "03_detect_speed_tier.py",
                     "04_align_time_series.py", "05_compute_rc.py",
                     "06_compute_tis.py", "07_aggregate.py"]
        else:
            # Some raw months are missing the tcp/web CSVs entirely in FCC's
            # archive (e.g. 2016-07 has no curr_webget; 2023-03 tarball is
            # truncated). Without both tcp and web there are no aligned pairs,
            # so RC/TIS can't be computed. Detect this up front and emit 0-unit
            # rows, keeping the panel structurally complete.
            with tarfile.open(tarpath, "r:gz") as tar:
                bases = [os.path.basename(m.name) for m in tar]
            has_tcp = any(b.startswith("curr_httpgetmt") and "httpgetmt6" not in b
                          and b.endswith(".csv") for b in bases)
            has_web = any(b.startswith("curr_webget") and "webget6" not in b
                          and b.endswith(".csv") for b in bases)
            if not has_tcp or not has_web:
                print(f"  raw month missing members tcp={has_tcp} web={has_web}; "
                      f"emitting 0-unit rows")
                rows = [{"data_year": year, "data_month": month, "dataset": dataset,
                         "technology": t, "n_units": 0, "rc": 0, "tis": 0}
                        for t in KEEP_TECH + ["overall"]]
                for r in rows:
                    print(f"  {r['technology']:>8}: n=0 rc=0 tis=0")
                return bool(_emit_rows(year, month, dataset, worker, rows, s3))

            os.makedirs(raw_bk_root, exist_ok=True)
            shutil.move(tarpath, os.path.join(raw_bk_root, row["filename"]))
            tarpath = None
            steps = ["01b_load_raw.py", "02_raw_meta.py", "03_detect_speed_tier.py",
                     "04_align_time_series.py", "05_compute_rc.py",
                     "06_compute_tis.py", "07_aggregate.py"]

        for i, step in enumerate(steps):
            print(f"  running {step}")
            run_step(step, env, logf)
            # For raw runs, the tcp/web load step produces web.parquet. If a
            # month has NO web measurements in FCC's archive (missing or empty
            # curr_webget), RC/TIS cannot be computed: there are no tcp+web
            # aligned pairs. Emit 0-unit rows so the panel stays structurally
            # complete and the real data gap is visible.
            if dataset == "raw" and i == 0:
                web_path = os.path.join(proc_root, "web.parquet")
                if os.path.isfile(web_path) and len(pd.read_parquet(web_path)) == 0:
                    print("  no web measurements this month; emitting 0-unit rows")
                    rows = [{"data_year": year, "data_month": month, "dataset": dataset,
                             "technology": t, "n_units": 0, "rc": 0, "tis": 0}
                            for t in KEEP_TECH + ["overall"]]
                    for r in rows:
                        print(f"  {r['technology']:>8}: n=0 rc=0 tis=0")
                    return bool(_emit_rows(year, month, dataset, worker, rows, s3))

        os.makedirs(os.path.join(out_root, "tables"), exist_ok=True)

        rows = compute_rows(year, month, dataset, proc_root)
        for r in rows:
            print(f"  {r['technology']:>8}: n={r['n_units']} rc={r['rc']} tis={r['tis']}")

        _emit_rows(year, month, dataset, worker, rows, s3)
        return True
    finally:
        shutil.rmtree(raw_root, ignore_errors=True)
        shutil.rmtree(proc_root, ignore_errors=True)
        shutil.rmtree(out_root, ignore_errors=True)
        shutil.rmtree(raw_bk_root, ignore_errors=True)
        if tarpath and os.path.exists(tarpath):
            os.remove(tarpath)
        print("  cleaned local data")


def main():
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    dataset, year, month, worker = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    if not mc.month_exists(dataset, year, month):
        print(f"SKIP: no {dataset} month {year}-{month} in manifest")
        return
    env = load_env()
    s3 = s3_client(env)
    os.makedirs(LOG_DIR, exist_ok=True)
    logpath = f"{LOG_DIR}/panel_{dataset}_{year}_{month:02d}_{worker}.log"
    with open(logpath, "a") as logf:
        logf.write(f"\n=== {year}-{month:02d} {dataset} start {pd.Timestamp.now()} ===\n")
        try:
            ok = process(dataset, year, month, worker, s3, logf)
            logf.write(f"=== {year}-{month:02d} {dataset} done {pd.Timestamp.now()} ===\n")
        except Exception as e:
            import traceback
            traceback.print_exc()
            logf.write(f"=== {year}-{month:02d} {dataset} FAILED: {e}\n")
            ok = False
    print("RESULT:", "OK" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()