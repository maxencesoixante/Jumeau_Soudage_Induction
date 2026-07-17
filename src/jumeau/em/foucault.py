"""Courants de Foucault en plaque mince anisotrope — fonction de courant ψ.

Hypothèses (Lin 1993 ; Grouve 2020) :
- plaque mince devant la profondeur de peau (δ ≈ 6 mm à 300 kHz pour
  σ0 = 2,2·10⁴ S/m > épaisseur 3,36 mm) → courants plans, Bz uniforme dans
  l'épaisseur de chaque couche conductrice ;
- champ de réaction (blindage) négligé — l'écart est absorbé par le facteur
  d'efficacité calibré (``facteur_couplage``), cf. README « limites » ;
- tous les courants portés par les fibres ; chaque couche (twill suscepteur,
  laminé homogénéisé) porte son propre tenseur de résistivité plan.

Formulation : J = ∇×(ψ ẑ) (Jx = ∂ψ/∂y, Jy = −∂ψ/∂x) garantit ∇·J = 0.
La loi de Faraday en phasor (∇×E)z = −jωBz avec E = ρ̃J donne :

    ∂/∂x(ρyy ∂ψ/∂x) + ∂/∂y(ρxx ∂ψ/∂y) = jω·Bz

Avec Bz réel (référence de phase), ψ est en quadrature : on résout le
problème réel  ρyy·ψxx + ρxx·ψyy = ω·Bz  avec ψ = 0 au bord (aucun courant
ne traverse le chant de la plaque). Le courant d'excitation étant une valeur
RMS, Bz est RMS et la dissipation moyenne est q = ρxx·Jx² + ρyy·Jy² (W/m³).
"""

from __future__ import annotations

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve


def resoudre_psi(Bz: np.ndarray, dx: float, dy: float,
                 rho_xx: float, rho_yy: float, omega: float) -> np.ndarray:
    """Résout ρyy·ψxx + ρxx·ψyy = ω·Bz, ψ=0 au bord. Renvoie ψ (nx, ny), A/m."""
    nx, ny = Bz.shape
    nxi, nyi = nx - 2, ny - 2                      # inconnues intérieures
    if nxi <= 0 or nyi <= 0:
        return np.zeros_like(Bz)

    ax = rho_yy / dx**2
    ay = rho_xx / dy**2
    n = nxi * nyi

    idx = np.arange(n).reshape(nxi, nyi)
    diag_c = np.full(n, -2.0 * (ax + ay))
    lignes = [idx.ravel()]
    cols = [idx.ravel()]
    vals = [diag_c]
    # voisins x
    lignes += [idx[1:, :].ravel(), idx[:-1, :].ravel()]
    cols += [idx[:-1, :].ravel(), idx[1:, :].ravel()]
    vals += [np.full(idx[1:, :].size, ax), np.full(idx[1:, :].size, ax)]
    # voisins y
    lignes += [idx[:, 1:].ravel(), idx[:, :-1].ravel()]
    cols += [idx[:, :-1].ravel(), idx[:, 1:].ravel()]
    vals += [np.full(idx[:, 1:].size, ay), np.full(idx[:, 1:].size, ay)]

    A = sparse.csr_matrix(
        (np.concatenate(vals), (np.concatenate(lignes), np.concatenate(cols))),
        shape=(n, n),
    )
    b = omega * Bz[1:-1, 1:-1].ravel()
    psi = np.zeros_like(Bz)
    psi[1:-1, 1:-1] = spsolve(A, b).reshape(nxi, nyi)
    return psi


def densite_joule(psi: np.ndarray, dx: float, dy: float,
                  rho_xx: float, rho_yy: float) -> np.ndarray:
    """Dissipation Joule moyenne q(x, y) en W/m³ à partir de ψ (RMS)."""
    Jx = np.gradient(psi, dy, axis=1)              # ∂ψ/∂y
    Jy = -np.gradient(psi, dx, axis=0)             # −∂ψ/∂x
    return rho_xx * Jx**2 + rho_yy * Jy**2
