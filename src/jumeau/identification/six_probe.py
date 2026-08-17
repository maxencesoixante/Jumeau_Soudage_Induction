"""Extraction de la conductivité électrique anisotrope par méthode « six-probe ».

Volet LOGICIEL de la caractérisation de la source du jumeau (issue #49). La
méthode six-probe (van den Berg, thèse Univ. Twente 2024, DOI
10.3990/1.9789036561495, ch. 2) injecte un courant continu sur la face
supérieure d'un coupon et mesure la chute de tension en face SUPÉRIEURE (``V_t``)
et INFÉRIEURE (``V_b``) sur une même distance ``l``. Comme la conductivité est
très anisotrope (in-plane >> transverse), le courant se redistribue dans
l'épaisseur et ``V_t != V_b`` ; le couple ``(V_t, V_b)`` + la géométrie permettent
de remonter à ``(sigma_x, sigma_z)``.

Trois briques :
- :func:`voltages_directes`  — modèle DIRECT (grille de résistances 2D, coupe
  x-z, analyse nodale) : ``(sigma_x, sigma_z, géo) -> (V_t, V_b)`` ;
- :func:`extraire_sigma`     — INVERSION (Levenberg-Marquardt sur log(sigma))
  ``(V_t, V_b, géo) -> (sigma_x, sigma_z)`` ;
- :func:`busch_sigma`        — approximation ANALYTIQUE de Busch (n=1), pour un
  garde-fou de sanité sur empilement mono-orientation.

Le solveur EM du jumeau (``em/foucault.py``) consomme déjà un tenseur
``(rho_xx, rho_yy) = (1/sigma_x, 1/sigma_y)`` : la conductivité mesurée s'y
insère sans refonte (issue #51).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.optimize import least_squares


@dataclass(frozen=True)
class GeometrieSixProbe:
    """Géométrie d'un essai six-probe (mètres, ampères) + finesse de grille.

    ``L`` : distance entre électrodes d'injection (face sup.) ;
    ``l`` : distance entre sondes de tension (centrée) ;
    ``w`` : largeur du coupon ; ``t`` : épaisseur ;
    ``I`` : courant injecté ; ``nx``/``nz`` : nœuds de la grille (x, épaisseur).
    """

    L: float = 0.120
    l: float = 0.040
    w: float = 0.020
    t: float = 0.0025
    I: float = 0.200
    nx: int = 81
    nz: int = 11


def voltages_directes(sigma_x: float, sigma_z: float,
                      geo: GeometrieSixProbe = GeometrieSixProbe()) -> tuple[float, float]:
    """Modèle direct : renvoie ``(V_t, V_b)`` [V] pour ``(sigma_x, sigma_z)`` [S/m].

    Grille de résistances 2D en coupe x-z (largeur ``w`` en facteur d'échelle).
    Courant ``+I`` injecté en A = (x=0, face sup.), ``-I`` en B = (x=L, face sup.).
    Analyse nodale (Kirchhoff + Ohm), nœud B pris comme référence (masse).
    """
    L, l, w, t, I, nx, nz = geo.L, geo.l, geo.w, geo.t, geo.I, geo.nx, geo.nz
    dx = L / (nx - 1)
    dz = t / (nz - 1)
    N = nx * nz

    def idx(i, j):
        return i * nz + j

    # volumes de contrôle : demi-mailles au bord
    dz_eff = np.full(nz, dz); dz_eff[0] = dz_eff[-1] = dz / 2.0
    dx_eff = np.full(nx, dx); dx_eff[0] = dx_eff[-1] = dx / 2.0

    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    diag = np.zeros(N)

    # liaisons horizontales (courant selon x) : G = sigma_x * (w * dz) / dx
    for i in range(nx - 1):
        for j in range(nz):
            g = sigma_x * (w * dz_eff[j]) / dx
            a, b = idx(i, j), idx(i + 1, j)
            rows += [a, b]; cols += [b, a]; data += [-g, -g]
            diag[a] += g; diag[b] += g

    # liaisons verticales (courant selon z) : G = sigma_z * (w * dx) / dz
    for i in range(nx):
        for j in range(nz - 1):
            g = sigma_z * (w * dx_eff[i]) / dz
            a, b = idx(i, j), idx(i, j + 1)
            rows += [a, b]; cols += [b, a]; data += [-g, -g]
            diag[a] += g; diag[b] += g

    rows += list(range(N)); cols += list(range(N)); data += list(diag)
    G = sp.csr_matrix((data, (rows, cols)), shape=(N, N))

    c = np.zeros(N)
    A_node, B_node = idx(0, 0), idx(nx - 1, 0)
    c[A_node] = I
    c[B_node] = -I

    # masse au nœud B : on retire sa ligne/colonne et on résout le système réduit
    keep = np.array([k for k in range(N) if k != B_node])
    Gr = G[keep][:, keep].tocsc()
    vr = spla.spsolve(Gr, c[keep])
    v = np.zeros(N)
    v[keep] = vr  # v[B] = 0 (référence)

    # sondes de tension à x = (L-l)/2 et (L+l)/2, faces sup. (j=0) et inf. (j=nz-1)
    i1 = int(round(((L - l) / 2) / dx))
    i2 = int(round(((L + l) / 2) / dx))
    V_t = abs(v[idx(i1, 0)] - v[idx(i2, 0)])
    V_b = abs(v[idx(i1, nz - 1)] - v[idx(i2, nz - 1)])
    return V_t, V_b


def extraire_sigma(V_t: float, V_b: float,
                   geo: GeometrieSixProbe = GeometrieSixProbe(),
                   sigma0: tuple[float, float] = (1.0e4, 10.0)) -> tuple[float, float]:
    """Inversion : ``(V_t, V_b, géo) -> (sigma_x, sigma_z)`` [S/m].

    Levenberg-Marquardt sur ``log(sigma)`` (garantit la positivité), résidu
    relatif sur les deux tensions. ``sigma0`` = point de départ (S/m).
    """
    log0 = np.log(np.asarray(sigma0, float))

    def residu(logs):
        sx, sz = np.exp(logs)
        vt, vb = voltages_directes(sx, sz, geo)
        return [(vt - V_t) / V_t, (vb - V_b) / V_b]

    res = least_squares(residu, log0, method="lm", xtol=1e-12, ftol=1e-12)
    sx, sz = np.exp(res.x)
    return float(sx), float(sz)


def busch_sigma(V_t: float, V_b: float,
                geo: GeometrieSixProbe = GeometrieSixProbe()) -> tuple[float, float]:
    """Approximation analytique de Busch (n=1) — garde-fou mono-orientation.

    D'après van den Berg (2024) éq. 2.8-2.9 :
    ``sqrt(rho_z/rho_x) = (L/(pi t)) arccosh(V_t/V_b)`` et
    ``sqrt(rho_z rho_x) = (V_t w)/(2 I sin(pi l/2L)) tanh((pi t/L) sqrt(rho_z/rho_x))``.
    """
    L, l, w, t, I = geo.L, geo.l, geo.w, geo.t, geo.I
    a = (L / (np.pi * t)) * np.arccosh(V_t / V_b)                       # sqrt(rho_z/rho_x)
    b = (V_t * w) / (2 * I * np.sin(np.pi * l / (2 * L))) * np.tanh((np.pi * t / L) * a)  # sqrt(rho_z rho_x)
    rho_x = b / a
    rho_z = b * a
    return float(1.0 / rho_x), float(1.0 / rho_z)


def balayage_angulaire(mesures: list[tuple[float, float, float]],
                       geo: GeometrieSixProbe = GeometrieSixProbe()
                       ) -> list[tuple[float, float, float]]:
    """De ``[(theta_deg, V_t, V_b), ...]`` vers ``[(theta_deg, sigma_x, sigma_z), ...]``.

    Un coupon découpé à l'angle ``theta`` par rapport au sens chaîne donne la
    conductivité in-plane dans cette direction : reconstitue ``sigma_x(theta)``.
    """
    out = []
    for theta, vt, vb in mesures:
        sx, sz = extraire_sigma(vt, vb, geo)
        out.append((theta, sx, sz))
    return out
