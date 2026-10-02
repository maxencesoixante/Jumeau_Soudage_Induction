#!/usr/bin/env python
"""Issue #71 — figures pour comprendre le montage « U + vessie ».

1. fig71_condition_cotes.png   — l'empilement (hauteur du U + plaques) face à la
   course disponible sous l'outil : jeu positif (la vessie amène les plaques à
   l'outil, les parois ne portent pas) ou interférence (les parois court-
   circuitent la vessie). À froid puis à chaud : dilatation et perte d'épaisseur
   à la fusion de l'interface déplacent le jeu. Schéma sans échelle.
2. fig71_controle_croise.png   — instrumentation (cellule de force au-dessus,
   manomètre sur la vessie) et lecture attendue : F_cellule = p·A tant qu'aucune
   paroi ne porte ; F_cellule < p·A dès qu'une paroi porte (schéma de principe).
3. fig71_temperature_vessie.png — température maximale mesurée à plat sur la face
   au contact de la future vessie (campagne à 3 TC, face opposée), comparée aux
   limites de service des matériaux de vessie (notes du projet : Rishon −112 /
   +454 °C, silicone générique 200–230 °C, EPDM/nitrile 120–150 °C).

Consigne de lisibilité : cotes, axes et légende ; pas de phrases dans les figures.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))
sys.path.insert(0, str(R / "code" / "scripts"))
sys.path.insert(0, str(R / "code" / "scripts" / "diag"))
sys.path.insert(0, str(R / "code" / "scripts" / "gen"))
import gen_schemas_montage as g  # noqa: E402
from _style import OKABE_ITO  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Rectangle, FancyArrowPatch, Ellipse  # noqa: E402

from jumeau.materiaux import Config  # noqa: E402
from jumeau.procede import Essai  # noqa: E402
from diag_epaisseur_3d_reference import mesure  # noqa: E402

OUT = R / "biblio" / "labo" / "figures" / "issue71"
C_VERRE, C_VERRE_BORD = "#E8E0C8", "#9A8C5A"
C_EFFORT, C_CHALEUR, C_BATI, C_VESSIE = "#009E73", OKABE_ITO["vermillon"], "#BFBFBF", "#F0E442"
C_OUTIL = "#7F7F7F"


def fleche(ax, p0, p1, c, lw=1.5, ms=10, style="-|>"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=ms, lw=lw, color=c, zorder=8))


def montage(ax, x0, jeu, porte, etiquette_jeu):
    """Coupe schématique : bâti, U en verre, vessie, deux plaques, outil."""
    W, ep, H = 4.0, 0.3, 2.2
    eP = 0.35                                     # épaisseur d'une plaque (sans échelle)
    ax.add_patch(Rectangle((x0 - 0.3, -0.35), W + 0.6, 0.35, fc=C_BATI, ec="0.4", hatch="\\\\\\", lw=0.6))
    for xm in (x0, x0 + W - ep):                  # parois du U
        ax.add_patch(Rectangle((xm, 0), ep, H, fc=C_VERRE, ec=C_VERRE_BORD, lw=0.8))
    ax.add_patch(Rectangle((x0, 0), W, ep, fc=C_VERRE, ec=C_VERRE_BORD, lw=0.8))
    y_pl = H + (0.0 if porte else jeu)            # bas des plaques
    ax.add_patch(Ellipse((x0 + W / 2, (ep + y_pl) / 2), W - 2 * ep - 0.15, y_pl - ep - 0.1,
                         fc=C_VESSIE, alpha=0.5, ec="0.4", lw=0.8))
    ax.add_patch(Rectangle((x0 - 0.1, y_pl), W + 0.2, eP, fc=g.C_COUPON, alpha=0.3, ec=g.C_COUPON, lw=0.8))
    ax.add_patch(Rectangle((x0 - 0.1, y_pl + eP), W + 0.2, eP, fc=g.C_COUPON, alpha=0.3, ec=g.C_COUPON, lw=0.8))
    ax.plot([x0 - 0.1, x0 + W + 0.1], [y_pl + eP, y_pl + eP], color=C_CHALEUR, lw=2.0, zorder=5)
    y_outil = y_pl + 2 * eP
    ax.add_patch(Rectangle((x0 + 0.6, y_outil), W - 1.2, 0.45, fc=C_OUTIL, alpha=0.6, ec="0.3", lw=0.8))
    # efforts
    for xi in np.linspace(x0 + 1.0, x0 + W - 1.0, 3):
        fleche(ax, (xi, ep + 0.25), (xi, y_pl - 0.05), C_EFFORT, lw=1.3)
    if porte:
        for xm in (x0 + ep / 2, x0 + W - ep / 2):
            fleche(ax, (xm, y_pl - 0.05), (xm, 0.4), OKABE_ITO["vermillon"], lw=1.6)
    if not porte and etiquette_jeu:
        g_ = W + 0.35
        for yy in (H, y_pl):
            ax.plot([x0 + W - 0.05, x0 + g_ + 0.1], [yy, yy], color="0.45", lw=0.6, ls=":")
        ax.annotate("", xy=(x0 + g_, H), xytext=(x0 + g_, y_pl),
                    arrowprops=dict(arrowstyle="<->", color="0.25", lw=0.8))
        ax.text(x0 + g_ + 0.12, (H + y_pl) / 2, etiquette_jeu, fontsize=7.4, va="center", color="0.25")
    return y_outil


def fig_condition_cotes():
    fig, ax = plt.subplots(figsize=(9.2, 3.3))
    cas = [("À froid : jeu > 0", 0.7, False, "jeu"),
           ("À chaud : dilatation, fusion", 0.3, False, "jeu réduit"),
           ("Interférence : jeu ≤ 0", 0.0, True, "")]
    for k, (titre, jeu, porte, lab) in enumerate(cas):
        x0 = k * 6.0
        montage(ax, x0, jeu, porte, lab)
        ax.text(x0 + 2.0, 4.4, titre, ha="center", va="bottom", fontsize=9.5)
    ax.set_xlim(-0.8, 17.4)
    ax.set_ylim(-0.5, 5.0)
    ax.set_aspect("equal")
    ax.axis("off")
    h = [Rectangle((0, 0), 1, 1, fc=C_OUTIL, alpha=0.6, ec="0.3", label="outil (vers la cellule)"),
         Rectangle((0, 0), 1, 1, fc=g.C_COUPON, alpha=0.3, ec=g.C_COUPON, label="plaques CF/PEKK"),
         Line2D([0], [0], color=C_CHALEUR, lw=2, label="interface soudée"),
         Rectangle((0, 0), 1, 1, fc=C_VESSIE, alpha=0.5, ec="0.4", label="vessie"),
         Rectangle((0, 0), 1, 1, fc=C_VERRE, ec=C_VERRE_BORD, label="U en fibre de verre"),
         Rectangle((0, 0), 1, 1, fc=C_BATI, ec="0.4", hatch="\\\\\\", label="bâti"),
         Line2D([0], [0], color=C_EFFORT, lw=1.5, marker=">", markersize=5, label="poussée de la vessie"),
         Line2D([0], [0], color=OKABE_ITO["vermillon"], lw=1.6, marker=">", markersize=5,
                label="effort détourné par les parois")]
    fig.legend(handles=h, loc="upper center", ncol=4, frameon=False, fontsize=7.6, bbox_to_anchor=(0.5, 0.06))
    g.savefig(fig, OUT / "fig71_condition_cotes.png", bbox_inches="tight")
    plt.close(fig)


def fig_controle_croise():
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.6), gridspec_kw=dict(width_ratios=[1.0, 1.0], wspace=0.25))
    ax = axes[0]
    y_outil = montage(ax, 0.0, 0.35, False, "")
    ax.add_patch(Rectangle((1.3, y_outil + 0.45), 1.4, 0.45, fc="#CC79A7", alpha=0.7, ec="0.3", lw=0.8))
    ax.text(2.0, y_outil + 0.67, "F", ha="center", va="center", fontsize=9, fontweight="bold", color="white")
    ax.plot([2.0, 2.0, 5.2], [1.1, 1.1, 1.1], color="0.3", lw=0.8)
    ax.add_patch(plt.Circle((5.6, 1.1), 0.38, fc="white", ec="0.3", lw=1.0, zorder=6))
    ax.plot([5.6, 5.8], [1.1, 1.3], color="0.2", lw=1.0, zorder=7)
    ax.text(5.6, 0.55, "p", ha="center", va="top", fontsize=9, fontweight="bold")
    ax.set_xlim(-0.6, 6.4)
    ax.set_ylim(-0.6, y_outil + 1.2)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Instrumentation", fontsize=9.5)

    ax = axes[1]
    pA = np.linspace(0, 1, 50)
    ax.plot(pA, pA, color=C_EFFORT, lw=2.0, label="aucune paroi ne porte : F = p·A")
    ax.plot(pA, 0.62 * pA, color=OKABE_ITO["vermillon"], lw=2.0, ls="--",
            label="une paroi porte : F < p·A")
    ax.fill_between(pA, 0.62 * pA, pA, color=OKABE_ITO["vermillon"], alpha=0.08)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("p · A  (manomètre × surface)")
    ax.set_ylabel("F  (cellule de force)")
    ax.set_title("Lecture attendue (principe)", fontsize=9.5)
    ax.legend(frameon=False, fontsize=7.6, loc="upper left")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    h = [Rectangle((0, 0), 1, 1, fc="#CC79A7", alpha=0.7, ec="0.3", label="cellule de force"),
         Line2D([0], [0], marker="o", color="none", markerfacecolor="white", markeredgecolor="0.3",
                markersize=8, label="manomètre (pression vessie)")]
    fig.legend(handles=h, loc="lower center", ncol=2, frameon=False, fontsize=7.6, bbox_to_anchor=(0.3, -0.04))
    g.savefig(fig, OUT / "fig71_controle_croise.png", bbox_inches="tight")
    plt.close(fig)


def fig_temperature_vessie():
    cfg = Config.charger(R / "code" / "config")
    essais = [("chauffe_174A_3TC", 174.4), ("chauffe_201A_3TC", 201.6), ("chauffe_226A_3TC", 226.0),
              ("chauffe_226A_3TC_bis", 226.0), ("chauffe_250A_3TC", 250.0)]
    I, To, Ti = [], [], []
    for nom, cour in essais:
        e = Essai(cfg, R / "code" / "config" / "essais" / f"{nom}.yaml", nx=31, ny=11, nz=15,
                  facteur_couplage=1.0, racine=R)
        t, s, i, o = mesure(e)
        I.append(cour); To.append(float(np.nanmax(o))); Ti.append(float(np.nanmax(i)))
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    bandes = [("EPDM / nitrile", 120, 150, "#D55E00"), ("silicone générique", 200, 230, "#E69F00"),
              ("Rishon (RCF)", 454, 454, "#009E73")]
    for lab, a, b, c in bandes:
        if a == b:
            ax.axhline(a, color=c, lw=1.6, ls="-")
            ax.text(167, a - 6, lab, color=c, fontsize=7.6, ha="left", va="top")
        else:
            ax.axhspan(a, b, color=c, alpha=0.15, lw=0)
            ax.text(167, b + 3, lab, color=c, fontsize=7.6, ha="left", va="bottom")
    ax.scatter(I, Ti, s=40, color=OKABE_ITO["vermillon"], edgecolor="k", lw=0.5, zorder=5,
               label="interface (pic)")
    ax.scatter(I, To, s=55, color=OKABE_ITO["bleu"], edgecolor="k", lw=0.5, zorder=5, marker="s",
               label="face au contact de la vessie (pic, à plat sous 3,36 mm)")
    ax.set_xlim(165, 256)
    ax.set_ylim(0, 480)
    ax.set_xlabel("courant (A)")
    ax.set_ylabel("température (°C)")
    ax.legend(frameon=False, fontsize=7.6, loc="lower right")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    g.savefig(fig, OUT / "fig71_temperature_vessie.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    fig_condition_cotes()
    fig_controle_croise()
    fig_temperature_vessie()
    print("ok")
