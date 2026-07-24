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


def test_decalage_x_zero_est_identite(cfg):
    """decalage_x=0.0 (explicite ou par défaut) doit reproduire EXACTEMENT
    la source d'avant l'introduction du paramètre : non-régression bit-à-bit."""
    g = construire_grille(cfg, nx=31, ny=11, nz=13)
    couches = construire_couches(cfg)
    Q_sans_arg = source_spot(g, cfg, couches, courant=250.0, centre_x=0.06)
    Q_decalage_nul = source_spot(g, cfg, couches, courant=250.0, centre_x=0.06,
                                  decalage_x=0.0)
    assert np.array_equal(Q_sans_arg, Q_decalage_nul)


def test_decalage_x_deplace_le_centre_bobine(cfg):
    """decalage_x translate le centre effectif de la bobine (donc le profil de
    Q en x) sans modifier la puissance totale déposée (même bobine, même I)."""
    g = construire_grille(cfg, nx=31, ny=11, nz=13)
    couches = construire_couches(cfg)
    centre = 0.06
    Q0 = source_spot(g, cfg, couches, courant=250.0, centre_x=centre)
    Q_decale = source_spot(g, cfg, couches, courant=250.0, centre_x=centre,
                            decalage_x=0.010)
    assert not np.array_equal(Q0, Q_decale)
    # puissance totale quasi conservée (translation de la bobine ; la légère
    # différence vient de la BC psi=0 au bord de plaque, PAS translation-
    # invariante — la bobine décalée est légèrement plus proche du bord x=L)
    assert np.isclose(Q0.sum(), Q_decale.sum(), rtol=1e-2)
    # décaler la bobine de +10 mm équivaut EXACTEMENT à évaluer la source non
    # décalée à centre_x + 10 mm (même géométrie relative bobine<->grille) :
    # c'est cette identité, pas la conservation approximative ci-dessus, qui
    # définit le comportement attendu de decalage_x
    Q_ref = source_spot(g, cfg, couches, courant=250.0, centre_x=centre + 0.010)
    assert np.allclose(Q_decale, Q_ref, rtol=1e-9)


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


def test_essai_decalage_x_defaut_et_surcharge(cfg):
    """decalage_x : valeur YAML (0.0) par défaut, surchargeable par programme
    comme facteur_couplage ; ne déplace pas le masque céramique/CFC."""
    chemin = RACINE / "config" / "essais" / "chauffe_250A_3TC.yaml"
    essai_defaut = Essai(cfg, chemin, nx=21, ny=9, nz=9, racine=RACINE)
    assert essai_defaut.decalage_x == 0.0

    essai_decale = Essai(cfg, chemin, nx=21, ny=9, nz=9, decalage_x=0.010, racine=RACINE)
    assert essai_decale.decalage_x == 0.010
    # la source change avec le décalage bobine...
    assert not np.array_equal(essai_defaut._Q_spots[0], essai_decale._Q_spots[0])
    # ...mais le masque céramique/CFC (posé sur le spot, pas sur la bobine) ne bouge pas
    assert np.array_equal(essai_defaut._masques[0], essai_decale._masques[0])


def test_essai_decalage_x_augmente_taux_chauffe_tc2(cfg):
    """Reproduit la découverte du 2026-07-18 : TC2 est au centre de symétrie
    du hairpin (zéro de dissipation exact) pour l'essai chauffe_250A_3TC ; un
    décalage bobine de +10 mm sort du zéro et accélère la chauffe locale
    (grille 31x11x13, facteur_couplage=3.85).

    VALEURS MISES À JOUR 2026-07-23 (correction de géométrie bobine : entraxe
    0.019 -> 0.01235 m, cf. resultats_geometrie_corrigee_recalibration.log) :
    taux_sim TC2 = 4.03 °C/s à decalage_x=0, 5.73 à +10 mm. Les brins plus
    rapprochés affaiblissent l'effet du décalage (×1.4 au lieu de ×2.3 sous
    l'ancienne géométrie) — le zéro de symétrie se place différemment. L'effet
    reste QUALITATIVEMENT le même (le décalage augmente le taux) ; decalage_x
    est de toute façon figé à 0 dans le θ* de référence."""
    from jumeau.validation.confrontation import taux_de_chauffe

    chemin = RACINE / "config" / "essais" / "chauffe_250A_3TC.yaml"
    essai0 = Essai(cfg, chemin, nx=31, ny=11, nz=13, facteur_couplage=3.85, racine=RACINE)
    essai_decale = Essai(cfg, chemin, nx=31, ny=11, nz=13, facteur_couplage=3.85,
                         decalage_x=0.010, racine=RACINE)
    # taux_de_chauffe ne regarde que la montée (croisement de T_ref=75°C,
    # atteint bien avant 30 s) : on écourte duree_totale pour le temps de
    # test, dt_sortie=1.0 (défaut, identique à scripts/valider.py) préservé
    essai0.spec["duree_totale"] = 60.0
    essai_decale.spec["duree_totale"] = 60.0

    solveur0, sol0 = essai0.simuler(dt_sortie=1.0)
    solveur_d, sol_d = essai_decale.simuler(dt_sortie=1.0)
    taux0 = taux_de_chauffe(sol0.t, essai0.series_tc(solveur0, sol0)["TC2"])
    taux_d = taux_de_chauffe(sol_d.t, essai_decale.series_tc(solveur_d, sol_d)["TC2"])

    assert taux0 == pytest.approx(4.03, abs=0.3)
    assert taux_d == pytest.approx(5.73, abs=0.5)
    assert taux_d > taux0          # le décalage augmente le taux (×1.4, cf. docstring)
