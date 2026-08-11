import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import os

OUT = "output/paper/tables"
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "figure.dpi": 150,
    "savefig.dpi": 300,
})

rows = []
for mo, cab, dsl in [
    ("March", dict(Total=2878, FC=696, PTIS=60, both=56), dict(Total=2009, FC=143, PTIS=68, both=52)),
    ("April", dict(Total=2914, FC=715, PTIS=46, both=46), dict(Total=2017, FC=136, PTIS=64, both=38)),
    ("May",   dict(Total=2961, FC=664, PTIS=39, both=38), dict(Total=1989, FC=343, PTIS=43, both=24)),
    ("June",  dict(Total=2925, FC=752, PTIS=23, both=22), dict(Total=1921, FC=355, PTIS=43, both=27)),
]:
    for label, r in [("Cable", cab), ("DSL", dsl)]:
        rows.append([
            mo, label, r["Total"], r["FC"], r["PTIS"], r["both"],
            f"{r['both']/r['PTIS']*100:.0f}%", f"{r['both']/r['FC']*100:.0f}%",
            f"{r['FC']/r['Total']*100:.0f}%", f"{r['PTIS']/r['Total']*100:.0f}%",
        ])

head = ["Month", "Tech", "Total\nunits", "RC\nunits", "TIS\nunits", "RC\u2229TIS",
        "RC\u2229TIS\n/ TIS", "RC\u2229TIS\n/ RC", "RC\nprev.", "TIS\nprev."]

fig, ax = plt.subplots(figsize=(10.5, 4.8))
ax.axis("off")

tbl = ax.table(
    cellText=rows,
    colLabels=head,
    cellLoc="center",
    loc="center",
    colColours=["#2c3e50"] * len(head),
)
tbl.auto_set_font_size(False)
tbl.set_fontsize(10.5)
tbl.scale(1, 1.8)

# header styling
for c in range(len(head)):
    cell = tbl[0, c]
    cell.get_text().set_color("white")
    cell.get_text().set_fontweight("bold")
    cell.get_text().set_fontsize(10)

# row styling + highlight intersection ratio cols
hl_bg = "#fbf3d0"
cable_bg = "#fdecea"
dsl_bg = "#eaf3fb"
for r in range(1, len(rows) + 1):
    tech = rows[r - 1][1]
    bg = cable_bg if tech == "Cable" else dsl_bg
    for c in range(len(head)):
        cell = tbl[r, c]
        cell.set_facecolor(bg)
        if c in (6, 7):
            cell.set_facecolor(hl_bg)
            if c == 7 and tech == "DSL":
                cell.get_text().set_color("#1a5276")
                cell.get_text().set_fontweight("bold")
            elif c == 7 and tech == "Cable":
                cell.get_text().set_color("#922b21")

# column widths so the table is balanced
widths = [0.09, 0.09, 0.10, 0.09, 0.09, 0.10, 0.11, 0.11, 0.10, 0.10]
for c, w in enumerate(widths):
    tbl.get_celld()[0, c].set_width(w)
    for r in range(1, len(rows) + 1):
        tbl.get_celld()[r, c].set_width(w)

fig.text(0.5, 0.03,
         "Cable: high RC but low RC\u2229TIS/RC (3\u20138%) \u2192 congestion sits deeper in the network, not the last mile.  "
         "DSL: lower RC but higher RC\u2229TIS/RC (7\u201336%) \u2192 congestion is mostly on the initial segment.",
         ha="center", va="bottom", fontsize=9, color="#333",
         bbox=dict(boxstyle="round,pad=0.4", fc="#f4f6f7", ec="#bdc3c7", lw=0.8))

fig.suptitle("Reproduction of Genin & Splett (2013): recurrent congestion (RC) and tight initial segment (TIS) prevalence",
             fontsize=12.5, y=0.98, fontweight="bold")
fig.tight_layout(rect=[0, 0.08, 1, 0.93])
fig.savefig(os.path.join(OUT, "poster_table_rc_tis.png"), bbox_inches="tight")
plt.close(fig)
print("Wrote poster_table_rc_tis.png")
