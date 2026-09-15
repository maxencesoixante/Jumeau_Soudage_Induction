"""Empreinte thermique d'une passe unique : carte du pic Tmax(x,y) à l'interface.

DEUX CORRECTIONS DE FOND, 2026-09-15 — lire avant de comparer à un ancien plan.

1. θ* — ce module FIGEAIT ``h_bord_x0 = 250``, valeur périmée depuis le
   2026-09-06 (re-calibrée 250 -> 125, commit fc92052) et écrasée EN DUR par
   dessus la config. `code/tests/test_planification.py` posait déjà 125 en
   commentant « θ* canonique » : l'override annulait silencieusement l'intention
   du test. La valeur vient désormais de la config ; ``h_bord_x0=250.0`` en
   argument reproduit à l'identique les plans d'avant cette date (#31/#37/#39).

2. FAMILLE DE MODÈLE MFC — un MFC raccourci n'a pas UN modèle mais QUATRE, qui
   ne diffèrent pas par leur finesse mais par une hypothèse physique : que
   devient le flux qui n'est plus sous le bloc de ferrite ? (cf.
   `biblio/modele/prediction_mfc_familles.md`)

       "tronquer"           il DISPARAÎT    -- Q coupé à l'empreinte, sans report
       "conserver"          il SE RECONCENTRE sous le bloc restant (famille A)
       "image_observation"  il ne se reconcentre pas : hors du bloc on retombe
       "image_source"       au cas sans MFC (famille B, deux troncatures duales)

   Le planificateur historique n'a jamais essayé que ``"tronquer"``, c'est-à-dire
   la variante la PLUS défavorable des quatre — celle qui retire la puissance au
   lieu de la déplacer. Le verdict « le MFC réduit ne débloque pas le centre »
   (#39) porte donc sur ce seul cas. Les deux variantes B n'existaient pas
   (livrées le 2026-09-14, commit e05d2e4).

Le défaut par défaut reste ``"tronquer"`` pour ne pas déplacer sous les pieds
des appelants existants ; le choix est explicite dans les scripts.

Note : ``cfg`` n'est plus muté en place (l'ancienne version écrivait le θ* dans
la config de l'appelant à chaque appel).
"""

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

FAMILLES = ("tronquer", "conserver", "image_observation", "image_source")


def empreinte(cfg: Config, x_c: float, y_c: float, courant: float, duree: float,
              *, mfc_longueur: float | None = None, famille: str = "tronquer",
              h_bord_x0: float | None = None,
              facteur: float = 6.0123, nx: int = 61, ny: int = 21, nz: int = 15):
    """Simule une passe (spot en (x_c, y_c), courant, durée) et renvoie
    ``(grille, Tmax)`` — ``Tmax(x, y)`` = pic de température d'interface. θ* figé.

    ``mfc_longueur`` (m ; ``None`` = MFC labo 55 mm, aucun traitement de
    réduction) : si renseigné, réduit le concentrateur (``cfc.longueur`` en
    mémoire) et applique le modèle de réduction choisi par ``famille``.

    ``famille`` — n'a d'effet QUE si ``mfc_longueur`` est renseigné ; voir la
    docstring du module pour l'hypothèse physique de chacune des quatre.

    ``h_bord_x0`` (W/m².K ; ``None`` = valeur de la config, canonique 125) :
    passer 250.0 pour reproduire les plans antérieurs au 2026-09-06.
    """
    if famille not in FAMILLES:
        raise ValueError(f"famille doit être l'une de {FAMILLES}, reçu {famille!r}")
    cfg = copy.deepcopy(cfg)
    reduit = mfc_longueur is not None
    if reduit:
        cfg.geometrie["cfc"]["longueur"] = float(mfc_longueur)
    cfg.contact.h_haut = 30.087
    cfg.ambiant.h_bas_2d = 37.424
    if h_bord_x0 is not None:
        cfg.ambiant.h_bord_x0 = float(h_bord_x0)

    masque_dur = reduit and famille in ("tronquer", "conserver")
    image_finie = reduit and famille.startswith("image_")
    e = Essai(cfg, _GABARIT, nx=nx, ny=ny, nz=nz, facteur_couplage=facteur,
              decalage_x=0.0, racine=_RACINE, masque_source_mfc=masque_dur)
    e.spots[0]["centre_x"] = x_c
    e.spec["duree_chauffe"] = duree
    e.spec["duree_totale"] = duree
    e.spots[0]["t_fin"] = duree
    # masque céramique/MFC recentré sous la passe (x_c, y_c)
    mask2d = masque_empreinte_cfc(e.grille, cfg, x_c, centre_y=y_c)
    e._masques = [mask2d]
    Q = source_spot(e.grille, cfg, e.couches, courant, x_c,
                    facteur_couplage=facteur, centre_y=y_c,
                    image_mfc_finie=image_finie,
                    mode_troncature_image=(famille.removeprefix("image_")
                                           if image_finie else "observation"))
    if masque_dur:                       # source coupée à l'empreinte du MFC réduit
        total = float(Q.sum())
        Q = Q * mask2d[:, :, None]
        if famille == "conserver":       # ... puis renormalisée : le flux se reconcentre
            masque_total = float(Q.sum())
            if masque_total > 0.0:
                Q = Q * (total / masque_total)
    e._Q_spots = [Q]
    e._P_spots_2d = [Q.sum(axis=2) * e.grille.dz]
    sv, sol = e.simuler(modele="2D")
    champs = np.array([sv.resultat_2d(sol, i) for i in range(sol.t.size)])  # (nt, nx, ny)
    return e.grille, champs.max(axis=0)


def bibliotheque(cfg: Config, x_cs, y_cs, courants, duree, *, mfc_longueurs=(None,),
                 famille: str = "tronquer", h_bord_x0: float | None = None,
                 facteur: float = 6.0123, nx: int = 61, ny: int = 21, nz: int = 15):
    """Pré-calcule les empreintes sur la grille
    (``x_cs`` × ``y_cs`` × ``courants`` × ``mfc_longueurs``).
    Renvoie ``(grille, {(x_c, y_c, courant, mfc_longueur): Tmax(x, y)})``.
    ``mfc_longueurs`` = largeurs de MFC (``None`` = MFC labo 55 mm).
    ``famille`` / ``h_bord_x0`` : voir ``empreinte``."""
    lib = {}
    grille = None
    for x_c, y_c, I, mfc in product(x_cs, y_cs, courants, mfc_longueurs):
        g, T = empreinte(cfg, x_c, y_c, I, duree, mfc_longueur=mfc, famille=famille,
                         h_bord_x0=h_bord_x0, facteur=facteur, nx=nx, ny=ny, nz=nz)
        grille = g
        mfc_cle = round(mfc, 6) if mfc is not None else None
        lib[(round(x_c, 6), round(y_c, 6), round(I, 3), mfc_cle)] = T
    return grille, lib
