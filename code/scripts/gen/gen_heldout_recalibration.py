#!/usr/bin/env python3
"""Held-out du θ* recalibré 231A (coin + refroid global) vs canonique — synthèse (issue #65).

RMSE moyen par essai, produit par les deux commandes de l'issue #65 :

  # canonique
  valider.py --modele 2D --facteur 6.0123 --h-haut 30.087 --h-bas-2d 37.424  --h-bord-x0 250
  # recalibré Δ*
  valider.py --modele 2D --facteur 6.5358 --h-haut 30.087 --h-bas-2d 124.872 --h-bord-x0 2.4
             --essais exp7_{150,176,200,225,250}A exp9_{175,200,226,250}A_monospot serieA_A-1 serieA_A-3 serieB_B-2

Held-out strict : le fit de Δ* n'a vu QUE l'essai 231A. Verdict : NO-GO (Δ* régresse
les familles semi-statiques serieA/B de +15 à +19 °C).

Sortie : biblio/labo/figures/fig_heldout_recalibration_231A.png
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts"))
from _style import savefig, OKABE_ITO  # noqa: E402

# RMSE moyen (°C) par essai — sortie des deux valider.py held-out
ESSAIS = ["exp7_150A", "exp7_176A", "exp7_200A", "exp7_225A", "exp7_250A",
          "exp9_175A", "exp9_200A", "exp9_226A", "exp9_250A",
          "serieA_A-1", "serieA_A-3", "serieB_B-2"]
CANON = [25.4, 24.4, 21.8, 21.5, 22.6, 11.3, 12.1, 7.8, 10.1, 36.3, 33.0, 65.3]
RECAL = [25.3, 23.4, 19.8, 24.3, 23.0, 13.7, 15.4, 7.3, 12.5, 54.8, 48.3, 82.2]
FAMILLE = ["exp7"] * 5 + ["exp9"] * 4 + ["serieA/B"] * 3

canon = np.array(CANON); recal = np.array(RECAL)
delta = recal - canon
x = np.arange(len(ESSAIS))

fig, ax = plt.subplots(figsize=(12.0, 5.2))
w = 0.4
ax.bar(x - w / 2, canon, w, label="canonique (θ*)", color=OKABE_ITO["bleu"])
ax.bar(x + w / 2, recal, w, label="recalibré Δ* (231A)", color=OKABE_ITO["vermillon"])
for i, d in enumerate(delta):
    ax.annotate(f"{d:+.0f}", (x[i], max(canon[i], recal[i]) + 1.5), ha="center",
                fontsize=7.5, color=("#B00020" if d > 3 else "0.35"),
                fontweight=("bold" if d > 10 else "normal"))
# séparateurs de familles
for xb in (4.5, 8.5):
    ax.axvline(xb, color="0.8", lw=0.8, ls=":")
ax.text(2, 78, "exp7 (held-out)", ha="center", fontsize=8.5, color="0.4")
ax.text(6.5, 78, "exp9 (held-out)", ha="center", fontsize=8.5, color="0.4")
ax.text(10, 78, "serieA/B (held-out)", ha="center", fontsize=8.5, color="0.4", fontweight="bold")

ax.set_xticks(x); ax.set_xticklabels(ESSAIS, rotation=35, ha="right", fontsize=8)
ax.set_ylabel("RMSE moyen (°C)")
ax.set_ylim(0, 88)
ax.set_title("Held-out : θ* recalibré 231A (coin + refroid global) vs canonique — VERDICT NO-GO",
             fontsize=12, fontweight="bold")
ax.legend(loc="upper left", fontsize=9)
note = ("Δ* calibré sur le SEUL essai 231A. Held-out : exp7 ~neutre (Δ≈0), exp9 légèrement pire (+2), "
        "mais serieA/B (semi-statique multi-passes, les plus proches du 231A) RÉGRESSENT de +15 à +19 °C.\n"
        "Le fort refroid. global (h_bas_2d 37→125) qui collait au 231A sous-chauffe les autres campagnes → NON adopté au canonique.")
ax.text(0.5, -0.42, note, transform=ax.transAxes, ha="center", va="top", fontsize=7.2, color="0.35", linespacing=1.5)
fig.tight_layout(rect=(0, 0.06, 1, 1))
savefig(fig, R / "biblio" / "labo" / "figures" / "fig_heldout_recalibration_231A")
plt.close(fig)

print("=== Held-out : canonique vs Δ* (RMSE moyen par essai) ===")
print(f"{'essai':>16} | {'canon':>6} | {'Δ* recal':>8} | {'ΔRMSE':>6}")
for e, c, r in zip(ESSAIS, CANON, RECAL):
    print(f"{e:>16} | {c:6.1f} | {r:8.1f} | {r - c:+6.1f}")
for fam in ("exp7", "exp9", "serieA/B"):
    idx = [i for i, f in enumerate(FAMILLE) if f == fam]
    dc = np.mean([CANON[i] for i in idx]); dr = np.mean([RECAL[i] for i in idx])
    print(f"  moyenne {fam:>9} : canon {dc:5.1f} -> Δ* {dr:5.1f}  ({dr - dc:+.1f})")
print(f"\n  moyenne held-out globale : canon {canon.mean():.1f} -> Δ* {recal.mean():.1f} "
      f"({recal.mean() - canon.mean():+.1f})  => VERDICT : NO-GO")
print("figure -> biblio/labo/figures/fig_heldout_recalibration_231A.png")
