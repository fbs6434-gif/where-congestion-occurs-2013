import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from config import YEAR

BASE = "data/processed/2011_{month}"
MONTHS = {"March": "march", "April": "april", "May": "may", "June": "june"}
OUTDIR = "output/paper"
os.makedirs(os.path.join(OUTDIR, "tables"), exist_ok=True)
os.makedirs(os.path.join(OUTDIR, "figures"), exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif", "Times New Roman"],
    "font.size": 11,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.facecolor": "white",
})

MONTH_COLORS = {"March": "#0050EF", "April": "#00CFFF", "May": "#EFEF00", "June": "#00B050"}
MONTH_MARKERS = {"March": "D", "April": "o", "May": "^", "June": "s"}

def load_all():
    frames = []
    for month_label, month_key in MONTHS.items():
        meta = pd.read_parquet(os.path.join(BASE.format(month=month_key), "meta_valid.parquet"))
        rc = pd.read_parquet(os.path.join(BASE.format(month=month_key), "rc.parquet"))
        tis = pd.read_parquet(os.path.join(BASE.format(month=month_key), "tis.parquet"))
        df = rc.merge(tis, on=["unit_id", "month"]).merge(
            meta[["unit_id", "isp", "technology"]], on="unit_id"
        )
        df["month_label"] = month_label
        frames.append(df)
    return pd.concat(frames, ignore_index=True)

def table(df, tech):
    rows = []
    for month_label in MONTHS:
        sub = df[(df["month_label"] == month_label) & (df["technology"] == tech)]
        N = len(sub)
        N_rc = sub["rc"].sum()
        N_tis = sub["tis"].sum()
        N_both = (sub["rc"] & sub["tis"]).sum()
        rows.append({
            "Month": month_label, "Total": N,
            "FC": N_rc, "PTIS": N_tis, "FC∩PTIS": N_both,
            "FC∩PTIS/PTIS": f"{N_both/N_tis*100:.0f}%" if N_tis else "0%",
            "FC∩PTIS/FC": f"{N_both/N_rc*100:.0f}%" if N_rc else "0%",
            "FC%": f"{N_rc/N*100:.0f}%", "PTIS%": f"{N_tis/N*100:.0f}%",
        })
    tbl = pd.DataFrame(rows)
    tbl.to_csv(os.path.join(OUTDIR, "tables", f"paper_table_{tech}.csv"), index=False)
    print(tbl.to_string(index=False))
    print()
    return tbl

def isp_summary(df, tech, month_label=None):
    sub = df[df["technology"] == tech]
    if month_label:
        sub = sub[sub["month_label"] == month_label]
    return sub.groupby("isp").agg(
        N=("unit_id", "count"), RC=("rc", "sum"), TIS=("tis", "sum"),
    ).reset_index()

def plot_prevalence(df, tech, metric, fname, ylabel):
    isps = sorted(df[df["technology"] == tech]["isp"].unique())
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for month_label in MONTHS:
        summary = isp_summary(df, tech, month_label)
        m = dict(zip(summary["isp"], summary[metric] / summary["N"] * 100))
        vals = [m.get(isp, np.nan) for isp in isps]
        ax.plot(range(len(isps)), vals, marker=MONTH_MARKERS[month_label],
                color=MONTH_COLORS[month_label], linestyle="none", ms=7,
                label=month_label, zorder=5)
    ax.set_xticks(range(len(isps)))
    ax.set_xticklabels(isps, rotation=45, ha="right", fontsize=9)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("ISP")
    all_vals = []
    for month_label in MONTHS:
        summary = isp_summary(df, tech, month_label)
        mm = dict(zip(summary["isp"], summary[metric] / summary["N"] * 100))
        all_vals.extend([mm.get(i, np.nan) for i in isps])
    ax.set_ylim(0, max(20, np.nanmax(all_vals) * 1.15))
    ax.yaxis.set_major_formatter(mticker.PercentFormatter())
    ax.legend(frameon=True, loc="upper right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTDIR, "figures", fname))
    plt.close()
    print(f"Saved {fname}")

def plot_scatter_april(df):
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    for tech, color in [("dsl", "#0050EF"), ("cable", "#EF0000")]:
        summary = isp_summary(df, tech, "April")
        rc = summary["RC"] / summary["N"] * 100
        tis = summary["TIS"] / summary["N"] * 100
        ax.scatter(tis, rc, c=color, s=90, edgecolors="black", linewidths=0.5, zorder=5)
        for _, row in summary.iterrows():
            ax.annotate(row["isp"], (row["TIS"]/row["N"]*100, row["RC"]/row["N"]*100),
                        xytext=(5, 5), textcoords="offset points", fontsize=8, color=color)
    ax.set_xlabel("TIS prevalence (%)")
    ax.set_ylabel("RC prevalence (%)")
    ax.set_title(f"{YEAR} April — TIS vs RC prevalence by ISP")
    ax.grid(alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTDIR, "figures", "fig5_scatter_april.png"))
    plt.close()
    print("Saved fig5_scatter_april.png")

def main():
    df = load_all()
    print(f"Total unit-months: {len(df)}")
    print("\n=== TABLE I: CABLE DATA ===")
    table(df, "cable")
    print("=== TABLE II: DSL DATA ===")
    table(df, "dsl")

    print("\n=== FIG 3: TIS cable ===")
    plot_prevalence(df, "cable", "TIS", "fig3_TIS_cable.png", "TIS prevalence")
    print("\n=== FIG 4: TIS dsl ===")
    plot_prevalence(df, "dsl", "TIS", "fig4_TIS_dsl.png", "TIS prevalence")
    print("\n=== FIG 6: RC cable ===")
    plot_prevalence(df, "cable", "RC", "fig6_RC_cable.png", "RC prevalence")
    print("\n=== FIG 7: RC dsl ===")
    plot_prevalence(df, "dsl", "RC", "fig7_RC_dsl.png", "RC prevalence")
    print("\n=== FIG 5: April scatter ===")
    plot_scatter_april(df)

if __name__ == "__main__":
    main()
