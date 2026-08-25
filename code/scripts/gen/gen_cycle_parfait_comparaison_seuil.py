#!/usr/bin/env python3
"""Comparaison du seuil de refroidissement inter-passes : 120 °C vs Tg (159 °C).

Gagner du temps procédé en repartant dès que le joint est figé (sous Tg du PEKK,
159 °C) au lieu d'attendre 120 °C. Temps total de cycle (4 passes, chauffe+refroid)
par courant, pour les deux critères, avec le gain.

Données = gen_cycle_parfait_semistatique.py (modèle 2D, θ*), campagne 2026-08-25 :
  - 120 °C : run par défaut (déjà commité) ;
  - 159 °C : SEUIL_REFROID=159 (juste sous Tg).
130 A NE SOUDE PAS dans les deux cas (P1 n'atteint jamais 390 °C).

Sortie : biblio/labo/figures/fig_cycle_parfait_comparaison_seuil.png
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts"))
from _style import apply_style, savefig  # noqa: E402
apply_style(**{"savefig.dpi": 200, "figure.dpi": 200})

# temps total de cycle (s) : {courant: (seuil_120, seuil_159, soude)}
TOTAL = {
    130: (1426.6, 1224.4, False),
    160: (780.5,  620.1,  True),
    230: (453.0,  317.5,  True),
    275: (373.1,  245.7,  True),
}
C_120, C_TG = "#0072B2", "#009E73"  # Okabe-Ito : 120 °C (bleu) / Tg 159 °C (vert)

courants = list(TOTAL)
x = np.arange(len(courants))
w = 0.38
t120 = np.array([TOTAL[i][0] for i in courants])
t159 = np.array([TOTAL[i][1] for i in courants])
gain = t120 - t159
pct = 100 * gain / t120

fig, ax = plt.subplots(figsize=(8.0, 4.8))
b1 = ax.bar(x - w / 2, t120, w, color=C_120, label="Refroidir jusqu'à 120 °C")
b2 = ax.bar(x + w / 2, t159, w, color=C_TG, label="Refroidir jusqu'à Tg (159 °C)")

for k, i in enumerate(courants):
    soude = TOTAL[i][2]
    if not soude:
        for b in (b1[k], b2[k]):
            b.set_hatch("///"); b.set_edgecolor("0.35"); b.set_alpha(0.55)
    # valeurs sur les barres
    ax.text(x[k] - w / 2, t120[k] + 12, f"{t120[k]:.0f}", ha="center", va="bottom", fontsize=8.2)
    ax.text(x[k] + w / 2, t159[k] + 12, f"{t159[k]:.0f}", ha="center", va="bottom", fontsize=8.2)
    # gain
    tag = "  (ne soude pas)" if not soude else ""
    ax.text(x[k], max(t120[k], t159[k]) + 70,
            f"−{gain[k]:.0f} s\n(−{pct[k]:.0f} %){tag}", ha="center", va="bottom",
            fontsize=8.6, fontweight="bold",
            color=("#B00020" if not soude else "#1B7837"))

ax.set_xticks(x)
ax.set_xticklabels([f"{i} A" for i in courants])
ax.set_ylabel("Temps total de cycle — 4 passes (s)")
ax.set_xlabel("Courant du générateur")
ax.set_ylim(0, t120.max() * 1.24)
ax.set_title("Seuil de refroidissement inter-passes : 120 °C vs Tg (159 °C)\n"
             "repartir dès que le joint est figé (sous Tg) raccourcit le cycle",
             fontsize=11, fontweight="bold")
ax.legend(loc="upper right", framealpha=0.95)
fig.tight_layout()
savefig(fig, R / "biblio" / "labo" / "figures" / "fig_cycle_parfait_comparaison_seuil")
print("figure -> biblio/labo/figures/fig_cycle_parfait_comparaison_seuil.png")
for i in courants:
    print(f"  {i} A : 120°C={TOTAL[i][0]:.0f}s  Tg159={TOTAL[i][1]:.0f}s  "
          f"gain={TOTAL[i][0]-TOTAL[i][1]:.0f}s ({100*(TOTAL[i][0]-TOTAL[i][1])/TOTAL[i][0]:.0f}%)")
