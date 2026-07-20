#!/usr/bin/env bash
set -euo pipefail

BASE_URL="https://data.fcc.gov/download/measuring-broadband-america/2011"
DATA_DIR="data/raw"

mkdir -p "$DATA_DIR"

for month in march april may june; do
    fname="raw-data-${month}-2011.tar.gz"
    echo "Downloading $fname ..."
    wget -q --show-progress "${BASE_URL}/${fname}" -O "${DATA_DIR}/${fname}"
    echo "Extracting $fname ..."
    tar xzf "${DATA_DIR}/${fname}" -C "$DATA_DIR"
done

echo "Done. Raw data in $DATA_DIR"
