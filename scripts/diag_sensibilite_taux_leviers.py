#!/usr/bin/env python
"""Diagnostic — sensibilité du TAUX de chauffe (dT/dt) aux leviers candidats,
à théta* de référence FIGÉ (aucune recalibration, aucun fichier config modifié).

Complète (sans répéter) :
  - resultats_diag_taux_chauffe.log : cp/e_eff/lumping déjà ÉCARTÉS comme
    levier du "2x trop lent" (le taux SOUS-SPOT est déjà correct à e_eff =
    stack complet ; réduire e_eff SUR-corrige). Pas re-testé ici.
  - resultats_diag_cp_kplan.log : k_plan déjà identifié comme le seul levier
    qui améliore RMSE+pic ENSEMBLE (mais sur le PIC/RMSE, pas le TAUX
    explicitement ; et k_plan=9 jugé "haut" au regard de l'homogénéisation).
  - resultats_diag_centre_transitoire.log : lissage de source (sigma) déjà
    testé sur la MAGNITUDE du remplissage centre-vs-chant (état matché en
    température), pas sur le TAUX dT/dt initial en régression.

ANGLE NOUVEAU (ce script) : quantifier l'effet de k_plan (dont ~7,3, valeur
identifiée par la calibration jointe bord+centre) et du lissage sigma
directement sur le déficit de TAUX (méthodologie de
diag_taux_dTdt_sous_hors_spot.py : régression 25-75% de la montée mesurée),
sur TOUTES les familles (sous-spot / centre-oeil / hors-spot), y compris
exp9 y=20 (absente des diagnostics précédents, campagne acquise le 2026-07-30).
+ un sweep h_haut (retrait pendant la chauffe) pour trancher si un levier de
PUITS peut fermer un déficit de TAUX (hypothèse : non, un puits RETIRE de
l'énergie nette, il n'accélère pas la MONTÉE hors-spot -- cf. mécanisme
"redistribue vs retire" de resultats_diag_cp_kplan.log §10).

théta* de référence (docs/modele/README.md) : facteur=6.0123, h_haut=30.087,
h_bas_2d=37.424, h_bord_x0=250 -- FIGÉS. Seul le levier testé varie.

Usage : .venv/bin/python scripts/diag_sensibilite_taux_leviers.py
Sortie : table stdout + journaux/resultats_diag_sensibilite_taux_leviers.log
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from jumeau.materiaux import Config
from jumeau.procede import Essai
from jumeau.validation.chargement import charger_mesures, recaler_a_la_chauffe
from diag_taux_dTdt_sous_hors_spot import ESSAIS, fenetre_montee, pente_fenetre

FACTEUR = 6.0123
H_HAUT = 30.087
H_BAS_2D = 37.424
H_BORD_X0 = 250.0

# essais representatifs (une famille de chaque : sous-spot fort, centre-oeil,
# hors-spot longitudinal) -- pas les 5 (cout), mais couvre tous les regimes.
ESSAIS_TEST = ["exp7_200A", "exp9_200A_monospot", "exp9_200A_y20_monospot"]

LEVIERS = [
    ("baseline (k_plan=3.0, config)", dict()),
    ("k_plan=7.3 (identifie, calib jointe)", dict(k_plan=7.3)),
    ("k_plan=9.0 (borne haute cp_kplan.log)", dict(k_plan=9.0)),
    ("source_sigma_mm=6 (centre_transitoire.log)", dict(source_sigma_mm=6.0)),
    ("h_haut x2 (60.17, pendant la chauffe)", dict(h_haut=2 * H_HAUT)),
    ("h_haut /2 (15.04, pendant la chauffe)", dict(h_haut=0.5 * H_HAUT)),
]


def famille(regime: str) -> str:
    if regime.startswith("sous-spot"):
        return "SOUS-SPOT"
    if regime.startswith("centre-oeil"):
        return "CENTRE-OEIL"
    if regime.startswith("hors-spot"):
        return "HORS-SPOT"
    return "LOBE-INTERMEDIAIRE"


def rouler(levier_kwargs: dict) -> pd.DataFrame:
    cfg = Config.charger(RACINE / "config")
    cfg.contact.h_haut = levier_kwargs.get("h_haut", H_HAUT)
    cfg.ambiant.h_bas_2d = H_BAS_2D
    cfg.ambiant.h_bord_x0 = H_BORD_X0
    if "k_plan" in levier_kwargs:
        cfg.materiau.k_plan = levier_kwargs["k_plan"]
    essai_kwargs = {}
    if "source_sigma_mm" in levier_kwargs:
        essai_kwargs["source_sigma_mm"] = levier_kwargs["source_sigma_mm"]

    lignes = []
    for nom in ESSAIS_TEST:
        regimes = ESSAIS[nom]
        chemin = RACINE / "config" / "essais" / f"{nom}.yaml"
        essai = Essai(cfg, chemin, nx=61, ny=21, nz=15,
                      facteur_couplage=FACTEUR, decalage_x=0.0, racine=RACINE,
                      **essai_kwargs)
        solveur, sol = essai.simuler(modele="2D")
        series = essai.series_tc(solveur, sol)
        df = recaler_a_la_chauffe(charger_mesures(essai.fichier_mesures))
        duree = float(essai.spec.get("duree_totale", essai.spec["duree_chauffe"]))
        tcol = df.columns[0]
        df = df[df[tcol] <= duree].reset_index(drop=True)
        t_mes_full = df[tcol].values

        for tc, regime in regimes.items():
            col = next((c for c in df.columns if c.startswith(tc)), None)
            if col is None or tc not in series:
                continue
            T_mes = df[col].values
            t_lo, t_hi = fenetre_montee(t_mes_full, T_mes)
            taux_mes = pente_fenetre(t_mes_full, T_mes, t_lo, t_hi)
            T_sim_interp = np.interp(t_mes_full, sol.t, series[tc])
            taux_sim = pente_fenetre(t_mes_full, T_sim_interp, t_lo, t_hi)
            deficit_pct = (taux_sim - taux_mes) / taux_mes * 100.0 if taux_mes else float("nan")
            lignes.append({
                "essai": nom, "TC": tc, "famille": famille(regime),
                "taux_mes": round(taux_mes, 2), "taux_sim": round(taux_sim, 2),
                "deficit_%": round(deficit_pct, 1),
            })
    return pd.DataFrame(lignes)


def main():
    pd.set_option("display.width", 160)
    resultats = {}
    for nom_levier, kwargs in LEVIERS:
        print(f"\n=== {nom_levier} ===")
        tbl = rouler(kwargs)
        resultats[nom_levier] = tbl
        resume = tbl.groupby("famille")["deficit_%"].mean().round(1)
        print(resume.to_string())

    # tableau de synthese : deficit_% moyen par famille x levier
    synthese = pd.DataFrame({
        nom: resultats[nom].groupby("famille")["deficit_%"].mean().round(1)
        for nom, _ in LEVIERS
    }).T
    print("\n\nSYNTHESE -- déficit % moyen par famille x levier (0 = parfait, <0 = trop lent) :")
    print(synthese.to_string())

    out = RACINE / "journaux" / "resultats_diag_sensibilite_taux_leviers.log"
    with open(out, "w") as f:
        f.write("Diagnostic -- sensibilite du TAUX (dT/dt) aux leviers, theta* fige\n")
        f.write("=" * 78 + "\n")
        f.write(f"Essais testes : {ESSAIS_TEST}\n")
        f.write(f"theta* de reference : facteur={FACTEUR} h_haut={H_HAUT} "
                f"h_bas_2d={H_BAS_2D} h_bord_x0={H_BORD_X0}\n\n")
        for nom_levier, tbl in resultats.items():
            f.write(f"--- {nom_levier} ---\n")
            f.write(tbl.to_string(index=False) + "\n\n")
        f.write("SYNTHESE -- deficit %% moyen par famille x levier :\n")
        f.write(synthese.to_string() + "\n")
    print(f"\n[log ecrit] {out}")


if __name__ == "__main__":
    main()
