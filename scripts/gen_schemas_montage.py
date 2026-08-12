"""Schemas de montage exp7 / exp9 -- deux vues (plan x-y + coupe), format
article (style docs/modele/figures, cf. scripts/gen_figures_elsevier.py).

Les deux vues sont EMPILEES (vue de dessus au-dessus, vue en coupe en dessous) :
figure en portrait, chaque vue prend toute la largeur -> plus grande une fois
inseree pleine largeur de colonne dans le document.

Les vues en COUPE sont dessinees a l'ECHELLE 1:1 (aspect equal), avec un
ENCART ZOOM sur le spot (MFC + tubes carres 6 mm + empilement) pour la
lisibilite. Les tubes Cu TRAVERSENT le MFC (config/geometrie.yaml) : face
inferieure au ras du bas du MFC, reposant sur la ceramique.

Geometrie prise EXCLUSIVEMENT dans config/geometrie.yaml et
config/materiaux.yaml (valeurs recopiees en tete de script, avec la source).

N'ecrit QUE les deux PNG de sortie -- ne touche a aucun autre fichier du repo.
"""
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from pathlib import Path

OUT = Path("/Users/maxencedubois/PycharmProjects/Jumeau_Soudage_Induction/docs/modele/figures")

# ----------------------------------------------------------------------
# rcParams -- meme style que gen_figures_elsevier.py (police sans-serif,
# 600 dpi, fond blanc)
# ----------------------------------------------------------------------
from _style import apply_style, savefig  # noqa: E402  (style partagé, issue #17)
apply_style(**{
    "font.size": 10, "axes.labelsize": 10.5, "axes.titlesize": 11,
    "legend.fontsize": 8.5, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "axes.linewidth": 0.8, "lines.linewidth": 1.2,
    "savefig.pad_inches": 0.08, "figure.facecolor": "white", "savefig.facecolor": "white",
})
mpl.rcParams["hatch.linewidth"] = 0.4   # fines lignes de hachure (look composite)

# Okabe-Ito palette imposee
C_COIL = "#E69F00"     # cuivre / bobine
C_MFC = "#7F7F7F"      # gris / concentrateur (Magnetic Flux Concentrator)
C_COUPON = "#0072B2"   # bleu / coupon-twill
C_TC = "#C1272D"       # rouge / thermocouples
C_CERAM = "#4D4D4D"    # gris foncé / céramique entretoise MFC-coupon
C_CERAM_EDGE = "#262626"  # contour céramique (gris très foncé)
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

# Les tubes Cu TRAVERSENT le MFC le long de son grand cote (// y) et RESSORTENT
# de chaque cote. Longueur active = MFC (55 mm) ; on dessine un debord
# schematique de chaque cote pour montrer que le cuivre sort du concentrateur.
COIL_OVERHANG = 9.0
COIL_DRAW_LEN = LEG_LEN + 2 * COIL_OVERHANG   # 73 mm dessines (55 actifs + debords)

# ----------------------------------------------------------------------
# Hauteurs des vues en COUPE, dessinees a l'ECHELLE 1:1 (mm, positif VERS
# LE HAUT au-dessus de la surface du lamine). Les tubes Cu (carres 6 mm)
# TRAVERSENT le MFC (config/geometrie.yaml : "tubes carres 6 mm traversant
# le MFC") : leur face INFERIEURE est au ras de la face inferieure du MFC,
# et ils reposent sur la ceramique. Le MFC forme un canal autour d'eux.
# ----------------------------------------------------------------------
H_CERAM_TOP = GAP_CERAM               # +2  (sommet ceramique = appui des tubes)
H_TUBE_BOT = GAP_CERAM                # +2
H_TUBE_TOP = GAP_CERAM + TUBE         # +8
H_MFC_BOT = GAP_CERAM                 # +2  (bas du MFC au ras du bas des tubes)
H_MFC_TOP = H_MFC_BOT + MFC_H         # +14
# empilement du coupon (sous la surface, negatif)
H_INTERFACE = -E_SUP                  # -3.36  (pli twill + TC)
H_FILM_TOP = -E_SUP                   # -3.36
H_FILM_BOT = -(E_SUP + E_FILM)        # -3.46
H_COUPON_BOT = -L_INF                 # -6.82

# Empreintes (cahier / config)
CENTRES_DWELL = [15.875, 45.875, 75.875, 105.875]   # empreintes.centres_pas30 (mm)


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


def coupon_weave(ax, x0, y0, w, h, zorder=1):
    """Coupon CF/PEKK : remplissage translucide + tissage (hachure croisée)
    pour évoquer un composite tissé, avec un contour net."""
    rect(ax, x0, y0, w, h, facecolor=C_COUPON, alpha=0.16, edgecolor="none", zorder=zorder)
    rect(ax, x0, y0, w, h, facecolor="none", edgecolor=C_COUPON, alpha=0.55,
         linewidth=1.3, hatch="xxxx", zorder=zorder)


def coil_legs_patch(ax, xc, yc):
    """Les deux jambes de la bobine hairpin, centrees sur (xc, yc)."""
    for sgn in (-1, 1):
        x_leg = xc + sgn * ENTRAXE / 2 - TUBE / 2
        rect(ax, x_leg, yc - COIL_DRAW_LEN / 2, TUBE, COIL_DRAW_LEN,
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


def ceramique_patch(ax):
    """Entretoise ceramique (2 mm) vue de dessus : plaque translucide gris
    fonce sur toute l'emprise du coupon, sous le MFC (comme le patch MFC,
    avec effet de transparence)."""
    rect(ax, 0, 0, L, W, facecolor=C_CERAM, alpha=0.28, edgecolor=C_CERAM_EDGE,
         linewidth=0.6, zorder=2)


def tc_marker(ax, x, y, label, dxlab=0, dylab=2.6, fs=7.4, ha="center", va="bottom"):
    ax.scatter([x], [y], s=22, marker="o", color=C_TC, edgecolor="black",
               linewidth=0.4, zorder=10)
    ax.annotate(label, (x, y), xytext=(x + dxlab, y + dylab), fontsize=fs,
                color=C_TC, ha=ha, va=va, zorder=10, fontweight="bold")


LEGEND_HANDLES = [
    Rectangle((0, 0), 1, 1, facecolor=C_COIL, edgecolor="0.2", label="Bobine hairpin (Cu, tube 6 mm)"),
    Rectangle((0, 0), 1, 1, facecolor=C_MFC, edgecolor="0.2", alpha=0.35, label="Concentrateur MFC (Ferrotron 559H)"),
    Rectangle((0, 0), 1, 1, facecolor=C_CERAM, edgecolor=C_CERAM_EDGE, alpha=0.55, label="Céramique (entretoise MFC/coupon, 2 mm)"),
    Rectangle((0, 0), 1, 1, facecolor=C_COUPON, edgecolor=C_COUPON, alpha=0.55,
              hatch="xxxx", label="Coupon CF/PEKK (laminé)"),
    Line2D([0], [0], marker="o", color="none", markerfacecolor=C_TC, markeredgecolor="black",
           markersize=6, label="Thermocouple (à l'interface, z = 3,36 mm)"),
]


def epaisseurs_box(ax, x, y, avec_tube=True):
    lignes = [
        "Épaisseurs :",
        f"céramique {GAP_CERAM:.2f} mm",
        f"laminé sup. {E_SUP:.2f} mm",
        f"film PEKK {E_FILM:.2f} mm",
        f"laminé inf. {E_INF:.2f} mm",
    ]
    if avec_tube:
        lignes.append(f"tube Cu (brin) {TUBE:.0f}×{TUBE:.0f} mm")
        lignes.append(f"MFC {MFC_H:.0f} mm (haut.)")
    txt = "\n".join(lignes)
    ax.text(x, y, txt, fontsize=6.9, color="0.2", ha="left", va="center",
            bbox=dict(facecolor="white", edgecolor="0.6", linewidth=0.6, pad=4.0), zorder=20)


# ----------------------------------------------------------------------
# Empilement du coupon + ceramique, a l'echelle 1:1 (hauteur en mm, +haut).
# ----------------------------------------------------------------------
def draw_stack_1to1(ax, a, b, interface_label=True):
    """Coupon (lamine + film + interface) + ceramique sur l'intervalle [a, b]
    (x ou y selon la coupe), dessine a l'echelle reelle (mm, +haut)."""
    # laminate sup / film / laminate inf
    rect(ax, a, H_FILM_TOP, b - a, -H_FILM_TOP, facecolor=C_COUPON, alpha=0.22,
         edgecolor="none", zorder=2)                      # sup: -3.36 -> 0
    rect(ax, a, H_FILM_BOT, b - a, H_FILM_TOP - H_FILM_BOT, facecolor=C_FILM,
         edgecolor="none", zorder=2)                       # film 0.1 mm
    rect(ax, a, H_COUPON_BOT, b - a, H_FILM_BOT - H_COUPON_BOT, facecolor=C_COUPON,
         alpha=0.22, edgecolor="none", zorder=2)          # inf
    # plis du lamine (aspect composite) : fines lignes horizontales
    for k in range(1, 4):
        z_sup = H_FILM_TOP * k / 4.0                       # entre -3,36 et 0
        ax.plot([a, b], [z_sup, z_sup], color=C_COUPON, alpha=0.30, lw=0.4, zorder=3)
        z_inf = H_FILM_BOT + (H_COUPON_BOT - H_FILM_BOT) * k / 4.0
        ax.plot([a, b], [z_inf, z_inf], color=C_COUPON, alpha=0.30, lw=0.4, zorder=3)
    # ceramique 0 -> +2 (entretoise entre coupon et MFC/tubes, couleur distincte)
    rect(ax, a, 0.0, b - a, H_CERAM_TOP, facecolor=C_CERAM, alpha=0.55,
         edgecolor=C_CERAM_EDGE, linewidth=0.7, zorder=5)
    # contours
    rect(ax, a, H_COUPON_BOT, b - a, -H_COUPON_BOT, facecolor="none", edgecolor=C_COUPON,
         linewidth=1.0, zorder=4)
    # interface soudure (twill + TC)
    ax.plot([a, b], [H_INTERFACE, H_INTERFACE], color=C_COUPON, linewidth=2.0,
            zorder=6, solid_capstyle="butt")


def coupe_axis_cosmetics(ax):
    """Axe z visible (comm. directrice), spines propres."""
    ax.set_yticks([H_COUPON_BOT, H_INTERFACE, 0, H_TUBE_TOP, H_MFC_TOP])
    ax.set_yticklabels(["−6,8", "−3,4", "0", "+8", "+14"])
    ax.tick_params(length=3, labelsize=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


# ========================================================================
# FIGURE exp7 -- cartographie bord -> centre en LARGEUR
# ========================================================================
def make_exp7():
    fig = plt.figure(figsize=(8.4, 9.8))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.55, 1.0], hspace=0.30,
                          top=0.955, bottom=0.125, left=0.12, right=0.97)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])

    xc, yc = 60.0, 20.0

    # --- Panneau 1 : vue de dessus (x-y) ---------------------------------
    coupon_weave(ax1, 0, 0, L, W)
    ceramique_patch(ax1)                    # entretoise translucide sous le MFC
    mfc_patch(ax1, xc, yc, style="solid")
    coil_legs_patch(ax1, xc, yc)

    ys_tc = [0, 10, 20, 30, 40]
    for i, y in enumerate(ys_tc, start=1):
        tc_marker(ax1, xc, y, f"TC{i}", dxlab=14.0, dylab=0, fs=7.6,
                  ha="left", va="center")

    # cotes
    cote_h(ax1, 0, L, -18.8, "L = 120 mm", above=False)
    cote_v(ax1, 0, W, -9.0, "l = 40 mm", right=False)
    cote_h(ax1, xc - ENTRAXE / 2, xc + ENTRAXE / 2, W + 20.0, f"entraxe {ENTRAXE:.2f} mm", fs=7.0)
    cote_h(ax1, xc - MFC_X / 2, xc + MFC_X / 2, W + 25.0, f"MFC {MFC_X:.1f} mm (x)", fs=7.0)

    ax1.set_xlim(-16, L + 12)
    ax1.set_ylim(-22, W + 31)
    ax1.set_aspect("equal")
    ax1.set_xlabel("x (mm) — longueur du coupon")
    ax1.set_ylabel("y (mm) — largeur")
    ax1.set_title("Vue de dessus (plan x–y)", fontsize=10)
    ax1.tick_params(length=3)
    for s in ("top", "right"):
        ax1.spines[s].set_visible(False)

    # --- Panneau 2 : coupe y-z a x = 60 mm (1:1) --------------------------
    # Contenu centre sur le coupon (y 0..40) ; le MFC (55 mm) va de -7,5 a 47,5.
    y_lo, y_hi = yc - MFC_Y / 2, yc + MFC_Y / 2   # -7,5 .. 47,5
    draw_stack_1to1(ax2, 0, W)
    # MFC (deborde la largeur : 55 > 40) — canal a l'echelle reelle
    rect(ax2, y_lo, H_MFC_BOT, MFC_Y, MFC_H, facecolor=C_MFC, edgecolor="0.2",
         alpha=0.35, linewidth=0.9, zorder=3)
    ax2.text(yc, H_MFC_TOP - 2.4, "MFC", ha="center", va="center", fontsize=8,
             bbox=BOXPROPS, zorder=8)
    # brins vus A TRAVERS le MFC (coupe y-z a x=60, entre les 2 jambes qui
    # courent selon y) -> bande cuivre qui TRAVERSE le MFC et RESSORT de chaque
    # cote (longueur dessinee 73 mm > MFC 55 mm). Les segments hors du MFC sont
    # opaques (cuivre a l'air), la portion dans le MFC est semi-transparente.
    z_mid = H_TUBE_BOT
    rect(ax2, y_lo, z_mid, MFC_Y, TUBE, facecolor=C_COIL, edgecolor="none",
         alpha=0.45, zorder=5)                                   # portion dans le MFC (vue au travers)
    for sgn in (-1, 1):                                          # 2 bouts qui ressortent
        x0 = yc + sgn * MFC_Y / 2 if sgn > 0 else yc - COIL_DRAW_LEN / 2
        w = COIL_OVERHANG
        rect(ax2, x0, z_mid, w, TUBE, facecolor=C_COIL, edgecolor="0.2",
             linewidth=0.7, alpha=0.95, zorder=6)
    rect(ax2, yc - COIL_DRAW_LEN / 2, z_mid, COIL_DRAW_LEN, TUBE, facecolor="none",
         edgecolor="0.3", linewidth=0.8, linestyle="--", zorder=6)
    ax2.annotate("brins Cu",
                 xy=(yc - COIL_DRAW_LEN / 2 + COIL_OVERHANG / 2, z_mid + TUBE / 2),
                 xytext=(yc - COIL_DRAW_LEN / 2, z_mid + TUBE + 2.6), fontsize=7.0,
                 color="0.2", ha="left", va="bottom", zorder=8, bbox=BOXPROPS,
                 arrowprops=dict(arrowstyle="-", color="0.4", lw=0.6))

    # TC sur l'interface
    for i, y in enumerate(ys_tc, start=1):
        tc_marker(ax2, y, H_INTERFACE, f"TC{i}", dxlab=0, dylab=-2.4, fs=6.6,
                  ha="center", va="top")

    # bord du coupon marque
    for yb in (0, W):
        ax2.plot([yb, yb], [H_COUPON_BOT, 0], color=C_COUPON, lw=0.9, zorder=4)

    ax2.set_xlim(yc - COIL_DRAW_LEN / 2 - 3, y_hi + 6)
    ax2.set_ylim(H_COUPON_BOT - 3, H_MFC_TOP + 3)
    ax2.set_aspect("equal")
    ax2.set_xlabel("y (mm) — largeur (coupe à x = 60 mm)")
    ax2.set_ylabel("z (mm) — hauteur / profondeur\n(0 = surface, + vers le haut)")
    ax2.set_title("Vue en coupe (plan y–z, x = 60 mm) — échelle 1:1", fontsize=10)
    coupe_axis_cosmetics(ax2)

    fig.legend(handles=LEGEND_HANDLES, loc="lower center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, 0.005), fontsize=8.0)

    savefig(fig, OUT / "schema_montage_exp7.png")
    plt.close(fig)


# ========================================================================
# FIGURE exp9 -- dissipation LONGITUDINALE
# ========================================================================
def make_exp9():
    fig = plt.figure(figsize=(8.8, 9.4))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.5, 0.72], hspace=0.28,
                          top=0.955, bottom=0.16, left=0.11, right=0.98)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])

    yc = 20.0
    xc_spot = 60.0

    # --- Panneau 1 : vue de dessus (x-y) ----------------------------------
    coupon_weave(ax1, 0, 0, L, W)
    ceramique_patch(ax1)                    # entretoise translucide sous le MFC
    mfc_patch(ax1, xc_spot, yc, style="solid")
    coil_legs_patch(ax1, xc_spot, yc)

    xs_tc = [0, 30, 60, 90, 120]
    for i, x in enumerate(xs_tc, start=1):
        tc_marker(ax1, x, 0, f"TC{i}", dxlab=0, dylab=-10.0, fs=7.4, ha="center", va="top")

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
    ax1.set_title("Vue de dessus (plan x–y) — 5 TC au bord (y = 0)", fontsize=10)
    ax1.tick_params(length=3)
    for s in ("top", "right"):
        ax1.spines[s].set_visible(False)

    # --- Panneau 2 : coupe x-z a y = 0, ZOOM 1:1 sur le spot --------------
    # La vue de dessus porte deja le contexte pleine longueur (5 TC + 4 dwells).
    # La coupe se concentre sur le spot (x=60) pour montrer la geometrie reelle
    # (tubes carres, MFC) a l'echelle 1:1. Fenetre x=[28, 92] : TC2/TC3/TC4.
    x_lo, x_hi = 0.0, 120.0                 # pleine longueur : le coupon fait 120 mm
    draw_stack_1to1(ax2, x_lo, x_hi)        # coupon borne a 0..120 mm (respecte L)
    # MFC spot (plein) + 2 tubes carres traversant (coupe ⊥ aux tubes -> carres)
    rect(ax2, xc_spot - MFC_X / 2, H_MFC_BOT, MFC_X, MFC_H, facecolor=C_MFC,
         edgecolor="0.2", alpha=0.35, linewidth=0.9, zorder=4)
    for sgn in (-1, 1):
        xt = xc_spot + sgn * ENTRAXE / 2 - TUBE / 2
        rect(ax2, xt, H_TUBE_BOT, TUBE, TUBE, facecolor=C_COIL, edgecolor="0.15",
             linewidth=0.8, alpha=0.92, zorder=6)
    ax2.text(xc_spot, H_MFC_TOP - 2.4, "MFC", ha="center", va="center",
             fontsize=7.6, bbox=BOXPROPS, zorder=8)
    ax2.annotate("tubes Cu",
                 xy=(xc_spot + ENTRAXE / 2 + TUBE / 2, H_TUBE_BOT + TUBE / 2),
                 xytext=(xc_spot + 13, H_TUBE_TOP + 3.0), fontsize=7.0, color="0.2",
                 ha="left", va="center", zorder=8, bbox=BOXPROPS,
                 arrowprops=dict(arrowstyle="-", color="0.4", lw=0.6))

    # TC visibles dans la fenetre (30/60/90)
    for i, x in enumerate(xs_tc, start=1):
        if x_lo - 2 <= x <= x_hi + 2:
            tc_marker(ax2, x, H_INTERFACE, f"TC{i}", dxlab=0, dylab=-2.4, fs=6.8,
                      ha="center", va="top")

    ax2.set_xlim(x_lo - 6, x_hi + 6)
    ax2.set_ylim(H_COUPON_BOT - 3, H_MFC_TOP + 3)
    ax2.set_aspect("equal")
    ax2.set_xlabel("x (mm) — longueur (coupe au bord y = 0, ligne des TC)")
    ax2.set_ylabel("z (mm) — hauteur / profondeur\n(0 = surface, + vers le haut)")
    ax2.set_title("Vue en coupe (plan x–z, y = 0) — échelle 1:1", fontsize=10)
    coupe_axis_cosmetics(ax2)

    fig.legend(handles=LEGEND_HANDLES, loc="lower center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, 0.06), fontsize=8.0)

    savefig(fig, OUT / "schema_montage_exp9.png")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    make_exp7()
    make_exp9()
    print("done")
