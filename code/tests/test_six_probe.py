"""Tests de l'extraction six-probe (issue #49).

Validation SYNTHÉTIQUE : on génère (V_t, V_b) depuis des conductivités connues
via le modèle direct, puis on vérifie que l'inversion les retrouve. Aucun banc
requis.
"""
import numpy as np
import pytest

from jumeau.identification.six_probe import (
    GeometrieSixProbe,
    voltages_directes,
    extraire_sigma,
    busch_sigma,
    balayage_angulaire,
)

GEO = GeometrieSixProbe()
CAS = [(1.46e4, 50.0), (2.2e4, 3.4), (1.1e4, 10.0)]


@pytest.mark.parametrize("sx_true, sz_true", CAS)
def test_roundtrip_exact(sx_true, sz_true):
    """Le round-trip (direct -> inverse) retrouve σx et σz à mieux que 1 %."""
    vt, vb = voltages_directes(sx_true, sz_true, GEO)
    sx, sz = extraire_sigma(vt, vb, GEO)
    assert abs(sx - sx_true) / sx_true < 1e-2
    assert abs(sz - sz_true) / sz_true < 1e-2


def test_physique_Vt_superieur_Vb():
    """La face supérieure voit plus de courant : V_t > V_b."""
    vt, vb = voltages_directes(1.46e4, 50.0, GEO)
    assert vt > vb > 0


def test_ratio_croit_avec_anisotropie():
    """Plus l'anisotropie σx/σz est forte, plus V_t/V_b est grand."""
    ratios = []
    for sz in (500.0, 50.0, 5.0):          # anisotropie croissante
        vt, vb = voltages_directes(1.46e4, sz, GEO)
        ratios.append(vt / vb)
    assert ratios[0] < ratios[1] < ratios[2]


def test_robustesse_bruit():
    """Sous 2 % de bruit sur les tensions, σx reste à <5 %, σz à <20 % (médianes)."""
    rng = np.random.default_rng(0)
    sx_true, sz_true = 1.46e4, 50.0
    vt, vb = voltages_directes(sx_true, sz_true, GEO)
    ex, ez = [], []
    for _ in range(15):
        vt_n = vt * (1 + 0.02 * rng.standard_normal())
        vb_n = vb * (1 + 0.02 * rng.standard_normal())
        sx, sz = extraire_sigma(vt_n, vb_n, GEO)
        ex.append(abs(sx / sx_true - 1))
        ez.append(abs(sz / sz_true - 1))
    assert np.median(ex) < 0.05
    assert np.median(ez) < 0.20


@pytest.mark.parametrize("sx_true, sz_true", CAS)
def test_busch_garde_fou_sigma_x(sx_true, sz_true):
    """Busch (n=1) est un garde-fou correct pour σx (à ~30 %) ; σz non fiable
    (borné large : le modèle grille reste la référence)."""
    vt, vb = voltages_directes(sx_true, sz_true, GEO)
    bx, bz = busch_sigma(vt, vb, GEO)
    assert abs(bx - sx_true) / sx_true < 0.30      # σx : bon garde-fou
    assert 0 < bz < 20 * sz_true                   # σz : seulement positif/ordre de grandeur


def test_balayage_angulaire():
    """Reconstitue σx(θ) depuis une liste (θ, V_t, V_b) synthétique."""
    sigma_x_vrai = {0: 2.0e4, 45: 1.1e4, 90: 1.9e4}
    mesures = []
    for theta, sx in sigma_x_vrai.items():
        vt, vb = voltages_directes(sx, 20.0, GEO)
        mesures.append((theta, vt, vb))
    res = balayage_angulaire(mesures, GEO)
    assert [t for t, _, _ in res] == [0, 45, 90]
    for (theta, sx, _), sx_vrai in zip(res, sigma_x_vrai.values()):
        assert abs(sx - sx_vrai) / sx_vrai < 1e-2
