#!/usr/bin/env python3
"""Recalibration JOINTE coin + refroidissement global sur l'essai réel 231 A.

Ajuste ensemble 3 paramètres effectifs du modèle 2D, sur la PASSE 1 (départ froid,
la plus informative) de l'essai 231 A du 26/08 :
  - facteur_couplage  -> échelle de la source (pics intérieurs)
  - h_bas_2d          -> perte globale face inférieure (vitesse de refroidissement)
  - h_bord_x0         -> puits de bord x=0 (pic du COIN, TC1)

Identifiabilité : le pic du coin (TC1=392) fixe h_bord_x0 ; le pic intérieur
(TC2=271) et la PENTE de refroidissement fixent ensemble facteur_couplage et
h_bas_2d (le refroid. ne dépend que des pertes, pas de la source -> lève la
dégénérescence source/perte). La source étant linéaire en facteur_couplage, on
scale P sans recalcul (évaluations rapides).

Ne touche PAS au canonique : imprime les θ* et sauve pour la variante de validation.
"""
from __future__ import annotations
import sys, copy
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import least_squares

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts" / "gen"))
sys.path.insert(0, str(R / "code" / "scripts"))
import gen_cycle_parfait_semistatique as g  # noqa: E402
from jumeau.thermique.solveur2d import SolveurThermique2D  # noqa: E402

FICH = R / "donnees" / "data" / "exp10_cycle-semistatique_231A_2026-08-26" / "231A_semistatique_bord_2026-08-26.txt"
DWELL1 = 77.0     # s — pic TC1 réel (coupe de la passe 1)
T_FIN = 222.0     # s — début de la passe 2 (fin de la fenêtre passe 1)

# --- données réelles passe 1 (recalées sur l'amorçage) ---
df = pd.read_csv(FICH, sep="\t", decimal=",")
df.columns = [c.strip() for c in df.columns]
t = df["Time (s)"].to_numpy(float).copy(); t -= t[0]
S = {f"TC{i}": pd.to_numeric(df[[c for c in df.columns if c.startswith(f'TC{i}')][0]],
                             errors="coerce").to_numpy(float).copy() for i in range(1, 6)}
maxtc = np.nanmax(np.vstack([S[f"TC{i}"] for i in range(1, 6)]), axis=0)
amb0 = np.nanmedian(np.vstack([S[f"TC{i}"][:10] for i in range(1, 6)]))
i0 = int(np.argmax(maxtc > amb0 + 15)); t -= t[i0]
win = (t >= 0) & (t <= T_FIN)
t_r = t[win]
TC1_r, TC2_r = S["TC1"][win], S["TC2"][win]

# --- base modèle (construit UNE fois ; on ne rebâtit que l'Ambiant + on scale P) ---
E = g.construire_essai(231.0)
P0 = E._P_spots_2d[0].copy()
MASQUE0 = E._masques[0]
GR, MAT, CONTACT = E.grille, E.cfg.materiau, E.cfg.contact
AMB_BASE = E.cfg.ambiant
POS = {n: (float(E.spec["thermocouples"][n]["x"]), float(E.spec["thermocouples"][n]["y"])) for n in ("TC1", "TC2")}
T0_FIELD = np.full(GR.nx * GR.ny, g.T_AMB)


def forward(fac, h_bas, h_bord):
    amb = copy.deepcopy(AMB_BASE)
    amb.h_bas_2d = float(h_bas)
    amb.h_bord_x0 = float(h_bord)
    solv = SolveurThermique2D(GR, MAT, amb, CONTACT, masque_ceramique=MASQUE0)
    P = P0 * (fac / g.FACTEUR)
    th = np.arange(0.0, DWELL1 + 0.25, 0.5)
    sol_h = solv.simuler(lambda tt: P, (0.0, DWELL1), t_eval=th, T_initial=T0_FIELD)
    field = sol_h.y[:, -1]
    Dc = T_FIN - DWELL1
    tc = np.arange(0.0, Dc + 0.5, 1.0)
    Pnul = np.zeros_like(P)
    sol_c = solv.simuler(lambda tt: Pnul, (0.0, Dc), t_eval=tc, T_initial=field)
    tt = np.concatenate([sol_h.t, DWELL1 + sol_c.t])
    out = {}
    for n in ("TC1", "TC2"):
        x, y = POS[n]
        s = np.concatenate([solv.serie_temporelle(sol_h, x, y), solv.serie_temporelle(sol_c, x, y)])
        out[n] = np.interp(t_r, tt, s)
    return out


_neval = [0]
W_PIC = 8.0        # poids des résidus de pic (sinon la longue queue de refroid. les noie)

def residus(theta):
    fac, h_bas, h_bord = theta
    m = forward(fac, h_bas, h_bord)
    r_curve = np.concatenate([m["TC1"] - TC1_r, m["TC2"] - TC2_r])
    r_pic = W_PIC * np.array([m["TC1"].max() - 392.0, m["TC2"].max() - 271.0])
    r = np.concatenate([r_curve, r_pic])
    _neval[0] += 1
    rmse = np.sqrt(np.mean(r_curve**2))
    print(f"  eval {_neval[0]:2d}: fac={fac:6.3f} h_bas={h_bas:6.2f} h_bord={h_bord:6.1f} "
          f"| RMSE_courbe={rmse:5.1f}  pics TC1={m['TC1'].max():.0f}(392) TC2={m['TC2'].max():.0f}(271)")
    return r


if __name__ == "__main__":
    x0 = np.array([g.FACTEUR, AMB_BASE.h_bas_2d, 100.0])
    print(f"θ0 (canon + coin) : fac={x0[0]:.4f} h_bas_2d={x0[1]:.3f} h_bord_x0={x0[2]:.0f}")
    print(f"cibles passe 1 : TC1_pic=392  TC2_pic=271  (fenêtre [0,{T_FIN:.0f}]s, dwell {DWELL1:.0f}s)\n")
    sol = least_squares(residus, x0, bounds=([4.0, 20.0, 0.0], [9.0, 130.0, 300.0]),
                        diff_step=0.04, xtol=1e-3, ftol=1e-3, max_nfev=70)
    fac, h_bas, h_bord = sol.x
    m = forward(fac, h_bas, h_bord)
    print("\n=== θ* recalibré (coin + refroidissement global, 231A passe 1) ===")
    print(f"  facteur_couplage : {g.FACTEUR:.4f}  ->  {fac:.4f}")
    print(f"  h_bas_2d         : {AMB_BASE.h_bas_2d:.3f}  ->  {h_bas:.3f}")
    print(f"  h_bord_x0        : 250  ->  {h_bord:.1f}")
    print(f"  RMSE passe1 final : {np.sqrt(np.mean(sol.fun**2)):.1f} °C")
    print(f"  pics modèle : TC1={m['TC1'].max():.0f} (cible 392)  TC2={m['TC2'].max():.0f} (cible 271)")
    np.save(R / "code" / "scripts" / "gen" / "_theta_coin_refroid.npy",
            np.array([fac, h_bas, h_bord]))
    print("  θ* sauvé -> _theta_coin_refroid.npy")
