#!/usr/bin/env python3
"""Ré-adoucissement des joints déjà soudés (cycle parfait semi-statique, seuil Tg).

Quand on repart dès que le point chaud d'un spot est redescendu à Tg (159 °C), le
joint qu'on vient de faire peut être **réchauffé au-dessus de Tg** par les passes
suivantes (spots voisins). La structure cristalline (formée en refroidissant sous
~279 °C) persiste → le joint tient ; seule la phase amorphe se ré-adoucit puis se
re-fige. On quantifie, pour chaque joint i (= CENTRE du spot i, y=0), la
température MAX atteinte APRÈS sa propre passe, l'excès au-dessus de Tg, et la
durée passée au-dessus de Tg.

On mesure AU CENTRE DES SPOTS (les joints réels), indépendamment de la position
des thermocouples physiques : on ajoute des capteurs virtuels JOINT_i aux centres
des spots (monkeypatch de construire_essai). Mode opératoire réel serieA/B (4
spots, pas 30 mm). Modèle 2D, θ*.

Sortie : biblio/labo/figures/fig_readoucissement_joint.png + tableau sur stdout.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts" / "gen"))
sys.path.insert(0, str(R / "code" / "scripts"))
from _style import apply_style, savefig, OKABE_ITO  # noqa: E402

import gen_cycle_parfait_semistatique as g  # noqa: E402

apply_style(**{"savefig.dpi": 200, "figure.dpi": 200})

TG = g.T_REFROID  # 159 °C (seuil d'avance = Tg)
COURANTS = [130.0, 160.0, 230.0, 275.0]

# --- monkeypatch : ajoute un capteur virtuel JOINT_i au CENTRE de chaque spot ---
_construire_orig = g.construire_essai


def _construire_avec_joints(courant):
    e = _construire_orig(courant)
    for i, s in enumerate(e.spots):
        e.spec["thermocouples"][f"JOINT{i + 1}"] = {
            "x": float(s["centre_x"]), "y": 0.0, "z": "interface"}
    e.spec["tc_valides"] = list(e.spec["thermocouples"])
    return e


g.construire_essai = _construire_avec_joints


def duree_au_dessus(t, y, seuil, t0):
    dur = 0.0
    for k in range(len(t) - 1):
        if t[k] >= t0 and y[k] > seuil:
            dur += t[k + 1] - t[k]
    return dur


resultats = {}
for I in COURANTS:
    print(f"\n=== I = {I:.0f} A ===")
    res = g.simuler_cycle(I)
    t, series, passes = res["t"], res["series"], res["passes"]
    lignes = []
    for i, p in enumerate(passes[:-1]):          # le dernier spot n'a pas de passe suivante
        y = series[f"JOINT{i + 1}"]              # joint i = centre du spot i
        t_fin = p["t_fin_refroid"]
        m = t > t_fin + 1e-6
        reheat = float(y[m].max()) if m.any() else float(y[-1])
        exces = reheat - TG
        duree = duree_au_dessus(t, y, TG, t_fin)
        lignes.append((i + 1, reheat, exces, duree))
        print(f"  joint {i + 1} (x={p['x_c'] * 1000:.1f} mm) : ré-chauffe max = {reheat:6.1f} °C "
              f"(Tg{exces:+5.1f} °C), durée > Tg = {duree:6.1f} s")
    resultats[I] = lignes

# --------------------------------------------------------------------------- #
fig, ax = plt.subplots(figsize=(8.4, 4.8))
couleurs = [OKABE_ITO[c] for c in ("bleu", "vert", "orange", "vermillon")]
n_j = max(len(v) for v in resultats.values())
x = np.arange(n_j)
w = 0.2
for k, I in enumerate(COURANTS):
    exces = [l[2] for l in resultats[I]] + [np.nan] * (n_j - len(resultats[I]))
    ax.bar(x + (k - 1.5) * w, exces, w, color=couleurs[k], label=f"{I:.0f} A")

ax.axhline(0, color="0.5", lw=1.0, ls="--")
ax.text(0.015, 0.94, "0 = Tg (159 °C) — au-dessus : le joint se ré-adoucit (amorphe) ; en-dessous : reste figé",
        transform=ax.transAxes, fontsize=8.3, color="0.35")
ax.set_xticks(x)
ax.set_xticklabels([f"joint {i + 1}" for i in range(n_j)])
ax.set_ylabel("Ré-chauffe max du joint − Tg  (°C)")
ax.set_xlabel("Joint déjà soudé (centre du spot), réchauffé par les passes suivantes")
ax.set_title("Ré-adoucissement des joints au seuil Tg (159 °C) — mode opératoire réel (4 passes)\n"
             "excès de température au-dessus de Tg subi par chaque joint après sa passe",
             fontsize=10.5, fontweight="bold")
ax.legend(title="Courant", loc="lower right", framealpha=0.95, ncol=2)
fig.tight_layout()
savefig(fig, R / "biblio" / "labo" / "figures" / "fig_readoucissement_joint")
print("\nfigure -> biblio/labo/figures/fig_readoucissement_joint.png")
