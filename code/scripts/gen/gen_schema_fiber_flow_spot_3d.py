#!/usr/bin/env python3
"""Vue 3D noir & blanc : *fiber flow* déclenché par UN spot de pression localisé.

Deux adhérents CF/PEKK empilés qui se touchent au plan de soudure (z=ZI). La
pression de consolidation est appliquée à UN endroit précis : un spot au centre
de la plaque. Sous ce spot, la matière flue radialement vers TOUS les bords
libres, où les fibres sont propulsées (squeeze-out) — le pourtour bombe
(gaussienne double, maximale au centre de chaque bord). Faces dessus/dessous
opaques, filet de plis en « jupe » sur le pourtour, flux radial figuré sur le
dessus. Trait noir sur blanc, texte minimal. Sortie : biblio/labo/figures/.
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
apply_style(**{"font.size": 9})

K = "black"
LX, LY = 12.0, 8.0        # dimensions en plan
ZT = 3.0                  # épaisseur totale (2 adhérents de 1.5)
ZI = ZT / 2               # plan de soudure (interface)
A = 2.3                   # débordement maxi (interface, centre de bord)
SZ = 0.62                 # écart-type gaussien en épaisseur
SX, SY = LX / 4.2, LY / 4.2   # écarts-types gaussiens le long des bords
XC, YC = LX / 2, LY / 2   # centre = emplacement du spot de pression
RS = 1.7                  # rayon du spot

xs = np.linspace(0, LX, 60)
ys = np.linspace(0, LY, 40)
th = np.linspace(0, 2 * np.pi, 60)


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


fig = plt.figure(figsize=(7.6, 5.6))
ax = fig.add_subplot(111, projection="3d")
ax.computed_zorder = False   # respecter les zorder (le tri auto masque les annotations)

# face du dessous (opaque)
lx, ly = ply_loop(0.0)
ax.add_collection3d(Poly3DCollection([list(zip(lx, ly, np.zeros_like(lx)))],
                    facecolor="#ECECEC", edgecolor=K, lw=1.3, zorder=0))

# plis (fibres) empilés : le débordement bombe le pourtour à mi-épaisseur.
# Faces opaques -> seul le débordement au-delà du bord reste visible (jupe).
for z in np.linspace(0, ZT, 13):
    if abs(z - ZI) < 1e-6:
        lw = 1.9          # plan de soudure : les fibres qui sortent le plus
    elif z in (0.0, ZT):
        continue
    else:
        lw = 0.8
    lx, ly = ply_loop(z)
    ax.plot(lx, ly, np.full_like(lx, z), color=K, lw=lw, zorder=1)

# face du dessus (opaque) — masque l'intérieur du filet, ne laisse que la jupe
lx, ly = ply_loop(ZT)
ax.add_collection3d(Poly3DCollection([list(zip(lx, ly, np.full_like(lx, ZT)))],
                    facecolor="#FBFBFB", edgecolor=K, lw=1.3, zorder=2))

# fibres propulsées hors du pourtour (squeeze-out) au centre de chaque bord
for (x0, y0, dx, dy) in ((XC, 0, 0, -1), (XC, LY, 0, 1),
                         (0, YC, -1, 0), (LX, YC, 1, 0)):
    ax.quiver(x0 + dx * (A + 0.2), y0 + dy * (A + 0.2), ZI,
              dx * 1.9, dy * 1.9, 0, color=K, lw=2.2, arrow_length_ratio=0.5,
              zorder=3)

# --- spot de pression localisé : double anneau sur la face du dessus ---
ax.plot(XC + RS * np.cos(th), YC + RS * np.sin(th), np.full(60, ZT),
        color=K, lw=2.4, zorder=8)
ax.plot(XC + 0.42 * RS * np.cos(th), YC + 0.42 * RS * np.sin(th),
        np.full(60, ZT), color=K, lw=1.3, zorder=8)

# --- pression appliquée au spot : flèches verticales groupées au-dessus ---
for (ox, oy) in ((-0.55, -0.55), (0.55, -0.55), (-0.55, 0.55), (0.55, 0.55)):
    ax.quiver(XC + ox, YC + oy, ZT + 1.9, 0, 0, -1.5, color=K, lw=2.4,
              arrow_length_ratio=0.5, zorder=10)

# --- texte (simple, format article) ---
ax.text(XC, YC, ZT + 2.7, "pression", ha="center", va="bottom",
        fontsize=8.5, color=K, zorder=11)
ax.text(XC - 2.0, -(A + 4.0), ZI - 1.6, "bourrelet (squeeze-out)",
        ha="center", va="top", fontsize=8.5, color=K, zorder=11)
fig.suptitle("Squeeze-out sous le spot de pression", fontsize=11,
             fontweight="bold", y=0.88)

ax.set_box_aspect((LX + 2 * A, LY + 2 * A, ZT + 4))
ax.set_xlim(-A - 1, LX + A + 1)
ax.set_ylim(-A - 1, LY + A + 1)
ax.set_zlim(0, ZT + 2.6)
ax.view_init(elev=27, azim=-56)
ax.set_axis_off()
fig.tight_layout()
savefig(fig, R / "biblio" / "labo" / "figures" / "fig_fiber_flow_spot_3d")
print("figure -> biblio/labo/figures/fig_fiber_flow_spot_3d.png")
