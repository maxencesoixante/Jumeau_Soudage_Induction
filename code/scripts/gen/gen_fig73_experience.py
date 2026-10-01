#!/usr/bin/env python
"""Issue #73 — figures pour comprendre l'essai du tube substitut.

1. fig73_mecanismes.png   — schéma (sans échelle) du chemin de l'effort de
   consolidation et de la sortie de la chaleur sous l'interface : montage à plat
   actuel, tube substitut sans contre-pression (#73), tube avec vessie (#71).
2. fig73_references.png   — les mesures à plat auxquelles l'essai sera comparé :
   cycle semi-statique réel à 231 A (5 TC d'interface au bord, même disposition
   que prévue sur le tube) et face opposée de la campagne à 3 TC (référence de Q2),
   avec Tg du PEKK.
3. fig73_instrumentation.png — colonne de TC à plat (campagne « épaisseur ») et
   colonne proposée sur le tube, à la même échelle (1:1).

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
from jumeau.validation.chargement import charger_mesures, recaler_a_la_chauffe  # noqa: E402
from diag_epaisseur_3d_reference import mesure  # noqa: E402

OUT = R / "biblio" / "labo" / "figures" / "issue73"
C_TUBE, C_TUBE_BORD = "#56B4E9", "#2B7FB0"
C_EFFORT, C_CHALEUR, C_BATI = "#009E73", OKABE_ITO["vermillon"], "#BFBFBF"
E_TUBE, T_G = 1.68, 159.0
COUL_TC = {"surface": OKABE_ITO["orange"], "interface": OKABE_ITO["vermillon"],
           "face opposée": OKABE_ITO["bleu"]}


def fleche(ax, p0, p1, couleur, lw=1.6, ms=10):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=ms, lw=lw,
                                 color=couleur, zorder=8))


# ---------------------------------------------------------------------------
def fig_mecanismes():
    fig, ax = plt.subplots(figsize=(9.0, 3.6))
    W, ec, ep = 4.0, 0.45, 0.25          # largeur, épaisseurs connecteur / paroi (sans échelle)
    H = 2.4                              # hauteur de cavité
    titres = ["Montage à plat (actuel)", "Tube substitut (#73)", "Tube + vessie (#71)"]
    for k, titre in enumerate(titres):
        x0 = k * 6.0
        ax.text(x0 + W / 2, 1.55, titre, ha="center", va="bottom", fontsize=9.5)
        # connecteur + interface
        ax.add_patch(Rectangle((x0 + 0.6, 0), W - 1.2, ec, fc=g.C_COUPON, alpha=0.25, ec=g.C_COUPON, lw=0.8, zorder=3))
        ax.add_patch(Rectangle((x0 + 0.6, -0.05), W - 1.2, 0.1, fc=C_CHALEUR, ec="none", zorder=4))
        for xi in np.linspace(x0 + 1.0, x0 + W - 1.0, 4):
            fleche(ax, (xi, 1.35), (xi, ec + 0.05), C_EFFORT)
        if k == 0:
            ax.add_patch(Rectangle((x0, -ec), W, ec, fc=g.C_COUPON, alpha=0.25, ec=g.C_COUPON, lw=0.8))
            ax.add_patch(Rectangle((x0 - 0.3, -ec - 0.35), W + 0.6, 0.35, fc=C_BATI, ec="0.4",
                                   hatch="\\\\\\", lw=0.6))
            for xi in np.linspace(x0 + 1.0, x0 + W - 1.0, 4):
                fleche(ax, (xi, -0.05), (xi, -ec - 0.3), C_EFFORT, lw=1.2)
            fleche(ax, (x0 + W / 2, -0.1), (x0 + W / 2, -ec + 0.02), C_CHALEUR, lw=2.2)
            continue
        # tube : dessus, murs, fond, bâti
        y_bas = -ep - H - ep
        ax.add_patch(Rectangle((x0, -ep), W, ep, fc=C_TUBE, alpha=0.35, ec=C_TUBE_BORD, lw=0.8, hatch="////"))
        for xm in (x0, x0 + W - ep):
            ax.add_patch(Rectangle((xm, -ep - H), ep, H, fc=C_TUBE, alpha=0.35, ec=C_TUBE_BORD, lw=0.8, hatch="////"))
        ax.add_patch(Rectangle((x0, y_bas), W, ep, fc=C_TUBE, alpha=0.35, ec=C_TUBE_BORD, lw=0.8, hatch="////"))
        ax.add_patch(Rectangle((x0 - 0.3, y_bas - 0.35), W + 0.6, 0.35, fc=C_BATI, ec="0.4", hatch="\\\\\\", lw=0.6))
        # flexion du dessus (déformée exagérée en pointillé) et effort dans les murs
        xs = np.linspace(x0 + ep, x0 + W - ep, 40)
        ys = -ep - 0.28 * np.sin(np.pi * (xs - x0 - ep) / (W - 2 * ep))
        if k == 1:
            ax.plot(xs, ys, color="0.3", lw=0.9, ls="--", zorder=6)
        for xm in (x0 + ep / 2, x0 + W - ep / 2):
            fleche(ax, (xm, -ep - 0.1), (xm, y_bas + ep + 0.05), C_EFFORT, lw=1.4)
        fleche(ax, (x0 + W / 2, -0.1), (x0 + W / 2, -ep - 0.35), C_CHALEUR, lw=1.0)
        if k == 2:
            ax.add_patch(Ellipse((x0 + W / 2, -ep - H / 2), W - 2 * ep - 0.3, H - 0.3, fc="#F0E442",
                                 alpha=0.45, ec="0.4", lw=0.8, zorder=2))
            for xi in np.linspace(x0 + 1.0, x0 + W - 1.0, 4):
                fleche(ax, (xi, -ep - H / 2 + 0.2), (xi, -ep - 0.05), C_EFFORT, lw=1.2)
    ax.set_xlim(-0.8, 16.8)
    ax.set_ylim(-3.55, 2.2)
    ax.set_aspect("equal")
    ax.axis("off")
    h = [Rectangle((0, 0), 1, 1, fc=g.C_COUPON, ec=g.C_COUPON, alpha=0.25, label="connecteur / laminé"),
         Rectangle((0, 0), 1, 1, fc=C_TUBE, ec=C_TUBE_BORD, alpha=0.35, hatch="////", label="parois du tube"),
         Rectangle((0, 0), 1, 1, fc=C_CHALEUR, label="interface chauffée"),
         Rectangle((0, 0), 1, 1, fc="#F0E442", ec="0.4", alpha=0.45, label="vessie gonflée"),
         Rectangle((0, 0), 1, 1, fc=C_BATI, ec="0.4", hatch="\\\\\\", label="bâti"),
         Line2D([0], [0], color=C_EFFORT, lw=1.6, marker=">", markersize=5, label="effort"),
         Line2D([0], [0], color=C_CHALEUR, lw=2, marker=">", markersize=5, label="chaleur sous l'interface"),
         Line2D([0], [0], color="0.3", lw=0.9, ls="--", label="flexion du dessus (exagérée)")]
    fig.legend(handles=h, loc="lower center", ncol=4, frameon=False, fontsize=7.6,
               bbox_to_anchor=(0.5, -0.08))
    g.savefig(fig, OUT / "fig73_mecanismes.png", bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
def fig_references():
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.4), gridspec_kw=dict(width_ratios=[1.55, 1], wspace=0.22))
    ax = axes[0]
    df = charger_mesures(R / "donnees" / "data" / "exp10_cycle-semistatique_231A_2026-08-26"
                         / "231A_semistatique_bord_2026-08-26.txt", seuil_aberrant=2000.0)
    df = recaler_a_la_chauffe(df)
    t = df.iloc[:, 0].to_numpy()
    coul = [OKABE_ITO[c] for c in ("noir", "bleu", "vert", "orange", "vermillon")]
    for k, c in enumerate(coul, start=1):
        ax.plot(t, df[f"TC{k} (C)"].to_numpy(), color=c, lw=1.2, label=f"TC{k} (x = {30 * (k - 1)})")
    ax.axhline(337, color="0.5", lw=0.7, ls=":")
    ax.axhline(T_G, color="0.5", lw=0.7, ls="--")
    ax.text(t[-1], 341, "Tf", fontsize=7, color="0.4", ha="right", va="bottom")
    ax.text(t[-1], T_G + 4, "Tg", fontsize=7, color="0.4", ha="right", va="bottom")
    ax.set_xlim(0, t[-1])
    ax.set_ylim(0, 430)
    ax.set_xlabel("temps (s)")
    ax.set_ylabel("température (°C)")
    ax.set_title("Cycle semi-statique à plat, 231 A (TC d'interface au bord)", fontsize=9)
    ax.legend(frameon=False, fontsize=7, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.2))

    ax = axes[1]
    cfg = Config.charger(R / "code" / "config")
    for nom, lab in (("chauffe_174A_3TC", "174 A"), ("chauffe_201A_3TC", "201 A"),
                     ("chauffe_226A_3TC", "226 A"), ("chauffe_226A_3TC_bis", "226 A bis"),
                     ("chauffe_250A_3TC", "250 A")):
        e = Essai(cfg, R / "code" / "config" / "essais" / f"{nom}.yaml", nx=31, ny=11, nz=15,
                  facteur_couplage=1.0, racine=R)
        tm, s, i, o = mesure(e)
        ax.plot(tm, i, color=COUL_TC["interface"], lw=0.8, alpha=0.45)
        ax.plot(tm, o, color=COUL_TC["face opposée"], lw=1.3)
    ax.axhline(T_G, color="0.5", lw=0.7, ls="--")
    ax.text(225, T_G + 4, "Tg", fontsize=7, color="0.4", ha="right", va="bottom")
    ax.set_xlim(0, 230)
    ax.set_ylim(0, 430)
    ax.set_xlabel("temps (s)")
    ax.set_title("Campagne à 3 TC, à plat (5 essais)", fontsize=9)
    ax.legend(handles=[Line2D([0], [0], color=COUL_TC["interface"], lw=0.8, alpha=0.6, label="interface"),
                       Line2D([0], [0], color=COUL_TC["face opposée"], lw=1.3, label="face opposée (3,36 mm sous l'interface)")],
              frameon=False, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.2))
    for a in axes:
        for sp in ("top", "right"):
            a.spines[sp].set_visible(False)
    g.savefig(fig, OUT / "fig73_references.png", bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
def fig_instrumentation():
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 2.9), sharey=True, gridspec_kw=dict(wspace=0.08))
    a, b = 0.0, 20.0
    for ax, cas in zip(axes, ("plat", "tube")):
        ax.add_patch(Rectangle((a, 0), b - a, g.GAP_CERAM, fc=g.C_CERAM, alpha=0.55, ec=g.C_CERAM_EDGE, lw=0.7))
        ax.add_patch(Rectangle((a, -g.E_SUP), b - a, g.E_SUP, fc=g.C_COUPON, alpha=0.22, ec=g.C_COUPON, lw=0.9))
        ax.plot([a, b], [-g.E_SUP, -g.E_SUP], color=g.C_COUPON, lw=2.0)
        z_bas = -g.E_SUP - g.E_FILM
        if cas == "plat":
            ep = g.E_INF
            ax.add_patch(Rectangle((a, z_bas - ep), b - a, ep, fc=g.C_COUPON, alpha=0.22, ec=g.C_COUPON, lw=0.9))
            ax.add_patch(Rectangle((a, z_bas - ep - 1.0), b - a, 1.0, fc=C_BATI, ec="0.4", hatch="\\\\\\", lw=0.6))
            titre, nom_bas = "À plat (campagne à 3 TC, mesurée)", "face opposée"
        else:
            ep = E_TUBE
            ax.add_patch(Rectangle((a, z_bas - ep), b - a, ep, fc=C_TUBE, alpha=0.35, ec=C_TUBE_BORD, lw=0.9, hatch="////"))
            ax.text((a + b) / 2, z_bas - ep - 1.6, "cavité", ha="center", va="center", fontsize=8, color="0.45",
                    style="italic")
            titre, nom_bas = "Tube substitut (proposé)", "face intérieure"
        zs = {"surface": 0.0, "interface": -g.E_SUP, nom_bas: z_bas - ep}
        for (n, z), c in zip(zs.items(), COUL_TC.values()):
            plein = not (cas == "tube" and n == nom_bas)
            ax.scatter([(a + b) / 2], [z], s=70, facecolor=c if plein else "white", edgecolor=c if not plein else "k",
                       linewidth=1.4 if not plein else 0.6, zorder=10, clip_on=False)
        g_ = (b - a) * 0.08
        cote = z_bas - ep
        ax.annotate("", xy=(b - g_, cote), xytext=(b - g_, -g.E_SUP),
                    arrowprops=dict(arrowstyle="<->", color="0.3", lw=0.7))
        ax.text(b - g_ - 0.4, (cote - g.E_SUP) / 2, f"{ep:.2f}".replace(".", ",") + " mm",
                ha="right", va="center", fontsize=7.2, color="0.3",
                bbox=dict(fc="white", ec="none", alpha=0.8, pad=1.0))
        ax.set_title(titre, fontsize=9.5)
        ax.set_xlim(a, b)
        ax.set_ylim(-g.E_SUP - g.E_FILM - g.E_INF - 1.3, g.GAP_CERAM + 0.4)
        ax.set_aspect("equal")
        ax.set_xticks([])
        for sp in ("top", "right", "bottom"):
            ax.spines[sp].set_visible(False)
    axes[0].set_ylabel("z (mm)")
    axes[0].set_yticks([-g.L_INF, -g.E_SUP - g.E_FILM - E_TUBE, -g.E_SUP, 0, g.GAP_CERAM])
    axes[0].set_yticklabels(["−6,8", "−5,1", "−3,4", "0", "2"])
    h = [Line2D([0], [0], marker="o", color="none", markerfacecolor=c, markeredgecolor="k", markersize=7,
                label=f"TC {n}") for n, c in COUL_TC.items()]
    h[2] = Line2D([0], [0], marker="o", color="none", markerfacecolor=COUL_TC["face opposée"], markeredgecolor="k",
                  markersize=7, label="TC face opposée (à plat)")
    h.append(Line2D([0], [0], marker="o", color="none", markerfacecolor="white", markeredgecolor=COUL_TC["face opposée"],
                    markeredgewidth=1.4, markersize=7, label="TC face intérieure du tube (proposé)"))
    h += [Rectangle((0, 0), 1, 1, fc=g.C_CERAM, ec=g.C_CERAM_EDGE, alpha=0.55, label="céramique"),
          Rectangle((0, 0), 1, 1, fc=g.C_COUPON, ec=g.C_COUPON, alpha=0.22, label="connecteur / laminé"),
          Rectangle((0, 0), 1, 1, fc=C_TUBE, ec=C_TUBE_BORD, alpha=0.35, hatch="////", label="paroi du tube")]
    fig.legend(handles=h, loc="upper center", ncol=4, frameon=False, fontsize=7.4, bbox_to_anchor=(0.5, 0.12))
    g.savefig(fig, OUT / "fig73_instrumentation.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    fig_mecanismes()
    fig_references()
    fig_instrumentation()
    print("ok")
