"""Existe-t-il un pas entre passes qui soude la plaque sans la brûler ?

D'où vient la question. Au pas du procédé réel (30 mm) rien n'atteint la fusion ;
au pas de 15 mm la couverture quadruple mais le centre dépasse le seuil de
dégradation avant que les chants n'atteignent la fusion
(`biblio/modele/plan_passes_familles.md`). La contrainte a changé de camp entre
les deux, donc un optimum est possible entre les deux — ou bien la fenêtre est
vide, ce qui serait un résultat aussi utile.

Ce que le balayage fait. L'étendue est FIXE (premier et dernier centre = ceux du
procédé semi-statique réel) ; seul le NOMBRE d'intervalles varie, ce qui donne
les pas réalisables 90/n mm. Tout le reste est tenu constant : courant, durée par
passe, position en largeur. Trois configurations sont balayées en parallèle, pour
que la réponse ne dépende pas d'une hypothèse de MFC :

  - MFC réduit sous l'hypothèse FAVORABLE (famille A, le flux se reconcentre) ;
  - MFC réduit sous l'hypothèse CORROBORÉE (famille B, pas de reconcentration) ;
  - MFC labo 55 mm, le point de comparaison.

Attention à la lecture. Resserrer le pas AJOUTE des passes, donc de l'énergie :
la courbe répond à « que donne tel pas ? », pas à « à énergie égale ». Et le
seuil de dégradation est appliqué à une interface calculée avec la config
canonique, qui surestime au-delà du point de fusion : un pas déclaré « sans
dégradation » l'est donc à coup sûr, alors qu'un pas déclaré dégradant peut ne
pas l'être. Le critère est conservateur dans le bon sens.

Sorties : biblio/modele/balayage_pas_mfc_reduit.md
          biblio/modele/figures/fig_balayage_pas_mfc_reduit.png
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))
sys.path.insert(0, str(R / "code" / "scripts"))
from _style import apply_style, savefig, OKABE_ITO                 # noqa: E402
from jumeau.materiaux import Config                                 # noqa: E402
from jumeau.planification.planificateur import (                    # noqa: E402
    verifier_sequentiel, metriques)

apply_style(**{"font.size": 10, "axes.titlesize": 11})

SORTIE_MD = R / "biblio" / "modele" / "balayage_pas_mfc_reduit.md"
SORTIE_FIG = R / "biblio" / "modele" / "figures" / "fig_balayage_pas_mfc_reduit.png"

FUSION, DEGRAD = 337.0, 450.0
X_PREMIER, X_DERNIER = 0.015875, 0.105875
Y_C, COURANT, DUREE = 0.020, 235.0, 20.0
MFC_REDUIT = 0.03175
N_INTERVALLES = range(2, 15)                 # pas = 90/n mm, de 45 a 6,4 mm

CONFIGS = [
    ("MFC réduit — hypothèse favorable (A)", MFC_REDUIT, "conserver",
     OKABE_ITO["vermillon"]),
    ("MFC réduit — hypothèse corroborée (B)", MFC_REDUIT, "image_observation",
     OKABE_ITO["vert"]),
    ("MFC labo 55 mm", None, "conserver", OKABE_ITO["bleu"]),
]


def sequence(n_int: int, mfc):
    xs = [X_PREMIER + k * (X_DERNIER - X_PREMIER) / n_int for k in range(n_int + 1)]
    return [{"x_c": x, "y_c": Y_C, "courant": COURANT,
             "mfc_longueur": mfc, "duree": DUREE} for x in xs]


def main() -> None:
    cfg = Config.charger(R / "code" / "config")
    span_mm = (X_DERNIER - X_PREMIER) * 1e3
    pas = [span_mm / n for n in N_INTERVALLES]
    npasses = [n + 1 for n in N_INTERVALLES]

    resultats = {}
    for nom, mfc, famille, _ in CONFIGS:
        soude, degrade = [], []
        for n in N_INTERVALLES:
            _, T = verifier_sequentiel(cfg, sequence(n, mfc), famille=famille)
            m = metriques(T, fusion=FUSION, degrad=DEGRAD)
            soude.append(m["pct_soude"])
            degrade.append(m["pct_degrade"])
            print(f"  {nom:40s} pas {span_mm / n:5.1f} mm ({n + 1:2d} passes) : "
                  f"soudé {m['pct_soude']:5.1f} %  dégradé {m['pct_degrade']:5.1f} %",
                  flush=True)
        resultats[nom] = (np.array(soude), np.array(degrade))

    # « pas parfait » = celui qui soude le plus SANS AUCUNE dégradation.
    optima = {}
    for nom, (soude, degrade) in resultats.items():
        propres = np.flatnonzero(degrade == 0.0)
        if propres.size:
            i = propres[int(np.argmax(soude[propres]))]
            optima[nom] = (pas[i], npasses[i], soude[i], degrade[i], True)
        else:
            i = int(np.argmax(soude - degrade))
            optima[nom] = (pas[i], npasses[i], soude[i], degrade[i], False)

    SORTIE_FIG.parent.mkdir(parents=True, exist_ok=True)
    fig, (ax_s, ax_d) = plt.subplots(1, 2, figsize=(11.4, 4.6))
    for nom, mfc, famille, couleur in CONFIGS:
        soude, degrade = resultats[nom]
        ax_s.plot(pas, soude, "o-", ms=4.5, lw=1.8, color=couleur, label=nom)
        ax_d.plot(pas, degrade, "o-", ms=4.5, lw=1.8, color=couleur, label=nom)
        p_opt, n_opt, s_opt, _, propre = optima[nom]
        if propre:
            ax_s.plot([p_opt], [s_opt], "*", ms=15, color=couleur,
                      mec="0.2", mew=0.6, zorder=5)
    ax_s.set_ylabel("interface soudée (%)")
    ax_d.set_ylabel("interface dégradée (%)")
    ax_s.set_title("Ce qui se soude")
    ax_d.set_title("Ce qui brûle")
    for ax in (ax_s, ax_d):
        ax.set_xlabel("pas entre passes (mm)")
        ax.invert_xaxis()                    # pas serré à droite = sens de lecture
        ax.grid(alpha=0.25)
    ax_d.axhline(0.0, color="0.4", lw=1.0, ls="--")
    ax_s.annotate("★ = pas le plus couvrant\nsans aucune dégradation",
                  xy=(0.03, 0.96), xycoords="axes fraction", va="top", fontsize=9,
                  color="0.25")
    # légende SOUS les deux panneaux : dans le cadre, elle recouvrait les courbes
    poignees, etiquettes = ax_s.get_legend_handles_labels()
    fig.legend(poignees, etiquettes, loc="upper center", bbox_to_anchor=(0.5, 0.055),
               ncol=3, fontsize=9.5, frameon=False)
    fig.subplots_adjust(bottom=0.26)
    fig.suptitle("Pas entre passes : la couverture et la brûlure montent ensemble "
                 f"({COURANT:.0f} A, {DUREE:.0f} s par passe, étendue fixe)", y=0.99)
    savefig(fig, SORTIE_FIG)
    plt.close(fig)

    L = [
        "# Y a-t-il un pas entre passes qui soude sans brûler ?",
        "",
        f"Généré le {date.today().isoformat()}. Étendue fixe "
        f"(`x` = {X_PREMIER * 1e3:.1f} → {X_DERNIER * 1e3:.1f} mm, celle du procédé "
        f"semi-statique réel), spot centré en largeur, {COURANT:.0f} A, "
        f"{DUREE:.0f} s par passe. Seul le pas varie — donc le nombre de passes, "
        "donc l'énergie déposée.",
        "",
        f"![Balayage du pas](figures/{SORTIE_FIG.name})",
        "",
        "## Le pas le plus couvrant sans aucune dégradation",
        "",
        "| configuration | pas | passes | soudé | dégradé |",
        "|---|---|---|---|---|",
    ]
    for nom, _, _, _ in CONFIGS:
        p_opt, n_opt, s_opt, d_opt, propre = optima[nom]
        marque = "" if propre else " *(aucun pas sans dégradation — meilleur compromis)*"
        L.append(f"| {nom}{marque} | {p_opt:.1f} mm | {n_opt} | {s_opt:.1f} % | "
                 f"{d_opt:.1f} % |")
    L += ["", "## Le balayage complet", "",
          "| pas (mm) | passes | " + " | ".join(f"{n} — soudé / dégradé"
                                                for n, _, _, _ in CONFIGS) + " |",
          "|---|---|" + "---|" * len(CONFIGS)]
    for i, (p_mm, npa) in enumerate(zip(pas, npasses)):
        cells = " | ".join(f"{resultats[n][0][i]:.1f} % / {resultats[n][1][i]:.1f} %"
                           for n, _, _, _ in CONFIGS)
        L.append(f"| {p_mm:.1f} | {npa} | {cells} |")
    L += [
        "",
        "## Réserves",
        "",
        "- **Ce n'est pas une comparaison à énergie égale.** Resserrer le pas "
        "ajoute des passes : le pas le plus serré du tableau dépose plusieurs fois "
        "l'énergie du plus large.",
        "- **Le critère de dégradation est conservateur.** Le seuil est appliqué à "
        "une interface calculée avec la config canonique (chaleur latente 130 J/g, "
        "sans plateau de fusion), qui surestime au-delà du point de fusion — 865 "
        "contre 508 °C sur le cycle 231 A. Un pas déclaré sans dégradation l'est "
        "donc à coup sûr ; un pas déclaré dégradant peut ne pas l'être.",
        "- **Le résidu structurel du jumeau joue dans le sens conservateur** pour la "
        "couverture : le centre du modèle se remplit trop lentement, donc la "
        "couverture réelle devrait être un peu meilleure que celle calculée.",
        "- Aucune des hypothèses de MFC réduit n'est de la physique établie ; c'est "
        "la campagne #55 qui dira laquelle décrit le concentrateur réel.",
        "",
        "Reproduire : `.venv/bin/python code/scripts/gen/gen_balayage_pas_mfc_reduit.py`",
    ]
    SORTIE_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("ecrit :", SORTIE_MD)
    print("ecrit :", SORTIE_FIG)


if __name__ == "__main__":
    main()
