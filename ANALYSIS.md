# Analysis — Reproduction fidelity and multi-year trends

This document summarizes two pieces of work on the reproduction of Genin & Splett (2013),
*Where Congestion Occurs in the US Broadband Access Networks* ([arXiv:1307.3696](https://arxiv.org/abs/1307.3696)):

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
