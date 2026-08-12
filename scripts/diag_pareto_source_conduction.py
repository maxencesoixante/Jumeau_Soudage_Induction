#!/usr/bin/env python
"""Carte de faisabilité SOURCE × CONDUCTION (réouverture du résidu in-plane).

Étape C de la séquence C→A (cf. docs/superpowers/specs/2026-08-12-pareto-
source-conduction-design.md). Balaie lambda_bord_mm × k_hot (k_cold figé),
restaure facteur_couplage par nœud, mesure contraste M + RMSE held-out, et
imprime un verdict GO/QUASI-GO/NO-GO. Diagnostic pur : ne modifie ni config,
ni flags, ni θ*. N'écrit que son CSV et son PNG.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from jumeau.materiaux import Config
from jumeau.procede import Essai

H_HAUT_FIGE = 30.087
H_BAS_2D_FIGE = 37.424
H_BORD_X0_FIGE = 250.0
K_COLD_FIGE = 7.5
KT_T_LO, KT_T_HI = 20.0, 340.0
K_PLAN_REF = 3.0

FIT = ("exp7_150A", "exp7_200A", "exp9_200A_y20_monospot")
HELDOUT = ("exp7_250A", "exp9_200A_monospot")
CONTRASTE_ESSAI = "exp7_200A"


def _cfg_noeud(k_hot: float | None, k_cold: float = K_COLD_FIGE) -> Config:
    """Config canonique + conduction du nœud. k_hot None => isotrope k_plan=3."""
    cfg = Config.charger(RACINE / "config")
    cfg.contact.h_haut = H_HAUT_FIGE
    cfg.ambiant.h_bas_2d = H_BAS_2D_FIGE
    cfg.ambiant.h_bord_x0 = H_BORD_X0_FIGE
    cfg.materiau.k_plan_x = cfg.materiau.k_plan_y = None
    if k_hot is None:
        cfg.materiau.k_plan_T = None
        cfg.materiau.k_plan = K_PLAN_REF
    else:
        cfg.materiau.k_plan_T = [[KT_T_LO, float(k_cold)], [KT_T_HI, float(k_hot)]]
    return cfg


def contraste_ktlb(facteur: float, k_hot: float | None, lambda_bord_mm: float,
                   k_cold: float = K_COLD_FIGE, nx=41, ny=15, nz=9):
    """Contraste du profil M (exp7_200A) — recette gen_figures_elsevier::fig2 /
    diag_anisotropie_kx_ky.contraste_m, étendue à k(T) + lambda_bord."""
    cfg = _cfg_noeud(k_hot, k_cold)
    e = Essai(cfg, RACINE / "config" / "essais" / f"{CONTRASTE_ESSAI}.yaml",
              nx=nx, ny=ny, nz=nz, facteur_couplage=facteur, decalage_x=0.0,
              racine=RACINE, lambda_bord_mm=lambda_bord_mm)
    sv, sol = e.simuler(modele="2D")
    mod = np.array([sv.serie_temporelle(sol, 0.060, y, "interface").max()
                    for y in (0.0, 0.010, 0.020, 0.030, 0.040)])
    amb = float(sv.serie_temporelle(sol, 0.060, 0.020, "interface")[0])
    profil = (mod - amb) / (mod[2] - amb)
    return float((profil[0] + profil[4]) / 2), profil
