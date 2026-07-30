#!/usr/bin/env bash
set -euo pipefail

YEAR=$1
BASE_DIR="/home/jovyan/work/project"
RAW_DIR="${BASE_DIR}/data/raw/${YEAR}"
# Determine month_dir from config
MONTH_DIR=$(python3 -c "from config import YC; print(YC['month_dir'])")
FULL_RAW="${RAW_DIR}/${MONTH_DIR}"

echo "============================================"
echo "  Processing year ${YEAR}..."
echo "============================================"

# 1. Create raw data directory
mkdir -p "${FULL_RAW}"

# 2. Download tarball
TARBALL_URL=$(python3 -c "from config import YC; print(YC['tarball_url'])")
TARBALL_NAME=$(basename "${TARBALL_URL}")
echo "Downloading ${TARBALL_URL} ..."
# Use wget with progress
wget -q --show-progress "${TARBALL_URL}" -O "/tmp/${TARBALL_NAME}" 2>&1 || \
  { echo "Download failed for ${YEAR}"; exit 1; }
echo "Downloaded: $(ls -lh /tmp/${TARBALL_NAME} | awk '{print $5}')"

# 3. Extract only the two CSVs we need
TCP_CSV=$(python3 -c "from config import YC; print(YC['tcp_csv'])")
WEB_CSV=$(python3 -c "from config import YC; print(YC['web_csv'])")
echo "Extracting ${TCP_CSV} and ${WEB_CSV} ..."
python3 -c "
import tarfile
tf = tarfile.open('/tmp/${TARBALL_NAME}')
for name in tf.getnames():
    if name.endswith('${TCP_CSV}') or name.endswith('${WEB_CSV}'):
        print(f'Extracting {name}')
        f = tf.extractfile(name)
        if f:
            import os
            outpath = os.path.join('${FULL_RAW}', os.path.basename(name))
            with open(outpath, 'wb') as out:
                out.write(f.read())
            print(f'  -> {outpath} ({os.path.getsize(outpath)} bytes)')
"

# 4. Delete tarball
rm -v "/tmp/${TARBALL_NAME}"

# 5. Run the pipeline
echo "Running pipeline for year ${YEAR}..."
YEAR="${YEAR}" python3 "${BASE_DIR}/src/run_all.py" "${YEAR}"

echo "Year ${YEAR} processing complete!"
