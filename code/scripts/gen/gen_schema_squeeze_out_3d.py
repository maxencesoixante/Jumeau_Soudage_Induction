#!/usr/bin/env python3
"""Vue 3D schématique de l'effet de squeeze-out au soudage par induction.

Deux adhérents composites CF/PEKK empilés ; sous la pression de consolidation,
la matière flue à l'interface et forme un bourrelet (résine + fibres) sur le
pourtour libre du joint. Schéma sans données. Sortie : biblio/labo/figures/.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts"))
from _style import apply_style, savefig  # noqa: E402
apply_style()

C_LAM = "#C9D6E5"      # laminé
C_LAM_E = "#5B6B7B"    # arêtes
C_TOP = "#B7C6D8"      # face supérieure (un peu plus foncée)
C_ARR = "#333333"

LX, LY = 10.0, 6.0     # longueur, largeur
ZB = (0.0, 1.5)        # adhérent inférieur (z0,z1)
ZT = (1.5, 3.0)        # adhérent supérieur
ZI = 1.5               # plan de soudure


def box(ax, x0, x1, y0, y1, z0, z1, top=False):
    v = np.array([[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
                  [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]])
    faces = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4],
             [2, 3, 7, 6], [1, 2, 6, 5], [0, 3, 7, 4]]
    polys = [[v[i] for i in f] for f in faces]
    pc = Poly3DCollection(polys, facecolor=C_LAM, edgecolor=C_LAM_E, lw=1.0, alpha=1.0)
    ax.add_collection3d(pc)
    if top:  # recouvre la face du dessus d'un ton légèrement distinct
        topface = Poly3DCollection([[v[i] for i in [4, 5, 6, 7]]],
                                   facecolor=C_TOP, edgecolor=C_LAM_E, lw=1.0)
        ax.add_collection3d(topface)


def bead_ridge(ax, x0, x1, y_edge, zc, sgn_y, r=0.75, n=26):
    """Bourrelet = demi-cylindre le long d'une arête libre du joint.
    sgn_y=-1 : déborde vers -y (arête avant)."""
    u = np.linspace(x0, x1, n)
    th = np.linspace(0, np.pi, n)
    U, T = np.meshgrid(u, th)
    X = U
    Y = y_edge + sgn_y * r * np.sin(T)
    Z = zc + r * np.cos(T)
    ax.plot_surface(X, Y, Z, color=C_LAM, edgecolor=C_LAM_E, lw=0.15,
                    alpha=1.0, antialiased=True, shade=False)


fig = plt.figure(figsize=(7.2, 5.2))
ax = fig.add_subplot(111, projection="3d")

box(ax, 0, LX, 0, LY, *ZB)              # adhérent inférieur
box(ax, 0, LX, 0, LY, *ZT, top=True)    # adhérent supérieur

# bourrelets sur les arêtes libres avant (y=0) et droite (x=LX)
bead_ridge(ax, 0.4, LX - 0.4, 0.0, ZI, sgn_y=-1)          # arête avant
# arête droite : demi-cylindre le long de y à x=LX
th = np.linspace(0, np.pi, 26); u = np.linspace(0.4, LY - 0.4, 26)
U, T = np.meshgrid(u, th)
ax.plot_surface(LX + 0.75 * np.sin(T), U, ZI + 0.75 * np.cos(T),
                color=C_LAM, edgecolor=C_LAM_E, lw=0.15, alpha=1.0, shade=False)

# plan de soudure (fin liseré sur la face avant)
ax.plot([0, LX], [0, 0], [ZI, ZI], color=C_LAM_E, lw=1.4, zorder=5)

# pression de consolidation : flèches vers le bas au-dessus du dessus
for xf in (2.5, 5.0, 7.5):
    for yf in (1.5, 4.5):
        ax.quiver(xf, yf, ZT[1] + 1.6, 0, 0, -1.3, color=C_ARR, lw=1.6,
                  arrow_length_ratio=0.45)
ax.text(LX / 2, LY / 2, ZT[1] + 2.1, "pression de consolidation $P$",
        ha="center", va="bottom", fontsize=9, color=C_ARR)

# annotations
ax.text(LX / 2, -2.7, 0.0, "bourrelet (squeeze-out) : résine + fibres expulsées",
        ha="center", va="top", fontsize=8.5, color=C_ARR)
ax.text(-0.5, LY, ZT[1], "adhérents CF/PEKK", ha="right", va="bottom",
        fontsize=8.5, color=C_ARR)

ax.set_box_aspect((LX, LY + 3, ZT[1] + 3))
ax.set_xlim(0, LX); ax.set_ylim(-2.5, LY); ax.set_zlim(0, ZT[1] + 2.4)
ax.view_init(elev=18, azim=-62)
ax.set_axis_off()
fig.suptitle("Effet de squeeze-out au soudage par induction (vue 3D)",
             fontsize=12, fontweight="bold", y=0.94)
fig.tight_layout()
savefig(fig, R / "biblio" / "labo" / "figures" / "fig_squeeze_out_3d")
print("figure -> biblio/labo/figures/fig_squeeze_out_3d.png")
