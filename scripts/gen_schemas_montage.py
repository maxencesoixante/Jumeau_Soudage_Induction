"""Schemas de montage exp7 / exp9 -- deux vues (plan x-y + coupe), format
article (style docs/figures_elsevier, cf. scripts/gen_figures_elsevier.py).

Les deux vues sont disposees COTE A COTE (vue de dessus | vue en coupe).

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
    # ceramique 0 -> +2
    rect(ax, a, 0.0, b - a, H_CERAM_TOP, facecolor=C_CERAM, edgecolor="0.3",
         linewidth=0.6, zorder=2)
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


# ----------------------------------------------------------------------
# Encart zoom de l'INTERFACE (empilement fin : film 0,1 mm + pli twill + TC),
# echelle z dilatee pour la lisibilite des couches minces.
# ----------------------------------------------------------------------
def layup_inset(ax_parent, rect_frac, xc):
    """Encart compact (auto-contenu) : zoom z sur l'empilement fin autour de
    l'interface (lamine sup / film 0,1 mm / pli twill + TC / lamine inf)."""
    axi = ax_parent.inset_axes(rect_frac)
    a, b = xc - 6, xc + 6
    top, bot = -2.4, -4.5
    rect(axi, a, H_FILM_TOP, b - a, top - H_FILM_TOP, facecolor=C_COUPON, alpha=0.22, edgecolor="none")
    rect(axi, a, H_FILM_BOT, b - a, H_FILM_TOP - H_FILM_BOT, facecolor=C_FILM, edgecolor="0.55", linewidth=0.5)
    rect(axi, a, bot, b - a, H_FILM_BOT - bot, facecolor=C_COUPON, alpha=0.22, edgecolor="none")
    axi.plot([a, b], [H_INTERFACE, H_INTERFACE], color=C_COUPON, linewidth=2.6, solid_capstyle="butt", zorder=5)
    axi.scatter([xc], [H_INTERFACE], s=18, marker="o", color=C_TC, edgecolor="black", linewidth=0.4, zorder=6)
    axi.text(a + 0.4, (H_FILM_TOP + top) / 2, "laminé sup.", fontsize=5.6, color="0.35", va="center")
    axi.text(a + 0.4, bot + 0.5, "laminé inf.", fontsize=5.6, color="0.35", va="bottom")
    axi.annotate("film 0,10 mm", xy=(b - 0.5, (H_FILM_TOP + H_FILM_BOT) / 2),
                 xytext=(xc - 1.0, H_FILM_BOT - 0.55), fontsize=5.6, color="0.3", va="top", ha="left",
                 arrowprops=dict(arrowstyle="-", color="0.5", lw=0.5))
    axi.set_xlim(a, b)
    axi.set_ylim(bot, top)
    axi.set_xticks([])
    axi.set_yticks([])
    for s in axi.spines.values():
        s.set_edgecolor("0.5")
        s.set_linewidth(0.8)
    axi.set_title("détail interface\n(pli twill + TC, zoom z)", fontsize=6.0, pad=1.5)
    return axi


# ========================================================================
# FIGURE exp7 -- cartographie bord -> centre en LARGEUR
# ========================================================================
def make_exp7():
    fig = plt.figure(figsize=(15.0, 6.4))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.1], wspace=0.16,
                          top=0.84, bottom=0.18, left=0.055, right=0.985)
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

    ax1.set_xlim(-18, L + 20)
    ax1.set_ylim(-20, W + 24)
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
    # brins vus A TRAVERS le MFC (la coupe y-z a x=60 passe ENTRE les 2 jambes,
    # qui courent selon y) -> bande cuivre transparente sur toute la longueur
    # des jambes (55 mm = largeur du MFC ; deborde le coupon de +/-7,5 mm).
    rect(ax2, yc - LEG_LEN / 2, H_TUBE_BOT, LEG_LEN, TUBE, facecolor=C_COIL,
         edgecolor="0.3", linewidth=0.9, alpha=0.42, zorder=5, linestyle="--")
    ax2.annotate("brins ⊥ à la coupe (vus à travers\nle MFC, débordent le coupon)",
                 xy=(y_hi - 4, H_TUBE_BOT + TUBE / 2),
                 xytext=(y_hi + 1.5, H_TUBE_TOP + 2.5), fontsize=6.6,
                 color="0.25", ha="left", va="center", zorder=8, bbox=BOXPROPS,
                 arrowprops=dict(arrowstyle="-", color="0.4", lw=0.6))

    # TC sur l'interface
    for i, y in enumerate(ys_tc, start=1):
        tc_marker(ax2, y, H_INTERFACE, f"TC{i}", dxlab=0, dylab=-2.4, fs=6.6,
                  ha="center", va="top")

    # bord du coupon marque
    for yb in (0, W):
        ax2.plot([yb, yb], [H_COUPON_BOT, 0], color=C_COUPON, lw=0.9, zorder=4)

    layup_inset(ax2, [0.72, 0.03, 0.25, 0.40], yc)

    ax2.set_xlim(y_lo - 4, y_hi + 22)
    ax2.set_ylim(H_COUPON_BOT - 3, H_MFC_TOP + 3)
    ax2.set_aspect("equal")
    ax2.set_xlabel("y (mm) — largeur (coupe à x = 60 mm)")
    ax2.set_ylabel("z (mm) — hauteur / profondeur\n(0 = surface, + vers le haut)")
    ax2.set_title("Vue en coupe (plan y–z, x = 60 mm) — échelle 1:1", fontsize=10)
    coupe_axis_cosmetics(ax2)

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
    fig = plt.figure(figsize=(15.6, 6.4))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.32], wspace=0.14,
                          top=0.84, bottom=0.17, left=0.045, right=0.99)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])

    yc = 20.0
    xc_spot = 60.0

    # --- Panneau 1 : vue de dessus (x-y) ----------------------------------
    rect(ax1, 0, 0, L, W, facecolor=C_COUPON, edgecolor=C_COUPON, alpha=0.20,
         linewidth=1.4, zorder=1)
    mfc_patch(ax1, xc_spot, yc, style="solid")
    coil_legs_patch(ax1, xc_spot, yc)
    for j, xd in enumerate(CENTRES_DWELL, start=1):
        mfc_patch(ax1, xd, yc, style="dotted")
        ax1.text(xd, yc - MFC_Y / 2 - 2.0, f"d{j}", ha="center", va="top",
                 fontsize=6.6, color="0.30", fontweight="bold")

    xs_tc = [0, 30, 60, 90, 120]
    for i, x in enumerate(xs_tc, start=1):
        tc_marker(ax1, x, 0, f"TC{i}\n({x}, 0)", dxlab=0, dylab=-11.0, fs=7.0, ha="center", va="top")

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
    x_lo, x_hi = 28.0, 92.0
    draw_stack_1to1(ax2, -8, L + 8)         # empilement dessine large, clipe par xlim
    # MFC spot (plein) + 2 tubes carres traversant (coupe ⊥ aux tubes -> carres)
    rect(ax2, xc_spot - MFC_X / 2, H_MFC_BOT, MFC_X, MFC_H, facecolor=C_MFC,
         edgecolor="0.2", alpha=0.35, linewidth=0.9, zorder=4)
    for sgn in (-1, 1):
        xt = xc_spot + sgn * ENTRAXE / 2 - TUBE / 2
        rect(ax2, xt, H_TUBE_BOT, TUBE, TUBE, facecolor=C_COIL, edgecolor="0.15",
             linewidth=0.8, alpha=0.92, zorder=6)
    ax2.text(xc_spot, H_MFC_TOP - 2.4, "MFC (spot)", ha="center", va="center",
             fontsize=7.6, bbox=BOXPROPS, zorder=8)
    ax2.annotate("2 tubes Cu 6×6 mm traversant le MFC\n(face basse au ras du bas du MFC)",
                 xy=(xc_spot + ENTRAXE / 2 + TUBE / 2, H_TUBE_BOT + TUBE / 2),
                 xytext=(xc_spot + 12, H_TUBE_TOP + 3.5), fontsize=6.6, color="0.2",
                 ha="left", va="center", zorder=8, bbox=BOXPROPS,
                 arrowprops=dict(arrowstyle="-", color="0.4", lw=0.6))

    # TC visibles dans la fenetre (30/60/90)
    for i, x in enumerate(xs_tc, start=1):
        if x_lo - 2 <= x <= x_hi + 2:
            tc_marker(ax2, x, H_INTERFACE, f"TC{i}", dxlab=0, dylab=-2.4, fs=6.8,
                      ha="center", va="top")
    ax2.text(x_hi - 1, H_INTERFACE - 5.6, "TC espacés de 30 mm (cf. vue de dessus)",
             ha="right", va="top", fontsize=6.4, color="0.4", style="italic")

    layup_inset(ax2, [0.015, 0.55, 0.22, 0.40], xc_spot)

    ax2.set_xlim(x_lo, x_hi + 6)
    ax2.set_ylim(H_COUPON_BOT - 6, H_MFC_TOP + 3)
    ax2.set_aspect("equal")
    ax2.set_xlabel("x (mm) — longueur (coupe au bord y = 0, ligne des TC)")
    ax2.set_ylabel("z (mm) — hauteur / profondeur\n(0 = surface, + vers le haut)")
    ax2.set_title("Vue en coupe (plan x–z, y = 0) — zoom spot, échelle 1:1", fontsize=10)
    coupe_axis_cosmetics(ax2)

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
