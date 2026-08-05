import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle, FancyArrowPatch, PathPatch
from matplotlib.lines import Line2D

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

FIG = "/home/jovyan/work/project/paper/figures/internet_pathway_2023_v2.png"

RED = "#E24A33"
BLUE = "#348ABD"
GREEN = "#2E8B57"
GREY = "#9A9A9A"
DGREY = "#444444"
LIGHT = "#F6F6F6"
EDGE = "#333333"

def box(ax, x, y, w, h, text, fc=LIGHT, ec=EDGE, fs=8.5, lw=1.3, tc="#111111"):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.015",
                       fc=fc, ec=ec, lw=lw, mutation_aspect=1)
    ax.add_patch(p)
    if text:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
                color=tc, linespacing=1.35)
    return p

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

def arrow(ax, x1, y1, x2, y2, color=EDGE, lw=2.2, ls="-", style="-|>", ms=18):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=ms,
                        color=color, lw=lw, linestyle=ls, shrinkA=0, shrinkB=0)
    ax.add_patch(a)

def cache(ax, x, y, w, h, label):
    box(ax, x, y, w, h, "", fc="#DFF0DF", ec=GREEN, lw=1.6)
    for i in range(3):
        ax.add_line(Line2D([x + 0.06 * w, x + 0.94 * w], [y + h * (0.30 + 0.20 * i)] * 2,
                           color=GREEN, lw=1.0))
    ax.text(x + w / 2, y + h - 0.10, label, ha="center", va="top", fontsize=7.5,
            color=GREEN, fontweight="bold")

def star(ax, x, y, r=0.02):
    # simple 4-spike burst as congestion marker
    ax.add_patch(PathPatch(__import__("matplotlib").path.Path(
        [(x, y + r), (x + 0.12 * r, y + 0.12 * r), (x + r, y),
         (x + 0.12 * r, y - 0.12 * r), (x, y - r),
         (x - 0.12 * r, y - 0.12 * r), (x - r, y),
         (x - 0.12 * r, y + 0.12 * r)],
        closed=True), fc=RED, ec="none"))

def main():
    fig, ax = plt.subplots(figsize=(12.5, 3.4))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    y0, h = 0.22, 0.50
    xc0, xc1 = 0.015, 0.195   # content
    xi0, xi1 = 0.225, 0.395   # IXP
    xs0, xs1 = 0.425, 0.665   # ISP
    xl0, xl1 = 0.695, 0.855   # initial segment
    xh0, xh1 = 0.885, 0.995   # home
    ym = y0 + h / 2

    # --- content / edge layer (pulled close, blue) ---
    box(ax, xc0, y0, xc1 - xc0, h, "Content\nCDN edge caches,\ncloud, hyperscalers\n(geo-distributed)",
        fc="#E9F2FA", ec=BLUE)

    # --- IXP / peering ---
    box(ax, xi0, y0, xi1 - xi0, h, "Internet\nexchange (IXP)\ndirect peering", fc="#E9F2FA", ec=BLUE)

    # --- transit detour (greyed out, above the path) ---
    tx0, tx1, ty0, ty1 = 0.16, 0.46, 0.80, 0.93
    box(ax, tx0, ty0, tx1 - tx0, ty1 - ty0, "transit\n(largely bypassed)", fc="#EFEFEF", ec=GREY, fs=8)
    arrow(ax, xc0 + 0.06, ty0, xc0 + 0.06, y0 + h + 0.02, color=GREY, lw=1.4, ls=":", ms=12)
    ax.add_line(Line2D([tx0 + 0.08, tx0 + 0.08], [ty0, ty1], color=GREY, lw=1.2, ls=":"))
    ax.add_line(Line2D([tx1 - 0.08, tx1 - 0.08], [ty0, ty1], color=GREY, lw=1.2, ls=":"))
    arrow(ax, tx1 - 0.08, ty0, xi1 - 0.06, y0 + h + 0.02, color=GREY, lw=1.4, ls=":", ms=12)
    ax.text(0.31, 0.945, "old long route through the core", ha="center", va="bottom",
            fontsize=7.5, color=GREY, style="italic")

    # --- ISP network, hosts an off-net CDN cache ---
    box(ax, xs0, y0, xs1 - xs0, h, "ISP network", fc="#E9F2FA", ec=BLUE)
    cache(ax, xs0 + 0.06, y0 + 0.08, 0.135, 0.22, "CDN cache\n(off-net)")
    # short local-serving path from the in-ISP cache straight to the user
    arrow(ax, xs0 + 0.06 + 0.0675, y0 + 0.08, xs0 + 0.06 + 0.0675, y0, color=GREEN, lw=1.6, ls="-", ms=12)

    # --- initial segment: upgraded (green) vs legacy DSL (red) ---
    fx0, fx1 = xl0, xl0 + (xl1 - xl0) * 0.55
    dx0, dx1 = fx1, xl1
    box(ax, fx0, y0, fx1 - fx0, h, "last mile\nfiber /\nDOCSIS 3.1", fc="#E7F4EB", ec=GREEN)
    box(ax, dx0, y0, dx1 - dx0, h, "legacy\nDSL\ncopper", fc="#FDE7E3", ec=RED, lw=2.0)
    # boundary between the two sub-boxes
    ax.add_line(Line2D([fx1, fx1], [y0, y0 + h], color=EDGE, lw=1.0, ls=":"))

    # --- home ---
    home(ax, xh0, y0, h)

    # --- fast lanes: short direct peering path, content -> IXP -> ISP -> user ---
    arrow(ax, xc1 - 0.010, ym, xi0 + 0.012, ym, color=GREEN, lw=2.6)
    arrow(ax, xi1 - 0.010, ym, xs0 + 0.012, ym, color=GREEN, lw=2.6)
    arrow(ax, xs1 - 0.010, ym, fx0 + 0.012, ym, color=GREEN, lw=2.6)
    arrow(ax, fx1 - 0.010, ym, dx0 + 0.012, ym, color=RED, lw=2.2)
    arrow(ax, xl1 - 0.010, ym, xh0 + 0.012, ym, color=GREEN, lw=2.6)

    # small labels on the fast lane
    ax.text((xc1 + xi0) / 2, y0 + h + 0.035, "peering (short path)", ha="center",
            fontsize=7.5, color=GREEN, style="italic")
    ax.text((xi1 + xs0) / 2, y0 + h + 0.035, "off-net / deep peering", ha="center",
            fontsize=7.5, color=GREEN, style="italic")

    # --- congestion markers now live at interconnection + legacy copper ---
    star(ax, xi1 - 0.004, ym + 0.055, r=0.014)
    star(ax, fx1 + 0.006, ym + 0.055, r=0.014)
    ax.text(xi1 + 0.015, ym + 0.075, "interconnection", ha="center", fontsize=7.5,
            color=RED, fontweight="bold", rotation=90, va="bottom")
    ax.text(fx1 - 0.015, ym + 0.075, "copper", ha="center", fontsize=7.5,
            color=RED, fontweight="bold", rotation=90, va="bottom")

    plt.savefig(FIG)
    print("saved", FIG)

if __name__ == "__main__":
    main()
