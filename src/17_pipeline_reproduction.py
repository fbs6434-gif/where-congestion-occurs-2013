import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

OUT = "/home/jovyan/work/project/paper/figures"
os.makedirs(OUT, exist_ok=True)

C_SRC = "#d6e4f0"
C_ING = "#fde8cd"
C_CORE = "#e6f2d9"
C_OUT = "#f2d9d9"

XLIM, YLIM = 20, 10
FIG_W, FIG_H = 14, 4.2

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, XLIM)
ax.set_ylim(0, YLIM)
ax.axis("off")


def line_h(fs):
    return fs * 2.0 / 72.0 * (YLIM / FIG_H)


def box(x, y, w, h, lines, fc, ec="#444", lw=1.3):
    p = FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                       boxstyle="round,pad=0.08", fc=fc, ec=ec, lw=lw, zorder=3)
    ax.add_patch(p)
    total = sum(line_h(fs) for _, fs, _, _ in lines)
    cur = y + total / 2
    for text, fs, weight, color in lines:
        style = "italic" if "italic" in str(weight) else "normal"
        weight = "normal" if "italic" in str(weight) else weight
        ax.text(x, cur, text, ha="center", va="center", fontsize=fs,
                weight=weight, style=style, color=color, zorder=4, linespacing=1.8)
        cur -= line_h(fs)


def arrow(x1, y1, x2, y2, lw=2.0, color="#555", rad=0.0):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=18,
                        lw=lw, color=color, zorder=2,
                        connectionstyle=f"arc3,rad={rad}")
    ax.add_patch(a)


# ===== Stage A: source =====
box(1.9, 5.0, 3.0, 5.4, [
    ("FCC MBA archives", 13, "bold", "#111"),
    ("2011", 13, "bold", "#111"),
    ("four months (March\u2013June)", 10, "normal", "#333"),
    ("raw + validated tarballs", 9.5, "normal", "#333"),
    ("TCP benchmark + 10 websites", 9.5, "normal", "#333"),
], C_SRC)

arrow(3.45, 5.0, 3.55, 5.0)

# ===== Stage B: download =====
box(4.7, 5.0, 2.3, 4.4, [
    ("Download & extract", 12, "bold", "#111"),
    ("00_download.py", 10.5, "normal", "#111"),
    ("tar \u2192 TCP + Web CSVs", 9.5, "normal", "#333"),
    ("+ unit metadata", 9.5, "normal", "#333"),
], C_ING)

arrow(5.85, 5.0, 6.15, 5.0)

# ===== Stage C: ingest =====
box(7.55, 5.0, 2.7, 4.8, [
    ("Ingest raw + validated", 11.5, "bold", "#111"),
    ("01b_load_raw.py", 10, "normal", "#111"),
    ("02_load_and_filter.py", 10, "normal", "#111"),
    ("schema-aware parse,", 9.5, "normal", "#333"),
    ("unit completeness filter", 9.5, "normal", "#333"),
], C_ING)

arrow(8.95, 5.0, 9.35, 5.0)

# ===== Stage D: core pipeline =====
box(11.1, 5.0, 3.0, 6.2, [
    ("Core reproduction pipeline", 12, "bold", "#111"),
    ("(per unit-month)", 9.5, "italic", "#333"),
    ("03 detect speed tier", 10, "normal", "#111"),
    ("04 align benchmark \u2194 sites", 10, "normal", "#111"),
    ("05 recurrent congestion (RC)", 10, "normal", "#111"),
    ("06 tight initial segment (TIS)", 10, "normal", "#111"),
    ("07 aggregate", 10, "normal", "#111"),
], C_CORE)

arrow(12.65, 5.0, 13.05, 5.0)

# ===== Stage E: outputs =====
box(14.4, 5.0, 2.7, 4.6, [
    ("Reproduction outputs", 12, "bold", "#111"),
    ("RC%, TIS% by", 10, "normal", "#111"),
    ("technology / ISP", 10, "normal", "#111"),
    ("March 2011 tables", 9.5, "normal", "#333"),
    ("+ figures", 9.5, "normal", "#333"),
], C_OUT)

fig.suptitle("Reproduction pipeline: Genin & Splett (2013) on 2011 FCC/SamKnows data",
             fontsize=13, weight="bold", y=0.98)
fig.subplots_adjust(left=0.02, right=0.98, top=0.90, bottom=0.02)

out = f"{OUT}/fig_pipeline_reproduction.png"
fig.savefig(out, dpi=200)
plt.close(fig)
print("Wrote", out)