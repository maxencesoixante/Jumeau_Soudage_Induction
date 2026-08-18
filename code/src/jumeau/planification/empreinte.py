"""Empreinte thermique d'une passe unique : carte du pic Tmax(x,y) à l'interface."""

from __future__ import annotations

import copy
from itertools import product
from pathlib import Path

import numpy as np

from ..materiaux import Config
from ..procede import Essai
from ..geometrie import masque_empreinte_cfc
from ..em.source_joule import source_spot

_RACINE = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())  # racine depot
_GABARIT = _RACINE / "code" / "config" / "essais" / "exp7_200A.yaml"


def empreinte(cfg: Config, x_c: float, y_c: float, courant: float, duree: float,
              *, mfc_longueur: float | None = None,
              facteur: float = 6.0123, nx: int = 61, ny: int = 21, nz: int = 15):
    """Simule une passe (spot en (x_c, y_c), courant, durée) et renvoie
    ``(grille, Tmax)`` — ``Tmax(x, y)`` = pic de température d'interface. θ* figé.

    ``mfc_longueur`` (m ; ``None`` = MFC labo 55 mm, sans masquage = comportement
    historique) : si renseigné, réduit le concentrateur (``cfc.longueur`` en
    mémoire, patron de ``scripts/gen/gen_mfc_reduit.py``) et **masque la source Joule
    à l'empreinte du MFC** posée en ``(x_c, y_c)`` — source localisée sous un MFC
    réduit (levier #39)."""
    masque_mfc = mfc_longueur is not None
    if masque_mfc:
        cfg = copy.deepcopy(cfg)
        cfg.geometrie["cfc"]["longueur"] = float(mfc_longueur)
    cfg.contact.h_haut = 30.087
    cfg.ambiant.h_bas_2d = 37.424
    cfg.ambiant.h_bord_x0 = 250.0
    e = Essai(cfg, _GABARIT, nx=nx, ny=ny, nz=nz, facteur_couplage=facteur,
              decalage_x=0.0, racine=_RACINE, masque_source_mfc=masque_mfc)
    e.spots[0]["centre_x"] = x_c
    e.spec["duree_chauffe"] = duree
    e.spec["duree_totale"] = duree
    e.spots[0]["t_fin"] = duree
    # masque céramique/MFC recentré sous la passe (x_c, y_c)
    mask2d = masque_empreinte_cfc(e.grille, cfg, x_c, centre_y=y_c)
    e._masques = [mask2d]
    Q = source_spot(e.grille, cfg, e.couches, courant, x_c,
                    facteur_couplage=facteur, centre_y=y_c)
    if masque_mfc:                       # source coupée à l'empreinte du MFC réduit
        Q = Q * mask2d[:, :, None]
    e._Q_spots = [Q]
    e._P_spots_2d = [Q.sum(axis=2) * e.grille.dz]
    sv, sol = e.simuler(modele="2D")
    champs = np.array([sv.resultat_2d(sol, i) for i in range(sol.t.size)])  # (nt, nx, ny)
    return e.grille, champs.max(axis=0)


def bibliotheque(cfg: Config, x_cs, y_cs, courants, duree, *, mfc_longueurs=(None,),
                 facteur: float = 6.0123, nx: int = 61, ny: int = 21, nz: int = 15):
    """Pré-calcule les empreintes sur la grille
    (``x_cs`` × ``y_cs`` × ``courants`` × ``mfc_longueurs``).
    Renvoie ``(grille, {(x_c, y_c, courant, mfc_longueur): Tmax(x, y)})``.
    ``mfc_longueurs`` = largeurs de MFC (``None`` = MFC labo 55 mm)."""
    lib = {}
    grille = None
    for x_c, y_c, I, mfc in product(x_cs, y_cs, courants, mfc_longueurs):
        g, T = empreinte(cfg, x_c, y_c, I, duree, mfc_longueur=mfc,
                         facteur=facteur, nx=nx, ny=ny, nz=nz)
        grille = g
        mfc_cle = round(mfc, 6) if mfc is not None else None
        lib[(round(x_c, 6), round(y_c, 6), round(I, 3), mfc_cle)] = T
    return grille, lib
