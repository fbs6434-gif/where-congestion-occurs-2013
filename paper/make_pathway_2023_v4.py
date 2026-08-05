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

FIG = "/home/jovyan/work/project/paper/figures/internet_pathway_2023_v4.png"

RED = "#E24A33"
BLUE = "#348ABD"
GREEN = "#2E8B57"
DGREY = "#444444"
LIGHT = "#F6F6F6"
EDGE = "#333333"

def box(ax, x, y, w, h, text, fc=LIGHT, ec=EDGE, fs=8.5, lw=1.3, tc="#111111"):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.015",
                       fc=fc, ec=ec, lw=lw, mutation_aspect=1)
    ax.add_patch(p)
    if text:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
                color=tc, linespacing=1.4)
    return p

def arrow(ax, x1, y1, x2, y2, color=EDGE, lw=2.4, ms=16):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=ms,
                        color=color, lw=lw, shrinkA=0, shrinkB=0)
    ax.add_patch(a)

def cache(ax, x, y, w, h, label):
    box(ax, x, y, w, h, "", fc="#DFF0DF", ec=GREEN, lw=1.5)
    for i in range(3):
        ax.add_line(matplotlib.lines.Line2D(
            [x + 0.08 * w, x + 0.92 * w], [y + h * (0.30 + 0.20 * i)] * 2,
            color=GREEN, lw=1.0))
    ax.text(x + w / 2, y + h - 0.055, label, ha="center", va="top", fontsize=6.5,
            color=GREEN, fontweight="bold")

def home(ax, x, y, h):
    w = 0.11
    box(ax, x, y, w, h, "", fc="#FBFBFB", ec=EDGE, lw=1.2)
    s = 0.035
    hx, hy = x + 0.012, y + h / 2 - 0.06
    ax.add_patch(Rectangle((hx, hy), 1.5 * s, 1.1 * s, fc="#DDDDDD", ec=EDGE, lw=1.1))
    ax.add_patch(Polygon([(hx - 0.2 * s, hy + 1.1 * s), (hx + 0.75 * s, hy + 1.1 * s),
                          (hx + 0.75 * s, hy + 1.7 * s), (hx + 0.48 * s, hy + 2.0 * s),
                          (hx + 0.30 * s, hy + 1.72 * s), (hx - 0.2 * s, hy + 1.72 * s)],
                         closed=True, fc="#C9C9C9", ec=EDGE, lw=1.1))
    ax.text(hx + 0.95 * s + 0.015, y + h / 2, "home", ha="left", va="center",
            fontsize=8, color=DGREY)

def main():
    fig, ax = plt.subplots(figsize=(12.5, 3.0))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    y0, h = 0.30, 0.44
    xc0, xc1 = 0.015, 0.195   # content
    xi0, xi1 = 0.225, 0.395   # IXP
    xs0, xs1 = 0.425, 0.665   # ISP
    xl0, xl1 = 0.695, 0.865   # last mile (parent)
    xh0, xh1 = 0.885, 0.995   # home
    ym = y0 + h / 2

    # main boxes
    box(ax, xc0, y0, xc1 - xc0, h, "Content\nCDN edge caches,\ncloud, hyperscalers",
        fc="#E9F2FA", ec=BLUE)
    box(ax, xi0, y0, xi1 - xi0, h, "Internet\nexchange (IXP)\ndirect peering",
        fc="#E9F2FA", ec=BLUE)
    box(ax, xs0, y0, xs1 - xs0, h, "ISP network", fc="#E9F2FA", ec=BLUE)
    cache(ax, 0.50, 0.43, 0.115, 0.16, "off-net CDN cache")

    # last mile: single parent box, two labeled sub-regions
    box(ax, xl0, y0, xl1 - xl0, h, "", fc="#FBFBFB", ec=EDGE, lw=1.3)
    ax.text((xl0 + xl1) / 2, y0 + h + 0.02, "last mile", ha="center", va="bottom",
            fontsize=9, color=DGREY, fontstyle="italic")
    box(ax, xl0 + 0.01, y0 + 0.03, 0.085, h - 0.06, "fiber\nDOCSIS 3.1",
        fc="#E7F4EB", ec=GREEN, fs=7.5)
    box(ax, xl1 - 0.095, y0 + 0.03, 0.085, h - 0.06, "legacy DSL\ncopper",
        fc="#FDE7E3", ec=RED, fs=7.5, lw=2.0)

    home(ax, xh0, y0, h)

    # path arrows only in gaps, no line crosses any box
    arrow(ax, xc1 + 0.004, ym, xi0 - 0.004, ym, color=GREEN)
    arrow(ax, xi1 + 0.004, ym, xs0 - 0.004, ym, color=GREEN)
    arrow(ax, xs1 + 0.004, ym, xl0 - 0.004, ym, color=GREEN)
    arrow(ax, xl1 + 0.004, ym, xh0 - 0.004, ym, color=GREEN)

    # congestion: red star at the interconnection, red border on copper
    ax.add_patch(Polygon([(xi1 - 0.006, ym + 0.075), (xi1 - 0.002, ym + 0.055),
                          (xi1 + 0.002, ym + 0.075), (xi1 + 0.006, ym + 0.055),
                          (xi1 - 0.006, ym + 0.045), (xi1 + 0.006, ym + 0.045)],
                         closed=True, fc=RED, ec="none"))

    plt.savefig(FIG)
    print("saved", FIG)

if __name__ == "__main__":
    main()
