import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

OUT = "output/figures"
os.makedirs(OUT, exist_ok=True)

# Colors
C_SRC = "#d6e4f0"   # source / acquisition
C_ING = "#fde8cd"   # ingest
C_CORE = "#e6f2d9"  # per-year core
C_ANA = "#e8ddf2"   # cross-year analysis
C_OUT = "#f2d9d9"   # outputs

fig, ax = plt.subplots(figsize=(13.5, 11))
ax.set_xlim(0, 10)
ax.set_ylim(0, 13)
ax.axis("off")

def box(x, y, w, h, text, fc, fs=9.5, ec="#444", lw=1.3, weight="normal"):
    p = FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                       boxstyle="round,pad=0.08", fc=fc, ec=ec, lw=lw, zorder=3)
    ax.add_patch(p)
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, weight=weight,
            zorder=4, color="#111")
    return (x, y)

def arrow(x1, y1, x2, y2, lw=1.6, color="#555", style="-|>", ls="-", rad=0.0):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=16,
                        lw=lw, color=color, linestyle=ls, zorder=2, connectionstyle=f"arc3,rad={rad}")
    ax.add_patch(a)

def label(x, y, text, fs=8.5, color="#555", style="italic"):
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=color, style=style)

# ---------------- Stage A: source ----------------
box(5, 12.55, 8.6, 0.85,
    "FCC Measuring Broadband America (MBA) archives  \u2022  2011\u20132023  \u2022  one month of measurements per year",
    C_SRC, fs=11, weight="bold")
label(5, 12.0, "~4,000\u20135,700 US broadband units/year  \u2022  every unit runs TCP downloads + Web downloads to a set of endpoints")

arrow(5, 12.12, 5, 11.15)

# ---------------- Stage B: download & extract ----------------
box(5, 10.6, 8.6, 0.9,
    "Download & extract per year  \u2014  process_year.sh / 00_download.py",
    C_ING, fs=10.5, weight="bold")
label(5, 10.05, "tar \u2192 curr_httpgetmt.csv (TCP throughput)  +  curr_webget.csv (Web throughput)  +  unit_metadata.csv")

arrow(5, 10.15, 5, 9.15)

# ---------------- Stage C: ingest (two tracks) ----------------
box(3.0, 8.55, 3.4, 1.15,
    "01b_load_raw.py\nRaw-unit ingest\n(schema-aware parse, inline\nheader-strip, 0-byte guard)",
    C_ING, fs=9)
box(7.0, 8.55, 3.4, 1.15,
    "02_load_and_filter.py\n02_raw_meta.py\nMetadata + unit filtering\n(validated-unit set)",
    C_ING, fs=9)
label(3.0, 7.85, "Reproduction track\n(all available units)", fs=8.5, color="#8a5a00")
label(7.0, 7.85, "Cross-check track\n(units with full metadata)", fs=8.5, color="#2c5a8a")

arrow(5, 10.15, 3.0, 9.2)
arrow(5, 10.15, 7.0, 9.2)

# ---------------- Stage D: per-year core (shared) ----------------
arrow(3.0, 7.98, 4.2, 7.25)
arrow(7.0, 7.98, 5.8, 7.25)

box(5, 6.6, 8.6, 1.1,
    "Per-year core pipeline (runs for every year 2011\u20132023)\n03_detect_speed_tier \u2192 04_align_time_series \u2192 05_compute_rc \u2192\n06_compute_tis \u2192 07_aggregate \u2192 08_plot",
    C_CORE, fs=10, weight="bold")
label(5, 5.95, "Outputs per year: meta_valid.parquet \u2022 rc.parquet (RC flag) \u2022 tis.parquet (TIS flag) \u2022 isp_agg.parquet \u2022 figures",
      fs=8.5, color="#3a6a1a")

arrow(5, 6.05, 5, 5.05)

# ---------------- Stage E: cross-year analysis ----------------
box(2.1, 4.45, 2.9, 1.0,
    "09_compare_years.py\n12-year trend analysis\n(RC%, TIS% by year/tech/ISP)",
    C_ANA, fs=9)
box(5.0, 4.45, 2.9, 1.0,
    "13_compare_raw_validated.py\nRaw vs validated\ncomparison, 2011\u20132023",
    C_ANA, fs=9)
box(7.9, 4.45, 2.9, 1.0,
    "10_validate_tis.py\n11_plot_validation.py\nTIS validation + plots",
    C_ANA, fs=9)

arrow(5, 6.05, 2.1, 5.0)
arrow(5, 6.05, 5.0, 5.0)
arrow(5, 6.05, 7.9, 5.0)

# ---------------- Stage F: synthesis ----------------
arrow(2.1, 3.95, 3.8, 3.35)
arrow(5.0, 3.95, 5.0, 3.35)
arrow(7.9, 3.95, 6.2, 3.35)

box(5, 2.85, 8.6, 0.95,
    "15_era_comparison.py  +  paper figures\n2011 model vs 2023 model  \u2022  speed tiers  \u2022  RC/TIS over time  \u2022  provider shift",
    C_ANA, fs=10, weight="bold")
label(5, 2.3, "ANALYSIS.md \u00a74  \u2022  TRENDS.md  \u2022  README.md  (findings: cable congestion 9\u00d7 drop, DSL persists, TIS vanishes post-2017)",
      fs=8.5, color="#4a2c6a")

arrow(5, 2.35, 5, 1.35)

# ---------------- Stage G: outputs ----------------
box(5, 0.85, 8.6, 0.95,
    "Outputs  \u2192  output/ figures + tables\nupload_to_s3.py  \u2192  S3 (chi.tacc.chameleoncloud.org/mba-data)  +  github.com/fbs6434-gif/where-congestion-occurs-2013",
    C_OUT, fs=10, weight="bold")
label(5, 0.3, "All large data in remote object storage (.env credentials); code + figures in the git repo", fs=8.5, color="#8a2c2c")

fig.suptitle("Reproduction & 12-year trend analysis pipeline (2011\u20132023)", fontsize=14, weight="bold", y=0.985)
fig.tight_layout(rect=[0, 0, 1, 0.96])
out = f"{OUT}/fig_pipeline.png"
fig.savefig(out, dpi=150)
plt.close(fig)
print("Wrote", out)
