"""Ingest RAW bulk FCC MBA data for one year into the standard processed layout.

Downloads the raw tarball (or reuses data/raw_bk/<year>/), extracts just the
tcp and web CSVs by basename (tarballs may wrap files in a YYYYMM/ directory),
and emits tcp.parquet / web.parquet in the same processed layout as the
validated pipeline so steps 03-09 run unchanged.

Raw units have NO embedded isp/technology metadata (except 2011 which embeds
them in the row). Metadata is attached later from the validated unit profile
(see attach_profile.py / 02_load_and_filter.py raw path).
"""
import os
import subprocess
import sys
import pandas as pd
from urllib.parse import urlparse
from raw_config import (RAW_DIR, PROCESSED_DIR, TAR_PATH, RAW_TAR_NAME,
                        RAW_TCP_CSV, RAW_WEB_CSV, RAW_URL)

BYTES_PER_MEGABIT = 125_000
MICROSECONDS_PER_MILLISECOND = 1000

DOMAIN_MAP = {"edition.cnn.com": "cnn.com"}

def extract_domain(url):
    try:
        domain = urlparse(url).netloc.replace("www.", "")
    except Exception:
        return "unknown"
    return DOMAIN_MAP.get(domain, domain)


def ensure_tarball():
    os.makedirs(os.path.dirname(TAR_PATH), exist_ok=True)
    if os.path.exists(TAR_PATH):
        print(f"Tarball present: {TAR_PATH}")
        return
    print(f"Downloading {RAW_TAR_NAME} ...")
    subprocess.run(["curl", "-sL", "--retry", "3", "-o", TAR_PATH, RAW_URL], check=True)


def members_to_extract(tar):
    """Locate the tcp/web CSVs by basename prefix (years differ in naming).

    Some years include a "curr_httpgetmt6_*.csv" 6-stream test alongside the
    standard "curr_httpgetmt_*.csv"; prefer the standard (non-"6") one.
    """
    found = {}
    for m in tar:
        base = os.path.basename(m.name)
        if base.startswith("curr_httpgetmt") and base.endswith(".csv"):
            if "httpgetmt6" in base:
                continue
            found.setdefault("tcp", m.name)
        elif base.startswith("curr_webget") and base.endswith(".csv"):
            found.setdefault("web", m.name)
    missing = [k for k in ("tcp", "web") if k not in found]
    if missing:
        raise FileNotFoundError(f"missing in tarball: {missing}")
    return found


def peek_header(path):
    """Read first non-empty line of an on-disk CSV. Returns (comment, header)."""
    with open(path, "rb") as f:
        line = b""
        while not line.strip():
            line = f.readline()
        text = line.decode("utf-8", "replace").strip()
    if text.startswith("#"):
        return "#", text.lstrip("#").strip()
    if text.lower().startswith("unit_id"):
        return None, text
    return None, None  # no header


def read_csv_to_parquet(csv_path, comment, header_line, kind):
    """Read a raw CSV chunked and emit the processed parquet.

    kind: "tcp" -> needs unit_id, dtime, bytes_sec
          "web" -> needs unit_id, dtime, target, fetch_time
    Handles both header and no-header layouts, and the varying column counts.
    """
    if header_line is None:
        # No header row: sniff column count from the first data line.
        with open(csv_path, "rb") as f:
            first = f.readline()
        ncols = len(first.decode("utf-8", "replace").strip().split(","))
        if kind == "tcp":
            cols = ["unit_id", "dtime", "target", "address", "fetch_time",
                    "bytes_total", "bytes_sec", "bytes_sec_interval", "warmup_time",
                    "warmup_bytes", "sequence", "threads", "successes", "failures",
                    "location_id"][:ncols]
            usecols = [0, 1, 6, 12]
        else:
            cols = ["unit_id", "dtime", "target", "address", "fetch_time",
                    "bytes_total", "bytes_sec", "objects", "threads", "requests",
                    "connections", "reused_connections", "lookups", "request_total_time",
                    "request_min_time", "request_avg_time", "request_max_time",
                    "ttfb_total", "ttfb_min", "ttfb_avg", "ttfb_max",
                    "lookup_total_time", "lookup_min_time", "lookup_avg_time", "lookup_max_time",
                    "successes", "failures", "location_id"][:ncols]
            usecols = [0, 1, 2, 4]  # unit_id, dtime, target, fetch_time
        reader = pd.read_csv(csv_path, names=cols, usecols=usecols,
                             comment=comment if comment else None,
                             chunksize=500_000, engine="c",
                             low_memory=False,
                             dtype={"unit_id": "int64"})
    else:
        if comment:
            # '#'-prefixed header: let pandas skip it as a comment, then the
            # columns come from our names list (header=None).
            if kind == "tcp":
                names = ["unit_id", "dtime", "target", "fetch_time", "bytes_total",
                         "bytes_sec", "warmup_time", "warmup_bytes", "sequence",
                         "threads", "successes", "failures"]
                usecols = [0, 1, 5, 10]
            else:
                names = ["unit_id", "dtime", "target", "fetch_time", "bytes_total",
                         "bytes_sec", "objects", "successes", "failures"]
                usecols = [0, 1, 2, 3]
            reader = pd.read_csv(csv_path, names=names, usecols=usecols, header=None,
                                 comment="#", chunksize=500_000, engine="c",
                                 low_memory=False,
                                 dtype={"unit_id": "int64"})
        else:
            # Has header; use names directly.
            if kind == "tcp":
                usecols = ["unit_id", "dtime", "bytes_sec", "successes"]
            else:
                usecols = ["unit_id", "dtime", "target", "fetch_time"]
            reader = pd.read_csv(csv_path, usecols=usecols,
                                 chunksize=500_000, engine="c",
                                 low_memory=False,
                                 dtype={"unit_id": "int64"})

    pieces = []
    for i, chunk in enumerate(reader):
        chunk["dtime"] = pd.to_datetime(chunk["dtime"], errors="coerce")
        chunk = chunk[chunk["dtime"].notna()]
        if kind == "tcp":
            # Raw bulk carries ~6 concurrent sequences per timestamp and failed
            # tests (bytes_sec=0). Drop failures and median-aggregate per
            # (unit, dtime), matching the validated pipeline's step 02. Without
            # this the daily-max speed-tier is inflated by PowerBoost bursts and
            # RC% is ~4x too high (see ANALYSIS.md).
            chunk = chunk[chunk["successes"] > 0]
            chunk["throughput_mbps"] = chunk["bytes_sec"] / BYTES_PER_MEGABIT
            piece = (chunk.groupby(["unit_id", "dtime"], as_index=False)["throughput_mbps"].median())
        else:
            if "successes" in chunk.columns:
                chunk = chunk[chunk["successes"] > 0]
            chunk["url"] = chunk["target"].apply(extract_domain).astype("category")
            chunk["load_time_ms"] = chunk["fetch_time"] / MICROSECONDS_PER_MILLISECOND
            piece = chunk[["unit_id", "dtime", "url", "load_time_ms"]].copy()
        pieces.append(piece)
        if (i + 1) % 10 == 0:
            print(f"  chunk {i+1}: {len(chunk)} rows")
    return pd.concat(pieces, ignore_index=True)


def main():
    ensure_tarball()
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    import tarfile, shutil
    with tarfile.open(TAR_PATH, "r:gz") as tar:
        found = members_to_extract(tar)
    member_pairs = [("tcp", found["tcp"], RAW_TCP_CSV),
                    ("web", found["web"], RAW_WEB_CSV)]

    # Extract the two CSVs to disk (single streaming pass), deduplicating any
    # repeated header rows (e.g. 2022 web) inline so we never double disk usage.
    with tarfile.open(TAR_PATH, "r:gz") as tar:
        for kind, member, basename in member_pairs:
            out_csv = os.path.join(RAW_DIR, basename)
            if not os.path.exists(out_csv) or os.path.getsize(out_csv) == 0:
                src = tar.extractfile(member)
                kept = False
                with open(out_csv, "wb") as dst:
                    for line in src:
                        if line.startswith(b"unit_id,"):
                            if kept:
                                continue
                            kept = True
                        dst.write(line)
                print(f"Extracted {member} -> {out_csv}")

    for kind, basename, outname in [("tcp", RAW_TCP_CSV, "tcp.parquet"),
                                    ("web", RAW_WEB_CSV, "web.parquet")]:
        csv_path = os.path.join(RAW_DIR, basename)
        comment, header_line = peek_header(csv_path)
        print(f"Reading {basename}: comment={comment!r} header={header_line!r}")
        df = read_csv_to_parquet(csv_path, comment, header_line, kind)
        print(f"  {kind}: {len(df)} rows, {df['unit_id'].nunique()} units")
        out = os.path.join(PROCESSED_DIR, outname)
        df.to_parquet(out)
        print(f"  Saved {out}")

    # The CSVs are intermediate: delete them once the parquets are saved.
    for base in (RAW_TCP_CSV, RAW_WEB_CSV):
        csv_path = os.path.join(RAW_DIR, base)
        if os.path.exists(csv_path):
            os.remove(csv_path)
            print(f"Deleted {csv_path}")

    print("Done.")

if __name__ == "__main__":
    main()