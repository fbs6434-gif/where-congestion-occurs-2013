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

XLIM, YLIM = 17.5, 10
FIG_W, FIG_H = 19, 8.5

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, XLIM)
ax.set_ylim(0, YLIM)
ax.axis("off")

registry = []


def line_h(fs):
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
                    weight=weight, style=style, color=color, zorder=4, linespacing=1.8)
        registry.append((t, "text", text[:28], p))
        cur -= line_h(fs)


def arrow(x1, y1, x2, y2, lw=1.6, color="#555", ls="-", rad=0.0):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=16,
                        lw=lw, color=color, linestyle=ls, zorder=2,
                        connectionstyle=f"arc3,rad={rad}")
    ax.add_patch(a)
    registry.append((a, "arrow", "", None))


# ============================ Stage A: source ============================
box(1.2, 5.0, 2.0, 4.6, [
    ("FCC MBA archives", 10.5, "bold", "#111"),
    ("2011\u20132023", 10.5, "bold", "#111"),
    ("one month of measurements", 8, "normal", "#333"),
    ("per year", 8, "normal", "#333"),
    ("~4,000\u20135,700 units/yr", 7.8, "normal", "#333"),
    ("TCP + Web downloads", 7.8, "normal", "#333"),
], C_SRC)

arrow(2.2, 5.0, 2.4, 5.0)

# ============================ Stage B: download ============================
box(3.4, 5.0, 2.0, 4.6, [
    ("Download & extract", 10.5, "bold", "#111"),
    ("per year", 10.5, "bold", "#111"),
    ("process_year.sh /", 8.5, "normal", "#333"),
    ("00_download.py", 8.5, "normal", "#333"),
    ("tar \u2192 TCP + Web CSVs", 8, "normal", "#333"),
    ("+ unit metadata", 8, "normal", "#333"),
], C_ING)

arrow(4.4, 5.4, 4.9, 6.9, rad=-0.15)
arrow(4.4, 4.6, 4.9, 3.1, rad=0.15)

# ============================ Stage C: ingest (two tracks) ============================
box(5.9, 6.9, 2.0, 2.9, [
    ("01b_load_raw.py", 9, "bold", "#111"),
    ("Raw-unit ingest", 8.5, "normal", "#111"),
    ("schema-aware parse,", 7.5, "normal", "#333"),
    ("inline header-strip,", 7.5, "normal", "#333"),
    ("0-byte guard", 7.5, "normal", "#333"),
    ("Reproduction track", 7, "italic", "#8a5a00"),
    ("(all units)", 7, "italic", "#8a5a00"),
], C_ING)

box(5.9, 3.1, 2.0, 2.9, [
    ("02_load_and_filter.py", 9, "bold", "#111"),
    ("02_raw_meta.py", 9, "bold", "#111"),
    ("Metadata + unit", 8.5, "normal", "#111"),
    ("filtering", 8.5, "normal", "#111"),
    ("validated-unit set", 7.5, "normal", "#333"),
    ("Cross-check track", 7, "italic", "#2c5a8a"),
    ("(full metadata)", 7, "italic", "#2c5a8a"),
], C_ING)

arrow(6.9, 6.9, 7.45, 6.3, rad=0.15)
arrow(6.9, 3.1, 7.45, 3.7, rad=-0.15)

# ============================ Stage D: per-year core ============================
box(8.6, 5.0, 2.3, 5.4, [
    ("Per-year core pipeline", 10, "bold", "#111"),
    ("(runs every year)", 8, "normal", "#333"),
    ("03_detect_speed_tier", 8.5, "normal", "#111"),
    ("04_align_time_series", 8.5, "normal", "#111"),
    ("05_compute_rc", 8.5, "normal", "#111"),
    ("06_compute_tis", 8.5, "normal", "#111"),
    ("07_aggregate \u2192 08_plot", 8.5, "normal", "#111"),
], C_CORE)

arrow(9.75, 6.3, 10.5, 7.5, rad=0.1)
arrow(9.75, 5.0, 10.5, 5.0)
arrow(9.75, 3.7, 10.5, 2.5, rad=-0.1)

# ============================ Stage E: cross-year ============================
box(11.5, 7.5, 2.0, 2.1, [
    ("09_compare_years.py", 8.5, "bold", "#111"),
    ("12-year trend analysis", 8, "normal", "#111"),
    ("RC%, TIS% by year/tech/ISP", 7.2, "normal", "#333"),
], C_ANA)

box(11.5, 5.0, 2.0, 2.1, [
    ("13_compare_raw_validated.py", 8.5, "bold", "#111"),
    ("Raw vs validated", 8, "normal", "#111"),
    ("comparison, 2011\u20132023", 7.2, "normal", "#333"),
], C_ANA)

box(11.5, 2.5, 2.0, 2.1, [
    ("10/11 TIS validation", 8.5, "bold", "#111"),
    ("validate_tis.py", 8, "normal", "#111"),
    ("independent TIS check", 7.2, "normal", "#333"),
], C_ANA)

arrow(12.5, 7.5, 13.0, 6.0, rad=-0.1)
arrow(12.5, 5.0, 13.0, 5.0)
arrow(12.5, 2.5, 13.0, 4.0, rad=0.1)

# ============================ Stage F: synthesis ============================
box(13.8, 5.0, 1.6, 4.2, [
    ("15_era_", 9, "bold", "#111"),
    ("comparison.py", 9, "bold", "#111"),
    ("+ paper figures", 8.5, "normal", "#111"),
    ("2011 vs 2023 model", 7.5, "normal", "#333"),
    ("speed tiers, RC/TIS,", 7.2, "normal", "#333"),
    ("provider shift", 7.2, "normal", "#333"),
], C_ANA)

arrow(14.6, 5.0, 15.0, 5.0)

# ============================ Stage G: outputs ============================
box(16.0, 5.0, 2.0, 4.4, [
    ("Outputs", 10.5, "bold", "#111"),
    ("figures + tables", 8.5, "normal", "#333"),
    ("upload_to_s3.py \u2192 S3", 8, "normal", "#333"),
    ("chi.tacc.chameleoncloud.org", 7.5, "normal", "#333"),
    ("+ github repo", 8, "normal", "#333"),
], C_OUT)

fig.suptitle("Reproduction & 12-year trend analysis pipeline (2011\u20132023)",
             fontsize=15, weight="bold", y=0.97)
fig.subplots_adjust(left=0.02, right=0.98, top=0.93, bottom=0.02)

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
    if not tag:
        continue
    tr = t_rect(t)
    for p, btag in boxes_:
        if p is owner:
            continue
        if overlap(tr, r_rect(p)):
            problems.append(f"TEXT OUTSIDE/OVER BOX: '{tag}' vs box '{btag}'")

for i in range(len(texts)):
    for j in range(i + 1, len(texts)):
        t1, tag1, _ = texts[i]
        t2, tag2, _ = texts[j]
        if not tag1 or not tag2:
            continue
        if overlap(t_rect(t1, 1), t_rect(t2, 1)):
            problems.append(f"TEXT-TEXT OVERLAP: '{tag1}' vs '{tag2}'")

for a, atag in arrows_:
    path = a.get_path()
    verts = a.get_patch_transform().transform(path.vertices)
    for t, tag, _ in texts:
        if not tag:
            continue
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
