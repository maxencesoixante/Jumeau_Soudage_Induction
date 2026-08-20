#!/usr/bin/env python3
"""Schéma noir & blanc du *fiber flow* au squeeze-out (soudage par induction).

Coupe transverse, trait noir sur blanc, texte minimal. Les deux adhérents
CF/PEKK se touchent au plan de soudure (y=0). Sous la pression de
consolidation, ce sont les fibres de la matière qui sont propulsées de chaque
côté : chaque pli s'étend au-delà du bord d'une quantité gaussienne, maximale
à l'interface (les fibres du centre ressortent le plus) et quasi nulle vers
les peaux — comme le bourrelet observé en vue de dessus. Sortie :
biblio/labo/figures/.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrow

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts"))
from _style import apply_style, savefig  # noqa: E402
apply_style()

K = "black"
H = 6.0                 # demi-épaisseur (adhérents empilés, ils se touchent en y=0)
X0, X1 = 6.0, 54.0      # bords nominaux du joint
A = 7.5                 # débordement maxi (au centre = interface)
SIG = 2.6               # écart-type de la gaussienne (peaux ≈ pas de débordement)


def prot(y):
    """Débordement des fibres au bord : gaussien, maximal à l'interface y=0."""
    return A * np.exp(-y ** 2 / (2 * SIG ** 2))


fig, ax = plt.subplots(figsize=(8.6, 3.3))
ax.set_xlim(X0 - A - 4, X1 + A + 4)
ax.set_ylim(-H - 1.6, H + 3.8)
ax.set_aspect("equal")
ax.axis("off")

# fibres = plis horizontaux ; chacune propulsée de A·gauss(y) de part et d'autre
ys = np.linspace(-H, H, 21)
for y in ys:
    if abs(y) < 1e-6:
        lw = 1.7          # plan de soudure (interface) : les fibres qui sortent le plus
    elif abs(y) > H - 1e-6:
        lw = 1.4          # peaux
    else:
        lw = 0.9
    ax.plot([X0 - prot(y), X1 + prot(y)], [y, y], color=K, lw=lw,
            solid_capstyle="round")

# enveloppe gaussienne des bourrelets (contour bombé) — ferme la pièce
yy = np.linspace(-H, H, 240)
ax.plot(X1 + prot(yy), yy, color=K, lw=1.4)
ax.plot(X0 - prot(yy), yy, color=K, lw=1.4)

# fibres propulsées : flèches vers l'extérieur à l'apex de chaque bourrelet
ax.add_patch(FancyArrow(X1 + A + 0.6, 0, 3.4, 0, width=0.18, head_width=1.2,
             head_length=1.1, color=K, length_includes_head=True))
ax.add_patch(FancyArrow(X0 - A - 0.6, 0, -3.4, 0, width=0.18, head_width=1.2,
             head_length=1.1, color=K, length_includes_head=True))

# pression de consolidation (flèches, sans texte)
for xf in np.linspace(X0 + 8, X1 - 8, 3):
    ax.add_patch(FancyArrow(xf, H + 2.9, 0, -2.0, width=0.18, head_width=1.1,
                 head_length=1.0, color=K, length_includes_head=True))

savefig(fig, R / "biblio" / "labo" / "figures" / "fig_fiber_flow")
print("figure -> biblio/labo/figures/fig_fiber_flow.png")
