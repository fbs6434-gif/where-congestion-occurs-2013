import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
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

YEARS = list(range(2011, 2024))
TECHS = ["cable", "dsl", "fiber"]
TECH_LABEL = {"cable": "Cable", "dsl": "DSL", "fiber": "Fiber"}
COLORS = {"cable": "#c0392b", "dsl": "#2980b9", "fiber": "#27ae60"}

rows = []
for y in YEARS:
    base = f"data/processed/{y}"
    mv = os.path.join(base, "meta_valid.parquet")
    rc = os.path.join(base, "rc.parquet")
    tis = os.path.join(base, "tis.parquet")
    if not all(os.path.exists(p) for p in [mv, rc, tis]):
        continue
    m = pd.read_parquet(mv)[["unit_id", "isp", "technology", "speed_tier"]].drop_duplicates("unit_id")
    r = pd.read_parquet(rc)[["unit_id", "rc", "rc_fraction"]].drop_duplicates("unit_id")
    t = pd.read_parquet(tis)[["unit_id", "tis", "tis_high_corr_count"]].drop_duplicates("unit_id")
    u = m.merge(r, on="unit_id").merge(t, on="unit_id")
    row = {
        "year": y, "N": len(u),
        "RC%": 100 * u["rc"].mean(),
        "TIS%": 100 * u["tis"].mean(),
        "both%": 100 * ((u["rc"]) & (u["tis"])).mean(),
        "both_of_RC%": 100 * ((u["rc"]) & (u["tis"])).sum() / max(1, u["rc"].sum()),
        "median_tier": u["speed_tier"].median(),
        "n_isps": u["isp"].nunique(),
        "tech_mix": u["technology"].value_counts(normalize=True).to_dict(),
    }
    for tech in TECHS:
        sub = u[u["technology"] == tech]
        row[f"RC%_{tech}"] = 100 * sub["rc"].mean() if len(sub) else np.nan
        row[f"TIS%_{tech}"] = 100 * sub["tis"].mean() if len(sub) else np.nan
    rows.append(row)
df = pd.DataFrame(rows).set_index("year")

# Append 2023 (from isp_agg; TIS not measured -> 0)
a = pd.read_parquet("data/processed/2023/isp_agg.parquet")
g = a.groupby("technology").agg(N=("N", "sum"), RC=("RC", "sum"))
row23 = {"year": 2023, "N": a["N"].sum(), "RC%": 100 * g["RC"].sum() / g["N"].sum(),
         "TIS%": 0.0, "both%": 0.0, "both_of_RC%": 0.0, "median_tier": np.nan,
         "n_isps": a["isp"].nunique()}
for tech in TECHS:
    row23[f"RC%_{tech}"] = 100 * g.loc[tech, "RC"] / g.loc[tech, "N"] if tech in g.index else np.nan
    row23[f"TIS%_{tech}"] = 0.0
df.loc[2023] = row23

df.to_csv(os.path.join(OUT, "era_trends_metrics.csv"))

# ---------------- Figure: 13-year dashboard ----------------
fig = plt.figure(figsize=(14, 10))
gs = fig.add_gridspec(2, 2, hspace=0.45, wspace=0.22)

# Panel 1: RC% & TIS% overall, with values annotated
ax = fig.add_subplot(gs[0, 0])
ax.plot(df.index, df["RC%"], "-o", color="#c0392b", lw=2.5, ms=6, label="RC% (recurrent congestion)")
ax.plot(df.index, df["TIS%"], "-s", color="#8e44ad", lw=2.5, ms=6, label="TIS% (tight initial segment)")
for x, v in df["RC%"].items():
    ax.annotate(f"{v:.1f}", (x, v), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=7.5, color="#c0392b")
for x, v in df["TIS%"].items():
    ax.annotate(f"{v:.2f}", (x, v), textcoords="offset points", xytext=(0, -13), ha="center", fontsize=7.5, color="#8e44ad")
ax.axhline(0, color="#95a5a6", lw=0.8)
ax.set_xticks(YEARS)
ax.set_xlabel("Year")
ax.set_ylabel("Share of units (%)")
ax.set_title("(a) Overall congestion: RC% and TIS%, 2011\u20132023")
ax.legend(frameon=False, loc="upper right")
ax.set_ylim(-0.4, 19)

# Panel 2: RC% by technology with values
ax = fig.add_subplot(gs[0, 1])
for tech in TECHS:
    col = f"RC%_{tech}"
    ax.plot(df.index, df[col], "-o", color=COLORS[tech], lw=2.5, ms=6, label=TECH_LABEL[tech])
for tech in TECHS:
    col = f"RC%_{tech}"
    for x, v in df[col].items():
        if pd.isna(v):
            continue
        ax.annotate(f"{v:.1f}", (x, v), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=7, color=COLORS[tech])
ax.axhline(0, color="#95a5a6", lw=0.8)
ax.set_xticks(YEARS)
ax.set_xlabel("Year")
ax.set_ylabel("Congested units (%)")
ax.set_title("(b) RC% by technology, 2011\u20132023")
ax.legend(frameon=False, loc="upper right")
ax.set_ylim(0, 27)

# Panel 3: Capacity (median tier) + sample size on twin axis
ax = fig.add_subplot(gs[1, 0])
ax.plot(df.index, df["median_tier"], "-o", color="#16a085", lw=2.5, ms=6, label="Median speed tier (Mbps)")
for x, v in df["median_tier"].items():
    if pd.isna(v):
        continue
    ax.annotate(f"{v:.0f}", (x, v), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=7.5, color="#16a085")
ax.set_yscale("log")
ax.set_yticks([5, 10, 25, 50, 100])
ax.get_yaxis().set_major_formatter(mticker.ScalarFormatter())
ax.set_xticks(YEARS)
ax.set_xlabel("Year")
ax.set_ylabel("Median advertised tier (Mbps, log)")
ax.set_title("(c) Capacity growth vs sample size")
ax.legend(frameon=False, loc="upper left")
ax2 = ax.twinx()
ax2.bar(df.index, df["N"], alpha=0.18, color="#7f8c8d", width=0.7, label="Units analyzed")
ax2.set_ylabel("Units analyzed", color="#7f8c8d")
ax2.tick_params(axis="y", labelcolor="#7f8c8d")
ax2.set_ylim(0, 7000)

# Panel 4: both% and share of RC that is also TIS
ax = fig.add_subplot(gs[1, 1])
ax.plot(df.index, df["both_of_RC%"], "-o", color="#e67e22", lw=2.5, ms=6, label="RC\u2229TIS / RC (%)")
ax.plot(df.index, df["both%"], "-^", color="#95a5a6", lw=2.5, ms=6, label="RC\u2229TIS / all units (%)")
for x, v in df["both_of_RC%"].items():
    ax.annotate(f"{v:.0f}%", (x, v), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=7.5, color="#e67e22")
ax.axhline(0, color="#95a5a6", lw=0.8)
ax.set_xticks(YEARS)
ax.set_xlabel("Year")
ax.set_ylabel("Share of units (%)")
ax.set_title("(d) Where congestion sits: RC\u2229TIS overlap, 2011\u20132023")
ax.legend(frameon=False, loc="upper right")
ax.set_ylim(0, 15)
ax.annotate("Initial-segment signature\ndisappears after 2017",
            xy=(2018, 0), xytext=(2014.5, 11), fontsize=9,
            arrowprops=dict(arrowstyle="->", lw=1), color="#333")

fig.suptitle("13-year trend in Internet congestion (FCC SamKnows MBA data, 2011\u20132023)", fontsize=13, y=0.98)
fig.savefig(os.path.join(OUT, "fig_era_dashboard_13yr.png"), bbox_inches="tight")
plt.close(fig)
print("Wrote era_trends_metrics.csv and fig_era_dashboard_13yr.png")
