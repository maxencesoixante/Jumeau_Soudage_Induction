#!/usr/bin/env python
"""Issue #74 — meilleur compromis de facteur_couplage, avec et sans k_z réduit
sous l'interface.

Question : réduire le k_z du laminé inférieur (transport transverse ralenti)
dégrade-t-il le MEILLEUR compromis atteignable entre les séries A/B et exp9 ?
À facteur égal, il aggrave exp9 ; mais le 3D non calibré avait déjà une tension
(exp9 trop chaud, A/B trop froid). On compare donc les optimums, pas un point.

Lit les sorties de valider.py dans resultats/compromis/<config>_f<facteur>.log
(grille 31×11×15), et calcule pour chaque (config, facteur) :
  - RMSE_AB  : RMSE moyen des TC intérieurs TC2–TC4 sur A-1, A-3, B-2 ;
  - RMSE_exp9: RMSE moyen du TC3 (interface, à l'aplomb du spot) sur les 5 exp9 ;
  - coût     : moyenne des deux (familles à poids égal).
Les TC de coin (TC1/TC5, peu fiables aux bords x) et les TC froids d'exp9 loin
du spot sont exclus : ils dilueraient ou fausseraient la comparaison.

Sorties : resultats/compromis/synthese.csv, biblio/labo/figures/issue74/fig74_compromis_facteur.png
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts"))
sys.path.insert(0, str(R / "code" / "scripts" / "gen"))
from gen_figures_issue74 import lire_log  # noqa: E402  (même lecteur que les figures #74)
from _style import OKABE_ITO, GRIS_MODELE, savefig  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

D = R / "resultats" / "compromis"
AB = ["serieA_A-1", "serieA_A-3", "serieB_B-2"]
EXP9 = ["exp9_175A_monospot", "exp9_200A_monospot", "exp9_200A_y20_monospot",
        "exp9_226A_monospot", "exp9_250A_monospot"]
CONFIGS = {"actuel": ("k_z uniforme 0,64 · h_contact 5", GRIS_MODELE),
           "kzinf": ("k_z inférieur 0,10 · h_contact 40", OKABE_ITO["bleu"]),
           "rcfusion": ("résistance d'interface jusqu'à la fusion 0,04 · h_contact 40", OKABE_ITO["vermillon"]),
           "combiA": ("combinaison k_z inf 0,25 + résistance 0,02", OKABE_ITO["vert"]),
           "combiB": ("combinaison k_z inf 0,15 + résistance 0,01", OKABE_ITO["rose"])}


def rmse_par_tc(chemin):
    """{essai: {TC: rmse}} (lire_log ne garde que delta_T_max)."""
    res, cur = {}, None
    for ligne in chemin.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"=== (\S+) \[3D\] ===", ligne)
        if m:
            cur = m.group(1); res[cur] = {}; continue
        m = re.match(r"(TC\d)\s+([-\d.]+)\s", ligne)
        if m and cur:
            res[cur][m.group(1)] = float(m.group(2))
    return res


def main(configs=("actuel", "kzinf", "rcfusion"), nom_fig="fig74_compromis_facteur.png"):
    """``configs`` : configurations tracées (toutes sont écrites dans synthese.csv)."""
    lignes = ["config,facteur,rmse_AB_TC2-4,rmse_exp9_TC3,cout,ecart_pic_AB_TC2-4,ecart_pic_exp9_TC3"]
    donnees = {c: [] for c in CONFIGS}
    for chemin in sorted(D.glob("*_f*.log")):
        m = re.match(r"(\w+)_f([\d.]+)\.log", chemin.name)
        if not m or m.group(1) not in CONFIGS:
            continue
        cfg, f = m.group(1), float(m.group(2))
        r, pics = rmse_par_tc(chemin), lire_log(chemin)
        if not all(e in r for e in AB + EXP9):
            print(f"incomplet : {chemin.name}"); continue
        rab = np.mean([r[e][k] for e in AB for k in ("TC2", "TC3", "TC4") if k in r[e]])
        rex = np.mean([r[e]["TC3"] for e in EXP9])
        pab = np.mean([pics[e][1][k] for e in AB for k in ("TC2", "TC3", "TC4") if k in pics[e][1]])
        pex = np.mean([pics[e][1]["TC3"] for e in EXP9])
        donnees[cfg].append((f, rab, rex, 0.5 * (rab + rex), pab, pex))
        lignes.append(f"{cfg},{f},{rab:.1f},{rex:.1f},{0.5 * (rab + rex):.1f},{pab:.1f},{pex:.1f}")
    (D / "synthese.csv").write_text("\n".join(lignes) + "\n", encoding="utf-8")
    print("\n".join(lignes))
    for cfg, v in donnees.items():
        if v:
            best = min(v, key=lambda x: x[3])
            print(f"optimum {cfg} : facteur {best[0]}  coût {best[3]:.1f}  "
                  f"(A/B {best[1]:.1f}, exp9 {best[2]:.1f})")

    fig, axes = plt.subplots(1, 3, figsize=(8.4, 2.9), sharex=True, gridspec_kw=dict(wspace=0.32))
    for cfg, (lab, c) in CONFIGS.items():
        if cfg not in configs:
            continue
        v = sorted(donnees[cfg])
        if not v:
            continue
        f = [x[0] for x in v]
        for ax, j in zip(axes, (1, 2, 3)):
            ax.plot(f, [x[j] for x in v], "o-", color=c, lw=1.5, ms=4, label=lab)
        b = min(v, key=lambda x: x[3])
        axes[2].plot(b[0], b[3], "*", color=c, ms=13, mec="k", mew=0.6, zorder=5)
    for ax, t in zip(axes, ("A/B : TC2–TC4", "exp9 : TC3", "coût joint (moyenne)")):
        ax.set_title(t)
        ax.set_xlabel("facteur_couplage")
    axes[0].set_ylabel("RMSE (°C)")
    h, l = axes[0].get_legend_handles_labels()
    rangs = -(-len(h) // 3)
    fig.legend(h, l, frameon=False, fontsize=7.8, loc="upper center", ncol=3,
               bbox_to_anchor=(0.5, -0.06 - 0.0 * rangs))
    fig.suptitle("Balayage de facteur_couplage, grille 3D 31×11×15 (étoiles : optimum du coût joint)",
                 fontsize=8.8, y=1.03)
    savefig(fig, R / "biblio" / "labo" / "figures" / "issue74" / nom_fig,
            bbox_inches="tight")


if __name__ == "__main__":
    main()
    main(configs=("actuel", "kzinf", "rcfusion", "combiA", "combiB"),
         nom_fig="fig74_compromis_combinaison.png")
