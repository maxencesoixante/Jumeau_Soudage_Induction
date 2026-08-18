"""Chargement des fichiers de mesures thermocouples (CSV corrigés + TXT LabVIEW).

Logique portée du notebook du vault ``40_donnees/tracer_courbes_thermocouples.ipynb`` :
- auto-détection séparateur (tab/virgule) et décimale (point/virgule) ;
- temps remis à zéro au premier échantillon ;
- valeurs aberrantes (> seuil, TC débranché lit ~2295 °C rail, ou < -20 °C)
  remplacées par interpolation.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def charger_mesures(chemin: str | Path, corriger: bool = True,
                    seuil_aberrant: float = 400.0,
                    t_min: float | None = None, t_max: float | None = None) -> pd.DataFrame:
    """Renvoie un DataFrame ``Time (s), TC1 (C), ..., TC5 (C)`` nettoyé.

    ``seuil_aberrant`` : au-delà -> NaN interpolé (défaut 400 °C comme le
    notebook du vault ; passer p.ex. 2000 pour garder des pics réels > 400).
    """
    chemin = Path(chemin)
    with open(chemin, encoding="utf-8", errors="replace") as f:
        f.readline()
        ligne = f.readline()
    sep = "\t" if "\t" in ligne else ","
    dec = "," if (sep == "\t" and ligne.count(",") > ligne.count(".")) else "."
    df = pd.read_csv(chemin, sep=sep, decimal=dec, engine="python")
    df.columns = [c.strip() for c in df.columns]
    tcol = df.columns[0]
    df[tcol] = df[tcol].astype(float) - float(df[tcol].iloc[0])
    if t_min is not None:
        df = df[df[tcol] >= t_min]
    if t_max is not None:
        df = df[df[tcol] <= t_max]
    df = df.reset_index(drop=True)
    if corriger:
        for c in df.columns[1:]:
            v = df[c].astype(float).copy()
            v[(v > seuil_aberrant) | (v < -20.0)] = np.nan
            df[c] = v.interpolate(limit_direction="both")
    return df


def detecter_debut_chauffe(df: pd.DataFrame, seuil_pente: float = 1.0) -> float:
    """Instant où la chauffe démarre (première pente > seuil_pente °C/s sur un TC).

    Utile pour les TXT bruts dont l'acquisition démarre avant la chauffe.
    """
    tcol = df.columns[0]
    t = df[tcol].values
    for c in df.columns[1:]:
        v = df[c].values
        dv = np.gradient(v, t)
        idx = np.where(dv > seuil_pente)[0]
        if len(idx):
            return float(t[idx[0]])
    return 0.0


def recaler_a_la_chauffe(df: pd.DataFrame, seuil_pente: float = 1.0) -> pd.DataFrame:
    """Tronque avant le début de chauffe et remet t=0 à cet instant."""
    tcol = df.columns[0]
    t0 = detecter_debut_chauffe(df, seuil_pente)
    df2 = df[df[tcol] >= t0].reset_index(drop=True).copy()
    df2[tcol] = df2[tcol] - float(df2[tcol].iloc[0])
    return df2
