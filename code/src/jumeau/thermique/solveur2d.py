"""Solveur thermique 2D transitoire, formulation LUMPÉE dans l'épaisseur.

Réduction du solveur 3D (``solveur3d.SolveurThermique3D``) au plan de
l'interface de soudure : la physique pertinente pour la confrontation aux
thermocouples des essais A/B (tous à l'interface) ne demande plus de
résoudre le gradient dans l'épaisseur (cf. décision de modélisation du
2026-07-20 — le déficit de gradient dans l'épaisseur (face opposée) est un
écart structurel non corrigeable, README § Limites connues). Le stack complet (laminé sup +
film + twill interface + laminé inf) est lumpé en UNE seule maille dans
l'épaisseur, de sorte que la température nodale (x, y) représente
directement l'interface.

Bilan par maille (imposé, cf. mission thermal-solver-engineer 2026-07-20) :

    (ρcp)_eff · e_eff · ∂T/∂t = ∇·(k_eff · e_eff · ∇T) + P_surf(x,y,t)
                                 − h_haut·(T − T_puits)·[masque MFC actif]
                                 − h_bas·(T − T_amb)

- ``e_eff`` : épaisseur totale du stack (identique à ``Grille3D.epaisseur``) ;
- ``(ρcp)_eff`` : le modèle thermique actuel n'a qu'un seul ``Materiau``
  massif (densité/cp/k identiques pour laminé et twill — seules les
  propriétés ÉLECTRIQUES du twill diffèrent, cf. ``geometrie.CoucheConductrice``
  et ``em/source_joule.py``) : la « moyenne pondérée par la masse des
  couches » demandée par la mission se réduit donc, avec les données de
  config actuelles, à ``mat.densite * mat.cp_apparent(T)`` — cp apparent AVEC
  le pic de fusion gaussien conservé (même fonction que le 3D, cf.
  ``materiaux.Materiau.cp_apparent``). Si des propriétés thermiques propres
  au twill sont mesurées un jour, cette moyenne devra être généralisée ici ;
- ``k_eff`` : ``mat.k_plan`` (conductivité dans le plan, identique au 3D) —
  dans le terme de conduction, ``e_eff`` se simplifie exactement de part et
  d'autre (∇·(k·e·∇T) / (ρcp·e) = k·∇²T / (ρcp)), donc le terme de conduction
  a la MÊME forme que le 3D (kx/rc, ky/rc), indépendamment de e_eff ;
- ``k_eff`` ANISOTROPE (prototype 2026-07-31, flag OFF par défaut) : ``kx``,
  ``ky`` proviennent de ``mat.k_plan_xy()`` (``materiaux.Materiau.k_plan_x``/
  ``k_plan_y``, ``None`` => isotrope, ``kx = ky = k_plan``, comportement
  historique bit-identique). Justification physique : le laminé CF/PEKK
  quasi-iso [45/-45/0/90]3s n'a pas de raison stricte d'être isotrope dans le
  plan une fois homogénéisé avec la géométrie du process (profil « M » en y,
  dissipation longitudinale en x) — cf. docs/modele/README.md § résidu
  ouvert, option (A) ;
- ``P_surf(x, y, t)`` : puissance Joule TOTALE intégrée sur l'épaisseur
  (W/m²), construite en sommant sur z le champ ``source_spot`` 3D existant
  (``jumeau.procede.Essai.source_fn_2d`` fait cette somme une fois par spot) ;
  Q_volumique_2D = P_surf / e_eff (W/m³), même rôle que ``Q`` dans le 3D ;
- ``h_haut`` (NOUVEAU, ``materiaux.ContactCeramique.h_haut``) : perte
  effective vers le puits céramique/concentrateur, active seulement là où le
  masque MFC l'est (même masque que le 3D) — remplace ``h_contact`` mais
  absorbe aussi la conduction à travers le demi-stack supérieur ;
- ``h_bas`` (NOUVEAU, ``materiaux.Ambiant.h_bas_2d``) : perte effective vers
  la face opposée/ambiant, appliquée PARTOUT (pas de masque) — absorbe
  convection+rayonnement de la face inférieure ET la conduction à travers le
  demi-stack inférieur du modèle 3D.

Les DEUX coefficients sont volontairement linéaires en (T − T_ref) : ce sont
des coefficients EFFECTIFS destinés à être recalibrés pour ce modèle réduit
(``calibration-uq-specialist``), pas une reproduction terme à terme du 3D
(qui, lui, distingue en plus convection+rayonnement T⁴ à chaque face).

Bords du domaine (x=0, x=L, y=0, y=W) : ce sont les chants RÉELS du stratifié
(hauteur e_eff), pas des artefacts du maillage — on y conserve donc EXACTEMENT
le traitement des chants du 3D (convection + rayonnement, préfacteur 2/d de
demi-cellule ; cf. solveur3d.py) : ``h_convection``/``emissivite`` restent les
grandeurs de surface non lumpées, réutilisées telles quelles depuis
``Ambiant``/``Materiau``. C'est le seul endroit où le 2D garde un terme non
linéaire (rayonnement, Kelvin) — pour rester cohérent avec la consigne
« conserver le rayonnement en Kelvin dans le jacobien » du solveur 3D.

Intégration : même schéma que le 3D (BDF, jacobien creux, colonnes pleines
pour les nœuds de contrôle du thermostat de consigne) mais stencil à 5 points
(x, y) au lieu de 7 (x, y, z) — la suppression de nz (~13-15) est ce qui donne
le gain de vitesse attendu (cf. rapport de vérification).

Mapping des thermocouples : un TC ``z: interface`` correspond directement à
la maille (x, y) de ce modèle. Les TC ``z: surface`` et ``z: opposee`` ne
sont PAS représentables (il n'y a plus qu'un seul nœud dans l'épaisseur) —
``jumeau.procede.Essai.series_tc`` les exclut silencieusement en mode 2D.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse
from scipy.integrate import solve_ivp

from ..materiaux import Ambiant, ContactCeramique, Materiau
from .solveur3d import KELVIN, Grille3D, bracket_lineaire


class SolveurThermique2D:
    """Intègre ∂T/∂t sur la grille PLANE (x, y) avec une source surfacique
    P_surf(t, x, y) [W/m²], modèle lumpé dans l'épaisseur (cf. docstring module).

    ``grille`` : une ``Grille3D`` existante (partage EXACTEMENT le même maillage
    (x, y) — et donc les mêmes positions de spots/TC — que le modèle 3D) dont
    seuls ``x, y, nx, ny, dx, dy, longueur, largeur, indice_xy`` sont utilisés ;
    ``z``/``nz`` sont ignorés. ``epaisseur`` (m), si fournie, écrase
    ``grille.epaisseur`` comme épaisseur effective du stack lumpé (par défaut,
    l'épaisseur totale de la grille 3D — cohérent avec ``construire_grille``).
    ``masque_ceramique`` : identique au 3D — bool (nx, ny), ou callable
    ``t -> masque`` pour suivre le spot actif du procédé séquentiel.
    """

    def __init__(
        self,
        grille: Grille3D,
        materiau: Materiau,
        ambiant: Ambiant,
        contact: ContactCeramique,
        masque_ceramique=None,
        epaisseur: float | None = None,
    ):
        self.g = grille
        self.mat = materiau
        self.amb = ambiant
        self.contact = contact
        self.e_eff = float(epaisseur) if epaisseur is not None else float(grille.epaisseur)
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
        g, mat, amb, contact = self.g, self.mat, self.amb, self.contact
        T = Tflat.reshape(g.nx, g.ny)
        cp = mat.cp_apparent(T)
        rc = mat.densite * cp                       # (ρ·cp)_eff, J/m3.K
        dT = np.zeros_like(T)

        # --- conduction dans le plan : différences secondes intérieures,
        # demi-cellule aux bords (identique au 3D — e_eff se simplifie du
        # terme de conduction, cf. docstring module) ; les bords (x, y) sont
        # les CHANTS RÉELS du stratifié -> convection + rayonnement, comme
        # les chants du 3D.
        Ta_K = amb.T_amb + KELVIN

        if not mat.a_k_variable():
            # ===== chemin historique : k scalaire/anisotrope constant (bit-identique) =====
            kx, ky = mat.k_plan_xy()  # isotrope par défaut (kx=ky=k_plan) sauf k_plan_x/y renseignés

            # axe x
            dT[1:-1, :] += kx * (T[:-2, :] - 2.0 * T[1:-1, :] + T[2:, :]) / g.dx**2
            for i, voisin in ((0, 1), (-1, -2)):
                T_edge = T[i, :]
                TedgeK = T_edge + KELVIN
                # Puits conductif du montage sur le chant x=0 SEUL (bridage/appui,
                # cf. Ambiant.h_bord_x0) : 0.0 par défaut -> chant inchangé.
                extra_x0 = amb.h_bord_x0 * (amb.T_amb - T_edge) if i == 0 else 0.0
                dT[i, :] += (2.0 / g.dx) * (
                    kx * (T[voisin, :] - T_edge) / g.dx
                    + amb.h_convection * (amb.T_amb - T_edge)
                    + mat.emissivite * amb.stefan_boltzmann * (Ta_K**4 - TedgeK**4)
                    + extra_x0
                )
            # axe y
            dT[:, 1:-1] += ky * (T[:, :-2] - 2.0 * T[:, 1:-1] + T[:, 2:]) / g.dy**2
            for j, voisin in ((0, 1), (-1, -2)):
                T_edge = T[:, j]
                TedgeK = T_edge + KELVIN
                dT[:, j] += (2.0 / g.dy) * (
                    ky * (T[:, voisin] - T_edge) / g.dy
                    + amb.h_convection * (amb.T_amb - T_edge)
                    + mat.emissivite * amb.stefan_boltzmann * (Ta_K**4 - TedgeK**4)
                )
        else:
            # ===== forme FLUX-CONSERVATIVE à k(T) variable (Lionetto éq. 5) =====
            # F_{i+½} = k_face·(T[i+1]−T[i])/d, k_face = moyenne arithmétique des
            # k(T) voisins ; à k constant se réduit exactement au laplacien
            # ci-dessus. Anisotropie k_plan_x/y NON combinée avec k(T) (garde
            # __init__) : ici k in-plane isotrope k_plan_field(T).
            kpf = mat.k_plan_field(T)          # (nx, ny) — in-plane k(T)

            # axe x
            kfx = 0.5 * (kpf[:-1, :] + kpf[1:, :])
            Fx = kfx * (T[1:, :] - T[:-1, :]) / g.dx
            dT[1:-1, :] += (Fx[1:, :] - Fx[:-1, :]) / g.dx
            # chant x=0 (avec puits conductif h_bord_x0)
            T_edge = T[0, :]; TedgeK = T_edge + KELVIN
            dT[0, :] += (2.0 / g.dx) * (
                Fx[0, :]
                + amb.h_convection * (amb.T_amb - T_edge)
                + mat.emissivite * amb.stefan_boltzmann * (Ta_K**4 - TedgeK**4)
                + amb.h_bord_x0 * (amb.T_amb - T_edge)
            )
            # chant x=L
            T_edge = T[-1, :]; TedgeK = T_edge + KELVIN
            dT[-1, :] += (2.0 / g.dx) * (
                -Fx[-1, :]
                + amb.h_convection * (amb.T_amb - T_edge)
                + mat.emissivite * amb.stefan_boltzmann * (Ta_K**4 - TedgeK**4)
            )
            # axe y
            kfy = 0.5 * (kpf[:, :-1] + kpf[:, 1:])
            Fy = kfy * (T[:, 1:] - T[:, :-1]) / g.dy
            dT[:, 1:-1] += (Fy[:, 1:] - Fy[:, :-1]) / g.dy
            # chant y=0
            T_edge = T[:, 0]; TedgeK = T_edge + KELVIN
            dT[:, 0] += (2.0 / g.dy) * (
                Fy[:, 0]
                + amb.h_convection * (amb.T_amb - T_edge)
                + mat.emissivite * amb.stefan_boltzmann * (Ta_K**4 - TedgeK**4)
            )
            # chant y=W
            T_edge = T[:, -1]; TedgeK = T_edge + KELVIN
            dT[:, -1] += (2.0 / g.dy) * (
                -Fy[:, -1]
                + amb.h_convection * (amb.T_amb - T_edge)
                + mat.emissivite * amb.stefan_boltzmann * (Ta_K**4 - TedgeK**4)
            )

        # --- pertes effectives top/bas (nouveaux coefficients lumpés, cf.
        # docstring module) : volumiques (divisées par e_eff, PAS par 2/dz —
        # ce n'est pas une demi-cellule de bord, la maille EST toute
        # l'épaisseur), linéaires (pas de T⁴ : coefficients effectifs calibrables).
        masque = self.masque_ceramique(t) if callable(self.masque_ceramique) else self.masque_ceramique
        perte_haut = np.where(masque, contact.h_haut * (contact.T_puits - T), 0.0)
        perte_bas = amb.h_bas_2d * (amb.T_amb - T)

        # --- source Joule surfacique -> volumique lumpée + pertes, normalisées par (ρcp)_eff
        P_surf = source_fn(t, T)                     # W/m² (déjà intégrée sur z)
        Q_vol = (P_surf + perte_haut + perte_bas) / self.e_eff   # W/m3
        return ((dT + Q_vol) / rc).ravel()

    # ------------------------------------------------------------------
    def _sparsite_jacobien(self, colonnes_controle=None) -> sparse.csr_matrix:
        """Motif de sparsité du jacobien de ``_rhs`` : stencil à 5 points
        (diagonale + 4 voisins x/y), plus les colonnes pleines de couplage
        source<->T_controle du thermostat (même raisonnement que le 3D,
        cf. ``solveur3d.SolveurThermique3D._sparsite_jacobien``)."""
        g = self.g
        n = g.nx * g.ny
        idx = np.arange(n).reshape(g.nx, g.ny)
        lignes, cols = [], []

        def lier(a, b):
            lignes.append(a.ravel())
            cols.append(b.ravel())

        lier(idx, idx)
        lier(idx[1:], idx[:-1]); lier(idx[:-1], idx[1:])
        lier(idx[:, 1:], idx[:, :-1]); lier(idx[:, :-1], idx[:, 1:])
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
        """Intègre et renvoie ``sol`` de solve_ivp ; sol.y a la forme (nx*ny, nt).

        ``source_fn`` : soit ``f(t) -> P_surf`` (source imposée, W/m², (nx,ny)),
        soit ``f(t, T) -> P_surf`` (source asservie au champ de température
        d'interface, T de forme (nx, ny) — thermostat de consigne).
        ``noeuds_controle`` : nœud(s) de contrôle dont dépend ``source_fn(t, T)``
        (cf. ``solveur3d.SolveurThermique3D.simuler``) ; chaque élément est un
        couple d'indices ``(ix, iy)`` ou un indice aplati déjà en ``ravel()``
        order C ; ``None`` (défaut) pour une source non asservie.
        ``resultat_2d(sol, i)`` redonne le champ (nx, ny) au pas i.
        """
        import inspect

        n_params = len(inspect.signature(source_fn).parameters)
        if n_params == 1:
            f_source = source_fn
            source_fn = lambda t, T: f_source(t)

        g = self.g
        if T_initial is None:
            T0 = np.full(g.nx * g.ny, self.amb.T_amb)
        elif np.isscalar(T_initial):
            T0 = np.full(g.nx * g.ny, float(T_initial))
        else:
            T0 = np.asarray(T_initial).ravel().copy()

        colonnes_controle = None
        if noeuds_controle is not None:
            colonnes_controle = [
                int(np.ravel_multi_index(c, (g.nx, g.ny))) if not np.isscalar(c) else int(c)
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

    def resultat_2d(self, sol, i: int) -> np.ndarray:
        g = self.g
        return sol.y[:, i].reshape(g.nx, g.ny)

    def serie_temporelle(self, sol, x: float, y: float, z: str | float | None = None) -> np.ndarray:
        """Température interpolée BILINÉAIREMENT en (x, y) pour tous les pas
        (cf. ``solveur3d.bracket_lineaire`` — avant 2026-07-21 : nœud le plus
        proche, ``indice_xy``, qui pouvait décaler la lecture de jusqu'à dx/2).

        ``z`` est accepté (et ignoré s'il vaut ``"interface"``) uniquement
        pour partager la même signature d'appel que le 3D depuis
        ``jumeau.procede.Essai.series_tc`` ; ``z="surface"``/``"opposee"``
        n'a PAS de sens dans ce modèle lumpé (une seule maille dans
        l'épaisseur) et lève une erreur explicite plutôt que de renvoyer
        silencieusement l'interface à la place.
        """
        if z is not None and z != "interface":
            raise ValueError(
                f"z={z!r} non représentable par le modèle 2D lumpé (une seule "
                "maille dans l'épaisseur = l'interface) — cf. docstring module."
            )
        g = self.g
        ix, wx = bracket_lineaire(g.x, x)
        iy, wy = bracket_lineaire(g.y, y)
        champ = sol.y.reshape(g.nx, g.ny, -1)
        return ((1.0 - wx) * (1.0 - wy) * champ[ix, iy]
                + wx * (1.0 - wy) * champ[ix + 1, iy]
                + (1.0 - wx) * wy * champ[ix, iy + 1]
                + wx * wy * champ[ix + 1, iy + 1])
