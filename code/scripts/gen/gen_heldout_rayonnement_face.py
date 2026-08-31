#!/usr/bin/env python3
"""Held-out du rayonnement de face sur exp7/exp9 — critère d'ADOPTION (issue #68).

Le rayonnement de face (`SolveurThermique2D(emissivite_face=)`, défaut OFF)
améliore le RMSE de cycle sur le 231 A mais NE résout PAS l'accumulation
(résidu structurel k_plan). Reste à décider s'il vaut la peine d'être adopté
comme amélioration MINEURE et INDÉPENDANTE : critère = held-out **neutre ou
meilleur** sur les essais formels exp7/exp9 (θ* canonique, AUCUN recalage).

Balaye emissivite_face ∈ {0.0, 0.6, 0.9} sur les 10 essais exp7/exp9 (modèle 2D,
facteur_couplage=6.0123 canonique) et compare le RMSE moyen par essai.

Ne modifie aucune config par défaut. Sorties :
  biblio/labo/figures/fig_heldout_rayonnement_face.png
  biblio/labo/heldout_rayonnement_face.md
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))
sys.path.insert(0, str(R / "code" / "scripts"))
from jumeau.materiaux import Config  # noqa: E402
from jumeau.procede import Essai  # noqa: E402
from jumeau.validation.chargement import charger_mesures, recaler_a_la_chauffe  # noqa: E402
from jumeau.validation.confrontation import rapport_essai  # noqa: E402
from _style import apply_style, savefig, OKABE_ITO  # noqa: E402

apply_style(**{"savefig.dpi": 200, "figure.dpi": 200})

FACTEUR = 6.0123  # θ* canonique 2D
ESSAIS = ["exp7_150A", "exp7_176A", "exp7_200A", "exp7_225A", "exp7_250A",
          "exp9_175A_monospot", "exp9_200A_monospot", "exp9_200A_y20_monospot",
          "exp9_226A_monospot", "exp9_250A_monospot"]
EMISS = [0.0, 0.6, 0.9]
CONFIG = R / "code" / "config"


def rmse_moyen(nom, emiss):
    cfg = Config.charger(CONFIG)
    essai = Essai(cfg, CONFIG / "essais" / f"{nom}.yaml", nx=61, ny=21, nz=15,
                  facteur_couplage=FACTEUR, decalage_x=0.0, racine=R)
    solveur, sol = essai.simuler(modele="2D", emissivite_face=emiss)
    series = essai.series_tc(solveur, sol)
    df = recaler_a_la_chauffe(charger_mesures(essai.fichier_mesures))
    duree = float(essai.spec.get("duree_totale", essai.spec["duree_chauffe"]))
    tcol = df.columns[0]
    df = df[df[tcol] <= duree].reset_index(drop=True)
    rapport = rapport_essai(series, sol.t, df, essai.spec.get("tc_valides", []))
    return float(rapport["rmse"].mean())


if __name__ == "__main__":
    res = {e: {} for e in EMISS}
    for nom in ESSAIS:
        for e in EMISS:
            res[e][nom] = rmse_moyen(nom, e)
        base = res[0.0][nom]
        print(f"{nom:<26} | " + " | ".join(f"ε={e}:{res[e][nom]:5.1f}" for e in EMISS)
              + f" | Δ(0.9-0)={res[0.9][nom]-base:+.1f}")

    moy = {e: float(np.mean([res[e][n] for n in ESSAIS])) for e in EMISS}
    print("\nRMSE moyen held-out (10 essais) : " + " | ".join(f"ε={e}: {moy[e]:.2f}" for e in EMISS))
    delta = moy[0.9] - moy[0.0]
    verdict = ("ADOPTABLE (held-out neutre/meilleur)" if delta <= 0.3
               else "NON adoptable (held-out régresse)")
    print("VERDICT :", verdict, f"(Δ moyen 0.9-0.0 = {delta:+.2f} °C)")

    # --- figure ---
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(13.0, 5.2))
    x = np.arange(len(ESSAIS)); w = 0.27
    labs = [n.replace("_monospot", "").replace("exp", "e") for n in ESSAIS]
    for k, (e, c) in enumerate(zip(EMISS, ("0.6", OKABE_ITO["orange"], OKABE_ITO["vermillon"]))):
        axA.bar(x + (k - 1) * w, [res[e][n] for n in ESSAIS], w, color=c, label=f"ε_face={e}")
    axA.set_xticks(x); axA.set_xticklabels(labs, rotation=45, ha="right", fontsize=7.0)
    axA.set_ylabel("RMSE moyen par essai (°C)")
    axA.set_title("Held-out exp7/exp9 : RMSE par essai vs rayonnement de face", fontsize=10.5, fontweight="bold")
    axA.legend(loc="upper left", fontsize=8, framealpha=0.93)
    # B : ΔRMSE (ε=0.9 − baseline) par essai
    dvals = [res[0.9][n] - res[0.0][n] for n in ESSAIS]
    cols = [OKABE_ITO["vert"] if d <= 0 else OKABE_ITO["vermillon"] for d in dvals]
    axB.bar(x, dvals, color=cols)
    axB.axhline(0.0, color="0.4", lw=1.0)
    axB.set_xticks(x); axB.set_xticklabels(labs, rotation=45, ha="right", fontsize=7.0)
    axB.set_ylabel("Δ RMSE (ε=0.9 − OFF) [°C]   négatif = amélioration")
    axB.set_title(f"Effet held-out : Δ moyen = {delta:+.2f} °C", fontsize=10.5, fontweight="bold")
    fig.tight_layout()
    savefig(fig, R / "biblio" / "labo" / "figures" / "fig_heldout_rayonnement_face")
    plt.close(fig)

    # --- markdown ---
    md = ["# Held-out du rayonnement de face — exp7/exp9 (issue #68, critère d'adoption)\n"]
    md.append("Critère d'adoption du flag `SolveurThermique2D(emissivite_face=)` : held-out "
              "**neutre ou meilleur** sur les 10 essais formels exp7/exp9 (modèle 2D, "
              "`facteur_couplage=6.0123` canonique, **aucun recalage**). Script : "
              "`code/scripts/gen/gen_heldout_rayonnement_face.py`.\n")
    md.append("| essai | RMSE ε=0.0 (OFF) | RMSE ε=0.6 | RMSE ε=0.9 | Δ (0.9−OFF) |")
    md.append("|---|---:|---:|---:|---:|")
    for nom in ESSAIS:
        b = res[0.0][nom]
        md.append(f"| {nom} | {b:.1f} | {res[0.6][nom]:.1f} | {res[0.9][nom]:.1f} | {res[0.9][nom]-b:+.1f} |")
    md.append(f"| **MOYENNE** | **{moy[0.0]:.2f}** | **{moy[0.6]:.2f}** | **{moy[0.9]:.2f}** | **{delta:+.2f}** |")
    md.append("")
    md.append(f"## Verdict : {verdict}\n")
    md.append(f"RMSE moyen held-out : {moy[0.0]:.2f} (OFF) → {moy[0.9]:.2f} (ε=0.9), "
              f"Δ = **{delta:+.2f} °C**. " +
              ("Le rayonnement de face est **neutre/positif en held-out** : ajout physique propre "
               "(défaut OFF bit-à-bit) adoptable comme amélioration mineure indépendante — décision "
               "d'activation par défaut à trancher (garder OFF par prudence, ou passer un défaut "
               "> 0 documenté).\n"
               if delta <= 0.3 else
               "Le rayonnement de face **régresse le held-out** : NE PAS adopter par défaut ; garder "
               "le flag à 0.0 (OFF). L'amélioration vue sur le 231 A ne généralise pas.\n"))
    (R / "biblio" / "labo" / "heldout_rayonnement_face.md").write_text("\n".join(md), encoding="utf-8")
    print("figure -> biblio/labo/figures/fig_heldout_rayonnement_face.png")
    print("md     -> biblio/labo/heldout_rayonnement_face.md")
