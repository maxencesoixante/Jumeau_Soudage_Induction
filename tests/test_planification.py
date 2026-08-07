"""Tests du planificateur de soudage uniforme (épique #31)."""

import sys
from pathlib import Path

import numpy as np
import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
from jumeau.materiaux import Config  # noqa: E402
from jumeau.procede import Essai  # noqa: E402
from jumeau.em.source_joule import source_spot  # noqa: E402


def _essai():
    """Essai gabarit exp7 (grille + couches), θ* figé — pour les tests source."""
    cfg = Config.charger(RACINE / "config")
    cfg.contact.h_haut = 30.087
    cfg.ambiant.h_bas_2d = 37.424
    cfg.ambiant.h_bord_x0 = 250.0
    e = Essai(cfg, RACINE / "config/essais/exp7_200A.yaml", nx=61, ny=21, nz=15,
              facteur_couplage=6.0123, decalage_x=0.0, racine=RACINE)
    return cfg, e


# --------------------------------------------------------------------------- #
# Task 1 — décalage en y de la source
# --------------------------------------------------------------------------- #
def test_source_spot_centre_y_defaut_non_regressif():
    """centre_y=None reproduit bit-à-bit l'appel historique (sans centre_y)."""
    cfg, e = _essai()
    Q0 = source_spot(e.grille, cfg, e.couches, 200.0, 0.060, facteur_couplage=6.0123)
    Q1 = source_spot(e.grille, cfg, e.couches, 200.0, 0.060, facteur_couplage=6.0123,
                     centre_y=None)
    assert np.array_equal(Q0, Q1)


def test_source_spot_centre_y_deplace_le_pic_en_y():
    """Décaler centre_y déplace le barycentre en y de la source déposée."""
    cfg, e = _essai()
    y = e.grille.y

    def barycentre_y(Q):
        P = Q.sum(axis=(0, 2))            # puissance par bande y
        return float((P * y).sum() / P.sum())

    Q_haut = source_spot(e.grille, cfg, e.couches, 200.0, 0.060,
                         facteur_couplage=6.0123, centre_y=0.010)
    Q_bas = source_spot(e.grille, cfg, e.couches, 200.0, 0.060,
                        facteur_couplage=6.0123, centre_y=0.030)
    assert barycentre_y(Q_haut) < barycentre_y(Q_bas) - 1e-3
