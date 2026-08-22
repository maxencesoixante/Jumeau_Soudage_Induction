#!/usr/bin/env python3
"""Courbes brutes T(t) des 5 thermocouples EN LONGUEUR — statique vs semi-statique.

Historiques temporels bruts (°C absolus) des 5 TC répartis le long de la
LONGUEUR (x = 0/30/60/90/120 mm) de la campagne dissipation longitudinale
exp9, 200 A :
  - (a) statique  : mono-spot fixe à x=60 mm (200A_y0_monospot) ;
  - (b) semi-statique : spot avançant de 30 mm par passe (200A_y0_semistatique).

Sortie : biblio/labo/figures/fig_courbes_longueur_brut.png
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

DATA = R / "donnees" / "data" / "exp9_dissipation-longitudinale_2026-07-28" / "200A"
X_MM = [0, 30, 60, 90, 120]
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


fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
panels = ((a, "200A_y0_monospot.txt", "(a) Statique — mono-spot (x=60 mm)"),
          (b, "200A_y0_semistatique.txt", "(b) Semi-statique — spot avançant (30 mm/passe)"))
for ax, fname, titre in panels:
    t, series = load(DATA / fname)
    for i in range(1, 6):
        lab = f"TC{i} — x={X_MM[i - 1]} mm" + (" (centre)" if X_MM[i - 1] == 60 else "")
        ax.plot(t, series[i], "-", color=COLORS[i - 1], lw=1.3, label=lab)
    ax.axhline(T_FUSION, color="#4DA6FF", ls="--", lw=1.0,
               label="Fusion PEKK (337 °C)" if ax is a else None)
    ax.set_title(titre)
    ax.set_xlabel("Temps (s)")
    ax.set_xlim(0, t[-1])
a.set_ylabel("Température (°C)")
a.legend(fontsize=8, loc="upper right", framealpha=0.9)

fig.suptitle("Historiques bruts des 5 TC en longueur — statique vs semi-statique, 200 A",
             fontsize=12, fontweight="bold")
fig.tight_layout()
savefig(fig, R / "biblio" / "labo" / "figures" / "fig_courbes_longueur_brut")
print("figure -> biblio/labo/figures/fig_courbes_longueur_brut.png")
