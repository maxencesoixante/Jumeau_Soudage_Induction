"""Tests d'intégration : source Joule assemblée + orchestration d'un essai."""

from pathlib import Path

import numpy as np
import pytest

from jumeau.geometrie import construire_couches, construire_grille, masque_empreinte_cfc
from jumeau.materiaux import Config
from jumeau.procede import Essai
from jumeau.em.source_joule import source_spot

RACINE = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def cfg():
    return Config.charger(RACINE / "config")


def test_source_localisee_et_positive(cfg):
    g = construire_grille(cfg, nx=25, ny=9, nz=9)
    couches = construire_couches(cfg)
    centre = 0.045875
    Q = source_spot(g, cfg, couches, courant=250.0, centre_x=centre)
    assert Q.shape == (25, 9, 9)
    assert np.all(Q >= 0.0) and Q.max() > 0.0
    # la source est concentrée autour du spot : max au voisinage de centre_x
    ix_max = np.unravel_index(np.argmax(Q), Q.shape)[0]
    assert abs(g.x[ix_max] - centre) < 0.02
    # le twill (interface) domine le dépôt : le nœud interface porte plus de
    # puissance que la face opposée
    profil_z = Q.sum(axis=(0, 1))
    assert profil_z[g.iz_interface] > profil_z[-1]


def test_source_croit_avec_courant(cfg):
    g = construire_grille(cfg, nx=15, ny=7, nz=7)
    couches = construire_couches(cfg)
    Q1 = source_spot(g, cfg, couches, courant=200.0, centre_x=0.06)
    Q2 = source_spot(g, cfg, couches, courant=250.0, centre_x=0.06)
    # Q ∝ I² (linéarité de Biot-Savart + quadratique de la dissipation)
    assert np.allclose(Q2, Q1 * (250.0 / 200.0) ** 2, rtol=1e-9)


def test_masque_cfc(cfg):
    g = construire_grille(cfg, nx=49, ny=17, nz=7)
    m = masque_empreinte_cfc(g, cfg, centre_x=0.015875)
    assert m.dtype == bool and m.any() and not m.all()
    # l'empreinte contient le centre du spot
    ix, iy = g.indice_xy(0.015875, g.largeur / 2)
    assert m[ix, iy]


def test_essai_chauffe_bout_en_bout(cfg):
    """Simulation courte de l'essai de chauffe sur grille grossière : sanité."""
    chemin = RACINE / "config" / "essais" / "chauffe_250A_3TC.yaml"
    essai = Essai(cfg, chemin, nx=21, ny=9, nz=9, racine=RACINE)
    # écourter pour le test
    essai.spec["duree_totale"] = 60.0
    solveur, sol = essai.simuler(dt_sortie=2.0)
    series = essai.series_tc(solveur, sol)
    assert set(series) == {"TC1", "TC2", "TC3"}
    # ça chauffe, et l'interface (twill) chauffe plus que la face opposée
    assert series["TC2"].max() > 30.0
    assert series["TC2"].max() > series["TC3"].max()
    # aucune température aberrante
    assert np.all(np.isfinite(sol.y))
    assert sol.y.max() < 2000.0
