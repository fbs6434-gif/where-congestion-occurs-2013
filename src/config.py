import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Year-specific settings (override with YEAR env var) ---
YEAR = int(os.environ.get("YEAR", "2011"))
MONTH = "march"
MONTH_NUM = "03"

# --- Where to find raw data ---
if YEAR == 2011:
    RAW_DIR = os.path.join(BASE_DIR, "data", "raw", "2011", "validated-march")
    DATA_IS_VALIDATED = True
    TCP_CSV = "curr_httpgetmt.csv"
    WEB_CSV = "curr_webget.csv"
    META_CSV = "unit_metadata.csv"
    META_URL = ""
    META_ENGINE = ""
elif YEAR == 2014:
    RAW_DIR = os.path.join(BASE_DIR, "data", "raw", "2014", "201403")
    DATA_IS_VALIDATED = False
    TCP_CSV = f"curr_httpgetmt_2014_{MONTH_NUM}.csv"
    WEB_CSV = f"curr_webget_2014_{MONTH_NUM}.csv"
    META_URL = "https://data.fcc.gov/download/measuring-broadband-america/2015/FCC_UnitProfile_Sept14.xls"
    META_ENGINE = "openpyxl"
    META_CSV = ""
elif YEAR == 2019:
    RAW_DIR = os.path.join(BASE_DIR, "data", "raw", "2019", "201903")
    DATA_IS_VALIDATED = False
    TCP_CSV = "curr_httpgetmt.csv"
    WEB_CSV = "curr_webget.csv"
    META_URL = "https://data.fcc.gov/download/measuring-broadband-america/2019/unit-profile-sept2018.xlsx"
    META_ENGINE = "openpyxl"
    META_CSV = ""

PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed", str(YEAR))
OUTPUT_DIR = os.path.join(BASE_DIR, "output", str(YEAR))

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
