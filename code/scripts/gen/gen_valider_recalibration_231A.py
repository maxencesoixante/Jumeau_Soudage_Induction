#!/usr/bin/env python3
"""Validation de la recalibration jointe (coin + refroidissement global) sur le
cycle complet 231 A, PILOTÉ PAR LES TEMPS RÉELS de l'essai.

On rejoue les 4 passes en imposant les fenêtres de chauffe/refroidissement
MESURÉES (starts + dwells extraits des courbes), pour comparer température à
température sans ambiguïté de pilotage. Trois modèles superposés au mesuré :
  - canonique (fac=6.0123, h_bas_2d=37.4, h_bord_x0=250) — ancien résultat CONSERVÉ
  - recalibré (θ* de calibrer_coin_refroid_231A.py : coin + refroid. global)

Sortie : biblio/labo/figures/fig_valider_recalibration_231A.png
"""
from __future__ import annotations
import sys, copy
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts" / "gen"))
sys.path.insert(0, str(R / "code" / "scripts"))
import gen_cycle_parfait_semistatique as g  # noqa: E402
from jumeau.thermique.solveur2d import SolveurThermique2D  # noqa: E402
from _style import savefig, OKABE_ITO  # noqa: E402

FICH = R / "donnees" / "data" / "exp10_cycle-semistatique_231A_2026-08-26" / "231A_semistatique_bord_2026-08-26.txt"
COUL = [OKABE_ITO[c] for c in ("noir", "bleu", "vert", "orange", "vermillon")]
NOMS = [f"TC{i}" for i in range(1, 6)]

# --- données réelles ---
df = pd.read_csv(FICH, sep="\t", decimal=",")
df.columns = [c.strip() for c in df.columns]
t = df["Time (s)"].to_numpy(float).copy(); t -= t[0]
S = {n: pd.to_numeric(df[[c for c in df.columns if c.startswith(n)][0]], errors="coerce").to_numpy(float).copy()
     for n in NOMS}
maxtc = np.nanmax(np.vstack([S[n] for n in NOMS]), axis=0)
AMB = float(np.nanmedian(np.vstack([S[n][:10] for n in NOMS])))
i0 = int(np.argmax(maxtc > AMB + 15)); t -= t[i0]
m0 = t >= 0
t = t[m0]; S = {n: S[n][m0] for n in NOMS}
maxtc = maxtc[m0]

# --- fenêtres de passe RÉELLES : pics des TC de contrôle puis vallée précédente ---
PIC_APPROX = [77.0, 332.0, 567.0, 843.0]
starts, dwells = [], []
for tpk in PIC_APPROX:
    w = (t >= tpk - 160) & (t <= tpk)
    tstart = t[w][int(np.argmin(maxtc[w]))]
    starts.append(float(tstart)); dwells.append(float(tpk - tstart))
gaps = [starts[i + 1] - (starts[i] + dwells[i]) for i in range(3)] + [t[-1] - (starts[3] + dwells[3])]
print("fenêtres réelles :", [f"P{i+1}: start={starts[i]:.0f} dwell={dwells[i]:.0f} gap={gaps[i]:.0f}" for i in range(4)])

# --- base modèle ---
E = g.construire_essai(231.0)
GR, MAT, CONTACT = E.grille, E.cfg.materiau, E.cfg.contact
AMB_BASE = E.cfg.ambiant
POS = {n: (float(E.spec["thermocouples"][n]["x"]), float(E.spec["thermocouples"][n]["y"])) for n in NOMS}


def cycle_reel_timing(fac, h_bas, h_bord, t_amb):
    amb = copy.deepcopy(AMB_BASE)
    amb.h_bas_2d = float(h_bas); amb.h_bord_x0 = float(h_bord); amb.T_amb = float(t_amb)
    field = np.full(GR.nx * GR.ny, float(t_amb))
    T_out = {n: [] for n in NOMS}; t_out = []
    t0 = 0.0
    for i in range(4):
        P = E._P_spots_2d[i] * (fac / g.FACTEUR)
        Pnul = np.zeros_like(P)
        solv = SolveurThermique2D(GR, MAT, amb, CONTACT, masque_ceramique=E._masques[i])
        # chauffe (t_eval strictement dans le span, dernier point = dwell exact)
        th = np.append(np.arange(0.0, dwells[i], 0.5), dwells[i])
        sh = solv.simuler(lambda tt: P, (0.0, dwells[i]), t_eval=th, T_initial=field)
        field = sh.y[:, -1]
        # refroid.
        tc = np.append(np.arange(0.0, gaps[i], 1.0), gaps[i])
        sc = solv.simuler(lambda tt: Pnul, (0.0, gaps[i]), t_eval=tc, T_initial=field)
        field = sc.y[:, -1]
        for (sol, off) in ((sh, 0.0), (sc, dwells[i])):
            for n in NOMS:
                x, y = POS[n]
                T_out[n].append(solv.serie_temporelle(sol, x, y))
            t_out.append(t0 + off + sol.t)
        t0 += dwells[i] + gaps[i]
    t_all = np.concatenate(t_out)
    return t_all, {n: np.concatenate(T_out[n]) for n in NOMS}


THETA = np.load(R / "code" / "scripts" / "gen" / "_theta_coin_refroid.npy")
fac_r, hbas_r, hbord_r = [float(v) for v in THETA]
print(f"θ* recalibré : fac={fac_r:.4f} h_bas_2d={hbas_r:.2f} h_bord_x0={hbord_r:.1f}")

t_can, S_can = cycle_reel_timing(g.FACTEUR, AMB_BASE.h_bas_2d, 250.0, AMB)   # canonique (ancien)
t_rec, S_rec = cycle_reel_timing(fac_r, hbas_r, hbord_r, AMB)                 # recalibré

# --- figure ---
fig, ax = plt.subplots(figsize=(12.0, 5.6))
for n, c in zip(NOMS, COUL):
    ax.plot(t, S[n], color=c, lw=1.7, alpha=0.9, label=f"{n} mesuré")
    ax.plot(t_rec, S_rec[n], color=c, lw=1.3, ls=(0, (4, 1.8)), label=f"{n} recalibré")
ax.plot(t_can, S_can["TC1"], color="0.55", lw=1.0, ls=(0, (1, 1.5)), label="TC1 canonique (ancien)", zorder=2)
ax.axhline(390, color=OKABE_ITO["vert"], lw=0.8, ls="--"); ax.axhline(337, color=OKABE_ITO["cyan"], lw=0.8, ls=":")
ax.set_xlim(0, t[-1]); ax.set_ylim(0, 560)
ax.set_xlabel("Temps (s) — pilotage par les temps RÉELS de l'essai")
ax.set_ylabel("Température (°C)")
ax.set_title("Recalibration jointe coin + refroid. global — validation cycle 231 A (temps réels)",
             fontsize=12, fontweight="bold")
ax.legend(loc="upper right", ncol=2, fontsize=7.0, framealpha=0.93)
fig.tight_layout()
savefig(fig, R / "biblio" / "labo" / "figures" / "fig_valider_recalibration_231A")
plt.close(fig)

# --- métriques : RMSE plein cycle sur la fenêtre commune, TC1..TC4 (TC5 = artefact x=L) ---
tmax = min(t[-1], t_rec[-1])
gr = np.linspace(0, tmax, 600)
print("\n=== RMSE plein cycle (canonique -> recalibré) & pics ===")
print(f"{'TC':>4} | {'RMSE can':>8} | {'RMSE rec':>8} | {'pic mes':>7} | {'pic can':>7} | {'pic rec':>7}")
for n in NOMS:
    sm = np.interp(gr, t, S[n])
    rc = np.interp(gr, t_can, S_can[n]); rr = np.interp(gr, t_rec, S_rec[n])
    ok = ~np.isnan(sm)
    rmse_c = np.sqrt(np.mean((rc[ok] - sm[ok])**2)); rmse_r = np.sqrt(np.mean((rr[ok] - sm[ok])**2))
    print(f"{n:>4} | {rmse_c:8.1f} | {rmse_r:8.1f} | {np.nanmax(S[n]):7.0f} | "
          f"{S_can[n].max():7.0f} | {S_rec[n].max():7.0f}")
print("figure -> biblio/labo/figures/fig_valider_recalibration_231A.png")
