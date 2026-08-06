import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

FIG = "/home/jovyan/work/project/paper/figures/fig1_modern_core_periphery.png"

RED = "#E24A33"
BLUE = "#348ABD"
GREY = "#777777"
DGREY = "#444444"
LIGHT = "#F6F6F6"
EDGE = "#333333"

def box(ax, x, y, w, h, text, fc=LIGHT, ec=EDGE, fs=8.5, lw=1.3):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.015",
                       fc=fc, ec=ec, lw=lw, mutation_aspect=1)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color="#111111", linespacing=1.35)
    return p

def home(ax, x, y, h):
    """Compact house + label inside a bordered region [x, x+w] x [y, y+h]."""
    w = 0.17
    box(ax, x, y, w, h, "", fc="#FBFBFB", ec=EDGE, lw=1.2)
    s = 0.048
    hx, hy = x + 0.030, y + 0.02
    ax.add_patch(Rectangle((hx, hy), 1.5 * s, 1.1 * s, fc="#DDDDDD", ec=EDGE, lw=1.1))
    ax.add_patch(Polygon([(hx - 0.2 * s, hy + 1.1 * s), (hx + 0.75 * s, hy + 1.1 * s),
                          (hx + 0.75 * s, hy + 1.7 * s), (hx + 0.48 * s, hy + 2.0 * s),
                          (hx + 0.30 * s, hy + 1.72 * s), (hx - 0.2 * s, hy + 1.72 * s)],
                         closed=True, fc="#C9C9C9", ec=EDGE, lw=1.1))
    ax.text(hx + 0.75 * s + 0.045, y + h / 2, "home /\nmeasurement\nunit", ha="left",
            va="center", fontsize=8, color=DGREY, linespacing=1.25)

def demark(ax, x, label, ytop, color=DGREY):
    ax.add_line(Line2D([x, x], [0.0, ytop], ls="--", color=color, lw=1.0, alpha=0.85))
    ax.text(x, ytop + 0.008, label, ha="center", va="bottom", fontsize=11.5,
            color=color, fontweight="bold")

def main():
    fig, ax = plt.subplots(figsize=(12.5, 5.4))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    x1, x2, x3, x4 = 0.195, 0.385, 0.580, 0.800
    for x in (x1, x2, x3, x4):
        demark(ax, x, "1" if x == x1 else "2" if x == x2 else "3" if x == x3 else "4", 0.985,
               color=RED if x in (x3, x4) else BLUE)

    # ================= TOP STRIP: 2013 (original Fig. 1) =================
    y0, h = 0.655, 0.27
    ax.text(0.012, y0 + h + 0.02, "2013 (original Fig. 1)", fontsize=11.5,
            fontweight="bold", color="#111111", ha="left", va="bottom")
    box(ax, 0.015, y0, x1 - 0.030, h, "Test servers /\nwebsites\n(content)", fc=LIGHT)
    box(ax, x1 + 0.015, y0, (x2 - x1) - 0.030, h, "Public Internet\n(transit, peering)", fc="#E8E8E8")
    box(ax, x2 + 0.015, y0, (x3 - x2) - 0.030, h, "ISP network\n(middle mile)", fc="#E8E8E8")
    box(ax, x3 + 0.015, y0, (x4 - x3) - 0.030, h, "Initial segment\n(last mile,\ncable / DSL)", fc="#FDE7E3", ec=RED)
    home(ax, x4 + 0.018, y0, h)

    ax.annotate("bottleneck sat here",
                xy=(0.68, y0), xytext=(0.28, 0.505),
                fontsize=9.5, color=RED, fontweight="bold", ha="center",
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.3))

    # ================= BOTTOM STRIP: 2023+ =================
    y0b, hb = 0.105, 0.30
    ax.text(0.012, y0b + hb + 0.02, "2023+ (this study)", fontsize=11.5,
            fontweight="bold", color="#111111", ha="left", va="bottom")
    box(ax, 0.015, y0b, x1 - 0.030, hb, "CDN edge cache /\ncloud / origin\n(geo-distributed)", fc="#E9F2FA", ec=BLUE)
    box(ax, x1 + 0.015, y0b, (x2 - x1) - 0.030, hb, "IXP peering /\ntransit\n(public Internet)", fc="#E9F2FA", ec=BLUE)
    box(ax, x2 + 0.015, y0b, (x3 - x2) - 0.030, hb, "ISP network —\nhosts CDN caches,\ndeep peering", fc="#E9F2FA", ec=BLUE)
    box(ax, x3 + 0.015, y0b, (x4 - x3) - 0.030, hb, "Initial segment\n(last mile: fiber,\nDOCSIS 3.1, DSL, 5G)", fc="#FDE7E3", ec=RED)
    home(ax, x4 + 0.018, y0b, hb)

    # modern congestion annotations (short arrows up into the strip)
    ax.annotate("content close to the user —\nedge caches at the IXP & inside the ISP",
                xy=(0.34, y0b + hb), xytext=(0.18, 0.012),
                fontsize=8.5, color=BLUE, ha="center",
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.1))
    ax.annotate("interconnection / peering",
                xy=(x2 - 0.01, y0b + hb), xytext=(0.50, 0.020),
                fontsize=8.5, color=RED, fontweight="bold", ha="center",
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.1))
    ax.annotate("legacy copper\nlast mile",
                xy=(0.66, y0b + hb), xytext=(0.845, 0.025),
                fontsize=8.5, color=RED, fontweight="bold", ha="center",
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.1))

    legend = [
        Patch(fc="#FDE7E3", ec=RED, label="persistent congestion"),
        Patch(fc="#E9F2FA", ec=BLUE, label="content / interconnection layer"),
        Patch(fc="#E8E8E8", ec=EDGE, label="transit (bypassed for major content)"),
    ]
    ax.legend(handles=legend, loc="upper center", bbox_to_anchor=(0.5, 1.005),
              ncol=3, frameon=True, fontsize=8.5, handlelength=1.2)

    ax.set_title("Boundary demarcations for a residential broadband connection — then and now",
                 fontsize=13.5, fontweight="bold", pad=12)
    plt.tight_layout()
    plt.savefig(FIG)
    print("saved", FIG)

if __name__ == "__main__":
    main()
