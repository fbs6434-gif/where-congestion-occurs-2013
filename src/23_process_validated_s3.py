"""Process validated FCC MBA months from S3 (fcc-mba/) into congestion metrics.

For each analysis year, downloads the validated tarball + unit profile from S3,
runs the validated pipeline (02_load_and_filter -> 03_detect_speed_tier ->
04_align_time_series -> 05_compute_rc -> 06_compute_tis), appends per-technology
RC/TIS counts to output/congestion_metrics.csv, then deletes all local data.

Works one month at a time so disk stays bounded (~24 GB peak per month).

Usage: python3 src/23_process_validated_s3.py [YEAR...]
  (no args = all validated years 2011-2023)
"""
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

import boto3
import pandas as pd
from botocore.config import Config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")
SRC_DIR = os.path.join(BASE_DIR, "src")
LOG_DIR = os.path.join(BASE_DIR, "data", "logs")
BUCKET = "mba-data"
FCC_PREFIX = "fcc-mba"
OUT_CSV = os.path.join(BASE_DIR, "output", "congestion_metrics.csv")

# Analysis year -> S3 details (collection year, validated tarball, unit profile,
# Excel engine). Profile names/engines mirror config.py's meta_source/meta_engine.
VALIDATED = {
    2011: {"coll": 2011, "tarball": "validated-march-data-2011.tar.gz",
           "profile": "unit_metadata.csv", "engine": None},
    2012: {"coll": 2012, "tarball": "data-validated--2012-apr.tar.gz",
           "profile": "FCC_UnitProfile_Sept12.xls", "engine": "xlrd"},
    2013: {"coll": 2012, "tarball": "data-validated-2012-sept.tar.gz",
           "profile": "FCC_UnitProfile_Sept12.xls", "engine": "xlrd"},
    2014: {"coll": 2013, "tarball": "data-validated-2013-sept.tar.gz",
           "profile": "FCC_Unit_Profile_20140207.xlsx", "engine": "openpyxl"},
    2015: {"coll": 2014, "tarball": "data-validated-2014-sept.tar.gz",
           "profile": "FCC_UnitProfile_Sept14.xls", "engine": "openpyxl"},
    2016: {"coll": 2015, "tarball": "validated-data-sept2015.tar.gz",
           "profile": "Unit-Profile-sept2015.xlsx", "engine": "openpyxl"},
    2017: {"coll": 2016, "tarball": "validated-data-sept2016.tar.gz",
           "profile": "Unit-Profile-sept2016.xlsx", "engine": "openpyxl"},
    2018: {"coll": 2017, "tarball": "validated-data-sept2017.tar.gz",
           "profile": "Unit-Profile-sept2017.xlsx", "engine": "openpyxl"},
    2019: {"coll": 2018, "tarball": "validated-data-sept2018.tar.gz",
           "profile": "Unit-Profile-sept2018.xlsx", "engine": "openpyxl"},
    2020: {"coll": 2019, "tarball": "validated-data-sept2019.tar.gz",
           "profile": "Unit-Profile-sept2019.xlsx", "engine": "openpyxl"},
    2021: {"coll": 2020, "tarball": "validated-data-sept2020.tar.gz",
           "profile": "unit-profile-sept2020.xlsx", "engine": "openpyxl"},
    2022: {"coll": 2021, "tarball": "validated-data-sept2021.tar.gz",
           "profile": "unit-profile-sept2021.xlsx", "engine": "openpyxl"},
    2023: {"coll": 2022, "tarball": "validated-data-sept2022.tar.gz",
           "profile": "unit-profile-sept2022.xlsx", "engine": "openpyxl"},
}

MONTH_NUM = {2011: 3, 2012: 4}
MONTH_DIR = {2011: "validated-march", 2012: "april"}

STEPS = ["02_load_and_filter.py", "03_detect_speed_tier.py",
         "04_align_time_series.py", "05_compute_rc.py", "06_compute_tis.py"]

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


def extract_tcp_web(tarpath, raw_dir):
    """Locate the tcp/web CSVs inside the validated tarball by basename prefix
    (tarballs may wrap files in a subdir and include a 6-stream variant), dedup
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
        raise FileNotFoundError(f"missing in validated tarball: {missing}")

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


def prepare_profile(s3, profile_key, profile_engine, raw_dir, logf=None):
    """Download the unit profile from S3 and stage it for the validated pipeline.

    Returns (local_filename, META_SOURCE_OVERRIDE) — Excel profiles are converted
    to CSV so 02_load_and_filter's local path reads them without schema changes.
    """
    if profile_engine is None:
        dst = os.path.join(raw_dir, "unit_metadata.csv")
        s3.download_file(BUCKET, profile_key, dst)
        return "unit_metadata.csv"
    tmp = os.path.join(tempfile.gettempdir(), os.path.basename(profile_key))
    s3.download_file(BUCKET, profile_key, tmp)
    try:
        df = pd.read_excel(tmp, engine=profile_engine)
    except Exception:
        df = None
        for alt in ("xlrd", "openpyxl", "calamine"):
            if alt == profile_engine:
                continue
            try:
                df = pd.read_excel(tmp, engine=alt)
                break
            except Exception:
                continue
        if df is None:
            raise RuntimeError(f"could not read profile {profile_key}")
    os.remove(tmp)
    out = os.path.join(raw_dir, "unit_profile.csv")
    df.to_csv(out, index=False)
    print(f"  staged profile {os.path.basename(profile_key)} -> {out} ({len(df)} rows)")
    return "unit_profile.csv"


def run_step(step, year, override, logf):
    env = {**os.environ, "YEAR": str(year), "META_SOURCE_OVERRIDE": override}
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


def load_existing_keys():
    if os.path.isfile(OUT_CSV):
        df = pd.read_csv(OUT_CSV, dtype={"data_year": int, "data_month": int})
        return set(zip(df["data_year"], df["data_month"], df["dataset"], df["technology"]))
    return set()


def append_month_rows(year, month, proc_dir):
    rc = pd.read_parquet(os.path.join(proc_dir, "rc.parquet"), columns=["unit_id", "rc"])
    tis = pd.read_parquet(os.path.join(proc_dir, "tis.parquet"), columns=["unit_id", "tis"])
    meta = pd.read_parquet(os.path.join(proc_dir, "meta_valid.parquet"),
                           columns=["unit_id", "technology"])
    merged = rc.merge(tis, on="unit_id", how="inner").merge(meta, on="unit_id", how="inner")
    merged["tech_norm"] = merged["technology"].astype(str).str.strip().str.lower().map(TECH_MAP)
    merged["tech_norm"] = merged["tech_norm"].fillna(
        merged["technology"].astype(str).str.strip().str.lower())

    existing = load_existing_keys()
    new = []
    rows = []
    groups = {"overall": merged}
    for tech in KEEP_TECH:
        groups[tech] = merged[merged["tech_norm"] == tech]
    for tech, sub in groups.items():
        row = {"data_year": year, "data_month": month, "dataset": "validated",
               "n_units": len(sub), "rc": int(sub["rc"].sum()),
               "tis": int(sub["tis"].sum()), "technology": tech}
        rows.append(row)
        if (year, month, "validated", tech) not in existing:
            new.append(row)
    if new:
        header = not os.path.isfile(OUT_CSV)
        pd.DataFrame(new, columns=CSV_COLUMNS).to_csv(OUT_CSV, mode="a",
                                                      header=header, index=False)
    return rows, new


def process_year(year, s3, logf):
    info = VALIDATED[year]
    month = MONTH_NUM.get(year, 9)
    month_dir = MONTH_DIR.get(year, "sept")
    raw_dir = os.path.join(BASE_DIR, "data", "raw", str(year), month_dir)
    proc_dir = os.path.join(BASE_DIR, "data", "processed", str(year))
    tarball_key = f"{FCC_PREFIX}/{info['coll']}/validated/{info['tarball']}"
    profile_key = f"{FCC_PREFIX}/{info['coll']}/profile/{info['profile']}"
    tarpath = os.path.join(tempfile.gettempdir(), info["tarball"])

    print(f"=== {year}-{month:02d} validated ===")
    try:
        os.makedirs(raw_dir, exist_ok=True)
        os.makedirs(proc_dir, exist_ok=True)

        print(f"  downloading {tarball_key}")
        s3.download_file(BUCKET, tarball_key, tarpath)
        extract_tcp_web(tarpath, raw_dir)
        os.remove(tarpath)
        print("  deleted tarball")

        override = prepare_profile(s3, profile_key, info["engine"], raw_dir)
        if info["engine"] is None:
            override = "unit_metadata.csv"

        run_step("02_load_and_filter.py", year, override, logf)
        # The raw CSVs are no longer needed once the parquets exist.
        for f in ("curr_httpgetmt.csv", "curr_webget.csv"):
            p = os.path.join(raw_dir, f)
            if os.path.isfile(p):
                os.remove(p)
        print("  deleted extracted CSVs")

        run_step("03_detect_speed_tier.py", year, override, logf)
        run_step("04_align_time_series.py", year, override, logf)
        # 05/06 only need aligned + meta_valid; drop tcp/web parquets to save disk.
        for f in ("tcp.parquet", "web.parquet"):
            p = os.path.join(proc_dir, f)
            if os.path.isfile(p):
                os.remove(p)
        print("  deleted tcp/web parquets")

        run_step("05_compute_rc.py", year, override, logf)
        run_step("06_compute_tis.py", year, override, logf)

        rows, new = append_month_rows(year, month, proc_dir)
        for r in rows:
            print(f"  {r['technology']:>8}: n={r['n_units']} rc={r['rc']} tis={r['tis']}")
        print(f"  appended {len(new)} new rows")
        return True
    finally:
        shutil.rmtree(raw_dir, ignore_errors=True)
        shutil.rmtree(proc_dir, ignore_errors=True)
        if os.path.isfile(tarpath):
            os.remove(tarpath)
        print("  cleaned local data")


def main():
    args = [int(a) for a in sys.argv[1:]]
    years = args or sorted(VALIDATED)
    env = load_env()
    s3 = s3_client(env)
    os.makedirs(LOG_DIR, exist_ok=True)

    ok = fail = 0
    for year in years:
        if year not in VALIDATED:
            print(f"SKIP unknown year {year}")
            continue
        logpath = os.path.join(LOG_DIR, f"validated_s3_{year}.log")
        with open(logpath, "a") as logf:
            logf.write(f"\n=== {year} start {pd.Timestamp.now()} ===\n")
            try:
                if process_year(year, s3, logf):
                    ok += 1
                logf.write(f"=== {year} done {pd.Timestamp.now()} ===\n")
            except Exception as e:
                fail += 1
                print(f"  ERROR {year}: {e}")
                logf.write(f"=== {year} FAILED: {e}\n")
    print(f"\nDone: {ok} OK, {fail} failed.")


if __name__ == "__main__":
    main()
