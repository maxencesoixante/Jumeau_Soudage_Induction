#!/usr/bin/env python3
"""Essai réel 231 A — thermocouples MESURÉS seuls (sans aucune courbe de simulation).

Figure « brute » de la campagne semi-statique 231 A du 26/08 : les 5 TC de bord
(y=0, x=0/30/60/90/120 mm) recalés sur l'amorçage. Aucune prédiction.

Sortie : biblio/labo/figures/fig_exp_231A_mesure.png
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts"))
from _style import apply_style, savefig, OKABE_ITO  # noqa: E402

# Style maison (labels d'axes en gras, palette, bbox serré) à la MÊME résolution
# que le reste de la famille 231 A (200 dpi), pour rester cohérent.
apply_style(**{"savefig.dpi": 200, "figure.dpi": 200})

FICH = R / "donnees" / "data" / "exp10_cycle-semistatique_231A_2026-08-26" / "231A_semistatique_bord_2026-08-26.txt"
NOMS = [f"TC{i}" for i in range(1, 6)]
XPOS = {"TC1": 0, "TC2": 30, "TC3": 60, "TC4": 90, "TC5": 120}
COUL = [OKABE_ITO[c] for c in ("noir", "bleu", "vert", "orange", "vermillon")]

df = pd.read_csv(FICH, sep="\t", decimal=",")
df.columns = [c.strip() for c in df.columns]
t = df["Time (s)"].to_numpy(float).copy(); t -= t[0]
S = {n: pd.to_numeric(df[[c for c in df.columns if c.startswith(n)][0]], errors="coerce").to_numpy(float).copy() for n in NOMS}
maxtc = np.nanmax(np.vstack([S[n] for n in NOMS]), axis=0)
amb = float(np.nanmedian(np.vstack([S[n][:10] for n in NOMS])))
i0 = int(np.argmax(maxtc > amb + 15)); t -= t[i0]
keep = t >= -5
t = t[keep]; S = {n: S[n][keep] for n in NOMS}

fig, ax = plt.subplots(figsize=(11.0, 4.8))
for n, c in zip(NOMS, COUL):
    ax.plot(t, S[n], color=c, lw=1.6, label=f"{n} (x={XPOS[n]} mm)")
for seuil, c, lab in ((337, OKABE_ITO["cyan"], "fusion 337 °C"),
                      (390, OKABE_ITO["vert"], "consigne 390 °C")):
    ax.axhline(seuil, color=c, lw=0.9, ls="--", zorder=1)
    ax.text(t[-1], seuil + 3, f" {lab}", color=c, fontsize=7.5, va="bottom", ha="right")

ax.set_xlim(t[0], t[-1])
ax.set_ylim(0, max(420, np.nanmax([np.nanmax(S[n]) for n in NOMS]) * 1.05))
ax.set_xlabel("Temps (s)")
ax.set_ylabel("Température (°C)")
ax.set_title("Essai réel 231 A — cycle semi-statique 4 passes (thermocouples de bord mesurés)",
             fontsize=12, fontweight="bold")
ax.legend(loc="upper left", ncol=5, fontsize=7.8, columnspacing=1.0, framealpha=0.92)
fig.tight_layout()
savefig(fig, R / "biblio" / "labo" / "figures" / "fig_exp_231A_mesure")
plt.close(fig)
print("pics mesurés :", {n: round(float(np.nanmax(S[n]))) for n in NOMS})
print("figure -> biblio/labo/figures/fig_exp_231A_mesure.png")
