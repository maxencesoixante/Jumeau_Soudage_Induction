"""Balayage held-out de `h_bord_x0` (2026-09-06) -- deux panneaux.

Gauche : RMSE moyen par essai de soudage en fonction de `h_bord_x0`, à θ*
canonique par ailleurs inchangé (facteur 6.0123, decalage_x 0), SANS
recalibration. Droite : écart de pic du thermocouple TC1, le seul posé
exactement au chant x = 0 où le puits agit.

Données : `biblio/labo/reouverture_h_bord_x0_heldout.md` (rejouables par
`python code/scripts/valider.py --modele 2D --facteur 6.0123 --decalage-x 0
--h-bord-x0 <H> --essais serieA_A-1 serieA_A-3 serieB_B-2`).

N'écrit QUE le PNG de sortie.
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _style import apply_style, OKABE_ITO  # noqa: E402

apply_style(**{
    "font.size": 10, "axes.labelsize": 10.5, "axes.titlesize": 10.5,
    "legend.fontsize": 8.8, "xtick.labelsize": 9.5, "ytick.labelsize": 9.5,
    "axes.linewidth": 0.9, "lines.linewidth": 1.7, "savefig.pad_inches": 0.06,
    "figure.facecolor": "white", "savefig.facecolor": "white",
})

H = np.array([0, 50, 100, 125, 150, 200, 250, 350], float)

RMSE = {                                     # °C, RMSE moyen par essai
    "A-1 (250 A)":  [40.0, 36.5, 35.2, 35.0, 35.1, 35.7, 36.5, 38.1],
    "A-3 (200 A)":  [32.8, 31.4, 31.4, 31.6, 31.9, 32.6, 33.4, 34.8],
    "B-2 (250 A)":  [69.1, 66.2, 65.2, 65.1, 65.0, 65.2, 65.6, 66.5],
}
DPIC_TC1 = {                                 # °C, écart de pic simulé - mesuré
    "A-1 (250 A)":  [97.6, 54.0, 15.5, -2.8, -21.3, -55.5, -70.1, -111.5],
    "A-3 (200 A)":  [65.6, 18.2, -26.4, -52.0, -64.2, -89.5, -107.4, -139.9],
    "B-2 (250 A)":  [28.3, -17.3, -32.7, -39.4, -46.7, -59.9, -72.2, -96.9],
}
COULEURS = {"A-1 (250 A)": OKABE_ITO["bleu"],
            "A-3 (200 A)": OKABE_ITO["vermillon"],
            "B-2 (250 A)": OKABE_ITO["vert"]}
MARQ = {"A-1 (250 A)": "o", "A-3 (200 A)": "s", "B-2 (250 A)": "^"}

H_ADOPTE, H_ANCIEN = 125.0, 250.0

fig, (axg, axd) = plt.subplots(1, 2, figsize=(11.4, 4.5))

# ---------------------------------------------------------------- panneau RMSE
axg.axvspan(100, 150, color="0.85", alpha=0.55, zorder=0, lw=0)
for nom, y in RMSE.items():
    axg.plot(H, y, marker=MARQ[nom], ms=5, color=COULEURS[nom], label=nom)

axg.set_xlabel("$h_{bord,x0}$  (W·m⁻²·K⁻¹)")
axg.set_ylabel("RMSE moyen (°C)")
axg.set_title("Chaque essai a son optimum entre 100 et 150 (bande grise)", fontsize=10.5)
axg.legend(title="essai de soudage (held-out)", loc="center right", frameon=True,
           framealpha=0.95, handlelength=1.8, borderpad=0.6)
axg.set_ylim(29, 72)


# ------------------------------------------------------------ panneau pic TC1
axd.axhline(0, color="0.35", lw=1.0, ls="-", zorder=1)
for nom, y in DPIC_TC1.items():
    axd.plot(H, y, marker=MARQ[nom], ms=5, color=COULEURS[nom], label=nom)
axd.set_xlabel("$h_{bord,x0}$  (W·m⁻²·K⁻¹)")
axd.set_ylabel("Écart de pic sur TC1, au chant $x=0$ (°C)")
axd.set_title("Le capteur du chant : trop chaud à gauche, trop froid à droite", fontsize=10.5)
axd.text(348, 72, "modèle trop CHAUD\nau chant", fontsize=8.8, color="0.3",
         va="center", ha="right", linespacing=1.35)
axd.text(18, -132, "modèle trop FROID\nau chant", fontsize=8.8, color="0.3",
         va="center", ha="left", linespacing=1.35)
axd.set_ylim(-152, 115)

# ------------------------------------------------- repères communs 125 vs 250
for ax in (axg, axd):
    ax.axvline(H_ANCIEN, color="0.55", lw=1.2, ls=":", zorder=2)
    ax.axvline(H_ADOPTE, color="0.15", lw=1.4, ls="--", zorder=2)
    ax.set_xlim(-12, 362)
    ax.grid(True, alpha=0.25, linewidth=0.5)
    y0, y1 = ax.get_ylim()
    yb = y0 + 0.03 * (y1 - y0)
    ax.text(H_ADOPTE - 7, yb, "125 adopté", rotation=90, fontsize=8.4,
            color="0.10", ha="right", va="bottom", fontweight="bold")
    ax.text(H_ANCIEN + 7, yb, "250 ancien", rotation=90, fontsize=8.4,
            color="0.45", ha="left", va="bottom")

fig.suptitle("Puits de bord $h_{bord,x0}$ — validation croisée, θ* par ailleurs inchangé "
             "(exp7 et exp9 strictement insensibles)", fontsize=11, y=0.995)
fig.tight_layout(rect=(0, 0, 1, 0.96))

OUT = R / "biblio" / "labo" / "figures" / "issue69" / "hbord_sweep_heldout.png"
fig.savefig(OUT)
print("écrit :", OUT)
