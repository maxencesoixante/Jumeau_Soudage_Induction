"""Planificateur glouton PUR : couvre une surface avec des empreintes Tmax,
sous contrainte de non-dégradation. Indépendant du modèle (opère sur des cartes)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ..materiaux import Config
from ..procede import Essai
from ..geometrie import masque_empreinte_cfc
from ..em.source_joule import source_spot

_RACINE = Path(__file__).resolve().parents[3]
_GABARIT = _RACINE / "config" / "essais" / "exp7_200A.yaml"


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


def verifier_sequentiel(cfg: Config, passes_params, *, facteur: float = 6.0123,
                        nx: int = 61, ny: int = 21, nz: int = 15):
    """Rejoue le plan en UNE séquence multi-passes (chaleur résiduelle incluse)
    et renvoie ``(grille, Tmax_reel(x, y))``. Chaque passe = un spot successif
    (patron de ``scripts/gen_procede_semistatique.py``). ``passes_params`` = liste
    de dicts ``{"x_c", "y_c", "courant", "duree"}``."""
    cfg.contact.h_haut = 30.087
    cfg.ambiant.h_bas_2d = 37.424
    cfg.ambiant.h_bord_x0 = 250.0
    e = Essai(cfg, _GABARIT, nx=nx, ny=ny, nz=nz,
              facteur_couplage=facteur, decalage_x=0.0, racine=_RACINE)
    t = 0.0
    spots, Qs = [], []
    for p in passes_params:
        spots.append({"centre_x": p["x_c"], "t_debut": t, "t_fin": t + p["duree"]})
        Qs.append(source_spot(e.grille, cfg, e.couches, p["courant"], p["x_c"],
                              facteur_couplage=facteur, centre_y=p["y_c"]))
        t += p["duree"]
    e.spots = spots
    # reconstruire les masques céramique/MFC pour matcher les NOUVELLES passes
    # (le gabarit exp7 n'a qu'un spot ; sans ça masque_fn indexe hors bornes).
    e._masques = [masque_empreinte_cfc(e.grille, cfg, p["x_c"], centre_y=p["y_c"])
                  for p in passes_params]
    e._Q_spots = Qs
    e._P_spots_2d = [Q.sum(axis=2) * e.grille.dz for Q in Qs]
    e.spec["duree_chauffe"] = t
    e.spec["duree_totale"] = t
    sv, sol = e.simuler(modele="2D")
    champs = np.array([sv.resultat_2d(sol, i) for i in range(sol.t.size)])
    return e.grille, champs.max(axis=0)
