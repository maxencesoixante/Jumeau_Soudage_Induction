#!/usr/bin/env python3
"""Synthèse du cycle parfait semi-statique : temps total de cycle par courant,
décomposé en chauffe (→390 °C) vs refroidissement (→120 °C), 4 passes cumulées.

Met en évidence que le REFROIDISSEMENT inter-passes domine la durée totale et
qu'il est quasi indépendant du courant → le goulot du procédé semi-statique.

Données = sortie de gen_cycle_parfait_semistatique.py (modèle 2D, θ* canonique,
facteur_couplage=6.0123), campagne 2026-08-25. 130 A NE SOUDE PAS (la passe 1
n'atteint jamais 390 °C dans les 300 s cappées).

Sortie : biblio/labo/figures/fig_cycle_parfait_synthese.png
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts"))
from _style import apply_style, savefig  # noqa: E402
apply_style()

# --- résultats cumulés (s) par courant : (chauffe totale, refroidissement total) ---
# somme des 4 passes ; cf. gen_cycle_parfait_semistatique.py
DATA = {
    130: dict(chauffe=847.3, refroid=579.3, soude=False),   # P1 cappée (non atteint)
    160: dict(chauffe=285.7, refroid=494.8, soude=True),
    230: dict(chauffe=82.3,  refroid=370.7, soude=True),
    275: dict(chauffe=49.2,  refroid=323.9, soude=True),
}
C_CHAUFFE, C_REFROID = "#D55E00", "#56B4E9"  # Okabe-Ito : chauffe (rouge) / refroid (bleu clair)

courants = list(DATA)
x = np.arange(len(courants))
chauffe = np.array([DATA[i]["chauffe"] for i in courants])
refroid = np.array([DATA[i]["refroid"] for i in courants])
total = chauffe + refroid

fig, ax = plt.subplots(figsize=(7.6, 4.8))
b1 = ax.bar(x, chauffe, 0.62, color=C_CHAUFFE, label="Chauffe (→ 390 °C)")
b2 = ax.bar(x, refroid, 0.62, bottom=chauffe, color=C_REFROID, label="Refroidissement (→ 120 °C)")

# hachure + marque pour 130 A (ne soude pas)
for k, i in enumerate(courants):
    if not DATA[i]["soude"]:
        for b in (b1[k], b2[k]):
            b.set_hatch("///"); b.set_edgecolor("0.35"); b.set_alpha(0.55)
        ax.text(x[k], total[k] + 30, "ne soude pas", ha="center", va="bottom",
                fontsize=8.5, color="#B00020", fontstyle="italic")

# étiquettes : total (s + min) et part de refroidissement
for k in range(len(courants)):
    pct = 100 * refroid[k] / total[k]
    ax.text(x[k], total[k] + (95 if not DATA[courants[k]]["soude"] else 20),
            f"{total[k]:.0f} s\n({total[k]/60:.1f} min)", ha="center", va="bottom",
            fontsize=9, fontweight="bold")
    ax.text(x[k], chauffe[k] + refroid[k] / 2, f"{pct:.0f} %\nrefroid.",
            ha="center", va="center", fontsize=8.3, color="0.15")
    ax.text(x[k], chauffe[k] / 2, f"{chauffe[k]:.0f} s", ha="center", va="center",
            fontsize=8.3, color="white")

ax.set_xticks(x)
ax.set_xticklabels([f"{i} A" for i in courants])
ax.set_ylabel("Temps cumulé sur 4 passes (s)")
ax.set_xlabel("Courant du générateur")
ax.set_ylim(0, total.max() * 1.16)
ax.set_title("Cycle parfait semi-statique — temps total par courant\n"
             "(le refroidissement inter-passes domine, quasi indépendant du courant)",
             fontsize=11, fontweight="bold")
ax.legend(loc="upper right", framealpha=0.95)
fig.tight_layout()
savefig(fig, R / "biblio" / "labo" / "figures" / "fig_cycle_parfait_synthese")
print("figure -> biblio/labo/figures/fig_cycle_parfait_synthese.png")
