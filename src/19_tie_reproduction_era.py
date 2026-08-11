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

TECHS = ["cable", "dsl", "fiber"]
TECH_LABEL = {"cable": "Cable", "dsl": "DSL", "fiber": "Fiber"}
COLORS = {"cable": "#c0392b", "dsl": "#2980b9", "fiber": "#27ae60"}
YEARS = list(range(2011, 2024))

# ---- Reproduction: per-month RC% for Mar-Jun 2011 (from 2011_{month} data) ----
MONTHS = ["March", "April", "May", "June"]
rep_rows = []
for ml in MONTHS:
    mk = ml.lower()
    m = pd.read_parquet(f"data/processed/2011_{mk}/meta_valid.parquet")[["unit_id", "technology"]]
    r = pd.read_parquet(f"data/processed/2011_{mk}/rc.parquet")[["unit_id", "rc"]]
    u = m.merge(r, on="unit_id")
    row = {"month": ml, "overall": 100 * u["rc"].mean()}
    for t in ["cable", "dsl"]:
        row[t] = 100 * u[u["technology"] == t]["rc"].mean()
    rep_rows.append(row)
rep = pd.DataFrame(rep_rows)
x_rep = np.arange(len(MONTHS))

# ---- Era: 13-year RC% by tech + DSL share of congestion ----
era_rows = []
for y in YEARS:
    base = f"data/processed/{y}"
    mv, rc = os.path.join(base, "meta_valid.parquet"), os.path.join(base, "rc.parquet")
    if not (os.path.exists(mv) and os.path.exists(rc)):
        continue
    m = pd.read_parquet(mv)[["unit_id", "technology"]].drop_duplicates("unit_id")
    r = pd.read_parquet(rc)[["unit_id", "rc"]].drop_duplicates("unit_id")
    u = m.merge(r, on="unit_id")
    row = {"year": y, "overall": 100 * u["rc"].mean(), "n_rc": int(u["rc"].sum())}
    for t in TECHS:
        s = u[u["technology"] == t]
        row[f"rc_{t}"] = int(s["rc"].sum())
        row[f"n_{t}"] = len(s)
        row[f"rcpct_{t}"] = 100 * s["rc"].mean() if len(s) else np.nan
    era_rows.append(row)
era = pd.DataFrame(era_rows)
a = pd.read_parquet("data/processed/2023/isp_agg.parquet")
g = a.groupby("technology").agg(N=("N", "sum"), RC=("RC", "sum"))
row23 = {"year": 2023, "overall": 100 * g["RC"].sum() / g["N"].sum(), "n_rc": int(g["RC"].sum())}
for t in TECHS:
    row23[f"rc_{t}"] = int(g.loc[t, "RC"]) if t in g.index else 0
    row23[f"n_{t}"] = int(g.loc[t, "N"]) if t in g.index else 0
    row23[f"rcpct_{t}"] = 100 * g.loc[t, "RC"] / g.loc[t, "N"] if t in g.index else np.nan
era = pd.concat([era, pd.DataFrame([row23])], ignore_index=True)
era["dsl_share"] = 100 * era["rc_dsl"] / era["n_rc"]

fig = plt.figure(figsize=(14, 9))
gs = fig.add_gridspec(2, 2, hspace=0.5, wspace=0.22)

# ---- Panel (a): 2011 reproduction, monthly RC% cable vs DSL ----
ax = fig.add_subplot(gs[0, 0])
w = 0.32
ax.bar(x_rep - w / 2, rep["cable"], w, color=COLORS["cable"], label="Cable")
ax.bar(x_rep + w / 2, rep["dsl"], w, color=COLORS["dsl"], label="DSL")
for i, (c, d) in enumerate(zip(rep["cable"], rep["dsl"])):
    ax.text(i - w / 2, c + 0.6, f"{c:.1f}%", ha="center", fontsize=8, color=COLORS["cable"])
    ax.text(i + w / 2, d + 0.6, f"{d:.1f}%", ha="center", fontsize=8, color=COLORS["dsl"])
ax.set_xticks(x_rep)
ax.set_xticklabels(rep["month"])
ax.set_ylabel("Congested units (%)")
ax.set_ylim(0, 30)
ax.set_title("(a) 2011 reproduction: RC% by month\n(Genin & Splett method, this work)")
ax.legend(frameon=False)
ax.grid(axis="y", alpha=0.3)

# ---- Panel (b): 13-year overall decline with the reproduction embedded ----
ax = fig.add_subplot(gs[0, 1])
ax.plot(era["year"], era["overall"], "-o", color="#7f3f98", lw=2.5, ms=6, label="Annual overall RC% (this work)")
ax.scatter([2011] * len(x_rep), rep["overall"], marker="x", s=80, color="#000000", zorder=6,
           label="2011 reproduction months")
for x, v in era["overall"].items():
    ax.annotate(f"{v:.1f}", (era["year"][x], v), textcoords="offset points", xytext=(0, 7),
                ha="center", fontsize=8, color="#7f3f98")
ax.axhline(0, color="#95a5a6", lw=0.8)
ax.set_xticks(YEARS)
ax.set_xlabel("Year")
ax.set_ylabel("Congested units (%)")
ax.set_ylim(0, 19)
ax.set_title("(b) 13-year trend: overall congestion collapses")
ax.legend(frameon=False, loc="upper right")
ax.grid(axis="y", alpha=0.3)
ax.annotate("17.0% \u2192 4.6%\n(\u22484\u00d7 decline)", xy=(2020, 5.5), xytext=(2013.2, 13.5),
            fontsize=9, arrowprops=dict(arrowstyle="->", lw=1.2), color="#7f3f98")

# ---- Panel (c): RC% by technology over 13 years ----
ax = fig.add_subplot(gs[1, 0])
for t in ["cable", "dsl", "fiber"]:
    col = f"rcpct_{t}"
    ax.plot(era["year"], era[col], "-o", color=COLORS[t], lw=2.5, ms=6, label=TECH_LABEL[t])
for t in ["cable", "dsl", "fiber"]:
    col = f"rcpct_{t}"
    for x, v in era[col].items():
        if pd.isna(v):
            continue
        ax.annotate(f"{v:.0f}", (era["year"][x], v), textcoords="offset points", xytext=(0, 6),
                    ha="center", fontsize=6.5, color=COLORS[t])
ax.axhline(0, color="#95a5a6", lw=0.8)
ax.set_xticks(YEARS)
ax.set_xlabel("Year")
ax.set_ylabel("Congested units (%)")
ax.set_ylim(0, 28)
ax.set_title("(c) By technology: cable collapses, DSL copper persists")
ax.legend(frameon=False, loc="upper right")
ax.grid(axis="y", alpha=0.3)

# ---- Panel (d): DSL share of all remaining congestion ----
ax = fig.add_subplot(gs[1, 1])
ax.plot(era["year"], era["dsl_share"], "-o", color="#2980b9", lw=3, ms=7)
ax.fill_between(era["year"], era["dsl_share"], alpha=0.15, color="#2980b9")
for x, v in era["dsl_share"].items():
    ax.annotate(f"{v:.0f}%", (era["year"][x], v), textcoords="offset points", xytext=(0, 8),
                ha="center", fontsize=8, color="#2980b9")
ax.axhline(0, color="#95a5a6", lw=0.8)
ax.set_xticks(YEARS)
ax.set_xlabel("Year")
ax.set_ylabel("Share of congested units (%)")
ax.set_ylim(0, 100)
ax.set_title("(d) The residual congestion concentrates in DSL copper")
ax.grid(axis="y", alpha=0.3)
ax.annotate("2011: 17%\n2023: 82%", xy=(2023, 82), xytext=(2014, 70),
            fontsize=9, arrowprops=dict(arrowstyle="->", lw=1.2), color="#2980b9")

fig.suptitle("Tying the 2011 reproduction to the 13-year trend: the Internet got less congested,\n"
             "and what remains sits in DSL copper", fontsize=13, y=0.99)
fig.savefig(os.path.join(OUT, "fig_reproduction_to_era_13yr.png"), bbox_inches="tight")
plt.close(fig)
print("Wrote fig_reproduction_to_era_13yr.png")
