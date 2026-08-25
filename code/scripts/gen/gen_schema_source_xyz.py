"""Schema pedagogique de la chaine EM -> Joule -> thermique, en suivant les
axes x (longueur), y (largeur), z (epaisseur).

Illustre, dans l'ordre, les etapes reelles du code (cf.
biblio/labo/explication_source_xyz.md pour le detail sourcé) :

  1. Bobine hairpin + concentrateur MFC (image de courant) -> champ Bz,
     coupe (y, z) au spot -- em/champ_coil.py (Biot-Savart, bz_plan).
  2. Courants de Foucault PLANS (x, y) : fonction de courant psi, psi=0 au
     bord -> profil de chauffe en « M » -- em/foucault.py (resoudre_psi).
  3. Repartition dans l'epaisseur z : regime plaque mince (delta >> epaisseur
     de couche), Bz echantillonne noeud par noeud + ecran e^(-2t/delta)
     entre couches -- em/source_joule.py (attenuation_blindage).
  4. q(x,y,z) = rho_xx.Jx^2 + rho_yy.Jy^2 depose sur la grille -> terme
     source de l'equation de la chaleur -- thermique/solveur3d.py.

Schema (diagramme + coupes annotees), PAS un graphe de donnees. PNG only,
palette Okabe-Ito, texte en francais, terminologie "MFC".

Sortie : biblio/presentations/figures_schemas/fig_schema_source_xyz.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch, FancyBboxPatch

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts"))
from _style import apply_style, savefig, OKABE_ITO  # noqa: E402

apply_style(**{
    "font.size": 9.3, "axes.labelsize": 8.8, "axes.titlesize": 9.6,
    "legend.fontsize": 8.0, "xtick.labelsize": 7.4, "ytick.labelsize": 7.4,
    "axes.linewidth": 0.8, "lines.linewidth": 1.3,
    "savefig.pad_inches": 0.12, "figure.facecolor": "white", "savefig.facecolor": "white",
})

OUT = R / "biblio" / "presentations" / "figures_schemas" / "fig_schema_source_xyz.png"

# --------------------------------------------------------------------- #
# Palette (Okabe-Ito, cf. _style.py)
# --------------------------------------------------------------------- #
C_COIL = OKABE_ITO["orange"]      # cuivre / bobine
C_MFC = "#7F7F7F"                 # gris / concentrateur MFC
C_PLATE = OKABE_ITO["bleu"]       # coupon CF/PEKK
C_TWILL = OKABE_ITO["vermillon"]  # pli twill suscepteur (siege de la chauffe)
C_FIELD = OKABE_ITO["vert"]       # lignes de champ Bz / flux
C_HEAT = OKABE_ITO["vermillon"]   # courbe / carte de puissance Joule
C_ARROW = "#222222"               # grandes fleches de flux du schema
C_TXT = "#1a1a1a"

BOXPROPS = dict(facecolor="white", alpha=0.92, edgecolor="0.65", linewidth=0.5, pad=2.0)


def down_arrow(fig, x, y_from, y_to, label=""):
    arr = FancyArrowPatch((x, y_from), (x, y_to), transform=fig.transFigure,
                           arrowstyle="-|>", mutation_scale=20, color=C_ARROW,
                           linewidth=2.0, zorder=30, shrinkA=1, shrinkB=1)
    fig.add_artist(arr)
    if label:
        fig.text(x + 0.010, (y_from + y_to) / 2, label, transform=fig.transFigure,
                  ha="left", va="center", fontsize=7.6, color=C_ARROW, fontweight="bold", zorder=31)


def side_arrow(fig, x_from, x_to, y, label=""):
    arr = FancyArrowPatch((x_from, y), (x_to, y), transform=fig.transFigure,
                           arrowstyle="-|>", mutation_scale=20, color=C_ARROW,
                           linewidth=2.0, zorder=30, shrinkA=1, shrinkB=1)
    fig.add_artist(arr)
    if label:
        fig.text((x_from + x_to) / 2, y + 0.014, label, transform=fig.transFigure,
                  ha="center", va="bottom", fontsize=7.6, color=C_ARROW, fontweight="bold", zorder=31)


# ======================================================================= #
# Figure : rangee haute = 3 panneaux (etapes 1-2-3, chacun avec son propre
# repere x/y/z) ; rangee basse = 1 bandeau pleine largeur (etape 4).
# Beaucoup de marge (top/bottom/hspace) pour eviter tout chevauchement.
# ======================================================================= #
fig = plt.figure(figsize=(15.4, 10.6))
gs = fig.add_gridspec(2, 3, height_ratios=[1.0, 0.40], width_ratios=[1.0, 1.05, 0.95],
                      hspace=0.55, wspace=0.38,
                      top=0.80, bottom=0.075, left=0.055, right=0.985)

ax1 = fig.add_subplot(gs[0, 0])   # coupe (y,z) : bobine + MFC + Bz

# panneau 2 = sous-grille verticale (courbe M en haut, vue de dessus en bas)
gs2 = gs[0, 1].subgridspec(2, 1, height_ratios=[0.40, 1.0], hspace=0.55)
ax2m = fig.add_subplot(gs2[0])    # courbe q(y) en "M"
ax2 = fig.add_subplot(gs2[1])     # vue de dessus (x,y)

ax3 = fig.add_subplot(gs[0, 2])   # coupe z : peau / couches / attenuation
ax4 = fig.add_subplot(gs[1, :])   # bandeau : Q(x,y,z) -> solveur thermique

fig.suptitle("De la bobine au chauffage volumique : la chaîne EM → Joule → thermique",
             fontsize=15.5, fontweight="bold", y=0.965, color=C_TXT)
fig.text(0.5, 0.925,
         "Repère commun : x = longueur du coupon, y = largeur, z = épaisseur (z croît vers le bas)",
         ha="center", va="top", fontsize=9.3, color="0.25", style="italic")

# ----------------------------------------------------------------------- #
# Panneau 1 -- coupe (y, z) : bobine hairpin + MFC (image de courant) -> Bz
# ----------------------------------------------------------------------- #
ax1.set_title("① Champ B — Biot-Savart + image MFC", pad=8, fontsize=10.2, fontweight="bold")

# Convention verticale : positif = au-dessus de la surface (bobine/MFC),
# negatif = dans l'epaisseur de la plaque (memes valeurs mm que
# gen_schemas_montage.py, source unique config/geometrie.yaml).
H_CERAM_TOP = 2.0            # sommet ceramique (2 mm)
H_TUBE_BOT, TUBE = 2.0, 6.0  # tubes Cu carres 6 mm, poses sur la ceramique
H_MFC_BOT, MFC_H = 2.0, 12.0
H_MFC_TOP = H_MFC_BOT + MFC_H
ENTRAXE = 12.35
E_SUP, T_TWILL = 3.36, 0.20
H_INTERFACE = -(E_SUP - T_TWILL)      # -3.16 (debut du pli twill)
H_STACK_BOT = -6.82

Y0, Y1 = -3.0, 43.0
yc_coil = 20.0

# plaque (coupon)
ax1.add_patch(Rectangle((0, H_STACK_BOT), 40, -H_STACK_BOT, facecolor=C_PLATE, alpha=0.16,
                        edgecolor=C_PLATE, linewidth=1.1, zorder=2))
ax1.add_patch(Rectangle((0, H_INTERFACE - T_TWILL), 40, T_TWILL * 3.0, facecolor=C_TWILL,
                        alpha=0.9, edgecolor="none", zorder=3))  # twill exagere x3 (visibilite)
ax1.text(20, H_INTERFACE - T_TWILL * 1.5, "twill suscepteur (interface, 0,20 mm)",
         ha="center", va="center", fontsize=6.6, color="white", fontweight="bold", zorder=4)
ax1.plot([0, 40], [0, 0], color=C_PLATE, lw=1.3, zorder=4)

# ceramique
ax1.add_patch(Rectangle((0, 0), 40, H_CERAM_TOP, facecolor="#4D4D4D", alpha=0.5,
                        edgecolor="#262626", linewidth=0.6, zorder=3))

# MFC (bloc gris)
ax1.add_patch(Rectangle((-3, H_MFC_BOT), 46, MFC_H, facecolor=C_MFC, alpha=0.30,
                        edgecolor="0.2", linewidth=1.0, zorder=1))
ax1.text(38.5, H_MFC_TOP - 0.9, "MFC (µᵣ≈16)", ha="right", va="top", fontsize=7.2,
         color="0.15", zorder=6)

# brins de la bobine (coupe, 2 carres) + image-miroir (courant eta.I)
# plan-image du MFC = sommet des brins (geometrie.plan_miroir_cfc = hauteur +
# rayon_tube = 5+3 = 8 mm), PAS le sommet du bloc MFC -- le reflet tombe donc
# dans la moitie haute du bloc (entre 8 et 14 mm), a l'interieur du MFC.
for yb in (yc_coil - ENTRAXE / 2, yc_coil + ENTRAXE / 2):
    ax1.add_patch(Rectangle((yb - TUBE / 2, H_TUBE_BOT), TUBE, TUBE, facecolor=C_COIL,
                            edgecolor="0.15", linewidth=0.9, zorder=8))
z_miroir = H_TUBE_BOT + TUBE   # 8 mm = coil.hauteur + rayon_tube
for yb in (yc_coil - ENTRAXE / 2, yc_coil + ENTRAXE / 2):
    ax1.add_patch(Rectangle((yb - TUBE / 2, z_miroir), TUBE, TUBE,
                            facecolor="none", edgecolor=C_COIL, linewidth=1.0, linestyle=":",
                            alpha=0.85, zorder=7))
ax1.plot([Y0, Y1], [z_miroir, z_miroir], color="0.45", lw=0.7, linestyle="--", zorder=5)
ax1.annotate("brins Cu (hairpin)", xy=(yc_coil - ENTRAXE / 2, H_TUBE_BOT + TUBE / 2),
             xytext=(2.0, H_TUBE_BOT + TUBE + 1.3), fontsize=6.9, color="0.15", ha="left",
             va="bottom", zorder=9, bbox=BOXPROPS,
             arrowprops=dict(arrowstyle="-", color="0.35", lw=0.6))
ax1.annotate("image η·I ≈ 0,88·I\n(reflet dans le MFC)",
             xy=(yc_coil + ENTRAXE / 2, z_miroir + TUBE / 2),
             xytext=(38.5, H_TUBE_BOT + TUBE + 1.3), fontsize=6.3, color="0.30",
             ha="right", va="bottom", zorder=9, bbox=BOXPROPS,
             arrowprops=dict(arrowstyle="-", color="0.4", lw=0.5))

# lignes de champ Bz (fleches vers le bas, a travers la plaque) -- une seule
# etiquette compacte, decalee au-dessus des fleches (pas de texte QUI les
# recouvre).
for yb in np.linspace(6, 34, 5):
    ax1.annotate("", xy=(yb, -0.3), xytext=(yb, H_TUBE_BOT - 0.55),
                 arrowprops=dict(arrowstyle="-|>", color=C_FIELD, lw=1.4, alpha=0.85), zorder=10)
ax1.text(37.0, H_TUBE_BOT - 0.55, "B_z", color=C_FIELD, fontsize=8.4, fontweight="bold",
         ha="right", va="center", zorder=11,
         bbox=dict(facecolor="white", alpha=0.85, edgecolor="none", pad=1.0))

ax1.set_xlim(Y0, Y1)
ax1.set_ylim(H_STACK_BOT - 1.0, H_MFC_TOP + 1.5)
ax1.set_xlabel("y — largeur (mm)")
ax1.set_ylabel("z — profondeur (mm)\n(0 = surface ; coupe à x = x_spot)")
ax1.set_yticks([0, H_INTERFACE - T_TWILL, H_STACK_BOT])
ax1.set_yticklabels(["0", "3,16\n(interface)", "6,82\n(face opp.)"])
for s in ("top", "right"):
    ax1.spines[s].set_visible(False)
# ----------------------------------------------------------------------- #
# Panneau 2a -- courbe q(y) en "M" (schematique), au-dessus de la vue du haut
# ----------------------------------------------------------------------- #
y_m = np.linspace(0, 40, 200)
q_m = 1.0 - 0.62 * np.exp(-((y_m - 20.0) / 9.0) ** 2)
ax2m.plot(y_m, q_m, color=C_HEAT, lw=1.8)
ax2m.fill_between(y_m, 0, q_m, color=C_HEAT, alpha=0.12)
ax2m.set_xlim(0, 40)
ax2m.set_ylim(0, 1.15)
ax2m.set_xticks([0, 20, 40])
ax2m.set_xticklabels(["chant y=0", "centre y=20", "chant y=40"], fontsize=6.8)
ax2m.set_yticks([])
ax2m.set_title("profil q(y) schématique — contraste bord/centre mesuré ≈ 2,4×",
               fontsize=7.6, color="0.2", pad=4)
for s in ("top", "right", "left"):
    ax2m.spines[s].set_visible(False)

# ----------------------------------------------------------------------- #
# Panneau 2b -- vue de dessus (x, y) : courants de Foucault plans, psi=0 au bord
# ----------------------------------------------------------------------- #
ax2.set_title("② Courants de Foucault plans ψ(x,y) — profil « M »", pad=8,
              fontsize=10.2, fontweight="bold")

L, W = 120.0, 40.0
ax2.add_patch(Rectangle((0, 0), L, W, facecolor=C_PLATE, alpha=0.14, edgecolor=C_PLATE,
                        linewidth=1.1, zorder=1))
ax2.add_patch(Rectangle((0, 0), L, W, facecolor="none", edgecolor=C_PLATE, alpha=0.5,
                        linewidth=1.0, hatch="....", zorder=1))

xc, yc = 60.0, 20.0
mfc_x, mfc_y = 31.5, 55.0
ax2.add_patch(Rectangle((xc - mfc_x / 2, max(0, yc - mfc_y / 2)), mfc_x, min(mfc_y, W),
                        facecolor=C_MFC, alpha=0.25, edgecolor="0.2", linewidth=0.9, zorder=2))
for sgn in (-1, 1):
    ax2.add_patch(Rectangle((xc + sgn * ENTRAXE / 2 - 1.5, 0), 3.0, W, facecolor=C_COIL,
                            edgecolor="0.2", linewidth=0.6, alpha=0.55, zorder=3))
ax2.text(xc, W + 2.0, "empreinte MFC + brins", ha="center", va="bottom", fontsize=7.0,
         color="0.2", zorder=4)

# boucles de courant de Foucault (schematique, sens opposes de part et d'autre du zero)
for lx, sense in ((xc - 16, -1), (xc + 16, 1)):
    th = np.linspace(0, 2 * np.pi, 100)
    ex, ey = lx + 13 * np.cos(th), yc + 15 * np.sin(th)
    ax2.plot(ex, ey, color=C_FIELD, lw=1.1, alpha=0.8, zorder=5)
    k = 25 if sense > 0 else 75
    ax2.annotate("", xy=(ex[k + 1], ey[k + 1]), xytext=(ex[k], ey[k]),
                 arrowprops=dict(arrowstyle="-|>", color=C_FIELD, lw=1.1), zorder=6)
ax2.text(xc, yc, "J = ∇×(ψ ẑ)\nJx=∂ψ/∂y, Jy=−∂ψ/∂x", ha="center", va="center", fontsize=7.4,
         color=C_TXT, bbox=BOXPROPS, zorder=7)

# BC psi=0 au bord (chants y=0 et y=40) -- annotations courtes, DANS le cadre
for yb, dy, va in ((0, -3.2, "top"), (W, 3.2, "bottom")):
    ax2.plot([0, L], [yb, yb], color=C_HEAT, lw=2.2, zorder=6)
    ax2.text(6, yb + dy, "ψ = 0 (chant)", fontsize=7.2, color=C_HEAT, ha="left", va=va, zorder=8)

ax2.set_xlim(-4, L + 4)
ax2.set_ylim(-7, W + 7)
ax2.set_xlabel("x — longueur (mm)")
ax2.set_ylabel("y — largeur (mm)")
for s in ("top", "right"):
    ax2.spines[s].set_visible(False)

# ----------------------------------------------------------------------- #
# Panneau 3 -- coupe z : regime plaque mince, peau, couches conductrices
# ----------------------------------------------------------------------- #
ax3.set_title("③ Épaisseur z — peau & couches conductrices", pad=8,
              fontsize=10.2, fontweight="bold")

z_layers = [
    ("laminé sup.\n3,16 mm", 0.0, 3.16, C_PLATE, 0.20, 0.60),
    ("twill 0,20 mm", 3.16, 3.36, C_TWILL, 0.95, 1.00),
    ("film PEKK 0,10 mm", 3.36, 3.46, "#D9D9D9", 0.9, 0.0),
    ("laminé inf.\n3,36 mm", 3.46, 6.82, C_PLATE, 0.20, 0.28),
]
X_STACK, W_STACK = 0.0, 1.0
X_BARS = 1.55
for name, z0, z1, col, alpha, qrel in z_layers:
    ax3.add_patch(Rectangle((X_STACK, -z1), W_STACK, z1 - z0, facecolor=col, alpha=alpha,
                            edgecolor="0.35", linewidth=0.8, zorder=2))
    if qrel > 0:
        bh = (z1 - z0) * 0.72
        ax3.add_patch(Rectangle((X_BARS, -(z0 + z1) / 2 - bh / 2), qrel * 0.62, bh,
                                facecolor=C_HEAT, alpha=0.85, edgecolor="none", zorder=3))
ax3.text(X_BARS, 0.35, "q déposé\n(relatif)", ha="left", va="bottom", fontsize=6.6, color=C_HEAT)

# Labels des 2 couches epaisses : centres, pleine place disponible.
ax3.text(X_STACK - 0.10, -1.58, "laminé sup.\n3,16 mm", ha="right", va="center",
         fontsize=6.8, color="0.15", zorder=3)
ax3.text(X_STACK - 0.10, -5.14, "laminé inf.\n3,36 mm", ha="right", va="center",
         fontsize=6.8, color="0.15", zorder=3)
# Labels des 2 couches FINES (twill 0,20 mm, film 0,10 mm) : trop minces pour
# un texte centre (elles se chevaucheraient) -> etiquettes decalees avec
# ligne de rappel, comme "brins Cu" au panneau 1.
ax3.annotate("twill 0,20 mm\n(siège chauffe)", xy=(X_STACK, -3.26),
             xytext=(-0.32, -2.30), fontsize=6.5, color="0.15", ha="right", va="center",
             zorder=5, bbox=BOXPROPS, arrowprops=dict(arrowstyle="-", color=C_TWILL, lw=0.8))
ax3.annotate("film 0,10 mm", xy=(X_STACK, -3.41),
             xytext=(-0.32, -4.55), fontsize=6.4, color="0.35", ha="right", va="center",
             zorder=5, bbox=BOXPROPS, arrowprops=dict(arrowstyle="-", color="0.5", lw=0.7))

# fleches Bz decroissantes (attenuation qualitative entre couches ecrans)
for i, z0 in enumerate([0.4, 1.6, 2.8]):
    ln = 1.0 - 0.28 * i
    ax3.annotate("", xy=(0.5, -z0 - ln), xytext=(0.5, -z0),
                 arrowprops=dict(arrowstyle="-|>", color=C_FIELD, lw=1.3, alpha=0.8), zorder=4)
ax3.text(0.5, 0.35, "Bz", color=C_FIELD, fontsize=8.0, fontweight="bold", ha="center", va="bottom")

ax3.set_xlim(-1.55, 2.35)
ax3.set_ylim(-7.6, 0.85)
ax3.set_xticks([])
ax3.set_ylabel("z — profondeur (mm)", labelpad=10)
for s in ("top", "right", "bottom"):
    ax3.spines[s].set_visible(False)

fig.text(0.985, 0.435,
         "δ_twill ≈ 7,7 mm, δ_réf ≈ 5,4–6 mm (388 kHz) ≫ épaisseur de couche (0,2–3,4 mm)\n"
         "→ régime « plaque mince » valide ; Bz échantillonné nœud z par nœud z,\n"
         "atténuation e⁻²ᵗ/ᵟ appliquée par couche-écran traversée",
         ha="right", va="top", fontsize=7.6, color="0.15",
         bbox=dict(facecolor="#F2F2F2", edgecolor="0.6", linewidth=0.6, pad=5.0))

# ----------------------------------------------------------------------- #
# Grandes fleches de flux : 1 -> 2 -> 3 (rangee haute), puis rangee haute
# -> bandeau (etape 4), toutes horizontales/verticales, sans diagonale.
# ----------------------------------------------------------------------- #
fig.canvas.draw()  # nécessaire pour que les positions d'axes (get_position) soient à jour
p1, p2, p3 = ax1.get_position(), ax2.get_position(), ax3.get_position()
y_mid_top = p1.y0 + 0.30 * p1.height
side_arrow(fig, p1.x1 + 0.006, p2.x0 - 0.006, y_mid_top, "Bz(x,y,z)")
side_arrow(fig, p2.x1 + 0.006, p3.x0 - 0.006, y_mid_top, "ψ(x,y) par couche")

x_mid = 0.5
down_arrow(fig, x_mid, p1.y0 - 0.020, gs.top - 0.335, "")
fig.text(x_mid + 0.012, p1.y0 - 0.075, "q(x,y,z) — une valeur par couche & par nœud z",
         ha="left", va="center", fontsize=7.8, color=C_ARROW, fontweight="bold")

# ----------------------------------------------------------------------- #
# Panneau 4 -- bandeau : depot Q(x,y,z) -> terme source du solveur thermique
# ----------------------------------------------------------------------- #
ax4.set_title("④ Dépôt de puissance & terme source du solveur thermique 3D", pad=6,
              fontsize=10.4, fontweight="bold")
ax4.axis("off")
ax4.set_xlim(0, 1)
ax4.set_ylim(0, 1)

boxes = [
    (0.010, 0.245, "#FFF3E9", C_HEAT, "Joule anisotrope",
     r"$q = \rho_{xx}J_x^2 + \rho_{yy}J_y^2$" + "\n[W/m³], par couche & nœud z"),
    (0.290, 0.245, "#EAF3FB", C_PLATE, "Dépôt sur la grille",
     "Q(nx,ny,nz), poids t/dz,\nconserve q·t par couche ;\n× facteur_couplage (calibré ≈ 6,0)"),
    (0.570, 0.42, "#EEF7F1", C_FIELD, "Équation de la chaleur 3D (solveur3d.py)",
     r"$\rho\,c_p^{app}(T)\,\dfrac{\partial T}{\partial t} = \nabla\!\cdot\!(k\nabla T) + Q(x,y,z,t)$"
     "\nconvection + rayonnement + contact céramique/MFC"),
]
for x0, w, fc, ec, title, body in boxes:
    ax4.add_patch(FancyBboxPatch((x0, 0.08), w, 0.72, boxstyle="round,pad=0.02",
                                 transform=ax4.transAxes, facecolor=fc, edgecolor=ec,
                                 linewidth=1.2, zorder=2))
    ax4.text(x0 + w / 2, 0.63, title, transform=ax4.transAxes, ha="center", va="center",
             fontsize=8.6, fontweight="bold", color=C_TXT, zorder=3)
    ax4.text(x0 + w / 2, 0.33, body, transform=ax4.transAxes, ha="center", va="center",
             fontsize=8.2, color=C_TXT, zorder=3)

ax4.annotate("", xy=(0.285, 0.44), xytext=(0.250, 0.44), xycoords="axes fraction",
             arrowprops=dict(arrowstyle="-|>", color=C_ARROW, lw=2.0), zorder=4)
ax4.annotate("", xy=(0.565, 0.44), xytext=(0.530, 0.44), xycoords="axes fraction",
             arrowprops=dict(arrowstyle="-|>", color=C_ARROW, lw=2.0), zorder=4)

fig.text(0.985, 0.012,
         "Sources : code/src/jumeau/em/{champ_coil,foucault,source_joule}.py, "
         "thermique/solveur3d.py, config/{geometrie,materiaux}.yaml",
         ha="right", va="bottom", fontsize=6.6, color="0.45", style="italic")

OUT.parent.mkdir(parents=True, exist_ok=True)
savefig(fig, OUT.with_suffix(""))
plt.close(fig)
print(f"figure -> {OUT.relative_to(R)}")
