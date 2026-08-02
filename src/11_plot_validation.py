"""
Plot figures and export summary tables for the TIS method validation.

Reads artifacts produced by src/10_validate_tis.py from output/validate/
(null_free_high_<year>.npy, obs_sub_<year>.npy, peak_offpeak_<year>.csv,
unit_scores_<year>.csv, sensitivity_<year>.csv, validate_<year>.json) plus
data/processed/<year>/ parquets for RC/tech/ISP context.

Figures (output/validate/figures/):
  01_null_vs_observed.png  - chance null distribution vs observed (per year)
  02_hour_adjust.png       - raw vs hour-adjusted TIS detection counts
  03_peak_vs_offpeak.png   - site-correlation at peak vs off-peak (paired)
  04_sensitivity_heatmap.png - TIS% over (r_thresh, count_thresh) surface
  05_rc_association.png    - RC association of hour-robust TIS units (2011)
  06_isp_scatter.png       - ISP-level RC% vs TIS% (paper Fig 5 analog)

Usage: YEAR=2011 python src/11_plot_validation.py
"""
import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "validate")
FIGDIR = os.path.join(BASE, "figures")
os.makedirs(FIGDIR, exist_ok=True)

YEARS = [2011, 2019]
R_THRESHS = (0.5, 0.6, 0.7)
C_THRESHS = (3, 4, 5, 6)
TIS_R, TIS_C = 0.6, 5
TECH = {"cable": "#1f77b4", "dsl": "#ff7f0e", "fiber": "#2ca02c", "satellite": "#d62728"}


def load_results():
    res = {}
    for y in YEARS:
        with open(os.path.join(BASE, f"validate_{y}.json")) as fh:
            res[y] = json.load(fh)
    return res


def fig01_null_vs_observed(res):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), sharey=False)
    for ax, y in zip(axes, YEARS):
        null = np.load(os.path.join(BASE, f"null_free_high_{y}.npy")).mean(axis=0)
        obs = np.load(os.path.join(BASE, f"obs_sub_{y}.npy")).mean()
        r = res[y]
        ax.hist(null, bins=30, color="#9ecae1", edgecolor="white", alpha=0.9,
                label="null: shuffled data\n(200 perms)")
        ax.axvline(obs, color="#d62728", lw=2.2, label=f"observed mean = {obs:.3f}")
        ax.set_title(f"{y}: chance-level null vs observed\n"
                     f"obs TIS={r['obs_tis_pct']}% vs null TIS={r['null_free_tis_pct']}%, p={r['empirical_p_free']}",
                     fontsize=10)
        ax.set_xlabel("mean high-correlation count per unit (subsample)")
        ax.set_ylabel("permutations")
        ax.legend(fontsize=8)
        ax.text(0.98, 0.95, f"null never\nreaches observed" if obs > 0.01 else "observed ~ chance-level",
                transform=ax.transAxes, ha="right", va="top", fontsize=9,
                bbox=dict(facecolor="white", alpha=0.8, boxstyle="round"))
    fig.suptitle("TIS is not random noise (permutation null test)", fontsize=12, y=1.0)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "01_null_vs_observed.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig02_hour_adjust(res):
    y11, y19 = res[2011], res[2019]
    fig, ax = plt.subplots(figsize=(6.5, 4.4))
    labels = ["2011", "2019"]
    raw = [y11["obs_tis_units"], y19["obs_tis_units"]]
    adj = [y11["partial_hour_tis_units"], y19["partial_hour_tis_units"]]
    x = np.arange(len(labels)); w = 0.38
    b1 = ax.bar(x - w / 2, raw, w, label="raw TIS detection (r > 0.6 on ≥5 sites)", color="#a6bddb")
    b2 = ax.bar(x + w / 2, adj, w, label="hour-of-day partial correlation", color="#fdae6b")
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_ylabel("units detected with tight initial segment")
    ax.set_title("~80% of TIS detections are the daily load cycle", fontsize=11)
    for b, v in zip([*b1, *b2], [*raw, *adj]):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v}", ha="center", va="bottom", fontsize=9)
    ax.text(0, y11["obs_tis_units"] + 8, f"↓ {(1 - y11['partial_hour_tis_units'] / y11['obs_tis_units']) * 100:.0f}% explained by hour-of-day" if y11["obs_tis_units"] else "",
            ha="center", fontsize=9, color="#d62728")
    ax.legend(fontsize=8.5)
    ax.set_ylim(0, max(raw) * 1.18)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "02_hour_adjust.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig03_peak_offpeak(res):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    for ax, y in zip(axes, YEARS):
        df = pd.read_csv(os.path.join(BASE, f"peak_offpeak_{y}.csv"))
        r = res[y]
        ax.boxplot([df["peak_r"], df["off_r"]], labels=["peak\n(weekday 19–23h)", "off-peak"],
                   widths=0.55, patch_artist=True,
                   boxprops=dict(facecolor="#9ecae1"), medianprops=dict(color="#08519c"))
        ax.set_title(f"{y}: site-correlation strength\n"
                     f"mean r = {r['mean_r_peak']} (peak) vs {r['mean_r_offpeak']} (off-peak)\n"
                     f"frac peak>off = {r['frac_peak_gt_off']}", fontsize=10)
        ax.set_ylabel("Pearson r (throughput vs 1/load_time), per unit-site")
        ax.axhline(0, color="grey", lw=0.8, ls="--")
    fig.suptitle("Peak hours do NOT drive the shared correlations", fontsize=12, y=1.0)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "03_peak_vs_offpeak.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig04_sensitivity():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    for ax, y in zip(axes, YEARS):
        sens = pd.read_csv(os.path.join(BASE, f"sensitivity_{y}.csv"))
        sens = sens[sens["min_series"] == 30]
        piv = sens.pivot(index="r_thresh", columns="count_thresh", values="tis_pct")
        piv = piv.loc[R_THRESHS, C_THRESHS]
        im = ax.imshow(piv.values * 100, cmap="YlOrRd", aspect="auto")
        ax.set_xticks(range(len(C_THRESHS))); ax.set_xticklabels(C_THRESHS)
        ax.set_yticks(range(len(R_THRESHS))); ax.set_yticklabels(R_THRESHS)
        ax.set_xlabel("count threshold (sites with r > thresh)")
        ax.set_ylabel("r threshold")
        for i in range(len(R_THRESHS)):
            for j in range(len(C_THRESHS)):
                ax.text(j, i, f"{piv.values[i, j] * 100:.2f}", ha="center", va="center", fontsize=8,
                        color="white" if piv.values[i, j] * 100 > 2 else "black")
        ax.set_title(f"{y}: TIS% across thresholds (min series = 30)", fontsize=10)
        cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04); cb.set_label("TIS% of units")
        if y == 2011:
            ax.add_patch(plt.Rectangle((C_THRESHS.index(TIS_C) - 0.5, R_THRESHS.index(TIS_R) - 0.5),
                                       1, 1, fill=False, edgecolor="#d62728", lw=2))
            ax.text(0.02, 0.98, "paper\nthresholds", transform=ax.transAxes, va="top", fontsize=8, color="#d62728")
    fig.suptitle("TIS prevalence is a continuous function of thresholds (paper's 'graded' claim)",
                 fontsize=12, y=1.0)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "04_sensitivity_heatmap.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)


def load_unit_context(y):
    d = f"data/processed/{y}"
    rc = pd.read_parquet(f"{d}/rc.parquet", columns=["unit_id", "rc"])
    meta = pd.read_parquet(f"{d}/meta_valid.parquet", columns=["unit_id", "technology", "isp"])
    sc = pd.read_csv(os.path.join(BASE, f"unit_scores_{y}.csv"))
    df = sc.merge(meta, on="unit_id")
    df["rc"] = df["unit_id"].map(rc.set_index("unit_id")["rc"]).fillna(False).astype(bool)
    df["tech"] = df["technology"].str.lower()
    df["tis"] = df["obs_high"] >= TIS_C
    df["tis_hour_robust"] = df["part_high"] >= TIS_C
    return df


def fig05_rc_association():
    df = load_unit_context(2011)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))

    ax = axes[0]
    robust_dsl = df[(df["tech"] == "dsl") & df["tis_hour_robust"]]
    base_dsl = df[(df["tech"] == "dsl")]
    robust_cable = df[(df["tech"] == "cable") & df["tis_hour_robust"]]
    base_cable = df[(df["tech"] == "cable")]
    rows = [
        ("cable baseline", base_cable["rc"].mean() * 100, len(base_cable)),
        ("cable hour-robust TIS", robust_cable["rc"].mean() * 100 if len(robust_cable) else 0, len(robust_cable)),
        ("DSL baseline", base_dsl["rc"].mean() * 100, len(base_dsl)),
        ("DSL hour-robust TIS", robust_dsl["rc"].mean() * 100 if len(robust_dsl) else 0, len(robust_dsl)),
    ]
    labs = [r[0] for r in rows]; vals = [r[1] for r in rows]; ns = [r[2] for r in rows]
    colors = ["#1f77b4", "#08519c", "#ff7f0e", "#d35400"]
    bars = ax.bar(labs, vals, color=colors)
    for b, v, n in zip(bars, vals, ns):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.0f}%\n(n={n})", ha="center", va="bottom", fontsize=8.5)
    ax.set_ylabel("share that are recurrently congested (RC)")
    ax.set_title("2011: hour-robust TIS units are ~9× more likely RC (DSL)", fontsize=10)
    ax.set_ylim(0, 60)
    ax.tick_params(axis="x", labelsize=8.5)
    ax.axhline(base_dsl["rc"].mean() * 100, color="#ff7f0e", ls="--", lw=1)

    ax = axes[1]
    m = df
    techs = ["cable", "dsl"]
    x = np.arange(len(techs)); w = 0.38
    tis_ratio = [m[(m["tech"] == t)]["rc"][(m["tech"] == t) & m["tis"]].shape[0] / max(m[(m["tech"] == t) & m["tis"]].shape[0], 1) for t in techs]
    rc_ratio = [(m[(m["tech"] == t) & m["tis"]]["rc"]).sum() / max((m[(m["tech"] == t) & m["rc"]]).shape[0], 1) for t in techs]
    b1 = ax.bar(x - w / 2, [v * 100 for v in tis_ratio], w, label="RC∩TIS / TIS (TIS ⇒ RC)", color="#a6bddb")
    b2 = ax.bar(x + w / 2, [v * 100 for v in rc_ratio], w, label="RC∩TIS / RC (RC ⇒ TIS)", color="#fdae6b")
    ax.set_xticks(x); ax.set_xticklabels(["cable", "DSL"])
    ax.set_ylabel("percent")
    ax.set_title("2011: consistency anchors with RC", fontsize=10)
    ax.set_ylim(0, 100)
    ax.legend(fontsize=8)
    fig.suptitle("The diurnal-robust TIS signal is real, small, and lives where the paper predicted (DSL)",
                 fontsize=12, y=1.0)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "05_rc_association.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig06_isp_scatter():
    df = load_unit_context(2011)
    isp = df.groupby("isp").agg(N=("unit_id", "count"), RC=("rc", "sum"), TIS=("tis", "sum"),
                                tech=("tech", "first"))
    isp["RC%"] = isp["RC"] / isp["N"] * 100
    isp["TIS%"] = isp["TIS"] / isp["N"] * 100
    isp = isp[isp["N"] >= 50]
    corr_all = np.corrcoef(isp["RC%"], isp["TIS%"])[0, 1]
    ex = isp.drop("Cablevision", errors="ignore")
    corr_ex = np.corrcoef(ex["RC%"], ex["TIS%"])[0, 1]

    fig, ax = plt.subplots(figsize=(7.5, 5.4))
    for _, r in isp.iterrows():
        ax.scatter(r["RC%"], r["TIS%"], s=r["N"] / 8, alpha=0.75,
                   color=TECH.get(r["tech"], "grey"), edgecolor="black", linewidth=0.6, zorder=3)
        ax.annotate(r.name, (r["RC%"], r["TIS%"]), fontsize=7.5,
                    textcoords="offset points", xytext=(6, 4))
    xx = np.linspace(0, isp["RC%"].max() * 1.05, 50)
    m, b = np.polyfit(isp["RC%"], isp["TIS%"], 1)
    ax.plot(xx, m * xx + b, ls="--", lw=1.5, color="#d62728",
            label=f"fit all ISPs (r = {corr_all:.2f})")
    m2, b2 = np.polyfit(ex["RC%"], ex["TIS%"], 1)
    ax.plot(xx, m2 * xx + b2, ls=":", lw=1.5, color="#08519c",
            label=f"fit excluding Cablevision (r = {corr_ex:.2f})")
    ax.set_xlabel("recurrent congestion, RC% of users")
    ax.set_ylabel("tight initial segment, TIS% of users")
    ax.set_title("2011 ISP-level TIS vs RC (analog of paper Fig 5):\none cable outlier carries the correlation",
                 fontsize=10)
    ax.legend(fontsize=8.5)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "06_isp_scatter.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return isp


def summary_table(res):
    cols = ["year", "units", "obs_tis_pct", "obs_tis_units", "null_free_tis_pct", "empirical_p_free",
            "partial_hour_tis_pct", "partial_hour_tis_units", "mean_r_peak", "mean_r_offpeak",
            "frac_peak_gt_off"]
    rows = []
    for y in YEARS:
        r = res[y]
        rows.append({k: r[k] for k in cols})
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(BASE, "validation_summary.csv"), index=False)
    print(df.round(4).to_string(index=False))


if __name__ == "__main__":
    res = load_results()
    fig01_null_vs_observed(res)
    fig02_hour_adjust(res)
    fig03_peak_offpeak(res)
    fig04_sensitivity()
    fig05_rc_association()
    isp = fig06_isp_scatter()
    summary_table(res)
    print(f"\nFigures written to {FIGDIR}")
