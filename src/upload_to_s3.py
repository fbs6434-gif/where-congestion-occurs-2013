import os
import boto3
from botocore.config import Config

S3_ENDPOINT = "https://chi.tacc.chameleoncloud.org:7480"
BUCKET = "mba-data"
PREFIX = "where-congestion-occurs-2013"

ALL_YEARS = [2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]

YEAR_DIRS = {y: f"/home/jovyan/work/project/output/{y}" for y in ALL_YEARS}
PROCESSED_DIRS = {y: f"/home/jovyan/work/project/data/processed/{y}" for y in ALL_YEARS}

def upload_file(s3, local_path, s3_key):
    if not os.path.isfile(local_path):
        print(f"  SKIP (not found): {local_path}")
        return
    s3.upload_file(local_path, BUCKET, s3_key, ExtraArgs={"ACL": "public-read"})
    print(f"  OK: {s3_key}")

def upload_dir(s3, local_dir, s3_prefix):
    for root, dirs, files in os.walk(local_dir):
        for f in files:
            local_path = os.path.join(root, f)
            rel = os.path.relpath(local_path, local_dir)
            s3_key = f"{s3_prefix}/{rel}"
            upload_file(s3, local_path, s3_key)

def main():
    with open("/home/jovyan/work/project/.env") as fh:
        env = fh.read()
    aws_key = [l for l in env.split("\n") if "AWS_ACCESS_KEY_ID" in l][0].split("=", 1)[1].strip()
    aws_secret = [l for l in env.split("\n") if "AWS_SECRET_ACCESS_KEY" in l][0].split("=", 1)[1].strip()
    session = boto3.Session(
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret,
    )
    s3 = session.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        config=Config(signature_version="s3v4"),
    )

    for year, out_dir in YEAR_DIRS.items():
        print(f"\n=== Uploading {year} tables ===")
        upload_dir(s3, os.path.join(out_dir, "tables"), f"{PREFIX}/output/{year}/tables")
        print(f"\n=== Uploading {year} figures ===")
        upload_dir(s3, os.path.join(out_dir, "figures"), f"{PREFIX}/output/{year}/figures")

    for year, proc_dir in PROCESSED_DIRS.items():
        isp_agg = os.path.join(proc_dir, "isp_agg.parquet")
        if os.path.isfile(isp_agg):
            s3_key = f"{PREFIX}/data/processed/{year}/isp_agg.parquet"
            upload_file(s3, isp_agg, s3_key)

    print("\n=== Uploading raw-vs-validated comparison ===")
    compare_dir = "/home/jovyan/work/project/output/compare_raw_validated"
    upload_dir(s3, os.path.join(compare_dir, "figures"),
               f"{PREFIX}/output/compare_raw_validated/figures")
    upload_dir(s3, os.path.join(compare_dir, "tables"),
               f"{PREFIX}/output/compare_raw_validated/tables")

    print("\nDone uploading.")

if __name__ == "__main__":
    main()
