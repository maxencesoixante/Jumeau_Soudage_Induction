"""Schema de montage -- thermographie plein champ sur plaque CF/PEKK LIBRE (issue #69).

Meme style que gen_schemas_montage.py (exp7 / exp9) : deux vues empilees, vue de
dessus au-dessus, vue en coupe en dessous, legende commune en bas.

Ce qui distingue ce montage des essais exp7/exp9 : la plaque est SUSPENDUE
(appuis ponctuels aux coins, quatre chants libres), il n'y a NI ceramique NI
pression NI empilement de soudage, et la mesure n'est pas faite par des
thermocouples mais par une CAMERA FLIR placee de l'autre cote de la plaque,
axe optique perpendiculaire, cadrant la plaque entiere avec marge.

Geometrie : config/geometrie.yaml (reprise de gen_schemas_montage.py).
Protocole : biblio/labo/protocole_thermographie_plaque_libre.md.

N'ecrit QUE le PNG de sortie.
"""
import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, FancyArrowPatch
from matplotlib.lines import Line2D
import matplotlib as mpl

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
_ap = argparse.ArgumentParser()
_ap.add_argument("--paysage", action="store_true",
                 help="variante panneaux CÔTE À CÔTE (diapositive 16:9) au lieu de l'empilement "
                      "portrait (document / colonne, style exp7-exp9)")
ARGS = _ap.parse_args()
_SUF = "_paysage" if ARGS.paysage else ""
OUT = R / "biblio" / "presentations" / "figures_schemas" / f"schema_montage_flir{_SUF}.png"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _style import apply_style  # noqa: E402

apply_style(**{
    "font.size": 10, "axes.labelsize": 10.5, "axes.titlesize": 11,
    "legend.fontsize": 8.5, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "axes.linewidth": 0.8, "lines.linewidth": 1.2,
    "savefig.pad_inches": 0.08, "figure.facecolor": "white", "savefig.facecolor": "white",
})
mpl.rcParams["hatch.linewidth"] = 0.4

C_COIL = "#E69F00"
C_MFC = "#7F7F7F"
C_COUPON = "#0072B2"
C_CAM = "#009E73"
C_ANNOT = "#C1272D"

# --- geometrie (mm) -------------------------------------------------------- #
L, W = 120.0, 40.0
E_TOT = 6.82                      # laminé (sup 3,36 + film 0,10 + inf 3,36)
TUBE, ENTRAXE = 6.0, 12.35
LEG_LEN, COIL_OVERHANG = 55.0, 9.0
COIL_DRAW_LEN = LEG_LEN + 2 * COIL_OVERHANG
MFC_Y, MFC_X, MFC_H = 55.0, 31.5, 12.0
COUPLAGE = 5.0                    # axe des brins au-dessus de la surface
H_TUBE_BOT = COUPLAGE - TUBE / 2  # +2
H_TUBE_TOP = COUPLAGE + TUBE / 2  # +8
H_MFC_BOT, H_MFC_TOP = H_TUBE_BOT, H_TUBE_BOT + MFC_H
X_CENTRE, X_BORD = 60.0, 15.0     # monospot centré / run bord


def rect(ax, x0, y0, w, h, **kw):
    ax.add_patch(Rectangle((x0, y0), w, h, **kw))


def cote_h(ax, x0, x1, y, text, color="0.25", above=True, fs=7.6):
    ax.annotate("", xy=(x1, y), xytext=(x0, y),
                arrowprops=dict(arrowstyle="<->", color=color, lw=0.7, shrinkA=0, shrinkB=0))
    dy = 0.014 * (ax.get_ylim()[1] - ax.get_ylim()[0])
    ax.text((x0 + x1) / 2, y + (dy if above else -dy), text, ha="center",
            va="bottom" if above else "top", fontsize=fs, color=color)


if ARGS.paysage:
    fig = plt.figure(figsize=(15.0, 6.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.06, 1.0], wspace=0.20,
                          left=0.052, right=0.985, top=0.925, bottom=0.175)
else:
    fig = plt.figure(figsize=(9.2, 10.4))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 0.92], hspace=0.30,
                          left=0.085, right=0.975, top=0.955, bottom=0.115)

# ======================================================================== #
# A -- vue de dessus (plan x-y)
# ======================================================================== #
axA = fig.add_subplot(gs[0])
axA.set_xlim(-20, 142); axA.set_ylim(-34, 72)

# champ de la camera : plaque entiere + marge
rect(axA, -12, -14, L + 24, W + 28, facecolor=C_CAM, alpha=0.06,
     edgecolor=C_CAM, linewidth=1.2, linestyle=(0, (5, 3)), zorder=0)
axA.text(-18, 69, "champ de la caméra FLIR (plaque entière + marge)",
         fontsize=8.4, color=C_CAM, ha="left", va="top")

# plaque CF/PEKK libre
rect(axA, 0, 0, L, W, facecolor=C_COUPON, alpha=0.16, edgecolor="none", zorder=1)
rect(axA, 0, 0, L, W, facecolor="none", edgecolor=C_COUPON, alpha=0.55,
     linewidth=1.3, hatch="xxxx", zorder=1)

# appuis ponctuels aux quatre coins (plaque suspendue, chants libres)
for xs in (7, L - 7):
    for ys in (6, W - 6):
        axA.scatter([xs], [ys], s=52, marker="^", facecolor="white",
                    edgecolor="0.25", linewidth=0.9, zorder=8)
axA.annotate("appuis ponctuels\n(4 chants libres)", xy=(L - 7, 34),
             xytext=(126, 52), fontsize=7.8, color="0.25", ha="center", va="center",
             linespacing=1.3, arrowprops=dict(arrowstyle="->", color="0.45", lw=0.7))

# position "run bord" (fantome)
rect(axA, X_BORD - MFC_X / 2, W / 2 - MFC_Y / 2, MFC_X, MFC_Y, facecolor="none",
     edgecolor=C_MFC, linewidth=1.0, linestyle="--", zorder=3)
for sgn in (-1, 1):
    rect(axA, X_BORD + sgn * ENTRAXE / 2 - TUBE / 2, W / 2 - COIL_DRAW_LEN / 2,
         TUBE, COIL_DRAW_LEN, facecolor="none", edgecolor=C_COIL,
         linewidth=1.0, linestyle="--", zorder=4)
axA.text(X_BORD, -21.0, "run « bord »\nx ≈ 15 mm", fontsize=8.0, color="0.3",
         ha="center", va="center", linespacing=1.3)

# position monospot centre (pleine)
rect(axA, X_CENTRE - MFC_X / 2, W / 2 - MFC_Y / 2, MFC_X, MFC_Y, facecolor=C_MFC,
     edgecolor="0.2", linewidth=0.9, alpha=0.35, zorder=3)
for sgn in (-1, 1):
    rect(axA, X_CENTRE + sgn * ENTRAXE / 2 - TUBE / 2, W / 2 - COIL_DRAW_LEN / 2,
         TUBE, COIL_DRAW_LEN, facecolor=C_COIL, edgecolor="0.2", linewidth=0.7,
         alpha=0.95, zorder=5)
axA.text(X_CENTRE, -21.0, "monospot centré\nx = 60 mm", fontsize=8.0, color="0.15",
         ha="center", va="center", linespacing=1.3, fontweight="bold")

cote_h(axA, 0, L, -30.0, "L = 120 mm", above=False)
axA.annotate("", xy=(-6, W), xytext=(-6, 0),
             arrowprops=dict(arrowstyle="<->", color="0.25", lw=0.7))
axA.text(-8.5, W / 2, "l = 40 mm", rotation=90, fontsize=7.6, color="0.25",
         ha="right", va="center")

axA.set_title("Vue de dessus (plan x–y) — plaque suspendue, un seul spot", pad=8)
axA.set_xlabel("x (mm) — longueur de la plaque")
axA.set_ylabel("y (mm) — largeur")
axA.set_aspect("equal")
for s in ("top", "right"):
    axA.spines[s].set_visible(False)

# ======================================================================== #
# B -- vue en coupe (plan x-z, y = 20 mm)
# ======================================================================== #
axB = fig.add_subplot(gs[1])
axB.set_xlim(30, 90); axB.set_ylim(-42, 22)

rect(axB, X_CENTRE - MFC_X / 2, H_MFC_BOT, MFC_X, MFC_H, facecolor=C_MFC,
     edgecolor="0.2", linewidth=0.9, alpha=0.35, zorder=3)
axB.text(X_CENTRE - MFC_X / 2 + 1.6, H_MFC_TOP - 2.4, "MFC", fontsize=9,
         ha="left", va="center", color="0.2")
for sgn in (-1, 1):
    rect(axB, X_CENTRE + sgn * ENTRAXE / 2 - TUBE / 2, H_TUBE_BOT, TUBE, TUBE,
         facecolor=C_COIL, edgecolor="0.2", linewidth=0.8, zorder=5)

# plaque : lamine 6,82 mm, plis fins, PAS de ceramique
rect(axB, 30, -E_TOT, 60, E_TOT, facecolor=C_COUPON, alpha=0.20, edgecolor="none", zorder=2)
for k in range(1, 6):
    z = -E_TOT * k / 6.0
    axB.plot([30, 90], [z, z], color=C_COUPON, alpha=0.30, lw=0.4, zorder=3)
axB.plot([30, 90], [0, 0], color=C_COUPON, lw=1.4, zorder=4)
axB.plot([30, 90], [-E_TOT, -E_TOT], color=C_COUPON, lw=1.4, zorder=4)

# entraxe des deux brins (la cote qui explique la bimodalité)
cote_h(axB, X_CENTRE - ENTRAXE / 2, X_CENTRE + ENTRAXE / 2, H_TUBE_TOP + 1.6,
       "entraxe 12,35 mm")
# hauteur de l'AXE des brins au-dessus de la surface (= couplage, sans céramique)
axB.annotate("", xy=(X_CENTRE + 19.5, 0), xytext=(X_CENTRE + 19.5, COUPLAGE),
             arrowprops=dict(arrowstyle="<->", color="0.25", lw=0.7))
axB.text(X_CENTRE + 21.0, 6.2, "axe des brins à 5 mm\n(couplage — ni céramique\nni pression)",
         fontsize=7.4, color="0.25", ha="left", va="center", linespacing=1.3)

# les deux depots Joule -> source bimodale
for sgn in (-1, 1):
    x = X_CENTRE + sgn * ENTRAXE / 2
    axB.add_patch(FancyArrowPatch((x, H_TUBE_BOT - 0.4), (x, -0.6),
                                  arrowstyle="-|>", mutation_scale=11,
                                  color=C_ANNOT, lw=1.5, zorder=9))
axB.text(X_CENTRE - 12.5, -8.2, "2 dépôts Joule\n= source BIMODALE\n(issue #69)",
         fontsize=8.4, color=C_ANNOT, ha="right", va="top", linespacing=1.4,
         fontweight="bold")

# camera FLIR de l'autre cote (hors echelle)
axB.add_patch(Polygon([(50, -34.0), (70, -34.0), (88, -16.0), (32, -16.0)],
                      closed=True, facecolor=C_CAM, alpha=0.10, edgecolor=C_CAM,
                      linewidth=1.0, linestyle=(0, (5, 3)), zorder=1))
rect(axB, X_CENTRE - 7.5, -38.6, 15, 4.6, facecolor=C_CAM, alpha=0.75,
     edgecolor="0.2", linewidth=0.8, zorder=6)
rect(axB, X_CENTRE - 2.6, -34.0, 5.2, 1.7, facecolor=C_CAM, alpha=0.95,
     edgecolor="0.2", linewidth=0.8, zorder=6)
axB.annotate("", xy=(X_CENTRE, -E_TOT - 0.8), xytext=(X_CENTRE, -32.0),
             arrowprops=dict(arrowstyle="-|>", color=C_CAM, lw=1.4))
axB.text(X_CENTRE + 4.5, -25.0, "Caméra FLIR — face OPPOSÉE au MFC,\n"
         "axe optique perpendiculaire à la plaque\n(distance hors échelle)",
         fontsize=7.8, color=C_CAM, ha="left", va="center", linespacing=1.35)

axB.set_title("Vue en coupe (plan x–z, y = 20 mm) — détail du spot, échelle 1:1", pad=8)
axB.set_xlabel("x (mm) — longueur de la plaque")
axB.set_ylabel("z (mm) — hauteur\n(0 = surface, + vers le haut)")
axB.set_yticks([-E_TOT, 0, COUPLAGE, H_TUBE_TOP, H_MFC_TOP])
axB.set_yticklabels(["−6,8", "0", "+5", "+8", "+14"])
axB.set_aspect("equal")
for s in ("top", "right"):
    axB.spines[s].set_visible(False)

# ======================================================================== #
handles = [
    Rectangle((0, 0), 1, 1, facecolor=C_COIL, edgecolor="0.2", label="Bobine hairpin (Cu, tube 6 mm)"),
    Rectangle((0, 0), 1, 1, facecolor=C_MFC, edgecolor="0.2", alpha=0.35, label="Concentrateur MFC (Ferrotron 559H)"),
    Rectangle((0, 0), 1, 1, facecolor=C_COUPON, edgecolor=C_COUPON, alpha=0.55,
              hatch="xxxx", label="Plaque CF/PEKK libre (6,8 mm, ni pression ni céramique)"),
    Rectangle((0, 0), 1, 1, facecolor=C_CAM, alpha=0.6, edgecolor="0.2", label="Caméra FLIR + son champ (face opposée)"),
    Line2D([0], [0], marker="^", color="none", markerfacecolor="white",
           markeredgecolor="0.25", markersize=8, label="Appui ponctuel (plaque suspendue)"),
]
fig.legend(handles=handles, loc="lower center", ncol=3 if ARGS.paysage else 2,
           frameon=False, bbox_to_anchor=(0.5, 0.008), columnspacing=2.2,
           handlelength=1.8)

fig.savefig(OUT)
print("écrit :", OUT)
