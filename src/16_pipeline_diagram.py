import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

OUT = "output/figures"
os.makedirs(OUT, exist_ok=True)

C_SRC = "#d6e4f0"
C_ING = "#fde8cd"
C_CORE = "#e6f2d9"
C_ANA = "#e8ddf2"
C_OUT = "#f2d9d9"

XLIM, YLIM = 0, 14
FIG_W, FIG_H = 13.5, 12.5

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, XLIM)
ax.set_ylim(0, YLIM)
ax.axis("off")

# registry for overlap checking: (artist, "text"|"box", tag)
registry = []


def line_h(fs):
    # approximate data-units height of one text line (generous)
    return fs * 2.0 / 72.0 * (YLIM / FIG_H)


def box(x, y, w, h, lines, fc, ec="#444", lw=1.3):
    """lines: list of (text, fs, weight, color). Text is vertically centered."""
    p = FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                       boxstyle="round,pad=0.08", fc=fc, ec=ec, lw=lw, zorder=3)
    ax.add_patch(p)
    registry.append((p, "box", lines[0][0][:28], None))
    total = sum(line_h(fs) for _, fs, _, _ in lines)
    cur = y + total / 2
    for text, fs, weight, color in lines:
        style = "italic" if "italic" in str(weight) else "normal"
        weight = "normal" if "italic" in str(weight) else weight
        t = ax.text(x, cur, text, ha="center", va="center", fontsize=fs,
                    weight=weight, style=style, color=color, zorder=4, linespacing=2.0)
        registry.append((t, "text", text[:28], p))
        cur -= line_h(fs)


def arrow(x1, y1, x2, y2, lw=1.6, color="#555", ls="-"):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=16,
                        lw=lw, color=color, linestyle=ls, zorder=2)
    ax.add_patch(a)
    registry.append((a, "arrow", "", None))


# ============================ Stage A: source ============================
box(5, 12.6, 9.2, 1.15, [
    ("FCC Measuring Broadband America (MBA) archives  \u2022  2011\u20132023", 11, "bold", "#111"),
    ("one month of measurements per year  \u2022  ~4,000\u20135,700 US broadband units  \u2022  TCP + Web downloads",
     8.5, "normal", "#333"),
], C_SRC)

arrow(5, 12.0, 5, 11.15)

# ============================ Stage B: download ============================
box(5, 10.6, 9.2, 1.15, [
    ("Download & extract per year  \u2014  process_year.sh / 00_download.py", 10.5, "bold", "#111"),
    ("tar \u2192 curr_httpgetmt.csv (TCP throughput)  +  curr_webget.csv (Web)  +  unit_metadata.csv",
     8.5, "normal", "#333"),
], C_ING)

arrow(5, 10.0, 5, 9.5)
arrow(5, 10.0, 3.0, 9.45)
arrow(5, 10.0, 7.0, 9.45)

# ============================ Stage C: ingest ============================
box(3.0, 8.6, 3.7, 1.7, [
    ("01b_load_raw.py", 9.5, "bold", "#111"),
    ("Raw-unit ingest", 9, "normal", "#111"),
    ("schema-aware parse, inline", 8, "normal", "#333"),
    ("header-strip, 0-byte guard", 8, "normal", "#333"),
    ("Reproduction track (all units)", 7.8, "italic", "#8a5a00"),
], C_ING)

box(7.0, 8.6, 3.7, 1.7, [
    ("02_load_and_filter.py", 9.5, "bold", "#111"),
    ("02_raw_meta.py", 9.5, "bold", "#111"),
    ("Metadata + unit filtering", 9, "normal", "#111"),
    ("validated-unit set", 8, "normal", "#333"),
    ("Cross-check track (full metadata)", 7.8, "italic", "#2c5a8a"),
], C_ING)

arrow(3.0, 7.7, 4.2, 7.4)
arrow(7.0, 7.7, 5.8, 7.4)

# ============================ Stage D: per-year core ============================
box(5, 6.7, 9.2, 1.4, [
    ("Per-year core pipeline (runs for every year 2011\u20132023)", 10.5, "bold", "#111"),
    ("03_detect_speed_tier \u2192 04_align_time_series \u2192 05_compute_rc \u2192 06_compute_tis",
     9, "normal", "#111"),
    ("07_aggregate \u2192 08_plot", 9, "normal", "#111"),
], C_CORE)

arrow(5, 6.0, 2.1, 5.0)
arrow(5, 6.0, 5.0, 5.0)
arrow(5, 6.0, 7.9, 5.0)

# ============================ Stage E: cross-year ============================
box(2.1, 4.5, 2.9, 1.0, [
    ("09_compare_years.py", 9, "bold", "#111"),
    ("12-year trend analysis", 8.5, "normal", "#111"),
    ("RC%, TIS% by year/tech/ISP", 7.8, "normal", "#333"),
], C_ANA)

box(5.0, 4.5, 2.9, 1.0, [
    ("13_compare_raw_validated.py", 9, "bold", "#111"),
    ("Raw vs validated", 8.5, "normal", "#111"),
    ("comparison, 2011\u20132023", 7.8, "normal", "#333"),
], C_ANA)

box(7.9, 4.5, 2.9, 1.0, [
    ("10/11 TIS validation", 9, "bold", "#111"),
    ("validate_tis.py + plots", 8.5, "normal", "#111"),
    ("independent TIS check", 7.8, "normal", "#333"),
], C_ANA)

arrow(2.1, 4.0, 3.8, 3.4)
arrow(5.0, 4.0, 5.0, 3.4)
arrow(7.9, 4.0, 6.2, 3.4)

# ============================ Stage F: synthesis ============================
box(5, 2.9, 9.2, 1.1, [
    ("15_era_comparison.py  +  paper figures", 10.5, "bold", "#111"),
    ("2011 model vs 2023 model  \u2022  speed tiers  \u2022  RC/TIS over time  \u2022  provider shift",
     8.5, "normal", "#333"),
    ("findings: cable congestion 9\u00d7 drop, DSL persists, TIS vanishes post-2017",
     8, "italic", "#4a2c6a"),
], C_ANA)

arrow(5, 2.35, 5, 1.45)

# ============================ Stage G: outputs ============================
box(5, 0.85, 9.2, 1.1, [
    ("Outputs  \u2192  output/ figures + tables", 10.5, "bold", "#111"),
    ("upload_to_s3.py \u2192 S3 (chi.tacc.chameleoncloud.org/mba-data) + github repo",
     8.5, "normal", "#333"),
    ("large data \u2192 remote object storage (.env); code + figures \u2192 git",
     8, "italic", "#8a2c2c"),
], C_OUT)

fig.suptitle("Reproduction & 12-year trend analysis pipeline (2011\u20132023)",
             fontsize=14, weight="bold", y=0.99)
fig.subplots_adjust(left=0.02, right=0.98, top=0.97, bottom=0.02)

# ============================ overlap check ============================
fig.canvas.draw()
renderer = fig.canvas.get_renderer()

def t_rect(t, pad=0):
    bb = t.get_window_extent(renderer)
    return (bb.x0 - pad, bb.y0 - pad, bb.x1 + pad, bb.y1 + pad)

def r_rect(p):
    bb = p.get_window_extent(renderer)
    return (bb.x0, bb.y0, bb.x1, bb.y1)

def overlap(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])

problems = []

texts = [(t, tag, owner) for t, kind, tag, owner in registry if kind == "text"]
boxes_ = [(p, tag) for p, kind, tag, _ in registry if kind == "box"]
arrows_ = [(a, tag) for a, kind, tag, _ in registry if kind == "arrow"]

for t, tag, owner in texts:
    tr = t_rect(t)
    for p, btag in boxes_:
        if p is owner:
            continue  # text is allowed inside its own box
        if overlap(tr, r_rect(p)):
            problems.append(f"TEXT OUTSIDE/OVER BOX: '{tag}' vs box '{btag}'")

# pairwise text overlap
for i in range(len(texts)):
    for j in range(i + 1, len(texts)):
        t1, tag1, o1 = texts[i]
        t2, tag2, o2 = texts[j]
        if overlap(t_rect(t1, 1), t_rect(t2, 1)):
            problems.append(f"TEXT-TEXT OVERLAP: '{tag1}' vs '{tag2}'")

# arrow vs text
for a, atag in arrows_:
    path = a.get_path()
    verts = a.get_patch_transform().transform(path.vertices)
    for t, tag, _ in texts:
        tr = t_rect(t, 2)
        hit = False
        for vx, vy in verts[::2]:
            if tr[0] <= vx <= tr[2] and tr[1] <= vy <= tr[3]:
                hit = True
                break
        if hit:
            problems.append(f"ARROW THROUGH TEXT: '{tag}'")

if problems:
    print("OVERLAP PROBLEMS:")
    for p in sorted(set(problems)):
        print("  -", p)
else:
    print("No overlaps detected.")

out = f"{OUT}/fig_pipeline.png"
fig.savefig(out, dpi=150)
plt.close(fig)
print("Wrote", out)
