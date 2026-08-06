import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

FIG = "/home/jovyan/work/project/paper/figures/internet_model_2010s_vs_2020s.png"

BLUE = "#348ABD"
CABLE = "#E24A33"
GREY = "#777777"
LIGHT = "#F2F2F2"
DGREY = "#555555"

def box(ax, x, y, w, h, text, fc="#FFFFFF", ec="#333333", fs=10, lw=1.4, style="round,pad=0.02,rounding_size=0.02"):
    p = FancyBboxPatch((x, y), w, h, boxstyle=style, fc=fc, ec=ec, lw=lw, mutation_aspect=1)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color="#111111", linespacing=1.35)
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

def main():
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.4))
    for ax in axes:
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    # ------------------------------------------------------------------
    # LEFT PANEL — early 2010s
    # ------------------------------------------------------------------
    ax = axes[0]
    ax.set_title("Early 2010s\nhierarchical, transit-routed", fontsize=13, fontweight="bold", pad=10)

    # Content at top
    box(ax, 0.30, 0.83, 0.40, 0.10, "Centralized content\n(datacenters, origin servers)", fs=10, fc=LIGHT)
    box(ax, 0.05, 0.64, 0.90, 0.10, "Tier-1 transit backbone", fs=10, fc=LIGHT)
    box(ax, 0.05, 0.45, 0.90, 0.10, "Regional / metro networks", fs=10, fc=LIGHT)

    # Access box (the 2013 bottleneck)
    box(ax, 0.05, 0.24, 0.90, 0.12, "Access ISP — last mile\n(cable / DSL plant)", fs=10, fc="#FDE7E3", ec=CABLE, lw=2.0)

    # Users
    for i, ux in enumerate((0.28, 0.50, 0.72)):
        user(ax, ux, 0.09)
        arrow(ax, ux, 0.10, ux, 0.24, color=CABLE, lw=2.4)
    arrow(ax, 0.50, 0.36, 0.50, 0.45, color="#333333")
    arrow(ax, 0.50, 0.55, 0.50, 0.64, color="#333333")
    arrow(ax, 0.50, 0.74, 0.50, 0.83, color="#333333")

    ax.annotate("bottleneck: the last mile", xy=(0.72, 0.20), xytext=(0.84, 0.30),
                fontsize=10, color=CABLE, fontweight="bold", ha="center",
                arrowprops=dict(arrowstyle="-", color=CABLE, lw=1.0))
    ax.text(0.50, 0.015, "Every path climbs through transit to reach far-away content",
            ha="center", va="bottom", fontsize=9, color=GREY, style="italic")

    # ------------------------------------------------------------------
    # RIGHT PANEL — 2023+
    # ------------------------------------------------------------------
    ax = axes[1]
    ax.set_title("2023+\nflat, CDN / hyperscaler-centric", fontsize=13, fontweight="bold", pad=10)

    # Edge / CDN layer
    box(ax, 0.08, 0.60, 0.34, 0.26, "Content delivered from the edge:\nCDN caches, cloud, hyperscalers\n(anycast + geo-distributed)", fs=9.5, fc="#E9F2FA", ec=BLUE, lw=1.8)
    box(ax, 0.55, 0.60, 0.37, 0.26, "Internet exchange (IXP)\ndeep peering, off-net\ncontent", fs=9.5, fc="#E9F2FA", ec=BLUE, lw=1.8)
    arrow(ax, 0.42, 0.73, 0.55, 0.73, color=BLUE, lw=2.0)

    # Access boxes: upgraded last mile vs legacy copper
    box(ax, 0.08, 0.33, 0.47, 0.14, "Upgraded access\n(fiber / DOCSIS 3.1)", fs=10, fc="#E7F4EB", ec="#2E8B57", lw=1.8)
    box(ax, 0.62, 0.33, 0.30, 0.14, "Legacy DSL\ncopper", fs=10, fc="#FDE7E3", ec=CABLE, lw=1.8)

    # Direct short paths: access -> edge cache / IXP
    arrow(ax, 0.32, 0.47, 0.32, 0.60, color="#2E8B57", lw=2.2)
    arrow(ax, 0.32, 0.47, 0.32, 0.60, color="#2E8B57", lw=2.2)
    arrow(ax, 0.74, 0.47, 0.74, 0.60, color=CABLE, lw=2.2, ls=":")

    # Users
    for i, ux in enumerate((0.28, 0.50, 0.72)):
        user(ax, ux, 0.09)
        arrow(ax, ux, 0.10, ux, 0.33, color="#2E8B57", lw=2.0)

    ax.annotate("congestion moved here:\nlegacy copper + interconnection",
                xy=(0.80, 0.40), xytext=(0.80, 0.12),
                fontsize=9.5, color=CABLE, fontweight="bold", ha="center",
                arrowprops=dict(arrowstyle="-", color=CABLE, lw=1.0))
    ax.text(0.50, 0.015, "Content pushed to the edge — short, peered paths, transit bypassed",
            ha="center", va="bottom", fontsize=9, color=GREY, style="italic")

    fig.suptitle("Two models of the Internet: where the latency lives", fontsize=14, fontweight="bold", y=1.01)
    plt.tight_layout()
    plt.savefig(FIG)
    print("saved", FIG)

if __name__ == "__main__":
    main()
