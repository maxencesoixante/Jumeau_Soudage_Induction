import sys
from pathlib import Path
RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts" / "diag"))
sys.path.insert(0, str(RACINE / "scripts"))
sys.path.insert(0, str(RACINE / "src"))

import numpy as np
from diag_pareto_source_conduction import contraste_ktlb


def test_contraste_reference_isotrope():
    # Nœud de référence (k(T) OFF, lambda=0) reproduit le contraste connu ~3.13.
    c, profil = contraste_ktlb(facteur=6.0123, k_hot=None, lambda_bord_mm=0.0)
    assert 3.0 <= c <= 3.25
    assert profil.shape == (5,)
    assert abs(profil[2] - 1.0) < 1e-6  # normalisé par le pic centre (y=20mm)


def test_lambda_bord_abaisse_le_contraste():
    # La raideur de source adoucie (lambda_bord>0) réduit le contraste du M.
    c0, _ = contraste_ktlb(facteur=6.0123, k_hot=None, lambda_bord_mm=0.0)
    c6, _ = contraste_ktlb(facteur=6.0123, k_hot=None, lambda_bord_mm=6.0)
    assert c6 < c0


from diag_pareto_source_conduction import (restaurer_facteur, rmse_pooled,
                                           charger_essais, _cfg_noeud)


def test_noeud_reference_rmse_et_facteur():
    fit = charger_essais(("exp7_150A", "exp7_200A", "exp9_200A_y20_monospot"))
    held = charger_essais(("exp7_250A", "exp9_200A_monospot"))
    cfg = _cfg_noeud(k_hot=None)  # isotrope de référence
    facteur = restaurer_facteur(fit, cfg, lambda_bord_mm=0.0)
    assert 4.5 <= facteur <= 8.0          # restaure ~6.0 sur le lot d'ajustement
    rmse = rmse_pooled(held, cfg, facteur, lambda_bord_mm=0.0)
    assert 12.0 <= rmse <= 21.0           # ordre de grandeur du held-out de réf (~16.5)


from diag_pareto_source_conduction import classer, verdict


def test_classer():
    # contraste dans la boîte + RMSE ≤ réf → faisable
    assert classer(2.10, 16.0, rmse_ref=16.5) == "faisable"
    # contraste ok mais RMSE entre réf et réf+0.7 → quasi
    assert classer(2.10, 17.0, rmse_ref=16.5) == "quasi"
    # contraste hors boîte → hors quel que soit le RMSE
    assert classer(2.50, 15.0, rmse_ref=16.5) == "hors"
    # contraste ok mais RMSE > réf+marge → hors
    assert classer(2.10, 18.0, rmse_ref=16.5) == "hors"


def test_verdict():
    assert verdict(["hors", "faisable", "quasi"]) == "GO"
    assert verdict(["hors", "quasi", "hors"]) == "QUASI-GO"
    assert verdict(["hors", "hors"]) == "NO-GO"
