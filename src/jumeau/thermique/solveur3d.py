"""Solveur thermique 3D transitoire par méthode des lignes (différences finies).

Généralisation 3D du modèle 1D validé (notebook MAX_InductionNumerical /
Samanis et al. 2026 éq. 2-3) :

- grille nodale x (longueur) × y (largeur) × z (épaisseur du stack complet
  laminé sup + film + laminé inf), nœuds SUR les surfaces ;
- nœuds intérieurs : ∂T/∂t = [kx·δ²x + ky·δ²y + kz·δ²z]T/(ρ·cp_app) + Q/(ρ·cp_app) ;
- nœuds de bord : demi-cellule de contrôle, préfacteur 2/d (identique à
  l'éq. 3 du 1D) avec flux surfaciques convection + rayonnement (Kelvin) ;
- face supérieure (z=0, côté bobine) : sous l'empreinte céramique/MFC ->
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


def bracket_lineaire(axe: np.ndarray, position: float) -> tuple[int, float]:
    """Indice du nœud inférieur encadrant ``position`` sur un axe régulier
    croissant, et poids de fraction ``w`` (0 = sur le nœud inférieur, 1 = sur
    le supérieur) pour une interpolation linéaire ``(1-w)*champ[i] + w*champ[i+1]``.
    ``position`` hors domaine est clampée (comportement nœud-le-plus-proche
    au-delà des bords, comme avant).

    Motivation (cf. rapport de vérification mesh-convergence 2026-07-21) :
    ``Grille3D.indice_xy`` (nœud le plus proche, ``argmin``) peut décaler la
    position LUE de jusqu'à dx/2 sur un profil pointu (ex. TC4 à x=90 mm tombe
    pile entre deux nœuds à la grille de calibration 31×11, dx=4 mm -> lecture
    décalée de 2 mm) ; cette erreur de positionnement discret n'est PAS une
    erreur de discrétisation du solveur (elle ne décroît pas monotone avec le
    maillage — elle peut même s'annuler par coïncidence à certains nx, cf.
    rapport) et fausse toute étude de convergence si elle n'est pas isolée par
    une lecture interpolée. Utilisée par ``SolveurThermique{2D,3D}.serie_temporelle``
    (lecture des TC) et par ``jumeau.procede.Essai._T_ctrl`` (nœud de contrôle
    du thermostat)."""
    n = len(axe)
    dx = axe[1] - axe[0]
    i = int(np.floor((position - axe[0]) / dx))
    i = int(np.clip(i, 0, n - 2))
    w = float(np.clip((position - axe[i]) / dx, 0.0, 1.0))
    return i, w


class SolveurThermique3D:
    """Intègre ∂T/∂t sur la grille avec une source volumique Q(t, x, y, z).

    ``source_fn(t) -> ndarray (nx, ny, nz)`` en W/m³ (peut être un champ figé
    par morceaux dans le temps — passes successives du procédé).
    ``masque_ceramique`` : bool (nx, ny) — True là où la face supérieure est
    en contact avec la céramique/MFC pressés (conductance vers le puits).
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
        if materiau.a_k_variable() and (materiau.k_plan_x is not None
                                        or materiau.k_plan_y is not None):
            raise ValueError(
                "k(T) (k_plan_T/k_z_T) et anisotropie in-plane (k_plan_x/k_plan_y) "
                "ne sont pas combinables (interaction non explorée) — n'en activer "
                "qu'un seul. Cf. Materiau.a_k_variable / docstring k_plan_field."
            )

    # ------------------------------------------------------------------
    def _rhs(self, t: float, Tflat: np.ndarray, source_fn) -> np.ndarray:
        g, mat, amb = self.g, self.mat, self.amb
        T = Tflat.reshape(g.nx, g.ny, g.nz)
        cp = mat.cp_apparent(T)
        rc = mat.densite * cp                       # ρ·cp_app, J/m3.K
        dT = np.zeros_like(T)

        Ta_K = amb.T_amb + KELVIN
        masque = self.masque_ceramique(t) if callable(self.masque_ceramique) else self.masque_ceramique

        if not mat.a_k_variable():
            # ===== chemin historique : k scalaire/anisotrope constant (bit-identique) =====
            kx, ky = mat.k_plan_xy()  # isotrope par défaut (kx=ky=k_plan) sauf k_plan_x/y renseignés
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
            flux_libre = (amb.h_convection * (amb.T_amb - T_top)
                          + mat.emissivite * amb.stefan_boltzmann * (Ta_K**4 - Ttop_K**4))
            flux_ceram = self.contact.h_contact * (self.contact.T_puits - T_top)
            flux_top = np.where(masque, flux_ceram, flux_libre)
            dT[:, :, 0] += (2.0 / g.dz) * (kz * (T[:, :, 1] - T_top) / g.dz + flux_top)

            # face inférieure z=h (côté bâti/table)
            T_bot = T[:, :, -1]
            Tbot_K = T_bot + KELVIN
            flux_bot = (amb.h_bas * (amb.T_amb - T_bot)
                        + mat.emissivite * amb.stefan_boltzmann * (Ta_K**4 - Tbot_K**4))
            dT[:, :, -1] += (2.0 / g.dz) * (kz * (T[:, :, -2] - T_bot) / g.dz + flux_bot)
        else:
            # ===== forme FLUX-CONSERVATIVE à k(T) variable (Lionetto éq. 5) =====
            # Flux de face F_{i+½} = k_face·(T[i+1]−T[i])/d, k_face = moyenne
            # arithmétique des k(T) des deux nœuds ; div = (F_{i+½}−F_{i−½})/d.
            # À k constant, k_face = k et cette forme se réduit exactement au
            # laplacien ci-dessus (à l'ordre des opérations flottantes près) —
            # cf. test_thermique.py::test_k_variable_constante_egale_scalaire.
            kpf = mat.k_plan_field(T)          # (nx, ny, nz) — in-plane k(T)
            kzf = mat.k_z_field(T)             # (nx, ny, nz) — transverse k_z(T)

            # axe x
            kfx = 0.5 * (kpf[:-1, :, :] + kpf[1:, :, :])
            Fx = kfx * (T[1:, :, :] - T[:-1, :, :]) / g.dx
            dT[1:-1, :, :] += (Fx[1:, :, :] - Fx[:-1, :, :]) / g.dx
            dT[0, :, :] += (2.0 / g.dx) * (Fx[0, :, :]
                                           + amb.h_convection * (amb.T_amb - T[0, :, :]))
            dT[-1, :, :] += (2.0 / g.dx) * (-Fx[-1, :, :]
                                            + amb.h_convection * (amb.T_amb - T[-1, :, :]))
            # axe y
            kfy = 0.5 * (kpf[:, :-1, :] + kpf[:, 1:, :])
            Fy = kfy * (T[:, 1:, :] - T[:, :-1, :]) / g.dy
            dT[:, 1:-1, :] += (Fy[:, 1:, :] - Fy[:, :-1, :]) / g.dy
            dT[:, 0, :] += (2.0 / g.dy) * (Fy[:, 0, :]
                                           + amb.h_convection * (amb.T_amb - T[:, 0, :]))
            dT[:, -1, :] += (2.0 / g.dy) * (-Fy[:, -1, :]
                                            + amb.h_convection * (amb.T_amb - T[:, -1, :]))
            # axe z — intérieur
            kfz = 0.5 * (kzf[:, :, :-1] + kzf[:, :, 1:])
            Fz = kfz * (T[:, :, 1:] - T[:, :, :-1]) / g.dz
            dT[:, :, 1:-1] += (Fz[:, :, 1:] - Fz[:, :, :-1]) / g.dz

            # face supérieure z=0 (côté bobine) — flux de bord identiques au chemin scalaire
            T_top = T[:, :, 0]
            Ttop_K = T_top + KELVIN
            flux_libre = (amb.h_convection * (amb.T_amb - T_top)
                          + mat.emissivite * amb.stefan_boltzmann * (Ta_K**4 - Ttop_K**4))
            flux_ceram = self.contact.h_contact * (self.contact.T_puits - T_top)
            flux_top = np.where(masque, flux_ceram, flux_libre)
            dT[:, :, 0] += (2.0 / g.dz) * (Fz[:, :, 0] + flux_top)

            # face inférieure z=h (côté bâti/table)
            T_bot = T[:, :, -1]
            Tbot_K = T_bot + KELVIN
            flux_bot = (amb.h_bas * (amb.T_amb - T_bot)
                        + mat.emissivite * amb.stefan_boltzmann * (Ta_K**4 - Tbot_K**4))
            dT[:, :, -1] += (2.0 / g.dz) * (-Fz[:, :, -1] + flux_bot)

        # --- source Joule + normalisation par la masse thermique
        # source_fn est normalisée par simuler() : signature (t, T) -> Q, ce qui
        # permet une source asservie à la température (coupure sur consigne).
        Q = source_fn(t, T)
        return ((dT + Q) / rc).ravel()

    # ------------------------------------------------------------------
    def _sparsite_jacobien(self, colonnes_controle=None) -> sparse.csr_matrix:
        """Motif de sparsité du jacobien de ``_rhs``.

        Le stencil à 7 points (diagonale + 6 voisins) couvre le terme de
        conduction. ``colonnes_controle`` ajoute des colonnes PLEINES (tous
        les nœuds en ligne) pour les nœuds de contrôle d'une source asservie
        (cf. ``simuler(noeuds_controle=...)``) : quand ``source_fn(t, T)``
        module Q(x,y,z) par un facteur scalaire dépendant de T à un nœud de
        contrôle c (thermostat, cf. Essai.source_fn), TOUT nœud i où Q_i≠0
        acquiert une dérivée ∂(Q_i/rc_i)/∂T_c ≠ 0. Sans cette colonne, BDF
        ne "voit" pas ce couplage (il est hors motif -> jamais évalué par les
        différences finies groupées par couleur de scipy), et Newton peine à
        converger près de la consigne (pas minuscules, quasi-plantage) alors
        que la source reste en réalité localement quasi-linéaire en T_c.
        Une poignée de colonnes pleines (une par nœud de contrôle distinct,
        typiquement un par spot) coûte peu face au stencil (7·n non-nuls) et
        la sparsité globale reste excellente.
        """
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
        if colonnes_controle is not None:
            colonnes_controle = np.atleast_1d(np.asarray(colonnes_controle, dtype=np.intp))
            colonnes_controle = np.unique(colonnes_controle)
            toutes_lignes = np.arange(n, dtype=np.intp)
            for c in colonnes_controle:
                lignes.append(toutes_lignes)
                cols.append(np.full(n, c, dtype=np.intp))
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
        noeuds_controle=None,
    ):
        """Intègre et renvoie ``sol`` de solve_ivp ; sol.y a la forme (n, nt).

        ``source_fn`` : soit ``f(t) -> Q`` (source imposée), soit ``f(t, T) -> Q``
        (source asservie au champ de température, T de forme (nx, ny, nz)).
        ``noeuds_controle`` : nœud(s) de contrôle dont dépend ``source_fn(t, T)``
        (thermostat/asservissement), à déclarer pour que le jacobien creux
        fourni à BDF inclue le couplage source<->T_controle (sinon les
        différences finies groupées par couleur ne l'évaluent jamais, cf.
        ``_sparsite_jacobien``). Chaque élément est un triplet d'indices
        ``(ix, iy, iz)`` ou un indice aplati déjà en ``ravel()`` order C ;
        ``None`` (défaut) pour une source non asservie (aucune colonne extra).
        ``resultat_3d(sol, i)`` redonne le champ (nx, ny, nz) au pas i.
        """
        import inspect

        n_params = len(inspect.signature(source_fn).parameters)
        if n_params == 1:
            f_source = source_fn
            source_fn = lambda t, T: f_source(t)

        g = self.g
        if T_initial is None:
            T0 = np.full(g.n, self.amb.T_amb)
        elif np.isscalar(T_initial):
            T0 = np.full(g.n, float(T_initial))
        else:
            T0 = np.asarray(T_initial).ravel().copy()

        colonnes_controle = None
        if noeuds_controle is not None:
            colonnes_controle = [
                int(np.ravel_multi_index(c, (g.nx, g.ny, g.nz))) if not np.isscalar(c) else int(c)
                for c in noeuds_controle
            ]

        sol = solve_ivp(
            self._rhs, t_span, T0, args=(source_fn,),
            method="BDF", t_eval=t_eval,
            jac_sparsity=self._sparsite_jacobien(colonnes_controle),
            rtol=rtol, atol=atol, max_step=max_step,
        )
        if not sol.success:
            raise RuntimeError(f"solve_ivp a échoué : {sol.message}")
        return sol

    def resultat_3d(self, sol, i: int) -> np.ndarray:
        g = self.g
        return sol.y[:, i].reshape(g.nx, g.ny, g.nz)

    def serie_temporelle(self, sol, x: float, y: float, z: str | float) -> np.ndarray:
        """Température interpolée BILINÉAIREMENT en (x, y) pour tous les pas
        (nœud z le plus proche de ``z`` : ``indice_z`` accepte des plans
        catégoriels 'surface'/'interface'/'opposee', pas des positions
        continues -- non interpolé, cf. ``bracket_lineaire``). Avant
        2026-07-21 : nœud (x, y) le plus proche (``indice_xy``), qui pouvait
        décaler la lecture de jusqu'à dx/2 -- cf. docstring ``bracket_lineaire``."""
        g = self.g
        iz = g.indice_z(z)
        ix, wx = bracket_lineaire(g.x, x)
        iy, wy = bracket_lineaire(g.y, y)
        champ = sol.y.reshape(g.nx, g.ny, g.nz, -1)[:, :, iz, :]
        return ((1.0 - wx) * (1.0 - wy) * champ[ix, iy]
                + wx * (1.0 - wy) * champ[ix + 1, iy]
                + (1.0 - wx) * wy * champ[ix, iy + 1]
                + wx * wy * champ[ix + 1, iy + 1])
