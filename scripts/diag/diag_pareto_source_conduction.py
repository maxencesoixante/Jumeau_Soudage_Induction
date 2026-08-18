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

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import least_squares

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from _style import apply_style, savefig
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


from calibrer_joint import EssaiCalibre

NX, NY, NZ = 31, 11, 13


def charger_essais(noms, nx=NX, ny=NY, nz=NZ):
    return [EssaiCalibre(n, nx, ny, nz) for n in noms]


def restaurer_facteur(essais_fit, cfg, lambda_bord_mm, facteur0=6.0123, max_nfev=15):
    """Fit 1-D de facteur_couplage minimisant les résidus σ-pondérés du lot."""
    def resid(x):
        f = float(x[0])
        return np.concatenate([e.residus(cfg, f, 0.0, lambda_bord_mm) for e in essais_fit])
    res = least_squares(resid, x0=[facteur0], bounds=([0.5], [30.0]),
                        max_nfev=max_nfev, method="trf")
    return float(res.x[0])


def rmse_pooled(essais, cfg, facteur, lambda_bord_mm):
    """Moyenne des RMSE par-TC (colonne 'rmse' de rapport_essai) sur les essais."""
    vals = []
    for e in essais:
        rap = e.rapport(cfg, facteur, 0.0, lambda_bord_mm)
        vals.extend(rap["rmse"].tolist())
    return float(np.mean(vals))


def classer(contraste, rmse_holdout, rmse_ref, cible=2.08, tol=0.15, marge_quasi=0.7):
    """Classifie un nœud d'après son contraste M et RMSE held-out.

    Retourne:
        'faisable': contraste dans [cible-tol, cible+tol] et RMSE ≤ rmse_ref.
        'quasi': contraste ok mais rmse_ref < RMSE ≤ rmse_ref + marge_quasi.
        'hors': sinon.
    """
    if abs(contraste - cible) > tol:
        return "hors"
    if rmse_holdout <= rmse_ref:
        return "faisable"
    if rmse_holdout <= rmse_ref + marge_quasi:
        return "quasi"
    return "hors"


def verdict(classes):
    """Agrège les classifications (liste de str) en un verdict GO/QUASI-GO/NO-GO.

    Retourne:
        'GO': au moins un nœud 'faisable'.
        'QUASI-GO': au moins un nœud 'quasi' et aucun 'faisable'.
        'NO-GO': tous les nœuds sont 'hors'.
    """
    if "faisable" in classes:
        return "GO"
    if "quasi" in classes:
        return "QUASI-GO"
    return "NO-GO"


LAMBDAS = [0.0, 1.0, 2.0, 3.0, 4.0, 6.0]
K_HOTS = [2.0, 3.0, 4.0, 5.0, 6.0]


def balayer(lambdas=LAMBDAS, k_hots=K_HOTS):
    fit = charger_essais(FIT)
    held = charger_essais(HELDOUT)

    # nœud de référence isotrope -> RMSE_REF
    cfg_ref = _cfg_noeud(k_hot=None)
    f_ref = restaurer_facteur(fit, cfg_ref, 0.0)
    rmse_ref = rmse_pooled(held, cfg_ref, f_ref, 0.0)
    c_ref, _ = contraste_ktlb(f_ref, None, 0.0)
    lignes = [dict(lambda_bord_mm=0.0, k_hot=float("nan"), facteur=f_ref,
                   contraste_M=c_ref, rmse_holdout=rmse_ref, rmse_fit=float("nan"),
                   classe="reference")]
    print(f"[REF] facteur={f_ref:.4f}  contraste={c_ref:.3f}  RMSE_held={rmse_ref:.2f}")

    for lb in lambdas:
        for kh in k_hots:
            cfg = _cfg_noeud(k_hot=kh)
            f = restaurer_facteur(fit, cfg, lb)
            rmse_h = rmse_pooled(held, cfg, f, lb)
            rmse_f = rmse_pooled(fit, cfg, f, lb)
            c, _ = contraste_ktlb(f, kh, lb)
            cls = classer(c, rmse_h, rmse_ref)
            lignes.append(dict(lambda_bord_mm=lb, k_hot=kh, facteur=f,
                               contraste_M=c, rmse_holdout=rmse_h, rmse_fit=rmse_f,
                               classe=cls))
            print(f"  λ={lb:>3} k_hot={kh:>3} | facteur={f:6.3f} "
                  f"contraste={c:5.3f} RMSE_held={rmse_h:6.2f} -> {cls}")
    return pd.DataFrame(lignes)


def tracer_pareto(df, png_path):
    """Nuage contraste_M (x) vs rmse_holdout (y). Couleur=lambda_bord,
    taille=k_hot. Boîte de faisabilité + point de référence tracés."""
    apply_style(**{"font.size": 10, "axes.labelsize": 11})
    ref = df[df["classe"] == "reference"].iloc[0]
    noeuds = df[df["classe"] != "reference"]
    rmse_ref = float(ref["rmse_holdout"])

    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    # boîte de faisabilité : |contraste-2.08|<=0.15 ET rmse<=rmse_ref
    ax.axvspan(2.08 - 0.15, 2.08 + 0.15, color="#009E73", alpha=0.10, zorder=0)
    ax.axhline(rmse_ref, color="#009E73", lw=1.0, ls="--",
               label=f"RMSE réf = {rmse_ref:.1f} °C")
    ax.axhline(rmse_ref + 0.7, color="#E69F00", lw=0.9, ls=":",
               label="seuil quasi (réf + 0,7)")
    sc = ax.scatter(noeuds["contraste_M"], noeuds["rmse_holdout"],
                    c=noeuds["lambda_bord_mm"], s=20 + 14 * noeuds["k_hot"],
                    cmap="viridis", edgecolor="0.2", linewidth=0.4, zorder=5)
    ax.scatter([ref["contraste_M"]], [ref["rmse_holdout"]], marker="*",
               s=240, color="#C1272D", edgecolor="black", zorder=6,
               label="référence isotrope (k=3, λ=0)")
    ax.axvline(2.08, color="0.4", lw=0.8, zorder=1)
    ax.annotate("contraste mesuré 2,08", xy=(2.08, ax.get_ylim()[1]),
                fontsize=8, color="0.4", ha="left", va="top", rotation=90)
    fig.colorbar(sc, ax=ax, label="lambda_bord (mm)")
    ax.set_xlabel("contraste M (exp7 200 A)  —  cible mesurée 2,08")
    ax.set_ylabel("RMSE held-out (°C)  —  exp7_250A + exp9 bord")
    ax.set_title("Faisabilité source × conduction (taille ∝ k_hot)", fontsize=11)
    ax.legend(fontsize=8, loc="best", framealpha=0.9)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    Path(png_path).parent.mkdir(parents=True, exist_ok=True)
    savefig(fig, png_path)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lambdas", type=float, nargs="+", default=LAMBDAS)
    ap.add_argument("--k-hots", type=float, nargs="+", default=K_HOTS)
    ap.add_argument("--csv", default=str(RACINE / "journaux" /
                    "resultats_pareto_source_conduction_2026-08-12.csv"))
    ap.add_argument("--png", default=str(RACINE / "docs" / "modele" / "figures" /
                    "pareto_source_conduction.png"))
    args = ap.parse_args()

    df = balayer(args.lambdas, args.k_hots)
    Path(args.csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.csv, index=False)

    noeuds = df[df["classe"] != "reference"]
    v = verdict(noeuds["classe"].tolist())
    tracer_pareto(df, args.png)  # défini en Task 5
    print(f"\n=== VERDICT : {v} ===")
    print(f"faisables={int((noeuds['classe']=='faisable').sum())} "
          f"quasi={int((noeuds['classe']=='quasi').sum())} "
          f"hors={int((noeuds['classe']=='hors').sum())}")
    print(f"CSV : {args.csv}\nPNG : {args.png}")


if __name__ == "__main__":
    main()
