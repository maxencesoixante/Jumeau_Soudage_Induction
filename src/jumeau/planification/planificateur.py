"""Planificateur glouton PUR : couvre une surface avec des empreintes Tmax,
sous contrainte de non-dégradation. Indépendant du modèle (opère sur des cartes)."""

from __future__ import annotations

import numpy as np


def metriques(Tmax: np.ndarray, *, fusion: float = 337.0, degrad: float = 450.0) -> dict:
    """Pourcentages de surface : soudée (fusion..degrad), non soudée (<fusion),
    dégradée (>=degrad)."""
    n = Tmax.size
    degrade = Tmax >= degrad
    soude = (Tmax >= fusion) & ~degrade
    return {
        "pct_soude": 100.0 * float(soude.sum()) / n,
        "pct_non_soude": 100.0 * float((Tmax < fusion).sum()) / n,
        "pct_degrade": 100.0 * float(degrade.sum()) / n,
    }


def planifier(lib: dict, *, ambiant: float = 20.0, fusion: float = 337.0,
              degrad: float = 450.0):
    """Glouton : ajoute à chaque étape la passe qui soude le plus de NOUVELLE
    surface sans faire dépasser ``degrad`` nulle part. Renvoie
    ``(passes_ordonnees, Tmax_combine, metriques)``."""
    ref = next(iter(lib.values()))
    combine = np.full_like(ref, ambiant, dtype=float)
    passes, restants = [], dict(lib)
    while True:
        meilleur, meilleur_gain, meilleur_comb = None, 0, None
        deja_soude = int((combine >= fusion).sum())
        for cle, emp in restants.items():
            cand = np.maximum(combine, emp)
            if (cand >= degrad).any():          # contrainte dure : pas de dégradation
                continue
            gain = int((cand >= fusion).sum()) - deja_soude
            if gain > meilleur_gain:
                meilleur, meilleur_gain, meilleur_comb = cle, gain, cand
        if meilleur is None:                     # plus aucune amélioration
            break
        combine = meilleur_comb
        passes.append(meilleur)
        del restants[meilleur]
    return passes, combine, metriques(combine, fusion=fusion, degrad=degrad)
