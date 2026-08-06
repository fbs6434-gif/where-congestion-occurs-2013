import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import os

OUT = "output/era_comparison"
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

TECHS = ["cable", "dsl", "fiber"]
TECH_LABEL = {"cable": "Cable", "dsl": "DSL", "fiber": "Fiber"}
COLORS = {"cable": "#c0392b", "dsl": "#2980b9", "fiber": "#27ae60"}
YEARS = list(range(2011, 2024))

speed_rows = []
rc_rows = []
for y in YEARS:
    mv = f"data/processed/{y}/meta_valid.parquet"
    rc = f"data/processed/{y}/rc.parquet"
    if os.path.exists(mv):
        m = pd.read_parquet(mv)
        for tech in TECHS:
            sub = m[m["technology"] == tech]
            if len(sub):
                speed_rows.append({"year": y, "tech": tech, "tier": sub["speed_tier"].median()})
    if os.path.exists(mv) and os.path.exists(rc):
        m = pd.read_parquet(mv)
        r = pd.read_parquet(rc)[["unit_id", "rc"]]
        m2 = m.merge(r, on="unit_id", how="left")
        m2["rc"] = m2["rc"].fillna(False)
        for tech in TECHS:
            sub = m2[m2["technology"] == tech]
            if len(sub):
                rc_rows.append({"year": y, "tech": tech, "rc": 100 * sub["rc"].mean()})

speed = pd.DataFrame(speed_rows)
rc = pd.DataFrame(rc_rows)

pivot = pd.read_csv("output/compare_raw_validated/tables/comparison_pivot.csv")
pivot = pivot.sort_values("year")

# ---------------- Figure 1: Speed tier growth ----------------
fig, ax = plt.subplots(figsize=(7, 4.4))
for tech in TECHS:
    sub = speed[speed["tech"] == tech].sort_values("year")
    ax.plot(sub["year"], sub["tier"], "-o", color=COLORS[tech], label=TECH_LABEL[tech], ms=4, lw=2)
all_speed = speed.groupby("year")["tier"].median().reset_index()
ax.plot(all_speed["year"], all_speed["tier"], "--", color="#7f8c8d", lw=2.5, label="All technologies")
ax.set_yscale("log")
ax.set_yticks([1, 2, 5, 10, 20, 50, 100, 200, 500])
ax.get_yaxis().set_major_formatter(mticker.ScalarFormatter())
ax.set_ylim(1, 800)
ax.set_xlabel("Year")
ax.set_ylabel("Median advertised download tier (Mbps, log scale)")
ax.set_title("The capacity model: median speed tier by technology, 2011-2022")
ax.legend(frameon=False, loc="upper left")
ax.annotate("Cable 17 \u2192 236 Mbps\n(+13.9x)", xy=(2022, 236), xytext=(2014.5, 300),
            arrowprops=dict(arrowstyle="->", lw=1), fontsize=9)
ax.annotate("DSL 3.0 \u2192 16 Mbps\n(+5.4x)", xy=(2022, 16), xytext=(2015, 9),
            arrowprops=dict(arrowstyle="->", lw=1), fontsize=9)
fig.tight_layout()
fig.savefig(f"{OUT}/fig_era_speed_tiers.png", dpi=150)
plt.close(fig)

# ---------------- Figure 2: RC% by technology 2011 vs 2023 ----------------
fig, ax = plt.subplots(figsize=(7, 4.4))
y_2011 = rc[(rc["year"] == 2011)]
y_2023 = pd.DataFrame({
    "tech": TECHS,
    "rc": [2.67, 6.59, 0.75],
})
x = range(len(TECHS))
w = 0.35
ax.bar([i - w / 2 for i in x], y_2011["rc"], w, color="#d35400", label="2011 (original study)")
ax.bar([i + w / 2 for i in x], y_2023["rc"], w, color="#1a7f8a", label="2023 (this work)")
ax.set_xticks(list(x))
ax.set_xticklabels([TECH_LABEL[t] for t in TECHS])
ax.set_ylabel("Congested units (%)")
ax.set_title("Where congestion lives: RC% by technology, 2011 vs 2023")
ax.legend(frameon=False)
for i, t in enumerate(TECHS):
    v11 = y_2011[y_2011["tech"] == t]["rc"].iloc[0]
    v23 = y_2023[y_2023["tech"] == t]["rc"].iloc[0]
    ax.text(i - w / 2, v11 + 0.5, f"{v11:.1f}%", ha="center", fontsize=9)
    ax.text(i + w / 2, v23 + 0.5, f"{v23:.1f}%", ha="center", fontsize=9)
ax.set_ylim(0, 28)
ax.text(0.02, 0.95, "Cable congestion collapsed 9x;\nDSL remains the persistent legacy\nbottleneck", transform=ax.transAxes,
        fontsize=9, va="top", color="#333", bbox=dict(fc="#fdf3e7", ec="#d35400", lw=0.8))
fig.tight_layout()
fig.savefig(f"{OUT}/fig_era_rc_by_tech_2011_vs_2023.png", dpi=150)
plt.close(fig)

# ---------------- Figure 3: RC% and TIS% over time ----------------
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharex=True)
ax = axes[0]
ax.plot(pivot["year"], pivot["raw_RC%"], "-o", color="#c0392b", label="Raw units (reproduced)", ms=4, lw=2)
ax.plot(pivot["year"], pivot["validated_RC%"], "-s", color="#1a7f8a", label="Validated units", ms=4, lw=2)
ax.set_xlabel("Year")
ax.set_ylabel("Congested units (%)")
ax.set_title("Overall congestion (RC%)")
ax.legend(frameon=False)
ax.set_ylim(0, 20)

ax = axes[1]
ax.plot(pivot["year"], pivot["raw_TIS%"], "-o", color="#c0392b", label="Raw units (reproduced)", ms=4, lw=2)
ax.plot(pivot["year"], pivot["validated_TIS%"], "-s", color="#1a7f8a", label="Validated units", ms=4, lw=2)
ax.axhline(0, color="#95a5a6", lw=0.8)
ax.set_xlabel("Year")
ax.set_ylabel("Time-in-system congestion (%)")
ax.set_title("Initial-segment / middle-mile congestion (TIS%)")
ax.legend(frameon=False)
ax.set_ylim(-0.3, 3.0)
ax.annotate("Initial-segment congestion\ndisappears after 2017", xy=(2018, 0), xytext=(2013, 2.3),
            arrowprops=dict(arrowstyle="->", lw=1), fontsize=9)
fig.suptitle("The congestion model changed: RC collapses, TIS vanishes", y=1.02)
fig.tight_layout()
fig.savefig(f"{OUT}/fig_era_rc_tis_over_time.png", dpi=150)
plt.close(fig)

# ---------------- Figure 4: ISP shift 2011 vs 2023 ----------------
d11 = pd.read_parquet("data/processed/2011/isp_agg.parquet")
d23 = pd.read_parquet("data/processed/2023/isp_agg.parquet")

def norm(df):
    s = df.groupby("isp").agg(N=("N", "sum"), RC=("RC", "sum")).reset_index()
    s["RC%"] = 100 * s["RC"] / s["N"]
    return s.sort_values("RC%", ascending=False).head(8)

n11, n23 = norm(d11), norm(d23)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
ax = axes[0]
ax.barh(n11["isp"][::-1], n11["RC%"][::-1], color="#d35400")
ax.set_title("2011: most congested providers")
ax.set_xlabel("Congested units (%)")
ax.set_xlim(0, 60)
ax = axes[1]
ax.barh(n23["isp"][::-1], n23["RC%"][::-1], color="#1a7f8a")
ax.set_title("2023: most congested providers")
ax.set_xlabel("Congested units (%)")
ax.set_xlim(0, 60)
fig.suptitle("The congestion shifted from cable giants to legacy DSL providers", y=1.02)
fig.tight_layout()
fig.savefig(f"{OUT}/fig_era_isp_2011_vs_2023.png", dpi=150)
plt.close(fig)

print("Wrote:", sorted(os.listdir(OUT)))
