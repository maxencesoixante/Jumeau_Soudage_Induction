"""Où se pose le MFC à chaque passe, pour le pas optimal de chaque configuration.

CE QUE LA FIGURE REND VISIBLE, et qu'un tableau de pourcentages ne dit pas : le
bloc de ferrite n'est pas réduit dans la direction où il avance.

Son empreinte vaut `largeur` = 31,5 mm le long de **x** (le sens du déplacement)
et `longueur` = 55 ou 31,75 mm le long de **y** (la largeur de la plaque, cf.
`geometrie.yaml:cfc` et `masque_empreinte_cfc`). Raccourcir le MFC de 55 à
31,75 mm agit donc **en largeur**, pas en longueur :

  - l'empreinte le long de x reste 31,5 mm dans les deux cas — le recouvrement
    entre passes ne dépend que du PAS, pas de la taille du bloc ;
  - en largeur, le bloc de 55 mm déborde la plaque (40 mm) de part et d'autre,
    tandis que le bloc réduit laisse ~4 mm de chant DÉCOUVERT de chaque côté.

C'est la raison géométrique du verdict de #39 : le MFC réduit « coupe les lobes
de bord ». On le voit ici directement, au lieu de le déduire d'un profil.

Pas optimaux repris de `balayage_pas_mfc_reduit.md` — le pas le plus couvrant
SANS AUCUNE dégradation, au critère de dose.

Sortie : biblio/modele/figures/fig_positions_passes_pas_optimal.png
         biblio/modele/positions_passes_pas_optimal.md
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))
sys.path.insert(0, str(R / "code" / "scripts"))
from _style import apply_style, savefig, OKABE_ITO                  # noqa: E402
from jumeau.materiaux import Config                                  # noqa: E402

apply_style(**{"font.size": 9.5, "axes.titlesize": 10.5})

SORTIE_FIG = R / "biblio" / "modele" / "figures" / "fig_positions_passes_pas_optimal.png"
SORTIE_MD = R / "biblio" / "modele" / "positions_passes_pas_optimal.md"

PLAQUE_L, PLAQUE_W = 120.0, 40.0        # mm
X_PREMIER, X_DERNIER, Y_C = 15.875, 105.875, 20.0

# (libellé, longueur MFC en y (mm), pas (mm), soudé propre (%), couleur)
CONFIGS = [
    ("MFC labo 55 mm", 55.0, 22.5, 16.2, OKABE_ITO["bleu"]),
    ("MFC réduit 31,75 mm — hypothèse favorable (A)", 31.75, 22.5, 27.2,
     OKABE_ITO["vermillon"]),
    ("MFC réduit 31,75 mm — hypothèse corroborée (B)", 31.75, 15.0, 39.2,
     OKABE_ITO["vert"]),
]
EMPREINTE_X = 31.5                      # mm — `cfc.largeur`, le long du déplacement


def centres(pas: float) -> list[float]:
    n_int = max(1, round((X_DERNIER - X_PREMIER) / pas))
    return [X_PREMIER + k * (X_DERNIER - X_PREMIER) / n_int for k in range(n_int + 1)]


def panneau(ax, libelle, longueur_y, pas, soude, couleur):
    cs = centres(pas)
    pas_eff = (X_DERNIER - X_PREMIER) / (len(cs) - 1)
    ax.add_patch(Rectangle((0, 0), PLAQUE_L, PLAQUE_W, facecolor="#F2F2F2",
                           edgecolor="0.35", lw=1.2, zorder=0))
    y0, y1 = Y_C - longueur_y / 2.0, Y_C + longueur_y / 2.0
    for k, x in enumerate(cs, 1):
        # empreinte du MFC : 31,5 mm le long de x dans TOUS les cas
        ax.add_patch(Rectangle((x - EMPREINTE_X / 2.0, y0), EMPREINTE_X, longueur_y,
                               facecolor=couleur, alpha=0.30, edgecolor=couleur,
                               lw=1.0, zorder=2))
        ax.plot([x], [Y_C], "+", ms=7, color="0.15", mew=1.4, zorder=4)
        ax.annotate(str(k), (x, PLAQUE_W + 1.5), ha="center", va="bottom",
                    fontsize=8.5, color="0.2", fontweight="bold")
    # chants laissés découverts en largeur (bloc réduit seulement)
    if y0 > 0:
        for yb in (0.0, y1):
            h = y0 if yb == 0.0 else PLAQUE_W - y1
            ax.add_patch(Rectangle((0, yb), PLAQUE_L, h, facecolor="none",
                                   edgecolor=OKABE_ITO["orange"], lw=1.3,
                                   ls=(0, (3, 2)), zorder=3))
        ax.annotate(f"chant découvert\n{y0:.1f} mm", xy=(PLAQUE_L + 2, y0 / 2),
                    fontsize=8.5, color=OKABE_ITO["orange"], va="center")
    recouvrement = EMPREINTE_X - pas_eff
    ax.set_title(f"{libelle}\npas {pas_eff:.1f} mm  ·  {len(cs)} passes  ·  "
                 f"recouvrement {recouvrement:.1f} mm  ·  soudé {soude:.1f} %")
    ax.set_xlim(-4, PLAQUE_L + 30)
    ax.set_ylim(-4, PLAQUE_W + 8)
    ax.set_aspect("equal")    # 120 x 40 mm : ne pas laisser matplotlib etirer
    ax.set_xlabel("x — longueur (mm)")
    ax.set_ylabel("y (mm)")
    return cs, pas_eff, recouvrement


def main() -> None:
    cfg = Config.charger(R / "code" / "config")
    assert abs(cfg.geometrie["cfc"]["largeur"] * 1e3 - EMPREINTE_X) < 1e-6, \
        "l'empreinte le long de x doit venir de geometrie.yaml:cfc.largeur"

    SORTIE_FIG.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 1, figsize=(9.6, 8.6))
    lignes = []
    for ax, (lib, ly, pas, soude, coul) in zip(axes, CONFIGS):
        cs, pas_eff, rec = panneau(ax, lib, ly, pas, soude, coul)
        lignes.append((lib, ly, pas_eff, cs, rec, soude))
        print(f"  {lib:48s} pas {pas_eff:5.1f} mm  {len(cs)} passes  "
              f"recouvrement {rec:5.1f} mm", flush=True)
    fig.suptitle("Position du MFC à chaque passe, au pas optimal de chaque "
                 "configuration\n"
                 "rectangle plein : empreinte du bloc  ·  + : centre de passe", y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    savefig(fig, SORTIE_FIG)
    plt.close(fig)

    L = ["# Où se pose le MFC à chaque passe, au pas optimal",
         "",
         f"Généré le {date.today().isoformat()}. Pas optimaux repris de "
         "`balayage_pas_mfc_reduit.md` (le plus couvrant **sans aucune dégradation**, "
         "au critère de dose). Étendue fixe : premier centre "
         f"`x` = {X_PREMIER:.1f} mm, dernier `x` = {X_DERNIER:.1f} mm, spot centré en "
         f"largeur (`y` = {Y_C:.0f} mm).",
         "",
         f"![Positions des passes](figures/{SORTIE_FIG.name})",
         "",
         "## Le point de géométrie qui explique tout le reste",
         "",
         f"L'empreinte du bloc vaut **{EMPREINTE_X:.1f} mm le long de `x`** (le sens du "
         "déplacement) et 55 ou 31,75 mm **le long de `y`** (la largeur de la plaque) — "
         "cf. `geometrie.yaml:cfc`. Deux conséquences :",
         "",
         f"- **Le recouvrement entre passes ne dépend que du pas**, jamais de la taille "
         f"du bloc : l'empreinte le long de `x` vaut {EMPREINTE_X:.1f} mm dans les deux "
         "cas.",
         "- **Raccourcir le MFC agit en largeur.** Le bloc de 55 mm déborde la plaque de "
         "7,5 mm de chaque côté ; le bloc réduit laisse **4,1 mm de chant découvert** de "
         "chaque côté. C'est la raison géométrique, visible directement, du verdict "
         "« le MFC réduit coupe les lobes de bord » (#39).",
         "",
         "## Positions de passe (mm)",
         "",
         "| configuration | pas | passes | recouvrement | centres `x` |",
         "|---|---|---|---|---|"]
    for lib, ly, pas_eff, cs, rec, soude in lignes:
        L.append(f"| {lib} | {pas_eff:.1f} mm | {len(cs)} | {rec:.1f} mm | "
                 + " · ".join(f"{x:.1f}" for x in cs) + " |")
    L += ["",
          "Les deux premières configurations partagent **les mêmes positions** : à pas "
          "égal, seule change l'emprise en largeur. La troisième resserre le pas, ce que "
          "le bloc réduit tolère sans dégrader là où le bloc de 55 mm ne le tolère plus.",
          "",
          "Reproduire : `.venv/bin/python code/scripts/gen/"
          "gen_positions_passes_pas_optimal.py`"]
    SORTIE_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("ecrit :", SORTIE_MD)
    print("ecrit :", SORTIE_FIG)


if __name__ == "__main__":
    main()
