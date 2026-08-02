# 13-Year Trends: Where Congestion Occurs, 2011–2023

Digestible version of the extended analysis. Method: the RC (recurrent congestion) and TIS
(tight initial segment) definitions from Genin & Splett (2013) applied to one month per year of
FCC Measuring Broadband America (SamKnows) data, uniformly with the `rows` completeness filter.
Full numbers in `ANALYSIS.md` §2 and `output/compare/tables/comparison_by_tech.csv`; figures in
`output/compare/figures/` (`compare_overall_trend.png`, `compare_RC_by_tech.png`, ...).

## TL;DR

- **Cable congestion collapsed, and the improvement is real.** Cable RC fell from **21% (2011)
  to ~2–7%** while advertised tiers rose ~7× (median ~17 → ~120 Mbps). Getting a 7× faster tier
  *and* cutting congestion means the gains are genuine, not a re-baselining artifact.
- **DSL is the persistent problem child.** DSL RC hovered ~3–8% and actually **bumped to
  10–12% in 2015–2018** (Frontier, AT&T, Windstream, Qwest all spiked). Copper economics: you
  cannot cheaply upgrade last-mile copper, so it never got fixed the way cable was.
- **Fiber is clean** (RC ≤ ~6.5%, mostly ≤ 2%).
- **The post-2017 TIS = 0 is an artifact, not a miracle.** The FCC changed the measurement
  websites; the TIS detector stopped firing because it is calibrated to the 2011 test design.
- **2011's scary cable numbers were a two-ISP story** (Cablevision 74% RC, Cox 46%). By 2012
  the industry had mostly normalized.

## The numbers

| | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Cable RC% | 21.2 | 10.0 | 10.7 | 7.5 | 6.4 | 4.4 | 4.7 | 6.9 | 6.3 | 4.0 | 2.3 | 4.0 | 2.7 |
| DSL RC% | 5.4 | 4.9 | 4.2 | 3.5 | **12.1** | **10.3** | **10.4** | **12.4** | 6.0 | 8.4 | 4.7 | 5.5 | 6.6 |
| Fiber RC% | – | 0.4 | 0.4 | 0.6 | 1.5 | 2.1 | 1.2 | 3.0 | 1.5 | 6.2 | 5.9 | 6.5 | 0.7 |
| Cable TIS% | 1.4 | 0.3 | 0.2 | 0.0 | 0.0 | 0.3 | 0.3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| DSL TIS% | 2.4 | 2.5 | 2.4 | 1.2 | 2.3 | 4.1 | 2.4 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

## What's real

### 1. Cable: a structural, industry-wide fix
Every major cable ISP improved — this is not one operator cleaning up:

| Cable ISP | 2011 | 2012 | 2013 | 2014 | 2015 | 2019 |
|---|---|---|---|---|---|---|
| Cablevision | 74.1 | 5.0 | 6.9 | 0.7 | 2.0 | – |
| Cox | 46.4 | 31.2 | 29.0 | 20.1 | 13.9 | 8.4 |
| Mediacom | 21.5 | 6.4 | 12.7 | 17.3 | 18.9 | 2.9 |
| Comcast | 15.2 | 5.0 | 3.7 | 2.8 | 4.9 | 6.8 |
| Charter | 14.2 | 8.1 | 7.0 | 7.5 | 2.8 | 6.4 |
| TimeWarner | 16.4 | 6.3 | 8.2 | – | 6.2 | – |

Capacity investment + tier upgrades explain it. Median cable tier rose **16.8 → 119.7 Mbps
(~7×)**; the *severity* of what congestion remains is unchanged (congested units still spend
~28–34% of measurements under 80% of their tier). Prevalence fell; the failure mode didn't.

### 2. DSL: stuck, and spiking mid-decade
The 2015–2018 bump to 10–12% is a wave of spiking DSL ISPs, not noise:

| DSL ISP | 2011 | 2012 | 2013 | 2014 | 2015 | 2019 |
|---|---|---|---|---|---|---|
| Windstream | 5.0 | 14.4 | 16.8 | 9.3 | 18.6 | 3.3 |
| Frontier | 14.5 | 6.5 | 4.0 | 5.9 | 19.4 | 6.3 |
| AT&T | 4.8 | 2.9 | 0.9 | 2.9 | 10.1 | – |
| Qwest | 4.9 | 2.2 | 2.8 | 1.1 | 8.7 | – |

DSL tiers rose only ~3.7× (3.0 → 11.2 Mbps) vs cable's 7×. The DSL fleet also churns out of
the sample (Verizon DSL gone by 2015, AT&T DSL by 2019). DSL — not cable — is the high-RC
technology in most years after 2015. This matches the paper's spirit turned upside down: the
last-mile limitation the paper flagged for DSL is the one that never got cheaper to fix.

### 3. The 2011 snapshot was extreme
2011's cable RC (21%) is dominated by Cablevision (74%) and Cox (46%). Remove those two and
2011 cable looks like 2012+. Treat the 2011 headline as "two cable ISPs were failing badly,"
not "cable was failing industry-wide."

## What's artifact

- **TIS ≈ 0 after 2017 (all technologies).** The FCC switched test sites to imdb/bing/bbc/
  apple/cnn/ebay/google (youtube/facebook/wikipedia/yahoo/netflix gone); benchmark↔site
  correlations collapsed (mean high-corr count 0.20 → 0.06 per unit) and no unit reaches the
  ≥5 threshold. The detector is calibrated to the 2011-era design. Do not read the zeros as
  "initial-segment congestion vanished."
- **Satellite RC (up to 85% in 2017–2018)** is tiny-sample noise, not a finding.
- **Fiber RC drifting up in 2019–2022 (1.5 → 6.5%)** is more likely tier re-baselining (faster
  tiers are harder to sustain) than worse service.

## Is the TIS method trustworthy? (validated on 2011 + 2019)

Validation (permutation null, hour-of-day control, sensitivity scan; `src/10_validate_tis.py`,
`output/validate/`):

1. **Not noise.** A chance-level (free-shuffle) null never produces TIS detections (0.0% vs
   observed 1.83% in 2011; dataset p = 0.0). The method sits on real structure.
2. **But ~80% of detections are the daily load cycle.** Controlling for hour-of-day drops 2011
   TIS from 1.83% → 0.35% (93 → 18 units). Most "tight initial segment" flags are units whose
   sites all slow at peak together — a diurnal artifact.
3. **The diurnal-robust signal is real, small, and DSL-flavored.** The 18 surviving units are
   17 DSL + 1 cable, and ~47% of them are also RC (vs a 5.4% DSL baseline — ~9× enrichment).
   This supports the paper's core claim that *DSL* recurrent congestion is more initial-segment.
4. **Peak hours don't explain the correlations.** Mean pairwise site correlation is *higher*
   off-peak (r = 0.131) than peak (r = 0.070); only 35% of (unit, site) pairs have peak > off-peak.
5. **ISP structure reproduces the paper's Fig 5.** One cable outlier (Cablevision: 74% RC /
   26% TIS — the analog of the paper's "ISP 3/10") drives the RC–TIS cross-ISP correlation
   (r = 0.77 with it, −0.17 without). High-RC cable ISPs (Cox, Comcast, TWC, Mediacom) have
   TIS ≈ 0: their congestion lives beyond the initial segment.
6. **In 2019 the method is blind.** Observed mean high-corr count 0.06 vs null 0.001 — residual
   structure is ~60× chance but far below any threshold; TIS = 0, p = 1.0.

**Bottom line:** use TIS as a DSL-oriented, hour-adjusted secondary lens, and only on
2011–2016-era data. Its headline rates are inflated ~5× by the diurnal cycle, and its post-2017
zeros are a measurement-program artifact.

## What to make of it

1. Broadband congestion was a 2011 cable + persistent DSL story; today it is almost entirely
   a DSL/copper story.
2. Capacity investment worked — cable raised tiers 7× and cut RC by ~7×. The market/policy
   lesson: the technologies that got upgraded got fixed.
3. The paper's TIS asymmetry (DSL more initial-segment congestion) survives scrutiny only as a
   small, hour-adjusted DSL signal; the paper's raw TIS rates are partly diurnal-cycle artifact.
4. Compare levels across years cautiously: months vary (Mar 2011, Apr 2012, Sep 2013+), the
   validated fleet shrank (5,095 → 1,769 units), and the measurement program changed
   (websites, schedules, processing). See `ANALYSIS.md` §2 caveats.
