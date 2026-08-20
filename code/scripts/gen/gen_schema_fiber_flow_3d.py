#!/usr/bin/env python3
"""Vue 3D noir & blanc du *fiber flow* au squeeze-out (soudage par induction).

Deux adhérents CF/PEKK empilés qui se touchent au plan de soudure (z=z_i).
Sous la pression de consolidation, les fibres de la matière sont propulsées
sur tout le pourtour libre : le débordement suit une gaussienne double —
maximal à mi-épaisseur (interface) et au centre de chaque bord, nul aux coins
et aux peaux — comme le bourrelet observé en vue de dessus. Chaque pli est
tracé (fibres) ; l'interface est en gras. Sortie : biblio/labo/figures/.
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

K = "black"
LX, LY = 12.0, 7.0        # dimensions en plan
ZT = 3.0                  # épaisseur totale (2 adhérents de 1.5)
ZI = ZT / 2               # plan de soudure (interface)
A = 2.3                   # débordement maxi (interface, centre de bord)
SZ = 0.62                 # écart-type gaussien en épaisseur
SX, SY = LX / 4.2, LY / 4.2   # écarts-types gaussiens le long des bords

xs = np.linspace(0, LX, 60)
ys = np.linspace(0, LY, 40)


def pz(z):
    return A * np.exp(-(z - ZI) ** 2 / (2 * SZ ** 2))


def gx(x):
    return np.exp(-((x - LX / 2) / SX) ** 2 / 2)


def gy(y):
    return np.exp(-((y - LY / 2) / SY) ** 2 / 2)


def ply_loop(z):
    """Contour d'un pli à la cote z, bombé vers l'extérieur (double gaussienne)."""
    P = pz(z)
    front = np.column_stack([xs, -P * gx(xs)])
    right = np.column_stack([LX + P * gy(ys), ys])
    back = np.column_stack([xs[::-1], LY + P * gx(xs[::-1])])
    left = np.column_stack([-P * gy(ys[::-1]), ys[::-1]])
    loop = np.vstack([front, right, back, left, front[:1]])
    return loop[:, 0], loop[:, 1]


fig = plt.figure(figsize=(7.4, 5.4))
ax = fig.add_subplot(111, projection="3d")

# faces pleines dessus / dessous (peaux, contour quasi droit) — un peu de corps
for z, fc in ((0.0, "#EDEDED"), (ZT, "#F6F6F6")):
    lx, ly = ply_loop(z)
    ax.add_collection3d(Poly3DCollection(
        [list(zip(lx, ly, np.full_like(lx, z)))],
        facecolor=fc, edgecolor=K, lw=1.3))

# plis (fibres) empilés ; le débordement bombe le pourtour à mi-épaisseur
zs = np.linspace(0, ZT, 19)
for z in zs:
    lx, ly = ply_loop(z)
    if abs(z - ZI) < 1e-6:
        lw = 1.9          # plan de soudure : les fibres qui sortent le plus
    elif z in (0.0, ZT):
        continue          # déjà tracées (peaux)
    else:
        lw = 0.8
    ax.plot(lx, ly, np.full_like(lx, z), color=K, lw=lw)

# fibres propulsées : flèches vers l'extérieur au centre de chaque bord (interface)
for (x0, y0, dx, dy) in ((LX / 2, 0, 0, -1), (LX / 2, LY, 0, 1),
                         (0, LY / 2, -1, 0), (LX, LY / 2, 1, 0)):
    ax.quiver(x0 + dx * (A + 0.3), y0 + dy * (A + 0.3), ZI,
              dx * 2.2, dy * 2.2, 0, color=K, lw=1.8, arrow_length_ratio=0.45)

# pression de consolidation : flèches vers le bas au-dessus du dessus
for xf in (LX * 0.28, LX * 0.5, LX * 0.72):
    ax.quiver(xf, LY / 2, ZT + 2.0, 0, 0, -1.5, color=K, lw=1.8,
              arrow_length_ratio=0.45)

ax.set_box_aspect((LX + 2 * A, LY + 2 * A, ZT + 4))
ax.set_xlim(-A - 1, LX + A + 1)
ax.set_ylim(-A - 1, LY + A + 1)
ax.set_zlim(0, ZT + 2.6)
ax.view_init(elev=24, azim=-58)
ax.set_axis_off()
fig.tight_layout()
savefig(fig, R / "biblio" / "labo" / "figures" / "fig_fiber_flow_3d")
print("figure -> biblio/labo/figures/fig_fiber_flow_3d.png")
