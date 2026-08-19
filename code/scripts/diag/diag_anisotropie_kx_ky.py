#!/usr/bin/env python
"""Diagnostic ANISOTROPIE kx/ky (mission thermal-solver-engineer 2026-07-31).

Contexte : dernier levier identifié pour le résidu du profil « M »/centre-fill
(cf. docs/modele/README.md § État & résidu ouvert, option A) -- kx != ky
(materiaux.Materiau.k_plan_x/k_plan_y, thermique/solveur2d.py) au lieu du
k_plan SCALAIRE. Ce script :

1. calcule le contraste du profil M (moyenne des pics normalisés aux chants
   y=0/40mm sur le pic centre y=20mm, exp7_200A -- même recette que
   scripts/gen/gen_figures_elsevier.py::fig2) pour un theta donné (isotrope ou
   anisotrope) ;
2. reproduit la vérification de MULTIMODALITÉ de ky : le fit joint anisotrope
   sans contrainte (scripts/calibrer_joint.py --anisotrope) pousse ky vers sa
   borne basse (2.0) -- ce script refait le fit avec ky >= 3.0 (= k_plan
   isotrope de référence) pour voir si l'optimiseur "veut" vraiment un ky plus
   haut (rapprochant le contraste de 2,09 mesuré) à un coût RMSE comparable,
   ou si c'est un optimum franchement pire.

RÉSULTAT (2026-07-31, logs journaux/archive/resultats_calibration_joint_anisotrope*.log) :
il existe DEUX optima locaux à ~3 % d'écart de coût :
  - ky libre (borne basse 2.0, PINNED) : kx=7.52, ky=2.03 -> RMSE global 17.8°C
    (bat la référence 18.5°C) MAIS contraste M 3.63 (PIRE que la référence
    isotrope 3.15, cible mesurée 2.09 -- s'éloigne).
  - ky >= 3.0 forcé : kx=7.39, ky=5.72 -> contraste M 2.50 (se rapproche de
    2.09, mieux que la référence) MAIS RMSE global 18.8°C (PIRE que la
    référence 18.5°C -- même échec que le fit joint scalaire k_plan de
    2026-07-30, RMSE 19.2°C).
Aucun des deux ne bat SIMULTANÉMENT le RMSE ET ne rapproche le contraste sans
casser la famille bord (TC2/TC3/TC4, lobes intermédiaires) -> anisotropie
kx/ky NON ADOPTÉE (cf. rapport thermal-solver-engineer 2026-07-31). kx seul
confirme (redondant) le kx~7.3-7.5 déjà identifié par le fit scalaire k_plan
joint du 2026-07-30 -- ce n'est pas une découverte nouvelle, c'est ky qui
échoue à concilier les deux familles, exactement comme k_plan scalaire avant
lui.

Usage :
    python scripts/diag/diag_anisotropie_kx_ky.py --contraste --facteur 6.0123 \\
        --h-bas-2d 37.424 --h-bord-x0 250.0 --k-plan 3.0
    python scripts/diag/diag_anisotropie_kx_ky.py --contraste --facteur 6.9013 \\
        --h-bas-2d 87.064 --h-bord-x0 77.51 --kx 7.515 --ky 2.0258
    python scripts/diag/diag_anisotropie_kx_ky.py --verif-ky-borne --ky-min 3.0 \\
        --n-lhs 4 --max-nfev 30
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

RACINE = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(RACINE / "code" / "src"))
sys.path.insert(0, str(RACINE / "code" / "scripts"))

H_HAUT_FIGE = 30.087


def contraste_m(facteur: float, h_bas_2d: float, h_bord_x0: float,
                kx: float | None = None, ky: float | None = None,
                k_plan: float | None = None, nx=41, ny=15, nz=9):
    """Contraste du profil M (exp7_200A) : moyenne des pics normalisés aux
    chants (y=0/40mm) sur le pic centre (y=20mm) -- recette de
    gen_figures_elsevier.py::fig2, factorisée ici pour être rejouable."""
    from jumeau.materiaux import Config
    from jumeau.procede import Essai

    cfg = Config.charger(RACINE / "code" / "config")
    cfg.contact.h_haut = H_HAUT_FIGE
    cfg.ambiant.h_bas_2d = h_bas_2d
    cfg.ambiant.h_bord_x0 = h_bord_x0
    if kx is not None:
        cfg.materiau.k_plan_x = kx
        cfg.materiau.k_plan_y = ky
    else:
        cfg.materiau.k_plan = k_plan

    e = Essai(cfg, RACINE / "code" / "config" / "essais" / "exp7_200A.yaml", nx=nx, ny=ny, nz=nz,
              facteur_couplage=facteur, decalage_x=0.0, racine=RACINE)
    sv, sol = e.simuler(modele="2D")
    mod = np.array([sv.serie_temporelle(sol, 0.060, y, "interface").max()
                    for y in (0.0, 0.010, 0.020, 0.030, 0.040)])
    amb_m = float(sv.serie_temporelle(sol, 0.060, 0.020, "interface")[0])
    profil = (mod - amb_m) / (mod[2] - amb_m)
    contraste = (profil[0] + profil[4]) / 2
    return contraste, profil


def verif_ky_borne(ky_min: float, n_lhs: int, max_nfev: int, seed: int = 1,
                   essais=("exp7_200A", "exp7_150A", "exp7_250A", "exp9_200A_y20_monospot")):
    """Refait le fit joint anisotrope avec ky >= ky_min (au lieu de 2.0) --
    teste si l'optimum ky=2.0 (borne basse) du fit libre est un artefact de
    borne ou un vrai minimum global (cf. docstring module)."""
    from calibrer_joint import EssaiCalibre, CalibrateurJoint

    essais_obj = [EssaiCalibre(n, 31, 11, 13) for n in essais]
    calib = CalibrateurJoint(essais_obj, anisotrope=True,
                             bornes_basses=(0.5, 2.0, 2.0, ky_min, 50.0),
                             bornes_hautes=(30.0, 300.0, 12.0, 12.0, 400.0))
    print(f"Bornes basses forcées : {calib.bornes[0].tolist()}")
    print(f"Bornes hautes : {calib.bornes[1].tolist()}")
    resultat = calib.calibrer(n_lhs=n_lhs, max_nfev=max_nfev, seed=seed)
    print(f"\n=== θ*_new (ky >= {ky_min} forcé) ===")
    for i, nom in enumerate(calib.noms):
        se = resultat["erreurs_std"].get(nom, float("nan"))
        print(f"  {nom} = {resultat['theta'][i]:.5g} ± {se:.3g}")
    print(f"Coût final : {resultat['cout']:.1f} | succès : {resultat['succes']} "
          f"| message : {resultat['message']}")
    return resultat


def principale():
    ap = argparse.ArgumentParser()
    ap.add_argument("--contraste", action="store_true")
    ap.add_argument("--verif-ky-borne", action="store_true")
    ap.add_argument("--facteur", type=float, default=6.0123)
    ap.add_argument("--h-bas-2d", type=float, default=37.424)
    ap.add_argument("--h-bord-x0", type=float, default=250.0)
    ap.add_argument("--kx", type=float, default=None)
    ap.add_argument("--ky", type=float, default=None)
    ap.add_argument("--k-plan", type=float, default=3.0)
    ap.add_argument("--ky-min", type=float, default=3.0)
    ap.add_argument("--n-lhs", type=int, default=4)
    ap.add_argument("--max-nfev", type=int, default=30)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    if args.contraste:
        c, profil = contraste_m(args.facteur, args.h_bas_2d, args.h_bord_x0,
                                args.kx, args.ky, args.k_plan)
        print(f"contraste = {c:.3f}")
        print(f"profil normalisé (y=0,10,20,30,40mm) = {np.round(profil, 3).tolist()}")
    if args.verif_ky_borne:
        verif_ky_borne(args.ky_min, args.n_lhs, args.max_nfev, args.seed)
    if not args.contraste and not args.verif_ky_borne:
        ap.print_help()


if __name__ == "__main__":
    principale()
