"""Les quatre passes du procédé, avec le MFC réduit, dans l'hypothèse la plus
FAVORABLE des quatre.

CE QUE CETTE FIGURE MONTRE — et ce qu'elle ne montre pas. L'hypothèse retenue
ici ("conserver", famille A) est celle où le flux qui n'est plus sous le bloc de
ferrite SE RECONCENTRE sous le bloc restant, à puissance Joule totale conservée.
C'est la seule des quatre où le MFC réduit produit un point chaud déplaçable, et
donc la seule qui vaille la peine d'être regardée pass par passe.

Ce n'est PAS l'hypothèse la mieux étayée. Les deux variantes de la famille B --
qui tronquent la même physique de deux façons duales, l'une côté observateur,
l'autre côté source -- s'accordent entre elles (contraste 2,49 et 2,62) alors que
la famille A est l'intrus (1,03) : cf. `biblio/modele/prediction_mfc_familles.md`.
Deux troncatures indépendantes qui tombent d'accord pèsent plus qu'une
redistribution postulée. Cette figure est donc une BORNE OPTIMISTE : ce que le
MFC réduit ferait au mieux, pas ce qu'on prédit qu'il fera.

Géométrie des passes : les quatre dwells du procédé semi-statique réel (pas de
30 mm, x = 15,9 / 45,9 / 75,9 / 105,9 mm -- mêmes centres que
`gen_procede_semistatique.py`), spot centré en largeur (y = 20 mm), là où le MFC
réduit est censé servir.

Sortie : biblio/modele/figures/fig_sequence_4passes_mfc_reduit.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))
sys.path.insert(0, str(R / "code" / "scripts"))
from _style import apply_style, savefig, OKABE_ITO                # noqa: E402
from jumeau.materiaux import Config                                # noqa: E402
from jumeau.planification.empreinte import empreinte               # noqa: E402
from jumeau.planification.planificateur import (                   # noqa: E402
    verifier_sequentiel, metriques)

apply_style(**{"font.size": 9.5, "axes.titlesize": 10.5})

SORTIE = R / "biblio" / "modele" / "figures" / "fig_sequence_4passes_mfc_reduit.png"
FUSION, DEGRAD = 337.0, 450.0
CENTRES = [0.015875, 0.045875, 0.075875, 0.105875]   # pas 30 mm, procédé réel
Y_C = 0.020                                          # centré en largeur
COURANT, DUREE = 235.0, 20.0
MFC_REDUIT = 0.03175
FAMILLE = "conserver"


def passes(n: int) -> list[dict]:
    return [{"x_c": x, "y_c": Y_C, "courant": COURANT,
             "mfc_longueur": MFC_REDUIT, "duree": DUREE} for x in CENTRES[:n]]


def carte(ax, grille, T, n, m) -> None:
    x_mm, y_mm = grille.x * 1e3, grille.y * 1e3
    im = ax.pcolormesh(x_mm, y_mm, T.T, cmap="inferno", vmin=20.0, vmax=DEGRAD,
                       shading="auto")
    ax.contour(x_mm, y_mm, T.T, levels=[FUSION], colors="white", linewidths=1.3)
    if T.max() > DEGRAD:
        ax.contour(x_mm, y_mm, T.T, levels=[DEGRAD], colors=OKABE_ITO["cyan"],
                   linewidths=1.2, linestyles="--")
    for k, x in enumerate(CENTRES[:n], 1):
        ax.plot(x * 1e3, Y_C * 1e3, "o", ms=6, mfc="none",
                mec=OKABE_ITO["cyan"], mew=1.7)
        ax.annotate(str(k), (x * 1e3, Y_C * 1e3), textcoords="offset points",
                    xytext=(0, 9), ha="center", fontsize=8.5,
                    color=OKABE_ITO["cyan"], fontweight="bold")
    ax.set_title(f"après {n} passe{'s' if n > 1 else ''}  —  "
                 f"soudé {m['pct_soude']:.1f} %  ·  dégradé {m['pct_degrade']:.1f} %")
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.set_aspect("equal")      # 120 x 40 mm : ne pas laisser matplotlib etirer
    return im


def main() -> None:
    cfg = Config.charger(R / "code" / "config")
    etapes = []
    for n in (1, 2, 3, 4):
        g, T = verifier_sequentiel(cfg, passes(n), famille=FAMILLE)
        m = metriques(T, fusion=FUSION, degrad=DEGRAD)
        etapes.append((n, g, T, m))
        print(f"  {n} passe(s) : soudé {m['pct_soude']:5.1f} %  "
              f"dégradé {m['pct_degrade']:5.1f} %  Tmax {T.max():6.1f} °C", flush=True)

    # contrepoint : les mêmes quatre passes au MFC labo, et sous la famille B
    g4, T_labo = verifier_sequentiel(
        cfg, [{**p, "mfc_longueur": None} for p in passes(4)], famille=FAMILLE)
    _, T_bobs = verifier_sequentiel(cfg, passes(4), famille="image_observation")
    m_labo = metriques(T_labo, fusion=FUSION, degrad=DEGRAD)
    m_bobs = metriques(T_bobs, fusion=FUSION, degrad=DEGRAD)
    print(f"  MFC labo 55 mm      : soudé {m_labo['pct_soude']:5.1f} %  "
          f"dégradé {m_labo['pct_degrade']:5.1f} %")
    print(f"  MFC réduit famille B : soudé {m_bobs['pct_soude']:5.1f} %  "
          f"dégradé {m_bobs['pct_degrade']:5.1f} %")

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(11.2, 8.2))
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 1.15], hspace=0.55, wspace=0.18)
    for idx, (n, g, T, m) in enumerate(etapes):
        im = carte(fig.add_subplot(gs[idx // 2, idx % 2]), g, T, n, m)

    ax = fig.add_subplot(gs[2, :])
    y_mm = etapes[-1][1].y * 1e3
    i_x = int(np.argmin(np.abs(etapes[-1][1].x - CENTRES[2])))   # coupe sous la passe 3
    ax.plot(y_mm, etapes[-1][2][i_x, :], "-", lw=2.0, color=OKABE_ITO["vermillon"],
            label=f"MFC réduit 31,75 mm — hypothèse favorable (A)")
    ax.plot(y_mm, T_bobs[i_x, :], "-", lw=1.8, color=OKABE_ITO["vert"],
            label="MFC réduit 31,75 mm — hypothèse corroborée (B)")
    ax.plot(y_mm, T_labo[i_x, :], "-", lw=1.8, color=OKABE_ITO["bleu"],
            label="MFC labo 55 mm")
    # seuils annotés A DROITE : la zone haute-gauche accueille la légende
    ax.axhline(FUSION, color="0.35", lw=1.1, ls="--")
    ax.annotate(f"fusion {FUSION:.0f} °C", (39.4, FUSION), textcoords="offset points",
                xytext=(0, 5), fontsize=8.5, color="0.35", ha="right")
    ax.axhline(DEGRAD, color=OKABE_ITO["cyan"], lw=1.1, ls=":")
    ax.annotate(f"dégradation {DEGRAD:.0f} °C", (39.4, DEGRAD), textcoords="offset points",
                xytext=(0, 5), fontsize=8.5, color=OKABE_ITO["cyan"], ha="right")
    ax.set_xlabel("y — largeur (mm)")
    ax.set_ylabel("pic de température\nd'interface (°C)")
    ax.set_title("Profil en largeur après les 4 passes, sous la passe 3")
    ax.set_xlim(0, 40)
    ax.set_ylim(180, 500)
    # légende SOUS le cadre : au-dessus elle recouvrait les courbes et les seuils
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.24), fontsize=9,
              ncol=3, frameon=False)

    fig.colorbar(im, ax=fig.axes[:4], label="pic de température d'interface (°C)",
                 fraction=0.028, pad=0.02)
    fig.suptitle("Quatre passes au MFC réduit 31,75 mm — hypothèse la plus favorable "
                 "(le flux se reconcentre)\n"
                 f"trait plein : fusion {FUSION:.0f} °C   ·   "
                 f"tireté : dégradation {DEGRAD:.0f} °C", y=0.985)
    savefig(fig, SORTIE)
    plt.close(fig)
    print("ecrit :", SORTIE)


if __name__ == "__main__":
    main()
