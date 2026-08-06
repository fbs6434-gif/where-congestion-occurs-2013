import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "savefig.dpi": 300,
})

FIG = "/home/jovyan/work/project/paper/figures/internet_model_2010s_vs_2020s.png"

BLUE = "#348ABD"
CABLE = "#E24A33"
GREY = "#777777"
LIGHT = "#F2F2F2"
DGREY = "#555555"

registry = []
pending_leaders = []


def box(ax, x, y, w, h, text, fc="#FFFFFF", ec="#333333", fs=10, lw=1.4):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.02",
                       fc=fc, ec=ec, lw=lw, mutation_aspect=1)
    ax.add_patch(p)
    t = ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color="#111111", linespacing=1.35)
    registry.append((ax, p, t, None))
    return p


def user(ax, x, y):
    c = Circle((x, y), 0.018, fc=DGREY, ec="none")
    ax.add_patch(c)
    r = Rectangle((x - 0.018, y - 0.045), 0.036, 0.028, fc=DGREY, ec="none")
    ax.add_patch(r)


def arrow(ax, x1, y1, x2, y2, color="#333333", lw=2.0, style="-|>", ls="-"):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=16,
                        color=color, lw=lw, linestyle=ls, shrinkA=0, shrinkB=0)
    ax.add_patch(a)
    registry.append((ax, None, None, a))
    return a


def annotate(ax, x, y, text, target=None, fs=10, color="#333", **kw):
    """Text placed at (x, y); leader line is drawn later from the top edge of
    the text to target so it never crosses the label."""
    kw.setdefault("ha", "center")
    kw.setdefault("va", "center")
    t = ax.text(x, y, text, fontsize=fs, color=color, **kw)
    registry.append((ax, None, t, None))
    if target is not None:
        pending_leaders.append((ax, t, target, color))
    return t


def main():
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.2))
    for ax in axes:
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    # ------------------------------------------------------------------
    # LEFT PANEL - early 2010s
    # ------------------------------------------------------------------
    ax = axes[0]
    ax.set_title("Early 2010s\nhierarchical, transit-routed", fontsize=13, fontweight="bold", pad=12)

    box(ax, 0.27, 0.76, 0.46, 0.10, "Centralized content\n(datacenters, origin servers)", fs=10, fc=LIGHT)
    box(ax, 0.05, 0.58, 0.90, 0.10, "Tier-1 transit backbone", fs=10, fc=LIGHT)
    box(ax, 0.05, 0.40, 0.90, 0.10, "Regional / metro networks", fs=10, fc=LIGHT)
    box(ax, 0.05, 0.22, 0.90, 0.12, "Access ISP - last mile\n(cable / DSL plant)", fs=10, fc="#FDE7E3", ec=CABLE, lw=2.0)

    arrow(ax, 0.50, 0.34, 0.50, 0.40)
    arrow(ax, 0.50, 0.50, 0.50, 0.58)
    arrow(ax, 0.50, 0.68, 0.50, 0.76)

    for ux in (0.25, 0.75):
        user(ax, ux, 0.10)
        arrow(ax, ux, 0.11, ux, 0.22, color=CABLE, lw=2.4)

    annotate(ax, 0.50, 0.155, "bottleneck: the last mile", target=(0.50, 0.22),
             fs=9.5, color=CABLE, fontweight="bold")
    annotate(ax, 0.50, 0.015, "Every path climbs through transit to reach far-away content",
             ha="center", va="bottom", color=GREY, style="italic", fs=9)

    # ------------------------------------------------------------------
    # RIGHT PANEL - 2023+
    # ------------------------------------------------------------------
    ax = axes[1]
    ax.set_title("2023+\nflat, CDN / hyperscaler-centric", fontsize=13, fontweight="bold", pad=12)

    box(ax, 0.08, 0.60, 0.36, 0.28, "Content from the edge:\nCDN caches, cloud,\nhyperscalers\n(anycast + geo-distributed)", fs=9, fc="#E9F2FA", ec=BLUE, lw=1.8)
    box(ax, 0.55, 0.60, 0.37, 0.26, "Internet exchange (IXP)\ndeep peering, off-net content", fs=9, fc="#E9F2FA", ec=BLUE, lw=1.8)
    arrow(ax, 0.44, 0.73, 0.55, 0.73, color=BLUE, lw=2.0)

    box(ax, 0.08, 0.33, 0.47, 0.14, "Upgraded access\n(fiber / DOCSIS 3.1)", fs=9.5, fc="#E7F4EB", ec="#2E8B57", lw=1.8)
    box(ax, 0.62, 0.33, 0.30, 0.14, "Legacy DSL\ncopper", fs=9.5, fc="#FDE7E3", ec=CABLE, lw=1.8)

    arrow(ax, 0.32, 0.47, 0.32, 0.60, color="#2E8B57", lw=2.2)
    arrow(ax, 0.74, 0.47, 0.74, 0.60, color=CABLE, lw=2.2, ls=":")

    for ux in (0.25, 0.75):
        user(ax, ux, 0.10)
        arrow(ax, ux, 0.11, ux, 0.33, color="#2E8B57", lw=2.0)

    annotate(ax, 0.50, 0.19, "congestion moved here:\nlegacy copper + interconnection",
             target=(0.70, 0.33), fs=9.5, color=CABLE, fontweight="bold")
    annotate(ax, 0.50, 0.015, "Content pushed to the edge - short, peered paths, transit bypassed",
             ha="center", va="bottom", color=GREY, style="italic", fs=9)

    fig.suptitle("Two models of the Internet: where the latency lives", fontsize=14, fontweight="bold", y=1.02)

    # ======================= draw leader lines ========================
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    for (ax_, t, target, color) in pending_leaders:
        bb = t.get_window_extent(renderer)
        inv = ax_.transData.inverted()
        x0, y0 = inv.transform((bb.x0, bb.y0))
        x1, y1 = inv.transform((bb.x1, bb.y1))
        # start at top-center of the text, nudge up a touch to clear the glyphs
        sx, sy = (x0 + x1) / 2, y1 + 0.012
        arrow(ax_, sx, sy, target[0], target[1], color=color, lw=1.2, style="-")

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
    boxes = [(ax_, p) for ax_, p, t, a in registry if p is not None]
    texts = [(ax_, t) for ax_, p, t, a in registry if t is not None]
    arrows = [(ax_, a) for ax_, p, t, a in registry if a is not None]

    def owning_box(ax_, t):
        # the box whose center contains the text center
        tx, ty = t.get_position()
        for (ax2, p) in boxes:
            if ax2 is not ax_:
                continue
            bx, by = p.get_x(), p.get_y()
            bw, bh = p.get_width(), p.get_height()
            if bx <= tx <= bx + bw and by <= ty <= by + bh:
                return p
        return None

    for (ax_, t) in texts:
        tr = t_rect(t, 2)
        owner = owning_box(ax_, t)
        for (ax2, p) in boxes:
            if ax2 is not ax_ or p is owner:
                continue
            if overlap(tr, r_rect(p)):
                problems.append(f"TEXT OVER BOX #{0 if ax_ is axes[0] else 1}: '{t.get_text()[:34]}'")

    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            ax1, t1 = texts[i]
            ax2, t2 = texts[j]
            if ax1 is not ax2:
                continue
            if overlap(t_rect(t1, 2), t_rect(t2, 2)):
                problems.append(f"TEXT-TEXT #{0 if ax1 is axes[0] else 1}: '{t1.get_text()[:26]}' vs '{t2.get_text()[:26]}'")

    for (ax_, a) in arrows:
        path = a.get_path()
        verts = a.get_patch_transform().transform(path.vertices)
        for (ax2, t) in texts:
            if ax2 is not ax_:
                continue
            tr = t_rect(t, 4)
            hit = any(tr[0] <= vx <= tr[2] and tr[1] <= vy <= tr[3] for vx, vy in verts[::2])
            if hit:
                problems.append(f"ARROW THROUGH TEXT #{0 if ax_ is axes[0] else 1}: '{t.get_text()[:26]}'")

    if problems:
        print("OVERLAP PROBLEMS:")
        for p_ in sorted(set(problems)):
            print("  -", p_)
    else:
        print("No overlaps detected.")

    plt.savefig(FIG)
    print("saved", FIG)


if __name__ == "__main__":
    main()
