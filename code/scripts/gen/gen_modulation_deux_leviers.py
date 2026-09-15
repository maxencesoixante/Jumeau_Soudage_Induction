"""Les deux réserves du calcul de modulation tiennent-elles ?

Le calcul précédent (`modulation_courant_limite.md`) conclut qu'aucune conduite du
courant ne met toute la plaque entre fusion (337 °C) et dégradation (450 °C),
parce que le rapport chaud/froid de l'état stationnaire vaut 2,30 pour un seuil de
1,356. Il portait deux réserves explicites. Elles sont testées ici, croisées.

LEVIER 1 — LA CONDITION DE BORD EN x = 0. Le point le plus froid tombait
exactement au coin x = 0, or `h_bord_x0 = 125` y est un paramètre EFFECTIF sans
base physique : au montage, les chants sont tous libres. On teste donc h_bord_x0
= 0. ATTENTION : cette valeur est RÉFUTÉE comme calibration (elle dégrade TC1 de
+98 °C sur les transitoires, cf. materiaux.yaml et issue #69). Ce n'est pas une
réouverture de ce verdict — c'est une mesure de SENSIBILITÉ : le verdict de
modulation dépend-il d'un paramètre qu'on sait mal fondé ?

LEVIER 2 — LE PLATEAU DE FUSION. Le calcul précédent était en régime linéaire
(80 A, rien ne fond), ce qui écarte la chaleur latente et le transport du bain.
On active ici le modèle de fusion (L_f = 40 J/g physique + k_plan(T > Tf) = 100).

UNE DISTINCTION QUI DÉCIDE DU RÉSULTAT : la chaleur latente est un tampon
TRANSITOIRE — une fois la matière passée par la zone de fusion, elle n'absorbe
plus rien et ne pèse plus sur l'état stationnaire. Ce qui subsiste au
stationnaire, c'est k_plan(T > Tf) : le bain fondu conduit ~33 fois mieux, donc
aplanit le champ LÀ OÙ IL EST DÉJÀ FONDU. On s'attend donc à un effet réel mais
qui ne touche pas les extrémités froides, restées sous Tf.

PROTOCOLE. Source moyenne des quatre spots (limite d'un balayage modulé), maintien
long. Les cellules à matériau canonique sont LINÉAIRES : une seule simulation
donne la forme, et l'amplitude optimale s'en déduit exactement par homothétie
(celle qui pose le point froid à 337 °C). Les cellules à fusion ne le sont pas :
elles sont balayées en courant.

Sorties : biblio/modele/modulation_deux_leviers.md
          biblio/modele/figures/fig_modulation_deux_leviers.png
"""
from __future__ import annotations

import copy
import sys
from datetime import date
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))
sys.path.insert(0, str(R / "code" / "scripts"))
from _style import apply_style, savefig, OKABE_ITO                  # noqa: E402
from jumeau.materiaux import Config                                  # noqa: E402
from jumeau.procede import Essai                                     # noqa: E402
from jumeau.geometrie import masque_empreinte_cfc                    # noqa: E402
from jumeau.em.source_joule import source_spot                       # noqa: E402

apply_style(**{"font.size": 9.5, "axes.titlesize": 10.5})

SORTIE_MD = R / "biblio" / "modele" / "modulation_deux_leviers.md"
SORTIE_FIG = R / "biblio" / "modele" / "figures" / "fig_modulation_deux_leviers.png"
GABARIT = R / "code" / "config" / "essais" / "exp7_200A.yaml"

FUSION, DEGRAD, AMBIANT = 337.0, 450.0, 20.0
SEUIL = (DEGRAD - AMBIANT) / (FUSION - AMBIANT)
CENTRES = [0.015875, 0.045875, 0.075875, 0.105875]
Y_C, MFC_REDUIT = 0.020, 0.03175
MAINTIEN = 1600.0
LF_PHYS, K_HOT = 40000.0, 100.0
TABLE_KT = [[0.0, 3.0], [FUSION, 3.0], [380.0, K_HOT], [700.0, K_HOT]]
COURANTS_FUSION = [200.0, 230.0, 260.0, 290.0]


def champ(courant, h_bord_x0, fusion, duree=MAINTIEN):
    cfg = copy.deepcopy(Config.charger(R / "code" / "config"))
    cfg.geometrie["cfc"]["longueur"] = MFC_REDUIT
    cfg.contact.h_haut = 30.087
    cfg.ambiant.h_bas_2d = 37.424
    cfg.ambiant.h_bord_x0 = float(h_bord_x0)
    if fusion:
        cfg.materiau.chaleur_latente = LF_PHYS
        cfg.materiau.k_plan_T = TABLE_KT
    e = Essai(cfg, GABARIT, nx=61, ny=21, nz=15, facteur_couplage=6.0123,
              decalage_x=0.0, racine=R, masque_source_mfc=False)
    e.spots = [{"centre_x": CENTRES[0], "t_debut": 0.0, "t_fin": duree}]
    e.spec["duree_chauffe"] = duree
    e.spec["duree_totale"] = duree
    Q_tot, masque_tot = None, None
    for x in CENTRES:
        m = masque_empreinte_cfc(e.grille, cfg, x, centre_y=Y_C)
        Q = source_spot(e.grille, cfg, e.couches, courant, x,
                        facteur_couplage=6.0123, centre_y=Y_C)
        total = float(Q.sum())
        Q = Q * m[:, :, None]
        Q = Q * (total / float(Q.sum()))     # famille A : le flux se reconcentre
        Q_tot = Q if Q_tot is None else Q_tot + Q
        masque_tot = m if masque_tot is None else np.maximum(masque_tot, m)
    Q_tot = Q_tot / len(CENTRES)
    e._masques = [masque_tot]
    e._Q_spots = [Q_tot]
    e._P_spots_2d = [Q_tot.sum(axis=2) * e.grille.dz]
    sv, sol = e.simuler(modele="2D")
    return e.grille, sv.resultat_2d(sol, sol.t.size - 1)


ETATS = ListedColormap(["#D9E8F5", "#B7E4C7", "#F4C7C3"])
BORNES = BoundaryNorm([-1e9, FUSION, DEGRAD, 1e9], ETATS.N)
LEGENDE = [Patch(facecolor="#D9E8F5", edgecolor="0.5",
                 label=f"sous {FUSION:.0f} °C"),
           Patch(facecolor="#B7E4C7", edgecolor="0.5",
                 label=f"fenêtre utile {FUSION:.0f}-{DEGRAD:.0f} °C"),
           Patch(facecolor="#F4C7C3", edgecolor="0.5",
                 label=f"au-dessus de {DEGRAD:.0f} °C")]


def bilan(T):
    """(Tmin, Tmax, rapport, % de l'interface dans la fenetre [337, 450])."""
    dans = float(np.mean((T >= FUSION) & (T <= DEGRAD)) * 100.0)
    return (float(T.min()), float(T.max()),
            float((T.max() - AMBIANT) / (T.min() - AMBIANT)), dans)


def optimum_lineaire(T):
    """Cas LINEAIRE : homothetie exacte posant le point froid a 337 °C."""
    k = (FUSION - AMBIANT) / (T.min() - AMBIANT)
    return bilan(AMBIANT + k * (T - AMBIANT))


def main() -> None:
    resultats, champs = {}, {}
    for h_bord in (125.0, 0.0):
        g, T = champ(80.0, h_bord, fusion=False)
        resultats[(h_bord, False)] = [(None,) + optimum_lineaire(T)]
        champs[(h_bord, False)] = (g, AMBIANT + (FUSION - AMBIANT)
                                   / (T.min() - AMBIANT) * (T - AMBIANT))
        print(f"  canonique h_bord_x0={h_bord:5.1f} : rapport "
              f"{resultats[(h_bord, False)][0][3]:.2f}  "
              f"fenetre {resultats[(h_bord, False)][0][4]:.1f} %", flush=True)

        lignes, meilleur = [], None
        for I in COURANTS_FUSION:
            g, T = champ(I, h_bord, fusion=True)
            b = bilan(T)
            lignes.append((I,) + b)
            print(f"  fusion    h_bord_x0={h_bord:5.1f} I={I:5.0f} A : "
                  f"min {b[0]:6.1f}  max {b[1]:6.1f}  rapport {b[2]:5.2f}  "
                  f"fenetre {b[3]:5.1f} %", flush=True)
            if meilleur is None or b[3] > meilleur[1][3]:
                meilleur = ((g, T), b)
        resultats[(h_bord, True)] = lignes
        champs[(h_bord, True)] = meilleur[0]

    SORTIE_FIG.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(11.0, 6.8))
    titres = {(125.0, False): "canonique · h_bord_x0 = 125 (référence)",
              (0.0, False): "canonique · h_bord_x0 = 0 (chants libres)",
              (125.0, True): "fusion · h_bord_x0 = 125",
              (0.0, True): "fusion · h_bord_x0 = 0"}
    for ax, cle in zip(axes.ravel(),
                       [(125.0, False), (0.0, False), (125.0, True), (0.0, True)]):
        g, T = champs[cle]
        x_mm, y_mm = g.x * 1e3, g.y * 1e3
        # carte TERNAIRE : la question posee est « quelle fraction est dans la
        # fenetre », pas « quelle temperature » — une echelle continue la noyait.
        ax.pcolormesh(x_mm, y_mm, T.T, cmap=ETATS, norm=BORNES, shading="auto")
        ax.contour(x_mm, y_mm, T.T, levels=[FUSION], colors="0.25", linewidths=1.1)
        if T.max() > DEGRAD:
            ax.contour(x_mm, y_mm, T.T, levels=[DEGRAD], colors="#C1272D",
                       linewidths=1.3, linestyles="--")
        b = bilan(T)
        ax.set_title(f"{titres[cle]}\nrapport {b[2]:.2f}  ·  "
                     f"dans la fenêtre {b[3]:.1f} %")
        ax.set_xlabel("x (mm)")
        ax.set_ylabel("y (mm)")
        ax.set_aspect("equal")   # 120 x 40 mm : ne pas laisser matplotlib etirer
    axes.ravel()[1].legend(handles=LEGENDE, loc="upper left",
                           bbox_to_anchor=(0.0, -0.42), ncol=3, fontsize=9,
                           frameon=False)
    fig.suptitle("Les deux réserves testées — l'une et l'autre font passer le "
                 f"rapport sous le seuil de {SEUIL:.2f}", y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    savefig(fig, SORTIE_FIG)
    plt.close(fig)

    L = [
        "# Les deux réserves du calcul de modulation, testées",
        "",
        f"Généré le {date.today().isoformat()}. Source moyenne des quatre spots "
        f"(limite d'un balayage modulé), maintien {MAINTIEN:.0f} s. Fenêtre utile = "
        f"interface entre {FUSION:.0f} et {DEGRAD:.0f} °C ; seuil de rapport "
        f"chaud/froid en dessous duquel une fenêtre peut exister : **{SEUIL:.3f}**.",
        "",
        f"![Les deux leviers](figures/{SORTIE_FIG.name})",
        "",
        "## Levier 1 — la condition de bord en `x` = 0",
        "",
        "Le point le plus froid tombait au coin `x` = 0, où `h_bord_x0 = 125` est un "
        "paramètre effectif sans base physique. ⚠️ `h_bord_x0 = 0` est **réfuté comme "
        "calibration** (+98 °C sur TC1 en transitoire, cf. issue #69) : ce test n'est "
        "pas une réouverture de ce verdict mais une mesure de **sensibilité**.",
        "",
        "| h_bord_x0 | rapport chaud/froid | dans la fenêtre |",
        "|---|---|---|",
    ]
    for h in (125.0, 0.0):
        r = resultats[(h, False)][0]
        L.append(f"| {h:.0f} | {r[3]:.2f} | {r[4]:.1f} % |")
    L += [
        "",
        "## Levier 2 — le plateau de fusion",
        "",
        "**Une distinction décide du résultat** : la chaleur latente est un tampon "
        "*transitoire*. Une fois la matière passée par la zone de fusion, elle "
        "n'absorbe plus rien et ne pèse plus sur l'état stationnaire. Ce qui "
        f"subsiste, c'est `k_plan(T > Tf) = {K_HOT:.0f}` : le bain conduit ~33 fois "
        "mieux et aplanit le champ **là où il est déjà fondu** — pas aux extrémités, "
        "restées sous Tf.",
        "",
        "| h_bord_x0 | courant | T min | T max | rapport | dans la fenêtre |",
        "|---|---|---|---|---|---|",
    ]
    for h in (125.0, 0.0):
        for I, tmin, tmax, r, dans in resultats[(h, True)]:
            L.append(f"| {h:.0f} | {I:.0f} A | {tmin:.0f} °C | {tmax:.0f} °C | "
                     f"{r:.2f} | {dans:.1f} % |")
    L += [
        "",
        "## Ce que ces chiffres renversent — et ce qu'ils ne prouvent pas",
        "",
        "**Les deux réserves étaient fondées, et le verdict précédent ne tient pas.** "
        "Il concluait qu'aucune conduite du courant ne peut mettre la plaque dans la "
        "fenêtre utile, sur la foi d'un rapport de 2,30. Chacun des deux leviers, "
        "pris seul, passe sous le seuil. Le calcul d'origine avait été fait en régime "
        "linéaire **précisément pour rendre l'argument propre** — et cette "
        "linéarisation écartait le mécanisme dominant.",
        "",
        "Mais trois choses interdisent de lire ces 100 % comme « la modulation "
        "marche » :",
        "",
        "- **Le critère de dégradation ignore le temps.** Il compare une température "
        f"de pic à {DEGRAD:.0f} °C. Or ces cellules sont des maintiens de "
        f"{MAINTIEN:.0f} s : tenir toute la plaque à 400 °C pendant vingt-sept "
        "minutes n'a rien d'équivalent à une brève excursion à "
        f"{DEGRAD:.0f} °C. La dégradation thermique est un produit temps × "
        "température, et le critère employé ici n'en voit qu'un facteur. C'est la "
        "limite la plus sérieuse des quatre cellules.",
        "- **Dans les cellules à fusion, la plaque entière est fondue** (point le "
        "plus froid à 375 °C, au-dessus de Tf). Ce n'est pas une soudure, c'est une "
        "plaque liquide tenue une demi-heure — elle ne garderait pas sa géométrie. "
        f"Et `k_plan(T > Tf) = {K_HOT:.0f}` est un **transport effectif** calibré sur "
        "le plateau d'un bain LOCALISÉ ; l'appliquer à une plaque intégralement "
        "fondue est une extrapolation large.",
        "- **La fenêtre en courant est extrêmement étroite** : 100 % à 200 A, 0 % à "
        "230 A, tout étant alors au-dessus du seuil. C'est précisément le problème "
        "de conduite qu'une modulation est censée résoudre — mais cela montre aussi "
        "que la marge est mince.",
        "",
        "**Conclusion honnête : le verdict « la modulation ne peut pas » n'est pas "
        "robuste.** Il dépendait d'un paramètre de bord sans base physique et d'une "
        "linéarisation qui excluait la physique utile. Ce qui le remplace n'est pas "
        "« la modulation marche », mais une question ouverte, et un critère de "
        "dégradation à refaire en temps × température avant d'aller plus loin.",
        "",
        "Reproduire : "
        "`.venv/bin/python code/scripts/gen/gen_modulation_deux_leviers.py`"]
    SORTIE_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("ecrit :", SORTIE_MD)
    print("ecrit :", SORTIE_FIG)


if __name__ == "__main__":
    main()
