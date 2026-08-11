"""Per-(year, month) configuration for the monthly panel pipeline.

Builds validated and raw month entries programmatically from the staged FCC
manifest (output/staging/fcc_manifest.csv), so the pipeline can process any
(data_year, data_month) listed there instead of only the single month per
analysis year hard-coded in config.py / raw_config.py.
"""
import os
import csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(BASE_DIR, "output", "staging", "fcc_manifest.csv")

# Profile metadata keyed by collection year -> list of
# (month_or_None, filename, s3_key, engine, meta_cols). The None entry is the
# default profile for that year (used for every month without a month-specific
# profile). meta_cols maps {dst_col: src_col}.
PROFILES = {
    2011: [(None, "unit_metadata.csv", "fcc-mba/2011/profile/unit_metadata.csv",
            None, {
                "unit_id": "UnitID", "isp": "ISP", "technology": "TECHNOLOGY",
                "speed_tier_down": "ISP DOWN"})],
    2012: [(None, "unit-profile-april-2012.xlsx",
            "fcc-mba/2012/profile/unit-profile-april-2012.xlsx",
            "openpyxl", {
                "unit_id": "UNIT_ID", "isp": "ISP", "technology": "TECHNOLOGY",
                "speed_tier_down": "DOWNLOAD_TIER"}),
           (9, "FCC_UnitProfile_Sept12.xls",
            "fcc-mba/2012/profile/FCC_UnitProfile_Sept12.xls",
            "xlrd", {
                "unit_id": "unit_id", "isp": "isp", "technology": "Technology",
                "speed_tier_down": "Download"})],
    2013: [(None, "FCC_Unit_Profile_20140207.xlsx",
            "fcc-mba/2013/profile/FCC_Unit_Profile_20140207.xlsx",
            "openpyxl", {
                "unit_id": "unit_id", "isp": "isp", "technology": "TECHNOLOGY",
                "speed_tier_down": "DOWN"})],
    2014: [(None, "FCC_UnitProfile_Sept14.xls",
            "fcc-mba/2014/profile/FCC_UnitProfile_Sept14.xls",
            "openpyxl", {
                "unit_id": "unit_id", "isp": "isp", "technology": "TECHNOLOGY",
                "speed_tier_down": "SK down"})],
    2015: [(None, "Unit-Profile-sept2015.xlsx",
            "fcc-mba/2015/profile/Unit-Profile-sept2015.xlsx",
            "openpyxl", {
                "unit_id": "unit_id", "isp": "isp", "technology": "TECHNOLOGY",
                "speed_tier_down": "Download"})],
    2016: [(None, "Unit-Profile-sept2016.xlsx",
            "fcc-mba/2016/profile/Unit-Profile-sept2016.xlsx",
            "openpyxl", {
                "unit_id": "unit_id", "isp": "isp", "technology": "Technology",
                "speed_tier_down": "Download"})],
    2017: [(None, "Unit-Profile-sept2017.xlsx",
            "fcc-mba/2017/profile/Unit-Profile-sept2017.xlsx",
            "openpyxl", {
                "unit_id": "unit_id", "isp": "ISP", "technology": "Technology",
                "speed_tier_down": "Download"})],
    2018: [(None, "Unit-Profile-sept2018.xlsx",
            "fcc-mba/2018/profile/Unit-Profile-sept2018.xlsx",
            "openpyxl", {
                "unit_id": "Unit ID", "isp": "ISP", "technology": "Technology",
                "speed_tier_down": "Download"})],
    2019: [(None, "Unit-Profile-sept2019.xlsx",
            "fcc-mba/2019/profile/Unit-Profile-sept2019.xlsx",
            "openpyxl", {
                "unit_id": "Unit ID", "isp": "ISP", "technology": "Technology",
                "speed_tier_down": "Download"})],
    2020: [(None, "unit-profile-sept2020.xlsx",
            "fcc-mba/2020/profile/unit-profile-sept2020.xlsx",
            "openpyxl", {
                "unit_id": "Unit ID", "isp": "ISP", "technology": "Technology",
                "speed_tier_down": "Download"})],
    2021: [(None, "unit-profile-sept2021.xlsx",
            "fcc-mba/2021/profile/unit-profile-sept2021.xlsx",
            "openpyxl", {
                "unit_id": "Unit ID", "isp": "ISP", "technology": "Technology",
                "speed_tier_down": "Download"})],
    2022: [(None, "unit-profile-sept2022.xlsx",
            "fcc-mba/2022/profile/unit-profile-sept2022.xlsx",
            "openpyxl", {
                "unit_id": "Unit ID", "isp": "ISP", "technology": "Technology",
                "speed_tier_down": "Download"})],
    2023: [(None, "unit-profile-sept2022.xlsx",
            "fcc-mba/2022/profile/unit-profile-sept2022.xlsx",
            "openpyxl", {
                "unit_id": "Unit ID", "isp": "ISP", "technology": "Technology",
                "speed_tier_down": "Download"})],
}

# Validated months whose curr_httpgetmt.csv / curr_webget.csv have no header
# row. Config.py analysis-year keys 2013/2014/2016 correspond to the
# collection months (2012-09), (2013-09), (2015-09).
VALIDATED_NO_HEADER = {(2012, 9), (2013, 9), (2015, 9)}

MONTH_NAMES = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May",
               6: "June", 7: "July", 8: "August", 9: "September", 10: "October",
               11: "November", 12: "December"}

_manifest_rows = None


def _rows():
    global _manifest_rows
    if _manifest_rows is None:
        with open(MANIFEST) as fh:
            _manifest_rows = list(csv.DictReader(fh))
    return _manifest_rows


def month_exists(dataset, year, month):
    for r in _rows():
        if (r["kind"] == dataset and int(r["data_year"]) == year
                and int(r["data_month"]) == month):
            return True
    return False


def tarball(dataset, year, month):
    """Return the manifest row (dict) for the given dataset month."""
    for r in _rows():
        if (r["kind"] == dataset and int(r["data_year"]) == year
                and int(r["data_month"]) == month):
            return r
    raise KeyError(f"no {dataset} month {year}-{month} in manifest")


def profile(year, month):
    """Return (filename, s3_key, engine, meta_cols) for the given (year, month)."""
    for m, fn, key, eng, cols in PROFILES.get(year, []):
        if m == month:
            return fn, key, eng, cols
    for m, fn, key, eng, cols in PROFILES.get(year, []):
        if m is None:
            return fn, key, eng, cols
    raise KeyError(f"no profile for {year}-{month}")


def profile_row(year, month):
    """Return the manifest row (dict) for the profile file used by (year, month)."""
    fname, key, _, _ = profile(year, month)
    for r in _rows():
        if r["kind"] == "profile" and int(r["data_year"]) == year and r["filename"] == fname:
            return r
    raise KeyError(f"no manifest profile row for {year}-{month} {fname}")


def dirs(dataset, year, month):
    """Return (raw_dir, processed_dir, output_dir) unique to (dataset, year, month)."""
    tag = f"{dataset}-{year}-{month:02d}"
    raw_dir = os.path.join(BASE_DIR, "data", "raw", tag)
    processed_dir = os.path.join(BASE_DIR, "data", "processed", tag)
    output_dir = os.path.join(BASE_DIR, "output", tag)
    return raw_dir, processed_dir, output_dir


def all_months(dataset):
    """Return sorted [(year, month), ...] for the given dataset from the manifest."""
    return sorted((int(r["data_year"]), int(r["data_month"]))
                  for r in _rows()
                  if r["kind"] == dataset and r["data_month"])
