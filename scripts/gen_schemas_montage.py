"""Schemas de montage exp7 / exp9 -- deux vues (plan x-y + coupe), format
article (style docs/figures_elsevier, cf. scripts/gen_figures_elsevier.py).

Les deux vues sont disposees COTE A COTE (vue de dessus | vue en coupe).

Geometrie prise EXCLUSIVEMENT dans config/geometrie.yaml et
config/materiaux.yaml (valeurs recopiees en tete de script, avec la source).

N'ecrit QUE les deux PNG de sortie -- ne touche a aucun autre fichier du repo.
"""
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from pathlib import Path

OUT = Path("/Users/maxencedubois/PycharmProjects/Jumeau_Soudage_Induction/docs/figures_elsevier")

# ----------------------------------------------------------------------
# rcParams -- meme style que gen_figures_elsevier.py (police sans-serif,
# 600 dpi, fond blanc)
# ----------------------------------------------------------------------
mpl.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "mathtext.fontset": "dejavusans",
    "font.size": 10, "axes.labelsize": 10.5, "axes.labelweight": "bold",
    "axes.titlesize": 11, "legend.fontsize": 8.5,
    "xtick.labelsize": 9, "ytick.labelsize": 9,
    "axes.linewidth": 0.8,
    "lines.linewidth": 1.2,
    "figure.dpi": 600, "savefig.dpi": 600, "savefig.bbox": "tight",
    "savefig.pad_inches": 0.08, "figure.facecolor": "white", "savefig.facecolor": "white",
})

# Okabe-Ito palette imposee
C_COIL = "#E69F00"     # cuivre / bobine
C_MFC = "#7F7F7F"      # gris / concentrateur (Magnetic Flux Concentrator)
C_COUPON = "#0072B2"   # bleu / coupon-twill
C_TC = "#C1272D"       # rouge / thermocouples
C_CERAM = "#CDE6F5"    # bleu tres clair / ceramique
C_FILM = "#EFEFEF"     # gris tres clair / film PEKK

BOXPROPS = dict(facecolor="white", alpha=0.82, edgecolor="none", pad=1.2)

# ----------------------------------------------------------------------
# Geometrie (mm) -- source config/geometrie.yaml, config/materiaux.yaml
# ----------------------------------------------------------------------
L = 120.0                 # laminate.longueur (x)
W = 40.0                  # laminate.largeur (y)
E_SUP = 3.36              # laminate.epaisseur_sup
E_FILM = 0.10             # laminate.epaisseur_film
E_INF = 3.36              # laminate.epaisseur_inf
Z_INTERFACE = E_SUP       # twill susceptor a l'interface de soudure
E_TWILL_NOM = 0.28        # twill_suscepteur.epaisseur (valeur active config)
L_INF = E_SUP + E_FILM + E_INF

GAP_CERAM = 2.0           # ceramique.epaisseur
TUBE = 6.0                # coil.rayon_tube * 2 (tube carre 6 mm)
ENTRAXE = 12.35           # coil.entraxe_jambes
LEG_LEN = 55.0             # coil.longueur_jambe
COIL_AXIS_H = 5.0         # coil.hauteur (axe au-dessus de la surface)

MFC_Y = 55.0               # cfc.longueur (grand cote, // y)
MFC_X = 31.5               # cfc.largeur (// x, direction du deplacement)
MFC_H = 12.0               # cfc.hauteur

# z (mm), convention config: z=0 surface superieure, z croit vers le bas
Z_TUBE_BOT = -GAP_CERAM                    # -2   (repose sur la ceramique)
Z_TUBE_TOP = -(GAP_CERAM + TUBE)           # -8
Z_MFC_BOT = -(COIL_AXIS_H + TUBE / 2)      # -8   (plan image = sommet des brins)
Z_MFC_TOP = Z_MFC_BOT - MFC_H              # -20

# Empreintes (cahier / config)
CENTRES_DWELL = [15.875, 45.875, 75.875, 105.875]   # empreintes.centres_pas30 (mm)

Z_SCALE = 2.6   # exageration de l'echelle z dans les vues en coupe


# ----------------------------------------------------------------------
# Helpers de cotation
# ----------------------------------------------------------------------
def cote_h(ax, x0, x1, y, text, color="0.25", above=True, fs=7.6):
    ax.annotate("", xy=(x1, y), xytext=(x0, y),
                arrowprops=dict(arrowstyle="<->", color=color, lw=0.7, shrinkA=0, shrinkB=0))
    dy = 0.012 * (ax.get_ylim()[1] - ax.get_ylim()[0])
    va = "bottom" if above else "top"
    ax.text((x0 + x1) / 2, y + (dy if above else -dy), text, ha="center", va=va,
            fontsize=fs, color=color)


def cote_v(ax, y0, y1, x, text, color="0.25", right=True, fs=7.6):
    ax.annotate("", xy=(x, y1), xytext=(x, y0),
                arrowprops=dict(arrowstyle="<->", color=color, lw=0.7, shrinkA=0, shrinkB=0))
    dx = 0.012 * (ax.get_xlim()[1] - ax.get_xlim()[0])
    ha = "left" if right else "right"
    ax.text(x + (dx if right else -dx), (y0 + y1) / 2, text, ha=ha, va="center",
            fontsize=fs, color=color, rotation=90)


def rect(ax, x0, y0, w, h, **kw):
    ax.add_patch(Rectangle((x0, y0), w, h, **kw))


def coil_legs_patch(ax, xc, yc):
    """Les deux jambes de la bobine hairpin, centrees sur (xc, yc)."""
    for sgn in (-1, 1):
        x_leg = xc + sgn * ENTRAXE / 2 - TUBE / 2
        rect(ax, x_leg, yc - LEG_LEN / 2, TUBE, LEG_LEN,
             facecolor=C_COIL, edgecolor="0.2", linewidth=0.7, alpha=0.95, zorder=5)


def mfc_patch(ax, xc, yc, style="solid"):
    x0, y0 = xc - MFC_X / 2, yc - MFC_Y / 2
    if style == "solid":
        rect(ax, x0, y0, MFC_X, MFC_Y, facecolor=C_MFC, edgecolor="0.2",
             linewidth=0.9, alpha=0.35, zorder=3)
    elif style == "dashed":
        rect(ax, x0, y0, MFC_X, MFC_Y, facecolor="none", edgecolor=C_MFC,
             linewidth=1.1, linestyle="--", zorder=3)
    elif style == "dotted":
        rect(ax, x0, y0, MFC_X, MFC_Y, facecolor="none", edgecolor="0.35",
             linewidth=1.0, linestyle=":", zorder=3)


def tc_marker(ax, x, y, label, dxlab=0, dylab=2.6, fs=7.4, ha="center", va="bottom"):
    ax.scatter([x], [y], s=22, marker="o", color=C_TC, edgecolor="black",
               linewidth=0.4, zorder=10)
    ax.annotate(label, (x, y), xytext=(x + dxlab, y + dylab), fontsize=fs,
                color=C_TC, ha=ha, va=va, zorder=10, fontweight="bold")


LEGEND_HANDLES = [
    Rectangle((0, 0), 1, 1, facecolor=C_COIL, edgecolor="0.2", label="Bobine hairpin (Cu, tube 6 mm)"),
    Rectangle((0, 0), 1, 1, facecolor=C_MFC, edgecolor="0.2", alpha=0.35, label="Concentrateur MFC (Ferrotron 559H)"),
    Rectangle((0, 0), 1, 1, facecolor=C_COUPON, edgecolor="0.2", alpha=0.25, label="Coupon CF/PEKK (laminé)"),
    Line2D([0], [0], marker="o", color="none", markerfacecolor=C_TC, markeredgecolor="black",
           markersize=6, label="Thermocouple (à l'interface, z = 3,36 mm)"),
]


def epaisseurs_box(ax, x, y, avec_tube=True):
    lignes = [
        "Épaisseurs (échelle z dilatée) :",
        f"céramique {GAP_CERAM:.2f} mm",
        f"laminé sup. {E_SUP:.2f} mm",
        f"film PEKK {E_FILM:.2f} mm",
        f"laminé inf. {E_INF:.2f} mm",
    ]
    if avec_tube:
        lignes.append(f"tube Cu (brin) {TUBE:.0f}×{TUBE:.0f} mm")
    txt = "\n".join(lignes)
    ax.text(x, y, txt, fontsize=6.9, color="0.2", ha="left", va="center",
            bbox=dict(facecolor="white", edgecolor="0.6", linewidth=0.6, pad=4.0), zorder=20)


# ========================================================================
# FIGURE exp7 -- cartographie bord -> centre en LARGEUR
# ========================================================================
def make_exp7():
    fig = plt.figure(figsize=(15.0, 6.4))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.15], wspace=0.16,
                          top=0.86, bottom=0.16, left=0.055, right=0.985)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])

    xc, yc = 60.0, 20.0

    # --- Panneau 1 : vue de dessus (x-y) ---------------------------------
    rect(ax1, 0, 0, L, W, facecolor=C_COUPON, edgecolor=C_COUPON, alpha=0.20,
         linewidth=1.4, zorder=1)
    mfc_patch(ax1, xc, yc, style="solid")
    coil_legs_patch(ax1, xc, yc)

    ys_tc = [0, 10, 20, 30, 40]
    for i, y in enumerate(ys_tc, start=1):
        tc_marker(ax1, xc, y, f"TC{i}\n({xc:.0f}, {y})", dxlab=18.5, dylab=0, fs=7.2,
                  ha="left", va="center")

    # cotes
    cote_h(ax1, 0, L, -13.0, "L = 120 mm", above=False)
    cote_v(ax1, 0, W, -9.0, "l = 40 mm", right=False)
    cote_h(ax1, xc - ENTRAXE / 2, xc + ENTRAXE / 2, W + 12.0, f"entraxe {ENTRAXE:.2f} mm", fs=6.8)
    cote_h(ax1, xc - MFC_X / 2, xc + MFC_X / 2, W + 17.0, f"MFC {MFC_X:.1f} mm (x)", fs=6.8)
    cote_v(ax1, yc - MFC_Y / 2, yc + MFC_Y / 2, L + 8.0, f"MFC {MFC_Y:.0f} mm (y)", fs=6.8)
    ax1.text(xc, -20.5, "Spot d'induction centré (x=60, y=20) — bobine + MFC centrés",
             ha="center", va="top", fontsize=7.6, color="0.25", style="italic")

    ax1.set_xlim(-18, L + 20)
    ax1.set_ylim(-27, W + 24)
    ax1.set_aspect("equal")
    ax1.set_xlabel("x (mm) — longueur du coupon")
    ax1.set_ylabel("y (mm) — largeur")
    ax1.set_title("Vue de dessus (plan x–y)\nempreinte bobine/MFC et 5 TC bord→centre",
                  fontsize=9.6)
    ax1.tick_params(length=3)
    for s in ("top", "right"):
        ax1.spines[s].set_visible(False)

    # --- Panneau 2 : coupe y-z a x = 60 mm (plan du spot) -----------------
    def zz(z):
        return -z * Z_SCALE

    y0c, y1c = -W * 0.30, W * 1.30  # marge pour montrer le debord du MFC (55>40)

    # MFC (plein, coupe au niveau du spot, deborde la largeur)
    rect(ax2, yc - MFC_Y / 2, zz(Z_MFC_TOP), MFC_Y, zz(Z_MFC_BOT) - zz(Z_MFC_TOP),
         facecolor=C_MFC, edgecolor="0.2", alpha=0.35, linewidth=0.9, zorder=3)
    ax2.text(yc, zz((Z_MFC_TOP + Z_MFC_BOT) / 2), "MFC (µr≈16)", ha="center", va="center",
             fontsize=7.4, bbox=BOXPROPS, zorder=6)

    # ceramique
    rect(ax2, 0, zz(0), W, zz(-GAP_CERAM) - zz(0), facecolor=C_CERAM, edgecolor="0.3",
         linewidth=0.7, zorder=2)

    # laminate sup / twill-interface / film / laminate inf
    rect(ax2, 0, zz(0), W, zz(E_SUP) - zz(0), facecolor=C_COUPON, alpha=0.22,
         edgecolor="none", zorder=2)
    rect(ax2, 0, zz(E_SUP), W, zz(E_SUP + E_FILM) - zz(E_SUP), facecolor=C_FILM,
         edgecolor="none", zorder=2)
    rect(ax2, 0, zz(E_SUP + E_FILM), W, zz(L_INF) - zz(E_SUP + E_FILM),
         facecolor=C_COUPON, alpha=0.22, edgecolor="none", zorder=2)
    ax2.plot([0, W], [zz(Z_INTERFACE), zz(Z_INTERFACE)], color=C_COUPON, linewidth=2.4,
             zorder=6, solid_capstyle="butt")

    # contour general du stack laminate + ceramique
    rect(ax2, 0, zz(0), W, zz(-GAP_CERAM) - zz(0), facecolor="none", edgecolor="0.3",
         linewidth=0.7, zorder=4)
    rect(ax2, 0, zz(L_INF), W, zz(0) - zz(L_INF), facecolor="none", edgecolor=C_COUPON,
         linewidth=1.0, zorder=4)

    # bord du coupon (0 et W) marque explicitement (le MFC deborde)
    ax2.plot([0, 0], [zz(-GAP_CERAM), zz(L_INF)], color=C_COUPON, linewidth=1.0, zorder=4)
    ax2.plot([W, W], [zz(-GAP_CERAM), zz(L_INF)], color=C_COUPON, linewidth=1.0, zorder=4)

    # note brins hors coupe (coupe a x=60, les brins sont en x=53,8 / 66,2)
    ax2.text(y0c + 1.0, zz(Z_TUBE_TOP + (Z_TUBE_BOT - Z_TUBE_TOP) / 2),
             "brins bobine\nhors coupe\n(x=53,8 / 66,2 mm)", fontsize=6.4, color=C_COIL,
             ha="left", va="center", style="italic")

    # TC (a l'interface, sur la coupe)
    for i, y in enumerate(ys_tc, start=1):
        tc_marker(ax2, y, zz(Z_INTERFACE), f"TC{i}", dxlab=0, dylab=zz(0) - zz(1.7),
                  fs=7.0, ha="center", va="bottom")

    # legende interface + boite epaisseurs, toutes deux SOUS le stack (zone libre)
    y_bottom_stack = zz(L_INF)
    ax2.text(W / 2, y_bottom_stack - 3.0,
             f"Interface soudure — pli twill (susceptible) ≈{E_TWILL_NOM:.2f} mm — "
             f"z = {Z_INTERFACE:.2f} mm (plan des TC)",
             fontsize=7.2, color=C_COUPON, ha="center", va="top", fontweight="bold")

    epaisseurs_box(ax2, W + 6.0, zz(L_INF / 2), avec_tube=True)

    ax2.set_xlim(y0c, y1c + 30)
    ax2.set_ylim(y_bottom_stack - 9, zz(Z_MFC_TOP) + 4)
    ax2.set_xlabel("y (mm) — largeur (coupe à x = 60 mm)")
    ax2.set_ylabel("(coupe verticale, échelle z dilatée ×2,6)")
    ax2.set_title("Vue en coupe (plan y–z, x = 60 mm)\nempilement et TC à l'interface",
                  fontsize=9.6)
    ax2.set_yticks([])
    for s in ("top", "right", "left"):
        ax2.spines[s].set_visible(False)
    ax2.tick_params(length=3)

    fig.legend(handles=LEGEND_HANDLES, loc="lower center", ncol=4, frameon=False,
               bbox_to_anchor=(0.5, 0.005), fontsize=8.0)
    fig.suptitle("Montage — exp7 : cartographie en largeur (profil M)",
                 fontsize=13, fontweight="bold", y=0.975)

    fig.savefig(OUT / "schema_montage_exp7.png")
    plt.close(fig)


# ========================================================================
# FIGURE exp9 -- dissipation LONGITUDINALE
# ========================================================================
def make_exp9():
    fig = plt.figure(figsize=(15.6, 6.2))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.28], wspace=0.14,
                          top=0.85, bottom=0.16, left=0.045, right=0.99)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])

    yc = 20.0
    xc_spot = 60.0

    # --- Panneau 1 : vue de dessus (x-y) ----------------------------------
    rect(ax1, 0, 0, L, W, facecolor=C_COUPON, edgecolor=C_COUPON, alpha=0.20,
         linewidth=1.4, zorder=1)

    # mode (a) spot unique -- MFC + bobine, trait plein
    mfc_patch(ax1, xc_spot, yc, style="solid")
    coil_legs_patch(ax1, xc_spot, yc)

    # mode (b) 4 positions de dwell -- MFC en pointille
    for j, xd in enumerate(CENTRES_DWELL, start=1):
        mfc_patch(ax1, xd, yc, style="dotted")
        ax1.text(xd, yc - MFC_Y / 2 - 2.0, f"d{j}", ha="center", va="top",
                 fontsize=6.6, color="0.30", fontweight="bold")

    # TC au bord y=0 (rangee bien sous l'empreinte MFC, qui deborde jusqu'a y=-7.5)
    xs_tc = [0, 30, 60, 90, 120]
    for i, x in enumerate(xs_tc, start=1):
        tc_marker(ax1, x, 0, f"TC{i}\n({x}, 0)", dxlab=0, dylab=-11.0, fs=7.0, ha="center", va="top")

    # fleche d'avance du spot (mode b) -- rangee sous les tags d1..d4 et les TC
    y_arrow = -25.0
    ax1.annotate("", xy=(CENTRES_DWELL[-1], y_arrow), xytext=(CENTRES_DWELL[0], y_arrow),
                 arrowprops=dict(arrowstyle="->", color="0.15", lw=1.3))
    ax1.text((CENTRES_DWELL[0] + CENTRES_DWELL[-1]) / 2, y_arrow - 2.2,
             "avance du spot, pas ≈ 30 mm",
             ha="center", va="top", fontsize=7.2, color="0.15", fontweight="bold")

    cote_h(ax1, 0, L, W + 26.0, "L = 120 mm", above=True)
    cote_v(ax1, 0, W, L + 5.0, "l = 40 mm", right=True)
    cote_h(ax1, xc_spot - MFC_X / 2, xc_spot + MFC_X / 2, yc + MFC_Y / 2 + 12.5,
           f"MFC {MFC_X:.1f} mm (x)", fs=6.6)

    ax1.set_xlim(-12, L + 22)
    ax1.set_ylim(y_arrow - 8, W + 34)
    ax1.set_aspect("equal")
    ax1.set_xlabel("x (mm) — longueur du coupon")
    ax1.set_ylabel("y (mm) — largeur")
    ax1.set_title("Vue de dessus (plan x–y) — 5 TC au bord (y=0)\n"
                  "(a) spot unique centré x=60   (b) 4 dwells, avance 30 mm",
                  fontsize=9.4)
    ax1.tick_params(length=3)
    for s in ("top", "right"):
        ax1.spines[s].set_visible(False)

    # --- Panneau 2 : coupe x-z a y = 0 mm (ligne des TC) -------------------
    def zz(z):
        return -z * Z_SCALE

    x0c, x1c = -10.0, L + 55.0

    # laminate sup / interface / film / laminate inf, sur toute la longueur
    rect(ax2, 0, zz(0), L, zz(E_SUP) - zz(0), facecolor=C_COUPON, alpha=0.22,
         edgecolor="none", zorder=2)
    rect(ax2, 0, zz(E_SUP), L, zz(E_SUP + E_FILM) - zz(E_SUP), facecolor=C_FILM,
         edgecolor="none", zorder=2)
    rect(ax2, 0, zz(E_SUP + E_FILM), L, zz(L_INF) - zz(E_SUP + E_FILM),
         facecolor=C_COUPON, alpha=0.22, edgecolor="none", zorder=2)
    ax2.plot([0, L], [zz(Z_INTERFACE), zz(Z_INTERFACE)], color=C_COUPON, linewidth=2.2,
             zorder=6, solid_capstyle="butt")
    rect(ax2, 0, zz(L_INF), L, zz(0) - zz(L_INF), facecolor="none", edgecolor=C_COUPON,
         linewidth=1.0, zorder=4)

    # ceramique, sur toute la longueur
    rect(ax2, 0, zz(0), L, zz(-GAP_CERAM) - zz(0), facecolor=C_CERAM, edgecolor="0.3",
         linewidth=0.7, zorder=2)

    # MFC dwell (pointille) -- 4 positions, pas de bobine (pour lisibilite)
    for xd in CENTRES_DWELL:
        rect(ax2, xd - MFC_X / 2, zz(Z_MFC_TOP), MFC_X, zz(Z_MFC_BOT) - zz(Z_MFC_TOP),
             facecolor="none", edgecolor="0.35", linewidth=0.9, linestyle=":", zorder=3)

    # MFC + bobine spot unique (trait plein / cuivre), cut a y=0 => dans l'empreinte
    rect(ax2, xc_spot - MFC_X / 2, zz(Z_MFC_TOP), MFC_X, zz(Z_MFC_BOT) - zz(Z_MFC_TOP),
         facecolor=C_MFC, edgecolor="0.2", alpha=0.35, linewidth=1.0, zorder=4)
    ax2.text(xc_spot, zz((Z_MFC_TOP + Z_MFC_BOT) / 2 - 1.6), "MFC\n(spot unique)", ha="center",
             va="center", fontsize=7.0, bbox=BOXPROPS, zorder=7)
    # 2 brins Cu = carres 6 mm, bord INFERIEUR colle au bord inferieur du MFC
    # (les tubes traversent le MFC ; leur face basse coincide avec le plan image).
    z_sq_bot = Z_MFC_BOT           # -8  (bas du carre = bas du MFC)
    z_sq_top = Z_MFC_BOT - TUBE    # -14 (haut du carre, dans le MFC)
    for sgn in (-1, 1):
        xt = xc_spot + sgn * ENTRAXE / 2 - TUBE / 2
        rect(ax2, xt, zz(z_sq_bot), TUBE, zz(z_sq_top) - zz(z_sq_bot),
             facecolor=C_COIL, edgecolor="0.2", linewidth=0.8, zorder=6)
    ax2.annotate("2 brins Cu 6×6 mm\n(bord bas au ras du MFC)",
                 xy=(xc_spot + ENTRAXE / 2 + TUBE / 2, zz((z_sq_top + z_sq_bot) / 2)),
                 xytext=(xc_spot + ENTRAXE / 2 + TUBE / 2 + 7,
                         zz((z_sq_top + z_sq_bot) / 2)),
                 fontsize=6.8, color="0.2", ha="left", va="center", zorder=7,
                 bbox=BOXPROPS,
                 arrowprops=dict(arrowstyle="-", color="0.4", lw=0.6))

    # TC sur l'interface, x = 0/30/60/90/120 (coupe exacte a y=0)
    for i, x in enumerate(xs_tc, start=1):
        tc_marker(ax2, x, zz(Z_INTERFACE), f"TC{i}", dxlab=0, dylab=zz(0) - zz(1.7),
                  fs=7.0, ha="center", va="bottom")

    # legende interface + boite epaisseurs, toutes deux SOUS le stack (zone libre)
    y_bottom_stack = zz(L_INF)
    ax2.text(L / 2, y_bottom_stack - 3.0,
             f"Interface soudure — pli twill (susceptible) ≈{E_TWILL_NOM:.2f} mm — "
             f"z = {Z_INTERFACE:.2f} mm — bord y=0 (ligne des TC)",
             fontsize=7.2, color=C_COUPON, ha="center", va="top", fontweight="bold")

    epaisseurs_box(ax2, L + 8.0, zz(L_INF / 2), avec_tube=False)

    ax2.set_xlim(x0c, x1c)
    ax2.set_ylim(y_bottom_stack - 9, zz(Z_MFC_TOP) + 4)
    ax2.set_xlabel("x (mm) — longueur (coupe au bord y = 0, ligne des TC)")
    ax2.set_ylabel("(coupe verticale, échelle z dilatée ×2,6)")
    ax2.set_title("Vue en coupe (plan x–z, y = 0)\nempilement, spot unique et 4 dwells",
                  fontsize=9.4)
    ax2.set_yticks([])
    for s in ("top", "right", "left"):
        ax2.spines[s].set_visible(False)
    ax2.tick_params(length=3)

    fig.legend(handles=LEGEND_HANDLES, loc="lower center", ncol=4, frameon=False,
               bbox_to_anchor=(0.5, 0.003), fontsize=8.0)
    fig.suptitle("Montage — exp9 : dissipation longitudinale",
                 fontsize=13, fontweight="bold", y=0.975)

    fig.savefig(OUT / "schema_montage_exp9.png")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    make_exp7()
    make_exp9()
    print("done")
