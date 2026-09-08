"""Schema du montage de soudage semi-statique SUR TUBE -- dessin pur.

AUCUN axe, AUCUNE graduation, AUCUN texte, AUCUNE cote : uniquement des
formes pleines, dans l'esprit des vignettes de coupe de la slide 9 du deck
NIAR (Thermoplastic Joining, Wichita State).

Difference avec `gen_schemas_montage.py` (exp7/exp9) : la plaque INFERIEURE
est remplacee par le TUBE composite, avec sa VESSIE GONFLABLE interieure
(contre-pression), le tube etant tenu par deux BRACKETS lateraux boulonnes
sur la TABLE de soudage semi-statique.

Deux vues : coupe transversale (tube vu en bout) et vue de cote (le long du
tube). Les elements caches sont en trait interrompu (convention de dessin).

N'ecrit QUE le PNG de sortie.
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import (Circle, Rectangle, Polygon, Wedge, FancyArrow,
                                FancyBboxPatch)

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
OUT = R / "biblio" / "presentations" / "figures_schemas" / "schema_montage_tube.png"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _style import apply_style  # noqa: E402

apply_style(**{"figure.facecolor": "white", "savefig.facecolor": "white",
               "savefig.pad_inches": 0.04})

# --- palette : celle des autres schemas du projet, aplatie facon NIAR -------- #
C_COIL = "#E69F00"      # bobine cuivre
C_MFC = "#B4B4B4"       # concentrateur
C_CERAM = "#6E6E6E"     # entretoise ceramique
C_TUBE = "#1F4E79"      # tube composite (fonce, facon NIAR)
C_PLAQUE = "#3E7CB1"    # piece rapportee CF/PEKK
C_VESSIE = "#C9B7E8"    # vessie gonflable (lavande)
C_BRACKET = "#9AA5B1"   # brackets
C_TABLE = "#5A6570"     # table
TRAIT = "#20303C"

# --- geometrie de dessin (unites arbitraires : rien n'est cote) -------------- #
R_EXT, R_INT = 40.0, 33.0
R_VESSIE = 27.0
EP_PLAQUE, EP_CERAM = 7.0, 3.0
DEMI_ANGLE = 30.0                     # demi-ouverture de la piece rapportee

fig = plt.figure(figsize=(13.6, 6.4))
axA = fig.add_axes([0.005, 0.02, 0.46, 0.96])
axB = fig.add_axes([0.485, 0.02, 0.51, 0.96])
for ax in (axA, axB):
    ax.set_aspect("equal")
    ax.axis("off")


def bande_arc(ax, r_int, ep, demi_angle, couleur, zorder):
    """Bande d'epaisseur constante epousant le haut du tube."""
    w = Wedge((0, 0), r_int + ep, 90 - demi_angle, 90 + demi_angle, width=ep,
              facecolor=couleur, edgecolor=TRAIT, linewidth=1.4, zorder=zorder)
    ax.add_patch(w)
    return w


# =========================================================================== #
# A -- coupe transversale : le tube vu en bout
# =========================================================================== #
# table
axA.add_patch(Rectangle((-96, -132), 192, 26, facecolor=C_TABLE,
                        edgecolor=TRAIT, linewidth=1.4, zorder=2))
for xs in np.arange(-84, 90, 24):     # rainures en T de la table
    axA.add_patch(Rectangle((xs, -112), 5, 6, facecolor="#3E4750",
                            edgecolor="none", zorder=3))

# brackets lateraux : blocs montant PLUS HAUT que l'axe du tube, dans lesquels
# une encoche circulaire est degagee (cercle blanc) -> le tube y repose.
for sgn in (-1, 1):
    x_int, x_ext = sgn * 26, sgn * 74
    corps = [(x_int, -106), (x_ext, -106), (x_ext, 16), (x_int, 16)]
    axA.add_patch(Polygon(corps, closed=True, facecolor=C_BRACKET,
                          edgecolor=TRAIT, linewidth=1.5, zorder=4))
    for dy in (-92, -74):
        axA.add_patch(Circle((sgn * 50, dy), 4.6, facecolor="#5F6B77",
                             edgecolor=TRAIT, linewidth=1.0, zorder=6))
# encoche : degage le logement du tube dans les deux brackets
axA.add_patch(Circle((0, 0), R_EXT + 1.0, facecolor="white", edgecolor="none",
                     zorder=5))

# tube composite (couronne)
axA.add_patch(Circle((0, 0), R_EXT, facecolor=C_TUBE, edgecolor=TRAIT,
                     linewidth=1.6, zorder=8))
axA.add_patch(Circle((0, 0), R_INT, facecolor="white", edgecolor=TRAIT,
                     linewidth=1.4, zorder=9))

# vessie gonflable + poussee radiale
axA.add_patch(Circle((0, -1.5), R_VESSIE, facecolor=C_VESSIE, edgecolor=TRAIT,
                     linewidth=1.3, zorder=10))
for a in np.arange(0, 360, 45):
    t = np.radians(a)
    x0, y0 = (R_VESSIE + 1.0) * np.cos(t), (R_VESSIE + 1.0) * np.sin(t) - 1.5
    dx, dy = (R_INT - R_VESSIE - 3.0) * np.cos(t), (R_INT - R_VESSIE - 3.0) * np.sin(t)
    axA.add_patch(FancyArrow(x0, y0, dx, dy, width=1.5, head_width=5.0,
                             head_length=3.6, length_includes_head=True,
                             facecolor="#6E5A96", edgecolor="none", zorder=11))
# tige de gonflage
axA.add_patch(Rectangle((-3.2, -R_EXT - 20), 6.4, 22, facecolor=C_VESSIE,
                        edgecolor=TRAIT, linewidth=1.2, zorder=7))
axA.add_patch(Rectangle((-7.0, -R_EXT - 27), 14.0, 8, facecolor="#6E5A96",
                        edgecolor=TRAIT, linewidth=1.2, zorder=7))

# piece rapportee + ceramique, epousant le tube
bande_arc(axA, R_EXT, EP_PLAQUE, DEMI_ANGLE, C_PLAQUE, 12)
bande_arc(axA, R_EXT + EP_PLAQUE, EP_CERAM, DEMI_ANGLE - 4, C_CERAM, 13)

# concentrateur + brins de bobine
y_mfc = R_EXT + EP_PLAQUE + EP_CERAM + 1.5
axA.add_patch(FancyBboxPatch((-34, y_mfc), 68, 20, boxstyle="round,pad=0,rounding_size=2.5",
                             facecolor=C_MFC, edgecolor=TRAIT, linewidth=1.5, zorder=14))
for sgn in (-1, 1):
    axA.add_patch(Rectangle((sgn * 9 - 6.5, y_mfc + 1.6), 13, 13, facecolor=C_COIL,
                            edgecolor=TRAIT, linewidth=1.3, zorder=15))

axA.set_xlim(-104, 104)
axA.set_ylim(-142, 108)

# =========================================================================== #
# B -- vue de cote : le long du tube
# =========================================================================== #
L = 190.0
axB.add_patch(Rectangle((-L / 2 - 26, -132), L + 52, 26, facecolor=C_TABLE,
                        edgecolor=TRAIT, linewidth=1.4, zorder=2))
for xs in np.arange(-L / 2 - 14, L / 2 + 20, 24):
    axB.add_patch(Rectangle((xs, -112), 5, 6, facecolor="#3E4750",
                            edgecolor="none", zorder=3))

for sgn in (-1, 1):                    # brackets aux deux extremites
    xc = sgn * (L / 2 - 18)
    axB.add_patch(Polygon([(xc - 20, -106), (xc + 20, -106), (xc + 20, -R_EXT + 6),
                           (xc - 20, -R_EXT + 6)], closed=True, facecolor=C_BRACKET,
                          edgecolor=TRAIT, linewidth=1.5, zorder=4))
    for dx in (-7, 7):
        axB.add_patch(Circle((xc + dx, -96), 4.2, facecolor="#5F6B77",
                             edgecolor=TRAIT, linewidth=1.0, zorder=6))

# tube (capsule) + vessie interieure en trait interrompu (element cache)
from matplotlib.patches import Ellipse
axB.add_patch(Rectangle((-L / 2, -R_EXT), L, 2 * R_EXT, facecolor=C_TUBE,
                        edgecolor="none", zorder=8))
for yy in (-R_EXT, R_EXT):
    axB.plot([-L / 2, L / 2], [yy, yy], color=TRAIT, lw=1.6, zorder=11,
             solid_capstyle="butt")
# fond ouvert cote droit : couronne elliptique -> le tube est creux
axB.add_patch(Ellipse((L / 2, 0), 26, 2 * R_EXT, facecolor=C_TUBE,
                      edgecolor=TRAIT, linewidth=1.6, zorder=9))
axB.add_patch(Ellipse((L / 2, 0), 26 * R_INT / R_EXT, 2 * R_INT, facecolor="#12324F",
                      edgecolor=TRAIT, linewidth=1.4, zorder=10))
axB.add_patch(Ellipse((-L / 2, 0), 26, 2 * R_EXT, facecolor="#17405F",
                      edgecolor=TRAIT, linewidth=1.5, zorder=7))
axB.add_patch(FancyBboxPatch((-L / 2 + 9, -R_VESSIE), L - 18, 2 * R_VESSIE,
                             boxstyle="round,pad=0,rounding_size=9",
                             facecolor="none", edgecolor="#D8CBF2", linewidth=1.8,
                             linestyle=(0, (7, 4)), zorder=12))
axB.add_patch(Rectangle((L / 2 + 6, -9), 26, 18, facecolor=C_VESSIE,
                        edgecolor=TRAIT, linewidth=1.2, zorder=7))
axB.add_patch(Rectangle((L / 2 + 30, -13), 9, 26, facecolor="#6E5A96",
                        edgecolor=TRAIT, linewidth=1.2, zorder=7))

# piece rapportee + ceramique sur le dessus du tube
axB.add_patch(Rectangle((-L / 2 + 16, R_EXT - 1), L - 32, EP_PLAQUE,
                        facecolor=C_PLAQUE, edgecolor=TRAIT, linewidth=1.4, zorder=12))
axB.add_patch(Rectangle((-L / 2 + 24, R_EXT - 1 + EP_PLAQUE), L - 48, EP_CERAM,
                        facecolor=C_CERAM, edgecolor=TRAIT, linewidth=1.3, zorder=13))

y_mfc = R_EXT - 1 + EP_PLAQUE + EP_CERAM + 1.5
axB.add_patch(FancyBboxPatch((-16, y_mfc), 32, 20, boxstyle="round,pad=0,rounding_size=2.5",
                             facecolor=C_MFC, edgecolor=TRAIT, linewidth=1.5, zorder=14))
for sgn in (-1, 1):
    axB.add_patch(Rectangle((sgn * 8 - 5.5, y_mfc + 1.6), 11, 13, facecolor=C_COIL,
                            edgecolor=TRAIT, linewidth=1.3, zorder=15))

axB.set_xlim(-L / 2 - 44, L / 2 + 54)
axB.set_ylim(-142, 108)

fig.savefig(OUT)
print("écrit :", OUT)
