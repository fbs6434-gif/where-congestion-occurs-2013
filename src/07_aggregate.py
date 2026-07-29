import os
import pandas as pd
from config import PROCESSED_DIR, MONTHS, MONTH, OUTPUT_DIR, YEAR

def main():
    rc = pd.read_parquet(os.path.join(PROCESSED_DIR, "rc.parquet"))
    tis = pd.read_parquet(os.path.join(PROCESSED_DIR, "tis.parquet"))
    meta = pd.read_parquet(os.path.join(PROCESSED_DIR, "meta_valid.parquet"))

    merged = rc.merge(tis, on=["unit_id", "month"]).merge(
        meta[["unit_id", "isp", "technology"]], on="unit_id"
    )

    os.makedirs(os.path.join(OUTPUT_DIR, "tables"), exist_ok=True)

    tech_groups = list(merged["technology"].unique())
    for tech in tech_groups:
        sub = merged[merged["technology"].str.lower() == tech]
        N = len(sub)
        N_rc = sub["rc"].sum()
        N_tis = sub["tis"].sum()
        N_both = ((sub["rc"]) & (sub["tis"])).sum()
        rows = [{
            "Year": YEAR, "Month": MONTH.capitalize(),
            "Technology": tech.capitalize(),
            "Total": N, "RC": N_rc, "TIS": N_tis, "RC∩TIS": N_both,
            "RC∩TIS/TIS%": round(N_both / N_tis * 100, 1) if N_tis else 0,
            "RC∩TIS/RC%": round(N_both / N_rc * 100, 1) if N_rc else 0,
            "RC%": round(N_rc / N * 100, 1) if N else 0,
            "TIS%": round(N_tis / N * 100, 1) if N else 0,
        }]
        tbl = pd.DataFrame(rows)
        fname = f"table_{tech}.csv"
        tbl.to_csv(os.path.join(OUTPUT_DIR, "tables", fname), index=False)
        print(f"Saved {fname}")
        print(tbl.to_string(index=False))
        print()

    # Overall (all techs combined)
    N = len(merged)
    N_rc = merged["rc"].sum()
    N_tis = merged["tis"].sum()
    N_both = ((merged["rc"]) & (merged["tis"])).sum()
    rows = [{
        "Year": YEAR, "Month": MONTH.capitalize(),
        "Technology": "All",
        "Total": N, "RC": N_rc, "TIS": N_tis, "RC∩TIS": N_both,
        "RC∩TIS/TIS%": round(N_both / N_tis * 100, 1) if N_tis else 0,
        "RC∩TIS/RC%": round(N_both / N_rc * 100, 1) if N_rc else 0,
        "RC%": round(N_rc / N * 100, 1) if N else 0,
        "TIS%": round(N_tis / N * 100, 1) if N else 0,
    }]
    tbl = pd.DataFrame(rows)
    tbl.to_csv(os.path.join(OUTPUT_DIR, "tables", "table_overall.csv"), index=False)
    print("Saved table_overall.csv")
    print(tbl.to_string(index=False))
    print()

    # ISP-level breakdown
    isp_agg = merged.groupby(["isp", "technology"]).agg(
        N=("unit_id", "count"),
        RC=("rc", "sum"),
        TIS=("tis", "sum"),
    ).reset_index()
    isp_agg["RC%"] = (isp_agg["RC"] / isp_agg["N"] * 100).round(1)
    isp_agg["TIS%"] = (isp_agg["TIS"] / isp_agg["N"] * 100).round(1)
    isp_agg["year"] = YEAR
    isp_agg.to_parquet(os.path.join(PROCESSED_DIR, "isp_agg.parquet"))
    print("Saved isp_agg.parquet")

if __name__ == "__main__":
    main()
