"""Sanité des essais branchés pour la calibration jointe consolidée (exp7/exp9).

Vérifie que chaque nouveau YAML (exp7 176/225 A, exp9 y=0 monospot 175/226/250 A)
se charge, simule en 2D et produit la BONNE STRUCTURE spatiale — assertions
structurelles (quel TC est le plus chaud, symétrie, décroissance) plutôt qu'une
tolérance absolue, car l'absolu est bridé par la coupure manuelle (~270-280 °C au
spot) et n'est de toute façon pas la cible de calibration (cf. READMEs exp7/exp9).

Régime de référence : facteur_couplage=6.0123 (valeur calibrée passée au runtime,
la config porte 1.0 par dégénérescence multiplicative).
"""
from pathlib import Path

import numpy as np
import pytest

from jumeau.materiaux import Config
from jumeau.procede import Essai

RACINE = Path(__file__).resolve().parents[1]
FACTEUR_REF = 6.0123
GRILLE = dict(nx=31, ny=11, nz=13)

ESSAIS_M = ["exp7_176A", "exp7_225A"]                       # famille profil « M » (largeur)
ESSAIS_CONDUCTION = ["exp9_175A_monospot",                  # famille conduction (longueur, y=0)
                     "exp9_226A_monospot", "exp9_250A_monospot"]


@pytest.fixture(scope="module")
def cfg():
    return Config.charger(RACINE / "config")


def _simuler(cfg, nom):
    chemin = RACINE / "config" / "essais" / f"{nom}.yaml"
    essai = Essai(cfg, chemin, facteur_couplage=FACTEUR_REF, racine=RACINE, **GRILLE)
    solveur, sol = essai.simuler(modele="2D")
    series = essai.series_tc(solveur, sol)
    tc = essai.spec["tc_valides"]
    pics = {k: float(np.max(series[k])) for k in tc}
    return series, pics


@pytest.mark.parametrize("nom", ESSAIS_M + ESSAIS_CONDUCTION)
def test_essai_se_charge_et_simule(cfg, nom):
    """Chargement + simulation 2D sans erreur, séries finies et non triviales."""
    series, pics = _simuler(cfg, nom)
    assert set(pics) == {"TC1", "TC2", "TC3", "TC4", "TC5"}
    for k, s in series.items():
        assert np.all(np.isfinite(s)), f"{nom}/{k} : valeurs non finies"
    # chauffe réelle : au moins un TC dépasse nettement l'ambiant
    assert max(pics.values()) > 40.0, f"{nom} : pas de chauffe détectée ({pics})"


@pytest.mark.parametrize("nom", ESSAIS_CONDUCTION)
def test_conduction_spot_central_et_decroissance(cfg, nom):
    """exp9 y=0 monospot : TC3 (spot, x=60) le plus chaud, décroissance vers les
    extrémités (TC1<TC2<TC3>TC4>TC5). Valide la position du spot en longueur."""
    _, p = _simuler(cfg, nom)
    assert p["TC3"] == max(p.values()), f"{nom} : le spot n'est pas à TC3 ({p})"
    assert p["TC2"] > p["TC1"] and p["TC4"] > p["TC5"], f"{nom} : décroissance longitudinale KO ({p})"
    assert p["TC3"] > 2 * p["TC2"], f"{nom} : pic au spot pas assez marqué ({p})"


@pytest.mark.parametrize("nom", ESSAIS_M)
def test_profil_m_symetrique(cfg, nom):
    """exp7 : profil « M » en largeur — chants (TC1,TC5) chauds, centre (TC3) froid,
    symétrie chant gauche/droite. Valide le câblage largeur y=0..0.040."""
    _, p = _simuler(cfg, nom)
    assert p["TC3"] == min(p.values()), f"{nom} : le centre TC3 n'est pas le point froid ({p})"
    assert p["TC1"] > p["TC2"] > p["TC3"], f"{nom} : flanc gauche du M KO ({p})"
    assert p["TC5"] > p["TC4"] > p["TC3"], f"{nom} : flanc droit du M KO ({p})"
    # symétrie des chants (montage symétrique, spot centré) à ±10 %
    assert abs(p["TC1"] - p["TC5"]) / max(p["TC1"], p["TC5"]) < 0.10, \
        f"{nom} : chants non symétriques ({p})"
