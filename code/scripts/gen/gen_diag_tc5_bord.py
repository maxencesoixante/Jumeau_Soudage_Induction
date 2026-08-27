#!/usr/bin/env python3
"""Diagnostic « pourquoi TC5 s'emballe » — profil de température MAX le long du bord y=0.

Montre que les DEUX coins (x=0 et x=120) sur-chauffent identiquement dans le modèle :
le puits ad-hoc `h_bord_x0` (appliqué au SEUL bord x=0) rabat le coin x=0 (TC1) et
laisse le coin x=120 (TC5) exposé. La physique est la même ; l'asymétrie est le puits
à sens unique + l'accumulation (TC5 = passe 4, plaque déjà chaude).

Profil = max sur tout le cycle de T(x, y=0), pour h_bord_x0 = 250 (canon) et = 0
(symétrique), + les 5 pics TC mesurés.

Sortie : biblio/labo/figures/fig_diag_tc5_bord.png
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
DW, GP = [77.0, 102.0, 86.0, 97.0], [145.0, 149.0, 175.0, 141.0]

# réel : pics des 5 TC
df = pd.read_csv(FICH, sep="\t", decimal=",")
df.columns = [c.strip() for c in df.columns]
S = {f"TC{i}": pd.to_numeric(df[[c for c in df.columns if c.startswith(f'TC{i}')][0]], errors="coerce").to_numpy(float) for i in range(1, 6)}
amb = float(np.nanmedian(np.vstack([S[f"TC{i}"][:10] for i in range(1, 6)])))
TC_X = np.array([0, 30, 60, 90, 120])
TC_PIC = np.array([np.nanmax(S[f"TC{i}"]) for i in range(1, 6)])

E = g.construire_essai(231.0)
GR, MAT, CONTACT = E.grille, E.cfg.materiau, E.cfg.contact
iy0 = int(np.argmin(abs(GR.y - 0.0)))


def profil_max_bord(hbord):
    """max sur tout le cycle de T(x, y=0), profil (nx,)."""
    amb2 = copy.deepcopy(E.cfg.ambiant); amb2.h_bord_x0 = hbord; amb2.T_amb = amb
    field = np.full(GR.nx * GR.ny, amb)
    prof = np.full(GR.nx, amb)
    for i in range(4):
        solv = SolveurThermique2D(GR, MAT, amb2, CONTACT, masque_ceramique=E._masques[i])
        P = E._P_spots_2d[i]; Pnul = np.zeros_like(P)
        for (D, src) in ((DW[i], P), (GP[i], Pnul)):
            te = np.append(np.arange(0.0, D, 0.5), D)
            s = solv.simuler(lambda tt: src, (0.0, D), t_eval=te, T_initial=field)
            Y = s.y.reshape(GR.nx, GR.ny, -1)[:, iy0, :]      # (nx, nt) le long du bord
            prof = np.maximum(prof, Y.max(axis=1))
            field = s.y[:, -1]
    return prof


x_mm = GR.x * 1000.0
p250 = profil_max_bord(250.0)
p0 = profil_max_bord(0.0)
# valeurs au nœud exact de chaque position TC (cohérent avec le tableau imprimé)
def val(prof, x):
    return float(prof[int(np.argmin(abs(x_mm - x)))])
v250 = np.array([val(p250, x) for x in TC_X])
v0 = np.array([val(p0, x) for x in TC_X])

fig, ax = plt.subplots(figsize=(10.5, 5.4))
xi = np.arange(5); w = 0.27
ax.bar(xi - w, v250, w, color=OKABE_ITO["bleu"], label="modèle h_bord_x0=250 (canon) — puits au SEUL bord x=0")
ax.bar(xi, v0, w, color=OKABE_ITO["orange"], label="modèle h_bord_x0=0 (bords symétriques)")
ax.bar(xi + w, TC_PIC, w, color="0.25", label="mesuré (231 A)")
for k in range(5):
    for off, v, c in ((-w, v250[k], OKABE_ITO["bleu"]), (0, v0[k], OKABE_ITO["orange"]), (w, TC_PIC[k], "0.25")):
        ax.annotate(f"{v:.0f}", (xi[k] + off, v + 8), ha="center", fontsize=7.4, color=c)
ax.axhline(g.T_FUSION, color=OKABE_ITO["cyan"], lw=0.9, ls="--", zorder=1)
ax.text(4.45, g.T_FUSION - 26, "fusion 337", color=OKABE_ITO["cyan"], fontsize=7.5, ha="right")

ax.annotate("puits h_bord_x0\n(TC1 : 442→276)", xy=(-w, v250[0]), xytext=(1.15, 175),
            fontsize=7.8, color=OKABE_ITO["bleu"], ha="center",
            arrowprops=dict(arrowstyle="->", color=OKABE_ITO["bleu"], lw=1.0))
ax.annotate("aucun puits ici\n+ accumulation P4\n→ TC5 s'emballe", xy=(4 - 0.05, v0[4]), xytext=(3.15, 655),
            fontsize=8.0, color=OKABE_ITO["vermillon"], ha="center", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=OKABE_ITO["vermillon"], lw=1.1))

ax.set_xticks(xi); ax.set_xticklabels([f"TC{i+1}\n(x={x} mm)" for i, x in enumerate(TC_X)], fontsize=8.5)
ax.set_ylabel("Température MAX sur le cycle (°C)")
ax.set_ylim(0, 700)
ax.set_title("Pourquoi TC5 s'emballe — pic de chaque TC de bord (cycle 231 A)",
             fontsize=12, fontweight="bold")
ax.legend(loc="upper left", fontsize=7.8, framealpha=0.93)
note = ("Sans puits (orange) les DEUX coins montent pareil (x=0 : 442, x=120 : 573) → même physique de bord, le modèle sur-accumule aux coins.\n"
        "Le puits ad-hoc h_bord_x0 n'agit qu'en x=0 → rabat TC1 et laisse TC5 exposé. Écart x=0↔x=120 = accumulation (TC5 en passe 4). Réel plat ~390.")
ax.text(0.5, -0.16, note, transform=ax.transAxes, ha="center", va="top", fontsize=7.2, color="0.35", linespacing=1.4)
fig.tight_layout(rect=(0, 0.04, 1, 1))
savefig(fig, R / "biblio" / "labo" / "figures" / "fig_diag_tc5_bord")
plt.close(fig)

print("profil max bord (°C) aux positions TC :")
for x in TC_X:
    ix = int(np.argmin(abs(x_mm - x)))
    print(f"  x={x:3d}mm : h_bord250={p250[ix]:.0f}  h_bord0={p0[ix]:.0f}  mesuré={TC_PIC[list(TC_X).index(x)]:.0f}")
print("figure -> biblio/labo/figures/fig_diag_tc5_bord.png")
