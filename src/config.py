import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Year-specific settings (override with YEAR env var) ---
YEAR = int(os.environ.get("YEAR", "2011"))

# Map: year -> (label, month_dir, tcp_csv, web_csv, has_header, meta_source, meta_engine_or_none)
# has_header: whether TCP/WEB CSVs have a header row (False for 2014 raw data only)
# meta_source: local filename (relative to RAW_DIR) or URL
# meta_cols: {dst_col: src_col} mapping to rename to unit_id/isp/technology/speed_tier_down
YEARS_CONFIG = {
    # --- On disk (already processed) ---
    2011: {
        "month": "March",
        "month_num": "03",
        "month_dir": "validated-march",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
        "has_header": True,
        "tarball_url": "",
        "meta_source": "unit_metadata.csv",
        "meta_engine": "",
        "meta_cols": {
            "unit_id": "UnitID",
            "isp": "ISP",
            "technology": "TECHNOLOGY",
            "speed_tier_down": "ISP DOWN",
        },
    },
    2014: {
        "month": "September",
        "month_num": "09",
        "month_dir": "sept",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
        "has_header": False,
        "tarball_url": "https://data.fcc.gov/download/measuring-broadband-america/2014/data-validated-2013-sept.tar.gz",
        "meta_source": "https://data.fcc.gov/download/measuring-broadband-america/2013/FCC_Unit_Profile_20140207.xlsx",
        "meta_engine": "openpyxl",
        "meta_cols": {
            "unit_id": "unit_id",
            "isp": "isp",
            "technology": "TECHNOLOGY",
            "speed_tier_down": "DOWN",
        },
    },
    # --- To download and process (validated data, all have headers) ---
    2012: {
        "month": "April",
        "month_num": "04",
        "month_dir": "april",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
        "has_header": True,
        "tarball_url": "https://data.fcc.gov/download/measuring-broadband-america/2012/data-validated--2012-apr.tar.gz",
        "meta_source": "https://data.fcc.gov/download/measuring-broadband-america/2012/FCC_UnitProfile_Sept12.xls",
        "meta_engine": "xlrd",
        "meta_cols": {
            "unit_id": "unit_id",
            "isp": "isp",
            "technology": "Technology",
            "speed_tier_down": "Download",
        },
    },
    2013: {
        "month": "September",
        "month_num": "09",
        "month_dir": "sept",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
        "has_header": False,
        "tarball_url": "https://data.fcc.gov/download/measuring-broadband-america/2012/data-validated-2012-sept.tar.gz",
        "meta_source": "https://data.fcc.gov/download/measuring-broadband-america/2012/FCC_UnitProfile_Sept12.xls",
        "meta_engine": "xlrd",
        "meta_cols": {
            "unit_id": "unit_id",
            "isp": "isp",
            "technology": "Technology",
            "speed_tier_down": "Download",
        },
    },
    2015: {
        "month": "September",
        "month_num": "09",
        "month_dir": "sept",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
        "has_header": True,
        "tarball_url": "https://data.fcc.gov/download/measuring-broadband-america/2015/data-validated-2014-sept.tar.gz",
        "meta_source": "https://data.fcc.gov/download/measuring-broadband-america/2015/FCC_UnitProfile_Sept14.xls",
        "meta_engine": "openpyxl",
        "meta_cols": {
            "unit_id": "unit_id",
            "isp": "isp",
            "technology": "TECHNOLOGY",
            "speed_tier_down": "SK down",
        },
    },
    2016: {
        "month": "September",
        "month_num": "09",
        "month_dir": "sept",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
        "has_header": False,
        "tarball_url": "https://data.fcc.gov/download/measuring-broadband-america/2016/validated-data-sept2015.tar.gz",
        "meta_source": "https://data.fcc.gov/download/measuring-broadband-america/2016/Unit-Profile-sept2015.xlsx",
        "meta_engine": "openpyxl",
        "meta_cols": {
            "unit_id": "unit_id",
            "isp": "isp",
            "technology": "TECHNOLOGY",
            "speed_tier_down": "Download",
        },
    },
    2017: {
        "month": "September",
        "month_num": "09",
        "month_dir": "sept",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
        "has_header": True,
        "tarball_url": "https://data.fcc.gov/download/measuring-broadband-america/2017/validated-data-sept2016.tar.gz",
        "meta_source": "https://data.fcc.gov/download/measuring-broadband-america/2017/Unit-Profile-sept2016.xlsx",
        "meta_engine": "openpyxl",
        "meta_cols": {
            "unit_id": "unit_id",
            "isp": "isp",
            "technology": "Technology",
            "speed_tier_down": "Download",
        },
    },
    2018: {
        "month": "September",
        "month_num": "09",
        "month_dir": "sept",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
        "has_header": True,
        "tarball_url": "https://data.fcc.gov/download/measuring-broadband-america/2018/validated-data-sept2017.tar.gz",
        "meta_source": "https://data.fcc.gov/download/measuring-broadband-america/2018/Unit-Profile-sept2017.xlsx",
        "meta_engine": "openpyxl",
        "meta_cols": {
            "unit_id": "unit_id",
            "isp": "ISP",
            "technology": "Technology",
            "speed_tier_down": "Download",
        },
    },
    2019: {
        "month": "September",
        "month_num": "09",
        "month_dir": "sept",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
        "has_header": True,
        "tarball_url": "https://data.fcc.gov/download/measuring-broadband-america/2019/validated-data-sept2018.tar.gz",
        "meta_source": "https://data.fcc.gov/download/measuring-broadband-america/2019/Unit-Profile-sept2018.xlsx",
        "meta_engine": "openpyxl",
        "meta_cols": {
            "unit_id": "Unit ID",
            "isp": "ISP",
            "technology": "Technology",
            "speed_tier_down": "Download",
        },
    },
    2020: {
        "month": "September",
        "month_num": "09",
        "month_dir": "sept",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
        "has_header": True,
        "tarball_url": "https://data.fcc.gov/download/measuring-broadband-america/2020/validated-data-sept2019.tar.gz",
        "meta_source": "https://data.fcc.gov/download/measuring-broadband-america/2020/Unit-Profile-sept2019.xlsx",
        "meta_engine": "openpyxl",
        "meta_cols": {
            "unit_id": "Unit ID",
            "isp": "ISP",
            "technology": "Technology",
            "speed_tier_down": "Download",
        },
    },
    2021: {
        "month": "September",
        "month_num": "09",
        "month_dir": "sept",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
        "has_header": True,
        "tarball_url": "https://data.fcc.gov/download/measuring-broadband-america/2021/validated-data-sept2020.tar.gz",
        "meta_source": "https://data.fcc.gov/download/measuring-broadband-america/2021/unit-profile-sept2020.xlsx",
        "meta_engine": "openpyxl",
        "meta_cols": {
            "unit_id": "Unit ID",
            "isp": "ISP",
            "technology": "Technology",
            "speed_tier_down": "Download",
        },
    },
    2022: {
        "month": "September",
        "month_num": "09",
        "month_dir": "sept",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
        "has_header": True,
        "tarball_url": "https://data.fcc.gov/download/measuring-broadband-america/2022/validated-data-sept2021.tar.gz",
        "meta_source": "https://data.fcc.gov/download/measuring-broadband-america/2022/unit-profile-sept2021.xlsx",
        "meta_engine": "openpyxl",
        "meta_cols": {
            "unit_id": "Unit ID",
            "isp": "ISP",
            "technology": "Technology",
            "speed_tier_down": "Download",
        },
    },
    2023: {
        "month": "September",
        "month_num": "09",
        "month_dir": "sept",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
        "has_header": True,
        "tarball_url": "https://data.fcc.gov/download/measuring-broadband-america/2023/validated-data-sept2022.tar.gz",
        "meta_source": "https://data.fcc.gov/download/measuring-broadband-america/2023/unit-profile-sept2022.xlsx",
        "meta_engine": "openpyxl",
        "meta_cols": {
            "unit_id": "Unit ID",
            "isp": "ISP",
            "technology": "Technology",
            "speed_tier_down": "Download",
        },
    },
}

# Resolve current year config
YC = YEARS_CONFIG[YEAR]
MONTH = YC["month"].lower()
MONTH_NUM = YC["month_num"]

RAW_DIR = os.path.join(BASE_DIR, "data", "raw", str(YEAR), YC["month_dir"])
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed", str(YEAR))
OUTPUT_DIR = os.path.join(BASE_DIR, "output", str(YEAR))

TCP_CSV = YC["tcp_csv"]
WEB_CSV = YC["web_csv"]
META_SOURCE = YC["meta_source"]
META_ENGINE = YC["meta_engine"]
META_COLS = YC["meta_cols"]
HAS_HEADER = YC["has_header"]
TARBALL_URL = YC["tarball_url"]

MONTHS = [MONTH]

KEEP_TECHNOLOGIES = None  # None = keep all

RC_Q = 0.8
RC_T = 0.2

TIS_R_THRESH = 0.6
TIS_COUNT_THRESH = 5

MIN_MATCHED_PAIRS = 180
SPEED_TIER_VARIATION_THRESH = 0.5

ALIGNMENT_WINDOW_HOURS = 1

WEBSITES = [
    "cnn.com",
    "youtube.com",
    "msn.com",
    "amazon.com",
    "yahoo.com",
    "ebay.com",
    "wikipedia.org",
    "facebook.com",
    "google.com",
    "netflix.com",
]
