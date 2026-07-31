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


def test_k_plan_xy_isotrope_par_defaut():
    """k_plan_x/k_plan_y non renseignés (None) => k_plan_xy() = (k_plan, k_plan)
    et le champ simulé est BIT-IDENTIQUE à avant l'ajout de l'anisotropie
    (mission thermal-solver-engineer 2026-07-31, flag OFF par défaut)."""
    mat = _materiau(latente=130000.0)
    assert mat.k_plan_x is None and mat.k_plan_y is None
    assert mat.k_plan_xy() == (mat.k_plan, mat.k_plan)

    g = _grille(nx=15, ny=9, nz=5)
    amb = Ambiant(h_convection=5.0, h_bas=0.0, h_bas_2d=10.0)
    contact = ContactCeramique(h_haut=5.0, T_puits=20.0)
    masque = np.zeros((g.nx, g.ny), dtype=bool)
    masque[5:9, 3:6] = True

    X, Y = np.meshgrid(g.x, g.y, indexing="ij")
    P0 = 2.0e5
    Pfield = P0 * np.exp(-((X - 0.06) ** 2 / (2 * 0.01**2) + (Y - 0.02) ** 2 / (2 * 0.008**2)))
    source = lambda t: Pfield
    t_eval = np.array([0.0, 30.0, 60.0])

    s_isotrope = SolveurThermique2D(g, mat, amb, contact, masque_ceramique=masque)
    sol_isotrope = s_isotrope.simuler(source, (0.0, 60.0), t_eval=t_eval)

    # Matériau EXPLICITEMENT isotrope (k_plan_x = k_plan_y = k_plan) : doit
    # donner un résultat identique au chemin par défaut (None, None).
    mat_explicite = _materiau(latente=130000.0)
    mat_explicite.k_plan_x = mat.k_plan
    mat_explicite.k_plan_y = mat.k_plan
    s_explicite = SolveurThermique2D(g, mat_explicite, amb, contact, masque_ceramique=masque)
    sol_explicite = s_explicite.simuler(source, (0.0, 60.0), t_eval=t_eval)

    assert np.array_equal(sol_isotrope.y, sol_explicite.y)


def test_k_plan_xy_anisotrope_modifie_le_champ():
    """kx != ky doit produire un champ différent de l'isotrope, avec un
    étalement plus rapide dans la direction de plus forte conductivité
    (vérifie que le stencil utilise bien kx en x et ky en y séparément,
    pas une moyenne scalaire)."""
    # Domaine CARRÉ (Lx = Ly) pour ce test : isole l'effet kx/ky de toute
    # confusion avec l'asymétrie géométrique du domaine réel (0.12 x 0.04 m).
    from jumeau.thermique.solveur3d import Grille3D
    g = Grille3D(0.04, 0.04, 0.00682, 0.00336, nx=15, ny=15, nz=5)
    amb = Ambiant(h_convection=0.0, h_bas=0.0, h_bas_2d=0.0)
    contact = ContactCeramique(h_haut=0.0, h_contact=0.0)

    X, Y = np.meshgrid(g.x, g.y, indexing="ij")
    P0 = 3.0e5
    Pfield = P0 * np.exp(-((X - 0.02) ** 2 / (2 * 0.004**2) + (Y - 0.02) ** 2 / (2 * 0.004**2)))
    source = lambda t: Pfield
    t_eval = np.array([0.0, 15.0])

    mat_iso = _materiau()
    s_iso = SolveurThermique2D(g, mat_iso, amb, contact)
    T_iso = s_iso.simuler(source, (0.0, 15.0), t_eval=t_eval).y[:, -1].reshape(g.nx, g.ny)

    mat_aniso = _materiau()
    mat_aniso.k_plan_x = 9.0   # forte conduction en x (longueur)
    mat_aniso.k_plan_y = 1.0   # faible conduction en y (largeur) -> pic plus contraste en y
    s_aniso = SolveurThermique2D(g, mat_aniso, amb, contact)
    T_aniso = s_aniso.simuler(source, (0.0, 15.0), t_eval=t_eval).y[:, -1].reshape(g.nx, g.ny)

    assert not np.allclose(T_iso, T_aniso)

    ix0 = np.argmin(np.abs(g.x - 0.02))
    iy0 = np.argmin(np.abs(g.y - 0.02))
    # Etalement en x : forte kx (aniso, 9) doit étaler davantage qu'isotrope
    # (k_plan=3) -> température au bord x plus haute (moins piégée sous le
    # pic) que l'isotrope.
    assert T_aniso[0, iy0] > T_iso[0, iy0]

    # Asymétrie x/y INTERNE au champ anisotrope (indépendant de l'isotrope) :
    # kx=9 (fort) doit aplatir le gradient en x nettement plus que ky=1
    # (faible) ne le fait en y -> la chute de température center->bord doit
    # être PLUS FAIBLE en x qu'en y (démontre que le stencil applique bien
    # kx et ky séparément aux deux directions, pas une moyenne scalaire).
    chute_x = T_aniso[ix0, iy0] - T_aniso[0, iy0]
    chute_y = T_aniso[ix0, iy0] - T_aniso[ix0, 0]
    assert chute_x < chute_y
