"""
Generate Figures 3-7 from the paper.
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from config import DATA_DIR, MONTHS, OUTPUT_DIR

sns.set_theme(style="whitegrid")
COLORS = ["#4c72b0", "#55a868", "#c44e52", "#8172b2"]

def bar_chart(data, x_col, y_col, hue_col, title, ylabel, fname):
    plt.figure(figsize=(10, 5))
    sns.barplot(data=data, x=x_col, y=y_col, hue=hue_col, palette=COLORS)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xlabel("ISP")
    plt.legend(title="Month")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "figures", fname), dpi=150)
    plt.close()
    print(f"Saved {fname}")

def main():
    os.makedirs(os.path.join(OUTPUT_DIR, "figures"), exist_ok=True)
    isp_agg = pd.read_parquet(os.path.join(DATA_DIR, "processed", "isp_agg.parquet"))
    meta = pd.read_parquet(os.path.join(DATA_DIR, "processed", "meta_valid.parquet"))
    rc = pd.read_parquet(os.path.join(DATA_DIR, "processed", "rc.parquet"))
    tis = pd.read_parquet(os.path.join(DATA_DIR, "processed", "tis.parquet"))

    merged = rc.merge(tis, on=["unit_id", "month"]).merge(
        meta[["unit_id", "isp", "technology"]], on="unit_id"
    )

    for tech, label in [("cable", "Cable"), ("dsl", "DSL")]:
        sub = isp_agg[isp_agg["technology"] == label.lower()].copy()
        sub["ISP"] = "ISP " + sub["isp"].astype(str)
        sub["Month"] = sub["month"].str.capitalize()

        bar_chart(sub, "ISP", "TIS%", "Month",
                  f"TIS Prevalence by {label} ISP",
                  "TIS (%)", f"fig{3 if label == 'Cable' else 4}_TIS_{label.lower()}.png")

    for tech, label, num in [("cable", "Cable", 6), ("dsl", "DSL", 7)]:
        sub = isp_agg[isp_agg["technology"] == label.lower()].copy()
        sub["ISP"] = "ISP " + sub["isp"].astype(int).astype(str)
        sub["Month"] = sub["month"].str.capitalize()

        bar_chart(sub, "ISP", "RC%", "Month",
                  f"RC Prevalence by {label} ISP",
                  "RC (%)", f"fig{num}_RC_{label.lower()}.png")

    fig5_data = []
    for (isp, tech, month), grp in merged.groupby(["isp", "technology", "month"]):
        N = len(grp)
        rc_pct = grp["rc"].mean() * 100
        tis_pct = grp["tis"].mean() * 100
        fig5_data.append({
            "ISP": isp, "Technology": tech, "Month": month,
            "RC%": rc_pct, "TIS%": tis_pct
        })
    fig5_df = pd.DataFrame(fig5_data)

    plt.figure(figsize=(8, 6))
    for tech, color, marker in [("dsl", "blue", "o"), ("cable", "red", "s")]:
        sub = fig5_df[fig5_df["Technology"] == tech]
        plt.scatter(sub["TIS%"], sub["RC%"], c=color, marker=marker,
                    label=tech.upper(), alpha=0.6, edgecolors="black")
    plt.xlabel("TIS (%)")
    plt.ylabel("RC (%)")
    plt.title("TIS vs RC Prevalence by ISP per Month")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "figures", "fig5_scatter.png"), dpi=150)
    plt.close()
    print("Saved fig5_scatter.png")

if __name__ == "__main__":
    main()
