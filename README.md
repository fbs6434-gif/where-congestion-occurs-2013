# Where in the Internet is congestion? — Reproduction

Reproduction of Genin & Splett (2013) [arXiv:1307.3696](https://arxiv.org/abs/1307.3696) using FCC SamKnows Measuring Broadband America data.

## Goal

Determine where recurrent congestion occurs in US residential broadband — in the ISP's **initial segment** (last mile) or **beyond the initial segment** (middle mile / public Internet) — for DSL and Cable access networks.

## Data

| Property | Value |
|----------|-------|
| Source | FCC Measuring Broadband America (SamKnows) |
| URL | https://data.fcc.gov/download/measuring-broadband-america/2011/ |
| Period | March, April, May, June 2011 |
| Technologies | DSL, Cable |
| Units | ~13,000 Whiteboxes → ~2,800 after filtering |

## Methodology

### Step 1 — Download
Run `src/01_download_data.sh` to fetch the four monthly tarballs.

### Step 2 — Load & Filter
Parse CSVs, merge on `unit_id`, keep only DSL and Cable connections.

### Step 3 — Speed Tier Detection
For each unit per month:
- Compute daily maximum sustained throughput
- If `(max - min) / mean > 0.5`, discard (speed tier changed)
- Otherwise set `speed_tier = mean(daily_max)`

### Step 4 — Time Series Alignment
For each unit per month, pair each M-Lab throughput test with the nearest measurement for each of 10 websites (±1 hour window). Drop unit-months with fewer than 180 paired measurements.

### Step 5 — Recurrent Congestion (RC)
For each unit-month: RC = True if `P(throughput / speed_tier < 0.8) > 0.2`

### Step 6 — Tight Initial Segment (TIS)
For each unit-month:
- Compute 10 Pearson correlations (M-Lab throughput × each website load time)
- TIS = True if ≥5 of 10 correlations exceed 0.6
- Correlations are only computed for (unit, site) series with ≥180 paired measurements (`TIS_MIN_SERIES`)

> Filter detail: the completeness filter (`MIN_MATCHED_RUNS`) counts distinct matched
> benchmark runs per unit-month (the paper's notion of a "matching pair"), not aligned rows.

### Step 7 — Aggregate
Cross-tabulate RC × TIS per ISP × technology × month.

### Step 8 — Plot
Generate Figures 3–7 and Tables I–II from the paper.

## Expected Results

| Metric | DSL | Cable |
|--------|-----|-------|
| RC% | 9–12% | 27–32% |
| TIS% | 5–7% | 3–4% |
| RC∩TIS / TIS | 37–50% | 91–100% |
| **RC∩TIS / RC** | **65–67%** | **8–13%** |

## Usage

```bash
pip install -r requirements.txt
bash src/01_download_data.sh
python src/run_all.py
```

Output goes to `output/tables/` and `output/figures/`.

## Extensions

- **Multi-year (2011–2023):** `src/09_compare_years.py` aggregates `isp_agg.parquet` across
  all years into `output/compare/` (tables + trend figures).
- **Reproduction fidelity and trend analysis:** see [`ANALYSIS.md`](ANALYSIS.md).
