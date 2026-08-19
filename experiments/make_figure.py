"""
Build Figure 1 for the preprint: calibration and base-rate sensitivity.

Reads results/metrics.json and results/ablation.md so the figure can never
disagree with the reported numbers - a lesson from review 4, where interpretive
text had been hard-coded and drifted from its own table.
"""
import json, os, re, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")

BLUE, ORANGE = "#2a78d6", "#eb6834"      # validated categorical slots 1 and 2
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#d8d7d2"

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8.5,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
    "axes.edgecolor": MUTED, "axes.linewidth": 0.6,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "text.color": INK, "axes.labelcolor": INK,
    "figure.dpi": 400, "savefig.dpi": 400,
})

metrics = json.load(open(os.path.join(RESULTS, "metrics.json"), encoding="utf-8"))
test = next(r for r in metrics if r["set"] == "Held-out test set")
cal = test["systems"]["fixed_band"]["calibration"]
ece = cal["ece"]

bins = [b for b in cal["bins"] if b["n"] > 0]
xs = [b["mean_p"] for b in bins]
ys = [b["observed"] for b in bins]
ns = [b["n"] for b in bins]

# base-rate table, parsed out of ablation.md so both cannot drift apart
ab = open(os.path.join(RESULTS, "ablation.md"), encoding="utf-8").read()
sec = ab.split("## How far do the headline numbers travel?")[1].split("##")[0]
rows = [l.split("|")[1:-1] for l in sec.strip().split("\n") if l.startswith("| 0.")]
series = {}
for r in rows:
    prior, pol, recall = float(r[0]), r[1].strip(), r[8].strip()
    if recall != "-":
        series.setdefault(pol, []).append((prior, float(recall)))
for k in series:
    series[k].sort()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.7))

# ---- (a) reliability -------------------------------------------------------
# Points, not a line: the bins are independent estimates, not a trajectory.
# Marker area is proportional to bin count, so the eye discounts the thin bins
# without needing to read every annotation.
ax1.plot([0, 1], [0, 1], color=GRID, lw=1.0, ls=(0, (4, 3)), zorder=1)
ax1.text(0.42, 0.40, "perfectly calibrated", color=MUTED, fontsize=6.8,
         rotation=45, rotation_mode="anchor", ha="center", va="bottom")
sizes = [26 + 9 * n for n in ns]
ax1.scatter(xs, ys, s=sizes, facecolor=BLUE, edgecolor="white",
            linewidth=1.2, zorder=3, clip_on=False)
for x, y, n in zip(xs, ys, ns):
    dx, dy, ha = 0, -16, "center"
    if y > 0.9:          # top of the panel: label below, clear of the diagonal
        dx, dy, ha = 0, -22, "center"
    elif y < 0.2:        # bottom: label above
        dy = 13
    ax1.annotate(f"n={n}", (x, y), textcoords="offset points",
                 xytext=(dx, dy), ha=ha, fontsize=7, color=MUTED, zorder=4)
ax1.set_xlim(-0.02, 1.02); ax1.set_ylim(-0.04, 1.10)
ax1.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
ax1.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
ax1.set_xlabel("Mean predicted P(not genuine)")
ax1.set_ylabel("Observed fake rate")
ax1.set_title(f"(a) Calibration, fixed-band policy (ECE {ece:.3f})", loc="left", pad=8)
ax1.grid(True, color=GRID, lw=0.4, alpha=0.7); ax1.set_axisbelow(True)
for sp in ("top", "right"): ax1.spines[sp].set_visible(False)

# ---- (b) base-rate sensitivity --------------------------------------------
style = {"fixed_band": (BLUE, "o", "Fixed bands (A)"),
         "expected_cost": (ORANGE, "s", "Expected cost (B)")}
for pol, pts in series.items():
    c, m, lab = style[pol]
    ax2.plot([p for p, _ in pts], [r for _, r in pts], color=c, lw=2.0,
             marker=m, ms=6, mec="white", mew=1.2, label=lab, zorder=3, clip_on=False)
    p0, r0 = pts[-1]
    ax2.annotate(lab, (p0, r0), textcoords="offset points", xytext=(6, 0),
                 fontsize=7.5, color=c, va="center")
ax2.set_xlim(0.02, 0.70); ax2.set_ylim(-0.04, 1.10)
ax2.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
ax2.set_xlabel("Prior P(fake)")
ax2.set_ylabel("Recall")
ax2.set_title("(b) Recall against assumed base rate", loc="left", pad=8)
ax2.grid(True, color=GRID, lw=0.4, alpha=0.7); ax2.set_axisbelow(True)
for sp in ("top", "right"): ax2.spines[sp].set_visible(False)

fig.tight_layout(pad=0.6, w_pad=3.2)
out = os.path.join(ROOT, "paper", "figures", "figure1.pdf")
fig.savefig(out, bbox_inches="tight")
fig.savefig(out.replace(".pdf", ".png"), bbox_inches="tight")
print("wrote", out)
print("calibration bins:", list(zip(xs, ys, ns)))
print("base rate series:", {k: v for k, v in series.items()})
