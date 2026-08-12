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
FIG_W, FIG_H = 22, 9.5

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
    registry.append((p, "box", lines[0][0][:28], None, (x - w / 2 - 0.08, y - h / 2 - 0.08, w + 0.16, h + 0.16)))
    total = sum(line_h(fs) for _, fs, _, _ in lines)
    cur = y + total / 2
    for text, fs, weight, color in lines:
        style = "italic" if "italic" in str(weight) else "normal"
        weight = "normal" if "italic" in str(weight) else weight
        t = ax.text(x, cur, text, ha="center", va="center", fontsize=fs,
                    weight=weight, style=style, color=color, zorder=4, linespacing=1.8)
        registry.append((t, "text", text[:28], p, None))
        cur -= line_h(fs)


def arrow(x1, y1, x2, y2, lw=2.0, color="#555", ls="-", rad=0.0):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=18,
                        lw=lw, color=color, linestyle=ls, zorder=2,
                        connectionstyle=f"arc3,rad={rad}")
    ax.add_patch(a)
    registry.append((a, "arrow", "", None, None))


# ============================ Stage A: source ============================
box(1.5, 5.0, 2.9, 5.2, [
    ("FCC MBA archives", 13, "bold", "#111"),
    ("2011", 13, "bold", "#111"),
    ("four months (March\u2013June)", 10, "normal", "#333"),
    ("raw + validated tarballs", 9.5, "normal", "#333"),
    ("TCP + Web downloads", 9.5, "normal", "#333"),
], C_SRC)

arrow(2.95, 5.0, 3.05, 5.0)

# ============================ Stage B: download ============================
box(4.25, 5.0, 2.4, 5.2, [
    ("Download & extract", 13, "bold", "#111"),
    ("per year", 13, "bold", "#111"),
    ("process_year.sh /", 10.5, "normal", "#111"),
    ("00_download.py", 10.5, "normal", "#111"),
    ("tar \u2192 TCP + Web CSVs", 10, "normal", "#333"),
    ("+ unit metadata", 10, "normal", "#333"),
], C_ING)

arrow(5.45, 5.5, 5.9, 7.0, rad=-0.15)
arrow(5.45, 4.5, 5.9, 3.0, rad=0.15)

# ============================ Stage C: ingest (two tracks) ============================
box(7.1, 7.0, 2.5, 3.4, [
    ("01b_load_raw.py", 11, "bold", "#111"),
    ("Raw-unit ingest", 10.5, "normal", "#111"),
    ("schema-aware parse,", 9.5, "normal", "#333"),
    ("inline header-strip,", 9.5, "normal", "#333"),
    ("0-byte guard", 9.5, "normal", "#333"),
    ("(all raw units)", 9, "italic", "#8a5a00"),
], C_ING)

box(7.1, 3.0, 2.5, 3.4, [
    ("02_load_and_filter.py", 11, "bold", "#111"),
    ("02_raw_meta.py", 11, "bold", "#111"),
    ("Metadata + unit", 10.5, "normal", "#111"),
    ("filtering", 10.5, "normal", "#111"),
    ("validated-unit set", 9.5, "normal", "#333"),
    ("(validated tarball)", 9, "italic", "#2c5a8a"),
], C_ING)

arrow(8.35, 7.0, 8.75, 6.4, rad=0.15)
arrow(8.35, 3.0, 8.75, 3.6, rad=-0.15)

# ============================ Stage D: per-year core ============================
box(10.15, 5.0, 2.8, 5.8, [
    ("Per-year core pipeline", 12, "bold", "#111"),
    ("(runs every year)", 10, "normal", "#333"),
    ("03_detect_speed_tier", 10.5, "normal", "#111"),
    ("04_align_time_series", 10.5, "normal", "#111"),
    ("05_compute_rc", 10.5, "normal", "#111"),
    ("06_compute_tis", 10.5, "normal", "#111"),
    ("07_aggregate", 10.5, "normal", "#111"),
], C_CORE)

arrow(11.55, 5.0, 12.0, 5.0)

# ============================ Stage E: outputs ============================
box(15.5, 5.0, 2.6, 5.2, [
    ("Reproduction outputs", 12.5, "bold", "#111"),
    ("figures + tables", 10.5, "normal", "#333"),
    ("RC%, TIS% by", 9.5, "normal", "#333"),
    ("technology / ISP", 9.5, "normal", "#333"),
    ("March 2011", 9.5, "normal", "#333"),
], C_OUT)

arrow(12.1, 5.0, 14.15, 5.0)

fig.suptitle("Reproduction pipeline: Genin & Splett (2013) on 2011 FCC/SamKnows data",
             fontsize=17, weight="bold", y=0.97)
fig.subplots_adjust(left=0.02, right=0.98, top=0.93, bottom=0.02)

# ============================ overlap check ============================
fig.canvas.draw()
renderer = fig.canvas.get_renderer()

def t_rect(t, pad=0):
    bb = t.get_window_extent(renderer)
    return (bb.x0 - pad, bb.y0 - pad, bb.x1 + pad, bb.y1 + pad)

def r_rect(p, tag):
    bx0, by0, bw, bh = tag
    disp = ax.transData.transform([(bx0, by0), (bx0 + bw, by0 + bh)])
    return (disp[0][0], disp[0][1], disp[1][0], disp[1][1])

def overlap(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])

problems = []

texts = [(t, tag, owner) for t, kind, tag, owner, _ in registry if kind == "text"]
boxes_ = [(p, tag, rect) for p, kind, tag, _, rect in registry if kind == "box"]
arrows_ = [(a, tag) for a, kind, tag, _, _ in registry if kind == "arrow"]

for t, tag, owner in texts:
    if not tag:
        continue
    tr = t_rect(t)
    if owner is not None:
        for p, btag, rect in boxes_:
            if p is owner:
                bx0, by0, bx1, by1 = r_rect(p, rect)
                if not (bx0 <= tr[0] and bx1 >= tr[2] and by0 <= tr[1] and by1 >= tr[3]):
                    problems.append(f"TEXT EXCEEDS OWN BOX: '{tag}'")
                break
    for p, btag, rect in boxes_:
        if p is owner:
            continue
        if overlap(tr, r_rect(p, rect)):
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
        if any(tr[0] <= vx <= tr[2] and tr[1] <= vy <= tr[3] for vx, vy in verts[::2]):
            problems.append(f"ARROW THROUGH TEXT: '{tag}'")

if problems:
    print("OVERLAP PROBLEMS:")
    for p in sorted(set(problems)):
        print("  -", p)
else:
    print("No overlaps detected.")

out = f"{OUT}/fig_pipeline_reproduction.png"
fig.savefig(out, dpi=150)
plt.close(fig)
print("Wrote", out)