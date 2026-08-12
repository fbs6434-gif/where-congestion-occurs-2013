import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CSV = "/home/jovyan/work/project/output/compare/tables/comparison_by_tech.csv"
OVERALL_CSV = "/home/jovyan/work/project/output/compare/tables/comparison_overall.csv"

# Paper (Genin & Splett 2013, March 2011) published ranges, from paper + ANALYSIS.md
PAPER = {
    "RC_pct": {"cable": (27, 32), "dsl": (9, 12)},
    "TIS_pct": {"cable": (3, 4), "dsl": (5, 7)},
}

THEM = {"cable": "Cable", "dsl": "DSL", "overall": "Overall"}

def load_2011():
    out = {"cable": {}, "dsl": {}}
    with open(CSV) as f:
        for row in csv.DictReader(f):
            if row["year"] == "2011" and row["technology"] in out:
                out[row["technology"]] = {"RC": float(row["RC%"]), "TIS": float(row["TIS%"])}
    with open(OVERALL_CSV) as f:
        for row in csv.DictReader(f):
            if row["year"] == "2011":
                out["overall"] = {"RC": float(row["RC%"]), "TIS": float(row["TIS%"])}
    return out

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

def make(metric_key, title, ymax, data):
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3), sharey=True)
    colors = {"Paper (2013)": "#009b8a", "Our replication": "#6dc5b8"}

    for ax, tech in zip(axes, ["cable", "dsl", "overall"]):
        ours = data[tech][metric_key.split("_")[0]]
        ax.set_title(THEM[tech], fontweight="bold")
        if tech == "cable":
            ax.set_ylabel("Prevalence (%)")
        ax.set_ylim(0, ymax)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", alpha=0.3)

        if tech == "overall":
            # paper reports no aggregate prevalence; show only our number
            ax.bar(["Our replication"], [ours], color="#6dc5b8",
                   edgecolor="black", linewidth=0.7, width=0.55)
            ax.text(0, ours + 0.3, f"{ours:.1f}%", ha="center", va="bottom",
                    fontsize=10, fontweight="bold")
            ax.annotate("not reported\nin paper", xy=(0, ours + 0.3), xytext=(0, ours + 2.2),
                        ha="center", fontsize=8, color="#555555",
                        arrowprops=dict(arrowstyle="-", color="#999999", lw=0.8))
        else:
            lo, hi = PAPER[metric_key][tech]
            ctr = (lo + hi) / 2
            ax.bar(["Paper (2013)", "Our replication"], [ctr, ours],
                   color=[colors["Paper (2013)"], colors["Our replication"]],
                   edgecolor="black", linewidth=0.7, width=0.55)
            ax.text(0, hi + 0.5, f"{lo:.0f}\u2013{hi:.0f}%", ha="center", va="bottom",
                    fontsize=10, fontweight="bold")
            ax.text(1, ours + 0.3, f"{ours:.1f}%", ha="center", va="bottom",
                    fontsize=10, fontweight="bold")

    fig.suptitle(title, fontsize=15, fontweight="bold", y=1.02)
    fig.tight_layout()
    fname = f"/home/jovyan/work/project/output/bar_{metric_key}.png"
    fig.savefig(fname)
    plt.close()
    print("Saved", fname)

def main():
    data = load_2011()
    make("RC_pct", "Recurrent Congestion", 35, data)
    make("TIS_pct", "Congestion in Network Periphery", 15, data)

if __name__ == "__main__":
    main()