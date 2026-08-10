import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Data from the CSV
data = {
    "RC_pct": {
        "Paper":     {"Overall": 21.3, "Cable": 26.7, "DSL": 11.5},
        "Raw":       {"Overall": 17.0, "Cable": 24.1, "DSL": 7.0},
        "Validated": {"Overall": 17.2, "Cable": 24.2, "DSL": 7.1},
    },
    "TIS_pct": {
        "Paper":     {"Overall": 4.5, "Cable": 3.5, "DSL": 6.4},
        "Raw":       {"Overall": 2.5, "Cable": 2.0, "DSL": 3.3},
        "Validated": {"Overall": 2.6, "Cable": 2.1, "DSL": 3.4},
    },
}

sources = ["Paper", "Raw", "Validated"]
techs = ["Overall", "Cable", "DSL"]
bar_colors = ["#4C72B0", "#DD8452", "#55A868"]

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

for metric_key, title in [("RC_pct", "Recurrent Congestion"), ("TIS_pct", "Congestion in Network Periphery")]:
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5), sharey=False)

    for ax, tech in zip(axes, techs):
        vals = [data[metric_key][s][tech] for s in sources]
        bars = ax.bar(sources, vals, color=bar_colors, edgecolor="black", linewidth=0.7, width=0.6)

        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    f"{v:.1f}%", ha="center", va="bottom", fontsize=10, fontweight="bold")

        ax.set_title(tech, fontweight="bold")
        ax.set_ylabel("Prevalence (%)" if tech == "Overall" else "")
        ax.set_ylim(0, max(vals) * 1.35)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle(title, fontsize=15, fontweight="bold", y=1.02)
    fig.tight_layout()
    fname = f"bar_{metric_key}.png"
    fig.savefig(f"/home/jovyan/work/project/output/{fname}")
    plt.close()
    print(f"Saved {fname}")
