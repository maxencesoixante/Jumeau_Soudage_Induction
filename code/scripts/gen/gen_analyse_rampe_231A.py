#!/usr/bin/env python3
"""Analyse de la DYNAMIQUE DE CHAUFFE (rampe) — cycle 231 A, par passe.

Au-delà des pics : compare la VITESSE de montée réelle vs modèle (canonique, piloté
aux temps réels), les instants de franchissement 337/390 °C, et la latence
d'amorçage, sur le TC de contrôle (le plus chaud) de chaque passe. Le point chaud
d'interface du modèle est tracé en contexte (non mesuré).

Sortie : biblio/labo/figures/fig_rampe_231A.png
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
COUL = {n: OKABE_ITO[c] for n, c in zip(NOMS, ("noir", "bleu", "vert", "orange", "vermillon"))}

# --- réel ---
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
# TC de contrôle réel = le plus chaud de chaque fenêtre de passe
ctrl = []
for i in range(4):
    w = (t >= starts[i]) & (t <= starts[i] + dwells[i])
    ctrl.append(max(NOMS, key=lambda n: np.nanmax(S[n][w])))
print("passes :", [f"P{i+1} start={starts[i]:.0f} dwell={dwells[i]:.0f} ctrl={ctrl[i]}" for i in range(4)])

# --- modèle canonique piloté aux temps réels : segments de chauffe par passe ---
E = g.construire_essai(231.0)
GR, MAT, CONTACT = E.grille, E.cfg.materiau, E.cfg.contact
amb = copy.deepcopy(E.cfg.ambiant); amb.T_amb = AMB
POS = {n: (float(E.spec["thermocouples"][n]["x"]), float(E.spec["thermocouples"][n]["y"])) for n in NOMS}
field = np.full(GR.nx * GR.ny, AMB)
segb = []   # par passe : dict(t, TC{...}, PC)
for i in range(4):
    P = E._P_spots_2d[i]; Pnul = np.zeros_like(P)
    solv = SolveurThermique2D(GR, MAT, amb, CONTACT, masque_ceramique=E._masques[i])
    th = np.append(np.arange(0.0, dwells[i], 0.5), dwells[i])
    sh = solv.simuler(lambda tt: P, (0.0, dwells[i]), t_eval=th, T_initial=field)
    seg = dict(t=sh.t, PC=solv.serie_temporelle(sh, float(E.spots[i]["centre_x"]), 0.0))
    for n in NOMS:
        seg[n] = solv.serie_temporelle(sh, *POS[n])
    segb.append(seg)
    field = sh.y[:, -1]
    tc = np.append(np.arange(0.0, gaps[i], 1.0), gaps[i])
    sc = solv.simuler(lambda tt: Pnul, (0.0, gaps[i]), t_eval=tc, T_initial=field)
    field = sc.y[:, -1]


def franchit(tt, T, seuil):
    idx = np.where(T >= seuil)[0]
    if len(idx) == 0 or idx[0] == 0:
        return float("nan")
    j = idx[0]
    return float(tt[j - 1] + (seuil - T[j - 1]) / (T[j] - T[j - 1]) * (tt[j] - tt[j - 1]))


def pente_montee(tt, T):
    """dT/dt moyenne sur la partie montante (de +10 % au pic) et max local lissé."""
    T0, Tp = T[0], T.max()
    if Tp - T0 < 10:
        return float("nan"), float("nan")
    lo = T0 + 0.1 * (Tp - T0)
    ip = int(np.argmax(T))
    il = int(np.argmax(T >= lo))
    moy = (T[ip] - T[il]) / (tt[ip] - tt[il]) if tt[ip] > tt[il] else float("nan")
    d = np.gradient(T, tt)
    mx = float(np.nanmax(d[:ip + 1])) if ip > 0 else float("nan")
    return moy, mx


# --- figure 2x2 + table ---
fig, axes = plt.subplots(2, 2, figsize=(12.0, 7.4))
print(f"\n{'P':>2} | {'TC':>4} | {'dwell':>5} | {'pente réel':>10} | {'pente mod':>9} | "
      f"{'t337 r/m':>10} | {'t390 r/m':>10} | {'lat r/m':>8}")
for i, ax in enumerate(axes.flat):
    n = ctrl[i]
    wr = (t >= starts[i]) & (t <= starts[i] + dwells[i] + 2)
    tr = t[wr] - starts[i]; Tr = S[n][wr]
    tm = segb[i]["t"]; Tm = segb[i][n]; PCm = segb[i]["PC"]
    # rampes
    pmoy_r, pmax_r = pente_montee(tr, Tr)
    pmoy_m, pmax_m = pente_montee(tm, Tm)
    t337_r, t390_r = franchit(tr, Tr, 337), franchit(tr, Tr, 390)
    t337_m, t390_m = franchit(tm, Tm, 337), franchit(tm, Tm, 390)
    lat_r = franchit(tr, Tr, Tr[0] + 10); lat_m = franchit(tm, Tm, Tm[0] + 10)

    ax.plot(tr, Tr, color=COUL[n], lw=1.8, label=f"{n} mesuré")
    ax.plot(tm, Tm, color=COUL[n], lw=1.4, ls=(0, (4, 1.8)), label=f"{n} modèle")
    ax.plot(tm, PCm, color="0.45", lw=1.0, ls=(0, (1, 1.4)), label="point chaud (modèle)")
    for s, cc in ((337, OKABE_ITO["cyan"]), (390, OKABE_ITO["vert"])):
        ax.axhline(s, color=cc, lw=0.8, ls="--", zorder=1)
    ax.set_title(f"Passe {i+1} — contrôle {n} (dwell {dwells[i]:.0f} s)", fontsize=10.5, fontweight="bold")
    ax.set_xlim(0, dwells[i] + 2); ax.set_ylim(0, 560)
    ax.text(0.03, 0.97, f"pente ↑ mesuré {pmoy_r:.1f} °C/s\npente ↑ modèle {pmoy_m:.1f} °C/s",
            transform=ax.transAxes, va="top", ha="left", fontsize=7.6, color="0.25",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.8", alpha=0.9))
    if i >= 2: ax.set_xlabel("Temps depuis début de passe (s)")
    if i % 2 == 0: ax.set_ylabel("Température (°C)")
    ax.legend(loc="lower right", fontsize=6.8, framealpha=0.9)

    def f(x): return f"{x:.0f}" if not np.isnan(x) else "—"
    print(f"{i+1:>2} | {n:>4} | {dwells[i]:5.0f} | {pmoy_r:5.1f}°C/s   | {pmoy_m:4.1f}°C/s  | "
          f"{f(t337_r):>4}/{f(t337_m):<4} | {f(t390_r):>4}/{f(t390_m):<4} | {f(lat_r):>3}/{f(lat_m):<3}")

fig.suptitle("Dynamique de chauffe 231 A — rampe mesurée vs modèle (canonique, temps réels)",
             fontsize=13, fontweight="bold", y=0.995)
fig.tight_layout(rect=(0, 0, 1, 0.97))
savefig(fig, R / "biblio" / "labo" / "figures" / "fig_rampe_231A")
plt.close(fig)
print("\n(t337/t390 = instant de franchissement 337/390 °C depuis début de passe, réel/modèle ;")
print(" lat = latence d'amorçage = instant du +10 °C. '—' = seuil jamais atteint par ce TC.)")
print("figure -> biblio/labo/figures/fig_rampe_231A.png")
