#!/usr/bin/env python
"""Diagnostic : k_plan(T) DÉCROISSANT ferme-t-il SIMULTANÉMENT le contraste du
« M » (exp7) et le déficit d'étalement hors-spot (exp9 centre) ?

Hypothèse (cf. docs/modele/README.md §résidu unifié + docs/modele/audit_lionetto_2017.md) :
le résidu structurel = un k_plan SCALAIRE ne peut être à la fois BAS sous le spot
(chaud) et HAUT hors-spot (froid). Un k_plan(T) décroissant donne exactement ce
champ non scalaire : k bas là où c'est chaud (lobes du M, sous-spot), k haut là
où c'est froid (creux central, extrémités longitudinales). On teste 3 configs à
θ* de référence FIGÉ (aucune recalibration) :
  - ref  : k_plan = 3,0 (constant, référence documentée)
  - kT   : k_plan(T) = 7,3→3,0 décroissant (borné par le k≈7,3 identifié en
           calibration jointe côté froid, le 3,0 config côté chaud) — HYPOTHÈSE
           de forme, à confirmer par Mesure 9 (k_plan(T) mesuré)
  - k73  : k_plan = 7,3 (constant) — témoin : un scalaire haut sur-étale le pic

Métriques : pic ΔT par TC, contraste chant/centre (exp7), profil longitudinal
(exp9), RMSE par TC vs mesure. AUCUNE adoption : diagnostic pur.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from calibrer_joint import EssaiCalibre, H_HAUT_FIGE  # noqa: E402
from jumeau.materiaux import Config  # noqa: E402

FACTEUR = 6.0123
KT_CURVE = [[20.0, 7.3], [150.0, 6.0], [250.0, 4.0], [340.0, 3.0]]
AMB = 20.0


def make_cfg(kind: str) -> Config:
    cfg = Config.charger(RACINE / "config")
    cfg.contact.h_haut = H_HAUT_FIGE
    cfg.ambiant.h_bas_2d = 37.424
    cfg.ambiant.h_bord_x0 = 250.0
    cfg.materiau.k_plan = 3.0
    cfg.materiau.k_plan_x = cfg.materiau.k_plan_y = None
    cfg.materiau.k_plan_T = cfg.materiau.k_z_T = None
    if kind == "kT":
        cfg.materiau.k_plan_T = [list(p) for p in KT_CURVE]
    elif kind == "k73":
        cfg.materiau.k_plan = 7.3
    return cfg


def eval_essai(e: EssaiCalibre, cfg: Config):
    _, _, sol, series = e.simuler(cfg, FACTEUR, 0.0)
    peaks, rmse = {}, {}
    for tc in e.tc_valides:
        peaks[tc] = float(np.max(series[tc]) - AMB)
        T_sim = np.interp(e.t_mes, sol.t, series[tc])
        T_mes = e.df[e.colonnes[tc]].values
        rmse[tc] = float(np.sqrt(np.mean((T_sim - T_mes) ** 2)))
    return peaks, rmse


def mesure_peaks(e: EssaiCalibre) -> dict:
    out = {}
    for tc in e.tc_valides:
        v = e.df[e.colonnes[tc]].values
        out[tc] = float(np.max(v) - v[0])
    return out


def contraste(peaks: dict) -> float:
    """chant/centre = moyenne(TC1,TC5) / TC3 (y=0/40 vs y=20)."""
    return 0.5 * (peaks["TC1"] + peaks["TC5"]) / peaks["TC3"]


def main():
    configs = {k: make_cfg(k) for k in ("ref", "kT", "k73")}

    print("=" * 78)
    print("EXP7 — profil « M » en largeur (contraste chant/centre)")
    print("=" * 78)
    for nom in ("exp7_150A", "exp7_200A", "exp7_250A"):
        e = EssaiCalibre(nom, 31, 11, 13)
        mp = mesure_peaks(e)
        print(f"\n--- {nom} ---  (mesuré : contraste={contraste(mp):.2f}, "
              f"pics ΔT TC1..5 = {[round(mp[f'TC{i}']) for i in range(1, 6)]})")
        rows = []
        for kind, cfg in configs.items():
            pk, rm = eval_essai(e, cfg)
            rows.append({
                "config": kind,
                **{f"pic_TC{i}": round(pk[f"TC{i}"]) for i in range(1, 6)},
                "contraste": round(contraste(pk), 2),
                "RMSE_moy": round(np.mean(list(rm.values())), 1),
            })
        print(pd.DataFrame(rows).to_string(index=False))

    print("\n" + "=" * 78)
    print("EXP9 — profil longitudinal (déficit d'étalement hors-spot)")
    print("=" * 78)
    for nom, libelle in (("exp9_200A_y20_monospot", "CENTRE y=20 (conduction pure — LE test)"),
                         ("exp9_200A_monospot", "BORD y=0 (source dominante — garde-fou)")):
        e = EssaiCalibre(nom, 31, 11, 13)
        mp = mesure_peaks(e)
        # profil normalisé au spot (TC3, x=60)
        print(f"\n--- {nom} : {libelle} ---")
        print(f"  mesuré  pic ΔT TC1..5 = {[round(mp[f'TC{i}']) for i in range(1, 6)]}  "
              f"(norm./spot = {[round(mp[f'TC{i}']/mp['TC3'], 2) for i in range(1, 6)]})")
        rows = []
        for kind, cfg in configs.items():
            pk, rm = eval_essai(e, cfg)
            spot = pk["TC3"]
            rows.append({
                "config": kind,
                **{f"TC{i}_norm": round(pk[f"TC{i}"] / spot, 2) for i in range(1, 6)},
                "pic_spot": round(spot),
                "RMSE_moy": round(np.mean(list(rm.values())), 1),
            })
        print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
