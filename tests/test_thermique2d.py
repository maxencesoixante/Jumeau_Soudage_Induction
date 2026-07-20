"""Vérifications du solveur thermique 2D (modèle lumpé dans l'épaisseur).

Cf. jumeau/thermique/solveur2d.py pour la formulation. Les tests d'énergie
ici sont l'équivalent 2D de ``test_thermique.py::test_conservation_energie_adiabatique``
(condition adiabatique : h_haut=h_bas=0, pas de convection/rayonnement) —
c'est l'essai de non-régression demandé par AGENTS.md (« conserve l'énergie —
c'est le test d'acceptation »).
"""

import numpy as np
import pytest
from scipy.integrate import quad

from jumeau.materiaux import Ambiant, ContactCeramique, Materiau
from jumeau.thermique.solveur2d import SolveurThermique2D
from jumeau.thermique.solveur3d import Grille3D


def _materiau(latente=0.0):
    return Materiau(
        densite=1600.0, cp_base=1200.0, T_fusion=337.0, delta_T_fusion=15.0,
        chaleur_latente=latente, k_plan=3.0, k_z=0.64, emissivite=0.0,
    )


def _grille(nx=9, ny=5, nz=3):
    # nz/epaisseur_interface n'affectent le 2D que via g.epaisseur (e_eff) ;
    # on réutilise Grille3D tel quel (cf. docstring solveur2d.py).
    return Grille3D(0.12, 0.04, 0.00682, 0.00336, nx=nx, ny=ny, nz=nz)


def test_equilibre_sans_source_2d():
    """Sans source et à T = T_amb partout, rien ne bouge (2D)."""
    g = _grille()
    s = SolveurThermique2D(g, _materiau(), Ambiant(h_bas_2d=0.0),
                           ContactCeramique(h_haut=0.0, T_puits=20.0))
    source = lambda t: np.zeros((g.nx, g.ny))
    sol = s.simuler(source, (0.0, 50.0), t_eval=np.array([0.0, 50.0]))
    assert np.allclose(sol.y[:, -1], 20.0, atol=1e-6)


def test_conservation_energie_adiabatique_2d_source_uniforme():
    """Source surfacique UNIFORME, système isolé (h_haut=h_bas_2d=0, pas de
    convection/rayonnement aux chants) : ΔT = P_surf·durée / ((ρcp)_eff·e_eff)
    exactement, partout (pas de gradient => la conduction ne redistribue rien) —
    reproduit à l'identique l'esprit du test 3D correspondant."""
    mat = _materiau()
    amb = Ambiant(h_convection=0.0, h_bas=0.0, h_bas_2d=0.0)
    g = _grille()
    s = SolveurThermique2D(g, mat, amb, ContactCeramique(h_contact=0.0, h_haut=0.0))
    P0 = 2.0e4                                        # W/m2 uniforme
    source = lambda t: np.full((g.nx, g.ny), P0)
    duree = 60.0
    sol = s.simuler(source, (0.0, duree), t_eval=np.array([0.0, duree]), rtol=1e-9, atol=1e-8)
    dT_attendu = P0 * duree / (mat.densite * mat.cp_base * g.epaisseur)
    assert np.allclose(sol.y[:, -1] - 20.0, dT_attendu, rtol=1e-6)


def test_conservation_energie_adiabatique_2d_source_localisee():
    """Source surfacique LOCALISÉE (gaussienne, traverse le pic de fusion),
    toujours adiabatique : l'énergie totale stockée (intégrale d'enthalpie,
    cp apparent y compris le pic de fusion) doit égaler l'énergie déposée à
    moins de 1 % — en pondérant les nœuds de bord par leur DEMI-cellule de
    contrôle (préfacteur 2/d, cf. solveur3d.py — c'est la même convention
    que le 3D, PAS dx·dy uniforme partout, sous peine d'un faux écart de
    quelques % purement dû au comptage, cf. rapport de vérification)."""
    mat = _materiau(latente=130000.0)
    amb = Ambiant(h_convection=0.0, h_bas=0.0, h_bas_2d=0.0)
    g = _grille(nx=25, ny=11, nz=5)
    s = SolveurThermique2D(g, mat, amb, ContactCeramique(h_contact=0.0, h_haut=0.0))

    X, Y = np.meshgrid(g.x, g.y, indexing="ij")
    P0 = 3.0e5
    Pfield = P0 * np.exp(-((X - 0.06) ** 2 / (2 * 0.01**2) + (Y - 0.02) ** 2 / (2 * 0.008**2)))
    source = lambda t: Pfield
    duree = 90.0
    sol = s.simuler(source, (0.0, duree), t_eval=np.array([0.0, duree]),
                    rtol=1e-10, atol=1e-9, max_step=2.0)

    T0 = 20.0
    Tf = sol.y[:, -1].reshape(g.nx, g.ny)

    def enthalpie(Tn):
        return quad(lambda TT: mat.cp_apparent(TT), T0, Tn, limit=200)[0]

    Hf = np.vectorize(enthalpie)(Tf)

    wx = np.full(g.nx, g.dx); wx[0] = g.dx / 2.0; wx[-1] = g.dx / 2.0
    wy = np.full(g.ny, g.dy); wy[0] = g.dy / 2.0; wy[-1] = g.dy / 2.0
    W = np.outer(wx, wy)

    energie_stockee = np.sum(mat.densite * Hf * g.epaisseur * W)
    energie_deposee = np.sum(Pfield * W) * duree

    assert Tf.max() > mat.T_fusion            # le pic de fusion est bien traversé
    assert energie_stockee == pytest.approx(energie_deposee, rel=1e-4)


def test_masque_h_haut_refroidit():
    """Le puits effectif h_haut (masque actif) doit tirer la température sous
    l'empreinte vers T_puits — équivalent 2D de
    ``test_thermique.py::test_puits_ceramique_refroidit``."""
    mat = _materiau()
    g = _grille()
    masque = np.zeros((g.nx, g.ny), dtype=bool)
    masque[3:6, 1:4] = True
    s = SolveurThermique2D(g, mat, Ambiant(h_bas_2d=0.0),
                           ContactCeramique(h_haut=200.0, T_puits=20.0),
                           masque_ceramique=masque)
    T0 = np.full(g.nx * g.ny, 200.0)
    source = lambda t: np.zeros((g.nx, g.ny))
    sol = s.simuler(source, (0.0, 30.0), t_eval=np.array([0.0, 30.0]), T_initial=T0)
    Tf = sol.y[:, -1].reshape(g.nx, g.ny)
    assert Tf[4, 2] < Tf[0, 0] - 5.0


def test_serie_temporelle_rejette_z_non_interface():
    """z='surface'/'opposee' n'a pas de sens dans le modèle lumpé (une seule
    maille dans l'épaisseur) : erreur explicite plutôt qu'un résultat
    silencieusement faux."""
    g = _grille()
    s = SolveurThermique2D(g, _materiau(), Ambiant(), ContactCeramique())
    source = lambda t: np.zeros((g.nx, g.ny))
    sol = s.simuler(source, (0.0, 5.0), t_eval=np.array([0.0, 5.0]))
    s.serie_temporelle(sol, 0.06, 0.02, "interface")   # OK
    s.serie_temporelle(sol, 0.06, 0.02)                # OK (z omis)
    with pytest.raises(ValueError):
        s.serie_temporelle(sol, 0.06, 0.02, "surface")
