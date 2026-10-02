#!/usr/bin/env python
"""Issue #73 — figure des simulations de la face intérieure du tube (Q2, enjeu de Q1).

Lit resultats/tube_q2/*.npz (code/scripts/diag/diag_tube_q2.py) :
  (a) spot fixe 201 A, modèle « k_z réduit » : interface et face du bas, à plat
      (sous 3,36 mm, sur le bâti) et sur le tube (sous 1,68 mm, cavité h = 5) ;
  (b) cycle semi-statique à 4 spots, même modèle : face du bas sous chaque spot
      (centre de la largeur), à plat et sur le tube ;
  (c) pic de la face du bas, spot fixe, pour les deux modèles d'épaisseur et
      trois pertes de cavité (h = 2, 5, 10), avec Tg et Tf.
Sortie : biblio/labo/figures/issue73/fig73_simulation_face_interieure.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts"))
sys.path.insert(0, str(R / "code" / "scripts" / "gen"))
import gen_schemas_montage as g  # noqa: E402  (style partagé)
from _style import OKABE_ITO  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

D = R / "resultats" / "tube_q2"
OUT = R / "biblio" / "labo" / "figures" / "issue73" / "fig73_simulation_face_interieure.png"
T_G, T_F = 159.0, 337.0
C_PLAT, C_TUBE = "0.35", OKABE_ITO["bleu"]


def charger(nom):
    return dict(np.load(D / f"{nom}.npz"))


def seuils(ax, xmax):
    ax.axhline(T_F, color="0.5", lw=0.7, ls=":")
    ax.axhline(T_G, color="0.5", lw=0.7, ls="--")
    ax.text(xmax, T_F + 4, "Tf", fontsize=7, color="0.4", ha="right", va="bottom")
    ax.text(xmax, T_G + 4, "Tg", fontsize=7, color="0.4", ha="right", va="bottom")


def main():
    fig, axes = plt.subplots(1, 3, figsize=(10.6, 3.5), gridspec_kw=dict(width_ratios=[1, 1.3, 0.9], wspace=0.34))
    # (a) spot fixe
    ax = axes[0]
    for nom, c in (("spot_ralenti_plat", C_PLAT), ("spot_ralenti_tube_h5", C_TUBE)):
        d = charger(nom)
        ax.plot(d["t"], d["TC2"], color=c, lw=1.0, alpha=0.6)
        ax.plot(d["t"], d["TC3"], color=c, lw=1.8)
    seuils(ax, 200)
    ax.set_xlim(0, 200)
    ax.set_ylim(0, 450)
    ax.set_xlabel("temps (s)")
    ax.set_ylabel("température (°C)")
    ax.set_title("Spot fixe, 201 A", fontsize=9.5)
    # (b) cycle à 4 spots
    ax = axes[1]
    for nom, c in (("cycle_ralenti_plat", C_PLAT), ("cycle_ralenti_tube_h5", C_TUBE)):
        d = charger(nom)
        for k in range(1, 5):
            ax.plot(d["t"], d[f"O{k}"], color=c, lw=1.3, alpha=0.9)
    seuils(ax, float(charger("cycle_ralenti_plat")["t"][-1]))
    ax.set_xlim(0, float(charger("cycle_ralenti_plat")["t"][-1]))
    ax.set_ylim(0, 450)
    ax.set_xlabel("temps (s)")
    ax.set_title("Cycle à 4 spots, face du bas sous chaque spot", fontsize=9.5)
    # (c) pics, deux modèles, trois pertes de cavité
    ax = axes[2]
    geoms = [("plat", "à plat"), ("tube_h2", "tube\nh = 2"), ("tube_h5", "tube\nh = 5"), ("tube_h10", "tube\nh = 10")]
    x = np.arange(len(geoms))
    w = 0.36
    for k, (modele, lab, c) in enumerate((("ralenti", "k_z réduit", OKABE_ITO["bleu"]),
                                          ("actuel", "modèle actuel", "0.6"))):
        v = [charger(f"spot_{modele}_{gname}")["TC3"].max() for gname, _ in geoms]
        ax.bar(x + (k - 0.5) * w, v, w, color=c, label=lab)
    seuils(ax, len(geoms) - 0.4)
    ax.set_xticks(x, [l for _, l in geoms], fontsize=7.6)
    ax.set_ylim(0, 450)
    ax.set_title("Pic de la face du bas, spot fixe", fontsize=9.5)
    ax.legend(frameon=False, fontsize=7.2, loc="upper left")
    for a in axes:
        for sp in ("top", "right"):
            a.spines[sp].set_visible(False)
    h = [Line2D([0], [0], color=C_PLAT, lw=1.8, label="à plat : face opposée (sous 3,36 mm, sur le bâti)"),
         Line2D([0], [0], color=C_TUBE, lw=1.8, label="tube : face intérieure (sous 1,68 mm, cavité h = 5)"),
         Line2D([0], [0], color="0.5", lw=1.0, alpha=0.6, label="interface (spot fixe)")]
    fig.legend(handles=h, loc="upper center", ncol=3, frameon=False, fontsize=7.6, bbox_to_anchor=(0.45, 0.0))
    g.savefig(fig, OUT, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
    print(OUT.relative_to(R))
