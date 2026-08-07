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


# --------------------------------------------------------------------------- #
# Task 2 — empreinte d'une passe
# --------------------------------------------------------------------------- #
def test_empreinte_forme_et_monotonie_courant():
    from jumeau.planification.empreinte import empreinte
    cfg = Config.charger(RACINE / "config")
    g, T160 = empreinte(cfg, 0.060, 0.020, 160.0, 15.0)
    _, T240 = empreinte(cfg, 0.060, 0.020, 240.0, 15.0)
    assert T160.shape == (g.nx, g.ny)
    assert T240.max() > T160.max()          # plus de courant -> plus chaud
    assert T160.min() >= 15.0               # au moins l'ambiant


# --------------------------------------------------------------------------- #
# Task 3 — bibliothèque d'empreintes
# --------------------------------------------------------------------------- #
def test_bibliotheque_cardinalite_et_cle():
    from jumeau.planification.empreinte import bibliotheque
    cfg = Config.charger(RACINE / "config")
    g, lib = bibliotheque(cfg, x_cs=[0.045, 0.075], y_cs=[0.020], courants=[200.0],
                          duree=12.0)
    assert len(lib) == 2                         # 2 x_c × 1 y_c × 1 courant
    assert (0.045, 0.020, 200.0) in lib
    assert lib[(0.045, 0.020, 200.0)].shape == (g.nx, g.ny)


# --------------------------------------------------------------------------- #
# Task 4 — planificateur glouton (pur, synthétique)
# --------------------------------------------------------------------------- #
def test_metriques_comptage():
    from jumeau.planification.planificateur import metriques
    T = np.array([[300.0, 400.0], [500.0, 340.0]])   # 1 sous-fusion, 2 soudés, 1 dégradé
    m = metriques(T)
    assert m["pct_soude"] == pytest.approx(50.0)      # 400 et 340
    assert m["pct_degrade"] == pytest.approx(25.0)    # 500
    assert m["pct_non_soude"] == pytest.approx(25.0)  # 300


def test_planifier_couvre_domaine_tuilable():
    from jumeau.planification.planificateur import planifier
    A = np.array([[340.0, 20.0]])
    B = np.array([[20.0, 340.0]])
    passes, Tc, m = planifier({"A": A, "B": B}, ambiant=20.0)
    assert m["pct_soude"] == pytest.approx(100.0)
    assert set(passes) == {"A", "B"}
    assert m["pct_degrade"] == 0.0


def test_planifier_rejette_passe_degradante():
    from jumeau.planification.planificateur import planifier
    A = np.array([[340.0, 20.0]])
    C = np.array([[20.0, 460.0]])           # souderait la 2e case mais en dégradant
    passes, Tc, m = planifier({"A": A, "C": C}, ambiant=20.0)
    assert "C" not in passes
    assert m["pct_degrade"] == 0.0
    assert m["pct_soude"] == pytest.approx(50.0)


def test_planifier_sarrete_sans_amelioration():
    from jumeau.planification.planificateur import planifier
    A = np.array([[340.0, 20.0]])
    D = np.array([[20.0, 100.0]])           # D ne soude rien
    passes, Tc, m = planifier({"A": A, "D": D}, ambiant=20.0)
    assert passes == ["A"]


# --------------------------------------------------------------------------- #
# Task 5 — vérification séquentielle (lent)
# --------------------------------------------------------------------------- #
@pytest.mark.slow
def test_verifier_sequentiel_au_moins_aussi_couvrant_que_max():
    """La couverture séquentielle (chaleur résiduelle incluse) est >= la
    combinaison indépendante par max des mêmes passes (glouton conservateur)."""
    from jumeau.planification.empreinte import empreinte
    from jumeau.planification.planificateur import verifier_sequentiel, metriques
    cfg = Config.charger(RACINE / "config")
    passes = [{"x_c": 0.045, "y_c": 0.020, "courant": 220.0, "duree": 12.0},
              {"x_c": 0.075, "y_c": 0.020, "courant": 220.0, "duree": 12.0}]
    maps = [empreinte(cfg, p["x_c"], p["y_c"], p["courant"], p["duree"])[1] for p in passes]
    T_max_indep = np.maximum.reduce(maps)
    g, T_seq = verifier_sequentiel(cfg, passes)
    assert metriques(T_seq)["pct_soude"] >= metriques(T_max_indep)["pct_soude"] - 1e-6
