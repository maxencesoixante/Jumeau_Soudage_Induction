"""Vérifications du solveur thermique 3D : énergie + régression contre le 1D."""

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from jumeau.materiaux import Ambiant, ContactCeramique, Materiau
from jumeau.thermique.solveur3d import Grille3D, SolveurThermique3D


def _materiau(latente=0.0):
    return Materiau(
        densite=1600.0, cp_base=1200.0, T_fusion=337.0, delta_T_fusion=15.0,
        chaleur_latente=latente, k_plan=3.0, k_z=0.64, emissivite=0.96,
    )


def test_equilibre_sans_source():
    """Sans source et à T = T_amb partout, rien ne bouge."""
    g = Grille3D(0.12, 0.04, 0.00682, 0.00336, nx=9, ny=5, nz=7)
    s = SolveurThermique3D(g, _materiau(), Ambiant(), ContactCeramique(T_puits=20.0))
    source = lambda t: np.zeros((g.nx, g.ny, g.nz))
    sol = s.simuler(source, (0.0, 50.0), t_eval=np.array([0.0, 50.0]))
    assert np.allclose(sol.y[:, -1], 20.0, atol=1e-6)


def test_conservation_energie_adiabatique():
    """Système isolé (h=0, ε=0) : ΔT = ∫Q·dt / (ρ·cp) exactement, partout."""
    mat = _materiau()
    mat.emissivite = 0.0
    amb = Ambiant(h_convection=0.0, h_bas=0.0)
    g = Grille3D(0.12, 0.04, 0.00682, 0.00336, nx=9, ny=5, nz=7)
    s = SolveurThermique3D(g, mat, amb, ContactCeramique(h_contact=0.0))
    q0 = 1e6                                           # W/m3 uniforme
    source = lambda t: np.full((g.nx, g.ny, g.nz), q0)
    duree = 60.0
    sol = s.simuler(source, (0.0, duree), t_eval=np.array([0.0, duree]), rtol=1e-8, atol=1e-6)
    dT_attendu = q0 * duree / (mat.densite * mat.cp_base)
    assert np.allclose(sol.y[:, -1] - 20.0, dT_attendu, rtol=1e-4)


def _simuler_1d_notebook(f_I, r_I, k_z, t_eval, courant, nodes=20, thickness=0.00112,
                         rho=1600.0, h_conv=15.0, T_amb=20.0, epsilon=0.96):
    """Port direct du simulateur 1D du notebook MAX_InductionNumerical (référence)."""
    sigma_sb = 5.67e-8
    dz = thickness / (nodes - 1)
    z = np.linspace(0.0, thickness, nodes)

    def cp_app(T):
        sig_f = 15.0 / 2.0
        return 1200.0 + (130000.0 / (sig_f * np.sqrt(2 * np.pi))) * np.exp(
            -0.5 * ((T - 337.0) / sig_f) ** 2)

    def rhs(t, T):
        Q = f_I * courant**2 * np.exp(-r_I * z)
        cp = cp_app(T)
        dT = np.zeros(nodes)
        dT[1:-1] = (k_z / (rho * cp[1:-1] * dz**2)) * (T[:-2] - 2 * T[1:-1] + T[2:]) \
            + Q[1:-1] / (rho * cp[1:-1])
        Ta_K = T_amb + 273.15
        for idx, voisin in ((0, 1), (-1, -2)):
            TK = T[idx] + 273.15
            dT[idx] = (2.0 / (rho * cp[idx] * dz)) * (
                k_z / dz * (T[voisin] - T[idx])
                + h_conv * (T_amb - T[idx])
                + epsilon * sigma_sb * (Ta_K**4 - TK**4)
            ) + Q[idx] / (rho * cp[idx])
        return dT

    sol = solve_ivp(rhs, (t_eval[0], t_eval[-1]), np.full(nodes, T_amb),
                    method="BDF", t_eval=t_eval, rtol=1e-6, atol=1e-4)
    return sol.y


def test_regression_3d_vs_1d():
    """Plaque 1 m × 1 m (bords lointains), source uniforme dans le plan :
    la colonne centrale du 3D doit reproduire le modèle 1D du notebook."""
    thickness, nodes = 0.00112, 20
    f_I, r_I, k_z, courant = 1500.0, 180.0, 0.64, 60.0
    t_eval = np.linspace(0.0, 120.0, 61)

    T1d = _simuler_1d_notebook(f_I, r_I, k_z, t_eval, courant, nodes=nodes)

    mat = _materiau(latente=130000.0)
    mat.k_z = k_z
    amb = Ambiant(h_convection=15.0, h_bas=15.0)
    g = Grille3D(1.0, 1.0, thickness, thickness / 2, nx=7, ny=7, nz=nodes)
    s = SolveurThermique3D(g, mat, amb, ContactCeramique(h_contact=0.0))

    Qz = f_I * courant**2 * np.exp(-r_I * g.z)
    Q = np.broadcast_to(Qz, (g.nx, g.ny, g.nz)).copy()
    sol = s.simuler(lambda t: Q, (0.0, 120.0), t_eval=t_eval, rtol=1e-6, atol=1e-4)

    Y = sol.y.reshape(g.nx, g.ny, g.nz, -1)
    centre = Y[g.nx // 2, g.ny // 2, :, :]
    # écart máx sur les deux faces au fil du temps
    assert np.max(np.abs(centre[0, :] - T1d[0, :])) < 1.5
    assert np.max(np.abs(centre[-1, :] - T1d[-1, :])) < 1.5


def test_puits_ceramique_refroidit():
    """Le contact céramique (masque actif) doit tirer la face sup vers T_puits."""
    mat = _materiau()
    g = Grille3D(0.12, 0.04, 0.00682, 0.00336, nx=9, ny=5, nz=7)
    masque = np.zeros((g.nx, g.ny), dtype=bool)
    masque[3:6, 1:4] = True
    s = SolveurThermique3D(g, mat, Ambiant(), ContactCeramique(h_contact=200.0, T_puits=20.0),
                           masque_ceramique=masque)
    T0 = np.full(g.n, 200.0)
    source = lambda t: np.zeros((g.nx, g.ny, g.nz))
    sol = s.simuler(source, (0.0, 30.0), t_eval=np.array([0.0, 30.0]), T_initial=T0)
    Tf = sol.y[:, -1].reshape(g.nx, g.ny, g.nz)
    # la zone sous masque refroidit plus vite que les coins libres
    assert Tf[4, 2, 0] < Tf[0, 0, 0] - 5.0
