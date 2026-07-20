import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw", "2011", "validated-march")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

MONTHS = ["march"]

KEEP_TECHNOLOGIES = ["dsl", "cable"]

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
]
