#!/usr/bin/env python3
"""Modèle de fusion physique : L_f physique (~40 J/g, cristallinité ~30 %) + transport
renforcé du bain fondu (k_plan(T) rehaussé au-dessus de Tf) — validation cycle 231 A.

Motivation : le plateau mesuré ~350-390 °C = coude de fusion (latente) + saturation.
Le modèle canonique ne sature pas car son point chaud s'emballe (~880 °C). Un k_plan(T)
qui monte au-dessus de Tf (convection/fluage du polymère fondu, LOCALISÉ à la zone
fondue) plafonne l'interface et fait apparaître le plateau — sans sur-refroidir les
régions froides (contrairement à un h_bas global, held-out NO-GO).

Compare, sur le cycle complet piloté aux temps RÉELS :
  - canonique   : L_f=130 J/g (100 % cristallin), k_plan=3.0 constant
  - fusion      : L_f=40 J/g (physique), k_plan(T) = 3.0 sous Tf -> K_HOT au-dessus

Sortie : biblio/labo/figures/fig_valider_fusion_231A.png
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
NOMS = [f"TC{i}" for i in range(1, 6)]
COUL = [OKABE_ITO[c] for c in ("noir", "bleu", "vert", "orange", "vermillon")]
LF_PHYS = 40000.0      # J/kg — chaleur latente physique (~30 % cristallin)
K_HOT = 100.0          # W/m.K — transport effectif du bain fondu (>Tf), calibré sur le plateau
TABLE_KT = [[0.0, 3.0], [337.0, 3.0], [380.0, K_HOT], [700.0, K_HOT]]

# --- réel + fenêtres ---
df = pd.read_csv(FICH, sep="\t", decimal=",")
df.columns = [c.strip() for c in df.columns]
t = df["Time (s)"].to_numpy(float).copy(); t -= t[0]
S = {n: pd.to_numeric(df[[c for c in df.columns if c.startswith(n)][0]], errors="coerce").to_numpy(float).copy() for n in NOMS}
maxtc = np.nanmax(np.vstack([S[n] for n in NOMS]), axis=0)
AMB = float(np.nanmedian(np.vstack([S[n][:10] for n in NOMS])))
i0 = int(np.argmax(maxtc > AMB + 15)); t -= t[i0]
keep = t >= 0; t = t[keep]; S = {n: S[n][keep] for n in NOMS}; maxtc = maxtc[keep]
from scipy.signal import find_peaks
pk, props = find_peaks(maxtc, prominence=30, distance=len(t) // 8)
pk = np.sort(pk[np.argsort(props["prominences"])[::-1][:4]])
starts, dwells = [], []
for j, ip in enumerate(pk):
    lo = 0 if j == 0 else pk[j - 1]
    istart = lo + int(np.argmin(maxtc[lo:ip + 1]))
    starts.append(float(t[istart])); dwells.append(float(t[ip] - t[istart]))
gaps = [starts[i + 1] - (starts[i] + dwells[i]) for i in range(3)] + [float(t[-1] - (starts[3] + dwells[3]))]

E = g.construire_essai(231.0)
GR, MAT, CONTACT = E.grille, E.cfg.materiau, E.cfg.contact
POS = {n: (float(E.spec["thermocouples"][n]["x"]), float(E.spec["thermocouples"][n]["y"])) for n in NOMS}


def cycle(Lf, table_kt, t_amb):
    MAT.chaleur_latente = Lf
    MAT.k_plan_T = table_kt          # None => k constant (chemin historique)
    amb = copy.deepcopy(E.cfg.ambiant); amb.T_amb = t_amb
    field = np.full(GR.nx * GR.ny, t_amb)
    T_out = {n: [] for n in NOMS}; t_out = []; PC = []; t0 = 0.0
    for i in range(4):
        P = E._P_spots_2d[i]; Pnul = np.zeros_like(P)
        solv = SolveurThermique2D(GR, MAT, amb, CONTACT, masque_ceramique=E._masques[i])
        th = np.append(np.arange(0.0, dwells[i], 0.5), dwells[i])
        sh = solv.simuler(lambda tt: P, (0.0, dwells[i]), t_eval=th, T_initial=field); field = sh.y[:, -1]
        tc = np.append(np.arange(0.0, gaps[i], 1.0), gaps[i])
        sc = solv.simuler(lambda tt: Pnul, (0.0, gaps[i]), t_eval=tc, T_initial=field); field = sc.y[:, -1]
        for sol, off in ((sh, 0.0), (sc, dwells[i])):
            for n in NOMS:
                T_out[n].append(solv.serie_temporelle(sol, *POS[n]))
            PC.append(solv.serie_temporelle(sol, float(E.spots[i]["centre_x"]), 0.0))
            t_out.append(t0 + off + sol.t)
        t0 += dwells[i] + gaps[i]
    return np.concatenate(t_out), {n: np.concatenate(T_out[n]) for n in NOMS}, np.concatenate(PC)


t_can, S_can, PC_can = cycle(130000.0, None, AMB)        # canonique
t_fus, S_fus, PC_fus = cycle(LF_PHYS, TABLE_KT, AMB)     # fusion physique + k(T)

fig, ax = plt.subplots(figsize=(12.0, 5.6))
for n, c in zip(NOMS, COUL):
    ax.plot(t, S[n], color=c, lw=1.7, alpha=0.9, label=f"{n} mesuré")
    ax.plot(t_fus, S_fus[n], color=c, lw=1.3, ls=(0, (4, 1.8)), label=f"{n} fusion")
ax.plot(t_fus, PC_fus, color="0.4", lw=1.0, ls=(0, (1, 1.4)), label="point chaud (fusion)")
ax.plot(t_can, PC_can, color="0.7", lw=0.9, ls=(0, (1, 2)), label="point chaud (canonique)", zorder=1.5)
ax.axhline(390, color=OKABE_ITO["vert"], lw=0.8, ls="--"); ax.axhline(337, color=OKABE_ITO["cyan"], lw=0.8, ls=":")
ax.set_xlim(0, t[-1]); ax.set_ylim(0, 900)
ax.set_xlabel("Temps (s) — pilotage par les temps réels")
ax.set_ylabel("Température (°C)")
ax.set_title(f"Modèle de fusion (L_f=40 J/g physique + k_plan(T>Tf)={K_HOT:.0f}) — cycle 231 A",
             fontsize=12, fontweight="bold")
ax.legend(loc="upper right", ncol=2, fontsize=6.8, framealpha=0.93)
fig.tight_layout()
savefig(fig, R / "biblio" / "labo" / "figures" / "fig_valider_fusion_231A")
plt.close(fig)

tmax = min(t[-1], t_fus[-1]); gr = np.linspace(0, tmax, 600)
print(f"L_f physique {LF_PHYS/1000:.0f} J/g + k_plan(T>Tf)={K_HOT:.0f} W/m.K")
print(f"\n{'TC':>4} | {'mesuré':>6} | {'canon':>6} | {'fusion':>6} | {'RMSE can':>8} | {'RMSE fus':>8}")
for n in NOMS:
    sm = np.interp(gr, t, S[n]); rc = np.interp(gr, t_can, S_can[n]); rf = np.interp(gr, t_fus, S_fus[n])
    ok = ~np.isnan(sm)
    print(f"{n:>4} | {np.nanmax(S[n]):6.0f} | {S_can[n].max():6.0f} | {S_fus[n].max():6.0f} | "
          f"{np.sqrt(np.mean((rc[ok]-sm[ok])**2)):8.1f} | {np.sqrt(np.mean((rf[ok]-sm[ok])**2)):8.1f}")
print(f"\npoint chaud max : canonique {PC_can.max():.0f}  ->  fusion {PC_fus.max():.0f} °C")
print("figure -> biblio/labo/figures/fig_valider_fusion_231A.png")
