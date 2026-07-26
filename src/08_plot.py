import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from config import PROCESSED_DIR, OUTPUT_DIR

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

TECH_COLORS = {"cable": "#E24A33", "dsl": "#348ABD"}
TECH_MARKERS = {"cable": "s", "dsl": "o"}
TECH_LABELS = {"cable": "Cable", "dsl": "DSL"}

ISP_NUMBERING = {}
ISP_TECH = {}


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
        RC_TIS=("rc", lambda x: (sub.loc[x.index, "rc"] & sub.loc[x.index, "tis"]).sum()),
    ).reset_index()
    summary["RC%"] = (summary["RC"] / summary["N"] * 100)
    summary["TIS%"] = (summary["TIS"] / summary["N"] * 100)
    summary["RC∩TIS/TIS%"] = np.where(
        summary["TIS"] > 0, summary["RC_TIS"] / summary["TIS"] * 100, 0
    )
    summary["RC∩TIS/RC%"] = np.where(
        summary["RC"] > 0, summary["RC_TIS"] / summary["RC"] * 100, 0
    )
    return summary


def build_isp_numbering(merged):
    isp_to_num = {
        # Cable ISPs (paper numbers: 2, 3, 5, 6, 7, 9, 10, 12)
        "Insight": 2,
        "Cablevision": 3,   # paper: very high TIS + high RC
        "Charter": 5,
        "TimeWarner": 6,
        "Cox": 7,           # paper: high RC, NOT high TIS
        "Comcast": 9,
        "Mediacom": 10,     # paper: very high TIS + high RC
        "Brighthouse": 12,
        # DSL ISPs (paper numbers: 1, 4, 8, 11, 13, 14)
        "CenturyLink": 1,
        "Frontier": 4,
        "AT&T": 8,
        "Qwest": 11,
        "Verizon": 13,
        "Windstream": 14,
    }
    tech_map = {
        isp: merged[merged["isp"] == isp]["technology"].iloc[0]
        for isp in isp_to_num
    }
    numbering = {isp: isp_to_num[isp] for isp in sorted(isp_to_num, key=lambda x: isp_to_num[x])}
    print(f"  ISP numbering ({len(numbering)} cable/DSL ISPs): {numbering}")
    for isp, num in numbering.items():
        print(f"    ISP {num:2d} = {isp:20s} ({tech_map[isp]})")
    return numbering, tech_map


def plot_isp_dotplot(summary, tech, metric, title, ylabel, fname):
    all_isps = sorted(ISP_NUMBERING.keys(), key=lambda x: ISP_NUMBERING[x])
    isp_labels = [f"ISP {ISP_NUMBERING[name]}\n({name})" for name in all_isps]
    tech_color = TECH_COLORS[tech]

    summary_map = dict(zip(summary["isp"], summary[metric]))
    n_map = dict(zip(summary["isp"], summary["N"]))

    x_pos = np.arange(len(all_isps))
    vals = np.array([summary_map.get(isp, np.nan) for isp in all_isps])
    ns = np.array([n_map.get(isp, 0) for isp in all_isps])

    max_val = np.nanmax(vals) if np.any(~np.isnan(vals)) else 1
    y_max = max(max_val * 1.45, 5)

    fig, ax = plt.subplots(figsize=(8, 3.5))

    mask = ~np.isnan(vals)
    ax.scatter(x_pos[mask], vals[mask], s=80, c=tech_color, edgecolors="black",
               linewidths=0.6, zorder=5)

    ax.axhline(y=0, color="black", linewidth=0.8, zorder=1)

    ax.set_ylim(-max_val * 0.05, y_max)
    ax.set_xlim(-0.6, len(all_isps) - 0.4)

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
        fig_data.append({
            "ISP": isp, "Technology": tech,
            "RC%": rc_pct, "TIS%": tis_pct
        })
    fig_df = pd.DataFrame(fig_data)

    fig, ax = plt.subplots(figsize=(7, 5.5))
    for tech in ["dsl", "cable"]:
        sub = fig_df[fig_df["Technology"] == tech]
        ax.scatter(sub["TIS%"], sub["RC%"],
                   c=TECH_COLORS[tech], marker=TECH_MARKERS[tech],
                   s=100, label=TECH_LABELS[tech],
                   edgecolors="black", linewidths=0.5,
                   alpha=0.85, zorder=5)

        for _, row in sub.iterrows():
            label = f"ISP {ISP_NUMBERING.get(row['ISP'], '?')}"
            ax.annotate(
                label,
                (row["TIS%"], row["RC%"]),
                xytext=(5, 5), textcoords="offset points",
                fontsize=7, fontweight="bold",
                color=TECH_COLORS[tech],
            )

    x_max = fig_df["TIS%"].max() * 1.3 + 0.5
    y_max = fig_df["RC%"].max() * 1.1 + 1
    ax.set_xlim(-0.5, x_max)
    ax.set_ylim(-0.5, y_max)

    ax.set_xlabel("TIS Prevalence (%)", fontsize=11)
    ax.set_ylabel("RC Prevalence (%)", fontsize=11)
    ax.set_title("RC vs TIS Prevalence by ISP (March 2011)", fontsize=12, fontweight="bold")
    ax.legend(frameon=True, fontsize=9, loc="upper left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR_FIGURES, "fig5_scatter.png"))
    plt.close()
    print(f"  Saved fig5_scatter.png")

    ax.set_yscale("log")
    ax.set_xscale("log")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR_FIGURES, "fig5_scatter_log.png"))
    plt.close()
    print(f"  Saved fig5_scatter_log.png")


def save_tables(merged):
    os.makedirs(os.path.join(OUTPUT_DIR, "tables"), exist_ok=True)
    for tech, label, fname in [("cable", "Cable", "table_I_cable.csv"),
                                ("dsl", "DSL", "table_II_dsl.csv")]:
        sub = merged[merged["technology"] == tech]
        N = len(sub)
        N_rc = sub["rc"].sum()
        N_tis = sub["tis"].sum()
        N_both = ((sub["rc"]) & (sub["tis"])).sum()
        rows = [{
            "Month": "March",
            "Total": N,
            "RC": N_rc,
            "TIS": N_tis,
            "RC∩TIS": N_both,
            "RC∩TIS/TIS%": round(N_both / N_tis * 100, 1) if N_tis else 0,
            "RC∩TIS/RC%": round(N_both / N_rc * 100, 1) if N_rc else 0,
            "RC%": round(N_rc / N * 100, 1) if N else 0,
            "TIS%": round(N_tis / N * 100, 1) if N else 0,
        }]
        tbl = pd.DataFrame(rows)
        tbl.to_csv(os.path.join(OUTPUT_DIR, "tables", fname), index=False)
        print(f"  Saved {fname}")
        print(tbl.to_string(index=False))
        print()


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
    print(f"\nPer-ISP {label} results:")
    print(tbl.to_string(index=False))


def main():
    print("Loading data...")
    merged = load_data()

    global ISP_NUMBERING, ISP_TECH
    ISP_NUMBERING, ISP_TECH = build_isp_numbering(merged)

    print("\nAggregate results:")
    save_tables(merged)

    for tech, label in [("cable", "Cable"), ("dsl", "DSL")]:
        print_isp_table(merged, tech, label)
        summary = compute_isp_summary(merged, tech)

        print(f"\nPlotting Figure 3/4 — TIS prevalence for {label}...")
        plot_isp_dotplot(
            summary, tech, "TIS%",
            f"TIS Prevalence — {label} ISPs",
            "TIS (%)", f"fig{3 if tech == 'cable' else 4}_TIS_{tech}.png"
        )

        print(f"Plotting Figure 6/7 — RC prevalence for {label}...")
        plot_isp_dotplot(
            summary, tech, "RC%",
            f"RC Prevalence — {label} ISPs",
            "RC (%)", f"fig{6 if tech == 'cable' else 7}_RC_{tech}.png"
        )

    print("\nPlotting Figure 5 — RC vs TIS scatter...")
    plot_scatter(merged)

    print("\nDone — all figures saved to output/figures/")


if __name__ == "__main__":
    main()
