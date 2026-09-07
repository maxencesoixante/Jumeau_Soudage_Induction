"""Validation en aveugle du cycle 231 A -- pics predits vs mesures, par thermocouple.

Version LISIBLE A PETITE TAILLE de `fig_compare_230A_vs_reel.png` (10 courbes,
illisible en vignette) : un couple de points par thermocouple, relies par un
segment dont la longueur EST l'ecart. Ordonnee en degres Celsius BRUTS (pas
d'ecart ni de normalisation sur l'axe, cf. preference projet).

Donnees : essai reel du 2026-08-26 (231 A, semi-statique, 4 passes, coupure TC
390 C) ; predictions FIGEES AVANT l'essai (gen_cycle_230A_TC390.py). Pics en C.
Cf. memoire projet `validation-231A-cycle-semistatique` et issue #64.

N'ecrit QUE le PNG de sortie.
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _style import apply_style, OKABE_ITO  # noqa: E402

apply_style(**{
    "font.size": 12, "axes.labelsize": 13, "axes.titlesize": 13.5,
    "legend.fontsize": 11, "xtick.labelsize": 12.5, "ytick.labelsize": 12,
    "axes.linewidth": 1.0, "lines.linewidth": 1.8, "savefig.pad_inches": 0.06,
    "figure.facecolor": "white", "savefig.facecolor": "white",
})

#            TC     mesuré  prédit  position
POINTS = [("TC1",   392.0,  302.0, "coin"),
          ("TC2",   350.0,  362.0, "int"),
          ("TC3",   381.0,  363.0, "int"),
          ("TC4",   383.0,  363.0, "int"),
          ("TC5",   387.0,  545.0, "coin")]

BLEU, ORANGE = OKABE_ITO["bleu"], OKABE_ITO["vermillon"]
fig, ax = plt.subplots(figsize=(6.8, 5.4))

ax.axhspan(355, 390, color=OKABE_ITO["vert"], alpha=0.13, lw=0, zorder=0)
ax.text(4.80, 372, "cible\nprocédé\n355–390 °C", fontsize=9.5, color="0.30",
        ha="left", va="center", linespacing=1.3, zorder=2)
ax.axhline(337, color="0.45", lw=1.2, ls=":", zorder=1)
ax.text(-0.42, 332, "fusion PEKK 337 °C", fontsize=9.5, color="0.35",
        ha="left", va="top", zorder=2)

for i, (nom, mes, pred, pos) in enumerate(POINTS):
    coul = BLEU if pos == "int" else ORANGE
    ax.plot([i, i], [mes, pred], color=coul, lw=2.6, alpha=0.55,
            solid_capstyle="round", zorder=4)
    ax.scatter([i], [mes], s=155, marker="o", color="0.15", zorder=6)
    ax.scatter([i], [pred], s=155, marker="D", facecolor="white",
               edgecolor=coul, linewidth=2.4, zorder=6)
    ecart = pred - mes
    ax.annotate(f"{ecart:+.0f} °C", (i, (mes + pred) / 2), xytext=(i + 0.17,
                (mes + pred) / 2), fontsize=11, fontweight="bold", color=coul,
                ha="left", va="center", zorder=7)

ax.set_xticks(range(len(POINTS)))
ax.set_xticklabels([f"{n}\n{'intérieur' if p == 'int' else 'coin'}"
                    for n, _, _, p in POINTS], linespacing=1.5)
ax.set_xlim(-0.55, 5.95)
ax.set_ylim(280, 575)
ax.set_ylabel("Température de pic (°C)")
ax.set_title("Cycle 231 A, 4 passes — prédiction figée AVANT l'essai", pad=9)
ax.grid(True, axis="y", alpha=0.25, lw=0.5)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)

ax.scatter([], [], s=155, marker="o", color="0.15", label="mesuré à l'essai")
ax.scatter([], [], s=155, marker="D", facecolor="white", edgecolor=BLEU,
           linewidth=2.4, label="prédit avant l'essai")
ax.legend(loc="upper left", frameon=True, framealpha=0.95, borderpad=0.6,
          handletextpad=0.6)

fig.tight_layout()
OUT = R / "biblio" / "labo" / "figures" / "fig_parite_231A.png"
fig.savefig(OUT)
print("écrit :", OUT)
