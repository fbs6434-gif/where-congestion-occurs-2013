import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from config import PROCESSED_DIR, OUTPUT_DIR, YEAR, MONTH

OUTPUT_DIR_FIGURES = os.path.join(OUTPUT_DIR, "figures")
os.makedirs(OUTPUT_DIR_FIGURES, exist_ok=True)

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

TECH_COLORS = {}
TECH_MARKERS = {}
_tech_palette = ["#E24A33", "#348ABD", "#2E8B57", "#FFD700", "#9370DB",
                 "#20B2AA", "#FF6347", "#4682B4", "#D2691E", "#8B0000"]
_tech_markers_list = ["o", "s", "^", "D", "v", "<", ">", "p", "*", "h"]

def load_data():
    meta = pd.read_parquet(os.path.join(PROCESSED_DIR, "meta_valid.parquet"))
    rc = pd.read_parquet(os.path.join(PROCESSED_DIR, "rc.parquet"))
    tis = pd.read_parquet(os.path.join(PROCESSED_DIR, "tis.parquet"))
    merged = rc.merge(tis, on=["unit_id", "month"]).merge(
        meta[["unit_id", "isp", "technology"]], on="unit_id"
    )
    return merged

def compute_isp_summary(merged, tech):
    sub = merged[merged["technology"] == tech]
    summary = sub.groupby("isp").agg(
        N=("unit_id", "count"),
        RC=("rc", "sum"),
        TIS=("tis", "sum"),
    ).reset_index()
    summary["RC%"] = (summary["RC"] / summary["N"] * 100)
    summary["TIS%"] = (summary["TIS"] / summary["N"] * 100)
    return summary

def plot_isp_dotplot(summary, isp_list, tech, metric, title, ylabel, fname):
    isp_labels = [f"{name}" for name in isp_list]
    tech_color = TECH_COLORS.get(tech, "#333333")
    summary_map = dict(zip(summary["isp"], summary[metric]))
    n_map = dict(zip(summary["isp"], summary["N"]))
    x_pos = np.arange(len(isp_list))
    vals = np.array([summary_map.get(isp, np.nan) for isp in isp_list])
    ns = np.array([n_map.get(isp, 0) for isp in isp_list])
    max_val = np.nanmax(vals) if np.any(~np.isnan(vals)) else 1
    y_max = max(max_val * 1.45, 5)
    fig, ax = plt.subplots(figsize=(max(8, len(isp_list) * 0.55), 3.5))
    mask = ~np.isnan(vals)
    ax.scatter(x_pos[mask], vals[mask], s=80, c=tech_color, edgecolors="black",
               linewidths=0.6, zorder=5)
    ax.axhline(y=0, color="black", linewidth=0.8, zorder=1)
    ax.set_ylim(-max_val * 0.05, y_max)
    ax.set_xlim(-0.6, len(isp_list) - 0.4)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(isp_labels, fontsize=6, rotation=45, ha="right")
    ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=5))
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))
    for v, n, x, has_data in zip(vals, ns, x_pos, mask):
        if has_data:
            ax.text(x, v + y_max * 0.02, f"{v:.1f}%",
                    ha="center", va="bottom", fontsize=8, fontweight="bold", color=tech_color)
            ax.text(x, -y_max * 0.02, f"N={n}",
                    ha="center", va="top", fontsize=7, color="gray")
    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_title(title, fontsize=10, fontweight="bold", pad=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(bottom=False)
    ax.grid(axis="y", alpha=0.25, zorder=0)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR_FIGURES, fname))
    plt.close()
    print(f"  Saved {fname}")

def plot_scatter(merged):
    fig_data = []
    for (isp, tech), grp in merged.groupby(["isp", "technology"]):
        N = len(grp)
        rc_pct = grp["rc"].mean() * 100
        tis_pct = grp["tis"].mean() * 100
        fig_data.append({"ISP": isp, "Technology": tech, "RC%": rc_pct, "TIS%": tis_pct})
    fig_df = pd.DataFrame(fig_data)
    techs = sorted(fig_df["Technology"].unique())
    fig, ax = plt.subplots(figsize=(7, 5.5))
    for tech in techs:
        sub = fig_df[fig_df["Technology"] == tech]
        c = TECH_COLORS.get(tech, "#333333")
        m = TECH_MARKERS.get(tech, "o")
        ax.scatter(sub["TIS%"], sub["RC%"], c=c, marker=m, s=100,
                   label=tech.capitalize(), edgecolors="black", linewidths=0.5,
                   alpha=0.85, zorder=5)
        for _, row in sub.iterrows():
            ax.annotate(row["ISP"], (row["TIS%"], row["RC%"]),
                        xytext=(5, 5), textcoords="offset points",
                        fontsize=7, fontweight="bold", color=c)
    x_max = fig_df["TIS%"].max() * 1.3 + 0.5
    y_max = fig_df["RC%"].max() * 1.1 + 1
    ax.set_xlim(-0.5, x_max)
    ax.set_ylim(-0.5, y_max)
    ax.set_xlabel("TIS Prevalence (%)", fontsize=11)
    ax.set_ylabel("RC Prevalence (%)", fontsize=11)
    month_label = MONTH.capitalize()
    ax.set_title(f"RC vs TIS Prevalence by ISP ({month_label} {YEAR})", fontsize=12, fontweight="bold")
    ax.legend(frameon=True, fontsize=9, loc="upper left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR_FIGURES, "fig_scatter.png"))
    plt.close()
    print(f"  Saved fig_scatter.png")
    ax.set_yscale("log")
    ax.set_xscale("log")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR_FIGURES, "fig_scatter_log.png"))
    plt.close()
    print(f"  Saved fig_scatter_log.png")

def save_tables(merged):
    os.makedirs(os.path.join(OUTPUT_DIR, "tables"), exist_ok=True)
    tech_groups = list(merged["technology"].unique())
    for tech in tech_groups:
        sub = merged[merged["technology"] == tech]
        N = len(sub)
        N_rc = sub["rc"].sum()
        N_tis = sub["tis"].sum()
        N_both = ((sub["rc"]) & (sub["tis"])).sum()
        rows = [{
            "Year": YEAR, "Month": MONTH.capitalize(),
            "Technology": tech.capitalize(),
            "Total": N, "RC": N_rc, "TIS": N_tis, "RC∩TIS": N_both,
            "RC∩TIS/TIS%": round(N_both / N_tis * 100, 1) if N_tis else 0,
            "RC∩TIS/RC%": round(N_both / N_rc * 100, 1) if N_rc else 0,
            "RC%": round(N_rc / N * 100, 1) if N else 0,
            "TIS%": round(N_tis / N * 100, 1) if N else 0,
        }]
        tbl = pd.DataFrame(rows)
        tbl.to_csv(os.path.join(OUTPUT_DIR, "tables", f"table_{tech}.csv"), index=False)

def print_isp_table(merged, tech, label):
    sub = merged[merged["technology"] == tech]
    rows = []
    for isp, grp in sub.groupby("isp"):
        N = len(grp)
        N_rc = grp["rc"].sum()
        N_tis = grp["tis"].sum()
        N_both = (grp["rc"] & grp["tis"]).sum()
        rows.append({
            "ISP": isp, "N": N,
            "RC%": round(N_rc / N * 100, 1),
            "TIS%": round(N_tis / N * 100, 1),
            "RC∩TIS/TIS%": round(N_both / N_tis * 100, 1) if N_tis else 0,
            "RC∩TIS/RC%": round(N_both / N_rc * 100, 1) if N_rc else 0,
        })
    tbl = pd.DataFrame(rows).sort_values("RC%", ascending=False)
    print(f"\nPer-{label} results:")
    print(tbl.to_string(index=False))

def main():
    print(f"Loading data for {MONTH.capitalize()} {YEAR}...")
    merged = load_data()

    techs = sorted(merged["technology"].unique())
    print(f"Technologies: {techs}")
    for i, tech in enumerate(techs):
        TECH_COLORS[tech] = _tech_palette[i % len(_tech_palette)]
        TECH_MARKERS[tech] = _tech_markers_list[i % len(_tech_markers_list)]

    isp_tech = merged.groupby("isp")["technology"].first().to_dict()
    print(f"ISPs ({len(isp_tech)}): {isp_tech}")

    print("\nAggregate results:")
    save_tables(merged)

    for tech in techs:
        label = tech.capitalize()
        print_isp_table(merged, tech, label)
        summary = compute_isp_summary(merged, tech)
        isps_in_tech = sorted(merged[merged["technology"] == tech]["isp"].unique())

        print(f"\nPlotting TIS prevalence for {label}...")
        plot_isp_dotplot(summary, isps_in_tech, tech, "TIS%",
                         f"TIS Prevalence — {label} ISPs ({MONTH.capitalize()} {YEAR})",
                         "TIS (%)", f"fig_TIS_{tech}.png")

        print(f"Plotting RC prevalence for {label}...")
        plot_isp_dotplot(summary, isps_in_tech, tech, "RC%",
                         f"RC Prevalence — {label} ISPs ({MONTH.capitalize()} {YEAR})",
                         "RC (%)", f"fig_RC_{tech}.png")

    print("\nPlotting RC vs TIS scatter...")
    plot_scatter(merged)

    print("\nDone — all figures saved.")

if __name__ == "__main__":
    main()
