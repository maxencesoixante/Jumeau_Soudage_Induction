#!/usr/bin/env python3
"""Schéma des passages du MFC + coil — soudage semi-statique (exp9 / serieA-B).

Vue de dessus (plan x-y) : la plaque CF/PEKK (120 × 40 mm) et les 4 positions
successives du MFC + bobine hairpin (avance de 30 mm par passe). Montre le
recouvrement des empreintes MFC (→ toute la longueur soudée), les 2 rails de
soudure (lobes du « M » aux chants y=0 et y=40) et les 5 thermocouples (ligne
de bord, exp9). Valeurs : config/geometrie.yaml.

Sortie : biblio/presentations/figures_schemas/fig_passages_mfc.png
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts"))
from _style import apply_style, savefig, OKABE_ITO  # noqa: E402
apply_style()

# --- géométrie (mm), cf. config/geometrie.yaml ---
L, W = 120.0, 40.0                                  # plaque : longueur x, largeur y
SPOTS = [15.875, 45.875, 75.875, 105.875]           # centres des spots (pas 30 mm)
MFC_X, MFC_Y = 31.5, 55.0                            # empreinte MFC : 31,5 mm (x) × 55 mm (y)
ENTRAXE, BRIN = 12.35, 6.0                           # bobine hairpin : entraxe, côté tube
TC_X = [0, 30, 60, 90, 120]                          # TC ligne de bord (y=0) — exp9
RAIL = 3.5                                            # épaisseur figurée des rails de soudure
COUL = [OKABE_ITO[c] for c in ("bleu", "vert", "orange", "rose")]
CU = "#B8860B"

fig, ax = plt.subplots(figsize=(11, 5.2))

# plaque
ax.add_patch(Rectangle((0, 0), L, W, facecolor="#EAF2F8", edgecolor="black", lw=1.4, zorder=1))
# rails de soudure (lobes du M, aux deux chants)
for y0 in (0.0, W - RAIL):
    ax.add_patch(Rectangle((0, y0), L, RAIL, facecolor="#D55E00", alpha=0.20, edgecolor="none", zorder=1.5))

# empreintes MFC + bobine, une par passe
for i, xc in enumerate(SPOTS):
    col = COUL[i]
    ax.add_patch(Rectangle((xc - MFC_X / 2, W / 2 - MFC_Y / 2), MFC_X, MFC_Y,
                           facecolor=col, alpha=0.14, edgecolor=col, lw=1.4, ls="--", zorder=2))
    for dx in (-ENTRAXE / 2, ENTRAXE / 2):           # 2 brins Cu (hairpin), parallèles à y
        ax.add_patch(Rectangle((xc + dx - BRIN / 2, W / 2 - MFC_Y / 2), BRIN, MFC_Y,
                               facecolor=CU, alpha=0.65, edgecolor="none", zorder=3))
    ax.text(xc, W / 2 + MFC_Y / 2 + 2.5, f"P{i + 1}", ha="center", va="bottom",
            color=col, fontweight="bold", fontsize=12, zorder=4)

# flèches d'avance +30 mm
for i in range(len(SPOTS) - 1):
    xm = 0.5 * (SPOTS[i] + SPOTS[i + 1])
    ax.add_patch(FancyArrowPatch((SPOTS[i], W / 2 + MFC_Y / 2 + 8), (SPOTS[i + 1], W / 2 + MFC_Y / 2 + 8),
                                 arrowstyle="-|>", mutation_scale=13, color="0.3", lw=1.3, zorder=4))
    ax.text(xm, W / 2 + MFC_Y / 2 + 9.5, "+30 mm", ha="center", va="bottom", fontsize=8.5, color="0.3")

# thermocouples (ligne de bord y=0)
ax.scatter(TC_X, [0] * len(TC_X), marker="x", s=70, color="#B00020", linewidths=2.2, zorder=5)
for k, x in enumerate(TC_X):
    ax.annotate(f"TC{k + 1}", (x, 0), xytext=(x, -5.0), ha="center", va="top",
                fontsize=8.5, color="#B00020", fontweight="bold")

# habillage
ax.set_xlim(-6, L + 6)
ax.set_ylim(-11, W / 2 + MFC_Y / 2 + 14)
ax.set_aspect("equal")
ax.set_xlabel("Longueur x (mm)")
ax.set_ylabel("Largeur y (mm)")
ax.set_yticks([0, 20, 40])
fig.suptitle("Passages du MFC + coil — soudage semi-statique (4 passes, avance 30 mm)",
             fontsize=13, fontweight="bold", y=0.99)
fig.text(0.5, 0.925, "Empreintes MFC (31,5 mm) recouvrantes au pas 30 mm → toute la longueur est soudée ; "
         "le MFC (55 mm ∥ y) déborde la largeur de 7,5 mm de chaque côté.",
         ha="center", va="top", fontsize=9, color="0.35")

# légende
handles = [
    Rectangle((0, 0), 1, 1, facecolor=COUL[0], alpha=0.14, edgecolor=COUL[0], ls="--", label="empreinte MFC (31,5 × 55 mm)"),
    Rectangle((0, 0), 1, 1, facecolor=CU, alpha=0.65, edgecolor="none", label="brins de la bobine (hairpin)"),
    Rectangle((0, 0), 1, 1, facecolor="#D55E00", alpha=0.20, edgecolor="none", label="rails de soudure (lobes du M, chants)"),
    plt.Line2D([0], [0], marker="x", color="#B00020", lw=0, markersize=8, markeredgewidth=2.2, label="thermocouples (bord, exp9)"),
]
fig.tight_layout(rect=(0, 0.13, 1, 0.90))
fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.005),
           ncol=2, fontsize=9, framealpha=0.95)
savefig(fig, R / "biblio" / "presentations" / "figures_schemas" / "fig_passages_mfc")
print("figure -> biblio/presentations/figures_schemas/fig_passages_mfc.png")
