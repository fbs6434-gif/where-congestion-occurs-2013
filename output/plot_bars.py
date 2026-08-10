import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

data = {
    "RC_pct": {
        "Original":       {"Overall": 21.3, "Cable": 26.7, "DSL": 11.5},
        "Our replication": {"Overall": 17.2, "Cable": 24.2, "DSL": 7.1},
    },
    "TIS_pct": {
        "Original":       {"Overall": 4.5, "Cable": 3.5, "DSL": 6.4},
        "Our replication": {"Overall": 2.6, "Cable": 2.1, "DSL": 3.4},
    },
}

sources = ["Original", "Our replication"]
techs = ["Overall", "Cable", "DSL"]
color_maps = {
    "RC_pct": ["#009b8a", "#6dc5b8"],
    "TIS_pct": ["#59B2D1", "#a8d8ea"],
}

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
    fig, axes = plt.subplots(1, 3, figsize=(8, 3), sharey=True)
    bar_colors = color_maps[metric_key]

    for ax, tech in zip(axes, techs):
        vals = [data[metric_key][s][tech] for s in sources]
        bars = ax.bar(sources, vals, color=bar_colors, edgecolor="black", linewidth=0.7, width=0.55)

        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    f"{v:.1f}%", ha="center", va="bottom", fontsize=10, fontweight="bold")

        ax.set_title(tech, fontweight="bold")
        if tech == "Overall":
            ax.set_ylabel("Prevalence (%)")
        ymax = 35 if metric_key == "RC_pct" else 15
        ax.set_ylim(0, ymax)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle(title, fontsize=15, fontweight="bold", y=1.02)
    fig.tight_layout()
    fname = f"bar_{metric_key}.png"
    fig.savefig(f"/home/jovyan/work/project/output/{fname}")
    plt.close()
    print(f"Saved {fname}")
