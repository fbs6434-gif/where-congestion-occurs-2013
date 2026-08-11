#!/usr/bin/env python3
"""Continuously merge worker panel parts from S3 into the monthly panel CSV.

Polling lists s3://mba-data/where-congestion-occurs-2013/panel_parts/*.csv,
downloads any changed part, merges into output/tables/monthly_panel_raw_validated.csv
(dedup on (data_year, data_month, dataset, technology)), and reports progress
against the authoritative manifest.

Usage:
  python3 merge_panel_parts.py            # single merge pass, then exit
  python3 merge_panel_parts.py --watch    # poll every 60s until all months done
"""
import os
import sys
import time

import boto3
import pandas as pd
from botocore.config import Config

import monthly_config as mc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")
BUCKET = "mba-data"
PARTS_PREFIX = "where-congestion-occurs-2013/panel_parts"
PANEL_CSV = os.path.join(BASE_DIR, "output", "tables", "monthly_panel_raw_validated.csv")

CSV_COLUMNS = ["data_year", "data_month", "dataset", "technology", "n_units", "rc", "tis"]
EXPECTED = {"raw": len(mc.all_months("raw")), "validated": len(mc.all_months("validated"))}


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


def list_parts(s3):
    keys = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET, Prefix=PARTS_PREFIX):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])
    return keys


def merge_pass(s3, report=True):
    keys = list_parts(s3)
    frames = []
    for key in keys:
        name = os.path.basename(key)
        tmp = os.path.join(os.path.dirname(PANEL_CSV), f".part_{name}")
        s3.download_file(BUCKET, key, tmp)
        df = pd.read_csv(tmp, dtype={"data_year": int, "data_month": int})
        os.remove(tmp)
        frames.append(df)
    if not frames:
        if report:
            print("no parts found")
        return None
    panel = pd.concat(frames, ignore_index=True)
    panel = panel.drop_duplicates(subset=CSV_COLUMNS[:4]).sort_values(CSV_COLUMNS[:4])
    panel[CSV_COLUMNS].to_csv(PANEL_CSV, index=False)
    n_months = panel[["data_year", "data_month", "dataset"]].drop_duplicates()
    counts = n_months["dataset"].value_counts().to_dict()
    done = counts.get("raw", 0), counts.get("validated", 0)
    if report:
        print(f"panel: {len(panel)} rows across {done[0]}/{EXPECTED['raw']} raw "
              f"and {done[1]}/{EXPECTED['validated']} validated months")
    return done


def months_left(s3):
    panel = set()
    keys = list_parts(s3)
    for key in keys:
        name = os.path.basename(key)
        tmp = os.path.join(os.path.dirname(PANEL_CSV), f".part_{name}")
        s3.download_file(BUCKET, key, tmp)
        df = pd.read_csv(tmp, dtype={"data_year": int, "data_month": int})
        os.remove(tmp)
        panel.update(zip(df["data_year"], df["data_month"], df["dataset"]))
    remaining = []
    for dataset in ("raw", "validated"):
        for (y, m) in mc.all_months(dataset):
            if (y, m, dataset) not in panel:
                remaining.append((dataset, y, m))
    return remaining


def main():
    watch = len(sys.argv) > 1 and sys.argv[1] == "--watch"
    env = load_env()
    s3 = s3_client(env)
    while True:
        done = merge_pass(s3)
        if not watch:
            return
        if done and done[0] >= EXPECTED["raw"] and done[1] >= EXPECTED["validated"]:
            print("all months done")
            return
        time.sleep(60)


if __name__ == "__main__":
    main()