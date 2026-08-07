"""Empreinte thermique d'une passe unique : carte du pic Tmax(x,y) à l'interface."""

from __future__ import annotations

from itertools import product
from pathlib import Path

import numpy as np

from ..materiaux import Config
from ..procede import Essai
from ..em.source_joule import source_spot

_RACINE = Path(__file__).resolve().parents[3]
_GABARIT = _RACINE / "config" / "essais" / "exp7_200A.yaml"


def empreinte(cfg: Config, x_c: float, y_c: float, courant: float, duree: float,
              *, facteur: float = 6.0123, nx: int = 61, ny: int = 21, nz: int = 15):
    """Simule une passe (spot en (x_c, y_c), courant, durée) et renvoie
    ``(grille, Tmax)`` — ``Tmax(x, y)`` = pic de température d'interface pendant
    la passe. θ* de référence figé (aucune recalibration)."""
    cfg.contact.h_haut = 30.087
    cfg.ambiant.h_bas_2d = 37.424
    cfg.ambiant.h_bord_x0 = 250.0
    e = Essai(cfg, _GABARIT, nx=nx, ny=ny, nz=nz,
              facteur_couplage=facteur, decalage_x=0.0, racine=_RACINE)
    e.spots[0]["centre_x"] = x_c
    e.spec["duree_chauffe"] = duree
    e.spec["duree_totale"] = duree
    e.spots[0]["t_fin"] = duree
    Q = source_spot(e.grille, cfg, e.couches, courant, x_c,
                    facteur_couplage=facteur, centre_y=y_c)
    e._Q_spots = [Q]
    e._P_spots_2d = [Q.sum(axis=2) * e.grille.dz]
    sv, sol = e.simuler(modele="2D")
    champs = np.array([sv.resultat_2d(sol, i) for i in range(sol.t.size)])  # (nt, nx, ny)
    return e.grille, champs.max(axis=0)


def bibliotheque(cfg: Config, x_cs, y_cs, courants, duree,
                 *, facteur: float = 6.0123, nx: int = 61, ny: int = 21, nz: int = 15):
    """Pré-calcule les empreintes sur la grille (``x_cs`` × ``y_cs`` × ``courants``).
    Renvoie ``(grille, {(x_c, y_c, courant): Tmax(x, y)})``."""
    lib = {}
    grille = None
    for x_c, y_c, I in product(x_cs, y_cs, courants):
        g, T = empreinte(cfg, x_c, y_c, I, duree,
                         facteur=facteur, nx=nx, ny=ny, nz=nz)
        grille = g
        lib[(round(x_c, 6), round(y_c, 6), round(I, 3))] = T
    return grille, lib
