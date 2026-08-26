#!/usr/bin/env python3
"""Animation GIF — passages du MFC + coil (soudage semi-statique).

Vue de dessus : le MFC + bobine s'arrête sur chaque spot (dwell = soudage, la
zone soudée se remplit sous l'empreinte), puis avance de 30 mm au spot suivant,
jusqu'à souder toute la longueur (4 passes). Positions exp9/serieA-B.

Sortie : biblio/presentations/figures_schemas/fig_passages_mfc.gif
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.animation import FuncAnimation, PillowWriter

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts"))
from _style import apply_style, OKABE_ITO  # noqa: E402
apply_style(fonts_only=True)

L, W = 120.0, 40.0
SPOTS = [15.875, 45.875, 75.875, 105.875]
MFC_X, MFC_Y = 31.5, 55.0
ENTRAXE, BRIN = 12.35, 6.0
TC_X = [0, 30, 60, 90, 120]
RAIL = 3.5
CU, VERM, VERT = "#B8860B", OKABE_ITO["vermillon"], OKABE_ITO["vert"]

N_DWELL, N_MOVE, N_HOLD = 12, 8, 10

# --- séquence de frames : (mfc_x, welded_x, phase) ---
frames = []
welded = 0.0
for i, xc in enumerate(SPOTS):
    target = min(xc + MFC_X / 2, L)
    for f in range(N_DWELL):                       # dwell : soudage, la zone se remplit
        w = welded + (target - welded) * (f + 1) / N_DWELL
        frames.append((xc, w, f"Passe {i + 1}/4 — soudage (dwell)"))
    welded = target
    if i < len(SPOTS) - 1:                          # déplacement +30 mm
        for f in range(N_MOVE):
            mx = xc + (SPOTS[i + 1] - xc) * (f + 1) / N_MOVE
            frames.append((mx, welded, "Déplacement +30 mm"))
for _ in range(N_HOLD):
    frames.append((SPOTS[-1], welded, "Terminé — toute la longueur soudée"))

fig, ax = plt.subplots(figsize=(9.2, 3.7), dpi=100)


def draw(k):
    mfc_x, welded_x, phase = frames[k]
    ax.clear()
    ax.add_patch(Rectangle((0, 0), L, W, facecolor="#EAF2F8", edgecolor="black", lw=1.2, zorder=1))
    for y0 in (0.0, W - RAIL):                      # zone déjà soudée (rails)
        ax.add_patch(Rectangle((0, y0), welded_x, RAIL, facecolor=VERT, alpha=0.6, edgecolor="none", zorder=1.5))
    ax.add_patch(Rectangle((mfc_x - MFC_X / 2, W / 2 - MFC_Y / 2), MFC_X, MFC_Y,
                           facecolor=VERM, alpha=0.16, edgecolor=VERM, lw=1.6, ls="--", zorder=2))
    for dx in (-ENTRAXE / 2, ENTRAXE / 2):
        ax.add_patch(Rectangle((mfc_x + dx - BRIN / 2, W / 2 - MFC_Y / 2), BRIN, MFC_Y,
                               facecolor=CU, alpha=0.7, edgecolor="none", zorder=3))
    ax.scatter(TC_X, [0] * len(TC_X), marker="x", s=28, color="#B00020", linewidths=1.6, zorder=5)
    ax.text(0.5, 1.06, phase, transform=ax.transAxes, ha="center", va="bottom",
            fontsize=11.5, fontweight="bold", color="0.15")
    ax.text(0.985, 0.055, f"soudé : 0 → {welded_x:.0f} mm", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=9.5, color=VERT, fontweight="bold")
    ax.set_xlim(-5, L + 5)
    ax.set_ylim(-9, W / 2 + MFC_Y / 2 + 2)
    ax.set_aspect("equal")
    ax.set_xticks([0, 30, 60, 90, 120])
    ax.set_yticks([0, 20, 40])
    ax.set_xlabel("Longueur x (mm)")
    ax.set_ylabel("Largeur y (mm)")
    return []


if __name__ == "__main__":
    anim = FuncAnimation(fig, draw, frames=len(frames), blit=False)
    out = R / "biblio" / "presentations" / "figures_schemas" / "fig_passages_mfc.gif"
    anim.save(str(out), writer=PillowWriter(fps=10))
    plt.close(fig)
    print(f"animation ({len(frames)} frames) -> {out.relative_to(R)}")
