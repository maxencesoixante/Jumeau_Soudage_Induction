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

LES PLAQUES SONT SEULEMENT POSÉES sur les ailes, non solidaires. Le contact est
donc UNILATÉRAL : il ne transmet que de la compression, jamais de traction. Comme
la vessie pousse la plaque VERS LE HAUT, c'est-à-dire loin des ailes, le contact
s'ouvre et le chemin parasite SE DÉCONNECTE DE LUI-MÊME. Il ne subsiste que si
les cotes le forcent (voir le panneau de droite).

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

    # contact UNILATERAL plaque / ailes : il s'ouvre quand la vessie pousse
    for x in (2.5, 37.5):
        ax.plot([x - 2.4, x + 2.4], [27, 27], color=PARASITE, lw=2.2, ls=(0, (2, 1.6)),
                solid_capstyle="butt", zorder=6)
    ax.annotate("contact simplement POSÉ\n→ unilatéral, il s'ouvre", xy=(2.5, 27),
                xytext=(-16.5, 19), fontsize=8.5, color=PARASITE, fontweight="bold",
                ha="left", va="center",
                arrowprops=dict(arrowstyle="->", color=PARASITE, lw=1.1))

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
    """Ce qui reste du problème : une condition de cotes, pas un partage d'effort."""
    ax.text(15, 34, "Les plaques étant seulement posées,\nle chemin parasite n'existe que\nsi les COTES le forcent.",
            ha="center", va="center", fontsize=9.5)

    for y0, coul, titre, detail in (
            (18, VOULU, "cotes correctes", "l'outil touche la plaque,\nles ailes ne portent pas\n→ tout passe par la vessie"),
            (2, PARASITE, "interférence de cotes", "les ailes portent la plaque\navant l'outil\n→ elles court-circuitent")):
        ax.add_patch(Rectangle((0, y0 + 7), 30, 1.8, facecolor="0.55", edgecolor="0.3"))
        ax.add_patch(Rectangle((0, y0 + 4.4), 30, 2.4, facecolor=CFPEKK, edgecolor="0.2"))
        ax.add_patch(Rectangle((2, y0), 3, 4.4 if coul is PARASITE else 3.4,
                               facecolor=VERRE, edgecolor="0.35"))
        ax.add_patch(Rectangle((25, y0), 3, 4.4 if coul is PARASITE else 3.4,
                               facecolor=VERRE, edgecolor="0.35"))
        ax.text(15, y0 + 2.2, titre, ha="center", va="center", fontsize=9,
                color=coul, fontweight="bold")
        ax.text(33, y0 + 3, detail, ha="left", va="center", fontsize=8.3, color=coul)

    ax.set_xlim(-3, 62)
    ax.set_ylim(-3, 39)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Ce qu'il reste à garantir", pad=8)


def main() -> None:
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    fig, (ag, ad) = plt.subplots(1, 2, figsize=(12.6, 5.2),
                                 gridspec_kw={"width_ratios": [1.25, 1]})
    panneau_montage(ag)
    panneau_raideurs(ad)
    fig.suptitle("Substitut de tube : le chemin de l'effort vers la soudure", y=1.02)
    savefig(fig, SORTIE)
    plt.close(fig)
    print("ecrit :", SORTIE)


if __name__ == "__main__":
    main()
