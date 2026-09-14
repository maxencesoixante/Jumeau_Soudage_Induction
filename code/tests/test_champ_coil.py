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



# --- image de bloc MFC fini (bz_plan(..., image_finie), défaut off) ---

def test_bz_plan_image_finie_defaut_identique_infini():
    """5 paramètres à None (défaut) : bit-à-bit identique au chemin
    historique (demi-espace infini) -- non-régression de bz_plan."""
    sommets = sommets_hairpin(0.05, 0.01, 0.005)
    X, Y = np.meshgrid(np.linspace(-0.03, 0.03, 15), np.linspace(-0.03, 0.03, 15), indexing="ij")
    Bz_hist = bz_plan(sommets, 250.0, X, Y, z_plan=0.0, mu_r_cfc=16.0, z_miroir=0.008)
    Bz_none = bz_plan(sommets, 250.0, X, Y, z_plan=0.0, mu_r_cfc=16.0, z_miroir=0.008,
                      centre_x_cfc=None, centre_y_cfc=None, demi_x_cfc=None,
                      demi_y_cfc=None, marge_cfc=None)
    assert np.array_equal(Bz_hist, Bz_none)


def test_bz_plan_image_finie_parametres_partiels_leve():
    """Fournir un sous-ensemble non vide des 5 paramètres -- ValueError
    explicite (pas de flag silencieusement à moitié actif)."""
    sommets = sommets_hairpin(0.05, 0.01, 0.005)
    X, Y = np.meshgrid(np.linspace(-0.02, 0.02, 5), np.linspace(-0.02, 0.02, 5), indexing="ij")
    with pytest.raises(ValueError):
        bz_plan(sommets, 250.0, X, Y, mu_r_cfc=16.0, z_miroir=0.008,
               centre_x_cfc=0.0, demi_x_cfc=0.02)


def test_bz_plan_image_finie_limite_bloc_infini():
    """Limite de cohérence : un bloc dont les demi-extensions tendent vers
    l'infini (grand devant tout le domaine d'observation ET devant la marge)
    doit redonner le champ de l'image de demi-espace infini -- la fenêtre de
    troncature vaut alors 1 partout où le champ est évalué."""
    sommets = sommets_hairpin(0.05, 0.01, 0.005)
    X, Y = np.meshgrid(np.linspace(-0.03, 0.03, 15), np.linspace(-0.02, 0.02, 15), indexing="ij")
    Bz_infini = bz_plan(sommets, 250.0, X, Y, z_plan=0.0, mu_r_cfc=16.0, z_miroir=0.008)
    Bz_grand_bloc = bz_plan(sommets, 250.0, X, Y, z_plan=0.0, mu_r_cfc=16.0, z_miroir=0.008,
                            centre_x_cfc=0.0, centre_y_cfc=0.0,
                            demi_x_cfc=10.0, demi_y_cfc=10.0, marge_cfc=0.012)
    assert np.allclose(Bz_grand_bloc, Bz_infini, rtol=1e-12, atol=1e-15)


def test_bz_plan_image_finie_differe_entre_longueur_mfc():
    """C'EST le résultat structurant recherché : contrairement à l'image de
    demi-espace infini (verrouillée identique quelle que soit la longueur du
    bloc par test_masque_source_mfc_off_est_non_regression, côté procede.py),
    l'image FINIE distingue un MFC 55 mm d'un MFC 31,75 mm -- la longueur du
    bloc entre enfin dans le champ calculé."""
    sommets = sommets_hairpin(0.05, 0.01, 0.005)
    X, Y = np.meshgrid(np.linspace(0.04, 0.08, 21), np.linspace(0.0, 0.04, 21), indexing="ij")
    z_miroir, mu_r = 0.008, 16.0
    centre_x_cfc, centre_y_cfc = 0.06, 0.02
    demi_x_cfc, marge = 0.01575, 0.012           # cfc.largeur/2 (inchangée entre A/B)

    Bz_labo = bz_plan(sommets, 250.0, X, Y, z_plan=0.0, mu_r_cfc=mu_r, z_miroir=z_miroir,
                      centre_x_cfc=centre_x_cfc, centre_y_cfc=centre_y_cfc,
                      demi_x_cfc=demi_x_cfc, demi_y_cfc=0.0275, marge_cfc=marge)   # 55 mm / 2
    Bz_reduit = bz_plan(sommets, 250.0, X, Y, z_plan=0.0, mu_r_cfc=mu_r, z_miroir=z_miroir,
                        centre_x_cfc=centre_x_cfc, centre_y_cfc=centre_y_cfc,
                        demi_x_cfc=demi_x_cfc, demi_y_cfc=0.015875, marge_cfc=marge)  # 31.75 mm / 2
    assert not np.allclose(Bz_labo, Bz_reduit)
    # aux chants (y=0/0.04, loin du centre du bloc réduit) le MFC réduit
    # doit être MOINS intensifié (fenêtre plus étroite) que le MFC labo
    iy_chant = 0
    assert np.abs(Bz_reduit[:, iy_chant]).max() < np.abs(Bz_labo[:, iy_chant]).max()


def test_fenetre_bord_bloc_bornee_et_monotone():
    """La fenêtre de troncature reste dans [0, 1], vaut 1 au centre et
    décroît (au sens large) en s'éloignant, coupure dure si marge<=0."""
    from jumeau.em.champ_coil import _fenetre_bord_bloc
    u = np.linspace(0.0, 0.05, 200)
    w = _fenetre_bord_bloc(u, demi=0.02, marge=0.01)
    assert np.all(w >= -1e-12) and np.all(w <= 1.0 + 1e-12)
    assert w[0] == pytest.approx(1.0)
    assert np.all(np.diff(w) <= 1e-12)          # monotone décroissante
    w_dur = _fenetre_bord_bloc(u, demi=0.02, marge=0.0)
    assert np.array_equal(w_dur, (u <= 0.02).astype(float))



# --- variante 2 : troncature côté SOURCE (mode_troncature_image="source") ---

def test_mode_source_egal_observation_sur_defaut_infini():
    """Les 5 paramètres à None : mode_troncature_image (quel qu'il soit,
    y compris invalide) est ignoré -- chemin historique bit-à-bit."""
    sommets = sommets_hairpin(0.05, 0.01, 0.005)
    X, Y = np.meshgrid(np.linspace(-0.02, 0.02, 9), np.linspace(-0.01, 0.01, 7), indexing="ij")
    Bz_obs = bz_plan(sommets, 250.0, X, Y, mu_r_cfc=16.0, z_miroir=0.008,
                     mode_troncature_image="observation")
    Bz_src = bz_plan(sommets, 250.0, X, Y, mu_r_cfc=16.0, z_miroir=0.008,
                     mode_troncature_image="source")
    Bz_bidon = bz_plan(sommets, 250.0, X, Y, mu_r_cfc=16.0, z_miroir=0.008,
                       mode_troncature_image="n_importe_quoi")
    assert np.array_equal(Bz_obs, Bz_src) and np.array_equal(Bz_obs, Bz_bidon)


def test_mode_source_mode_invalide_leve_si_bloc_fini():
    """Avec les 5 paramètres de bloc fini fournis, un mode invalide lève
    ValueError (seulement dans ce cas -- pas quand n_fournis=0)."""
    sommets = sommets_hairpin(0.05, 0.01, 0.005)
    X, Y = np.meshgrid(np.linspace(-0.02, 0.02, 5), np.linspace(-0.01, 0.01, 5), indexing="ij")
    with pytest.raises(ValueError):
        bz_plan(sommets, 250.0, X, Y, mu_r_cfc=16.0, z_miroir=0.008,
               centre_x_cfc=0.0, centre_y_cfc=0.0, demi_x_cfc=0.016, demi_y_cfc=0.0275,
               marge_cfc=0.012, mode_troncature_image="ni_obs_ni_source")


def test_mode_source_limite_bloc_infini():
    """Limite de cohérence (variante 2) : un bloc dont les demi-extensions
    tendent vers l'infini doit redonner le champ de l'image non tronquée --
    poids=1 sur tout sous-segment, et subdiviser un segment rectiligne à
    courant constant ne change pas son champ (superposition linéaire)."""
    sommets = sommets_hairpin(0.05, 0.01, 0.005)
    X, Y = np.meshgrid(np.linspace(-0.03, 0.03, 15), np.linspace(-0.02, 0.02, 15), indexing="ij")
    Bz_infini = bz_plan(sommets, 250.0, X, Y, mu_r_cfc=16.0, z_miroir=0.008)
    Bz_grand_bloc = bz_plan(sommets, 250.0, X, Y, mu_r_cfc=16.0, z_miroir=0.008,
                            centre_x_cfc=0.0, centre_y_cfc=0.0,
                            demi_x_cfc=10.0, demi_y_cfc=10.0, marge_cfc=0.012,
                            mode_troncature_image="source")
    assert np.allclose(Bz_grand_bloc, Bz_infini, rtol=1e-6, atol=1e-12)


def test_mode_source_differe_entre_longueur_mfc():
    """Même résultat structurant que la variante 1 (côté observation), mais
    obtenu en tronquant la SOURCE : le champ distingue enfin un MFC 55 mm
    d'un MFC 31,75 mm. Géométrie réaliste (orientation='y', jambes 55 mm
    selon y comme le hairpin réel, cf. config/geometrie.yaml:coil) posée AU
    SPOT (centre coïncidant avec le centre du bloc MFC -- sinon la troncature
    source, qui pondère la position du FIL, n'a aucune prise)."""
    sommets = sommets_hairpin(0.055, 0.01235, 0.005, centre_x=0.06, centre_y=0.02,
                              orientation="y")
    X, Y = np.meshgrid(np.linspace(0.04, 0.08, 15), np.linspace(0.0, 0.04, 15), indexing="ij")
    z_miroir, mu_r = 0.008, 16.0
    centre_x_cfc, centre_y_cfc = 0.06, 0.02
    demi_x_cfc, marge = 0.01575, 0.012

    Bz_labo = bz_plan(sommets, 250.0, X, Y, mu_r_cfc=mu_r, z_miroir=z_miroir,
                      centre_x_cfc=centre_x_cfc, centre_y_cfc=centre_y_cfc,
                      demi_x_cfc=demi_x_cfc, demi_y_cfc=0.0275, marge_cfc=marge,
                      mode_troncature_image="source")
    Bz_reduit = bz_plan(sommets, 250.0, X, Y, mu_r_cfc=mu_r, z_miroir=z_miroir,
                        centre_x_cfc=centre_x_cfc, centre_y_cfc=centre_y_cfc,
                        demi_x_cfc=demi_x_cfc, demi_y_cfc=0.015875, marge_cfc=marge,
                        mode_troncature_image="source")
    assert not np.allclose(Bz_labo, Bz_reduit)
    # la portion de jambe au-delà de l'empreinte réduite (55 mm de jambe vs
    # 31,75 mm de bloc) n'est plus réfléchie -> intensification MOINDRE avec
    # le MFC réduit sur cette coupe
    assert np.abs(Bz_reduit).max() < np.abs(Bz_labo).max()


def test_mode_source_et_observation_different_generalement():
    """Les deux variantes (pondération observation vs source) sont deux
    modèles DISTINCTS -- pas de raison qu'ils coïncident exactement pour un
    bloc fini quelconque (ils coïncident seulement à la limite infinie)."""
    sommets = sommets_hairpin(0.055, 0.01235, 0.005, centre_x=0.06, centre_y=0.02,
                              orientation="y")
    X, Y = np.meshgrid(np.linspace(0.04, 0.08, 15), np.linspace(0.0, 0.04, 15), indexing="ij")
    kw = dict(mu_r_cfc=16.0, z_miroir=0.008, centre_x_cfc=0.06, centre_y_cfc=0.02,
             demi_x_cfc=0.01575, demi_y_cfc=0.015875, marge_cfc=0.012)
    Bz_obs = bz_plan(sommets, 250.0, X, Y, mode_troncature_image="observation", **kw)
    Bz_src = bz_plan(sommets, 250.0, X, Y, mode_troncature_image="source", **kw)
    assert not np.allclose(Bz_obs, Bz_src)
