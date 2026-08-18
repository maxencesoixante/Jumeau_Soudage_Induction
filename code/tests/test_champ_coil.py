"""Vérifications analytiques du module Biot-Savart."""

import numpy as np
import pytest

from jumeau.em.champ_coil import MU0, bz_plan, champ_segments, sommets_hairpin


def test_boucle_circulaire_centre():
    """Polygone à 200 côtés vs B = µ0·I/(2R) au centre d'une boucle."""
    R, I = 0.02, 100.0
    theta = np.linspace(0.0, 2.0 * np.pi, 201)
    sommets = np.column_stack([R * np.cos(theta), R * np.sin(theta), np.zeros_like(theta)])
    B = champ_segments(np.array([[0.0, 0.0, 0.0]]), sommets, I)
    attendu = MU0 * I / (2.0 * R)
    assert B[0, 2] == pytest.approx(attendu, rel=1e-3)
    assert abs(B[0, 0]) < 1e-9 and abs(B[0, 1]) < 1e-9


def test_boucle_circulaire_axe():
    """Sur l'axe à distance d : B = µ0·I·R²/(2(R²+d²)^1.5)."""
    R, I, d = 0.02, 100.0, 0.01
    theta = np.linspace(0.0, 2.0 * np.pi, 201)
    sommets = np.column_stack([R * np.cos(theta), R * np.sin(theta), np.zeros_like(theta)])
    B = champ_segments(np.array([[0.0, 0.0, d]]), sommets, I)
    attendu = MU0 * I * R**2 / (2.0 * (R**2 + d**2) ** 1.5)
    assert B[0, 2] == pytest.approx(attendu, rel=1e-3)


def test_hairpin_symetrie_et_signe():
    """Bz du hairpin : antisymétrique de part et d'autre du plan des brins ? Non —
    boucle rectangulaire => Bz maximal entre les brins, symétrique en y."""
    sommets = sommets_hairpin(0.05, 0.01, 0.005, centre_x=0.0, centre_y=0.0)
    X, Y = np.meshgrid(np.linspace(-0.04, 0.04, 21), np.linspace(-0.02, 0.02, 11), indexing="ij")
    Bz = bz_plan(sommets, 250.0, X, Y, z_plan=0.0)
    # symétrie x -> -x et y -> -y (rectangle centré)
    assert np.allclose(Bz, Bz[::-1, :], atol=1e-9)
    assert np.allclose(Bz, Bz[:, ::-1], atol=1e-9)
    # le champ max est à l'intérieur de l'empreinte de la boucle (|x|<L/2, |y|<s/2)
    ix, iy = np.unravel_index(np.argmax(np.abs(Bz)), Bz.shape)
    assert abs(X[ix, iy]) <= 0.025 and abs(Y[ix, iy]) <= 0.005
    # et le centre est du même ordre que le max (plateau entre les brins)
    assert np.abs(Bz[10, 5]) > 0.5 * np.abs(Bz).max()


def test_image_cfc_intensifie():
    """L'image du CFC (µr=16) doit intensifier |Bz| sous la bobine."""
    sommets = sommets_hairpin(0.05, 0.01, 0.005)
    X, Y = np.meshgrid(np.linspace(-0.02, 0.02, 11), np.linspace(-0.01, 0.01, 7), indexing="ij")
    Bz_sans = bz_plan(sommets, 250.0, X, Y, z_plan=0.0)
    Bz_avec = bz_plan(sommets, 250.0, X, Y, z_plan=0.0, mu_r_cfc=16.0, z_miroir=0.008)
    assert np.max(np.abs(Bz_avec)) > np.max(np.abs(Bz_sans))
    # facteur d'intensification borné par 1+η < 2
    assert np.max(np.abs(Bz_avec)) < 2.0 * np.max(np.abs(Bz_sans))
