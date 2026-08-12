import sys
from pathlib import Path
RACINE = Path(__file__).resolve().parents[1]
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
