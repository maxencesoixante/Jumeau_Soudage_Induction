#!/usr/bin/env python3
"""Schéma physique de l'effet de squeeze-out (expulsion résine + fibres) au
soudage par induction de composites CF/PEKK.

Vue en coupe (avant / après) : sous la pression de consolidation, l'interface
fondue (pli twill suscepteur) flue et l'excédent de résine — et une partie des
fibres — est expulsé aux bords libres, formant un bourrelet (« squeeze-out »).
Schéma sans données (comme schema_montage). Sortie : biblio/labo/figures/.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrow, PathPatch
from matplotlib.path import Path as MPath

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts"))
from _style import apply_style, savefig  # noqa: E402
apply_style()

C_LAM = "#C9D6E5"      # laminé (gris-bleu clair)
C_LAM_E = "#5B6B7B"    # bord laminé
C_FIB = "#3A4654"      # plis / fibres
C_HOT = "#E69F00"      # interface fondue / suscepteur (Okabe-Ito orange)
C_BEAD = "#D55E00"     # bourrelet expulsé
C_ARR = "#333333"


def laminate(ax, x0, x1, y0, y1, nplis=5, color=C_LAM):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=color,
                           edgecolor=C_LAM_E, lw=1.2, zorder=2))
    for y in np.linspace(y0, y1, nplis + 1)[1:-1]:
        ax.plot([x0, x1], [y, y], color=C_FIB, lw=0.7, alpha=0.55, zorder=3)


def pressure(ax, xc, ytop, n=3, span=26):
    plate_y = ytop + 1.5
    for dx in np.linspace(-span / 2, span / 2, n):
        ax.add_patch(FancyArrow(xc + dx, plate_y, 0, -(plate_y - ytop - 0.2),
                     width=0.4, head_width=2.0, head_length=1.2, color=C_ARR,
                     zorder=6, length_includes_head=True))
    ax.add_patch(Rectangle((xc - span / 2 - 4, plate_y), span + 8, 1.0,
                 facecolor="#8A8A8A", edgecolor="none", zorder=5))
    ax.text(xc, plate_y + 1.35, "pression de consolidation  $P$", ha="center",
            va="bottom", fontsize=8.5, color=C_ARR)


def bead(ax, xedge, yc, sgn):
    """Bourrelet (lentille) expulsé au bord ; sgn=-1 gauche, +1 droite.
    Même matière que les plis -> même couleur que le laminé."""
    w, h = 7.0, 4.2
    t = np.linspace(0, np.pi, 40)
    ex = xedge + sgn * w * np.sin(t)
    ey = yc + h / 2 * np.cos(t)
    ax.fill(np.r_[xedge, ex, xedge], np.r_[yc + h / 2, ey, yc - h / 2],
            facecolor=C_LAM, edgecolor=C_LAM_E, lw=1.0, zorder=4)
    # quelques fibres expulsées dans le bourrelet (même couleur que les plis)
    for k in (-1, 0, 1):
        ax.plot([xedge, xedge + sgn * w * 0.85], [yc + k * 0.9, yc + k * 1.5],
                color=C_FIB, lw=0.7, alpha=0.6, zorder=5)
    # flèche d'expulsion (neutre)
    ax.add_patch(FancyArrow(xedge + sgn * 1.5, yc, sgn * (w + 3), 0, width=0.35,
                 head_width=1.8, head_length=2.0, color=C_ARR, zorder=6,
                 length_includes_head=True))


fig, (a, b) = plt.subplots(1, 2, figsize=(10.2, 2.6))

for ax in (a, b):
    ax.set_xlim(6, 94)
    ax.set_ylim(3, 26.5)
    ax.set_aspect("equal")
    ax.axis("off")

# géométrie verticale commune : les deux adhérents se touchent à l'interface
Y_SUP = (14.0, 21.5)      # adhérent supérieur (y0, y1)
Y_INF = (6.5, 14.0)       # adhérent inférieur
YC = 14.0                 # plan de soudure

# --- (a) AVANT : plis alignés, mise sous pression ---
X0, X1 = 18, 82
laminate(a, X0, X1, *Y_SUP)
laminate(a, X0, X1, *Y_INF)
a.plot([X0, X1], [YC, YC], color=C_LAM_E, lw=1.4, zorder=4)     # plan de soudure
pressure(a, (X0 + X1) / 2, Y_SUP[1])
a.annotate("adhérents CF/PEKK\n(plis alignés)", xy=(X1, 18.5), xytext=(84, 20.5),
           fontsize=8, color=C_ARR, ha="left", va="center",
           arrowprops=dict(arrowstyle="-", color="0.55", lw=0.6))
a.set_title("(a) Avant — mise sous pression", loc="left", fontsize=10.5,
            fontweight="bold")

# --- (b) APRÈS : fluage, squeeze-out aux bords ---
X0b, X1b = 24, 76                          # empreinte plus étroite (matière expulsée)
laminate(b, X0b, X1b, *Y_SUP)
laminate(b, X0b, X1b, *Y_INF)
b.plot([X0b, X1b], [YC, YC], color=C_LAM_E, lw=1.4, zorder=4)   # plan de soudure
pressure(b, (X0b + X1b) / 2, Y_SUP[1])
bead(b, X0b, YC, -1)
bead(b, X1b, YC, +1)
for sgn in (-1, 1):
    b.add_patch(FancyArrow((X0b + X1b) / 2 + sgn * 6, YC, sgn * 9, 0, width=0.25,
                head_width=1.2, head_length=1.6, color="0.4", zorder=6,
                length_includes_head=True, alpha=0.85))
b.text((X0b + X1b) / 2, 9.8, "fluage vers les bords", ha="center", va="center",
       fontsize=7.5, color=C_ARR, zorder=6)
b.annotate("bourrelet : résine + fibres\nexpulsées (squeeze-out)",
           xy=(X1b + 7, YC - 1), xytext=(58, 4.6), fontsize=8, color=C_ARR,
           ha="left", va="top",
           arrowprops=dict(arrowstyle="-", color="0.55", lw=0.7))
b.set_title("(b) Après — squeeze-out", loc="left", fontsize=10.5,
            fontweight="bold")

fig.suptitle("Effet de squeeze-out au soudage par induction (coupe transverse)",
             fontsize=12, fontweight="bold", y=1.0)
fig.tight_layout(rect=(0, 0, 1, 0.94))
savefig(fig, R / "biblio" / "labo" / "figures" / "fig_squeeze_out")
print("figure -> biblio/labo/figures/fig_squeeze_out.png")
