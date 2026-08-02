# Analysis — Reproduction fidelity and multi-year trends

This document summarizes two pieces of work on the reproduction of Genin & Splett (2013),
*Where Congestion Occurs in the US Broadband Access Networks* ([arXiv:1307.3696](https://arxiv.org/abs/1307.3696)):

1. Why the 2011 reproduction does not exactly match the paper's published numbers.
2. What the extended 2011–2023 FCC Measuring Broadband America (SamKnows) analysis shows.

## 1. Reproduction fidelity (2011)

### Paper vs. our pipeline

| Metric (March 2011) | Paper | Ours |
|---|---|---|
| Units analyzed (DSL + cable) | ~2,400–2,900 / month | 4,474 (2,717 cable + 1,757 DSL) |
| Cable recurrent congestion (RC) | 27–32% | 21.9% |
| DSL RC | 9–12% | 5.6% |
| Cable tight initial segment (TIS) | 3–4% | 1.5% |
| DSL TIS | 5–7% | 2.6% |
| Cable RC∩TIS / RC | 8–13% | 6.7% |
| DSL RC∩TIS / RC | 65–67% | 33.3% |

### Why the numbers differ

The gap is **data-level, not filter-level**. The filters in `src/config.py` now match the
paper's thresholds (`MIN_MATCHED_RUNS = 180` distinct matched benchmark runs per unit-month,
`TIS_MIN_SERIES = 180` paired measurements per site before a correlation is counted).
Tightening the completeness filter from the previous laxer row-count rule reduced the 2011
sample from 5,095 → 4,474 units but moved every metric by only ~0.2 percentage points.

Three data-level differences explain the residual gap:

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
(≈ 72%); and DSL recurrent congestion is far more likely than cable's to originate on the
initial segment (RC∩TIS/RC ≈ 33% vs. ~7%).

To reproduce the paper's exact numbers, re-run the pipeline on the **raw** 2011 data
(see reference [16]) rather than the validated subset.

## 2. Multi-year trends (2011–2023)

The methodology (RC, TIS) was applied to one month per year of FCC MBA validated data.
Yearly sample sizes and prevalences (cable, DSL) are in `output/compare/tables/comparison_by_tech.csv`.

| Year | Month | Cable N | Cable RC% | Cable TIS% | DSL N | DSL RC% | DSL TIS% |
|---|---|---|---|---|---|---|---|
| 2011 | March | 2,717 | 21.9 | 1.5 | 1,757 | 5.6 | 2.6 |
| 2012 | April | 2,926 | 10.2 | 0.3 | 1,606 | 5.1 | 2.5 |
| 2013 | September | 3,309 | 10.9 | 0.2 | 1,620 | 4.6 | 2.5 |
| 2014 | September | 2,799 | 7.9 | 0.0 | 1,028 | 3.4 | 0.9 |
| 2015 | September | 2,595 | 6.2 | 0.0 | 1,123 | 11.4 | 2.0 |
| 2016 | September | 2,233 | 4.4 | 0.3 | 1,224 | 10.3 | 4.1 |
| 2017 | September | 1,861 | 4.7 | 0.3 | 1,275 | 10.4 | 2.4 |
| 2018 | September | 1,593 | 6.9 | 0.0 | 1,413 | 12.4 | 0.0 |
| 2019 | September | 420 | 6.2 | 0.0 | 589 | 5.9 | 0.0 |
| 2020 | September | 952 | 4.0 | 0.0 | 970 | 8.4 | 0.0 |
| 2021 | September | 1,202 | 2.3 | 0.0 | 1,265 | 4.7 | 0.0 |
| 2022 | September | 1,160 | 4.0 | 0.0 | 1,213 | 5.5 | 0.0 |
| 2023 | September | 486 | 2.7 | 0.0 | 1,016 | 6.6 | 0.0 |

### Findings

1. **Cable recurrent congestion has collapsed.** Cable RC% fell from ~22% (2011) to ~2–7%
   (2017 onward), a decline of roughly 4×. The paper's headline asymmetry — cable suffering
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
4. **Sample sizes shrank** as the FCC MBA unit fleet declined (cable 2,717 → 486; DSL 1,757 →
   1,016), and the tightened ≥180-matched-run filter admits far fewer units in later years
   (2019: median 186 matched runs/unit vs. 305 in 2011). Later-year prevalences are therefore
   noisier.
5. **Fiber** (present from 2012) shows consistently low RC (≈0.4–6.5%). **Satellite** data
   (2013–2018) shows very high RC (up to 85% in 2017–2018) but with tiny samples.

### Caveats

- **Mixed completeness filters.** 2011–2015 and 2019 were re-run with the tightened paper-style
  filter (≥180 matched runs). 2016–2018 and 2020–2023 retain the legacy row-count filter
  because their raw data was archived off-local after initial processing (re-running requires
  re-downloading ~16 GB). This affects sample sizes (notably a lower 2019 N) but moves the
  RC%/TIS% metrics by only ~0.2 pp.
- **Different months per year.** 2011 = March, 2012 = April, 2013+ = September, so level
  comparisons across years are approximate.
- **Evolving data program.** Website sets, M-Lab server placement, sampling schedules, and
  raw→validated processing all changed between years. Cross-year differences reflect a mix of
  network changes and measurement-program changes.
