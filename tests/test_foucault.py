"""Vérifications du solveur de fonction de courant (courants de Foucault)."""

import numpy as np
import pytest

from jumeau.em.foucault import densite_joule, resoudre_psi


def _grille(nx=41, ny=41, L=0.1):
    x = np.linspace(0, L, nx)
    y = np.linspace(0, L, ny)
    return x, y, x[1] - x[0], y[1] - y[0]


def test_psi_nul_au_bord():
    x, y, dx, dy = _grille()
    Bz = np.full((len(x), len(y)), 1e-3)
    psi = resoudre_psi(Bz, dx, dy, 1e-4, 1e-4, 2 * np.pi * 3e5)
    assert np.all(psi[0, :] == 0) and np.all(psi[-1, :] == 0)
    assert np.all(psi[:, 0] == 0) and np.all(psi[:, -1] == 0)
    assert np.max(np.abs(psi)) > 0


def test_symetrie_cas_isotrope():
    """Bz uniforme sur un carré isotrope : ψ garde les symétries du carré."""
    x, y, dx, dy = _grille()
    Bz = np.full((len(x), len(y)), 1e-3)
    psi = resoudre_psi(Bz, dx, dy, 1e-4, 1e-4, 2 * np.pi * 3e5)
    assert np.allclose(psi, psi[::-1, :], rtol=1e-10, atol=1e-12)
    assert np.allclose(psi, psi[:, ::-1], rtol=1e-10, atol=1e-12)
    assert np.allclose(psi, psi.T, rtol=1e-10, atol=1e-12)


def test_scaling_frequence_et_resistivite():
    """ψ ∝ ω/ρ et q ∝ ω²/ρ (plaque mince sans réaction) — scaling exact."""
    x, y, dx, dy = _grille(nx=21, ny=21)
    Bz = np.full((len(x), len(y)), 1e-3)
    rho, omega = 1e-4, 2 * np.pi * 3e5

    psi1 = resoudre_psi(Bz, dx, dy, rho, rho, omega)
    psi2 = resoudre_psi(Bz, dx, dy, rho, rho, 2 * omega)
    assert np.allclose(psi2, 2 * psi1, rtol=1e-10)

    psi3 = resoudre_psi(Bz, dx, dy, 2 * rho, 2 * rho, omega)
    assert np.allclose(psi3, 0.5 * psi1, rtol=1e-10)

    q1 = densite_joule(psi1, dx, dy, rho, rho)
    q2 = densite_joule(psi2, dx, dy, rho, rho)
    assert np.allclose(q2, 4 * q1, rtol=1e-10)


def test_dissipation_positive():
    x, y, dx, dy = _grille(nx=21, ny=21)
    rng = np.random.default_rng(0)
    Bz = rng.normal(0, 1e-3, (len(x), len(y)))
    psi = resoudre_psi(Bz, dx, dy, 2e-4, 5e-5, 2 * np.pi * 3e5)
    q = densite_joule(psi, dx, dy, 2e-4, 5e-5)
    assert np.all(q >= 0)


def test_equation_verifiee_interieur():
    """Le ψ résolu satisfait ρyy·ψxx + ρxx·ψyy = ω·Bz aux nœuds intérieurs."""
    x, y, dx, dy = _grille(nx=31, ny=31)
    rho_xx, rho_yy = 2e-4, 5e-5
    omega = 2 * np.pi * 3e5
    X, Y = np.meshgrid(x, y, indexing="ij")
    Bz = 1e-3 * np.exp(-((X - 0.05) ** 2 + (Y - 0.05) ** 2) / 0.001)
    psi = resoudre_psi(Bz, dx, dy, rho_xx, rho_yy, omega)
    lap = (rho_yy * (psi[:-2, 1:-1] - 2 * psi[1:-1, 1:-1] + psi[2:, 1:-1]) / dx**2
           + rho_xx * (psi[1:-1, :-2] - 2 * psi[1:-1, 1:-1] + psi[1:-1, 2:]) / dy**2)
    assert np.allclose(lap, omega * Bz[1:-1, 1:-1], rtol=1e-8, atol=1e-8 * omega * Bz.max())
