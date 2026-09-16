"""La séquence de passes recommandée, une image par passe, quasi sans texte.

Figure volontairement muette : ni titre, ni axes, ni graduations, ni légende.
SEULE EXCEPTION, les COTES — et elles ne figurent que sur les deux PREMIERS
panneaux : dimensions de la plaque et de l'empreinte sur le premier, pas entre
passes sur le second. Les répéter sur chaque vignette masquerait ce que la
séquence doit montrer ; les omettre laisserait le lecteur sans échelle. Les
limites d'axes restent identiques sur tous les panneaux, cotés ou non, sans quoi
les vignettes cessent d'être comparables entre elles. Elle sert à montrer la progression d'un coup d'œil — l'état de
l'interface après chaque passe — là où les figures commentées servent à
argumenter. Tout le chiffrage vit dans `balayage_pas_mfc_reduit.md` et
`positions_passes_pas_optimal.md`.

Configuration tracée : MFC réduit 31,75 mm sous l'**hypothèse corroborée** (image
tronquée, la famille que deux troncatures indépendantes soutiennent), 235 A, 20 s
par passe. `--pas-mm` choisit le pas — **seule variable entre deux figures**, pour
que deux séquences se comparent panneau à panneau.

`--mfc` choisit le bloc : `reduit` (défaut) ou `55` pour le MFC labo. Avec le
bloc de 55 mm il n'y a aucune réduction à modéliser — donc aucune hypothèse de
famille en jeu — et son empreinte DÉBORDE la plaque en largeur : le liseré sort
du cadre en haut et en bas, ce qui est exactement ce qu'il faut voir. Les limites
d'axes restent celles de la plaque dans tous les cas, pour que les figures se
comparent entre elles.

Trois figures valent d'être tracées : le bloc réduit à **15 mm** (le plus couvrant
qui ne dégrade rien dans son hypothèse), le bloc réduit à **22,5 mm** (pour isoler
l'effet du pas), et le **bloc de 55 mm à 22,5 mm**, qui est son propre optimum.

Trois états, trois aplats : sous la fusion / soudé / dégradé. La dégradation est
jugée en temps × température (`jumeau.thermique.dose_degradation`), pas au pic.
Le liseré marque l'empreinte du bloc à la passe courante.

Sortie : biblio/modele/figures/fig_passes_muettes_pas<N>mm.png
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Rectangle, FancyArrowPatch

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))
sys.path.insert(0, str(R / "code" / "scripts"))
from _style import apply_style, savefig                              # noqa: E402
from jumeau.materiaux import Config                                   # noqa: E402
from jumeau.planification.planificateur import verifier_sequentiel    # noqa: E402
from jumeau.thermique.dose_degradation import dose                    # noqa: E402

apply_style()

FIGURES = R / "biblio" / "modele" / "figures"
FUSION = 337.0
X_PREMIER, X_DERNIER, Y_C = 0.015875, 0.105875, 0.020
MFC_REDUIT = 0.03175
COURANT, DUREE, FAMILLE = 235.0, 20.0, "image_observation"
EMPREINTE_X, EMPREINTE_Y = 31.5, 31.75          # mm — cfc.largeur / cfc.longueur

ETATS = ListedColormap(["#D9E8F5", "#B7E4C7", "#F4C7C3"])
BORNES = BoundaryNorm([-0.5, 0.5, 1.5, 2.5], ETATS.N)


def centres(pas_mm: float) -> list[float]:
    n_int = max(1, round((X_DERNIER - X_PREMIER) * 1e3 / pas_mm))
    return [X_PREMIER + k * (X_DERNIER - X_PREMIER) / n_int for k in range(n_int + 1)]


def cote(ax, p0, p1, texte, decalage=0.0, vertical=False):
    """Une cote : double flèche entre p0 et p1, valeur au milieu."""
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="<|-|>", mutation_scale=7,
                                 lw=0.9, color="0.25", shrinkA=0, shrinkB=0,
                                 zorder=6))
    mx, my = (p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0
    ax.annotate(texte, (mx, my), textcoords="offset points",
                xytext=(0, decalage) if not vertical else (decalage, 0),
                ha="center", va="center", fontsize=7.5, color="0.2", zorder=7,
                rotation=90 if vertical else 0)


def etat(champs, temps) -> np.ndarray:
    """0 = sous la fusion, 1 = soudé, 2 = dégradé (dose > 1)."""
    pic = champs.max(axis=0)
    degrade = dose(champs, temps) > 1.0
    return np.where(degrade, 2, np.where(pic >= FUSION, 1, 0))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pas-mm", type=float, default=15.0,
                    help="pas entre centres de passe (mm ; défaut 15)")
    ap.add_argument("--mfc", choices=("reduit", "55"), default="reduit",
                    help="bloc tracé : réduit 31,75 mm (défaut) ou labo 55 mm")
    a = ap.parse_args()
    labo = a.mfc == "55"
    mfc_longueur = None if labo else MFC_REDUIT
    empreinte_y = 55.0 if labo else EMPREINTE_Y
    cfg = Config.charger(R / "code" / "config")
    cs = centres(a.pas_mm)
    pas_eff = (X_DERNIER - X_PREMIER) * 1e3 / (len(cs) - 1)
    # le nom sans préfixe reste celui du bloc réduit : ses deux figures sont
    # déjà publiées sur #62 et leurs URL ne doivent pas se rompre.
    prefixe = "fig_passes_muettes_mfc55" if labo else "fig_passes_muettes"
    sortie = FIGURES / f"{prefixe}_pas{pas_eff:.0f}mm.png"
    etats = []
    for n in range(1, len(cs) + 1):
        passes = [{"x_c": x, "y_c": Y_C, "courant": COURANT,
                   "mfc_longueur": mfc_longueur, "duree": DUREE} for x in cs[:n]]
        g, _, t, champs = verifier_sequentiel(cfg, passes, famille=FAMILLE,
                                              retour_historique=True)
        etats.append((g, etat(champs, t), cs[n - 1]))
        print(f"  passe {n}/{len(cs)}", flush=True)

    sortie.parent.mkdir(parents=True, exist_ok=True)
    # hauteur et hspace ajustes ensemble : les marges qui logent les cotes
    # creusaient des blancs entre vignettes (aspect egal => on ne peut pas
    # reduire la marge sans reduire l'echelle).
    fig, axes = plt.subplots(len(etats), 1, figsize=(7.2, 1.45 * len(etats)))
    for idx, (ax, (g, e, x_courant)) in enumerate(zip(np.atleast_1d(axes), etats)):
        x_mm, y_mm = g.x * 1e3, g.y * 1e3
        ax.pcolormesh(x_mm, y_mm, e.T, cmap=ETATS, norm=BORNES, shading="auto")
        ax.add_patch(Rectangle((x_courant * 1e3 - EMPREINTE_X / 2.0,
                                Y_C * 1e3 - empreinte_y / 2.0),
                               EMPREINTE_X, empreinte_y, facecolor="none",
                               edgecolor="0.15", lw=1.4, zorder=3))
        # limites IDENTIQUES sur tous les panneaux, cotés ou non : l'autoscale
        # les rendait incomparables, et les marges doivent loger les cotes.
        haut_empreinte = max(y_mm[-1], Y_C * 1e3 + empreinte_y / 2.0)
        ax.set_xlim(-16.0, x_mm[-1] + EMPREINTE_X / 2.0 + 6.0)
        ax.set_ylim(min(y_mm[0], Y_C * 1e3 - empreinte_y / 2.0) - 13.0,
                    haut_empreinte + 10.0)
        ax.set_aspect("equal")   # 120 x 40 mm : ne pas laisser matplotlib etirer
        ax.axis("off")           # ni axes, ni graduations, ni titre

        xl, yl = x_mm[-1], y_mm[-1]
        xc = x_courant * 1e3
        if idx == 0:             # panneau 1 : la plaque et l'empreinte du bloc
            cote(ax, (0, -7.0), (xl, -7.0), f"{xl:.0f} mm", decalage=-7)
            cote(ax, (-7.0, 0), (-7.0, yl), f"{yl:.0f} mm", decalage=-8,
                 vertical=True)
            cote(ax, (xc - EMPREINTE_X / 2.0, haut_empreinte + 4.0),
                 (xc + EMPREINTE_X / 2.0, haut_empreinte + 4.0),
                 f"{EMPREINTE_X:.1f}", decalage=6)
            y0, y1 = Y_C * 1e3 - empreinte_y / 2.0, Y_C * 1e3 + empreinte_y / 2.0
            cote(ax, (xc + EMPREINTE_X / 2.0 + 4.0, y0),
                 (xc + EMPREINTE_X / 2.0 + 4.0, y1),
                 f"{empreinte_y:.2f}".rstrip("0").rstrip("."), decalage=9,
                 vertical=True)
        elif idx == 1:           # panneau 2 : le pas, lisible dès deux passes
            cote(ax, (cs[0] * 1e3, haut_empreinte + 4.0),
                 (cs[1] * 1e3, haut_empreinte + 4.0),
                 f"pas {pas_eff:.1f}", decalage=6)
    # hspace POSITIF obligatoire : en negatif, le panneau suivant recouvrait la
    # cote de longueur placee sous le premier. Un chevauchement est un defaut,
    # un blanc n'est qu'une question d'esthetique.
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01, hspace=0.04)
    savefig(fig, sortie)
    plt.close(fig)
    print("ecrit :", sortie)


if __name__ == "__main__":
    main()
