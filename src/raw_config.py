import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

YEAR = int(os.environ.get("YEAR", "2011"))

import monthly_config as _mc

_MONTH_ENV = os.environ.get("MONTH", "").strip()
_MONTHLY = _MONTH_ENV.isdigit()
DATASET = os.environ.get("DATASET", "raw").strip().lower()

# Raw bulk data: collection month per analysis year.
# key: analysis-year label (collection month). 2011=Mar, 2012=Apr, 2013+=Sep.
# Not every collection month has a public raw tarball; 2022-sep does NOT (see ANALYSIS.md).
#   t: full URL of the raw tarball
#   tbl_name: tarball filename (also the local cache name under data/raw_bk/<year>/)
#   tcp_csv / web_csv: CSV basenames inside the tarball (located by basename,
#       because tarballs may wrap files in a "YYYYMM/" directory).
RAWS = {
    2011: {
        "month": "March",
        "month_num": "03",
        "t": "https://data.fcc.gov/download/measuring-broadband-america/raw-bulk-mar-2011.tar.gz",
        "tbl_name": "raw-bulk-mar-2011.tar.gz",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
    },
    2012: {
        "month": "April",
        "month_num": "04",
        "t": "https://data.fcc.gov/download/measuring-broadband-america/2012/data-raw-2012-apr.tar.gz",
        "tbl_name": "data-raw-2012-apr.tar.gz",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
    },
    2013: {
        "month": "September",
        "month_num": "09",
        "t": "https://data.fcc.gov/download/measuring-broadband-america/2012/data-raw-2012-sept.tar.gz",
        "tbl_name": "data-raw-2012-sept.tar.gz",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
    },
    2014: {
        "month": "September",
        "month_num": "09",
        "t": "https://data.fcc.gov/download/measuring-broadband-america/2014/data-raw-2013-sept.tar.gz",
        "tbl_name": "data-raw-2013-sept.tar.gz",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
    },
    2015: {
        "month": "September",
        "month_num": "09",
        "t": "https://data.fcc.gov/download/measuring-broadband-america/2015/data-raw-2014-sept.tar.gz",
        "tbl_name": "data-raw-2014-sept.tar.gz",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
    },
    2016: {
        "month": "September",
        "month_num": "09",
        "t": "https://data.fcc.gov/download/measuring-broadband-america/2016/data-raw-2015-sept.tar.gz",
        "tbl_name": "data-raw-2015-sept.tar.gz",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
    },
    2017: {
        "month": "September",
        "month_num": "09",
        "t": "https://data.fcc.gov/download/measuring-broadband-america/2017/data-raw-2016-sept.tar.gz",
        "tbl_name": "data-raw-2016-sept.tar.gz",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
    },
    2018: {
        "month": "September",
        "month_num": "09",
        "t": "https://data.fcc.gov/download/measuring-broadband-america/2017/data-raw-2017-sept.tar.gz",
        "tbl_name": "data-raw-2017-sept.tar.gz",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
    },
    2019: {
        "month": "September",
        "month_num": "09",
        "t": "https://data.fcc.gov/download/measuring-broadband-america/2018/data-raw-2018-sept.tar.gz",
        "tbl_name": "data-raw-2018-sept.tar.gz",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
    },
    2020: {
        "month": "September",
        "month_num": "09",
        "t": "https://data.fcc.gov/download/measuring-broadband-america/2019/data-raw-2019-sept.tar.gz",
        "tbl_name": "data-raw-2019-sept.tar.gz",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
    },
    2021: {
        "month": "September",
        "month_num": "09",
        "t": "https://data.fcc.gov/download/measuring-broadband-america/2020/data-raw-2020-sep.tar.gz",
        "tbl_name": "data-raw-2020-sep.tar.gz",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
    },
    2022: {
        "month": "September",
        "month_num": "09",
        "t": "https://data.fcc.gov/download/measuring-broadband-america/2021/data-raw-2021-sep.tar.gz",
        "tbl_name": "data-raw-2021-sep.tar.gz",
        "tcp_csv": "curr_httpgetmt.csv",
        "web_csv": "curr_webget.csv",
    },
}

# No public raw tarball for the Sept 2022 collection; key 2023 stays on validated data.
if _MONTHLY:
    YEAR_MONTH = int(_MONTH_ENV)
    _row = _mc.tarball("raw", YEAR, YEAR_MONTH)
    RAW_TAR_NAME = _row["filename"]
    RAW_URL = _row["url"]
    RAW_TAR_S3_KEY = _row["s3_key"]
    RAW_TCP_CSV = "curr_httpgetmt.csv"
    RAW_WEB_CSV = "curr_webget.csv"
    RAW_DIR, PROCESSED_DIR, OUTPUT_DIR = _mc.dirs("raw", YEAR, YEAR_MONTH)
    RAW_BK_DIR = os.path.join(BASE_DIR, "data", "raw_bk", f"raw-{YEAR}-{YEAR_MONTH:02d}")
else:
    RAW_URL = RAWS[YEAR]["t"]
    RAW_TAR_NAME = RAWS[YEAR]["tbl_name"]
    RAW_TCP_CSV = RAWS[YEAR]["tcp_csv"]
    RAW_WEB_CSV = RAWS[YEAR]["web_csv"]

    # Multi-month reproduction (paper used Mar-Jun 2011): select a month with MONTH=april|may|june
    # (MONTH=march is the default single-tarball path above).
    _MONTH = os.environ.get("MONTH", "").strip().lower()
    MONTHS_2011 = {
        "march": ("raw-bulk-data-mar-2011.tar.gz",
                  "https://data.fcc.gov/download/measuring-broadband-america/raw-bulk-data-mar-2011.tar.gz"),
        "april": ("raw-bulk-data-apr-2011.tar.gz",
                  "https://data.fcc.gov/download/measuring-broadband-america/raw-bulk-data-apr-2011.tar.gz"),
        "may": ("raw-bulk-data-may-2011.tar.gz",
                "https://data.fcc.gov/download/measuring-broadband-america/raw-bulk-data-may-2011.tar.gz"),
        "june": ("raw-bulk-data-jun-2011.tar.gz",
                 "https://data.fcc.gov/download/measuring-broadband-america/raw-bulk-data-jun-2011.tar.gz"),
    }

    if YEAR == 2011 and _MONTH in MONTHS_2011:
        RAW_TAR_NAME, RAW_URL = MONTHS_2011[_MONTH]
        RAW_DIR = os.path.join(BASE_DIR, "data", "raw", "2011", _MONTH, "raw")
        PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed", f"2011_{_MONTH}")
        OUTPUT_DIR = os.path.join(BASE_DIR, "output", f"2011_{_MONTH}")
    else:
        RAW_DIR = os.path.join(BASE_DIR, "data", "raw", str(YEAR), "raw")
        PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed", str(YEAR))
        OUTPUT_DIR = os.path.join(BASE_DIR, "output", str(YEAR))

    RAW_BK_DIR = os.path.join(BASE_DIR, "data", "raw_bk", str(YEAR))

TAR_PATH = os.path.join(RAW_BK_DIR, RAW_TAR_NAME)