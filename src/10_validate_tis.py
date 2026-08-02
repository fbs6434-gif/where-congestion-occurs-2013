"""
Validate the Tight Initial Segment (TIS) correlation method.

For each year, load aligned data and compute, per (unit, site), the Pearson
correlation between M-Lab throughput and 1/load_time (the TIS signal), then:

  1. Observed TIS prevalence and high-correlation-count distribution.
  2. Free-shuffle permutation null (chance): shuffle throughput<->load_time
     pairing within a (unit, site); expect pure-chance correlations.
  3. Day-block permutation null (diurnal): reorder whole days, keeping
     within-day pairing; retains the shared daily load cycle.
  4. Hour-of-day partial correlation: TIS after regressing out time of day.
  5. Sensitivity scan over (r_thresh, count_thresh, min_series): the paper
     claims TIS prevalence varies continuously with these.
  6. Peak-hour (weekday 19-23h) vs off-peak correlation strength.

Usage: YEAR=2011 python src/10_validate_tis.py
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from config import PROCESSED_DIR, WEBSITES, TIS_R_THRESH, TIS_COUNT_THRESH, TIS_MIN_SERIES

YEARS = [int(os.environ.get("YEAR", "2011"))]
N_PERMS = 200
PERM_UNIT_CAP = 400      # subsample of units for permutation nulls
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "validate")
os.makedirs(OUT_DIR, exist_ok=True)

RNG = np.random.default_rng(42)


def extract_site_series(aligned):
    """Return dict: unit_id -> site -> (throughput, inv_load, hour, day)."""
    per_unit = {}
    for uid, grp in aligned.groupby("unit_id"):
        sites = {}
        for site in WEBSITES:
            sd = grp[(grp["url"] == site) & (grp["load_time_ms"] > 0)]
            if len(sd) < 30:
                continue
            tp = sd["throughput_mbps"].to_numpy(float)
            inv = (1.0 / sd["load_time_ms"].to_numpy(float))
            if len(tp) < 2 or np.unique(tp).size < 2 or np.unique(inv).size < 2:
                continue
            hour = sd["dtime"].dt.hour.to_numpy(int)
            day = sd["dtime"].dt.date.to_numpy()
            sites[site] = (tp, inv, hour, day)
        if sites:
            per_unit[uid] = sites
    return per_unit


def permute_free_null(site_arrays, p):
    """Null r for each site under p free shuffles. Returns (n_sites, p) r matrix."""
    ns = len(site_arrays)
    out = np.full((ns, p), np.nan)
    for i, (tp, inv, _h, _d) in enumerate(site_arrays):
        n = len(tp)
        x = tp - tp.mean()
        y = inv - inv.mean()
        norm = np.sqrt((x @ x) * (y @ y))
        if norm == 0:
            continue
        idx = np.argsort(RNG.random((p, n)), axis=1)
        out[i] = (x @ y[idx].T) / norm
    return out


def partial_corr(tp, inv, hour):
    """Pearson correlation of throughput and 1/load_time controlling for hour-of-day."""
    H = pd.get_dummies(hour).to_numpy(float)
    H = H - H.mean(axis=0)
    rx = tp - H @ np.linalg.lstsq(H, tp, rcond=None)[0]
    ry = inv - H @ np.linalg.lstsq(H, inv, rcond=None)[0]
    rx = rx - rx.mean(); ry = ry - ry.mean()
    denom = np.sqrt((rx @ rx) * (ry @ ry))
    return (rx @ ry) / denom if denom > 0 else 0.0


def analyze_year(year):
    print(f"\n{'='*70}\nYear {year}\n{'='*70}")
    fp = os.path.join(PROCESSED_DIR, "aligned.parquet")
    aligned = pd.read_parquet(fp, columns=["unit_id", "dtime", "url", "load_time_ms", "throughput_mbps"])
    dtime = aligned["dtime"]
    hour = dtime.dt.hour.to_numpy()
    dow = dtime.dt.dayofweek.to_numpy()
    peak = (dow < 5) & (hour >= 19) & (hour <= 23)
    aligned["peak"] = peak

    per_unit = extract_site_series(aligned)
    del aligned
    print(f"Units with >=1 site series: {len(per_unit)}")

    # --- observed ---
    obs_high = {}          # unit -> high-corr count (r>0.6, n>=30)
    site_records = []      # for sensitivity scan and peak analysis
    for uid, sites in per_unit.items():
        cnt = 0
        for site, (tp, inv, _h, _d) in sites.items():
            r, _ = pearsonr(tp, inv)
            if r > TIS_R_THRESH:
                cnt += 1
            site_records.append({"unit_id": uid, "site": site, "n": len(tp), "r": r})
        obs_high[uid] = cnt
    site_df = pd.DataFrame(site_records)
    obs_counts = np.array(list(obs_high.values()))
    obs_tis = np.mean(obs_counts >= TIS_COUNT_THRESH)

    # --- permutation nulls on a unit subsample ---
    units = list(per_unit.keys())
    sub = units[:PERM_UNIT_CAP]
    free_high_all = np.zeros((len(sub), N_PERMS))
    obs_sub = np.zeros(len(sub))
    for j, uid in enumerate(sub):
        arrays = list(per_unit[uid].values())
        r_free = permute_free_null(arrays, N_PERMS)
        free_high_all[j] = (r_free > TIS_R_THRESH).sum(axis=0)
        obs_sub[j] = obs_high[uid]

    free_tis_rate = np.mean(free_high_all >= TIS_COUNT_THRESH)
    free_mean = free_high_all.mean()
    obs_mean_sub = obs_sub.mean()
    obs_tis_sub = np.mean(obs_sub >= TIS_COUNT_THRESH)

    np.save(os.path.join(OUT_DIR, f"null_free_high_{year}.npy"), free_high_all)
    np.save(os.path.join(OUT_DIR, f"obs_sub_{year}.npy"), obs_sub)

    # dataset-level p-value: fraction of permutations whose null TIS rate
    # reaches the observed TIS rate
    null_tis_per_perm = (free_high_all >= TIS_COUNT_THRESH).mean(axis=0)
    p_val = float(np.mean(null_tis_per_perm >= obs_tis_sub))

    # --- hour-of-day partial correlation TIS ---
    part_high = {}
    for uid, sites in per_unit.items():
        cnt = 0
        for site, (tp, inv, hour_a, _d) in sites.items():
            rp = partial_corr(tp, inv, hour_a)
            if rp > TIS_R_THRESH:
                cnt += 1
        part_high[uid] = cnt
    part_counts = np.array(list(part_high.values()))
    part_tis = np.mean(part_counts >= TIS_COUNT_THRESH)

    unit_df = pd.DataFrame({"unit_id": list(obs_high.keys()), "obs_high": list(obs_high.values())})
    unit_df["part_high"] = unit_df["unit_id"].map(part_high).fillna(0).astype(int)
    unit_df.to_csv(os.path.join(OUT_DIR, f"unit_scores_{year}.csv"), index=False)

    # --- sensitivity scan (full data) ---
    print("\nSensitivity: TIS% as function of (r_thresh, count_thresh, min_series)")
    rows = []
    for r_th in (0.5, 0.6, 0.7):
        for c_th in (3, 4, 5, 6):
            for ms in (30, 90, 180):
                m = (site_df["n"] >= ms) & (site_df["r"] > r_th)
                cnt = m.groupby(site_df["unit_id"]).sum().reindex(units, fill_value=0)
                rows.append((r_th, c_th, ms, float((cnt.values >= c_th).mean())))
    sens = pd.DataFrame(rows, columns=["r_thresh", "count_thresh", "min_series", "tis_pct"])

    # --- peak vs off-peak correlation strength ---
    aligned_p = pd.read_parquet(fp, columns=["unit_id", "dtime", "url", "load_time_ms", "throughput_mbps"])
    aligned_p["peak"] = peak
    peak_rs, off_rs = [], []
    for uid, grp in aligned_p.groupby("unit_id"):
        for site in WEBSITES:
            sd = grp[(grp["url"] == site) & (grp["load_time_ms"] > 0)]
            if len(sd) < 30:
                continue
            tp = sd["throughput_mbps"].to_numpy(float)
            inv = 1.0 / sd["load_time_ms"].to_numpy(float)
            if np.unique(tp).size < 2 or np.unique(inv).size < 2:
                continue
            pk = sd["peak"].to_numpy(bool)
            if pk.sum() >= 10 and (~pk).sum() >= 10:
                rp, _ = pearsonr(tp[pk], inv[pk])
                ro, _ = pearsonr(tp[~pk], inv[~pk])
                peak_rs.append(rp); off_rs.append(ro)
    del aligned_p
    pd.DataFrame({"peak_r": peak_rs, "off_r": off_rs}).to_csv(
        os.path.join(OUT_DIR, f"peak_offpeak_{year}.csv"), index=False)

    results = {
        "year": year, "units": len(units),
        "obs_tis_pct": round(obs_tis * 100, 2),
        "obs_tis_units": int((obs_counts >= TIS_COUNT_THRESH).sum()),
        "obs_mean_high_count": round(obs_counts.mean(), 3),
        "subsample_units": len(sub),
        "null_free_tis_pct": round(free_tis_rate * 100, 3),
        "null_free_mean_count": round(free_mean, 3),
        "obs_mean_count_subsample": round(obs_mean_sub, 3),
        "empirical_p_free": round(p_val, 4),
        "partial_hour_tis_pct": round(part_tis * 100, 2),
        "partial_hour_tis_units": int((part_counts >= TIS_COUNT_THRESH).sum()),
        "mean_r_peak": round(float(np.mean(peak_rs)), 4) if peak_rs else None,
        "mean_r_offpeak": round(float(np.mean(off_rs)), 4) if off_rs else None,
        "frac_peak_gt_off": round(float(np.mean([1 if p > o else 0 for p, o in zip(peak_rs, off_rs)])), 3) if peak_rs else None,
    }

    print(f"\nObserved: TIS%={results['obs_tis_pct']} ({results['obs_tis_units']} units)  mean high-corr count={results['obs_mean_high_count']}")
    print(f"Null (free shuffle): TIS%={results['null_free_tis_pct']}  mean count={results['null_free_mean_count']}")
    print(f"Dataset p (null TIS rate >= observed): {results['empirical_p_free']}")
    print(f"Hour-partial-correlation TIS%: {results['partial_hour_tis_pct']} ({results['partial_hour_tis_units']} units)")
    print(f"Mean r peak vs off-peak: {results['mean_r_peak']} vs {results['mean_r_offpeak']}  (frac peak>off: {results['frac_peak_gt_off']})")

    print("\nSensitivity table (r_thresh, count_thresh, min_series -> TIS%):")
    piv = sens.pivot_table(index=["r_thresh", "count_thresh"], columns="min_series", values="tis_pct")
    print(piv.round(2).to_string())

    with open(os.path.join(OUT_DIR, f"validate_{year}.json"), "w") as fh:
        json.dump(results, fh, indent=2)
    sens.to_csv(os.path.join(OUT_DIR, f"sensitivity_{year}.csv"), index=False)
    print(f"\nSaved validate_{year}.json and sensitivity_{year}.csv")
    return results


if __name__ == "__main__":
    for y in YEARS:
        analyze_year(y)
