#!/usr/bin/env python3
"""Storyboard des passages du MFC + coil — soudage semi-statique (4 vignettes).

Une vignette par passe (vue de dessus) : position courante du MFC + bobine, et la
ZONE DÉJÀ SOUDÉE (rails aux chants) qui progresse passe après passe jusqu'à
couvrir toute la longueur. Positions exp9/serieA-B (spots pas 30 mm, 5 TC bord).

Sortie : biblio/presentations/figures_schemas/fig_passages_mfc_storyboard.png
"""
from __future__ import annotations
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts"))
from _style import apply_style, savefig, OKABE_ITO  # noqa: E402
apply_style()

L, W = 120.0, 40.0
SPOTS = [15.875, 45.875, 75.875, 105.875]
MFC_X, MFC_Y = 31.5, 55.0
ENTRAXE, BRIN = 12.35, 6.0
TC_X = [0, 30, 60, 90, 120]
RAIL = 3.5
CU, VERM, VERT = "#B8860B", OKABE_ITO["vermillon"], OKABE_ITO["vert"]

fig, axes = plt.subplots(2, 2, figsize=(12, 5.8))
for i, ax in enumerate(axes.flat):
    xc = SPOTS[i]
    x_soude = min(xc + MFC_X / 2, L)                 # bord droit de la zone soudée cumulée

    ax.add_patch(Rectangle((0, 0), L, W, facecolor="#EAF2F8", edgecolor="black", lw=1.2, zorder=1))
    # zone déjà soudée (rails aux deux chants, de 0 à x_soude)
    for y0 in (0.0, W - RAIL):
        ax.add_patch(Rectangle((0, y0), x_soude, RAIL, facecolor=VERT, alpha=0.55, edgecolor="none", zorder=1.5))
    # empreintes des passes précédentes (pointillé gris)
    for j in range(i):
        ax.add_patch(Rectangle((SPOTS[j] - MFC_X / 2, W / 2 - MFC_Y / 2), MFC_X, MFC_Y,
                               facecolor="none", edgecolor="0.6", lw=0.7, ls=":", zorder=2))
    # MFC + bobine — passe COURANTE
    ax.add_patch(Rectangle((xc - MFC_X / 2, W / 2 - MFC_Y / 2), MFC_X, MFC_Y,
                           facecolor=VERM, alpha=0.16, edgecolor=VERM, lw=1.6, ls="--", zorder=2.5))
    for dx in (-ENTRAXE / 2, ENTRAXE / 2):
        ax.add_patch(Rectangle((xc + dx - BRIN / 2, W / 2 - MFC_Y / 2), BRIN, MFC_Y,
                               facecolor=CU, alpha=0.7, edgecolor="none", zorder=3))
    # thermocouples
    ax.scatter(TC_X, [0] * len(TC_X), marker="x", s=32, color="#B00020", linewidths=1.7, zorder=5)

    ax.set_title(f"Passe {i + 1} — soudé : 0 → {x_soude:.0f} mm", fontsize=11, fontweight="bold")
    ax.set_xlim(-5, L + 5)
    ax.set_ylim(-9, W / 2 + MFC_Y / 2 + 2)
    ax.set_aspect("equal")
    ax.set_xticks([0, 30, 60, 90, 120])
    ax.set_yticks([0, 20, 40])
    ax.tick_params(labelsize=8)
    if i >= 2:
        ax.set_xlabel("Longueur x (mm)", fontsize=9)
    if i % 2 == 0:
        ax.set_ylabel("Largeur y (mm)", fontsize=9)

fig.suptitle("Storyboard — passages du MFC + coil (soudage semi-statique, avance 30 mm)",
             fontsize=13, fontweight="bold", y=0.99)

handles = [
    Rectangle((0, 0), 1, 1, facecolor=VERT, alpha=0.55, edgecolor="none", label="zone déjà soudée (rails)"),
    Rectangle((0, 0), 1, 1, facecolor=VERM, alpha=0.16, edgecolor=VERM, ls="--", label="MFC actif (empreinte)"),
    Rectangle((0, 0), 1, 1, facecolor=CU, alpha=0.7, edgecolor="none", label="brins de la bobine"),
    Rectangle((0, 0), 1, 1, facecolor="none", edgecolor="0.6", ls=":", label="passes précédentes"),
    plt.Line2D([0], [0], marker="x", color="#B00020", lw=0, markersize=8, markeredgewidth=1.7, label="thermocouples (bord)"),
]
fig.tight_layout(rect=(0, 0.08, 1, 0.94))
fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.005),
           ncol=5, fontsize=8.5, framealpha=0.95)

savefig(fig, R / "biblio" / "presentations" / "figures_schemas" / "fig_passages_mfc_storyboard")
print("figure -> biblio/presentations/figures_schemas/fig_passages_mfc_storyboard.png")
