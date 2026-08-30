#!/usr/bin/env python3
"""Comparaison v2 (layout TC serie A/B) — correction de bord x OFF vs ON.

Isole l'effet de la correction `lambda_bord_x_mm` (auto = épaisseur de couche,
commit 5056d77) sur les TC posés aux bords x : TC1(x=0) et TC5(x=120), au centre
y=20 en v2. Modèle canonique piloté aux temps réels ; on rejoue le cycle avec la
source OFF (défaut) et ON (auto), mêmes fenêtres.

Sortie : biblio/labo/figures/fig_compare_231A_v2_corrige.png
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
from jumeau.em.source_joule import source_spot  # noqa: E402
from jumeau.thermique.solveur2d import SolveurThermique2D  # noqa: E402
from _style import savefig, OKABE_ITO  # noqa: E402

FICH = R / "donnees" / "data" / "exp10_cycle-semistatique_231A_2026-08-26" / "231A_semistatique_TCy20-serieAB_2026-08-27.txt"
NOMS = [f"TC{i}" for i in range(1, 6)]
COUL = [OKABE_ITO[c] for c in ("noir", "bleu", "vert", "orange", "vermillon")]
POS_V2 = {"TC1": (0.000, 0.020), "TC2": (0.030, 0.0), "TC3": (0.060, 0.0),
          "TC4": (0.090, 0.0), "TC5": (0.120, 0.020)}
BORDX = ("TC1", "TC5")   # aux bords x (cibles de la correction)

# --- réel + fenêtres ---
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

E = g.construire_essai(231.0)
GR, MAT, CONTACT = E.grille, E.cfg.materiau, E.cfg.contact

def sources_2d(lam):
    Q = [source_spot(E.grille, g.cfg, E.couches, 231.0, float(s["centre_x"]),
                     facteur_couplage=g.FACTEUR, decalage_x=0.0, lambda_bord_x_mm=lam)
         for s in E.spots]
    return [q.sum(axis=2) * E.grille.dz for q in Q]

def cycle(P2d):
    amb = copy.deepcopy(E.cfg.ambiant); amb.T_amb = AMB
    field = np.full(GR.nx * GR.ny, AMB); T_out = {n: [] for n in NOMS}; t_out = []; t0 = 0.0
    for i in range(4):
        P = P2d[i]; Pnul = np.zeros_like(P)
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
    return np.concatenate(t_out), {n: np.concatenate(T_out[n]) for n in NOMS}

t_off, S_off = cycle(sources_2d(0.0))    # OFF (canonique)
t_on, S_on = cycle(sources_2d(None))     # ON (auto = épaisseur de couche)

fig, ax = plt.subplots(figsize=(12.0, 5.8))
for n, c in zip(NOMS, COUL):
    ax.plot(t, S[n], color=c, lw=1.7, alpha=0.9, label=f"{n} mesuré")
    if n in BORDX:
        ax.plot(t_off, S_off[n], color=c, lw=1.0, ls=(0, (1, 1.5)), alpha=0.8, label=f"{n} modèle OFF")
        ax.plot(t_on, S_on[n], color=c, lw=1.5, ls=(0, (4, 1.8)), label=f"{n} modèle ON (corrigé)")
    else:
        ax.plot(t_on, S_on[n], color=c, lw=1.2, ls=(0, (4, 1.8)), label=f"{n} modèle (OFF≡ON)")
ax.axhline(390, color=OKABE_ITO["vert"], lw=0.8, ls="--"); ax.axhline(337, color=OKABE_ITO["cyan"], lw=0.8, ls=":")
ax.set_xlim(0, max(t[-1], t_on[-1])); ax.set_ylim(0, 720)
ax.set_xlabel("Temps (s) — pilotage par les temps réels")
ax.set_ylabel("Température (°C)")
ax.set_title("v2 (TC1/TC5 au centre y=20) — correction de bord x OFF vs ON",
             fontsize=12, fontweight="bold")
ax.legend(loc="upper right", ncol=2, fontsize=6.6, framealpha=0.93)
fig.tight_layout()
savefig(fig, R / "biblio" / "labo" / "figures" / "fig_compare_231A_v2_corrige")
plt.close(fig)

print(f"{'TC':>4} | {'pos':>13} | {'mesuré':>6} | {'OFF':>6} | {'ON':>6} | {'ΔON-OFF':>7}")
for n in NOMS:
    po, pn, pm = S_off[n].max(), S_on[n].max(), float(np.nanmax(S[n]))
    tag = " (bord x, corrigé)" if n in BORDX else " (intérieur)"
    print(f"{n:>4} | {str(POS_V2[n]):>13} | {pm:6.0f} | {po:6.0f} | {pn:6.0f} | {pn-po:+7.0f}{tag}")
print("figure -> biblio/labo/figures/fig_compare_231A_v2_corrige.png")
