#!/usr/bin/env python3
"""Courbes brutes T(t) des 5 thermocouples EN LONGUEUR — statique et semi-statique.

Historiques temporels bruts (°C absolus) des 5 TC répartis le long de la
LONGUEUR (x = 0/30/60/90/120 mm) de la campagne dissipation longitudinale
exp9, 200 A. Deux figures SÉPARÉES (une par mode de procédé) :
  - (a) statique  : mono-spot fixe à x=60 mm (200A_y0_monospot) ;
  - (b) semi-statique : spot avançant de 30 mm par passe (200A_y0_semistatique).

Le plateau ambiant répété en tête de courbe est retiré et le temps est re-calé
sur l'amorçage (t=0 = début de chauffe).

Sorties : biblio/labo/figures/fig_courbes_longueur_statique_brut.png
          biblio/labo/figures/fig_courbes_longueur_semistatique_brut.png
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
FIGDIR = R / "biblio" / "labo" / "figures"


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
    """Retire le plateau ambiant répété en tête (avant l'amorçage) et re-cale t=0.

    L'amorçage est détecté au premier instant où la plus chaude des 5 voies
    dépasse l'ambiant de 5 % de la montée totale ; on garde `margin` points de
    ligne de base avant, puis on ré-origine le temps sur ce point.
    """
    Y = np.vstack([series[i] for i in range(1, 6)])
    amb = np.nanmedian(Y[:, :3])
    peak = np.nanmax(Y)
    hot = np.nanmax(Y, axis=0) > amb + 0.05 * (peak - amb)
    start = max(0, int(np.argmax(hot)) - margin)
    return t[start:] - t[start], {i: series[i][start:] for i in range(1, 6)}


def figure_mode(fname: str, out: str):
    """Trace les 5 TC bruts d'un mode (statique ou semi-statique) dans sa propre figure."""
    t, series = load(DATA / fname)
    t, series = trim_lead(t, series)
    fig, ax = plt.subplots(1, 1, figsize=(6.2, 4.2))
    for i in range(1, 6):
        lab = f"TC{i} — x={X_MM[i - 1]} mm" + (" (centre)" if X_MM[i - 1] == 60 else "")
        ax.plot(t, series[i], "-", color=COLORS[i - 1], lw=1.3, label=lab)
    ax.axhline(T_FUSION, color="#4DA6FF", ls="--", lw=1.0, label="Fusion PEKK (337 °C)")
    ax.set_xlabel("Temps (s)")
    ax.set_ylabel("Température (°C)")
    ax.set_xlim(0, t[-1])
    ax.legend(fontsize=8, loc="upper right", framealpha=0.9)
    fig.tight_layout()
    savefig(fig, FIGDIR / out)
    plt.close(fig)
    print(f"figure -> biblio/labo/figures/{out}.png")


figure_mode("200A_y0_monospot.txt", "fig_courbes_longueur_statique_brut")
figure_mode("200A_y0_semistatique.txt", "fig_courbes_longueur_semistatique_brut")
