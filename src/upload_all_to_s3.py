"""Upload all local data to S3 so we can free disk space.

Uploads:
- processed parquets for years 2011-2022 (tcp, web, aligned, rc, tis, meta, meta_valid)
- raw tarballs for years 2012-2022
- pipeline logs
"""
import os
import sys
import boto3
from botocore.config import Config
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError

# Load .env
ENV_PATH = "/home/jovyan/work/project/.env"
with open(ENV_PATH) as fh:
    env = {}
    for line in fh:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k] = v

S3_ENDPOINT = "https://chi.tacc.chameleoncloud.org:7480"
BUCKET = "mba-data"
PREFIX = "where-congestion-occurs-2013"
BASE = "/home/jovyan/work/project"

s3 = boto3.client("s3",
    aws_access_key_id=env["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=env["AWS_SECRET_ACCESS_KEY"],
    endpoint_url=S3_ENDPOINT,
    config=Config(signature_version="s3v4"))

transfer_config = TransferConfig(
    multipart_threshold=100_000_000,
    multipart_chunksize=100_000_000,
    max_concurrency=4,
)

uploaded = []
skipped = []
failed = []


def upload_file(local_path, s3_key):
    """Upload a file to S3, skipping if already present with same size."""
    if not os.path.isfile(local_path):
        return
    local_size = os.path.getsize(local_path)
    try:
        head = s3.head_object(Bucket=BUCKET, Key=s3_key)
        if head["ContentLength"] == local_size:
            skipped.append(s3_key)
            return
    except ClientError:
        pass
    s3.upload_file(local_path, BUCKET, s3_key, Config=transfer_config)
    uploaded.append(s3_key)
    print(f"  uploaded: {os.path.basename(local_path)} ({local_size/1e6:.1f} MB)")


def main():
    # 1. Upload processed parquets for 2011-2022
    PARQUETS = ["tcp.parquet", "web.parquet", "aligned.parquet", "rc.parquet",
                "tis.parquet", "meta.parquet", "meta_valid.parquet", "isp_agg.parquet"]
    YEARS = list(range(2011, 2023))

    print("=== Uploading processed parquets (2011-2022) ===")
    for year in YEARS:
        proc_dir = os.path.join(BASE, "data", "processed", str(year))
        for fname in PARQUETS:
            local = os.path.join(proc_dir, fname)
            s3_key = f"{PREFIX}/data/processed/{year}/{fname}"
            upload_file(local, s3_key)

    # 2. Upload raw tarballs for 2012-2022
    print("\n=== Uploading raw tarballs (2012-2022) ===")
    for year in range(2012, 2023):
        bk_dir = os.path.join(BASE, "data", "raw_bk", str(year))
        if not os.path.isdir(bk_dir):
            continue
        for fname in os.listdir(bk_dir):
            local = os.path.join(bk_dir, fname)
            if os.path.isfile(local) and fname.endswith(".tar.gz"):
                s3_key = f"{PREFIX}/data/raw_bk/{year}/{fname}"
                upload_file(local, s3_key)

    # 3. Upload pipeline logs
    print("\n=== Uploading pipeline logs ===")
    logs_dir = os.path.join(BASE, "data", "logs")
    if os.path.isdir(logs_dir):
        for fname in os.listdir(logs_dir):
            local = os.path.join(logs_dir, fname)
            if os.path.isfile(local):
                s3_key = f"{PREFIX}/data/logs/{fname}"
                upload_file(local, s3_key)

    # 4. Upload stale loose parquets at processed root
    print("\n=== Uploading stale loose parquets ===")
    for fname in os.listdir(os.path.join(BASE, "data", "processed")):
        local = os.path.join(BASE, "data", "processed", fname)
        if os.path.isfile(local) and fname.endswith(".parquet"):
            s3_key = f"{PREFIX}/data/processed/{fname}"
            upload_file(local, s3_key)

    # Summary
    total_uploaded_size = 0
    for key in uploaded:
        try:
            head = s3.head_object(Bucket=BUCKET, Key=key)
            total_uploaded_size += head["ContentLength"]
        except Exception:
            pass

    print(f"\n=== SUMMARY ===")
    print(f"Uploaded: {len(uploaded)} files ({total_uploaded_size/1e9:.2f} GB)")
    print(f"Skipped (already in S3): {len(skipped)} files")
    print(f"Failed: {len(failed)} files")
    if failed:
        print("Failed files:")
        for f in failed:
            print(f"  {f}")


if __name__ == "__main__":
    main()
