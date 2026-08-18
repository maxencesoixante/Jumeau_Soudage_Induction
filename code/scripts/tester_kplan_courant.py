"""Test d'indépendance de k_plan au courant (modèle 2D).

Sur la série exp9 y=0 monospot (spot fixe x=60, ligne de bord), à 4 courants
(175/200/226/250 A), on ajuste UNIQUEMENT k_plan par courant — tous les autres
paramètres figés à θ* (défaut = θ*_consolidé du fit joint 2026-08-14). L'objectif
est de vérifier si le k_plan identifié dépend du courant.

CIBLE DU FIT = profil longitudinal NORMALISÉ au spot (ΔT_pic(TC_i) ÷ ΔT_pic(TC3)),
et NON l'absolu : chaque essai est coupé manuellement au même pic ~270-285 °C
(cf. READMEs exp9), donc l'amplitude est bridée et ne trace pas la loi I². La
forme longitudinale, elle, ne dépend que de la conduction in-plane (k_plan) et est
insensible au facteur d'amplitude — c'est l'observable propre pour isoler k_plan.

k_plan pilote l'étalement : plus il est grand, plus le profil normalisé est LARGE
(TC2/TC4 et TC1/TC5 remontent). σ(k_plan) est estimé depuis le jacobien du résidu
réduit (cov = s²·(JᵀJ)⁻¹, s² = 2·coût/ddl), même convention que
CalibrateurJoint._incertitudes.

Usage :
    python scripts/tester_kplan_courant.py
    python scripts/tester_kplan_courant.py --facteur 6.0123 --h-bas-2d 37.424 --h-bord-x0 250
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

RACINE = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(RACINE / "code" / "src"))
sys.path.insert(0, str(RACINE / "code" / "scripts"))

from calibrer_joint import EssaiCalibre  # réutilise le préchargement essai/mesures  # noqa: E402
from jumeau.materiaux import Config  # noqa: E402

# θ* consolidé (fit joint 2026-08-14) — valeurs par défaut des paramètres FIGÉS.
FACTEUR_DEF, HBAS_DEF, HBORD_DEF = 6.5518, 68.841, 50.638
H_HAUT_FIGE = 30.087
GRILLE = dict(nx=31, ny=11, nz=13)
COURANTS = [
    (175, "exp9_175A_monospot"),
    (200, "exp9_200A_monospot"),
    (226, "exp9_226A_monospot"),
    (250, "exp9_250A_monospot"),
]


def profil_normalise_mesure(ess: EssaiCalibre) -> dict[str, float]:
    """ΔT au pic (max - ligne de base), normalisé par TC3 (spot)."""
    prof = {}
    for tc in ess.tc_valides:
        col = ess.colonnes[tc]
        v = ess.df[col].to_numpy()
        base = float(np.median(v[:3]))
        prof[tc] = float(np.max(v)) - base
    ref = prof["TC3"]
    return {tc: prof[tc] / ref for tc in ess.tc_valides}


def profil_normalise_sim(series: dict[str, np.ndarray], tc_valides) -> dict[str, float]:
    prof = {}
    for tc in tc_valides:
        s = np.asarray(series[tc])
        prof[tc] = float(np.max(s)) - float(s[0])  # s[0] = ambiant (état initial)
    ref = prof["TC3"]
    return {tc: prof[tc] / ref for tc in tc_valides}


def ajuster_kplan(ess: EssaiCalibre, facteur, h_bas_2d, h_bord_x0):
    """Ajuste k_plan (1 paramètre) sur le profil normalisé ; renvoie (k, sigma, rmse_forme)."""
    cible = profil_normalise_mesure(ess)
    tcs_off = [tc for tc in ess.tc_valides if tc != "TC3"]  # TC3=1 par construction

    cfg = Config.charger(RACINE / "code" / "config")
    cfg.contact.h_haut = H_HAUT_FIGE
    cfg.ambiant.h_bas_2d = float(h_bas_2d)
    cfg.ambiant.h_bord_x0 = float(h_bord_x0)

    def residu(theta):
        cfg.materiau.k_plan = float(theta[0])
        _, _, _, series = ess.simuler(cfg, facteur, 0.0, 0.0)
        prof = profil_normalise_sim(series, ess.tc_valides)
        return np.array([prof[tc] - cible[tc] for tc in tcs_off])

    res = least_squares(residu, [8.0], bounds=([1.0], [15.0]),
                        xtol=1e-4, ftol=1e-4, diff_step=0.05, max_nfev=40)
    k = float(res.x[0])
    r = res.fun
    dof = max(len(r) - 1, 1)
    s2 = 2.0 * float(res.cost) / dof
    JTJ = float((res.jac.T @ res.jac).ravel()[0])
    sigma = float(np.sqrt(s2 / JTJ)) if JTJ > 0 else float("nan")
    rmse_forme = float(np.sqrt(np.mean(r ** 2)))
    return k, sigma, rmse_forme, cible


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--facteur", type=float, default=FACTEUR_DEF)
    ap.add_argument("--h-bas-2d", type=float, default=HBAS_DEF)
    ap.add_argument("--h-bord-x0", type=float, default=HBORD_DEF)
    args = ap.parse_args()

    print(f"Paramètres FIGÉS : facteur={args.facteur} h_bas_2d={args.h_bas_2d} "
          f"h_bord_x0={args.h_bord_x0} h_haut={H_HAUT_FIGE}")
    print("Fit : k_plan seul, cible = profil longitudinal normalisé au spot.\n")

    resultats = []
    for I, nom in COURANTS:
        ess = EssaiCalibre(nom, **GRILLE)
        k, sigma, rmse, cible = ajuster_kplan(ess, args.facteur, args.h_bas_2d, args.h_bord_x0)
        prof_str = " / ".join(f"{cible[tc]:.3f}" for tc in ess.tc_valides)
        print(f"  {I} A ({nom}) : k_plan = {k:.3f} ± {sigma:.3f}  "
              f"(RMSE forme={rmse:.4f} ; profil mes normalisé {prof_str})")
        resultats.append((I, k, sigma))

    ks = np.array([k for _, k, _ in resultats])
    sig = np.array([s for _, _, s in resultats])
    # moyenne pondérée par 1/σ² + test de compatibilité (χ² à une constante)
    w = 1.0 / np.clip(sig, 1e-6, None) ** 2
    k_moy = float(np.sum(w * ks) / np.sum(w))
    sig_moy = float(np.sqrt(1.0 / np.sum(w)))
    chi2 = float(np.sum(((ks - k_moy) / np.clip(sig, 1e-6, None)) ** 2))
    ddl = len(ks) - 1
    print(f"\n  k_plan moyen (pondéré) = {k_moy:.3f} ± {sig_moy:.3f}")
    print(f"  Test de constance : χ²={chi2:.2f} pour {ddl} ddl (χ²/ddl={chi2/ddl:.2f})")
    verdict = ("COMPATIBLE avec un k_plan constant" if chi2 / ddl < 3.0
               else "k_plan DÉPEND du courant (dispersion > bruit)")
    print(f"  Verdict : {verdict}")

    # export CSV pour la figure
    out = RACINE / "donnees" / "journaux" / "resultats_kplan_courant_2026-08-14.csv"
    with open(out, "w") as f:
        f.write("courant_A,k_plan,sigma\n")
        for I, k, s in resultats:
            f.write(f"{I},{k:.4f},{s:.4f}\n")
        f.write(f"# k_moy={k_moy:.4f} sig_moy={sig_moy:.4f} chi2={chi2:.4f} ddl={ddl}\n")
    print(f"\n  CSV -> {out}")


if __name__ == "__main__":
    main()
