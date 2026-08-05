# Analysis — Reproduction fidelity and multi-year trends

This document summarizes two pieces of work on the reproduction of Genin & Splett (2013),
*Where in the Internet is congestion?* ([arXiv:1307.3696](https://arxiv.org/abs/1307.3696)):

1. Why the 2011 reproduction does not exactly match the paper's published numbers.
2. What the extended 2011–2023 FCC Measuring Broadband America (SamKnows) analysis shows.

## 1. Reproduction fidelity (2011)

### Paper vs. our pipeline (default/legacy filters)

| Metric (March 2011) | Paper | Ours |
|---|---|---|
| Units analyzed (DSL + cable) | ~2,400–2,900 / month | 5,095 (3,047 cable + 2,048 DSL) |
| Cable recurrent congestion (RC) | 27–32% | 21.2% |
| DSL RC | 9–12% | 5.4% |
| Cable tight initial segment (TIS) | 3–4% | 1.4% |
| DSL TIS | 5–7% | 2.4% |
| Cable RC∩TIS / RC | 8–13% | 6.3% |
| DSL RC∩TIS / RC | 65–67% | 31.5% |

### Paper-faithful filter variant

`src/config.py` supports a paper-faithful completeness filter via
`COMPLETENESS_MODE=runs` (count distinct matched benchmark runs, ≥180 per unit-month)
plus `TIS_MIN_SERIES=180` (per-site series length before a correlation counts). Evaluated
on 2011 this admitted 4,474 units (2,717 cable + 1,757 DSL) and moved every metric by only
~0.2–0.5 percentage points (cable RC 21.9%, DSL RC 5.6%, cable TIS 1.5%, DSL TIS 2.6%).

### Why the numbers differ

The gap is **data-level, not filter-level** — switching to the paper's exact filter
thresholds barely moved the metrics. Three data-level differences explain it:

1. **Raw vs. validated data.** The paper used the four *raw* 2011 monthly tarballs
   (its reference [16]); we use the validated March 2011 tarball. The validated file contains
   7,378 units vs. ~13,404 in the raw data — a different, smaller population.
2. **No last-5-second throughput column.** The paper (footnote 4) used the last-5-second
   sustained rate (`bytes_sec_interval`) to make speed-tier estimation robust to PowerBoost.
   The validated `curr_httpgetmt.csv` contains only the full-run average (`bytes_sec`), so the
   estimated speed tier (mean of daily maxima) is computed from a different quantity.
3. **Different time window.** The paper's numbers span March–June with several ISPs and a
   full monthly schedule; our validated file is a single month.

**Qualitative conclusions are preserved.** Even with lower absolute levels, the paper's core
signatures hold in direction: cable RC ≫ DSL RC; a tight initial segment almost always
coincides with recurrent congestion for cable (RC∩TIS/TIS ≈ 95%) but less so for DSL
(≈ 70%); and DSL recurrent congestion is far more likely than cable's to originate on the
initial segment (RC∩TIS/RC ≈ 32% vs. ~6%).

To reproduce the paper's exact numbers, re-run the pipeline on the **raw** 2011 data
(see reference [16]) rather than the validated subset.

## 2. Multi-year trends (2011–2023)

The methodology (RC, TIS) was applied to one month per year of FCC MBA validated data,
uniformly with the default completeness filter. Yearly sample sizes and prevalences
(cable, DSL) are in `output/compare/tables/comparison_by_tech.csv`.

| Year | Month | Cable N | Cable RC% | Cable TIS% | DSL N | DSL RC% | DSL TIS% |
|---|---|---|---|---|---|---|---|
| 2011 | March | 3,047 | 21.2 | 1.4 | 2,048 | 5.4 | 2.4 |
| 2012 | April | 3,214 | 10.0 | 0.3 | 1,828 | 4.9 | 2.5 |
| 2013 | September | 3,534 | 10.7 | 0.2 | 1,915 | 4.2 | 2.4 |
| 2014 | September | 3,103 | 7.5 | 0.0 | 1,521 | 3.5 | 1.2 |
| 2015 | September | 2,953 | 6.4 | 0.0 | 1,259 | 12.1 | 2.3 |
| 2016 | September | 2,233 | 4.4 | 0.3 | 1,224 | 10.3 | 4.1 |
| 2017 | September | 1,861 | 4.7 | 0.3 | 1,275 | 10.4 | 2.4 |
| 2018 | September | 1,593 | 6.9 | 0.0 | 1,413 | 12.4 | 0.0 |
| 2019 | September | 916 | 6.3 | 0.0 | 1,324 | 6.0 | 0.0 |
| 2020 | September | 952 | 4.0 | 0.0 | 970 | 8.4 | 0.0 |
| 2021 | September | 1,202 | 2.3 | 0.0 | 1,265 | 4.7 | 0.0 |
| 2022 | September | 1,160 | 4.0 | 0.0 | 1,213 | 5.5 | 0.0 |
| 2023 | September | 486 | 2.7 | 0.0 | 1,016 | 6.6 | 0.0 |

### Findings

1. **Cable recurrent congestion has collapsed.** Cable RC% fell from ~21% (2011) to ~2–7%
   (2017 onward), a decline of roughly 3–4×. The paper's headline asymmetry — cable suffering
   far more recurrent congestion than DSL — has essentially disappeared by the mid-2010s.
2. **DSL RC stayed roughly flat.** DSL RC% hovers in the 3–8% range, with a 2015–2018 bump
   to ~10–12%. DSL, not cable, is now the higher-RC technology in most years.
3. **TIS collapses to ~0 for every technology from ~2017/2018.** This is a **methodological
   break, not evidence that initial-segment congestion vanished**. The FCC changed the website
   test set over time — by 2019 the sites were imdb, bing, bbc, apple, cnn, ebay, google
   (youtube, facebook, wikipedia, yahoo, netflix gone) — and benchmark↔website correlations
   systematically weakened (mean high-correlation count per unit fell from 0.20 in 2011 to
   0.06 in 2019, and no unit reached the ≥5 threshold). The TIS detector is calibrated to the
   2011-era test design; in modern data it no longer fires.
4. **Sample sizes shrank** as the FCC MBA unit fleet declined (cable 3,047 → 486; DSL 2,048 →
   1,016), so later-year prevalences are noisier.
5. **Fiber** (present from 2012) shows consistently low RC (≈0.4–6.5%). **Satellite** data
   (2013–2018) shows very high RC (up to 85% in 2017–2018) but with tiny samples.

### What drives the trends

- **Speed tiers.** Median estimated cable tier rose ~7× (16.8 → 119.7 Mbps, 2011→2019); DSL
  only ~3.7× (3.0 → 11.2 Mbps). Cable RC fell *despite* a ~7× harder tier target, so the cable
  improvement is real capacity/tier investment, not re-baselining downward.
- **RC severity is unchanged.** Among congested units, the median share of measurements below
  0.8× tier is ~0.27–0.34 in every year. Prevalence collapsed; the failure mode did not.
- **Cable collapse is industry-wide, not one ISP.** Every major cable ISP improved
  (Cablevision 74→≤7%, Cox 46→8%, Mediacom 22→3%, Comcast 15→~5%, Charter 14→~6%,
  TimeWarner 16→~6%). 2011's cable headline was largely a two-ISP story (Cablevision + Cox).
- **DSL bump is a specific-ISP wave.** Frontier (19%), AT&T (10%), Windstream (19%), Qwest (9%)
  all spiked around 2015; Windstream had already been high (14–17%) in 2012–2013. The DSL fleet
  churns (Verizon DSL exits by 2015, AT&T DSL by 2019).

### Caveats

- **Uniform filter, documented alternative.** All 13 years use the default `rows`
  completeness filter so the comparison is consistent without re-downloading archived raw
  data for 2016–2018 and 2020–2023. The paper-faithful `COMPLETENESS_MODE=runs` filter
  (plus `TIS_MIN_SERIES=180`) is implemented and was evaluated on 2011 (Section 1); applying
  it to every year would require re-downloading ~16 GB of raw data and re-processing, and it
  changes the metrics by only ~0.2–0.5 pp.
- **Different months per year.** 2011 = March, 2012 = April, 2013+ = September, so level
  comparisons across years are approximate.
- **Evolving data program.** Website sets, M-Lab server placement, sampling schedules, and
  raw→validated processing all changed between years. Cross-year differences reflect a mix of
  network changes and measurement-program changes.

## 3. TIS method validation (2011 + 2019)

`src/10_validate_tis.py` checks whether the tight-initial-segment (TIS) detector measures real
shared congestion rather than chance or the daily load cycle. It runs the full alignment +
TIS pipeline on two contrasting years — 2011 (paper-era, method fires) and 2019 (post-break,
method silent). Outputs in `output/validate/validate_{year}.json` and `sensitivity_{year}.csv`.

### Design

- **Permutation null.** For each (unit, site), shuffle the throughput↔load-time pairing within
  the (unit, site) pair (200 permutations on a 400-unit subsample, capped per unit), re-running
  the full site-level correlation + ≥5-of-10 detection on each permuted dataset. The null is
  "chance correlation given identical marginal distributions."
- **Hour-of-day control.** Re-run the same detection with partial correlations after removing
  the shared hour-of-day pattern (load and throughput are both strongly diurnal).
- **Sensitivity scan.** TIS% over r-thresholds 0.5/0.6/0.7 × count-thresholds 3–6 × minimum
  series length 30/90/180.
- **Peak vs. off-peak.** Mean site-correlation during weekday 19:00–23:00 vs. the rest of the
  week. If peak congestion drove the correlations, peak r should exceed off-peak r.

### Results (2011)

| Diagnostic | Value |
|---|---|
| Observed TIS% | 1.83% (93 of 5,093 units), mean high-corr count 0.20 |
| Free-shuffle null TIS% | 0.00% (mean count 0.00) — null never reaches observed |
| Dataset p (null ≥ observed) | 0.0 |
| Hour-of-day partial-correlation TIS% | 0.35% (18 units) |
| Mean r peak vs. off-peak | 0.070 vs. 0.131 (fraction peak > off-peak: 0.35) |
| Cross-ISP corr(RC%, TIS%) | 0.77 (all); −0.17 (excluding Cablevision outlier) |

### Results (2019)

| Diagnostic | Value |
|---|---|
| Observed TIS% | 0.00% (0 units), mean high-corr count 0.06 |
| Free-shuffle null TIS% | 0.00% (mean count 0.001) |
| Dataset p | 1.0 |

### Interpretation

1. **The method is not noise.** In 2011 the chance null never produces a TIS detection while
   the real data produces 93. The correlations sit on real structure.
2. **But ~80% of that structure is the diurnal cycle.** Controlling for hour-of-day drops TIS
   from 1.83% to 0.35% (93 → 18 units). Most "tight initial segment" detections are units whose
   benchmark sites slow in lockstep with daily load — a shared-time artifact, not shared
   congestion.
3. **The diurnal-robust signal is real, small, and DSL-concentrated.** The 18 surviving units
   are 17 DSL + 1 cable; ~47% are also RC (vs. a 5.4% DSL baseline → ~9× enrichment). This is
   the strongest evidence the paper's *qualitative* claim (DSL recurrent congestion is more
   initial-segment than cable's) survives scrutiny — as a small, hour-adjusted DSL effect.
4. **Peak hours do not explain the correlations** — mean r is *higher* off-peak. The expected
   "peak-usage → shared bottleneck" signature is absent.
5. **Sensitivity is continuous** (TIS% rises smoothly as thresholds loosen; max ~6% at
   r>0.5/≥3/30), supporting the paper's graded-treatment claim, but the whole surface is low —
   the detector is conservative regardless of thresholds.
6. **ISP structure reproduces the paper's Fig 5.** One cable outlier (Cablevision: 74% RC /
   26% TIS — the analog of the paper's "ISP 3/10") drives the positive cross-ISP RC–TIS
   correlation; without it there is no correlation (r = −0.17). High-RC cable ISPs (Cox 46%,
   Comcast 15%, TimeWarner 16%) have TIS ≈ 0 — their congestion lives beyond the initial
   segment, exactly as the paper found.
7. **By 2019 the method is blind.** Observed mean high-corr count (0.06) is ~60× the null
   (0.001) — faint residual structure remains — but far below any threshold, so TIS = 0 with
   p = 1.0. This is a measurement-program property (website-set change; see §2 finding 3), not
   proof initial-segment congestion vanished.

**Bottom line:** the TIS method measures real structure, but its headline rates are inflated
~5× by the daily load cycle. Use it as a DSL-oriented, hour-adjusted secondary lens, only on
2011–2016-era data, and do not read its post-2017 zeros as an absence of congestion.

## 4. Raw-unit extension (2011–2022) and raw-vs-validated comparison

Sections 1–3 analyzed the **validated** FCC MBA tarballs (the pre-filtered fleet published by
FCC/SamKnows). Because the validated fleet shrinks over time (5,095 → 1,769 units) and is a
selection of the full measurement population, we re-ran the full pipeline on the **raw bulk**
tarballs for every year that has one (2011–2022; the Sept-2022 collection used for 2023 was
never published raw, so 2023 stays validated-only). Raw ingest is `src/01b_load_raw.py`
(download/extract/ingest to `tcp.parquet`/`web.parquet`), metadata attach is
`src/02_raw_meta.py` (validated profile; `unknown` where no profile exists), and the rest of
the pipeline (`03`–`08`) is shared.

### Raw ingest notes

- **Concurrent sequences.** The raw bulk carries ~6 concurrent benchmark sequences per
  (unit, dtime) plus failed tests (`successes == 0`). Ingest keeps `successes > 0` and
  median-aggregates throughput per (unit, dtime), matching the validated pipeline. Without
  this, the daily-max speed-tier is inflated by PowerBoost bursts and RC% runs ~4× too high
  (cable 82% vs. paper's 27–32%).
- **Schema drift.** 2011 = 12-col `#`-commented header; 2012–2016 = date-suffixed names
  (`curr_httpgetmt_2012_04.csv`) with no header; 2017+ = 15-col plain header. `01b_load_raw.py`
  locates members by basename prefix (skipping the `curr_httpgetmt6_*.csv` 6-stream variant
  present from 2015) and dedupes the repeated header rows that appear mid-file in some years.
- **Full years:** 2011–2022 (12 years), one raw collection month per analysis year
  (Mar-2011, Apr-2012, Sep-2013…Sep-2021).

### Raw vs. validated, overall

`output/compare_raw_validated/` (tables + figures) compares the two on the shared cable/DSL/
fiber subset so the fleet definitions align.

| Year | Raw N | Validated N | Raw RC% | Validated RC% | Raw TIS% | Validated TIS% |
|---|---|---|---|---|---|---|
| 2011 | 5,074 | 5,074 | 17.0 | 17.0 | 2.5 | 2.5 |
| 2012 | 5,692 | 5,733 | 9.0 | 7.2 | 1.0 | 1.0 |
| 2013 | 5,924 | 6,139 | 9.3 | 7.5 | 0.9 | 0.8 |
| 2014 | 3,284 | 5,246 | 5.6 | 5.5 | 0.5 | 0.4 |
| 2015 | 4,397 | 4,758 | 7.3 | 7.3 | 0.6 | 0.7 |
| 2016 | 3,947 | 3,936 | 11.1 | 5.9 | 1.1 | 1.5 |
| 2017 | 3,952 | 3,627 | 7.1 | 6.3 | 1.4 | 1.0 |
| 2018 | 3,603 | 3,646 | 9.1 | 8.3 | 0.0 | 0.0 |
| 2019 | 2,335 | 2,773 | 8.3 | 5.2 | 0.0 | 0.0 |
| 2020 | 2,592 | 2,618 | 8.0 | 6.2 | 0.0 | 0.0 |
| 2021 | 3,217 | 3,228 | 6.4 | 4.1 | 0.0 | 0.0 |
| 2022 | 3,102 | 3,037 | 10.0 | 5.1 | 0.0 | 0.0 |

(Full per-technology rows in `tables/comparison_by_tech_raw_valid.csv`.)

### Findings

1. **2011 agrees exactly** (both fleets → identical 5,074 units and 17.0% RC). The raw and
   validated March-2011 populations coincide, so the two reproduce the same numbers.
2. **The validated fleet understates RC in most later years.** On the raw fleet, RC% runs
   1.5–2× the validated-based figure (2016: 11.1 vs 5.9; 2019: 8.3 vs 5.2; 2022: 10.0 vs 5.1).
   The validated selection tilts toward higher-performing units, so prevalence estimates based
   on it are a lower bound.
3. **The overall story is unchanged.** Raw RC% still collapses from ~17% (2011) to mid-single
   digits, cable still leads DSL in 2011 only, and TIS still falls to ~0 by 2018 (a measurement-
   program artifact — see §2 finding 3). The raw data makes congestion look *somewhat worse* in
   the 2010s, not structurally different.
4. **TIS raw ≈ TIS validated** everywhere (both → 0 after 2017), so the TIS conclusions in §2–§3
   are robust to the raw-vs-validated choice.
5. **2023 stays validated-only** because no raw tarball exists for the Sept-2022 collection;
   treat its 4.6% RC (validated fleet) as consistent with the other later years.

### Figures

- `compare_raw_valid_RC_overall.png` / `TIS_overall.png` — raw vs validated prevalence trend.
- `compare_raw_valid_RC_by_tech.png` / `TIS_by_tech.png` — per technology (cable/DSL/fiber).
- `compare_raw_valid_RC_isp_scatter.png` / `TIS_isp_scatter.png` — ISP-year raw vs validated
  with y=x line and Pearson r.

### Validation figures and tables

Generated by `src/11_plot_validation.py` from the `10_validate_tis.py` artifacts into
`output/validate/`:

- `figures/01_null_vs_observed.png` — permutation-null distribution vs. observed mean
  high-correlation count (2011, 2019); the "not noise" result.
- `figures/02_hour_adjust.png` — raw vs. hour-of-day-adjusted TIS detection counts; the ~80%
  diurnal-cycle artifact.
- `figures/03_peak_vs_offpeak.png` — paired site-correlation strength at peak vs. off-peak;
  peak hours do not drive the correlations.
- `figures/04_sensitivity_heatmap.png` — TIS% over the (r-threshold, count-threshold) surface
  (min series = 30); continuous, conservative response.
- `figures/05_rc_association.png` — RC share among hour-robust TIS units vs. baseline (DSL
  ~9× enrichment) and the RC∩TIS consistency anchors.
- `figures/06_isp_scatter.png` — 2011 ISP-level TIS% vs. RC% (paper Fig 5 analog); the
  Cablevision outlier carries the correlation (r = 0.77 all ISPs, −0.17 without).
- `validation_summary.csv` — headline metrics for both years in one table.
