# Processing One Month for the Monthly Panel

This doc describes the operational procedure for computing one month of
congestion data (raw **or** validated) and adding its row(s) to the panel CSV.

The pipeline is **year-keyed** in `src/config.py` / `src/raw_config.py`
(one month per analysis year). To build the monthly panel we process one
(year, month, dataset) at a time and append the result.

## 1. The CSV file you are augmenting

**`output/tables/monthly_panel_raw_validated.csv`** — one row per
(year, month, dataset, technology):

| column       | type | meaning                                              |
|--------------|------|------------------------------------------------------|
| `data_year`  | int  | collection year of the month                         |
| `data_month` | int  | collection month (1–12)                              |
| `dataset`    | str  | `raw` or `validated`                                 |
| `technology` | str  | `cable` \| `dsl` \| `fiber` \| `overall`             |
| `n_units`    | int  | number of units (after the relevant filter)          |
| `rc`         | int  | units flagged Recurrent Congestion (count, not %)    |
| `tis`        | int  | units flagged Tight Initial Segment (count, not %)   |

Each month contributes **4 rows** (cable, dsl, fiber, overall) per dataset.

## 2. Choosing a month

The authoritative inventory of what exists is
**`output/staging/fcc_manifest.csv`** (produced by
`src/00_scrape_fcc_manifest.py`). It lists every raw/validated/profile file,
its FCC URL, its S3 key under `s3://mba-data/fcc-mba/<year>/<kind>/`, size and
sha256.

Known gaps (verified against FCC directory listings): raw is missing
2011-jan, 2020-oct, 2022-sept, 2022-oct; 2023 raw stops at July; 2023 has no
validated month.

## 3. Data source

The tarball for the month lives in S3:

- `s3://mba-data/fcc-mba/<year>/raw/<tarball>` (e.g. `data-raw-2013-mar.tar.gz`)
- `s3://mba-data/fcc-mba/<year>/validated/<tarball>` (e.g. `data-validated-2013-sept.tar.gz`)
- unit profile: `s3://mba-data/fcc-mba/<year>/profile/<file>`

**Disk discipline:** the VM has ~64 GB free and tarballs are 2–6 GB.
Always work one month at a time: download → process → delete the tarball
before moving on. Never accumulate months on local disk.

## 4. Setup needed per month

The pipeline reads configuration from `config.py` (validated) or
`raw_config.py` (raw), keyed by `YEAR`. Each run needs:

1. A config entry for that exact (year, month) pointing at the tarball URL,
   the `curr_httpgetmt.csv` / `curr_webget.csv` basenames, the `has_header`
   flag, and the unit-profile source.
2. `data_month`/`month` value so downstream steps label the month correctly.

> **For months not already in the configs** (i.e. any month other than the
> one per analysis year already present), add an entry mirroring the existing
> ones before running. The manifest row for the month supplies the tarball
> URL/filename.

## 5. Validated vs raw — the one rule that differs

The only intentional difference between datasets is in
**`src/03_detect_speed_tier.py:21-23`**, which drops units whose
`(daily_max.max() - daily_max.min()) / mean > 0.5` — the "mid-month plan
change" inference:

- **raw**: keep this filter (matches the existing raw pipeline).
- **validated**: skip it — do **not** infer that a plan changed mid-month.

Concretely the script needs a `SKIP_PLAN_CHANGE_FILTER` env toggle around
that variation check; when set, units pass through as long as they have
`>= 15` days of data and non-zero mean speed tier. (This toggle is the small
code change required before the first validated month is processed this way.)

## 6. Running one month

Both paths below assume the tarball is on local disk under
`data/raw/<year>/<month_dir>/`. Set `YEAR` (and for 2011 the `MONTH` env
var, `march|april|may|june`) for every step.

### 6a. Validated month

```bash
# download the validated tarball + unit profile from S3 first, then:
YEAR=<year> python src/run_all.py <year>
```

`run_all.py` runs, in order:
`02_load_and_filter` → `03_detect_speed_tier` → `04_align_time_series` →
`05_compute_rc` → `06_compute_tis` → `07_aggregate` → `08_plot`.
For validated months run `03` with the skip toggle set (see §5).

### 6b. Raw month

```bash
# download the raw tarball from S3 first, then:
YEAR=<year> python src/01b_load_raw.py      # ingest tarball -> tcp/web parquet
YEAR=<year> python src/02_raw_meta.py       # attach profile -> meta.parquet
YEAR=<year> python src/03_detect_speed_tier.py   # raw: KEEP the plan-change filter
YEAR=<year> python src/04_align_time_series.py
YEAR=<year> python src/05_compute_rc.py
YEAR=<year> python src/06_compute_tis.py
YEAR=<year> python src/07_aggregate.py
YEAR=<year> python src/08_plot.py
```

(`src/run_raw_all.sh` does the same loop for a list of years.)

### 6c. What each step produces

All outputs land in `data/processed/<year>/`:

| step | output | purpose |
|------|--------|---------|
| 01b / 02 | `tcp.parquet`, `web.parquet`, `meta.parquet` | raw measurements + profile |
| 03 | `meta_valid.parquet` | units passing speed-tier filter (this is where the validated/raw difference lives) |
| 04 | `aligned.parquet` | TCP×web matched pairs per unit-month |
| 05 | `rc.parquet` | per-unit boolean `rc` |
| 06 | `tis.parquet` | per-unit boolean `tis` |
| 07 | `output/<year>/tables/table_{tech}.csv`, `table_overall.csv`, `isp_agg.parquet` | aggregated tables |

## 7. Computing the panel row and appending

The 4 rows for the month are derived from `07_aggregate` output
(`isp_agg.parquet`, which has per-ISP per-technology `N`/`RC`/`TIS` counts):

```python
import pandas as pd, os

BASE = "/home/jovyan/work/project"
year, month, dataset = 2013, 3, "raw"        # example
agg = pd.read_parquet(os.path.join(BASE, "data", "processed", str(year), "isp_agg.parquet"))

TECH_MAP = {"uverse": "dsl", "ipbb": "dsl"}
KEEP = {"cable", "dsl", "fiber"}
agg["technology"] = agg["technology"].map(TECH_MAP).fillna(agg["technology"])
rows = []
for tech in sorted(KEEP):
    sub = agg[agg["technology"] == tech]
    rows.append([year, month, dataset, tech, int(sub["N"].sum()),
                 int(sub["RC"].sum()), int(sub["TIS"].sum())])
rows.append([year, month, dataset, "overall", int(agg["N"].sum()),
             int(agg["RC"].sum()), int(agg["TIS"].sum())])

panel = os.path.join(BASE, "output", "tables", "monthly_panel_raw_validated.csv")
out = pd.DataFrame(rows, columns=["data_year", "data_month", "dataset",
                                  "technology", "n_units", "rc", "tis"])
if os.path.exists(panel):
    out = pd.concat([pd.read_csv(panel), out], ignore_index=True)
out = out.sort_values(["data_year", "data_month", "dataset", "technology"]).drop_duplicates()
out.to_csv(panel, index=False)
print(out)
```

Sanity checks before appending:
- `rc` and `tis` are **counts** (`N_rc`, `N_tis`), not percentages.
- `n_units` should match the per-technology totals printed by `07_aggregate`.
- Rerunning the same (year, month, dataset) should not duplicate rows
  (`drop_duplicates` guards this).

## 8. Cleanup

```bash
rm -f data/raw/<year>/<month_dir>/curr_httpgetmt.csv data/raw/<year>/<month_dir>/curr_webget.csv
```

Keep the small parquets (`data/processed/<year>/`) until you've confirmed
the rows; the tarball must always be deleted after each month.

## 9. Throughput expectations

- Ingest (01b / 02): ~10 min per month.
- Rest of pipeline (03→07): ~5 min per month.
- ~15 min sequential per month; 154 month-runs (141 raw + 13 validated)
  ≈ 1.5 days serial. Multiple months can be run concurrently (each streaming
  from S3) to cut wall-clock time.
