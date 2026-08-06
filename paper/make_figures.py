import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = "/home/jovyan/work/project"
FIG = os.path.join(BASE, "paper", "figures")
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

CABLE = "#E24A33"
DSL = "#348ABD"
FIBER = "#2E8B57"
SATELLITE = "#9370DB"

# Load validated-era per-year overall and per-tech aggregates
def load_years():
    c = pd.read_csv(os.path.join(BASE, "data", "validated_backup", "compare", "tables", "comparison_overall.csv"))
    t = pd.read_csv(os.path.join(BASE, "data", "validated_backup", "compare", "tables", "comparison_by_tech.csv"))
    return c, t

def load_raw_vs_valid():
    return pd.read_csv(os.path.join(BASE, "output", "compare_raw_validated", "tables", "comparison_pivot.csv"))

def fig1_overall_trend(c):
    fig, ax1 = plt.subplots(figsize=(7.5, 4.2))
    ax1.plot(c["year"], c["RC%"], color=CABLE, marker="o", lw=2.2, ms=7, label="Recurrent congestion (RC)")
    ax1.plot(c["year"], c["TIS%"], color=DSL, marker="s", lw=2.2, ms=7, label="Tight initial segment (TIS)")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Prevalence (%)")
    ax1.set_title("Overall congestion prevalence, 2011–2023 (validated fleet)", fontweight="bold")
    ax1.set_xticks(c["year"])
    ax1.legend(frameon=True)
    ax1.axvspan(2017.5, 2023.5, color="#DDDDDD", alpha=0.5, zorder=0)
    ax1.text(2020.25, ax1.get_ylim()[1] * 0.95, "website-set change →\nTIS detector silent",
             ha="center", va="top", fontsize=8, color="#555555")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.grid(True, alpha=0.3)
    plt.tight_layout()
    out = os.path.join(FIG, "fig1_overall_trend.png")
    plt.savefig(out); plt.close()
    print("saved", out)

def fig2_rc_by_tech(t):
    techs = [("cable", CABLE), ("dsl", DSL), ("fiber", FIBER)]
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    for tech, c in techs:
        sub = t[t["technology"] == tech].sort_values("year")
        ax.plot(sub["year"], sub["RC%"], color=c, marker="o", lw=2.2, ms=6, label=tech.capitalize())
    ax.set_xlabel("Year")
    ax.set_ylabel("RC prevalence (%)")
    ax.set_title("Recurrent congestion by technology, 2011–2023", fontweight="bold")
    ax.set_xticks(sorted(t["year"].unique()))
    ax.legend(frameon=True)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out = os.path.join(FIG, "fig2_rc_by_tech.png")
    plt.savefig(out); plt.close()
    print("saved", out)

def fig3_tis_by_tech(t):
    techs = [("cable", CABLE), ("dsl", DSL), ("fiber", FIBER)]
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    for tech, c in techs:
        sub = t[t["technology"] == tech].sort_values("year")
        ax.plot(sub["year"], sub["TIS%"], color=c, marker="o", lw=2.2, ms=6, label=tech.capitalize())
    ax.set_xlabel("Year")
    ax.set_ylabel("TIS prevalence (%)")
    ax.set_title("Tight initial segment by technology, 2011–2023", fontweight="bold")
    ax.set_xticks(sorted(t["year"].unique()))
    ax.legend(frameon=True)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out = os.path.join(FIG, "fig3_tis_by_tech.png")
    plt.savefig(out); plt.close()
    print("saved", out)

def fig4_rc_by_isp():
    agg = []
    for y in range(2011, 2024):
        fp = os.path.join(BASE, "data", "validated_backup", "processed", str(y), "isp_agg.parquet")
        if os.path.isfile(fp):
            df = pd.read_parquet(fp)
            df["year"] = y
            agg.append(df)
    df = pd.concat(agg, ignore_index=True)
    df = df[df["technology"] == "cable"]
    isp = df.groupby("isp")["N"].sum().sort_values(ascending=False).head(10).index
    fig, ax = plt.subplots(figsize=(8.5, 5))
    for name in isp:
        sub = df[df["isp"] == name].sort_values("year")
        ax.plot(sub["year"], sub["RC%"], marker="o", ms=5, lw=1.8, label=name)
    ax.set_xlabel("Year"); ax.set_ylabel("RC prevalence (%)")
    ax.set_title("Cable recurrent congestion by ISP, 2011–2023", fontweight="bold")
    ax.set_xticks(sorted(df["year"].unique()))
    ax.legend(frameon=True, fontsize=8, ncol=2)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out = os.path.join(FIG, "fig4_rc_by_isp.png")
    plt.savefig(out); plt.close()
    print("saved", out)

def fig5_raw_vs_valid(rv):
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.plot(rv["year"], rv["raw_RC%"], color=CABLE, marker="o", lw=2.2, ms=7, label="Raw fleet")
    ax.plot(rv["year"], rv["validated_RC%"], color=DSL, marker="s", lw=2.2, ms=7, label="Validated fleet")
    ax.set_xlabel("Year"); ax.set_ylabel("RC prevalence (%)")
    ax.set_title("RC prevalence: full raw fleet vs. validated subset", fontweight="bold")
    ax.set_xticks(rv["year"].dropna().astype(int))
    ax.legend(frameon=True)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out = os.path.join(FIG, "fig5_raw_vs_valid.png")
    plt.savefig(out); plt.close()
    print("saved", out)

def fig6_fleet_size():
    years = []; ns = []
    for y in range(2011, 2024):
        fp = os.path.join(BASE, "data", "validated_backup", "processed", str(y), "isp_agg.parquet")
        if os.path.isfile(fp):
            df = pd.read_parquet(fp)
            years.append(y); ns.append(int(df["N"].sum()))
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax.bar(years, ns, color="#666666", width=0.7)
    ax.set_xlabel("Year"); ax.set_ylabel("Validated units")
    ax.set_title("FCC MBA validated fleet size over time", fontweight="bold")
    ax.set_xticks(years)
    for x, v in zip(years, ns):
        ax.text(x, v + 150, f"{v:,}", ha="center", fontsize=8)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    out = os.path.join(FIG, "fig6_fleet_size.png")
    plt.savefig(out); plt.close()
    print("saved", out)

def fig7_2011_vs_2023():
    # RC% by tech, 2011 vs 2023, grouped bar
    t = pd.read_csv(os.path.join(BASE, "data", "validated_backup", "compare", "tables", "comparison_by_tech.csv"))
    y2011 = t[(t["year"] == 2011) & (t["technology"].isin(["cable", "dsl"]))].set_index("technology")
    y2023 = t[(t["year"] == 2023) & (t["technology"].isin(["cable", "dsl", "fiber"]))].set_index("technology")
    techs = ["cable", "dsl", "fiber"]
    v11 = [y2011.loc[tech, "RC%"] if tech in y2011.index else np.nan for tech in techs]
    v23 = [y2023.loc[tech, "RC%"] if tech in y2023.index else np.nan for tech in techs]
    x = np.arange(len(techs)); w = 0.35
    fig, ax = plt.subplots(figsize=(6.5, 4))
    ax.bar(x - w/2, v11, w, color=CABLE, label="2011", edgecolor="black", linewidth=0.5)
    ax.bar(x + w/2, v23, w, color=DSL, label="2023", edgecolor="black", linewidth=0.5)
    for xi, vi, ci in zip(x - w/2, v11, ["%s" for _ in techs]):
        if not np.isnan(vi): ax.text(xi, vi + 0.3, f"{vi:.1f}", ha="center", fontsize=9)
    for xi, vi in zip(x + w/2, v23):
        if not np.isnan(vi): ax.text(xi, vi + 0.3, f"{vi:.1f}", ha="center", fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels([t.capitalize() for t in techs])
    ax.set_ylabel("RC prevalence (%)")
    ax.set_title("Recurrent congestion: 2011 vs 2023", fontweight="bold")
    ax.legend(frameon=True)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    out = os.path.join(FIG, "fig7_2011_vs_2023.png")
    plt.savefig(out); plt.close()
    print("saved", out)

if __name__ == "__main__":
    c, t = load_years()
    fig1_overall_trend(c)
    fig2_rc_by_tech(t)
    fig3_tis_by_tech(t)
    fig4_rc_by_isp()
    rv = load_raw_vs_valid()
    fig5_raw_vs_valid(rv)
    fig6_fleet_size()
    fig7_2011_vs_2023()
    print("All paper figures done.")
