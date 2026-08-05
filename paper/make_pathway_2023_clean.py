import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle, FancyArrowPatch
from matplotlib.lines import Line2D

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

FIG = "/home/jovyan/work/project/paper/figures/internet_pathway_2023_clean.png"

RED = "#E24A33"
BLUE = "#348ABD"
DGREY = "#444444"
LIGHT = "#F6F6F6"
EDGE = "#333333"

def box(ax, x, y, w, h, text, fc=LIGHT, ec=EDGE, fs=9, lw=1.3):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.015",
                       fc=fc, ec=ec, lw=lw, mutation_aspect=1)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color="#111111", linespacing=1.35)
    return p

def home(ax, x, y, h):
    w = 0.18
    box(ax, x, y, w, h, "", fc="#FBFBFB", ec=EDGE, lw=1.2)
    s = 0.055
    hx, hy = x + 0.028, y + 0.03
    ax.add_patch(Rectangle((hx, hy), 1.5 * s, 1.1 * s, fc="#DDDDDD", ec=EDGE, lw=1.1))
    ax.add_patch(Polygon([(hx - 0.2 * s, hy + 1.1 * s), (hx + 0.75 * s, hy + 1.1 * s),
                          (hx + 0.75 * s, hy + 1.7 * s), (hx + 0.48 * s, hy + 2.0 * s),
                          (hx + 0.30 * s, hy + 1.72 * s), (hx - 0.2 * s, hy + 1.72 * s)],
                         closed=True, fc="#C9C9C9", ec=EDGE, lw=1.1))
    ax.text(hx + 0.8 * s + 0.04, y + h / 2, "home /\nmeasurement\nunit", ha="left",
            va="center", fontsize=8.5, color=DGREY, linespacing=1.25)

def demark(ax, x, label, ytop):
    ax.add_line(Line2D([x, x], [0.0, ytop], ls="--", color=DGREY, lw=1.0, alpha=0.8))
    ax.text(x, ytop + 0.008, label, ha="center", va="bottom", fontsize=12,
            color=DGREY, fontweight="bold")

def flow(ax, x1, x2, y):
    a = FancyArrowPatch((x1, y), (x2, y), arrowstyle="-|>", mutation_scale=18,
                        color=EDGE, lw=1.8, shrinkA=0, shrinkB=0)
    ax.add_patch(a)

def main():
    fig, ax = plt.subplots(figsize=(12.5, 2.6))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    y0, h = 0.16, 0.60
    x1, x2, x3, x4 = 0.185, 0.365, 0.560, 0.765

    for x in (x1, x2, x3, x4):
        demark(ax, x, "1" if x == x1 else "2" if x == x2 else "3" if x == x3 else "4", 0.97)

    box(ax, 0.015, y0, x1 - 0.030, h, "Content\nCDN edge caches, cloud,\nhyperscalers\n(geo-distributed)",
        fc="#E9F2FA", ec=BLUE)
    box(ax, x1 + 0.015, y0, (x2 - x1) - 0.030, h, "Public Internet\nIXP peering & transit",
        fc="#E9F2FA", ec=BLUE)
    box(ax, x2 + 0.015, y0, (x3 - x2) - 0.030, h, "ISP network\n(hosts CDN caches,\ndeep peering)",
        fc="#E9F2FA", ec=BLUE)
    box(ax, x3 + 0.015, y0, (x4 - x3) - 0.030, h, "Initial segment\nlast mile\nfiber / DOCSIS 3.1 /\nDSL / 5G",
        fc="#FDE7E3", ec=RED)
    home(ax, x4 + 0.018, y0, h)

    ym = y0 + h / 2
    flow(ax, x1 - 0.012, x1 + 0.014, ym)
    flow(ax, x2 - 0.012, x2 + 0.014, ym)
    flow(ax, x3 - 0.012, x3 + 0.014, ym)
    flow(ax, x4 - 0.012, x4 + 0.014, ym)

    plt.savefig(FIG)
    print("saved", FIG)

if __name__ == "__main__":
    main()
