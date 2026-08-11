import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import pandas as pd
import numpy as np
import os

OUT = "output/era_comparison"
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
    "savefig.dpi": 200,
})

df = pd.read_csv(os.path.join(OUT, "era_trends_metrics.csv"))
YEARS = list(range(2011, 2024))

fig = plt.figure(figsize=(14, 9.5))
gs = fig.add_gridspec(2, 2, hspace=0.45, wspace=0.22,
                      height_ratios=[1, 1])

# ---------- Panel (a): the evidence — TIS collapses to zero ----------
ax = fig.add_subplot(gs[0, 0])
ax.plot(df["year"], df["TIS%"], "-o", color="#8e44ad", lw=2.5, ms=6, label="TIS% (tight initial segment)")
ax.plot(df["year"], df["both_of_RC%"], "-s", color="#e67e22", lw=2.5, ms=6, label="RC\u2229TIS / RC (%)")
for x, v in df["TIS%"].items():
    ax.annotate(f"{v:.2f}", (df['year'][x], v), textcoords="offset points",
                xytext=(0, 7), ha="center", fontsize=7.5, color="#8e44ad")
ax.axvspan(2017.5, 2023.5, color="#f4d03f", alpha=0.18)
ax.axhline(0, color="#95a5a6", lw=0.8)
ax.set_xticks(YEARS)
ax.set_xlabel("Year")
ax.set_ylabel("Share of units (%)")
ax.set_ylim(-0.4, 14)
ax.set_title("(a) The evidence: the tight-initial-segment signal disappears after 2017")
ax.legend(frameon=False, loc="upper right")
ax.text(2020.5, 12.6, "TIS \u2261 0", ha="center", fontsize=11, color="#7b241c", fontweight="bold")

# ---------- Panel (b): why validity matters — method vs reality ----------
ax = fig.add_subplot(gs[0, 1])
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis("off")
ax.set_title("(b) The validity question: artifact or reality?", fontsize=11)

rows = [
    ("SamKnows correlation method", "detects a tight resource on the shared\ninitial segment via correlated slowdowns", "#8e44ad"),
    ("Valid until ~2017", "then TIS prevalence drops to exactly 0%\nacross cable AND DSL for 6 straight years", "#e67e22"),
    ("Two competing explanations", "congestion genuinely left the last mile\nvs. the detector's assumptions broke", "#2c3e50"),
]
y = 8.6
for title, body, col in rows:
    box = FancyBboxPatch((0.3, y - 0.95), 6.2, 1.9,
                         boxstyle="round,pad=0.08", fc="white", ec=col, lw=1.6)
    ax.add_patch(box)
    ax.text(0.7, y + 0.45, title, fontsize=10.5, fontweight="bold", va="center", color=col)
    ax.text(0.7, y - 0.25, body, fontsize=8.5, va="center", color="#333")
    y -= 2.6

# open question banner
qb = FancyBboxPatch((6.9, 4.4), 2.9, 3.0, boxstyle="round,pad=0.1",
                    fc="#fef9e7", ec="#b7950b", lw=1.4)
ax.add_patch(qb)
ax.text(7.05, 6.9, "Open question", fontsize=9, fontweight="bold", color="#7d6608")
ax.text(7.05, 5.4, "Did last-mile congestion\ntruly vanish, or did the\ndetector go blind?", fontsize=8, color="#333", va="center")

# ---------- Panel (c): future work — validating TIS ----------
ax = fig.add_subplot(gs[1, :])
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis("off")
ax.set_title("(c) Future work: re-establish TIS validity", fontsize=12)

steps = [
    ("1", "Method audit", "Re-derive correlation thresholds (0.6 / count\u22655) and\nthe 180-run completeness cut on post-2017 data; check\nwhether M-Lab server / website diversity shrank."),
    ("2", "Independent validation", "Cross-check TIS flags against ground truth: traceroute-based\nbottleneck detection, TCP BDP analysis, and ISP-reported\nspeed-tier shortfall on the initial segment."),
    ("3", "Discriminate last-mile vs middle-mile", "Compare correlation strength across path pairs that share\nonly the initial segment vs pairs sharing more of the path, to\nseparate true initial-segment tightness from middle-mile noise."),
    ("4", "Sensitivity & power", "Measure how TIS prevalence responds to the correlation and\ncount thresholds and to run-interval resolution (\u22482 h) \u2014\ndetermine if short-lived tightness is simply invisible."),
    ("5", "Re-run on 2018\u20132023", "Apply the validated detector to the years where TIS\u22610.\nA true zero would confirm the last mile decongested;\na non-zero result would attribute the gap to detector drift."),
]
y = 8.4
colors = ["#8e44ad", "#c0392b", "#2980b9", "#16a085", "#7f3f98"]
for i, (num, title, body) in enumerate(steps):
    col = colors[i]
    circle = plt.Circle((0.75, y + 0.15), 0.45, fc=col, ec="white", lw=1.5, zorder=5)
    ax.add_patch(circle)
    ax.text(0.75, y + 0.15, num, ha="center", va="center", fontsize=12,
            fontweight="bold", color="white", zorder=6)
    ax.text(1.5, y + 0.75, title, fontsize=11, fontweight="bold", va="center", color=col)
    ax.text(1.5, y - 0.35, body, fontsize=8.3, va="top", color="#333")
    if i < len(steps) - 1:
        arr = FancyArrowPatch((0.75, y - 0.05), (0.75, y - 1.55),
                              arrowstyle="-|>", mutation_scale=18, color="#999", lw=1.6)
        ax.add_patch(arr)
    y -= 1.95

# ---------- Bottom takeaway banner ----------
tb = FancyBboxPatch((0.3, 0.15), 9.4, 0.85, boxstyle="round,pad=0.1",
                    fc="#eafaf1", ec="#1e8449", lw=1.4)
ax.add_patch(tb)
ax.text(5.0, 0.58, "Goal: determine whether the 2011 finding (last-mile congestion) is a real era that ended,\n"
                   "or a measurement blind spot that we have yet to rule out \u2014 before trusting the 13-year decline.",
        ha="center", va="center", fontsize=9.5, color="#1e8449", fontweight="bold")

fig.suptitle("TIS validity: the 2011 localization result must be re-validated before it can be extended to today",
             fontsize=13, y=0.995)
fig.savefig(os.path.join(OUT, "fig_tis_validity_future_work.png"), bbox_inches="tight")
plt.close(fig)
print("Wrote fig_tis_validity_future_work.png")
