import os
import subprocess
import sys
from config import RAW_DIR

URL = "https://data.fcc.gov/download/measuring-broadband-america/validated-march-data-2011.tar.gz"
TAR_PATH = os.path.join(os.path.dirname(RAW_DIR), "validated-march-data-2011.tar.gz")

def main():
    os.makedirs(os.path.dirname(RAW_DIR), exist_ok=True)
    if os.path.exists(TAR_PATH):
        print(f"Tarball already exists at {TAR_PATH}, skipping download.")
    else:
        print("Downloading validated March 2011 data (~2.5 GB)...")
        subprocess.run(["curl", "-L", "--retry", "3", "-o", TAR_PATH, URL], check=True)
        print("Download complete.")

    os.makedirs(RAW_DIR, exist_ok=True)
    print("Extracting...")
    subprocess.run(["tar", "xzf", TAR_PATH, "-C", RAW_DIR], check=True)
    print(f"Extracted to {RAW_DIR}")

if __name__ == "__main__":
    main()
