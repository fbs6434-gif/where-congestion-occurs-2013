"""Scrape the FCC measuring-broadband-america download directory and build a
manifest (CSV) of every raw/validated/profile file needed for staging to S3.

Usage:
    python src/00_scrape_fcc_manifest.py [out.csv]

Columns: data_year, data_month (int), kind (raw|validated|profile|metadata),
fcc_dir, filename, url, size (bytes), sha256 (filled by stager), s3_key, staged.
"""
import argparse
import csv
import os
import re
import sys

import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

BASE_URL = "https://data.fcc.gov/download/measuring-broadband-america/"
UA = {"User-Agent": "Mozilla/5.0"}

MONTH_NAMES = {
    "jan": 1, "feb": 2, "mar": 3, "march": 3, "apr": 4, "april": 4,
    "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7, "aug": 8,
    "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}

# regexes -> (kind, year_capture, month_capture_or_name, numeric_month?)
# capture numbers are 1-based regex group indices
PATTERNS = [
    (re.compile(r"data-raw-(\d{4})-([a-z]+)\.tar\.gz$"), "raw", 1, 2, False),
    (re.compile(r"raw-bulk-data-([a-z]+)-(\d{4})\.tar\.gz$"), "raw", 2, 1, False),
    (re.compile(r"raw-bulk-([a-z]+)-(\d{4})\.tar\.gz$"), "raw", 2, 1, False),
    (re.compile(r"fcc_(\d{4})(\d{2})\.tar\.gz$"), "raw", 1, 2, True),
    (re.compile(r"data-validated-+(\d{4})-([a-z]+)\.tar\.gz$"), "validated", 1, 2, False),
    (re.compile(r"validated-data-sept(\d{4})\.tar\.gz$"), "validated", 1, None, None),
    (re.compile(r"validated-([a-z]+)-data-(\d{4})\.tar\.gz$"), "validated", 2, 1, False),
]

PROFILE_RE = re.compile(r"unit[-_]?profile", re.I)


def fetch(url):
    r = requests.get(url, timeout=60, headers=UA)
    r.raise_for_status()
    return r.text


def parse_listing(html):
    rows = re.findall(
        r'<a href="([^"]+)">[^<]*</a>.*?</td>\s*'
        r'<td align="right">([^<]*)</td>\s*<td align="right">([^<]*)</td>',
        html, re.S)
    out = []
    for href, mod, size in rows:
        href = href.strip()
        if href.startswith("?C="):
            continue
        out.append((href, mod.strip(), size.strip()))
    return out


def parse_size(s):
    s = s.strip()
    if s in ("", "-"):
        return None
    mult = {"K": 1024, "M": 1024 ** 2, "G": 1024 ** 3, "T": 1024 ** 4}
    m = re.match(r"^([\d.]+)([KMGTP]?)$", s)
    if not m:
        return None
    num = float(m.group(1))
    return int(num * mult.get(m.group(2), 1))


def classify(filename, dirname):
    """Return (kind, data_year, data_month) or None."""
    if filename.endswith(".txt") or filename.startswith("fcc_"):
        # fcc_YYYYMM.tar.gz are renamed duplicates of data-raw-YYYY-mon.tar.gz
        return None
    for pat in PATTERNS:
        pat_re, kind, ycap, mcap, numeric = pat
        m = pat_re.search(filename)
        if not m:
            continue
        year = int(m.group(ycap))
        if mcap is None:
            mon = MONTH_NAMES.get("sept")
        elif numeric:
            mon = int(m.group(mcap))
        else:
            monname = m.group(mcap).lower()
            mon = MONTH_NAMES.get(monname)
        if mon is None:
            continue
        return kind, year, mon
    if PROFILE_RE.search(filename):
        m = re.search(r"sept(\d{4})", filename, re.I)
        if m:
            return "profile", int(m.group(1)), 9
        m = re.search(r"(\d{4})", filename)
        if m:
            y = int(m.group(1))
            if re.match(r"FCC_Unit_Profile_\d{8}", filename):
                y -= 1  # FCC_Unit_Profile_YYYYMMDD is dated after the collection year
            return "profile", y, None
        m = re.search(r"[Ss]ept(\d{2})", filename)
        if m:
            return "profile", 2000 + int(m.group(1)), 9
        if dirname.isdigit():
            return "profile", int(dirname), None
        return "profile", None, None
    return None


def crawl():
    found = {}  # filename -> dict(url=..., size=..., dir=..., kind=..., year=..., month=...)

    def add(filename, url, size, dirname):
        cls = classify(filename, dirname)
        if cls is None:
            return
        kind, year, month = cls
        if filename in found:
            cur = found[filename]
            # prefer occurrence whose dir matches the tarball's own year
            cur_dir = cur["dir"]
            if dirname == str(year) and cur_dir != str(year):
                cur.update(url=url, size=size, dir=dirname)
            return
        found[filename] = {
            "url": url, "size": size, "dir": dirname,
            "kind": kind, "year": year, "month": month,
        }

    # crawl root + year dirs + a few odd dirs
    dirs = ["", "2011", "2012", "2013", "2014", "2015", "2016", "2017",
            "2018", "2019", "2020", "2021", "2022", "2023",
            "12122017", "hide_2012-1", "hide_2013-1", "fupdate",
            "special-studies", "vc5jrmjptm"]
    for d in dirs:
        base = BASE_URL if d == "" else BASE_URL + d + "/"
        try:
            html = fetch(base)
        except Exception as e:
            print(f"  !! {d}: {e}", file=sys.stderr)
            continue
        for href, mod, size in parse_listing(html):
            if href.endswith("/"):
                continue
            add(href, base + href, parse_size(size), d)
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default=os.path.join(
        BASE_DIR, "output", "staging", "fcc_manifest.csv"))
    args = ap.parse_args()

    found = crawl()

    # cross-check validated tarball URLs in src/config.py
    cfg = None
    try:
        import config
        cfg = {y: c["tarball_url"] for y, c in config.YEARS_CONFIG.items()
               if c.get("tarball_url")}
    except Exception as e:
        print(f"  !! could not import config: {e}", file=sys.stderr)

    print(f"\nDiscovered {len(found)} data files:")
    from collections import Counter
    kinds = Counter(f["kind"] for f in found.values())
    for k, c in sorted(kinds.items()):
        print(f"  {k}: {c}")
    byyear = Counter((f["year"], f["kind"]) for f in found.values()
                     if f["year"] is not None)
    for yk in sorted(byyear):
        print(f"  {yk[0]} {yk[1]}: {byyear[yk]}")

    if cfg:
        cfg_basenames = {os.path.basename(u): u for u in cfg.values()}
        missing_cfg = [u for u in cfg.values()
                       if os.path.basename(u) not in found]
        if missing_cfg:
            print("\n  !! config validated URLs NOT found in scrape:")
            for u in missing_cfg:
                print(f"     {u}")
        else:
            print("\n  all config validated URLs found in scrape")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["data_year", "data_month", "kind", "fcc_dir", "filename",
                    "url", "size", "sha256", "s3_key", "staged"])
        for fn in sorted(found):
            f = found[fn]
            w.writerow([f["year"], f["month"], f["kind"], f["dir"], fn,
                        f["url"], f["size"], "",
                        f"fcc-mba/{f['year']}/{f['kind']}/{fn}" if f["year"] else "",
                        ""])
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
