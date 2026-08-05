import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle, FancyArrowPatch

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

FIG = "/home/jovyan/work/project/paper/figures/internet_pathway_2023_v6.png"

RED = "#E24A33"
BLUE = "#348ABD"
GREEN = "#2E8B57"
DGREY = "#444444"
LIGHT = "#F6F6F6"
EDGE = "#333333"

def box(ax, x, y, w, h, text, fc=LIGHT, ec=EDGE, fs=8.5, lw=1.3, tc="#111111",
        alpha=1.0, z=3):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.015",
                       fc=fc, ec=ec, lw=lw, mutation_aspect=1, alpha=alpha, zorder=z)
    ax.add_patch(p)
    if text:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
                color=tc, linespacing=1.4, zorder=z + 1)
    return p

def arrow(ax, x1, y1, x2, y2, color=EDGE, lw=2.4, ms=16):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=ms,
                        color=color, lw=lw, shrinkA=0, shrinkB=0, zorder=5)
    ax.add_patch(a)

def star(ax, cx, cy, R, r, color=RED, z=6):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = R if i % 2 == 0 else r
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    ax.add_patch(Polygon(pts, closed=True, fc=color, ec="none", zorder=z))

def home(ax, x, y, h, w=0.11):
    box(ax, x, y, w, h, "", fc="#FBFBFB", ec=EDGE, lw=1.2)
    s = 0.035
    hx, hy = x + 0.012, y + h / 2 - 0.06
    ax.add_patch(Rectangle((hx, hy), 1.5 * s, 1.1 * s, fc="#DDDDDD", ec=EDGE, lw=1.1, zorder=4))
    ax.add_patch(Polygon([(hx - 0.2 * s, hy + 1.1 * s), (hx + 0.75 * s, hy + 1.1 * s),
                          (hx + 0.75 * s, hy + 1.7 * s), (hx + 0.48 * s, hy + 2.0 * s),
                          (hx + 0.30 * s, hy + 1.72 * s), (hx - 0.2 * s, hy + 1.72 * s)],
                         closed=True, fc="#C9C9C9", ec=EDGE, lw=1.1, zorder=4))
    ax.text(hx + 0.95 * s + 0.015, y + h / 2, "home", ha="left", va="center",
            fontsize=8, color=DGREY)

def main():
    fig, ax = plt.subplots(figsize=(12.5, 3.0))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    y0, h = 0.30, 0.44
    xc0, xc1 = 0.015, 0.195   # content
    xi0, xi1 = 0.225, 0.395   # IXP
    xs0, xs1 = 0.425, 0.665   # ISP
    xl0, xl1 = 0.695, 0.855   # last mile (parent)
    xh0, xh1 = 0.90, 0.995    # home
    ym = y0 + h / 2

    # main boxes
    box(ax, xc0, y0, xc1 - xc0, h, "Content\nCDN edge caches,\ncloud, hyperscalers",
        fc="#E9F2FA", ec=BLUE)
    box(ax, xi0, y0, xi1 - xi0, h, "Internet\nexchange (IXP)\ndirect peering",
        fc="#E9F2FA", ec=BLUE)
    box(ax, xs0, y0, xs1 - xs0, h, "", fc="#E9F2FA", ec=BLUE)

    # ISP: label (bottom) and off-net cache (top), no overlap
    ax.text((xs0 + xs1) / 2, y0 + 0.075, "ISP network", ha="center", va="bottom",
            fontsize=10, color="#111111")
    box(ax, 0.47, 0.52, 0.15, 0.16, "CDN cache\n(off-net)", fc="#DFF0DF",
        ec=GREEN, fs=8, lw=1.5)

    # last mile: fiber and legacy DSL overlapping as a clean blended layer
    box(ax, xl0, y0, xl1 - xl0, h, "", fc="#FBFBFB", ec=EDGE, lw=1.3)
    ax.text((xl0 + xl1) / 2, y0 + h + 0.02, "last mile", ha="center", va="bottom",
            fontsize=9, color=DGREY, fontstyle="italic")
    box(ax, 0.705, y0 + 0.03, 0.095, h - 0.06, "fiber\nDOCSIS 3.1",
        fc="#E7F4EB", ec=GREEN, fs=7.5, alpha=0.8, z=2)
    box(ax, 0.770, y0 + 0.03, 0.075, h - 0.06, "legacy DSL\ncopper",
        fc="#FDE7E3", ec=RED, fs=7.5, lw=2.0, alpha=0.8, z=2)

    home(ax, xh0, y0, h, w=0.095)

    # path arrows only in gaps
    arrow(ax, xc1 + 0.004, ym, xi0 - 0.004, ym, color=GREEN)
    arrow(ax, xi1 + 0.004, ym, xs0 - 0.004, ym, color=GREEN)
    arrow(ax, xs1 + 0.004, ym, xl0 - 0.004, ym, color=GREEN)
    arrow(ax, xl1 + 0.004, ym, xh0 - 0.004, ym, color=GREEN)

    # congestion cued only by the red copper border

    plt.savefig(FIG)
    print("saved", FIG)

if __name__ == "__main__":
    main()
