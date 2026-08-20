#!/usr/bin/env python3
"""Schéma noir & blanc du *fiber flow* au squeeze-out (soudage par induction).

Coupe transverse, trait noir sur blanc, texte minimal. Deux adhérents CF/PEKK
séparés par le plan de soudure : dans le volume les plis (fibres) restent
droits, mais au bord libre la matière d'interface flue et les fibres se
replient vers l'extérieur en bourrelet. Sortie : biblio/labo/figures/.
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
L = 34.0          # longueur du joint
H = 6.0           # demi-épaisseur (par adhérent)
G = 0.45          # demi-interstice de l'interface (plan de soudure)


def bulk_plies(ax, x0, x1):
    """Plis droits dans le volume des deux adhérents (hors zone d'interface)."""
    for s in (+1, -1):
        for y in np.linspace(G + 0.7, H - 0.4, 6) * s:
            ax.plot([x0, x1], [y, y], color=K, lw=0.9, solid_capstyle="round")


def edge_bead(ax, xe, sgn):
    """Bourrelet au bord libre : arcs emboîtés = fibres repliées/expulsées."""
    th = np.linspace(-np.pi / 2, np.pi / 2, 90)
    for r in (0.55, 1.05, 1.55, 2.05):
        ax.plot(xe + sgn * r * np.cos(th), r * np.sin(th), color=K, lw=0.9)


def interface_flow(ax, xe, sgn, xin):
    """Plis d'interface qui dévient vers le bord et alimentent le bourrelet."""
    for s in (+1, -1):
        for y0, rt in ((0.6, 0.55), (1.2, 1.05)):
            xx = np.linspace(xin, xe, 60)
            t = (xx - xin) / (xe - xin)
            yy = s * (y0 + (rt - y0) * t ** 2)
            ax.plot(xx, yy, color=K, lw=0.9)


fig, ax = plt.subplots(figsize=(8.0, 3.2))
ax.set_xlim(-6, L + 6)
ax.set_ylim(-H - 1.6, H + 3.4)
ax.set_aspect("equal")
ax.axis("off")

# contour des deux adhérents (interstice = interface)
for (yb, yt) in ((G, H), (-H, -G)):
    ax.plot([0, L, L, 0, 0], [yb, yb, yt, yt, yb], color=K, lw=1.4)

bulk_plies(ax, 0.5, L - 0.5)
for xe, sgn, xin in ((L, +1, L - 15), (0.0, -1, 15)):
    interface_flow(ax, xe, sgn, xin)
    edge_bead(ax, xe, sgn)

# pression de consolidation (flèches, sans texte)
for xf in np.linspace(7, L - 7, 3):
    ax.add_patch(FancyArrow(xf, H + 2.7, 0, -2.0, width=0.18, head_width=1.1,
                 head_length=1.0, color=K, length_includes_head=True))

savefig(fig, R / "biblio" / "labo" / "figures" / "fig_fiber_flow")
print("figure -> biblio/labo/figures/fig_fiber_flow.png")
