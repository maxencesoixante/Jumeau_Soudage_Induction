"""Carte du champ EM du couple bobine + MFC -- notre montage actuel.

Dans l'esprit des vignettes de la slide 10 du deck NIAR (Thermoplastic
Joining, Wichita State) : coupe verticale, lignes de champ autour de la
bobine, et la piece figuree par une barre coloree par la chauffe induite.

Ici la carte n'est PAS un dessin : tout est calcule par la chaine EM du
jumeau -- Biot-Savart sur la polyligne hairpin reelle (`champ_coil`), MFC
traite par courants images, courants de Foucault en plaque mince
(`foucault`), densite Joule integree dans l'epaisseur (`source_joule`).

Deux colonnes, strictement comparables (meme chemin de calcul, seul mu_r
change) : bobine SEULE (mu_r = 1 -> image nulle) et bobine + MFC (mu_r = 16,
notre montage). La comparaison montre ce que le concentrateur apporte.

Coupe : plan x-z a mi-largeur de plaque. Les deux brins de la hairpin y
apparaissent en bout, parcourus par des courants OPPOSES.

N'ecrit QUE le PNG de sortie.
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from matplotlib.colors import Normalize

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jumeau.materiaux import Config                      # noqa: E402
from jumeau.geometrie import (sommets_bobine, plan_miroir_cfc,
                              construire_grille)         # noqa: E402
from jumeau.em.champ_coil import champ_segments          # noqa: E402
from jumeau.em.source_joule import source_spot           # noqa: E402
from jumeau.procede import Essai                         # noqa: E402
from _style import apply_style                           # noqa: E402

apply_style(**{
    "font.size": 10.5, "axes.labelsize": 11, "axes.titlesize": 12,
    "xtick.labelsize": 9.5, "ytick.labelsize": 9.5, "axes.linewidth": 0.9,
    "savefig.pad_inches": 0.06, "figure.facecolor": "white",
    "savefig.facecolor": "white",
})

COURANT = 250.0
CENTRE_X = 0.060

cfg = Config.charger(R / "code" / "config")
essai = Essai(cfg, R / "code" / "config/essais/exp9_200A_monospot.yaml",
              nx=121, ny=41, nz=15, facteur_couplage=1.0, racine=R)
grille, couches = essai.grille, essai.couches

geo = cfg.geometrie
centre_y = geo["laminate"]["largeur"] / 2.0
sommets = sommets_bobine(cfg, CENTRE_X, centre_y=centre_y)
z_miroir = plan_miroir_cfc(cfg)
entraxe = geo["coil"]["entraxe_jambes"]
tube = 2.0 * geo["coil"]["rayon_tube"]
h_coil = geo["coil"]["hauteur"]
mfc_x, mfc_h = geo["cfc"]["largeur"], geo["cfc"]["hauteur"]
ep_plaque = grille.z[-1]

# --- coupe x-z a mi-largeur ------------------------------------------------- #
xs = np.linspace(0.030, 0.090, 260)
zs = np.linspace(-0.014, 0.026, 200)
XG, ZG = np.meshgrid(xs, zs, indexing="ij")
pts = np.column_stack([XG.ravel(), np.full(XG.size, centre_y), ZG.ravel()])


def champ_coupe(avec_mfc: bool):
    B = champ_segments(pts, sommets, COURANT)
    if avec_mfc:
        mu_r = float(geo["cfc"]["mu_r"])
        eta = (mu_r - 1.0) / (mu_r + 1.0)
        image = sommets.copy()
        image[:, 2] = 2.0 * z_miroir - image[:, 2]
        B += champ_segments(pts, image, eta * COURANT)
    Bx = B[:, 0].reshape(XG.shape)
    Bz = B[:, 2].reshape(XG.shape)
    return Bx, Bz


def chauffe_induite(mu_r: float):
    """Puissance Joule surfacique le long de x, a mi-largeur (W/m²).

    Passe par `source_spot` -- le MEME chemin que la production : seul mu_r
    change (mu_r = 1 -> eta = 0 -> image nulle -> pas de MFC).
    """
    mem = cfg.geometrie["cfc"]["mu_r"]
    cfg.geometrie["cfc"]["mu_r"] = mu_r
    try:
        Q = source_spot(grille, cfg, couches, courant=COURANT, centre_x=CENTRE_X,
                        centre_y=centre_y)
    finally:
        cfg.geometrie["cfc"]["mu_r"] = mem
    jy = grille.ny // 2
    return np.trapezoid(Q[:, jy, :], grille.z, axis=1)     # W/m²


CAS = [("Bobine seule", False, 1.0), ("Bobine + MFC — montage actuel", True, float(geo["cfc"]["mu_r"]))]
chauffes = [chauffe_induite(mu) for _, _, mu in CAS]
vmax = max(c.max() for c in chauffes)
norme = Normalize(0.0, vmax)

fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.4), sharey=True)
for ax, (titre, avec_mfc, _), chauffe in zip(axes, CAS, chauffes):
    Bx, Bz = champ_coupe(avec_mfc)
    Bn = np.hypot(Bx, Bz)

    ax.contourf(XG * 1e3, ZG * 1e3, np.log10(Bn + 1e-12), levels=22,
                cmap="Blues", alpha=0.35, zorder=0)
    ax.streamplot(xs * 1e3, zs * 1e3, Bx.T, Bz.T, color="0.35", linewidth=0.7,
                  density=1.5, arrowsize=0.7, zorder=2)

    # la piece : barre coloree par la chauffe induite (comme les vignettes NIAR)
    xg = grille.x * 1e3
    seg = np.stack([xg[:-1], xg[1:]], axis=1)
    for (xa, xb), val in zip(seg, 0.5 * (chauffe[:-1] + chauffe[1:])):
        ax.add_patch(Rectangle((xa, -ep_plaque * 1e3), xb - xa, ep_plaque * 1e3,
                               facecolor=plt.cm.inferno(norme(val)), edgecolor="none",
                               zorder=6))
    ax.add_patch(Rectangle((xg[0], -ep_plaque * 1e3), xg[-1] - xg[0], ep_plaque * 1e3,
                           facecolor="none", edgecolor="0.15", linewidth=1.2, zorder=7))

    # concentrateur
    if avec_mfc:
        ax.add_patch(Rectangle(((CENTRE_X - mfc_x / 2) * 1e3, z_miroir * 1e3),
                               mfc_x * 1e3, mfc_h * 1e3, facecolor="#B4B4B4",
                               edgecolor="0.15", linewidth=1.3, zorder=4))
    # brins de la bobine, courants opposes
    for sgn, marque in ((-1, "×"), (1, "•")):
        xc = (CENTRE_X + sgn * entraxe / 2) * 1e3
        ax.add_patch(Rectangle((xc - tube / 2 * 1e3, (h_coil - tube / 2) * 1e3),
                               tube * 1e3, tube * 1e3, facecolor="#E69F00",
                               edgecolor="0.15", linewidth=1.2, zorder=8))
        ax.text(xc, h_coil * 1e3, marque, ha="center", va="center",
                fontsize=13 if marque == "×" else 20, fontweight="bold",
                color="0.1", zorder=9)

    if avec_mfc:
        gain = chauffes[1].max() / chauffes[0].max()
        ax.text(0.985, 0.045, f"pic de chauffe  ×{gain:.1f}".replace(".", ","),
                transform=ax.transAxes, ha="right", va="bottom", fontsize=11.5,
                fontweight="bold", color="0.12", zorder=12,
                bbox=dict(facecolor="white", alpha=0.88, edgecolor="0.6", pad=3.5))
    ax.set_title(titre, pad=8)
    ax.set_xlabel("x (mm) — longueur de la plaque")
    ax.set_xlim(xs[0] * 1e3, xs[-1] * 1e3)
    ax.set_ylim(zs[0] * 1e3, zs[-1] * 1e3)
    ax.set_aspect("equal")

axes[0].set_ylabel("z (mm) — hauteur")
sm = plt.cm.ScalarMappable(norm=norme, cmap="inferno")
cb = fig.colorbar(sm, ax=axes, fraction=0.026, pad=0.02)
cb.set_label("Puissance Joule induite dans la plaque (W/m²)")

OUT = R / "biblio" / "modele" / "figures" / "fig_carte_champ_em.png"
fig.savefig(OUT)
print("écrit :", OUT)
print(f"pic de chauffe  sans MFC : {chauffes[0].max():.3e} W/m²")
print(f"pic de chauffe  avec MFC : {chauffes[1].max():.3e} W/m²  "
      f"(×{chauffes[1].max() / chauffes[0].max():.2f})")
