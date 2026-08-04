"""Tests d'intégration : source Joule assemblée + orchestration d'un essai."""

from pathlib import Path

import numpy as np
import pytest

from jumeau.geometrie import construire_couches, construire_grille, masque_empreinte_cfc
from jumeau.materiaux import Config
from jumeau.procede import Essai
from jumeau.em.source_joule import source_spot

RACINE = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def cfg():
    return Config.charger(RACINE / "config")


def test_source_localisee_et_positive(cfg):
    g = construire_grille(cfg, nx=25, ny=9, nz=9)
    couches = construire_couches(cfg)
    centre = 0.045875
    Q = source_spot(g, cfg, couches, courant=250.0, centre_x=centre)
    assert Q.shape == (25, 9, 9)
    assert np.all(Q >= 0.0) and Q.max() > 0.0
    # la source est concentrée autour du spot : max au voisinage de centre_x
    ix_max = np.unravel_index(np.argmax(Q), Q.shape)[0]
    assert abs(g.x[ix_max] - centre) < 0.02
    # le twill (interface) domine le dépôt : le nœud interface porte plus de
    # puissance que la face opposée
    profil_z = Q.sum(axis=(0, 1))
    assert profil_z[g.iz_interface] > profil_z[-1]


def test_source_croit_avec_courant(cfg):
    g = construire_grille(cfg, nx=15, ny=7, nz=7)
    couches = construire_couches(cfg)
    Q1 = source_spot(g, cfg, couches, courant=200.0, centre_x=0.06)
    Q2 = source_spot(g, cfg, couches, courant=250.0, centre_x=0.06)
    # Q ∝ I² (linéarité de Biot-Savart + quadratique de la dissipation)
    assert np.allclose(Q2, Q1 * (250.0 / 200.0) ** 2, rtol=1e-9)


def test_decalage_x_zero_est_identite(cfg):
    """decalage_x=0.0 (explicite ou par défaut) doit reproduire EXACTEMENT
    la source d'avant l'introduction du paramètre : non-régression bit-à-bit."""
    g = construire_grille(cfg, nx=31, ny=11, nz=13)
    couches = construire_couches(cfg)
    Q_sans_arg = source_spot(g, cfg, couches, courant=250.0, centre_x=0.06)
    Q_decalage_nul = source_spot(g, cfg, couches, courant=250.0, centre_x=0.06,
                                  decalage_x=0.0)
    assert np.array_equal(Q_sans_arg, Q_decalage_nul)


def test_decalage_x_deplace_le_centre_bobine(cfg):
    """decalage_x translate le centre effectif de la bobine (donc le profil de
    Q en x) sans modifier la puissance totale déposée (même bobine, même I)."""
    g = construire_grille(cfg, nx=31, ny=11, nz=13)
    couches = construire_couches(cfg)
    centre = 0.06
    Q0 = source_spot(g, cfg, couches, courant=250.0, centre_x=centre)
    Q_decale = source_spot(g, cfg, couches, courant=250.0, centre_x=centre,
                            decalage_x=0.010)
    assert not np.array_equal(Q0, Q_decale)
    # puissance totale quasi conservée (translation de la bobine ; la légère
    # différence vient de la BC psi=0 au bord de plaque, PAS translation-
    # invariante — la bobine décalée est légèrement plus proche du bord x=L)
    assert np.isclose(Q0.sum(), Q_decale.sum(), rtol=1e-2)
    # décaler la bobine de +10 mm équivaut EXACTEMENT à évaluer la source non
    # décalée à centre_x + 10 mm (même géométrie relative bobine<->grille) :
    # c'est cette identité, pas la conservation approximative ci-dessus, qui
    # définit le comportement attendu de decalage_x
    Q_ref = source_spot(g, cfg, couches, courant=250.0, centre_x=centre + 0.010)
    assert np.allclose(Q_decale, Q_ref, rtol=1e-9)


def test_masque_cfc(cfg):
    g = construire_grille(cfg, nx=49, ny=17, nz=7)
    m = masque_empreinte_cfc(g, cfg, centre_x=0.015875)
    assert m.dtype == bool and m.any() and not m.all()
    # l'empreinte contient le centre du spot
    ix, iy = g.indice_xy(0.015875, g.largeur / 2)
    assert m[ix, iy]


def test_essai_chauffe_bout_en_bout(cfg):
    """Simulation courte de l'essai de chauffe sur grille grossière : sanité."""
    chemin = RACINE / "config" / "essais" / "chauffe_250A_3TC.yaml"
    essai = Essai(cfg, chemin, nx=21, ny=9, nz=9, racine=RACINE)
    # écourter pour le test
    essai.spec["duree_totale"] = 60.0
    solveur, sol = essai.simuler(dt_sortie=2.0)
    series = essai.series_tc(solveur, sol)
    assert set(series) == {"TC1", "TC2", "TC3"}
    # ça chauffe, et l'interface (twill) chauffe plus que la face opposée
    assert series["TC2"].max() > 30.0
    assert series["TC2"].max() > series["TC3"].max()
    # aucune température aberrante
    assert np.all(np.isfinite(sol.y))
    assert sol.y.max() < 2000.0


def test_essai_decalage_x_defaut_et_surcharge(cfg):
    """decalage_x : valeur YAML (0.0) par défaut, surchargeable par programme
    comme facteur_couplage ; ne déplace pas le masque céramique/CFC."""
    chemin = RACINE / "config" / "essais" / "chauffe_250A_3TC.yaml"
    essai_defaut = Essai(cfg, chemin, nx=21, ny=9, nz=9, racine=RACINE)
    assert essai_defaut.decalage_x == 0.0

    essai_decale = Essai(cfg, chemin, nx=21, ny=9, nz=9, decalage_x=0.010, racine=RACINE)
    assert essai_decale.decalage_x == 0.010
    # la source change avec le décalage bobine...
    assert not np.array_equal(essai_defaut._Q_spots[0], essai_decale._Q_spots[0])
    # ...mais le masque céramique/CFC (posé sur le spot, pas sur la bobine) ne bouge pas
    assert np.array_equal(essai_defaut._masques[0], essai_decale._masques[0])


def test_essai_decalage_x_augmente_taux_chauffe_tc2(cfg):
    """Reproduit la découverte du 2026-07-18 : TC2 est au centre de symétrie
    du hairpin (zéro de dissipation exact) pour l'essai chauffe_250A_3TC ; un
    décalage bobine de +10 mm sort du zéro et accélère la chauffe locale
    (grille 31x11x13, facteur_couplage=3.85).

    VALEURS RECALÉES 2026-07-29 (twill_suscepteur.epaisseur 0.28 -> 0.20 mm,
    mesure user ; la source Joule concentrée sur une nappe plus fine change la
    répartition de puissance par couche et donc les deux taux, cf. consolidation
    2026-07-29) : taux_sim TC2 = 4.64 °C/s à decalage_x=0, 7.61 à +10 mm (ratio
    ~1.64, contre 2.6 sous l'ancien twill 0.28). Le sens de l'effet est
    invariant au twill : le décalage sort TC2 du zéro de symétrie du hairpin
    et AUGMENTE le taux dans les deux régimes ; c'est cette intention
    (monotonie), pas les valeurs elles-mêmes, que le test doit garantir.
    decalage_x est de toute façon figé à 0 dans le θ* de référence."""
    from jumeau.validation.confrontation import taux_de_chauffe

    chemin = RACINE / "config" / "essais" / "chauffe_250A_3TC.yaml"
    essai0 = Essai(cfg, chemin, nx=31, ny=11, nz=13, facteur_couplage=3.85, racine=RACINE)
    essai_decale = Essai(cfg, chemin, nx=31, ny=11, nz=13, facteur_couplage=3.85,
                         decalage_x=0.010, racine=RACINE)
    # taux_de_chauffe ne regarde que la montée (croisement de T_ref=75°C,
    # atteint bien avant 30 s) : on écourte duree_totale pour le temps de
    # test, dt_sortie=1.0 (défaut, identique à scripts/valider.py) préservé
    essai0.spec["duree_totale"] = 60.0
    essai_decale.spec["duree_totale"] = 60.0

    solveur0, sol0 = essai0.simuler(dt_sortie=1.0)
    solveur_d, sol_d = essai_decale.simuler(dt_sortie=1.0)
    taux0 = taux_de_chauffe(sol0.t, essai0.series_tc(solveur0, sol0)["TC2"])
    taux_d = taux_de_chauffe(sol_d.t, essai_decale.series_tc(solveur_d, sol_d)["TC2"])

    assert taux0 == pytest.approx(4.64, abs=0.3)
    assert taux_d == pytest.approx(7.61, abs=0.4)
    assert taux_d > taux0          # le décalage augmente le taux (invariant au twill, cf. docstring)


# --- loi thermostat 'capteurs' (défaut off, cf. Essai.thermostat_capteurs) ---

def _essai_b2(cfg, **kw):
    chemin = RACINE / "config" / "essais" / "serieB_B-2.yaml"
    return Essai(cfg, chemin, nx=25, ny=11, nz=9, racine=RACINE, **kw)


def test_thermostat_capteurs_off_est_non_regression(cfg):
    """Flag off (défaut) : nœuds de contrôle et T_ctrl strictement inchangés."""
    e_def = _essai_b2(cfg)
    e_off = _essai_b2(cfg, thermostat_capteurs=False)
    assert e_def._noeuds_controle == e_off._noeuds_controle
    assert e_def._noeuds_controle_2d == e_off._noeuds_controle_2d
    assert e_def._brackets_capteurs == []          # non construit quand off
    rng = np.random.default_rng(0)
    T = rng.random((e_def.grille.nx, e_def.grille.ny)) * 400.0
    spot = e_def.spots[0]
    assert e_def._T_ctrl(T, spot, deux_d=True) == e_off._T_ctrl(T, spot, deux_d=True)


def test_thermostat_capteurs_on_controle_sur_le_max_des_tc(cfg):
    """Flag on : T_ctrl = max de T aux positions TC d'interface (≠ loi section)."""
    from jumeau.thermique.solveur3d import bracket_lineaire
    e_on = _essai_b2(cfg, thermostat_capteurs=True)
    e_off = _essai_b2(cfg)
    g = e_on.grille
    assert e_on._brackets_capteurs                 # construit quand on
    # nœuds de contrôle = brackets des TC, différents de la loi section
    assert e_on._noeuds_controle_2d != e_off._noeuds_controle_2d

    # champ synthétique : bosse localisée exactement sur un nœud proche de TC3
    # (x=60mm, y=0). T_ctrl 'capteurs' doit valoir le max bilinéaire aux TC.
    rng = np.random.default_rng(1)
    T = rng.random((g.nx, g.ny)) * 50.0
    positions = e_on._positions_capteurs_interface()
    assert positions                                # B-2 a des TC d'interface
    attendu = -np.inf
    for x, y in positions:
        ix, wx = bracket_lineaire(g.x, x)
        iy, wy = bracket_lineaire(g.y, y)
        v = ((1 - wx) * (1 - wy) * T[ix, iy] + wx * (1 - wy) * T[ix + 1, iy]
             + (1 - wx) * wy * T[ix, iy + 1] + wx * wy * T[ix + 1, iy + 1])
        attendu = max(attendu, v)
    spot = e_on.spots[0]
    assert e_on._T_ctrl(T, spot, deux_d=True) == pytest.approx(attendu)
    # et c'est bien un MAX -> >= la valeur de n'importe quel TC pris seul
    assert e_on._T_ctrl(T, spot, deux_d=True) >= T.min()


# --- lissage de source (délocalisation twill, cf. source_joule._lisser_source) ---

def test_lissage_source_off_est_identite(cfg):
    """sigma=0 (défaut) : source strictement inchangée (non-régression)."""
    g = construire_grille(cfg, nx=25, ny=11, nz=9)
    c = construire_couches(cfg)
    Q0 = source_spot(g, cfg, c, 250.0, 0.06)
    Q0b = source_spot(g, cfg, c, 250.0, 0.06, lissage_sigma_mm=0.0)
    assert np.array_equal(Q0, Q0b)


def test_lissage_source_conserve_puissance_et_remplit_centre(cfg):
    """sigma>0 : puissance totale conservée, œil de boucle rempli, pic abaissé."""
    g = construire_grille(cfg, nx=61, ny=21, nz=13)
    c = construire_couches(cfg)
    Q0 = source_spot(g, cfg, c, 250.0, 0.06)
    Q6 = source_spot(g, cfg, c, 250.0, 0.06, lissage_sigma_mm=6.0)
    assert Q6.sum() == pytest.approx(Q0.sum(), rel=1e-6)      # puissance conservée
    ix = int(np.argmin(np.abs(g.x - 0.06))); iy = g.ny // 2
    assert Q0[ix, iy, :].sum() < 1.0                           # œil de boucle ~0
    assert Q6[ix, iy, :].sum() > 100.0 * Q0[ix, iy, :].sum()   # rempli
    assert Q6.max() < Q0.max()                                 # pic abaissé


# --- adoucissement du bord (psi=0 repoussé, cf. source_joule.lambda_bord_mm) ---

def test_lambda_bord_off_est_identite(cfg):
    """lambda_bord_mm=0 (défaut) : source strictement inchangée (non-régression)."""
    g = construire_grille(cfg, nx=25, ny=11, nz=9)
    c = construire_couches(cfg)
    Q0 = source_spot(g, cfg, c, 250.0, 0.06)
    Q0b = source_spot(g, cfg, c, 250.0, 0.06, lambda_bord_mm=0.0)
    assert np.array_equal(Q0, Q0b)


def test_lambda_bord_adoucit_le_contraste_chant_centre(cfg):
    """lambda_bord_mm>0 : le contraste bord/centre du profil en y (largeur)
    DIMINUE avec lambda_bord_mm croissant -- adoucissement du "M" (cf.
    docstring module source_joule.py, section "Adoucissement du bord"). Le
    bord (y=0, ψ=0 repoussé) est un nœud EXACT de la grille -> comparaison
    directe sans interpolation."""
    g = construire_grille(cfg, nx=31, ny=21, nz=9)
    c = construire_couches(cfg)
    iy_centre = g.ny // 2
    contrastes = []
    for lam in (0.0, 2.0, 4.0, 6.0, 8.0):
        Q = source_spot(g, cfg, c, 200.0, 0.06, lambda_bord_mm=lam)
        prof_y = Q.sum(axis=(0, 2))
        contrastes.append(prof_y[0] / prof_y[iy_centre])
    # strictement décroissant
    assert all(c1 > c2 for c1, c2 in zip(contrastes, contrastes[1:])), contrastes
    # symétrie y -> centre_y = largeur/2 conservée par construction (le pad
    # est symétrique de part et d'autre)
    Q4 = source_spot(g, cfg, c, 200.0, 0.06, lambda_bord_mm=4.0)
    prof_y4 = Q4.sum(axis=(0, 2))
    assert np.allclose(prof_y4, prof_y4[::-1], rtol=1e-9)


def test_lambda_bord_incompatible_champ_reaction(cfg):
    """lambda_bord_mm>0 + champ_reaction=True : combinaison non explorée,
    ValueError explicite (cf. docstring module)."""
    g = construire_grille(cfg, nx=15, ny=9, nz=7)
    c = construire_couches(cfg)
    with pytest.raises(ValueError):
        source_spot(g, cfg, c, 200.0, 0.06, lambda_bord_mm=4.0, champ_reaction=True)


def test_essai_lambda_bord_defaut_et_surcharge(cfg):
    """Essai(..., lambda_bord_mm=...) : défaut 0.0 identique au chemin
    historique, surcharge propagée à la source EM (non-régression du même
    style que decalage_x/source_sigma_mm)."""
    chemin = RACINE / "config" / "essais" / "exp7_200A.yaml"
    e_off = Essai(cfg, chemin, nx=15, ny=9, nz=7, racine=RACINE)
    e_off2 = Essai(cfg, chemin, nx=15, ny=9, nz=7, racine=RACINE, lambda_bord_mm=0.0)
    assert np.array_equal(e_off._Q_spots[0], e_off2._Q_spots[0])
    e_on = Essai(cfg, chemin, nx=15, ny=9, nz=7, racine=RACINE, lambda_bord_mm=4.0)
    assert not np.array_equal(e_off._Q_spots[0], e_on._Q_spots[0])
    assert e_on._Q_spots[0].sum() > 0.0


# --- masque de source à l'empreinte MFC (défaut off, cf. Essai.masque_source_mfc) ---

def test_masque_source_mfc_off_est_non_regression(cfg):
    """Flag off (défaut, explicite ou implicite) : source strictement
    inchangée, bit-à-bit -- non-régression."""
    chemin = RACINE / "config" / "essais" / "exp7_200A.yaml"
    e_defaut = Essai(cfg, chemin, nx=25, ny=17, nz=9, racine=RACINE)
    e_off = Essai(cfg, chemin, nx=25, ny=17, nz=9, racine=RACINE, masque_source_mfc=False)
    assert e_defaut.masque_source_mfc is False
    assert np.array_equal(e_defaut._Q_spots[0], e_off._Q_spots[0])
    assert np.array_equal(e_defaut._P_spots_2d[0], e_off._P_spots_2d[0])


def test_masque_source_mfc_on_confine_hors_empreinte(cfg):
    """Flag on (MFC labo, cfc.largeur=31.5 mm le long de x) : la source est
    EXACTEMENT nulle hors de l'empreinte en x (au-delà de centre_x ±
    largeur/2), et là où elle est non nulle elle vaut EXACTEMENT Q_off*masque
    (masque dur, pas de redistribution) -- puissance totale RÉDUITE (pas
    conservée, cf. docstring Essai.masque_source_mfc : simple troncature, pas
    une concentration par conservation)."""
    chemin = RACINE / "config" / "essais" / "exp7_200A.yaml"
    e_off = Essai(cfg, chemin, nx=61, ny=21, nz=9, racine=RACINE)
    e_on = Essai(cfg, chemin, nx=61, ny=21, nz=9, racine=RACINE, masque_source_mfc=True)
    Q_off, Q_on = e_off._Q_spots[0], e_on._Q_spots[0]
    masque = e_on._masques[0]
    assert np.array_equal(Q_on, Q_off * masque[:, :, None])
    assert np.all(Q_on[~masque] == 0.0)
    assert Q_on.sum() < Q_off.sum()
    # empreinte MFC labo (55 mm) déborde largement la largeur 40 mm de
    # l'échantillon -> masque toujours vrai en y ; seule la troncature en x
    # (31.5 mm, plus étroite que le halo de diffusion EM) réduit la puissance
    ratio = Q_on.sum() / Q_off.sum()
    assert 0.80 < ratio < 0.95


def test_masque_source_mfc_reduit_confine_les_chants(cfg):
    """MFC réduit (cfc.longueur 0.055 -> 0.03175 m, override EN MÉMOIRE,
    PAS en config -- cf. brief) : l'empreinte ne couvre plus toute la largeur
    de l'échantillon -> la source est nulle EXACTEMENT aux chants (y=0 et
    y=largeur), contrairement au MFC labo (test précédent, où l'empreinte
    déborde la largeur donc y=0/largeur restent non masqués)."""
    import copy
    cfg_reduit = copy.deepcopy(cfg)
    cfg_reduit.geometrie["cfc"]["longueur"] = 0.03175

    chemin = RACINE / "config" / "essais" / "exp7_200A.yaml"
    e_labo_on = Essai(cfg, chemin, nx=25, ny=21, nz=9, racine=RACINE, masque_source_mfc=True)
    e_reduit_on = Essai(cfg_reduit, chemin, nx=25, ny=21, nz=9, racine=RACINE,
                        masque_source_mfc=True)

    Q_labo = e_labo_on._Q_spots[0]
    Q_reduit = e_reduit_on._Q_spots[0]
    # MFC labo : empreinte déborde -> chants non masqués (source non nulle)
    assert Q_labo[:, 0, :].sum() > 0.0
    assert Q_labo[:, -1, :].sum() > 0.0
    # MFC réduit : empreinte plus courte que la largeur -> chants masqués (nuls)
    assert Q_reduit[:, 0, :].sum() == 0.0
    assert Q_reduit[:, -1, :].sum() == 0.0
    # la puissance totale confinée par le MFC réduit est nettement plus petite
    assert Q_reduit.sum() < 0.6 * Q_labo.sum()
    # cfg (fixture module-scope) non muté par l'override en mémoire
    assert cfg.geometrie["cfc"]["longueur"] == 0.055


# --- bilan de conservation d'énergie (θ* de référence, essai réaliste) ---

def test_bilan_energie_exp7_200A_theta_reference(cfg):
    """Bilan énergie/puissance (AGENTS.md §Conservation checks) au θ* de
    référence 2D canonique (facteur_couplage=6.0123 -- argument runtime, PAS
    en config, cf. consolidation 2026-07-29 ; h_haut/h_bas_2d/h_bord_x0 sont
    les défauts de config/materiaux.yaml depuis cette même consolidation),
    twill 0.20 mm, sur l'essai exp7_200A (représentatif, 5 TC bord->centre,
    AVEC céramique) : énergie stockée (intégrale d'enthalpie, cp apparent) =
    énergie déposée (source Joule) - pertes cumulées (h_haut masque MFC +
    h_bas_2d + convection/rayonnement/h_bord_x0 aux 4 chants réels), TOUS
    calculés en post-traitement à partir de sol (pas depuis l'intérieur du
    RHS) -- vérifie donc aussi que solve_ivp (BDF) ne laisse pas fuir
    d'énergie au-delà de la tolérance demandée.

    Durée écourtée à 40 s (chauffe 18 s + refroidissement court, au lieu des
    115 s mesurés) et grille allégée (25x9x9) pour rester un test rapide
    (<10 s) ; ``dt_sortie=0.1`` (au lieu du défaut 1.0 s de scripts/valider.py)
    est nécessaire pour ne pas biaiser la quadrature trapézoïdale en temps
    sur le créneau raide de coupure de source à t=18 s (vérifié séparément :
    résidu 5.1 % à dt_sortie=1.0 vs 0.6 % à 0.1 sur la grille de production
    61x21x15 -- c'est un artefact de quadrature documenté, pas une fuite du
    solveur, cf. rapport de vérification 2026-07-29). Tolérance 1 % ici
    (obtenu : ~0.2 % sur cette grille allégée) -- généreuse pour absorber le
    résidu de quadrature restant, pas un nombre à sur-interpréter comme
    "convergé" (grille volontairement grossière, cf. AGENTS.md)."""
    from scipy.integrate import quad

    from jumeau.thermique.solveur3d import KELVIN

    FACTEUR_COUPLAGE = 6.0123     # θ* de référence 2D (runtime, pas en config)

    chemin = RACINE / "config" / "essais" / "exp7_200A.yaml"
    e = Essai(cfg, chemin, nx=25, ny=9, nz=9, facteur_couplage=FACTEUR_COUPLAGE, racine=RACINE)
    e.spec["duree_totale"] = 40.0
    solveur, sol = e.simuler(dt_sortie=0.1, modele="2D")

    g, mat, amb, contact = solveur.g, solveur.mat, solveur.amb, solveur.contact
    e_eff = solveur.e_eff

    wx = np.full(g.nx, g.dx); wx[0] = g.dx / 2.0; wx[-1] = g.dx / 2.0
    wy = np.full(g.ny, g.dy); wy[0] = g.dy / 2.0; wy[-1] = g.dy / 2.0
    W = np.outer(wx, wy)

    nt = sol.t.size
    P_dep = np.zeros(nt); P_haut = np.zeros(nt); P_bas = np.zeros(nt); P_chants = np.zeros(nt)
    Ta_K = amb.T_amb + KELVIN

    for k in range(nt):
        t = sol.t[k]
        T = sol.y[:, k].reshape(g.nx, g.ny)
        P_dep[k] = np.sum(e.source_fn_2d(t, T) * W)
        masque = solveur.masque_ceramique(t) if callable(solveur.masque_ceramique) else solveur.masque_ceramique
        P_haut[k] = np.sum(np.where(masque, contact.h_haut * (contact.T_puits - T), 0.0) * W)
        P_bas[k] = np.sum(amb.h_bas_2d * (amb.T_amb - T) * W)
        # chants réels (x=0, x=L, y=0, y=W) : flux physique [W/m2] * longueur
        # d'arête pondérée trapèze * e_eff (PAS le préfacteur 2/d volumique du
        # RHS -- ici on veut le flux physique direct, indépendant du maillage).
        flux_x0 = (amb.h_convection * (amb.T_amb - T[0, :])
                   + mat.emissivite * amb.stefan_boltzmann * (Ta_K**4 - (T[0, :] + KELVIN)**4)
                   + amb.h_bord_x0 * (amb.T_amb - T[0, :]))
        flux_xL = (amb.h_convection * (amb.T_amb - T[-1, :])
                   + mat.emissivite * amb.stefan_boltzmann * (Ta_K**4 - (T[-1, :] + KELVIN)**4))
        flux_y0 = (amb.h_convection * (amb.T_amb - T[:, 0])
                   + mat.emissivite * amb.stefan_boltzmann * (Ta_K**4 - (T[:, 0] + KELVIN)**4))
        flux_yW = (amb.h_convection * (amb.T_amb - T[:, -1])
                   + mat.emissivite * amb.stefan_boltzmann * (Ta_K**4 - (T[:, -1] + KELVIN)**4))
        P_chants[k] = (np.sum(flux_x0 * wy) + np.sum(flux_xL * wy)
                       + np.sum(flux_y0 * wx) + np.sum(flux_yW * wx)) * e_eff

    energie_apportee = np.trapezoid(P_dep + P_haut + P_bas + P_chants, sol.t)

    T0 = amb.T_amb
    Tf = sol.y[:, -1].reshape(g.nx, g.ny)
    enthalpie = np.vectorize(lambda Tn: quad(lambda TT: mat.cp_apparent(TT), T0, Tn, limit=200)[0])
    energie_stockee = np.sum(mat.densite * enthalpie(Tf) * e_eff * W)

    assert energie_apportee > 0.0                       # sanity : la source a bien chauffé
    residu_relatif = abs(energie_stockee - energie_apportee) / energie_apportee
    assert residu_relatif < 0.01
