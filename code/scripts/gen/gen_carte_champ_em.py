"""Cartes du champ EM et de la chauffe induite -- 3 configurations de MFC.

Esprit des vignettes de conception de bobine du deck NIAR (Thermoplastic
Joining, Wichita State) : coupe verticale, lignes de champ autour des brins,
et la piece figuree par une barre coloree par la chauffe induite. Rien n'est
dessine a la main : le champ vient de la chaine EM du jumeau (Biot-Savart sur
la polyligne hairpin reelle, MFC par courants images, courants de Foucault en
plaque mince, densite Joule integree dans l'epaisseur).

Trois fichiers, un par configuration :
    fig_champ_em_1_bobine_seule.png     bobine seule (mu_r = 1 -> image nulle)
    fig_champ_em_2_mfc_actuel.png       + MFC labo      (31,5 x 55 mm)
    fig_champ_em_3_mfc_reduit.png       + MFC raccourci (31,5 x 31,75 mm)

GEOMETRIE (verifiee contre gen_schemas_montage.py, echelle 1:1, z=0 = surface
du lamine, z positif vers le haut) :
    laminate    0     -> -6,82 mm  (interface de soudure a -3,36 mm)
    ceramique   0     -> +2 mm
    tubes Cu    +2    -> +8 mm     carres 6 mm, entraxe 12,35 mm
    bloc MFC    +2    -> +14 mm    largeur 31,5 mm selon x, hauteur 12 mm
Les tubes sont EMBOITES dans le MFC (le bloc forme un canal autour d'eux) :
sa face inferieure est au ras de la leur, a +2 mm. A NE PAS confondre avec
`plan_miroir_cfc` = hauteur + rayon_tube = +8 mm, qui est le PLAN IMAGE du
calcul (sommet des brins), pas une face du bloc physique -- confusion qui
faisait "flotter" le bloc 6 mm trop haut dans une version precedente.

LIMITE ESSENTIELLE, affichee sur la figure 3. La methode des images
(`champ_coil.bz_plan`) ne connait que mu_r et le plan miroir -- un PLAN
INFINI. Elle ne depend NI de la longueur NI de la largeur du bloc. Le champ
calcule est donc RIGOUREUSEMENT IDENTIQUE entre MFC labo et MFC raccourci
(verrouille par `test_masque_source_mfc_off_est_non_regression`). Le seul
mecanisme supporte dans le projet pour representer le MFC raccourci est le
MASQUE D'EMPREINTE applique a posteriori a Q, en mode "conserver"
(renormalisation a puissance totale constante), comme le fait
`gen_mfc_reduit.py`. C'est une approximation du 1er ordre : masque dur 0/1
sans frange de bord, champ NON re-resolu pour un bloc plus petit,
`facteur_couplage` NON recalibre. Tendance seulement, pas de niveau absolu
valide -- le MFC raccourci est commande, pas encore essaye.

Ce que le MFC raccourci change : `cfc.longueur`, 55 -> 31,75 mm, c'est-a-dire
la dimension selon y. `cfc.largeur` (31,5 mm selon x) est INCHANGEE. La coupe
x-z ne peut donc pas distinguer les configurations 2 et 3 : c'est la vue en
plan qui le montre.

N'ecrit QUE les trois PNG de sortie.
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from matplotlib.colors import Normalize

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jumeau.materiaux import Config                                  # noqa: E402
from jumeau.geometrie import (sommets_bobine, plan_miroir_cfc,
                              masque_empreinte_cfc)                  # noqa: E402
from jumeau.em.champ_coil import champ_segments                      # noqa: E402
from jumeau.em.source_joule import source_spot                       # noqa: E402
from jumeau.geometrie import construire_grille, construire_couches    # noqa: E402
from _style import apply_style                                       # noqa: E402

apply_style(**{
    "font.size": 10.5, "axes.labelsize": 11, "axes.titlesize": 11.5,
    "xtick.labelsize": 9.5, "ytick.labelsize": 9.5, "axes.linewidth": 0.9,
    "savefig.pad_inches": 0.06, "figure.facecolor": "white",
    "savefig.facecolor": "white",
})

COURANT = 250.0
CENTRE_X = 0.060
# theta* canonique : SANS lui, source_spot rend la puissance EM BRUTE (son
# defaut facteur_couplage=1.0), soit ~6x sous la puissance reellement deposee
# par le modele. Indispensable des lors que la figure affiche des W/m2 absolus
# et qu'on en deduit une vitesse de chauffe.
FACTEUR_COUPLAGE = 6.0123
LONGUEUR_MFC_REDUIT = 0.03175          # m -- valeur commandee (cfc.longueur)

C_COIL, C_MFC, C_CERAM = "#E69F00", "#B4B4B4", "#6E6E6E"
C_LAMINE, TRAIT = "#CFE0EE", "#20303C"

cfg = Config.charger(R / "code" / "config")
# Grille et couches viennent directement de la config : elles ne dependent
# d'aucun essai. (Passer par un Essai refaisait tout le calcul EM de ses spots
# pour n'en garder que la grille, et couplait la figure a un YAML arbitraire.)
grille = construire_grille(cfg, nx=121, ny=41, nz=15)
couches = construire_couches(cfg)

geo = cfg.geometrie
centre_y = geo["laminate"]["largeur"] / 2.0
# decalage_x est marque "a identifier par calibration" dans geometrie.yaml : on
# le lit explicitement pour que la figure suive le modele si un jour il bouge.
DECALAGE_X = float(geo["coil"].get("decalage_x", 0.0))
sommets = sommets_bobine(cfg, CENTRE_X + DECALAGE_X, centre_y=centre_y)
z_miroir = plan_miroir_cfc(cfg)                      # +8 mm : PLAN IMAGE
entraxe = float(geo["coil"]["entraxe_jambes"])
tube = 2.0 * float(geo["coil"]["rayon_tube"])         # 6 mm
h_axe = float(geo["coil"]["hauteur"])                 # +5 mm (axe des brins)
mfc_x, mfc_h = float(geo["cfc"]["largeur"]), float(geo["cfc"]["hauteur"])
mfc_y_labo = float(geo["cfc"]["longueur"])

# --- empilement physique, en mm (cf. docstring) ----------------------------- #
Z_CERAM_BAS, Z_CERAM_HAUT = 0.0, (h_axe - tube / 2) * 1e3      # 0 -> +2
Z_TUBE_BAS, Z_TUBE_HAUT = Z_CERAM_HAUT, Z_CERAM_HAUT + tube * 1e3   # +2 -> +8
Z_MFC_BAS, Z_MFC_HAUT = Z_CERAM_HAUT, Z_CERAM_HAUT + mfc_h * 1e3    # +2 -> +14
Z_LAM_BAS = -grille.z[-1] * 1e3
Z_INTERFACE = -geo["laminate"]["epaisseur_sup"] * 1e3

# --- coupe x-z a mi-largeur ------------------------------------------------- #
xs = np.linspace(0.030, 0.090, 240)
zs = np.linspace(-0.014, 0.028, 190)
XG, ZG = np.meshgrid(xs, zs, indexing="ij")
pts = np.column_stack([XG.ravel(), np.full(XG.size, centre_y), ZG.ravel()])


def champ_coupe(avec_mfc):
    B = champ_segments(pts, sommets, COURANT)
    if avec_mfc:
        mu_r = float(geo["cfc"]["mu_r"])
        eta = (mu_r - 1.0) / (mu_r + 1.0)
        image = sommets.copy()
        image[:, 2] = 2.0 * z_miroir - image[:, 2]
        B += champ_segments(pts, image, eta * COURANT)
    return B[:, 0].reshape(XG.shape), B[:, 2].reshape(XG.shape)


def chauffe(mu_r, longueur_mfc=None):
    """Puissance Joule surfacique (W/m²), integree dans l'epaisseur.

    mu_r = 1 -> eta = 0 -> image nulle -> bobine seule. `longueur_mfc` non nul
    applique le masque d'empreinte en mode "conserver" (puissance totale
    inchangee, reconcentree sous l'empreinte) -- seul mecanisme du projet
    representant un bloc plus court.
    """
    # ATTENTION a l'ordre : `mu_r` est lu par la physique EM (source_spot le
    # relit a chaque appel) et doit donc etre en place AVANT le calcul, tandis
    # que `longueur` n'est lu QUE par masque_empreinte_cfc, donc APRES. Les deux
    # mutations ont des portees differentes ; les intervertir casserait le
    # resultat en silence.
    mem_mu, mem_lg = geo["cfc"]["mu_r"], geo["cfc"]["longueur"]
    geo["cfc"]["mu_r"] = mu_r
    try:
        Q = source_spot(grille, cfg, couches, courant=COURANT,
                        centre_x=CENTRE_X, centre_y=centre_y,
                        decalage_x=DECALAGE_X,
                        facteur_couplage=FACTEUR_COUPLAGE)
        if longueur_mfc is not None:
            geo["cfc"]["longueur"] = longueur_mfc
            m = masque_empreinte_cfc(grille, cfg, CENTRE_X, centre_y)[:, :, None]
            total = Q.sum()
            Q = Q * m
            if Q.sum() > 0:
                Q *= total / Q.sum()          # mode "conserver"
    finally:
        geo["cfc"]["mu_r"], geo["cfc"]["longueur"] = mem_mu, mem_lg
    # Somme de Riemann a pas constant, PAS np.trapezoid : `source_spot` construit
    # Q avec un poids par couche (`poids = epaisseur / (len(iz)*dz)`) tel que
    # sum_z(Q)*dz redonne EXACTEMENT la puissance surfacique deposee. La regle
    # des trapezes donnerait un demi-poids aux noeuds z extremes du domaine
    # GLOBAL (z=0, cote bobine, le plus chaud ; et z=z[-1]) -> sous-estimation
    # systematique d'environ 4 %. Meme convention que `procede.py` (_P_spots_2d).
    return Q.sum(axis=2) * grille.dz                    # (nx, ny) W/m²


CAS = [
    ("1_bobine_seule", "Bobine seule — sans concentrateur", False, 1.0, None, None),
    ("2_mfc_actuel", "Bobine + MFC actuel (31,5 × 55 mm)", True,
     float(geo["cfc"]["mu_r"]), mfc_y_labo,
     "Chauffe restreinte à l'empreinte du bloc (masque à puissance conservée) pour être\n"
     "comparable à la figure du MFC raccourci ; ce masque est DÉSACTIVÉ par défaut dans le\n"
     "modèle de production, où la source rayonne au-delà de l'empreinte."),
    ("3_mfc_reduit", "Bobine + MFC raccourci (31,5 × 31,75 mm)", True,
     float(geo["cfc"]["mu_r"]), LONGUEUR_MFC_REDUIT,
     "Champ EM strictement identique au MFC actuel : la méthode des images ne dépend que de\n"
     "µr et du plan miroir, pas de la taille du bloc. Seule l'empreinte change — masque dur à\n"
     "puissance conservée, 1er ordre, sans frange de bord et sans recalibrage. Tendance seulement."),
]

cartes = [chauffe(mu, lg) for nom, _, _, mu, lg, _ in CAS]
vmax = max(c.max() for c in cartes)
norme = Normalize(0.0, vmax)
pic_seule = cartes[0].max()

for (nom, _titre, avec_mfc, _, longueur_mfc, _avert), carte in zip(CAS, cartes):
    fig, (axg, axd) = plt.subplots(1, 2, figsize=(13.4, 5.2),
                                   gridspec_kw={"width_ratios": [1.0, 1.12]})

    # ---------------------------------------------------- coupe x-z (champ)
    Bx, Bz = champ_coupe(avec_mfc)
    axg.contourf(XG * 1e3, ZG * 1e3, np.log10(np.hypot(Bx, Bz) + 1e-12),
                 levels=22, cmap="Blues", alpha=0.32, zorder=0)
    axg.streamplot(xs * 1e3, zs * 1e3, Bx.T, Bz.T, color="0.35", linewidth=0.7,
                   density=1.4, arrowsize=0.7, zorder=2)

    x0, x1 = xs[0] * 1e3, xs[-1] * 1e3
    xg = grille.x * 1e3
    # max EN LARGEUR : a mi-largeur on tombe dans le creux du profil en M et la
    # moyenne dilue tout ; le max repond a "quelle chaleur atteint-on a cette
    # abscisse", sur la meme echelle de couleur que la vue en plan.
    profil = carte.max(axis=1)
    for xa, xb, val in zip(xg[:-1], xg[1:], 0.5 * (profil[:-1] + profil[1:])):
        axg.add_patch(Rectangle((xa, Z_LAM_BAS), xb - xa, -Z_LAM_BAS,
                                facecolor=plt.cm.inferno(norme(val)),
                                edgecolor="none", zorder=6))
    axg.plot([x0, x1], [Z_INTERFACE] * 2, color="white", lw=1.0, ls=(0, (5, 3)),
             zorder=7)
    axg.plot([x0, x1], [0, 0], color=TRAIT, lw=1.3, zorder=7)
    axg.plot([x0, x1], [Z_LAM_BAS, Z_LAM_BAS], color=TRAIT, lw=1.3, zorder=7)

    axg.add_patch(Rectangle((x0, Z_CERAM_BAS), x1 - x0, Z_CERAM_HAUT,
                            facecolor=C_CERAM, alpha=0.55, edgecolor=TRAIT,
                            linewidth=0.9, zorder=5))
    if avec_mfc:
        axg.add_patch(Rectangle(((CENTRE_X - mfc_x / 2) * 1e3, Z_MFC_BAS),
                                mfc_x * 1e3, Z_MFC_HAUT - Z_MFC_BAS,
                                facecolor=C_MFC, edgecolor=TRAIT, linewidth=1.3,
                                zorder=8))
    for sgn, marque, taille in ((-1, "×", 13), (1, "•", 20)):
        xc = (CENTRE_X + sgn * entraxe / 2) * 1e3
        axg.add_patch(Rectangle((xc - tube / 2 * 1e3, Z_TUBE_BAS), tube * 1e3,
                                tube * 1e3, facecolor=C_COIL, edgecolor=TRAIT,
                                linewidth=1.2, zorder=9))
        axg.text(xc, (Z_TUBE_BAS + Z_TUBE_HAUT) / 2, marque, ha="center",
                 va="center", fontsize=taille, fontweight="bold", color="0.1",
                 zorder=10)

    axg.set_title("Coupe de côté", pad=7, fontsize=12)
    axg.set_xlabel("x (mm) — longueur de la plaque")
    axg.set_ylabel("z (mm) — hauteur")
    axg.set_xlim(x0, x1); axg.set_ylim(zs[0] * 1e3, zs[-1] * 1e3)
    axg.set_aspect("equal")

    # ------------------------------------------- vue en plan (empreinte)
    im = axd.pcolormesh(grille.x * 1e3, grille.y * 1e3, carte.T, cmap="inferno",
                        norm=norme, shading="gouraud", zorder=1)
    axd.add_patch(Rectangle((0, 0), geo["laminate"]["longueur"] * 1e3,
                            geo["laminate"]["largeur"] * 1e3, facecolor="none",
                            edgecolor="white", linewidth=1.4, zorder=3))
    if avec_mfc:
        axd.add_patch(Rectangle(((CENTRE_X - mfc_x / 2) * 1e3,
                                 (centre_y - longueur_mfc / 2) * 1e3),
                                mfc_x * 1e3, longueur_mfc * 1e3, facecolor="none",
                                edgecolor="#39D0C6", linewidth=2.0, zorder=4))
    axd.set_title("Vue de dessus", pad=7, fontsize=12)
    axd.set_xlabel("x (mm) — longueur"); axd.set_ylabel("y (mm) — largeur")
    axd.set_aspect("equal")
    cb = fig.colorbar(im, ax=axd, fraction=0.032, pad=0.02)
    cb.set_label("Puissance Joule induite (W/m²)")

    fig.tight_layout()
    out = R / "biblio" / "modele" / "figures" / f"fig_champ_em_{nom}.png"
    fig.savefig(out); plt.close(fig)
    print(f"écrit : {out.name}   pic = {carte.max():.3e} W/m² "
          f"(×{carte.max() / pic_seule:.2f} vs bobine seule)")
