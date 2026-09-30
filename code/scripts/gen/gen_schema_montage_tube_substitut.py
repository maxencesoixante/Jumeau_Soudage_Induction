"""Schéma du montage « tube substitut » (issue #73) -- même esprit que les
schémas exp7 / exp9 (gen_schemas_montage.py, dont on réutilise style et helpers).

Le tube substitut est assemblé à partir de plaques CF/PEKK consolidées à la
presse chauffante, drapage [45,-45,0,-45,45,0_3]_S (16 plis) :
  - deux MURS de 40 mm de haut,
  - une plaque de DESSUS et une plaque de FOND de 50 mm,
  - les rainures dessus/murs et fond/murs fondues au fer à souder (maintien).
Le « connecteur » habituel ([45,-45,0,90]_3S, 120 × 40 mm, 3,36 mm) est soudé
sur la plaque de dessus, en cycle semi-statique.

Géométrie (valeurs utilisateur) : parois 1,68 mm (2026-09-28), caisson fermé
(2026-09-28), tube de 240 mm de long avec le connecteur de 120 mm centré
(2026-09-30). Hypothèses de dessin restantes : faces extérieures des murs
affleurant les bords des plaques de 50 mm ; même ligne de 5 TC d'interface
qu'en exp9 (bord du connecteur, y = 0).

Trois vues, à l'échelle 1:1 : dessus (x-y), côté (x-z) et coupe transverse
(y-z, au centre du connecteur). Consigne de lisibilité (2026-09-30) : les cotes
et la légende portent l'information, pas d'annotations explicatives.
N'écrit QUE le PNG de sortie.
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_schemas_montage as g  # noqa: E402  (style + helpers + géométrie bobine/MFC)
from gen_schemas_montage import rect  # noqa: E402

OUT = g.R / "biblio" / "labo" / "figures" / "fig_montage_tube_substitut.png"

# ----------------------------------------------------------------------
# Géométrie (mm) — repère : x le long du tube (0 à 240), y en largeur
# (connecteur de 0 à 40), z = 0 à la surface du connecteur, + vers le haut.
# ----------------------------------------------------------------------
E_TUBE = 1.68                   # parois [45,-45,0,-45,45,0_3]_S
H_MUR = 40.0                    # hauteur des murs
W_TUBE = 50.0                   # largeur des plaques de dessus et de fond
L_TUBE = 240.0                  # longueur du tube
X0_CONN = (L_TUBE - g.L) / 2    # 60 : connecteur de 120 mm centré sur le tube
Y0_TUBE = (g.W - W_TUBE) / 2    # -5 : tube centré sous le connecteur
PORTEE = W_TUBE - 2 * E_TUBE    # portée libre entre murs

Z_INTERF = -g.E_SUP                       # -3,36
Z_FILM_BOT = Z_INTERF - g.E_FILM          # -3,46
Z_DESSUS_BOT = Z_FILM_BOT - E_TUBE        # -5,14 (face intérieure du dessus)
Z_MUR_BOT = Z_DESSUS_BOT - H_MUR          # -45,14 (face intérieure du fond)
Z_FOND_BOT = Z_MUR_BOT - E_TUBE           # -46,82 (appui sur le bâti)

XC = X0_CONN + g.L / 2                    # 120 : spot au centre du connecteur
YC = g.W / 2
X_TC = [X0_CONN + x for x in (0, 30, 60, 90, 120)]

C_TUBE = "#56B4E9"
C_TUBE_BORD = "#2B7FB0"
C_SOUDURE_FER = "#D55E00"
C_BATI = "#BFBFBF"
C_EFFORT = "#009E73"


def virgule(v, n=2):
    return f"{v:.{n}f}".replace(".", ",")


def plaque_tube(ax, x0, y0, w, h, zorder=2, alpha=0.30):
    rect(ax, x0, y0, w, h, facecolor=C_TUBE, alpha=alpha, edgecolor="none", zorder=zorder)
    rect(ax, x0, y0, w, h, facecolor="none", edgecolor=C_TUBE_BORD, linewidth=0.9,
         hatch="////", alpha=0.6, zorder=zorder)


def fleche(ax, x, y0, y1):
    ax.annotate("", xy=(x, y1), xytext=(x, y0),
                arrowprops=dict(arrowstyle="-|>", color=C_EFFORT, lw=1.3, mutation_scale=9),
                zorder=12)


def connecteur_coupe(ax, a, b):
    """Connecteur + film vus en coupe sur [a, b] (z de 0 à Z_FILM_BOT)."""
    rect(ax, a, Z_INTERF, b - a, g.E_SUP, facecolor=g.C_COUPON, alpha=0.22,
         edgecolor=g.C_COUPON, linewidth=1.0, zorder=3)
    for k in range(1, 4):
        z = Z_INTERF * k / 4
        ax.plot([a, b], [z, z], color=g.C_COUPON, alpha=0.3, lw=0.4, zorder=3)
    ax.plot([a, b], [Z_INTERF, Z_INTERF], color=g.C_COUPON, lw=2.0, zorder=6,
            solid_capstyle="butt")


def habillage(ax, xlabel, ylabel, titre):
    ax.set_aspect("equal")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(titre, fontsize=10)
    ax.tick_params(length=3, labelsize=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def vue_dessus(ax):
    plaque_tube(ax, 0, Y0_TUBE, L_TUBE, W_TUBE, zorder=1)
    for yb in (Y0_TUBE, Y0_TUBE + W_TUBE - E_TUBE):           # murs, sous le dessus
        rect(ax, 0, yb, L_TUBE, E_TUBE, facecolor="none", edgecolor=C_TUBE_BORD,
             linewidth=0.8, linestyle="--", zorder=2)
    g.coupon_weave(ax, X0_CONN, 0, g.L, g.W, zorder=3)
    rect(ax, X0_CONN, 0, g.L, g.W, facecolor=g.C_CERAM, alpha=0.22,
         edgecolor=g.C_CERAM_EDGE, linewidth=0.6, zorder=4)
    g.mfc_patch(ax, XC, YC, style="solid")
    g.coil_legs_patch(ax, XC, YC)
    for i, x in enumerate(X_TC, start=1):
        g.tc_marker(ax, x, 0, f"TC{i}", dxlab=0, dylab=-19.5, fs=7.2, ha="center", va="top")
    centres = [X0_CONN + c for c in g.CENTRES_DWELL]
    ya = -33.0
    ax.annotate("", xy=(centres[-1], ya), xytext=(centres[0], ya),
                arrowprops=dict(arrowstyle="->", color="0.15", lw=1.2))
    ax.text((centres[0] + centres[-1]) / 2, ya - 2.0, "spot, pas 30 mm", ha="center",
            va="top", fontsize=7.0, color="0.15")
    y_bob = YC + g.COIL_DRAW_LEN / 2                          # haut des brins (56,5)
    g.cote_h(ax, 0, L_TUBE, y_bob + 13.0, "tube 240 mm")
    g.cote_h(ax, X0_CONN, X0_CONN + g.L, y_bob + 4.0, "connecteur 120 mm")
    g.cote_v(ax, 0, g.W, X0_CONN + g.L + 4.0, "40", right=True, fs=7.0)
    g.cote_v(ax, Y0_TUBE, Y0_TUBE + W_TUBE, L_TUBE + 5.0, "50", right=True, fs=7.0)
    ax.set_xlim(-6, L_TUBE + 16)
    ax.set_ylim(ya - 8, y_bob + 20)
    habillage(ax, "x (mm)", "y (mm)", "Vue de dessus")


def vue_cote(ax):
    # tube vu de côté : paroi de mur en face, plaques de dessus et de fond en tranche
    plaque_tube(ax, 0, Z_MUR_BOT, L_TUBE, H_MUR, zorder=2, alpha=0.12)
    plaque_tube(ax, 0, Z_DESSUS_BOT, L_TUBE, E_TUBE, zorder=3)
    plaque_tube(ax, 0, Z_FOND_BOT, L_TUBE, E_TUBE, zorder=3)
    rect(ax, -8, Z_FOND_BOT - 3.0, L_TUBE + 16, 3.0, facecolor=C_BATI, edgecolor="0.4",
         hatch="\\\\\\", linewidth=0.6, zorder=2)
    connecteur_coupe(ax, X0_CONN, X0_CONN + g.L)
    rect(ax, X0_CONN, 0, g.L, g.H_CERAM_TOP, facecolor=g.C_CERAM, alpha=0.55,
         edgecolor=g.C_CERAM_EDGE, linewidth=0.7, zorder=5)
    rect(ax, XC - g.MFC_X / 2, g.H_MFC_BOT, g.MFC_X, g.MFC_H, facecolor=g.C_MFC,
         edgecolor="0.2", alpha=0.35, linewidth=0.9, zorder=4)
    for sgn in (-1, 1):
        rect(ax, XC + sgn * g.ENTRAXE / 2 - g.TUBE / 2, g.H_TUBE_BOT, g.TUBE, g.TUBE,
             facecolor=g.C_COIL, edgecolor="0.15", linewidth=0.8, alpha=0.92, zorder=6)
    for x in X_TC:
        ax.scatter([x], [Z_INTERF], s=16, color=g.C_TC, edgecolor="black", linewidth=0.4, zorder=10)
    for x in (XC - 18, XC, XC + 18):
        fleche(ax, x, g.H_MFC_TOP + 9, g.H_MFC_TOP + 0.8)
    g.cote_h(ax, 0, L_TUBE, g.H_MFC_TOP + 18.0, "tube 240 mm")
    g.cote_h(ax, X0_CONN, X0_CONN + g.L, g.H_MFC_TOP + 12.0, "connecteur 120 mm")
    g.cote_v(ax, Z_FOND_BOT, Z_DESSUS_BOT + E_TUBE, L_TUBE + 4.0,
             f"{virgule(H_MUR + 2 * E_TUBE, 1)}", right=True, fs=7.0)
    ax.set_xlim(-10, L_TUBE + 16)
    ax.set_ylim(Z_FOND_BOT - 6, g.H_MFC_TOP + 24)
    ax.set_yticks([Z_FOND_BOT, 0, g.H_MFC_TOP])
    ax.set_yticklabels([virgule(Z_FOND_BOT, 1).replace("-", "−"), "0", "+14"])
    habillage(ax, "x (mm)", "z (mm)", "Vue de côté")


def coupe_transverse(ax):
    connecteur_coupe(ax, 0, g.W)
    plaque_tube(ax, Y0_TUBE, Z_DESSUS_BOT, W_TUBE, E_TUBE, zorder=3)
    for yb in (Y0_TUBE, Y0_TUBE + W_TUBE - E_TUBE):
        plaque_tube(ax, yb, Z_MUR_BOT, E_TUBE, H_MUR, zorder=3)
    plaque_tube(ax, Y0_TUBE, Z_FOND_BOT, W_TUBE, E_TUBE, zorder=3)
    for yb, sgn in ((Y0_TUBE + E_TUBE, 1), (Y0_TUBE + W_TUBE - E_TUBE, -1)):
        for z, m in ((Z_DESSUS_BOT - 0.6, "v"), (Z_MUR_BOT + 0.6, "^")):
            ax.scatter([yb + sgn * 0.6], [z], s=34, marker=m, color=C_SOUDURE_FER,
                       edgecolor="0.2", linewidth=0.4, zorder=9)
    rect(ax, Y0_TUBE - 6, Z_FOND_BOT - 3.0, W_TUBE + 12, 3.0, facecolor=C_BATI,
         edgecolor="0.4", hatch="\\\\\\", linewidth=0.6, zorder=2)
    rect(ax, 0, 0, g.W, g.H_CERAM_TOP, facecolor=g.C_CERAM, alpha=0.55,
         edgecolor=g.C_CERAM_EDGE, linewidth=0.7, zorder=5)
    y_lo = YC - g.MFC_Y / 2
    rect(ax, y_lo, g.H_MFC_BOT, g.MFC_Y, g.MFC_H, facecolor=g.C_MFC, edgecolor="0.2",
         alpha=0.35, linewidth=0.9, zorder=4)
    rect(ax, y_lo, g.H_TUBE_BOT, g.MFC_Y, g.TUBE, facecolor=g.C_COIL, alpha=0.45,
         edgecolor="none", zorder=5)
    for x0 in (YC - g.COIL_DRAW_LEN / 2, YC + g.MFC_Y / 2):
        rect(ax, x0, g.H_TUBE_BOT, g.COIL_OVERHANG, g.TUBE, facecolor=g.C_COIL,
             edgecolor="0.2", linewidth=0.7, alpha=0.95, zorder=6)
    g.tc_marker(ax, 0, Z_INTERF, "", dxlab=0, dylab=0)
    ax.scatter([YC], [Z_DESSUS_BOT], s=24, marker="o", facecolor="white",
               edgecolor=g.C_TC, linewidth=1.1, zorder=10)
    for y in (6, 13, 20, 27, 34):
        fleche(ax, y, g.H_MFC_TOP + 7, g.H_MFC_TOP + 0.6)
    for yb in (Y0_TUBE + E_TUBE / 2, Y0_TUBE + W_TUBE - E_TUBE / 2):
        fleche(ax, yb, Z_DESSUS_BOT - 4, Z_MUR_BOT + 2)
    g.cote_h(ax, Y0_TUBE + E_TUBE, Y0_TUBE + W_TUBE - E_TUBE, -30.0,
             f"portée libre {virgule(PORTEE, 1)}", fs=7.0)
    g.cote_h(ax, Y0_TUBE, Y0_TUBE + W_TUBE, Z_FOND_BOT - 8.0, "50", fs=7.0, above=False)
    g.cote_v(ax, Z_MUR_BOT, Z_DESSUS_BOT, Y0_TUBE + W_TUBE + 3.0, "40", fs=7.0)
    ax.text(Y0_TUBE + W_TUBE + 5.0, (Z_INTERF + Z_DESSUS_BOT) / 2 - 0.6,
            f"paroi {virgule(E_TUBE)}", fontsize=6.6, color=C_TUBE_BORD, ha="left", va="center")
    ax.text(g.W + 8.0, Z_INTERF / 2 + 0.3, f"connecteur {virgule(g.E_SUP)}",
            fontsize=6.6, color=g.C_COUPON, ha="left", va="center")
    ax.set_xlim(y_lo - 11, y_lo + g.MFC_Y + 26)
    ax.set_ylim(Z_FOND_BOT - 14, g.H_MFC_TOP + 10)
    ax.set_yticks([Z_FOND_BOT, Z_DESSUS_BOT, 0, g.H_MFC_TOP])
    ax.set_yticklabels([virgule(z, 1).replace("-", "−").replace("0,0", "0").replace("14,0", "+14")
                        for z in (Z_FOND_BOT, Z_DESSUS_BOT, 0, g.H_MFC_TOP)])
    habillage(ax, "y (mm)", "z (mm)", "Coupe transverse (centre du connecteur)")


def make():
    fig = plt.figure(figsize=(8.8, 13.2))
    gs = fig.add_gridspec(3, 1, height_ratios=[1.0, 0.95, 1.55], hspace=0.28,
                          top=0.97, bottom=0.10, left=0.10, right=0.98)
    vue_dessus(fig.add_subplot(gs[0]))
    vue_cote(fig.add_subplot(gs[1]))
    coupe_transverse(fig.add_subplot(gs[2]))

    handles = [
        Rectangle((0, 0), 1, 1, facecolor=g.C_COIL, edgecolor="0.2", label="Bobine hairpin"),
        Rectangle((0, 0), 1, 1, facecolor=g.C_MFC, edgecolor="0.2", alpha=0.35, label="Concentrateur MFC"),
        Rectangle((0, 0), 1, 1, facecolor=g.C_CERAM, edgecolor=g.C_CERAM_EDGE, alpha=0.55,
                  label="Céramique (2 mm)"),
        Rectangle((0, 0), 1, 1, facecolor=g.C_COUPON, edgecolor=g.C_COUPON, alpha=0.55, hatch="xxxx",
                  label="Connecteur [45,−45,0,90]₃ₛ"),
        Rectangle((0, 0), 1, 1, facecolor=C_TUBE, edgecolor=C_TUBE_BORD, alpha=0.6, hatch="////",
                  label="Tube [45,−45,0,−45,45,0₃]ₛ"),
        Rectangle((0, 0), 1, 1, facecolor=C_BATI, edgecolor="0.4", hatch="\\\\\\", label="Bâti"),
        Line2D([0], [0], marker="v", color="none", markerfacecolor=C_SOUDURE_FER,
               markeredgecolor="0.2", markersize=6, label="Rainure fondue au fer"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=g.C_TC, markeredgecolor="black",
               markersize=6, label="TC d'interface"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="white", markeredgecolor=g.C_TC,
               markersize=6, label="TC face intérieure (proposé)"),
        Line2D([0], [0], color=C_EFFORT, lw=1.3, marker=">", markersize=5, label="Effort de consolidation"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, 0.005), fontsize=7.8)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    g.savefig(fig, OUT)
    plt.close(fig)


if __name__ == "__main__":
    make()
    print(OUT.relative_to(g.R))
