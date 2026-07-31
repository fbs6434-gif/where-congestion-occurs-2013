import os
import itertools
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

ALL_YEARS = [2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
PROCESSED_DIRS = {y: f"/home/jovyan/work/project/data/processed/{y}" for y in ALL_YEARS}
OUTPUT_DIR = "/home/jovyan/work/project/output/compare"
os.makedirs(os.path.join(OUTPUT_DIR, "figures"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "tables"), exist_ok=True)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

TECH_COLORS = {}
_tech_palette = ["#E24A33", "#348ABD", "#2E8B57", "#FFD700", "#9370DB",
                 "#20B2AA", "#FF6347", "#4682B4", "#D2691E", "#8B0000"]
TECH_MARKERS = {}
_tech_markers_list = ["o", "s", "^", "D", "v", "<", ">", "p", "*", "h"]

ISP_NAME_NORMALIZE = {
    "TimeWarner": "Time Warner Cable",
    "Time Warner Cable": "Time Warner Cable",
    "Wildblue/ViaSat": "Hughes",
    "Hughes": "Hughes",
    "Cincinnati Bell": "Cincinnati Bell",
    "Optimum": "Optimum",
}

def normalize_isp(name):
    return ISP_NAME_NORMALIZE.get(name, name)

def load_all():
    frames = []
    for year, d in PROCESSED_DIRS.items():
        fp = os.path.join(d, "isp_agg.parquet")
        if os.path.isfile(fp):
            df = pd.read_parquet(fp)
            df["year"] = year
            frames.append(df)
    combined = pd.concat(frames, ignore_index=True)
    combined["isp_norm"] = combined["isp"].apply(normalize_isp)
    return combined

def plot_metric_by_tech(combined, metric, title, ylabel, fname):
    techs = sorted(combined["technology"].unique())
    fig, ax = plt.subplots(figsize=(8, 5))
    for i, tech in enumerate(techs):
        sub = combined[combined["technology"] == tech]
        agg = sub.groupby("year").agg(N=("N", "sum"), RC=("RC", "sum"), TIS=("TIS", "sum")).reset_index()
        agg["RC%"] = (agg["RC"] / agg["N"] * 100).round(1)
        agg["TIS%"] = (agg["TIS"] / agg["N"] * 100).round(1)
        c = _tech_palette[i % len(_tech_palette)]
        m = _tech_markers_list[i % len(_tech_markers_list)]
        ax.plot(agg["year"], agg[metric], color=c, marker=m, label=tech.capitalize(),
                linewidth=2, markersize=8, zorder=5)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xticks(sorted(combined["year"].unique()))
    ax.legend(frameon=True, fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "figures", fname))
    plt.close()
    print(f"Saved {fname}")

def plot_metric_per_tech(combined, metric, title, ylabel, fname_prefix):
    techs = sorted(combined["technology"].unique())
    for i, tech in enumerate(techs):
        sub = combined[combined["technology"] == tech]
        agg = sub.groupby("year").agg(N=("N", "sum"), RC=("RC", "sum"), TIS=("TIS", "sum")).reset_index()
        agg["RC%"] = (agg["RC"] / agg["N"] * 100).round(1)
        agg["TIS%"] = (agg["TIS"] / agg["N"] * 100).round(1)
        c = _tech_palette[i % len(_tech_palette)]
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(agg["year"], agg[metric], color=c, marker="o",
                linewidth=2.5, markersize=9, zorder=5)
        ax.set_xlabel("Year", fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_title(f"{title}: {tech.capitalize()}", fontsize=12, fontweight="bold")
        ax.set_xticks(sorted(agg["year"]))
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        fname = f"{fname_prefix}_{tech.replace(' ', '_')}.png"
        plt.savefig(os.path.join(OUTPUT_DIR, "figures", fname))
        plt.close()
        print(f"  Saved {fname}")

ARTICLE_ISPS = ["AT&T", "Brighthouse", "Cablevision", "CenturyLink", "Charter",
                "Comcast", "Cox", "Frontier", "Insight", "Mediacom", "Qwest",
                "Time Warner Cable", "Verizon", "Windstream"]

def plot_metric_by_isp(combined, metric, title, ylabel, fname, isp_filter=None):
    isp_agg = combined.groupby(["isp_norm", "year"]).agg(
        N=("N", "sum"), RC=("RC", "sum"), TIS=("TIS", "sum")
    ).reset_index()
    isp_agg["RC%"] = (isp_agg["RC"] / isp_agg["N"] * 100).round(1)
    isp_agg["TIS%"] = (isp_agg["TIS"] / isp_agg["N"] * 100).round(1)
    if isp_filter is not None:
        isp_agg = isp_agg[isp_agg["isp_norm"].isin(isp_filter)]
    isp_years = isp_agg.groupby("isp_norm")["year"].apply(set)
    common_isps = sorted([isp for isp in isp_years.index if len(isp_years[isp]) >= 2])
    if not common_isps:
        print("No ISPs with data in 2+ years for ISP-level plot")
        return
    styles = list(itertools.product(_tech_palette, _tech_markers_list))
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for i, isp in enumerate(common_isps):
        sub = isp_agg[isp_agg["isp_norm"] == isp].sort_values("year")
        c, m = styles[i % len(styles)]
        ax.plot(sub["year"], sub[metric], color=c, marker=m, label=isp,
                linewidth=2, markersize=8, zorder=5)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xticks(sorted(combined["year"].unique()))
    ax.legend(frameon=True, fontsize=7, loc="best", ncol=2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "figures", fname))
    plt.close()
    print(f"Saved {fname}")

def save_comparison_table(combined):
    overall = combined.groupby("year").agg(
        N=("N", "sum"), RC=("RC", "sum"), TIS=("TIS", "sum")
    ).reset_index()
    overall["RC%"] = (overall["RC"] / overall["N"] * 100).round(1)
    overall["TIS%"] = (overall["TIS"] / overall["N"] * 100).round(1)
    month_map = {2011: "March", 2012: "April", 2013: "September", 2014: "September",
                 2015: "September", 2016: "September", 2017: "September",
                 2018: "September", 2019: "September", 2020: "September",
                 2021: "September", 2022: "September", 2023: "September"}
    overall["Month"] = overall["year"].map(month_map)
    overall = overall[["year", "Month", "N", "RC", "TIS", "RC%", "TIS%"]]
    overall.to_csv(os.path.join(OUTPUT_DIR, "tables", "comparison_overall.csv"), index=False)
    print("Saved comparison_overall.csv")
    print(overall.to_string(index=False))

    by_tech = combined.groupby(["year", "technology"]).agg(
        N=("N", "sum"), RC=("RC", "sum"), TIS=("TIS", "sum")
    ).reset_index()
    by_tech["RC%"] = (by_tech["RC"] / by_tech["N"] * 100).round(1)
    by_tech["TIS%"] = (by_tech["TIS"] / by_tech["N"] * 100).round(1)
    by_tech = by_tech.sort_values(["year", "technology"])
    by_tech.to_csv(os.path.join(OUTPUT_DIR, "tables", "comparison_by_tech.csv"), index=False)
    print("Saved comparison_by_tech.csv")
    print(by_tech.to_string(index=False))

def main():
    print("Loading data...")
    combined = load_all()
    print(f"Loaded {len(combined)} ISP-year rows from years {sorted(combined['year'].unique())}")

    print("\nSaving comparison tables...")
    save_comparison_table(combined)

    print("\nPlotting RC% by technology...")
    plot_metric_by_tech(combined, "RC%",
        "Recurrent Congestion (RC) Prevalence by Technology",
        "RC (%)", "compare_RC_by_tech.png")

    print("Plotting TIS% by technology...")
    plot_metric_by_tech(combined, "TIS%",
        "Tight Initial Segment (TIS) Prevalence by Technology",
        "TIS (%)", "compare_TIS_by_tech.png")

    print("\nPlotting per-technology RC% trends...")
    plot_metric_per_tech(combined, "RC%",
        "Recurrent Congestion (RC) Prevalence",
        "RC (%)", "compare_RC_tech")

    print("Plotting per-technology TIS% trends...")
    plot_metric_per_tech(combined, "TIS%",
        "Tight Initial Segment (TIS) Prevalence",
        "TIS (%)", "compare_TIS_tech")

    aggregated = combined.groupby("year").agg(
        N=("N", "sum"), RC=("RC", "sum"), TIS=("TIS", "sum")
    ).reset_index()
    aggregated["RC%"] = (aggregated["RC"] / aggregated["N"] * 100).round(1)
    aggregated["TIS%"] = (aggregated["TIS"] / aggregated["N"] * 100).round(1)
    plt.figure(figsize=(7, 4))
    plt.plot(aggregated["year"], aggregated["RC%"], color=_tech_palette[0],
             marker="o", linewidth=2.5, markersize=10, label="RC%")
    plt.plot(aggregated["year"], aggregated["TIS%"], color=_tech_palette[1],
             marker="s", linewidth=2.5, markersize=10, label="TIS%")
    plt.xlabel("Year")
    plt.ylabel("Prevalence (%)")
    plt.title("Overall Congestion Prevalence Over Time", fontsize=12, fontweight="bold")
    plt.xticks(sorted(aggregated["year"]))
    plt.legend(frameon=True)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "figures", "compare_overall_trend.png"))
    plt.close()
    print("Saved compare_overall_trend.png")

    print("\nPlotting overall RC-only and TIS-only trends...")
    shared_ylim = (0, max(30, aggregated["RC%"].max() * 1.1))

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(aggregated["year"], aggregated["RC%"], color=_tech_palette[0],
            marker="o", linewidth=2.5, markersize=10)
    ax.set_xlabel("Year")
    ax.set_ylabel("RC (%)")
    ax.set_title("Recurrent Congestion Prevalence Over Time", fontsize=12, fontweight="bold")
    ax.set_xticks(sorted(aggregated["year"]))
    ax.set_ylim(shared_ylim)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "figures", "compare_RC_overall.png"))
    plt.close()
    print("Saved compare_RC_overall.png")

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(aggregated["year"], aggregated["TIS%"], color=_tech_palette[1],
            marker="s", linewidth=2.5, markersize=10)
    ax.set_xlabel("Year")
    ax.set_ylabel("TIS (%)")
    ax.set_title("Tight Initial Segment Prevalence Over Time", fontsize=12, fontweight="bold")
    ax.set_xticks(sorted(aggregated["year"]))
    ax.set_ylim(shared_ylim)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "figures", "compare_TIS_overall.png"))
    plt.close()
    print("Saved compare_TIS_overall.png")

    print("\nPlotting ISP-level comparisons...")
    plot_metric_by_isp(combined, "RC%",
        "RC Prevalence by ISP Over Time",
        "RC (%)", "compare_RC_by_isp.png")
    plot_metric_by_isp(combined, "TIS%",
        "TIS Prevalence by ISP Over Time",
        "TIS (%)", "compare_TIS_by_isp.png")

    print("\nPlotting ISP-level comparisons (article ISPs only)...")
    plot_metric_by_isp(combined, "RC%",
        "RC Prevalence by ISP Over Time (2011 Article ISPs)",
        "RC (%)", "compare_RC_by_isp_article.png", isp_filter=ARTICLE_ISPS)
    plot_metric_by_isp(combined, "TIS%",
        "TIS Prevalence by ISP Over Time (2011 Article ISPs)",
        "TIS (%)", "compare_TIS_by_isp_article.png", isp_filter=ARTICLE_ISPS)

    print("\nDone.")

if __name__ == "__main__":
    main()
