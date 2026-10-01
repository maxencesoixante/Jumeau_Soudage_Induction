#!/usr/bin/env python
"""Issue #74 — figures pour comprendre les expériences et les mécanismes.

1. fig74_montage_3TC.png    — montage de la campagne « épaisseur » : bobine et
   MFC fixes au centre, colonne de 3 TC empilés en (x = 60, y = 20) : surface
   côté bobine, interface, face opposée. Vue de dessus et coupe x-z à 1:1.
2. fig74_mesures_3TC.png    — les 5 essais mesurés (T brute en °C), un panneau
   par essai, avec le rapport face opposée / interface au pic d'interface.
3. fig74_mecanismes.png     — schéma (sans échelle) des trois façons de
   représenter le passage de la chaleur sous l'interface : modèle actuel,
   k_z réduit dans le laminé inférieur, résistance d'interface levée à la fusion.

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
import gen_schemas_montage as g  # noqa: E402  (style + géométrie bobine/MFC/coupon)
from _style import OKABE_ITO  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Rectangle, FancyArrowPatch  # noqa: E402

from jumeau.materiaux import Config  # noqa: E402
from jumeau.procede import Essai  # noqa: E402
from diag_epaisseur_3d_reference import mesure  # noqa: E402

OUT = R / "biblio" / "labo" / "figures" / "issue74"
COUL = {"surface": OKABE_ITO["orange"], "interface": OKABE_ITO["vermillon"],
        "face opposée": OKABE_ITO["bleu"]}
ESSAIS = [("chauffe_174A_3TC", "174 A"), ("chauffe_201A_3TC", "201 A"),
          ("chauffe_226A_3TC", "226 A"), ("chauffe_226A_3TC_bis", "226 A bis"),
          ("chauffe_250A_3TC", "250 A")]
XC, YC = 60.0, 20.0
Z_TC = {"surface": 0.0, "interface": -g.E_SUP, "face opposée": -g.L_INF}


def virgule(v, n=2):
    return f"{v:.{n}f}".replace(".", ",")


# ---------------------------------------------------------------------------
def fig_montage():
    fig = plt.figure(figsize=(8.6, 7.4))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.25, 1.0], hspace=0.30,
                          top=0.95, bottom=0.12, left=0.10, right=0.97)
    ax = fig.add_subplot(gs[0])
    g.coupon_weave(ax, 0, 0, g.L, g.W)
    g.ceramique_patch(ax)
    g.mfc_patch(ax, XC, YC, style="solid")
    g.coil_legs_patch(ax, XC, YC)
    ax.scatter([XC], [YC], s=70, color=g.C_TC, edgecolor="white", linewidth=1.2, zorder=12)
    ax.annotate("TC1–TC3", (XC, YC), xytext=(XC + 22, YC + 9), fontsize=7.6, color=g.C_TC,
                fontweight="bold", zorder=12,
                arrowprops=dict(arrowstyle="-", color=g.C_TC, lw=0.7))
    g.cote_h(ax, 0, g.L, g.W + 22, "120 mm")
    g.cote_v(ax, 0, g.W, g.L + 5, "40 mm", right=True)
    ax.set_xlim(-6, g.L + 16)
    ax.set_ylim(-22, g.W + 30)
    ax.set_aspect("equal")
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.set_title("Vue de dessus", fontsize=10)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

    ax = fig.add_subplot(gs[1])
    a, b = 36.0, 84.0
    g.draw_stack_1to1(ax, a, b)
    ax.add_patch(Rectangle((XC - g.MFC_X / 2, g.H_MFC_BOT), g.MFC_X, g.MFC_H, fc=g.C_MFC,
                           alpha=0.35, ec="0.2", lw=0.9, zorder=4))
    for sgn in (-1, 1):
        ax.add_patch(Rectangle((XC + sgn * g.ENTRAXE / 2 - g.TUBE / 2, g.H_TUBE_BOT), g.TUBE,
                               g.TUBE, fc=g.C_COIL, ec="0.15", lw=0.8, zorder=6))
    for nom, z in Z_TC.items():
        ax.scatter([XC], [z], s=60, color=COUL[nom], edgecolor="black", linewidth=0.6,
                   zorder=12, clip_on=False)
    for i, (nom, z) in enumerate(Z_TC.items(), start=1):
        ax.annotate(f"TC{i}", (XC, z), xytext=(b + 1.5, z), fontsize=7.6, color=COUL[nom],
                    fontweight="bold", va="center", annotation_clip=False,
                    arrowprops=dict(arrowstyle="-", color=COUL[nom], lw=0.6, alpha=0.7))
    ax.set_xlim(a, b + 8)
    ax.set_ylim(g.H_COUPON_BOT - 1.5, g.H_MFC_TOP + 1.5)
    ax.set_aspect("equal")
    ax.set_yticks([g.H_COUPON_BOT, g.H_INTERFACE, 0, g.GAP_CERAM, g.H_MFC_TOP])
    ax.set_yticklabels(["−6,8", "−3,4", "0", "2", "14"])
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("z (mm)")
    ax.set_title("Coupe x-z à y = 20 mm (échelle 1:1)", fontsize=10)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

    h = [Rectangle((0, 0), 1, 1, fc=g.C_COIL, ec="0.2", label="Bobine hairpin (fixe)"),
         Rectangle((0, 0), 1, 1, fc=g.C_MFC, ec="0.2", alpha=0.35, label="Concentrateur MFC (fixe)"),
         Rectangle((0, 0), 1, 1, fc=g.C_CERAM, ec=g.C_CERAM_EDGE, alpha=0.55, label="Céramique 2 mm"),
         Rectangle((0, 0), 1, 1, fc=g.C_COUPON, ec=g.C_COUPON, alpha=0.4, hatch="xxxx",
                   label="Laminés CF/PEKK 3,36 + 3,36 mm"),
         Line2D([0], [0], color=g.C_COUPON, lw=2.0, label="Interface (twill + film PEKK)")]
    h += [Line2D([0], [0], marker="o", color="none", markerfacecolor=c, markeredgecolor="k",
                 markersize=7, label=f"TC{i} : {n}") for i, (n, c) in enumerate(COUL.items(), start=1)]
    fig.legend(handles=h, loc="upper center", ncol=3, frameon=False, fontsize=7.8,
               bbox_to_anchor=(0.5, 0.075))
    g.savefig(fig, OUT / "fig74_montage_3TC.png", bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
def fig_mesures():
    cfg = Config.charger(R / "code" / "config")
    fig, axes = plt.subplots(1, 5, figsize=(10.2, 3.1), sharey=True,
                             gridspec_kw=dict(wspace=0.16))
    for ax, (nom, lab) in zip(axes, ESSAIS):
        e = Essai(cfg, R / "code" / "config" / "essais" / f"{nom}.yaml", nx=31, ny=11, nz=15,
                  facteur_couplage=1.0, racine=R)
        t, s, i, o = mesure(e)
        for (n, c), v in zip(COUL.items(), (s, i, o)):
            ax.plot(t, v, color=c, lw=1.4, label=n)
        k = int(np.nanargmax(i))
        ax.plot([t[k], t[k]], [o[k], i[k]], color="0.35", lw=0.8, ls=":")
        ax.text(t[k] + 4, o[k] - 14, virgule(o[k] / i[k]), fontsize=8.5,
                color="0.2", va="top", fontweight="bold")
        dch = float(e.spec["duree_chauffe"])
        ax.axvspan(0, dch, color="0.92", zorder=0)
        ax.set_title(f"{lab} — chauffe {dch:.0f} s", fontsize=9)
        ax.set_xlim(0, min(float(t[-1]), 230))
        ax.set_xlabel("temps (s)")
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    axes[0].set_ylabel("température (°C)")
    axes[0].set_ylim(0, 420)
    h, l = axes[0].get_legend_handles_labels()
    h.append(Rectangle((0, 0), 1, 1, fc="0.92", ec="none"))
    l.append("chauffe")
    h.append(Line2D([0], [0], color="0.35", lw=0.8, ls=":"))
    l.append("face opposée / interface au pic d'interface")
    fig.legend(h, l, loc="lower center", ncol=5, frameon=False, fontsize=7.8,
               bbox_to_anchor=(0.5, -0.12))
    g.savefig(fig, OUT / "fig74_mesures_3TC.png", bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
def colonne(ax, x0, cas):
    """Empilement schématique (sans échelle) avec flèches de flux de chaleur."""
    w, e_sup, e_inf = 3.0, 2.0, 2.0
    ax.add_patch(Rectangle((x0, 0), w, e_sup, fc=g.C_COUPON, alpha=0.18, ec=g.C_COUPON, lw=0.8))
    c_inf = 0.45 if cas == "kz" else 0.18
    ax.add_patch(Rectangle((x0, -e_inf), w, e_inf, fc=g.C_COUPON, alpha=c_inf, ec=g.C_COUPON, lw=0.8,
                           hatch="////" if cas == "kz" else None))
    ax.add_patch(Rectangle((x0, -0.08), w, 0.16, fc=OKABE_ITO["vermillon"], ec="none", zorder=4))
    ax.add_patch(Rectangle((x0 - 0.2, e_sup), w + 0.4, 0.5, fc=g.C_CERAM, alpha=0.55,
                           ec=g.C_CERAM_EDGE, lw=0.6))

    def fleche(y0, y1, lw):
        ax.add_patch(FancyArrowPatch((x0 + w / 2, y0), (x0 + w / 2, y1), arrowstyle="-|>",
                                     mutation_scale=10, lw=lw, color=OKABE_ITO["vermillon"], zorder=6))

    fleche(0.15, e_sup - 0.15, 2.2 if cas != "actuel" else 1.6)       # vers le haut
    if cas == "actuel":
        fleche(-0.15, -e_inf + 0.15, 2.6)
    elif cas == "kz":
        fleche(-0.15, -e_inf + 0.15, 0.9)
    else:
        # résistance à l'interface : ressort en zigzag, deux états
        xs = np.linspace(x0 + 0.3, x0 + w - 0.3, 13)
        ys = -0.32 + 0.12 * np.array([0, 1, -1] * 4 + [0])
        ax.plot(xs, ys, color="0.15", lw=1.1, zorder=7)
        fleche(-0.5, -e_inf + 0.15, 0.9)


def fig_mecanismes():
    fig, ax = plt.subplots(figsize=(8.0, 3.2))
    titres = [("actuel", "Modèle actuel"), ("kz", "k_z réduit\nsous l'interface"),
              ("rc", "Résistance d'interface\nlevée à la fusion")]
    for k, (cas, t) in enumerate(titres):
        x0 = k * 5.0
        colonne(ax, x0, cas)
        ax.text(x0 + 1.5, 3.2, t, ha="center", va="bottom", fontsize=9)
    ax.text(10 + 1.5, -2.65, "T < Tf : active · T > Tf : levée", ha="center", va="top",
            fontsize=7.4, color="0.25")
    ax.set_xlim(-0.8, 14.0)
    ax.set_ylim(-3.0, 4.2)
    ax.axis("off")
    h = [Rectangle((0, 0), 1, 1, fc=g.C_CERAM, ec=g.C_CERAM_EDGE, alpha=0.55, label="céramique (vers MFC et bobine)"),
         Rectangle((0, 0), 1, 1, fc=g.C_COUPON, ec=g.C_COUPON, alpha=0.18, label="laminé"),
         Rectangle((0, 0), 1, 1, fc=OKABE_ITO["vermillon"], label="interface chauffée (twill)"),
         Rectangle((0, 0), 1, 1, fc=g.C_COUPON, ec=g.C_COUPON, alpha=0.45, hatch="////", label="conduction transverse réduite"),
         Line2D([0], [0], color="0.15", lw=1.1, label="résistance de contact"),
         Line2D([0], [0], color=OKABE_ITO["vermillon"], lw=2, marker=">", label="flux de chaleur (épaisseur ∝ intensité)")]
    fig.legend(handles=h, loc="lower center", ncol=3, frameon=False, fontsize=7.6,
               bbox_to_anchor=(0.5, -0.12))
    g.savefig(fig, OUT / "fig74_mecanismes.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    fig_montage()
    fig_mesures()
    fig_mecanismes()
    print("ok")
