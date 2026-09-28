"""Schéma du montage « tube substitut » (issue à venir) -- même esprit que les
schémas exp7 / exp9 (gen_schemas_montage.py, dont on réutilise style et helpers).

Le tube substitut est assemblé à partir de plaques CF/PEKK consolidées à la
presse chauffante, drapage [45,-45,0,-45,45,0_3]_S (16 plis) :
  - deux MURS de 40 mm de haut,
  - une plaque de DESSUS de 50 mm posée sur les murs,
  - les rainures dessus/murs fondues au fer à souder (assemblage de maintien).
Le « connecteur » habituel ([45,-45,0,90]_3S, 120 × 40 mm, 3,36 mm) est soudé
sur la plaque de dessus, en cycle semi-statique.

HYPOTHÈSES DE DESSIN (à confirmer terrain, reprises dans l'issue) :
  - épaisseur des parois du tube : 1,68 mm (valeur utilisateur, 2026-09-28) ;
  - section en Π, fond OUVERT : les murs reposent directement sur le bâti ;
  - faces extérieures des murs affleurant les bords de la plaque de 50 mm ;
  - tube de même longueur que le connecteur (120 mm), connecteur centré en largeur ;
  - TC : même ligne de 5 TC d'interface qu'en exp9 (bord du connecteur, y = 0).

Vues : dessus (x-y) et coupe TRANSVERSE (y-z, x = 60 mm) à l'échelle 1:1 --
la coupe transverse est ici la vue qui porte l'information (chemin d'effort).
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
# Géométrie du tube substitut (mm)
# ----------------------------------------------------------------------
E_TUBE = 1.68                   # [45,-45,0,-45,45,0_3]_S, épaisseur donnée par l'utilisateur
H_MUR = 40.0                    # hauteur des murs (plaques de 40 mm)
W_DESSUS = 50.0                 # largeur de la plaque de dessus
Y0_TUBE = (g.W - W_DESSUS) / 2  # -5 : tube centré sous le connecteur (y 0..40)
PORTEE = W_DESSUS - 2 * E_TUBE  # portée libre entre murs, 46,64 mm

# cotes z (0 = surface du connecteur, + vers le haut)
Z_INTERF = -g.E_SUP                       # -3,36
Z_FILM_BOT = Z_INTERF - g.E_FILM          # -3,46
Z_DESSUS_BOT = Z_FILM_BOT - E_TUBE        # -5,14 (face intérieure, côté cavité)
Z_MUR_BOT = Z_DESSUS_BOT - H_MUR          # -45,14 (appui sur le bâti)

C_TUBE = "#56B4E9"      # bleu ciel Okabe-Ito : plaques du tube (≠ connecteur)
C_SOUDURE_FER = "#D55E00"  # vermillon : rainures fondues au fer
C_BATI = "#BFBFBF"
C_EFFORT = "#009E73"    # vert : chemin d'effort


def plaque_tube(ax, x0, y0, w, h, zorder=2, **kw):
    rect(ax, x0, y0, w, h, facecolor=C_TUBE, alpha=0.30, edgecolor="none", zorder=zorder)
    rect(ax, x0, y0, w, h, facecolor="none", edgecolor="#2B7FB0", linewidth=0.9,
         hatch="////", alpha=0.6, zorder=zorder, **kw)


def fleche(ax, x, y0, y1, **kw):
    ax.annotate("", xy=(x, y1), xytext=(x, y0),
                arrowprops=dict(arrowstyle="-|>", color=C_EFFORT, lw=1.3,
                                mutation_scale=9, **kw), zorder=12)


def make():
    fig = plt.figure(figsize=(8.8, 12.4))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 1.25], hspace=0.22,
                          top=0.965, bottom=0.10, left=0.12, right=0.97)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    xc, yc = 60.0, 20.0

    # --- Panneau 1 : vue de dessus -----------------------------------------
    plaque_tube(ax1, 0, Y0_TUBE, g.L, W_DESSUS, zorder=1)
    for yb in (Y0_TUBE, Y0_TUBE + W_DESSUS - E_TUBE):          # murs, sous le dessus
        rect(ax1, 0, yb, g.L, E_TUBE, facecolor="none", edgecolor="#2B7FB0",
             linewidth=0.8, linestyle="--", zorder=2)
    g.coupon_weave(ax1, 0, 0, g.L, g.W, zorder=3)
    rect(ax1, 0, 0, g.L, g.W, facecolor=g.C_CERAM, alpha=0.22, edgecolor=g.C_CERAM_EDGE,
         linewidth=0.6, zorder=4)                               # céramique
    g.mfc_patch(ax1, xc, yc, style="solid")
    g.coil_legs_patch(ax1, xc, yc)
    for i, x in enumerate([0, 30, 60, 90, 120], start=1):
        g.tc_marker(ax1, x, 0, f"TC{i}", dxlab=0, dylab=-9.0, fs=7.4, ha="center", va="top")

    y_arrow = -24.0
    ax1.annotate("", xy=(g.CENTRES_DWELL[-1], y_arrow), xytext=(g.CENTRES_DWELL[0], y_arrow),
                 arrowprops=dict(arrowstyle="->", color="0.15", lw=1.3))
    ax1.text((g.CENTRES_DWELL[0] + g.CENTRES_DWELL[-1]) / 2, y_arrow - 2.2,
             "cycle semi-statique : avance du spot, pas ≈ 30 mm",
             ha="center", va="top", fontsize=7.2, color="0.15", fontweight="bold")
    g.cote_h(ax1, 0, g.L, g.W + 27.0, "L = 120 mm (tube et connecteur)")
    g.cote_v(ax1, 0, g.W, g.L + 4.0, "connecteur 40", right=True, fs=7.0)
    g.cote_v(ax1, Y0_TUBE, Y0_TUBE + W_DESSUS, g.L + 11.0, "tube 50", right=True, fs=7.0)
    ax1.text(-3, Y0_TUBE + W_DESSUS - E_TUBE / 2, "mur", ha="right", va="center",
             fontsize=6.8, color="#2B7FB0")
    ax1.text(-3, Y0_TUBE + E_TUBE / 2, "mur", ha="right", va="center",
             fontsize=6.8, color="#2B7FB0")

    ax1.set_xlim(-12, g.L + 20)
    ax1.set_ylim(y_arrow - 8, g.W + 33)
    ax1.set_aspect("equal")
    ax1.set_xlabel("x (mm) — longueur")
    ax1.set_ylabel("y (mm) — largeur")
    ax1.set_title("Vue de dessus (plan x–y) — connecteur soudé sur le tube substitut",
                  fontsize=10)
    ax1.tick_params(length=3)
    for s in ("top", "right"):
        ax1.spines[s].set_visible(False)

    # --- Panneau 2 : coupe transverse y-z à x = 60 mm, 1:1 -------------------
    # connecteur (0 .. -3,36), film, plaque de dessus du tube, murs, bâti
    rect(ax2, 0, Z_INTERF, g.W, g.E_SUP, facecolor=g.C_COUPON, alpha=0.22,
         edgecolor=g.C_COUPON, linewidth=1.0, zorder=3)
    for k in range(1, 4):
        z = Z_INTERF * k / 4
        ax2.plot([0, g.W], [z, z], color=g.C_COUPON, alpha=0.3, lw=0.4, zorder=3)
    ax2.plot([0, g.W], [Z_INTERF, Z_INTERF], color=g.C_COUPON, lw=2.0, zorder=6,
             solid_capstyle="butt")
    plaque_tube(ax2, Y0_TUBE, Z_DESSUS_BOT, W_DESSUS, E_TUBE, zorder=3)
    for yb in (Y0_TUBE, Y0_TUBE + W_DESSUS - E_TUBE):
        plaque_tube(ax2, yb, Z_MUR_BOT, E_TUBE, H_MUR, zorder=3)
    # rainures fondues au fer (coins intérieurs dessus/mur)
    for yb, sgn in ((Y0_TUBE + E_TUBE, 1), (Y0_TUBE + W_DESSUS - E_TUBE, -1)):
        ax2.scatter([yb + sgn * 0.6], [Z_DESSUS_BOT - 0.6], s=38, marker="v",
                    color=C_SOUDURE_FER, edgecolor="0.2", linewidth=0.4, zorder=9)
    # bâti
    rect(ax2, Y0_TUBE - 6, Z_MUR_BOT - 3.0, W_DESSUS + 12, 3.0, facecolor=C_BATI,
         edgecolor="0.4", hatch="\\\\\\", linewidth=0.6, zorder=2)
    # céramique + MFC + tubes Cu (vus en long : ils courent selon y)
    rect(ax2, 0, 0, g.W, g.H_CERAM_TOP, facecolor=g.C_CERAM, alpha=0.55,
         edgecolor=g.C_CERAM_EDGE, linewidth=0.7, zorder=5)
    y_lo = yc - g.MFC_Y / 2
    rect(ax2, y_lo, g.H_MFC_BOT, g.MFC_Y, g.MFC_H, facecolor=g.C_MFC, edgecolor="0.2",
         alpha=0.35, linewidth=0.9, zorder=4)
    rect(ax2, y_lo, g.H_TUBE_BOT, g.MFC_Y, g.TUBE, facecolor=g.C_COIL, alpha=0.45,
         edgecolor="none", zorder=5)
    for x0 in (yc - g.COIL_DRAW_LEN / 2, yc + g.MFC_Y / 2):
        rect(ax2, x0, g.H_TUBE_BOT, g.COIL_OVERHANG, g.TUBE, facecolor=g.C_COIL,
             edgecolor="0.2", linewidth=0.7, alpha=0.95, zorder=6)
    ax2.text(yc, g.H_MFC_TOP - 2.4, "MFC", ha="center", va="center", fontsize=8,
             bbox=g.BOXPROPS, zorder=8)

    # TC1..5 sont sur la ligne y = 0 ; TC d'interface vu en coupe au bord
    g.tc_marker(ax2, 0, Z_INTERF, "TC3", dxlab=-2.0, dylab=0, fs=6.8, ha="right",
                va="center")
    # TC proposé face intérieure (côté cavité) pour la question thermique
    ax2.scatter([yc], [Z_DESSUS_BOT], s=26, marker="o", facecolor="white",
                edgecolor=g.C_TC, linewidth=1.1, zorder=10)
    ax2.annotate("TC face intérieure\n(proposé, x = 60)", (yc, Z_DESSUS_BOT),
                 xytext=(yc, Z_DESSUS_BOT - 7.5), fontsize=6.8, color=g.C_TC,
                 ha="center", va="top", zorder=10, bbox=g.BOXPROPS,
                 arrowprops=dict(arrowstyle="-", color=g.C_TC, lw=0.6))

    # chemin d'effort : pression de consolidation -> dessus -> murs -> bâti
    for y in (6, 13, 20, 27, 34):
        fleche(ax2, y, g.H_MFC_TOP + 7, g.H_MFC_TOP + 0.6)
    ax2.text(yc, g.H_MFC_TOP + 7.8, "pression de consolidation", ha="center",
             va="bottom", fontsize=7.6, color=C_EFFORT, fontweight="bold")
    for yb in (Y0_TUBE + E_TUBE / 2, Y0_TUBE + W_DESSUS - E_TUBE / 2):
        fleche(ax2, yb, Z_DESSUS_BOT - 4, Z_MUR_BOT + 2)
    ax2.text(yc, -26, "cavité d'air\n(pas de contre-pression)", ha="center",
             va="center", fontsize=7.6, color="0.3", style="italic")
    ax2.annotate("rainures fondues\nau fer à souder", xy=(Y0_TUBE + E_TUBE + 0.8, Z_DESSUS_BOT - 0.8),
                 xytext=(Y0_TUBE + 6, -15), fontsize=6.8, color=C_SOUDURE_FER, ha="left",
                 va="center", zorder=10, bbox=g.BOXPROPS,
                 arrowprops=dict(arrowstyle="-", color=C_SOUDURE_FER, lw=0.6))
    ax2.text(yc, Z_MUR_BOT - 4.5, "bâti — les murs reprennent l'effort", ha="center",
             va="top", fontsize=7.2, color="0.25")

    # cotes
    g.cote_h(ax2, Y0_TUBE + E_TUBE, Y0_TUBE + W_DESSUS - E_TUBE, -36.5,
             f"portée libre {PORTEE:.1f} mm".replace(".", ","), fs=7.0)
    g.cote_v(ax2, Z_MUR_BOT, Z_DESSUS_BOT, Y0_TUBE + W_DESSUS + 3.0,
             f"mur {H_MUR:.0f} mm", fs=7.0)
    ax2.text(Y0_TUBE + W_DESSUS + 4.5, (Z_INTERF + Z_DESSUS_BOT) / 2 - 0.6,
             f"dessus {E_TUBE:.2f} mm".replace(".", ","), fontsize=6.6, color="#2B7FB0", ha="left", va="center")
    ax2.text(g.W + 7.5, Z_INTERF / 2 + 0.3, f"connecteur {g.E_SUP:.2f} mm".replace(".", ","),
             fontsize=6.6, color=g.C_COUPON, ha="left", va="center")

    ax2.set_xlim(y_lo - 11, y_lo + g.MFC_Y + 22)
    ax2.set_ylim(Z_MUR_BOT - 9, g.H_MFC_TOP + 12)
    ax2.set_aspect("equal")
    ax2.set_xlabel("y (mm) — largeur (coupe à x = 60 mm)")
    ax2.set_ylabel("z (mm) — hauteur\n(0 = surface du connecteur)")
    ax2.set_title("Coupe transverse (plan y–z, x = 60 mm) — échelle 1:1", fontsize=10)
    ax2.set_yticks([Z_MUR_BOT, Z_DESSUS_BOT, 0, g.H_MFC_TOP])
    ax2.set_yticklabels([f"{z:+.1f}".replace("-", "−").replace(".", ",").replace("+0,0", "0")
                         for z in (Z_MUR_BOT, Z_DESSUS_BOT, 0, g.H_MFC_TOP)])
    ax2.tick_params(length=3, labelsize=8)
    for s in ("top", "right"):
        ax2.spines[s].set_visible(False)

    handles = [
        Rectangle((0, 0), 1, 1, facecolor=g.C_COIL, edgecolor="0.2", label="Bobine hairpin (Cu, tube 6 mm)"),
        Rectangle((0, 0), 1, 1, facecolor=g.C_MFC, edgecolor="0.2", alpha=0.35, label="Concentrateur MFC"),
        Rectangle((0, 0), 1, 1, facecolor=g.C_CERAM, edgecolor=g.C_CERAM_EDGE, alpha=0.55,
                  label="Céramique (2 mm)"),
        Rectangle((0, 0), 1, 1, facecolor=g.C_COUPON, edgecolor=g.C_COUPON, alpha=0.55, hatch="xxxx",
                  label="Connecteur [45,−45,0,90]₃ₛ"),
        Rectangle((0, 0), 1, 1, facecolor=C_TUBE, edgecolor="#2B7FB0", alpha=0.6, hatch="////",
                  label="Tube substitut [45,−45,0,−45,45,0₃]ₛ"),
        Line2D([0], [0], marker="v", color="none", markerfacecolor=C_SOUDURE_FER,
               markeredgecolor="0.2", markersize=6, label="Rainure fondue au fer"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=g.C_TC, markeredgecolor="black",
               markersize=6, label="TC d'interface (ligne y = 0)"),
        Line2D([0], [0], color=C_EFFORT, lw=1.3, marker=">", markersize=5, label="Chemin d'effort"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, 0.005), fontsize=7.8)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    g.savefig(fig, OUT)
    plt.close(fig)


if __name__ == "__main__":
    make()
    print(OUT.relative_to(g.R))
