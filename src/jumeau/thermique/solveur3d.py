"""Solveur thermique 3D transitoire par méthode des lignes (différences finies).

Généralisation 3D du modèle 1D validé (notebook MAX_InductionNumerical /
Samanis et al. 2026 éq. 2-3) :

- grille nodale x (longueur) × y (largeur) × z (épaisseur du stack complet
  laminé sup + film + laminé inf), nœuds SUR les surfaces ;
- nœuds intérieurs : ∂T/∂t = [kx·δ²x + ky·δ²y + kz·δ²z]T/(ρ·cp_app) + Q/(ρ·cp_app) ;
- nœuds de bord : demi-cellule de contrôle, préfacteur 2/d (identique à
  l'éq. 3 du 1D) avec flux surfaciques convection + rayonnement (Kelvin) ;
- face supérieure (z=0, côté bobine) : sous l'empreinte céramique/CFC ->
  conductance de contact h_contact vers T_puits (bobine + concentrateur
  refroidis, O'Shaughnessey 2014) ; hors empreinte -> convection + rayonnement ;
- face inférieure : convection h_bas + rayonnement vers T_amb ;
- chants (x, y) : convection.

La fusion est absorbée par le cp apparent (pic gaussien), cf. materiaux.py.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import sparse
from scipy.integrate import solve_ivp

from ..materiaux import Ambiant, ContactCeramique, Materiau

KELVIN = 273.15


@dataclass
class Grille3D:
    """Grille nodale régulière par axe, nœuds sur les surfaces."""

    longueur: float
    largeur: float
    epaisseur: float          # stack complet
    z_interface: float        # profondeur de l'interface de soudure
    nx: int = 49
    ny: int = 17
    nz: int = 15

    def __post_init__(self):
        self.x = np.linspace(0.0, self.longueur, self.nx)
        self.y = np.linspace(0.0, self.largeur, self.ny)
        self.z = np.linspace(0.0, self.epaisseur, self.nz)
        self.dx = self.x[1] - self.x[0]
        self.dy = self.y[1] - self.y[0]
        self.dz = self.z[1] - self.z[0]
        self.iz_interface = int(np.argmin(np.abs(self.z - self.z_interface)))

    @property
    def n(self) -> int:
        return self.nx * self.ny * self.nz

    def indice_z(self, position: str | float) -> int:
        """'surface' | 'interface' | 'opposee' | profondeur en mètres."""
        if isinstance(position, str):
            return {"surface": 0, "interface": self.iz_interface, "opposee": self.nz - 1}[position]
        return int(np.argmin(np.abs(self.z - float(position))))

    def indice_xy(self, x: float, y: float) -> tuple[int, int]:
        return int(np.argmin(np.abs(self.x - x))), int(np.argmin(np.abs(self.y - y)))


class SolveurThermique3D:
    """Intègre ∂T/∂t sur la grille avec une source volumique Q(t, x, y, z).

    ``source_fn(t) -> ndarray (nx, ny, nz)`` en W/m³ (peut être un champ figé
    par morceaux dans le temps — passes successives du procédé).
    ``masque_ceramique`` : bool (nx, ny) — True là où la face supérieure est
    en contact avec la céramique/CFC pressés (conductance vers le puits).
    Peut être un callable ``t -> masque`` pour suivre le spot actif du
    procédé séquentiel (le concentrateur n'appuie que sur l'empreinte active).
    """

    def __init__(
        self,
        grille: Grille3D,
        materiau: Materiau,
        ambiant: Ambiant,
        contact: ContactCeramique,
        masque_ceramique=None,
    ):
        self.g = grille
        self.mat = materiau
        self.amb = ambiant
        self.contact = contact
        if masque_ceramique is None:
            masque_ceramique = np.zeros((grille.nx, grille.ny), dtype=bool)
        self.masque_ceramique = masque_ceramique

    # ------------------------------------------------------------------
    def _rhs(self, t: float, Tflat: np.ndarray, source_fn) -> np.ndarray:
        g, mat, amb = self.g, self.mat, self.amb
        T = Tflat.reshape(g.nx, g.ny, g.nz)
        cp = mat.cp_apparent(T)
        rc = mat.densite * cp                       # ρ·cp_app, J/m3.K
        dT = np.zeros_like(T)

        kx = ky = mat.k_plan
        kz = mat.k_z

        # --- conduction : différences secondes intérieures, demi-cellule aux bords
        # axe x
        dT[1:-1, :, :] += kx * (T[:-2, :, :] - 2.0 * T[1:-1, :, :] + T[2:, :, :]) / g.dx**2
        dT[0, :, :] += (2.0 / g.dx) * (kx * (T[1, :, :] - T[0, :, :]) / g.dx
                                       + amb.h_convection * (amb.T_amb - T[0, :, :]))
        dT[-1, :, :] += (2.0 / g.dx) * (kx * (T[-2, :, :] - T[-1, :, :]) / g.dx
                                        + amb.h_convection * (amb.T_amb - T[-1, :, :]))
        # axe y
        dT[:, 1:-1, :] += ky * (T[:, :-2, :] - 2.0 * T[:, 1:-1, :] + T[:, 2:, :]) / g.dy**2
        dT[:, 0, :] += (2.0 / g.dy) * (ky * (T[:, 1, :] - T[:, 0, :]) / g.dy
                                       + amb.h_convection * (amb.T_amb - T[:, 0, :]))
        dT[:, -1, :] += (2.0 / g.dy) * (ky * (T[:, -2, :] - T[:, -1, :]) / g.dy
                                        + amb.h_convection * (amb.T_amb - T[:, -1, :]))
        # axe z — intérieur
        dT[:, :, 1:-1] += kz * (T[:, :, :-2] - 2.0 * T[:, :, 1:-1] + T[:, :, 2:]) / g.dz**2

        # face supérieure z=0 (côté bobine)
        T_top = T[:, :, 0]
        Ttop_K = T_top + KELVIN
        Ta_K = amb.T_amb + KELVIN
        flux_libre = (amb.h_convection * (amb.T_amb - T_top)
                      + mat.emissivite * amb.stefan_boltzmann * (Ta_K**4 - Ttop_K**4))
        flux_ceram = self.contact.h_contact * (self.contact.T_puits - T_top)
        masque = self.masque_ceramique(t) if callable(self.masque_ceramique) else self.masque_ceramique
        flux_top = np.where(masque, flux_ceram, flux_libre)
        dT[:, :, 0] += (2.0 / g.dz) * (kz * (T[:, :, 1] - T_top) / g.dz + flux_top)

        # face inférieure z=h (côté bâti/table)
        T_bot = T[:, :, -1]
        Tbot_K = T_bot + KELVIN
        flux_bot = (amb.h_bas * (amb.T_amb - T_bot)
                    + mat.emissivite * amb.stefan_boltzmann * (Ta_K**4 - Tbot_K**4))
        dT[:, :, -1] += (2.0 / g.dz) * (kz * (T[:, :, -2] - T_bot) / g.dz + flux_bot)

        # --- source Joule + normalisation par la masse thermique
        Q = source_fn(t)
        return ((dT + Q) / rc).ravel()

    # ------------------------------------------------------------------
    def _sparsite_jacobien(self) -> sparse.csr_matrix:
        g = self.g
        n = g.n
        idx = np.arange(n).reshape(g.nx, g.ny, g.nz)
        lignes, cols = [], []

        def lier(a, b):
            lignes.append(a.ravel())
            cols.append(b.ravel())

        lier(idx, idx)
        lier(idx[1:], idx[:-1]); lier(idx[:-1], idx[1:])
        lier(idx[:, 1:], idx[:, :-1]); lier(idx[:, :-1], idx[:, 1:])
        lier(idx[:, :, 1:], idx[:, :, :-1]); lier(idx[:, :, :-1], idx[:, :, 1:])
        lignes = np.concatenate(lignes)
        cols = np.concatenate(cols)
        donnees = np.ones(len(lignes), dtype=np.int8)
        return sparse.csr_matrix((donnees, (lignes, cols)), shape=(n, n))

    # ------------------------------------------------------------------
    def simuler(
        self,
        source_fn,
        t_span: tuple[float, float],
        t_eval: np.ndarray | None = None,
        T_initial: np.ndarray | float | None = None,
        rtol: float = 1e-4,
        atol: float = 1e-2,
        max_step: float = 5.0,
    ):
        """Intègre et renvoie ``sol`` de solve_ivp ; sol.y a la forme (n, nt).

        ``resultat_3d(sol, i)`` redonne le champ (nx, ny, nz) au pas i.
        """
        g = self.g
        if T_initial is None:
            T0 = np.full(g.n, self.amb.T_amb)
        elif np.isscalar(T_initial):
            T0 = np.full(g.n, float(T_initial))
        else:
            T0 = np.asarray(T_initial).ravel().copy()

        sol = solve_ivp(
            self._rhs, t_span, T0, args=(source_fn,),
            method="BDF", t_eval=t_eval,
            jac_sparsity=self._sparsite_jacobien(),
            rtol=rtol, atol=atol, max_step=max_step,
        )
        if not sol.success:
            raise RuntimeError(f"solve_ivp a échoué : {sol.message}")
        return sol

    def resultat_3d(self, sol, i: int) -> np.ndarray:
        g = self.g
        return sol.y[:, i].reshape(g.nx, g.ny, g.nz)

    def serie_temporelle(self, sol, x: float, y: float, z: str | float) -> np.ndarray:
        """Température au nœud le plus proche de (x, y, z) pour tous les pas."""
        g = self.g
        ix, iy = g.indice_xy(x, y)
        iz = g.indice_z(z)
        return sol.y.reshape(g.nx, g.ny, g.nz, -1)[ix, iy, iz, :]
