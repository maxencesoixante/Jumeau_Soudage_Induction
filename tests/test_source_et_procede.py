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

    VALEURS MISES À JOUR 2026-07-27 (2e correction de géométrie bobine : hauteur
    0.0068 -> 0.005 m, source ~1.34x plus forte, cf.
    resultats_hauteur_5mm_recalibration.log ; succède à la correction d'entraxe
    du 2026-07-23) : taux_sim TC2 = 5.43 °C/s à decalage_x=0, 14.16 à +10 mm.
    Les brins plus rapprochés + plus bas rendent le décalage PLUS sensible
    (×2.6) — le zéro de symétrie se place différemment. L'effet reste
    QUALITATIVEMENT le même (le décalage augmente le taux) ; decalage_x est de
    toute façon figé à 0 dans le θ* de référence."""
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

    assert taux0 == pytest.approx(5.43, abs=0.3)
    assert taux_d == pytest.approx(14.16, abs=0.6)
    assert taux_d > taux0          # le décalage augmente le taux (×2.6, cf. docstring)


# --- loi thermostat 'capteurs' (défaut off, cf. Essai.thermostat_capteurs) ---

def _essai_b2(cfg, **kw):
    chemin = RACINE / "config" / "essais" / "serieB_B-2.yaml"
    return Essai(cfg, chemin, nx=25, ny=11, nz=9, racine=RACINE, **kw)


def test_thermostat_capteurs_off_est_non_regression(cfg):
    """Flag off (défaut) : nœuds de contrôle et T_ctrl strictement inchangés."""
    e_def = _essai_b2(cfg)
    e_off = _essai_b2(cfg, thermostat_capteurs=False)
    assert e_def._noeuds_controle == e_off._noeuds_controle
    assert e_def._noeuds_controle_2d == e_off._noeuds_controle_2d
    assert e_def._brackets_capteurs == []          # non construit quand off
    rng = np.random.default_rng(0)
    T = rng.random((e_def.grille.nx, e_def.grille.ny)) * 400.0
    spot = e_def.spots[0]
    assert e_def._T_ctrl(T, spot, deux_d=True) == e_off._T_ctrl(T, spot, deux_d=True)


def test_thermostat_capteurs_on_controle_sur_le_max_des_tc(cfg):
    """Flag on : T_ctrl = max de T aux positions TC d'interface (≠ loi section)."""
    from jumeau.thermique.solveur3d import bracket_lineaire
    e_on = _essai_b2(cfg, thermostat_capteurs=True)
    e_off = _essai_b2(cfg)
    g = e_on.grille
    assert e_on._brackets_capteurs                 # construit quand on
    # nœuds de contrôle = brackets des TC, différents de la loi section
    assert e_on._noeuds_controle_2d != e_off._noeuds_controle_2d

    # champ synthétique : bosse localisée exactement sur un nœud proche de TC3
    # (x=60mm, y=0). T_ctrl 'capteurs' doit valoir le max bilinéaire aux TC.
    rng = np.random.default_rng(1)
    T = rng.random((g.nx, g.ny)) * 50.0
    positions = e_on._positions_capteurs_interface()
    assert positions                                # B-2 a des TC d'interface
    attendu = -np.inf
    for x, y in positions:
        ix, wx = bracket_lineaire(g.x, x)
        iy, wy = bracket_lineaire(g.y, y)
        v = ((1 - wx) * (1 - wy) * T[ix, iy] + wx * (1 - wy) * T[ix + 1, iy]
             + (1 - wx) * wy * T[ix, iy + 1] + wx * wy * T[ix + 1, iy + 1])
        attendu = max(attendu, v)
    spot = e_on.spots[0]
    assert e_on._T_ctrl(T, spot, deux_d=True) == pytest.approx(attendu)
    # et c'est bien un MAX -> >= la valeur de n'importe quel TC pris seul
    assert e_on._T_ctrl(T, spot, deux_d=True) >= T.min()


# --- lissage de source (délocalisation twill, cf. source_joule._lisser_source) ---

def test_lissage_source_off_est_identite(cfg):
    """sigma=0 (défaut) : source strictement inchangée (non-régression)."""
    g = construire_grille(cfg, nx=25, ny=11, nz=9)
    c = construire_couches(cfg)
    Q0 = source_spot(g, cfg, c, 250.0, 0.06)
    Q0b = source_spot(g, cfg, c, 250.0, 0.06, lissage_sigma_mm=0.0)
    assert np.array_equal(Q0, Q0b)


def test_lissage_source_conserve_puissance_et_remplit_centre(cfg):
    """sigma>0 : puissance totale conservée, œil de boucle rempli, pic abaissé."""
    g = construire_grille(cfg, nx=61, ny=21, nz=13)
    c = construire_couches(cfg)
    Q0 = source_spot(g, cfg, c, 250.0, 0.06)
    Q6 = source_spot(g, cfg, c, 250.0, 0.06, lissage_sigma_mm=6.0)
    assert Q6.sum() == pytest.approx(Q0.sum(), rel=1e-6)      # puissance conservée
    ix = int(np.argmin(np.abs(g.x - 0.06))); iy = g.ny // 2
    assert Q0[ix, iy, :].sum() < 1.0                           # œil de boucle ~0
    assert Q6[ix, iy, :].sum() > 100.0 * Q0[ix, iy, :].sum()   # rempli
    assert Q6.max() < Q0.max()                                 # pic abaissé
