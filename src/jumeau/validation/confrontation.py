"""Confrontation simulation <-> mesures : métriques par thermocouple."""

from __future__ import annotations

import numpy as np
import pandas as pd


def taux_de_chauffe(t: np.ndarray, T: np.ndarray, T_ref: float = 75.0) -> float:
    """Pente (°C/s) au passage de T_ref pendant la montée (métrique Grouve 2020)."""
    dT = np.gradient(np.asarray(T, float), np.asarray(t, float))
    montee = np.where((T[:-1] < T_ref) & (T[1:] >= T_ref))[0]
    if len(montee) == 0:
        return float("nan")
    return float(dT[montee[0]])


def metriques_tc(t_sim: np.ndarray, T_sim: np.ndarray,
                 t_mes: np.ndarray, T_mes: np.ndarray) -> dict:
    """RMSE, T max, écart de T max et taux de chauffe sim vs mesure (grille mesure)."""
    T_interp = np.interp(t_mes, t_sim, T_sim)
    return {
        "rmse": float(np.sqrt(np.mean((T_interp - T_mes) ** 2))),
        "T_max_sim": float(np.max(T_sim)),
        "T_max_mes": float(np.max(T_mes)),
        "delta_T_max": float(np.max(T_sim) - np.max(T_mes)),
        "taux_sim": taux_de_chauffe(t_sim, T_sim),
        "taux_mes": taux_de_chauffe(t_mes, T_mes),
    }


def rapport_essai(series_sim: dict[str, np.ndarray], t_sim: np.ndarray,
                  df_mes: pd.DataFrame, tc_valides: list[str]) -> pd.DataFrame:
    """Tableau de métriques par TC (lignes = TC valides de l'essai)."""
    tcol = df_mes.columns[0]
    t_mes = df_mes[tcol].values
    lignes = []
    for tc in tc_valides:
        col = next((c for c in df_mes.columns if c.startswith(tc)), None)
        if col is None or tc not in series_sim:
            continue
        m = metriques_tc(t_sim, series_sim[tc], t_mes, df_mes[col].values)
        m["TC"] = tc
        lignes.append(m)
    return pd.DataFrame(lignes).set_index("TC")
