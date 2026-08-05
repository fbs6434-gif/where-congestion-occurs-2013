import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

BASE = "/home/jovyan/work/project"
ALL_YEARS = [2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
RAW_YEARS = [y for y in ALL_YEARS if y != 2023]  # 2023 has no raw tarball
OUTPUT_DIR = os.path.join(BASE, "output", "compare_raw_validated")
os.makedirs(os.path.join(OUTPUT_DIR, "figures"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "tables"), exist_ok=True)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.facecolor": "white",
    "axes.edgecolor": "black",
    "axes.linewidth": 1.2,
    "grid.alpha": 0.3,
})

RAW_COLOR = "#E24A33"
VALID_COLOR = "#348ABD"

MONTH_MAP = {2011: "March", 2012: "April", 2013: "September", 2014: "September",
             2015: "September", 2016: "September", 2017: "September",
             2018: "September", 2019: "September", 2020: "September",
             2021: "September", 2022: "September", 2023: "September"}

# Raw carries extra FCC profile labels that the validated pipeline filtered out
# ('unknown' = no profile, 'remove'/'misc' = legacy profile classes). Keep the
# core technologies that appear in both; 'uverse'/'ipbb' are copper/DSL-class
# labels merged to dsl for apples-to-apples comparison.
TECH_MAP = {"uverse": "dsl", "ipbb": "dsl"}
KEEP_TECH = {"cable", "dsl", "fiber"}

def load(dataset):
    """Load isp_agg.parquet for a dataset ('validated'|'raw') across years."""
    frames = []
    years = RAW_YEARS if dataset == "raw" else ALL_YEARS
    for y in years:
        if dataset == "raw":
            d = os.path.join(BASE, "data", "processed", str(y))
        else:
            d = os.path.join(BASE, "data", "validated_backup", "processed", str(y))
        fp = os.path.join(d, "isp_agg.parquet")
        if os.path.isfile(fp):
            df = pd.read_parquet(fp)
            df["year"] = y
            df["dataset"] = dataset
            frames.append(df)
    combined = pd.concat(frames, ignore_index=True)
    combined["tech_norm"] = combined["technology"].map(TECH_MAP).fillna(combined["technology"])
    combined = combined[combined["tech_norm"].isin(KEEP_TECH)]
    combined["isp_lc"] = combined["isp"].astype(str).str.strip().str.lower()
    return combined


def tech_agg(df):
    """Aggregate to (dataset, year, tech) prevalence."""
    agg = df.groupby(["dataset", "year", "tech_norm"]).agg(
        N=("N", "sum"), RC=("RC", "sum"), TIS=("TIS", "sum")).reset_index()
    agg["RC%"] = agg["RC"] / agg["N"] * 100
    agg["TIS%"] = agg["TIS"] / agg["N"] * 100
    return agg


def overall_agg(df):
    agg = df.groupby(["dataset", "year"]).agg(
        N=("N", "sum"), RC=("RC", "sum"), TIS=("TIS", "sum")).reset_index()
    agg["RC%"] = agg["RC"] / agg["N"] * 100
    agg["TIS%"] = agg["TIS"] / agg["N"] * 100
    return agg


def plot_metric_overall(agg, metric, ylabel, fname, title):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for dataset, c in [("raw", RAW_COLOR), ("validated", VALID_COLOR)]:
        sub = agg[agg["dataset"] == dataset].sort_values("year")
        ax.plot(sub["year"], sub[metric], color=c, marker="o" if dataset == "raw" else "s",
                linewidth=2.2, markersize=8, label=("Raw" if dataset == "raw" else "Validated"))
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontweight="bold")
    ax.set_xticks(ALL_YEARS)
    ax.legend(frameon=True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "figures", fname))
    plt.close()
    print(f"  Saved {fname}")


def plot_metric_by_tech(agg, metric, ylabel, fname, title):
    techs = sorted(agg["tech_norm"].unique())
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for tech in techs:
        for dataset, c, ls in [("raw", RAW_COLOR, "-"), ("validated", VALID_COLOR, "--")]:
            sub = agg[(agg["tech_norm"] == tech) & (agg["dataset"] == dataset)].sort_values("year")
            label = f"{tech.capitalize()} ({'raw' if dataset == 'raw' else 'validated'})"
            ax.plot(sub["year"], sub[metric], color=c, ls=ls, marker="o",
                    linewidth=1.8, markersize=5, label=label)
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontweight="bold")
    ax.set_xticks(ALL_YEARS)
    ax.legend(frameon=True, ncol=2, fontsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "figures", fname))
    plt.close()
    print(f"  Saved {fname}")


def plot_isp_scatter(raw, valid, metric, ylabel, fname, title):
    """Scatter raw vs validated per ISP-year (common ISPs only), with 1:1 line."""
    r = raw.groupby(["isp_lc", "year"]).agg(N=("N", "sum"), RC=("RC", "sum"),
                                            TIS=("TIS", "sum")).reset_index()
    v = valid.groupby(["isp_lc", "year"]).agg(N=("N", "sum"), RC=("RC", "sum"),
                                              TIS=("TIS", "sum")).reset_index()
    for d in (r, v):
        d["RC%"] = d["RC"] / d["N"] * 100
        d["TIS%"] = d["TIS"] / d["N"] * 100
    merged = r.merge(v, on=["isp_lc", "year"], suffixes=("_raw", "_valid"))
    merged = merged[merged["N_raw"] >= 5]
    x = merged[f"{metric}_valid"]
    y = merged[f"{metric}_raw"]
    fig, ax = plt.subplots(figsize=(6.5, 6))
    ax.scatter(x, y, s=45, c="#666666", alpha=0.7, edgecolors="white", linewidths=0.3, zorder=3)
    lim = max(merged[f"{metric}_valid"].max(), merged[f"{metric}_raw"].max())
    lim = max(lim * 1.1, 5)
    ax.plot([0, lim], [0, lim], ls="--", color="black", lw=1.2, label="y = x", zorder=2)
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("Validated Prevalence (%)")
    ax.set_ylabel("Raw Prevalence (%)")
    ax.set_title(title, fontweight="bold")
    ax.legend(frameon=True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.3)
    corr = np.corrcoef(x, y)[0, 1]
    ax.text(0.03, 0.97, f"r = {corr:.2f}  (n = {len(merged)})",
            transform=ax.transAxes, va="top", fontsize=9,
            bbox=dict(boxstyle="round", fc="white", ec="gray", alpha=0.8))
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "figures", fname))
    plt.close()
    print(f"  Saved {fname}")


def save_tables(overall, by_tech):
    overall = overall[["year", "dataset", "N", "RC", "TIS", "RC%", "TIS%"]]
    overall = overall.sort_values(["year", "dataset"])
    overall.to_csv(os.path.join(OUTPUT_DIR, "tables", "comparison_overall_raw_valid.csv"),
                   index=False)
    pivot = overall.pivot(index="year", columns="dataset", values=["N", "RC%", "TIS%"])
    pivot.columns = [f"{c[1]}_{c[0]}" for c in pivot.columns]
    pivot = pivot.reset_index()
    pivot.to_csv(os.path.join(OUTPUT_DIR, "tables", "comparison_pivot.csv"), index=False)
    print("  Saved comparison_overall_raw_valid.csv / comparison_pivot.csv")
    print(pivot.to_string(index=False))

    by_tech.to_csv(os.path.join(OUTPUT_DIR, "tables", "comparison_by_tech_raw_valid.csv"),
                   index=False)
    print("  Saved comparison_by_tech_raw_valid.csv")


def main():
    print("Loading raw and validated ISP aggregates...")
    raw = load("raw")
    valid = load("validated")
    print(f"  raw: {len(raw)} ISP-year rows over {sorted(raw['year'].unique())}")
    print(f"  valid: {len(valid)} ISP-year rows over {sorted(valid['year'].unique())}")

    print("\nSaving comparison tables...")
    overall = overall_agg(pd.concat([raw, valid], ignore_index=True))
    by_tech = tech_agg(pd.concat([raw, valid], ignore_index=True))
    save_tables(overall, by_tech)

    print("\nPlotting overall trends...")
    plot_metric_overall(overall, "RC%", "RC Prevalence (%)",
                        "compare_raw_valid_RC_overall.png",
                        "Recurrent Congestion Prevalence: Raw vs Validated")
    plot_metric_overall(overall, "TIS%", "TIS Prevalence (%)",
                        "compare_raw_valid_TIS_overall.png",
                        "Tight Initial Segment Prevalence: Raw vs Validated")

    print("\nPlotting per-technology trends...")
    plot_metric_by_tech(by_tech, "RC%", "RC Prevalence (%)",
                        "compare_raw_valid_RC_by_tech.png",
                        "RC Prevalence by Technology: Raw vs Validated")
    plot_metric_by_tech(by_tech, "TIS%", "TIS Prevalence (%)",
                        "compare_raw_valid_TIS_by_tech.png",
                        "TIS Prevalence by Technology: Raw vs Validated")

    print("\nPlotting per-ISP raw-vs-validated scatter...")
    plot_isp_scatter(raw, valid, "RC%", "Raw RC (%)",
                     "compare_raw_valid_RC_isp_scatter.png",
                     "ISP-Year RC%: Raw vs Validated (N>=5)")
    plot_isp_scatter(raw, valid, "TIS%", "Raw TIS (%)",
                     "compare_raw_valid_TIS_isp_scatter.png",
                     "ISP-Year TIS%: Raw vs Validated (N>=5)")

    print("\nDone.")

if __name__ == "__main__":
    main()
