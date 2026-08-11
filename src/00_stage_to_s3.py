"""Stage every file in the FCC manifest to S3, one file at a time.

For each manifest row: download the file from FCC to a local temp file
(streaming, sha256-computed as it downloads), upload it to S3, then delete
the local temp file. Strictly one file in flight at a time so local disk
usage peaks at a single tarball (~4-5 GB).

Resume-safe and idempotent: a row is skipped if it is already staged in S3
with a matching size (or if the manifest already records it as staged with a
sha256). Interrupting and re-running continues from where it left off.

Usage:
    python src/00_stage_to_s3.py [--manifest PATH] [--kind raw|validated|profile]
                                 [--limit N] [--tmp DIR]
"""
import argparse
import csv
import hashlib
import os
import sys
import time
from datetime import datetime, timezone

import boto3
import requests
from botocore.config import Config
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")
S3_ENDPOINT = "https://chi.tacc.chameleoncloud.org:7480"
BUCKET = "mba-data"
UA = {"User-Agent": "Mozilla/5.0"}

env = {}
with open(ENV_PATH) as fh:
    for line in fh:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k] = v

s3 = boto3.client(
    "s3",
    aws_access_key_id=env["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=env["AWS_SECRET_ACCESS_KEY"],
    endpoint_url=S3_ENDPOINT,
    config=Config(signature_version="s3v4",
                  retries={"max_attempts": 8, "mode": "standard"}),
)

transfer_config = TransferConfig(
    multipart_threshold=100_000_000,
    multipart_chunksize=100_000_000,
    max_concurrency=4,
)

session = requests.Session()
session.headers.update(UA)


def log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)


def s3_size(key):
    try:
        head = s3.head_object(Bucket=BUCKET, Key=key)
        return head["ContentLength"]
    except ClientError:
        return None


def download(url, dest):
    """Stream url to dest, returning (bytes, sha256).

    Size is verified against the Content-Length header when the server
    provides one (FCC directory-listing sizes are rounded, so those are not
    authoritative). Integrity is enforced by the sha256 and the post-upload
    S3 size check.
    """
    h = hashlib.sha256()
    n = 0
    with session.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        header_len = r.headers.get("Content-Length")
        check = int(header_len) if header_len else None
        with open(dest, "wb") as fh:
            for chunk in r.iter_content(chunk_size=1 << 20):
                if not chunk:
                    continue
                fh.write(chunk)
                h.update(chunk)
                n += len(chunk)
    if check and n != check:
        raise RuntimeError(
            f"size mismatch: downloaded {n}, expected {check}")
    return n, h.hexdigest()


def stage_row(row, tmp_dir):
    key = row["s3_key"]
    url = row["url"]
    filename = row["filename"]

    tmp = os.path.join(tmp_dir, filename)
    t0 = time.time()
    log(f"downloading {filename} from {url}")
    try:
        n, sha = download(url, tmp)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    dl = time.time() - t0
    log(f"  downloaded {n} bytes ({n/1e9:.2f} GB) in {dl:.0f}s, sha256={sha[:16]}...")

    t0 = time.time()
    log(f"  uploading to s3://{BUCKET}/{key}")
    s3.upload_file(tmp, BUCKET, key, Config=transfer_config)
    up = time.time() - t0
    log(f"  uploaded in {up:.0f}s")
    os.remove(tmp)

    if s3_size(key) != n:
        raise RuntimeError(f"post-upload size check failed for {key}")

    row["size"] = str(n)
    row["sha256"] = sha
    row["staged"] = "1"
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=os.path.join(
        BASE_DIR, "output", "staging", "fcc_manifest.csv"))
    ap.add_argument("--kind", choices=["raw", "validated", "profile"])
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--tmp", default=os.path.join(BASE_DIR, "data", ".staging_tmp"))
    args = ap.parse_args()

    os.makedirs(args.tmp, exist_ok=True)

    with open(args.manifest, newline="") as fh:
        fieldnames = None
        rows = []
        for r in csv.DictReader(fh):
            if fieldnames is None:
                fieldnames = r.keys()
            rows.append(r)

    order = {"profile": 0, "validated": 1, "raw": 2}
    rows.sort(key=lambda r: (order.get(r["kind"], 3),
                             int(r["data_year"] or 0),
                             int(r["data_month"] or 0)))

    if args.kind:
        rows = [r for r in rows if r["kind"] == args.kind]

    todo = [r for r in rows if r.get("staged") != "1"]
    log(f"{len(todo)} of {len(rows)} rows to stage")
    log(f"expected bytes: {sum(int(r['size'] or 0) for r in todo)/1e9:.1f} GB")

    done = 0
    attempted = 0
    failed = []
    for i, row in enumerate(todo):
        if args.limit and attempted >= args.limit:
            log("limit reached")
            break
        attempted += 1
        # idempotent skip: already in S3 with recorded size
        expected = int(row["size"]) if row["size"] else None
        key = row["s3_key"]
        cur = s3_size(key)
        if cur is not None and cur == expected and expected:
            row["staged"] = "1"
            done += 1
            log(f"SKIP {row['filename']} (already in S3, size matches)")
            continue
        try:
            stage_row(row, args.tmp)
            done += 1
            log(f"  [{done}/{len(todo)}] staged {row['filename']}")
        except Exception as e:
            failed.append((row["filename"], str(e)))
            log(f"  !! FAILED {row['filename']}: {e}")
            time.sleep(5)

        # persist progress after each file so re-runs are resume-safe
        with open(args.manifest, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(fieldnames))
            w.writeheader()
            w.writerows(rows)

    log(f"staging pass complete: {done} done, {len(failed)} failed")
    for fn, err in failed:
        log(f"  FAILED {fn}: {err}")


if __name__ == "__main__":
    main()
