#!/usr/bin/env python3
"""Comparaison prédit ↔ mesuré — essai 231 A v2 (layout de TC serie A/B).

v2 : TC1(x=0) et TC5(x=120) au CENTRE largeur y=20 ; TC2/3/4 (x=30/60/90) au bord
y=0. Modèle 2D canonique piloté par les temps RÉELS (fenêtres auto-détectées).
Distingue les TC FIABLES (TC2/3/4, bord intérieur) des NON fiables (TC1/TC5, aux
bords x=0/x=120 où la source du modèle est mal distribuée — artefact ψ=0).

Sortie : biblio/labo/figures/fig_compare_231A_v2.png
"""
from __future__ import annotations
import sys, copy
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts" / "gen"))
sys.path.insert(0, str(R / "code" / "scripts"))
import gen_cycle_parfait_semistatique as g  # noqa: E402
from jumeau.thermique.solveur2d import SolveurThermique2D  # noqa: E402
from _style import savefig, OKABE_ITO  # noqa: E402

FICH = R / "donnees" / "data" / "exp10_cycle-semistatique_231A_2026-08-26" / "231A_semistatique_TCy20-serieAB_2026-08-27.txt"
NOMS = [f"TC{i}" for i in range(1, 6)]
COUL = [OKABE_ITO[c] for c in ("noir", "bleu", "vert", "orange", "vermillon")]
POS_V2 = {"TC1": (0.000, 0.020), "TC2": (0.030, 0.0), "TC3": (0.060, 0.0),
          "TC4": (0.090, 0.0), "TC5": (0.120, 0.020)}
FIABLES = ("TC2", "TC3", "TC4")

df = pd.read_csv(FICH, sep="\t", decimal=",")
df.columns = [c.strip() for c in df.columns]
t = df["Time (s)"].to_numpy(float).copy(); t -= t[0]
S = {n: pd.to_numeric(df[[c for c in df.columns if c.startswith(n)][0]], errors="coerce").to_numpy(float).copy() for n in NOMS}
maxtc = np.nanmax(np.vstack([S[n] for n in NOMS]), axis=0)
AMB = float(np.nanmedian(np.vstack([S[n][:10] for n in NOMS])))
i0 = int(np.argmax(maxtc > AMB + 15)); t -= t[i0]
keep = t >= 0; t = t[keep]; S = {n: S[n][keep] for n in NOMS}; maxtc = maxtc[keep]
pk, props = find_peaks(maxtc, prominence=30, distance=len(t) // 8)
pk = np.sort(pk[np.argsort(props["prominences"])[::-1][:4]])
starts, dwells = [], []
for j, ip in enumerate(pk):
    lo = 0 if j == 0 else pk[j - 1]
    istart = lo + int(np.argmin(maxtc[lo:ip + 1]))
    starts.append(float(t[istart])); dwells.append(float(t[ip] - t[istart]))
gaps = [starts[i + 1] - (starts[i] + dwells[i]) for i in range(3)] + [float(t[-1] - (starts[3] + dwells[3]))]
print("fenêtres v2 :", [f"P{i+1} dwell={dwells[i]:.0f} gap={gaps[i]:.0f}" for i in range(4)])

E = g.construire_essai(231.0)
# Cette figure illustre l'artefact de bord x AVANT correction (récit chronologique) :
# on force la source CANONIQUE (lambda_bord_x_mm=0.0) même si la correction est active
# par défaut ailleurs. La correction (OFF vs ON) est montrée par gen_compare_231A_v2_corrige.py.
from jumeau.em.source_joule import source_spot  # noqa: E402
E._Q_spots = [source_spot(E.grille, g.cfg, E.couches, 231.0, float(s["centre_x"]),
                          facteur_couplage=g.FACTEUR, decalage_x=0.0, lambda_bord_x_mm=0.0)
              for s in E.spots]
E._P_spots_2d = [q.sum(axis=2) * E.grille.dz for q in E._Q_spots]
GR, MAT, CONTACT = E.grille, E.cfg.materiau, E.cfg.contact
amb = copy.deepcopy(E.cfg.ambiant); amb.T_amb = AMB
field = np.full(GR.nx * GR.ny, AMB)
T_out = {n: [] for n in NOMS}; t_out = []; t0 = 0.0
for i in range(4):
    P = E._P_spots_2d[i]; Pnul = np.zeros_like(P)
    solv = SolveurThermique2D(GR, MAT, amb, CONTACT, masque_ceramique=E._masques[i])
    th = np.append(np.arange(0.0, dwells[i], 0.5), dwells[i])
    sh = solv.simuler(lambda tt: P, (0.0, dwells[i]), t_eval=th, T_initial=field); field = sh.y[:, -1]
    tc = np.append(np.arange(0.0, gaps[i], 1.0), gaps[i])
    sc = solv.simuler(lambda tt: Pnul, (0.0, gaps[i]), t_eval=tc, T_initial=field); field = sc.y[:, -1]
    for sol, off in ((sh, 0.0), (sc, dwells[i])):
        for n in NOMS:
            T_out[n].append(solv.serie_temporelle(sol, *POS_V2[n]))
        t_out.append(t0 + off + sol.t)
    t0 += dwells[i] + gaps[i]
t_m = np.concatenate(t_out); S_m = {n: np.concatenate(T_out[n]) for n in NOMS}

fig, ax = plt.subplots(figsize=(12.0, 5.6))
for n, c in zip(NOMS, COUL):
    if n in FIABLES:
        ax.plot(t, S[n], color=c, lw=1.7, alpha=0.9, label=f"{n} mesuré (bord)")
        ax.plot(t_m, S_m[n], color=c, lw=1.3, ls=(0, (4, 1.8)), label=f"{n} modèle")
    else:
        ax.plot(t, S[n], color=c, lw=1.7, alpha=0.9, label=f"{n} mesuré (y=20)")
        ax.plot(t_m, S_m[n], color="0.6", lw=1.0, ls=(0, (1, 1.5)), label=f"{n} modèle — ARTEFACT bord x")
ax.axhline(390, color=OKABE_ITO["vert"], lw=0.8, ls="--"); ax.axhline(337, color=OKABE_ITO["cyan"], lw=0.8, ls=":")
ax.set_xlim(0, max(t[-1], t_m[-1])); ax.set_ylim(0, 620)
ax.set_xlabel("Temps (s) — pilotage par les temps réels")
ax.set_ylabel("Température (°C)")
ax.set_title("Validation 231 A v2 (TC1/TC5 au centre y=20) — mesuré vs modèle",
             fontsize=12, fontweight="bold")
ax.legend(loc="upper right", ncol=2, fontsize=6.8, framealpha=0.93)
fig.tight_layout()
savefig(fig, R / "biblio" / "labo" / "figures" / "fig_compare_231A_v2")
plt.close(fig)

tmax = min(t[-1], t_m[-1]); gr = np.linspace(0, tmax, 600)
print(f"\n{'TC':>4} | {'pos':>10} | {'pic mes':>7} | {'pic mod':>7} | {'RMSE':>6} | fiable ?")
for n in NOMS:
    sm = np.interp(gr, t, S[n]); sp = np.interp(gr, t_m, S_m[n]); ok = ~np.isnan(sm)
    loc = "y=20 (x-bord)" if n in ("TC1", "TC5") else "y=0 bord"
    fl = "OUI" if n in FIABLES else "NON (artefact)"
    print(f"{n:>4} | {loc:>12} | {np.nanmax(S[n]):7.0f} | {S_m[n].max():7.0f} | "
          f"{np.sqrt(np.mean((sp[ok]-sm[ok])**2)):6.1f} | {fl}")
print("figure -> biblio/labo/figures/fig_compare_231A_v2.png")
