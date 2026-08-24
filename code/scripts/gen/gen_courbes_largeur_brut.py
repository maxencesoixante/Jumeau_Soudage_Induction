#!/usr/bin/env python3
"""Courbes brutes T(t) des 5 thermocouples EN LARGEUR — profil bord->centre.

Historiques temporels bruts (°C absolus) des 5 TC répartis sur la LARGEUR
(y = 0/10/20/30/40 mm, x = 60 mm, spot centré) de la campagne bord->centre
avec céramique (exp7, 200 A, essai v6) : les chants (y=0 et y=40 mm) chauffent
le plus, le centre (y=20 mm) le moins — c'est le profil en « M ».

Le plateau ambiant répété en tête de courbe est retiré et le temps est re-calé
sur l'amorçage (t=0 = début de chauffe), comme pour les figures en longueur.

Sortie : biblio/labo/figures/fig_courbes_largeur_brut.png
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts"))
from _style import apply_style, savefig  # noqa: E402
apply_style()

DATA = (R / "donnees" / "data"
        / "exp7_bord-centre_2026-07-28_avec-ceramique" / "200A" / "200A_v6.txt")
Y_MM = [0, 10, 20, 30, 40]
COLORS = ["#0072B2", "#009E73", "#E69F00", "#D55E00", "#CC79A7"]  # Okabe-Ito
T_FUSION = 337.0


def load(path: Path):
    df = pd.read_csv(path, sep="\t", decimal=",")
    df.columns = [c.strip() for c in df.columns]
    t = df["Time (s)"].to_numpy(dtype=float)
    t = t - t[0]
    series = {}
    for i in range(1, 6):
        col = next(c for c in df.columns if c.startswith(f"TC{i}"))
        y = df[col].to_numpy(dtype=float).copy()
        y[(y > 500) | (y < 0)] = np.nan            # voie débranchée / aberrant
        idx = np.arange(len(y))
        ok = ~np.isnan(y)
        if ok.sum() > 1:
            y = np.interp(idx, idx[ok], y[ok])
        series[i] = y
    return t, series


def trim_lead(t, series, margin=2):
    """Retire le plateau ambiant répété en tête (avant l'amorçage) et re-cale t=0."""
    Y = np.vstack([series[i] for i in range(1, 6)])
    amb = np.nanmedian(Y[:, :3])
    peak = np.nanmax(Y)
    hot = np.nanmax(Y, axis=0) > amb + 0.05 * (peak - amb)
    start = max(0, int(np.argmax(hot)) - margin)
    return t[start:] - t[start], {i: series[i][start:] for i in range(1, 6)}


t, series = load(DATA)
t, series = trim_lead(t, series)

fig, ax = plt.subplots(1, 1, figsize=(6.2, 4.2))
for i in range(1, 6):
    est_bord = Y_MM[i - 1] in (0, 40)
    suffix = " (chant)" if est_bord else (" (centre)" if Y_MM[i - 1] == 20 else "")
    ax.plot(t, series[i], "-", color=COLORS[i - 1], lw=1.3,
            label=f"TC{i} — y={Y_MM[i - 1]} mm{suffix}")
ax.axhline(T_FUSION, color="#4DA6FF", ls="--", lw=1.0, label="Fusion PEKK (337 °C)")
ax.set_xlabel("Temps (s)")
ax.set_ylabel("Température (°C)")
ax.set_xlim(0, t[-1])
ax.legend(fontsize=8, loc="upper right", framealpha=0.9)

fig.tight_layout()
savefig(fig, R / "biblio" / "labo" / "figures" / "fig_courbes_largeur_brut")
print("figure -> biblio/labo/figures/fig_courbes_largeur_brut.png")
