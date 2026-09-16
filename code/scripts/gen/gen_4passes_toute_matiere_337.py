"""Que faut-il pour que TOUTE la matière dépasse 337 °C en quatre passes ?

La séquence de référence (4 passes au pas de 30 mm, MFC réduit, 235 A, 20 s)
n'amène aucun point de la largeur à la fusion. La question posée est donc : à
quel réglage y arrive-t-on, et à quel prix ?

RÉPONSE COURTE : on y arrive, et le prix est la plaque. Un balayage conjoint
courant × durée (200-250 A, 30-150 s) donne le résultat suivant — aucun réglage
n'amène 100 % de l'interface au-dessus de 337 °C sans en porter ~98 % au-delà du
seuil de dégradation. Le moins destructeur trouvé est 200 A / 120 s, et il
dégrade encore 98,4 %.

LA RAISON est géométrique, pas énergétique. Le point le plus froid de la plaque
et le plus chaud sont dans un rapport d'environ 3, et ce rapport ne descend pas
en chauffant plus : monter la puissance monte les deux ensemble. Le point froid
vient de deux endroits que la source n'atteint pas — le centre de la largeur, qui
est la ligne nodale de la dissipation, et les extrémités en longueur, au-delà de
la première et de la dernière passe. Tant que ce rapport reste au-dessus de
450/337 = 1,33, il n'existe aucune fenêtre où tout fond sans que rien ne brûle.

Cette figure montre donc les deux choses à la fois : la séquence au réglage qui
atteint la consigne, et la courbe qui dit pourquoi ce réglage est le seul et ce
qu'il coûte.

Sortie : biblio/modele/figures/fig_4passes_toute_matiere_337.png
"""
from __future__ import annotations

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
from _style import apply_style, savefig, OKABE_ITO                 # noqa: E402
from jumeau.materiaux import Config                                 # noqa: E402
from jumeau.planification.planificateur import (                    # noqa: E402
    verifier_sequentiel, metriques)
from jumeau.thermique.dose_degradation import metriques_dose      # noqa: E402

apply_style(**{"font.size": 9.5, "axes.titlesize": 10.5})

SORTIE = R / "biblio" / "modele" / "figures" / "fig_4passes_toute_matiere_337.png"
NOTE = R / "biblio" / "modele" / "4passes_toute_matiere_337.md"
FUSION, DEGRAD = 337.0, 450.0
CENTRES = [0.015875, 0.045875, 0.075875, 0.105875]      # pas 30 mm, procédé réel
Y_C, MFC_REDUIT, FAMILLE = 0.020, 0.03175, "conserver"
COURANT, DUREE = 200.0, 120.0                           # réglage qui atteint la consigne
DUREES_BALAYAGE = [20.0, 30.0, 45.0, 60.0, 75.0, 90.0, 120.0, 150.0]


def passes(n: int, courant: float, duree: float) -> list[dict]:
    return [{"x_c": x, "y_c": Y_C, "courant": courant,
             "mfc_longueur": MFC_REDUIT, "duree": duree} for x in CENTRES[:n]]


# Carte TERNAIRE plutôt que continue : à ce réglage tout dépasse le seuil de
# dégradation, et une échelle continue saturée ne montrait plus rien. Les trois
# états — froid / fondu / dégradé — sont ce que la question demande de lire.
ETATS = ListedColormap(["#D9E8F5", "#B7E4C7", "#F4C7C3"])
BORNES = BoundaryNorm([-1e9, FUSION, DEGRAD, 1e9], ETATS.N)
LEGENDE = [Patch(facecolor="#D9E8F5", edgecolor="0.5",
                 label=f"sous {FUSION:.0f} °C — pas soudé"),
           Patch(facecolor="#B7E4C7", edgecolor="0.5",
                 label=f"entre {FUSION:.0f} et {DEGRAD:.0f} °C — soudé"),
           Patch(facecolor="#F4C7C3", edgecolor="0.5",
                 label=f"au-dessus de {DEGRAD:.0f} °C — dégradé")]


def carte(ax, grille, T, n, m) -> None:
    x_mm, y_mm = grille.x * 1e3, grille.y * 1e3
    ax.pcolormesh(x_mm, y_mm, T.T, cmap=ETATS, norm=BORNES, shading="auto")
    ax.contour(x_mm, y_mm, T.T, levels=[FUSION], colors="0.25", linewidths=1.1)
    if T.max() > DEGRAD:
        ax.contour(x_mm, y_mm, T.T, levels=[DEGRAD], colors="#C1272D",
                   linewidths=1.3, linestyles="--")
    for k, x in enumerate(CENTRES[:n], 1):
        ax.plot(x * 1e3, Y_C * 1e3, "o", ms=6, mfc="none", mec="0.2", mew=1.5)
        ax.annotate(str(k), (x * 1e3, Y_C * 1e3), textcoords="offset points",
                    xytext=(0, 9), ha="center", fontsize=8.5, color="0.2",
                    fontweight="bold")
    # titre COURT : les titres longs se chevauchaient d'un panneau à l'autre
    ax.set_title(f"{n} passe{'s' if n > 1 else ''}  —  soudé {m['pct_soude']:.1f} %  ·  "
                 f"dégradé {m['pct_degrade']:.1f} %")
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.set_aspect("equal")        # 120 x 40 mm : ne pas laisser matplotlib etirer


def main() -> None:
    cfg = Config.charger(R / "code" / "config")

    etapes = []
    for n in (1, 2, 3, 4):
        g, T, tt, ch = verifier_sequentiel(cfg, passes(n, COURANT, DUREE),
                                           famille=FAMILLE, retour_historique=True)
        m = metriques_dose(ch, tt, fusion=FUSION)
        etapes.append((n, g, T, m))
        print(f"  {n} passe(s) : >=337 sur {m['pct_soude'] + m['pct_degrade']:5.1f} %  "
              f"dégradé {m['pct_degrade']:5.1f} %  "
              f"Tmin {T.min():5.1f}  Tmax {T.max():6.1f} °C", flush=True)

    au_dessus, degrade = [], []
    for d in DUREES_BALAYAGE:
        _, T, tt, ch = verifier_sequentiel(cfg, passes(4, COURANT, d),
                                           famille=FAMILLE, retour_historique=True)
        m = metriques_dose(ch, tt, fusion=FUSION)
        au_dessus.append(m["pct_soude"] + m["pct_degrade"])
        degrade.append(m["pct_degrade"])
        print(f"  durée {d:5.1f} s : >=337 sur {au_dessus[-1]:5.1f} %  "
              f"dégradé {degrade[-1]:5.1f} %", flush=True)

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(11.2, 8.2))
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 1.15], hspace=0.55, wspace=0.18)
    axes_cartes = []
    for idx, (n, g, T, m) in enumerate(etapes):
        a = fig.add_subplot(gs[idx // 2, idx % 2])
        carte(a, g, T, n, m)
        axes_cartes.append(a)
    axes_cartes[1].legend(handles=LEGENDE, loc="upper left",
                          bbox_to_anchor=(1.02, 1.0), fontsize=9, frameon=False)

    ax = fig.add_subplot(gs[2, :])
    ax.plot(DUREES_BALAYAGE, au_dessus, "o-", lw=2.0, ms=5,
            color=OKABE_ITO["vermillon"], label="matière au-dessus de 337 °C (fondue)")
    ax.plot(DUREES_BALAYAGE, degrade, "o-", lw=2.0, ms=5,
            color=OKABE_ITO["cyan"], label="matière au-dessus de 450 °C (dégradée)")
    ax.axvline(DUREE, color="0.45", lw=1.1, ls="--")
    ax.annotate(f"réglage de la figure\n{COURANT:.0f} A · {DUREE:.0f} s",
                xy=(DUREE, 50), xytext=(-8, 0), textcoords="offset points",
                ha="right", va="center", fontsize=9, color="0.3")
    ax.set_xlabel(f"durée par passe (s), à {COURANT:.0f} A")
    ax.set_ylabel("fraction de l'interface (%)")
    ax.set_title("Les deux seuils sont franchis presque ensemble : "
                 "il n'y a pas de fenêtre entre les deux")
    ax.set_ylim(-3, 105)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.24), fontsize=9,
              ncol=2, frameon=False)

    fig.suptitle("Quatre passes au MFC réduit 31,75 mm (hypothèse A), réglées pour "
                 f"que toute la matière dépasse 337 °C — {COURANT:.0f} A, "
                 f"{DUREE:.0f} s par passe", y=0.985)
    savefig(fig, SORTIE)
    plt.close(fig)

    # Note ECRITE PAR CE SCRIPT (cf. gen_sequence_4passes : une prose ajoutee a la
    # main dans une note generee voisine disparait a la regeneration suivante).
    L = [f"# Faire dépasser {FUSION:.0f} °C à toute la matière en quatre passes, "
         "et ce que ça coûte",
         "",
         f"Généré le {date.today().isoformat()}. MFC réduit 31,75 mm, hypothèse la "
         f"plus favorable, pas de 30 mm, {COURANT:.0f} A, {DUREE:.0f} s par passe.",
         "",
         f"![Quatre passes](figures/{SORTIE.name})",
         "",
         "| après | au-dessus de 337 °C | dégradé | T min | T max |",
         "|---|---|---|---|---|",
         *[f"| {n} passe{'s' if n > 1 else ''} | "
           f"{m['pct_soude'] + m['pct_degrade']:.1f} % | {m['pct_degrade']:.1f} % | "
           f"{T.min():.0f} °C | {T.max():.0f} °C |" for n, _, T, m in etapes],
         "",
         f"### Balayage de la durée de passe, à {COURANT:.0f} A",
         "",
         "| durée par passe | > 337 °C | dégradé |",
         "|---|---|---|",
         *[f"| {d:.0f} s | {a:.1f} % | {dg:.1f} % |"
           for d, a, dg in zip(DUREES_BALAYAGE, au_dessus, degrade)],
         "",
         "**La contrainte est géométrique, pas énergétique.** Le point le plus froid et "
         "le plus chaud sont dans un rapport d'environ 3, et ce rapport ne descend pas "
         "quand on chauffe plus : monter la puissance monte les deux ensemble. Le froid "
         "vient de deux endroits que la source n'atteint pas — le centre de la largeur, "
         "ligne nodale de la dissipation, et les extrémités en longueur au-delà des "
         "passes extrêmes.",
         "",
         "La dégradation est jugée en **temps × température** "
         "(`jumeau.thermique.dose_degradation`), pas au seuil de pic — ce qui change "
         "le verdict des maintiens longs.",
         "",
         "Reproduire : `.venv/bin/python code/scripts/gen/"
         "gen_4passes_toute_matiere_337.py`"]
    NOTE.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("ecrit :", NOTE)
    print("ecrit :", SORTIE)


if __name__ == "__main__":
    main()
