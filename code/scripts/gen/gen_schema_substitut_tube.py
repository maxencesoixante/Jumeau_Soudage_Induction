"""Schéma du problème de cheminement d'effort — substitut de tube en U (issue à ouvrir).

Le tube CF/PEKK ne sera pas disponible. Le substitut envisagé : un U en fibre de
verre refermé par une plaque CF/PEKK consolidée 120 x 40 mm — l'ensemble formant
un tube. Une vessie gonflable occupe la cavité.

LA SOUDURE EST ENTRE DEUX PLAQUES CF/PEKK de même longueur, posées sur le tube,
comme sur le montage plan actuel. Le U n'est PAS un substrat de soudure : il est
purement structurel. (Une version antérieure de ce schéma plaçait à tort les
interfaces sur les ailes du U.)

LA VESSIE pousse l'empilement vers le haut contre l'OUTIL SUPÉRIEUR : c'est cette
réaction qui comprime l'interface de soudure.

LA QUESTION : faire passer l'effort de la cellule de force DANS LA VESSIE, et non
dans les parois du U.

Ce schéma pose le problème tel qu'il est, c'est-à-dire un partage d'effort entre
DEUX CHEMINS EN PARALLÈLE :
  - le chemin voulu   : cellule -> vessie -> interfaces de soudure ;
  - le chemin parasite : cellule -> plaque -> ailes du U -> bâti.
Deux raideurs en parallèle se partagent l'effort au prorata de leur raideur. Or
une paroi de verre en compression est raide, une vessie sous pression est
souple : par défaut, l'effort part presque entièrement dans les parois. Le chemin
souhaité est précisément le plus souple — c'est tout le problème.

COTES : seules celles de la plaque sont connues (120 x 40 mm, comme les
échantillons actuels). La section du U, l'épaisseur des ailes et la vessie ne le
sont pas — la référence vessie est attendue de RCF Technologies. Le schéma les
laisse donc explicitement en « ? » plutôt que d'inventer des valeurs.

Sortie : biblio/labo/figures/fig_substitut_tube_chemins_effort.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, FancyArrowPatch

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _style import apply_style, savefig, OKABE_ITO  # noqa: E402

apply_style(**{"font.size": 10, "axes.titlesize": 11})

SORTIE = R / "biblio" / "labo" / "figures" / "fig_substitut_tube_chemins_effort.png"
VERRE, CFPEKK = "#BBBBBB", OKABE_ITO["bleu"]
VOULU, PARASITE = OKABE_ITO["vert"], OKABE_ITO["vermillon"]


def panneau_montage(ax) -> None:
    """Coupe transverse : le U, la plaque soudée, la vessie, les deux chemins."""
    # bati
    ax.add_patch(Rectangle((-6, -6), 52, 6, facecolor="0.75", edgecolor="0.4"))
    ax.text(40, -3, "bâti", ha="center", va="center", fontsize=8.5, color="0.25")

    # U en fibre de verre : ame + deux ailes
    ax.add_patch(Rectangle((0, 0), 40, 5, facecolor=VERRE, edgecolor="0.35"))
    ax.add_patch(Rectangle((0, 5), 5, 22, facecolor=VERRE, edgecolor="0.35"))
    ax.add_patch(Rectangle((35, 5), 5, 22, facecolor=VERRE, edgecolor="0.35"))
    ax.text(20, 2.4, "U — fibre de verre", ha="center", va="center", fontsize=8.5)

    # vessie dans la cavite
    ax.add_patch(FancyBboxPatch((7, 8), 26, 16, boxstyle="round,pad=0.6,rounding_size=3",
                                facecolor="#F6D9C3", edgecolor=OKABE_ITO["orange"], lw=1.4))
    ax.text(20, 16, "vessie\n(réf. RCF à venir)", ha="center", va="center", fontsize=8.5)

    # plaque 1 : referme le U pour en faire un tube
    ax.add_patch(Rectangle((0, 27), 40, 3, facecolor=CFPEKK, edgecolor="0.2"))
    # plaque 2 : soudee sur la premiere, meme longueur
    ax.add_patch(Rectangle((0, 30.4), 40, 3, facecolor=CFPEKK, edgecolor="0.2"))
    ax.annotate("2 plaques\nCF/PEKK\n120 × 40 mm", xy=(1.5, 31.9), xytext=(-16.5, 28),
                fontsize=8.5, color=CFPEKK, ha="left", va="center",
                arrowprops=dict(arrowstyle="->", color=CFPEKK, lw=1.1))

    # INTERFACE DE SOUDURE : entre les deux plaques, pas sur les ailes du U
    ax.plot([0, 40], [30.2, 30.2], color=OKABE_ITO["rose"], lw=3.0,
            solid_capstyle="butt", zorder=6)
    ax.annotate("interface de soudure\n(CF/PEKK sur CF/PEKK)", xy=(36, 30.2), xytext=(44, 24),
                fontsize=8.5, color=OKABE_ITO["rose"], ha="left",
                arrowprops=dict(arrowstyle="->", color=OKABE_ITO["rose"], lw=1.1))

    # outil superieur + cellule au-dessus
    ax.add_patch(Rectangle((-3, 34), 46, 3, facecolor="0.55", edgecolor="0.3"))
    ax.text(20, 35.5, "outil supérieur", ha="center", va="center", fontsize=8.5,
            color="white")
    ax.add_patch(Rectangle((14, 39), 12, 4.5, facecolor="white", edgecolor="0.2", lw=1.3))
    ax.text(20, 41.2, "cellule de force", ha="center", va="center", fontsize=8.5)

    # chemin PARASITE : par les ailes
    for x in (2.5, 37.5):
        ax.add_patch(FancyArrowPatch((x, 26), (x, 6), arrowstyle="-|>", mutation_scale=13,
                                     color=PARASITE, lw=2.4, alpha=0.9))
    ax.text(-9, 16, "chemin\nPARASITE\n(ailes du U)\nen traction", ha="center",
            va="center", fontsize=8.5, color=PARASITE, fontweight="bold")

    # chemin VOULU : la vessie POUSSE VERS LE HAUT, l'outil reagit
    for x in (11, 20, 29):
        ax.add_patch(FancyArrowPatch((x, 23.2), (x, 26.6), arrowstyle="-|>",
                                     mutation_scale=15, color=VOULU, lw=2.6))
    ax.annotate("chemin VOULU\nvessie → interface → outil",
                xy=(29, 25), xytext=(44, 13),
                fontsize=8.5, color=VOULU, fontweight="bold", ha="left", va="center",
                arrowprops=dict(arrowstyle="->", color=VOULU, lw=1.1))

    ax.set_xlim(-17, 66)
    ax.set_ylim(-8, 46)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Coupe transverse du substitut", pad=8)


def panneau_raideurs(ax) -> None:
    """Le même montage vu comme deux raideurs en parallèle."""
    ax.add_patch(Rectangle((0, 0), 30, 3, facecolor="0.75", edgecolor="0.4"))
    ax.add_patch(Rectangle((0, 22), 30, 3, facecolor=CFPEKK, edgecolor="0.2"))
    ax.add_patch(FancyArrowPatch((15, 31), (15, 25.6), arrowstyle="-|>",
                                 mutation_scale=16, color="0.2", lw=2))
    ax.text(15, 32.6, "$F$ (cellule)", ha="center", fontsize=9.5)

    import numpy as np
    for x0, tours, coul, nom in ((5, 11, PARASITE, "$k_{\\rm paroi}$ (raide)"),
                                 (22, 4, VOULU, "$k_{\\rm vessie}$ (souple)")):
        t = np.linspace(0, 1, 400)
        ax.plot(x0 + 2.0 * np.sin(2 * np.pi * tours * t), 4 + 17 * t,
                color=coul, lw=2.0)
        ax.text(x0, -1.6, nom, ha="center", va="top", fontsize=9, color=coul)

    ax.annotate("", xy=(20.4, 13), xytext=(7.4, 13),
                arrowprops=dict(arrowstyle="<->", color="0.35", lw=1.1))
    ax.text(14, 14.2, "en parallèle", ha="center", fontsize=8.5, color="0.35")
    ax.text(15, -9.4, r"$\dfrac{F_{\rm paroi}}{F_{\rm vessie}} = "
                      r"\dfrac{k_{\rm paroi}}{k_{\rm vessie}} \gg 1$",
            ha="center", va="center", fontsize=12.5)

    ax.set_xlim(-4, 34)
    ax.set_ylim(-15, 38)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Le problème, en une ligne", pad=8)


def main() -> None:
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    fig, (ag, ad) = plt.subplots(1, 2, figsize=(11.4, 5.0),
                                 gridspec_kw={"width_ratios": [1.75, 1]})
    panneau_montage(ag)
    panneau_raideurs(ad)
    fig.suptitle("Substitut de tube : par où passe l'effort de la cellule ?", y=1.02)
    savefig(fig, SORTIE)
    plt.close(fig)
    print("ecrit :", SORTIE)


if __name__ == "__main__":
    main()
