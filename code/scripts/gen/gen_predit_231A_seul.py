#!/usr/bin/env python3
"""Validation 231 A — TC PRÉDITS SEULS (sans données banc).

Même modèle et même mise en page que gen_compare_230A_vs_reel.py, mais on
n'affiche QUE les 5 TC prédits par le jumeau (modèle 2D, θ*, pilotage TC=360
modèle ≈ 390 réel). Aucune courbe mesurée : figure « simulation seule » pour
présenter la prédiction du cycle 231 A indépendamment de l'essai.

Sortie : biblio/labo/figures/fig_predit_231A_seul.png
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts" / "gen"))
sys.path.insert(0, str(R / "code" / "scripts"))
import gen_cycle_230A_TC390 as m  # noqa: E402
from _style import savefig, OKABE_ITO  # noqa: E402

COURANT = 231.0
COUL = [OKABE_ITO[c] for c in ("noir", "bleu", "vert", "orange", "vermillon")]


if __name__ == "__main__":
    print("simulation du modèle (231 A)…")
    res = m.simuler_cycle_tc(COURANT)
    t_sim, series_sim, noms = res["t"], res["series"], res["noms"]

    fig, ax = plt.subplots(figsize=(11.5, 5.2))
    for nom, coul in zip(noms, COUL):
        ax.plot(t_sim, series_sim[nom], color=coul, lw=1.6, label=f"{nom} prédit")
    ax.axhline(390, color=OKABE_ITO["vert"], lw=0.9, ls="--", zorder=1)
    ax.axhline(337, color=OKABE_ITO["cyan"], lw=0.9, ls=":", zorder=1)
    ax.text(ax.get_xlim()[1], 393, " consigne 390", fontsize=7.5,
            color=OKABE_ITO["vert"], va="bottom", ha="right")

    ax.set_xlim(0, t_sim[-1])
    ax.set_ylim(0, 560)
    ax.set_xlabel("Temps (s)")
    ax.set_ylabel("Température (°C)")
    ax.set_title("Simulation 231 A — TC prédits (modèle seul)",
                 fontsize=12, fontweight="bold")
    ax.legend(loc="upper right", ncol=1, fontsize=8, framealpha=0.93)
    fig.tight_layout()
    savefig(fig, R / "biblio" / "labo" / "figures" / "fig_predit_231A_seul")
    plt.close(fig)

    print("\n=== Pics prédits (modèle, 231 A) ===")
    for nom in noms:
        print(f"{nom:>4} | {float(np.max(series_sim[nom])):7.0f} °C")
    print("figure -> biblio/labo/figures/fig_predit_231A_seul.png")
