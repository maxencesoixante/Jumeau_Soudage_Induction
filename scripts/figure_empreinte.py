#!/usr/bin/env python
"""Figure façon Lionetto et al. 2017 (Mat. & Design, Fig. 4) — cartes de
température simulées à l'interface de soudure à différents instants.

Équivalent semi-statique : au lieu d'une bobine avançant en continu (2 mm/s),
la tête (hairpin + CFC) est indexée sur 4 empreintes successives ; chaque
panneau montre la carte d'interface à la fin de l'impulsion de chauffe d'une
empreinte. L'empreinte CFC active est tracée en pointillés rouges, la flèche
indique la direction d'avance de la tête.

Usage :
    python scripts/figure_empreinte.py config/essais/serieA_A-1.yaml \
        --facteur 3.849 --h-contact 5.0 --h-bas 45.87 [--temps 79 473 820 1169]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrow, Rectangle

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from jumeau.materiaux import Config
from jumeau.procede import Essai


def principale():
    ap = argparse.ArgumentParser()
    ap.add_argument("essai", nargs="?", default="config/essais/serieA_A-1.yaml")
    ap.add_argument("--modele", choices=["2D", "3D"], default="2D",
                    help="2D lumpé à l'interface (défaut, cohérent avec la "
                         "validation/calibration) ou 3D avec gradient d'épaisseur")
    ap.add_argument("--facteur", type=float, default=1.0)
    ap.add_argument("--decalage-x", type=float, default=0.0,
                    help="décalage bobine<->montage le long de x (m), calibré")
    ap.add_argument("--h-contact", type=float, default=None, help="(modèle 3D)")
    ap.add_argument("--h-bas", type=float, default=None, help="(modèle 3D)")
    ap.add_argument("--h-haut", type=float, default=None, help="(modèle 2D)")
    ap.add_argument("--h-bas-2d", type=float, default=None, help="(modèle 2D)")
    ap.add_argument("--h-bord-x0", type=float, default=None,
                    help="(modèle 2D) puits de bord au chant x=0, W/m².K")
    ap.add_argument("--temps", type=float, nargs="+", default=None,
                    help="instants des panneaux (défaut : fin de chaque impulsion)")
    ap.add_argument("--nx", type=int, default=61)
    ap.add_argument("--ny", type=int, default=21)
    ap.add_argument("--nz", type=int, default=15)
    ap.add_argument("--tmax-couleur", type=float, default=None,
                    help="borne haute de l'échelle de couleur (défaut : max global)")
    ap.add_argument("--depuis-cache", action="store_true",
                    help="recharge resultats/<nom>_cartes.npz au lieu de re-simuler")
    ap.add_argument("--suffixe", default="", help="suffixe du nom de fichier figure")
    ap.add_argument("--sortie", default="resultats")
    args = ap.parse_args()

    cfg = Config.charger(RACINE / "config")
    if args.h_contact is not None:
        cfg.contact.h_contact = args.h_contact
    if args.h_bas is not None:
        cfg.ambiant.h_bas = args.h_bas
    if args.h_haut is not None:
        cfg.contact.h_haut = args.h_haut
    if args.h_bas_2d is not None:
        cfg.ambiant.h_bas_2d = args.h_bas_2d
    if args.h_bord_x0 is not None:
        cfg.ambiant.h_bord_x0 = args.h_bord_x0

    essai = Essai(cfg, args.essai, nx=args.nx, ny=args.ny, nz=args.nz,
                  facteur_couplage=args.facteur, decalage_x=args.decalage_x,
                  racine=RACINE)
    nom = essai.spec["nom"]
    dossier = RACINE / args.sortie
    dossier.mkdir(exist_ok=True)
    cache = dossier / f"{nom}_cartes.npz"

    g = essai.grille
    if args.depuis_cache and cache.exists():
        print(f"Rechargement de {cache}")
        d = np.load(cache)
        t_sol, carte = d["t"], d["carte"]
    else:
        print(f"Simulation {nom} [{args.modele}] — grille {args.nx}×{args.ny}×{args.nz}, "
              f"facteur={args.facteur}, consigne={essai.spec.get('consigne_interface')}")
        solveur, sol = essai.simuler(modele=args.modele)
        if args.modele == "2D":
            carte = sol.y.reshape(g.nx, g.ny, -1)
        else:
            Y4 = sol.y.reshape(g.nx, g.ny, g.nz, -1)
            carte = Y4[:, :, g.iz_interface, :]
        t_sol = sol.t
        np.savez_compressed(cache, t=t_sol, carte=carte, x=g.x, y=g.y)
        print(f"Cartes d'interface mises en cache : {cache}")

    # instants des panneaux : fin de l'impulsion de chaque empreinte
    if args.temps is None:
        temps = sorted({float(s["t_fin"]) for s in essai.spots})
    else:
        temps = list(args.temps)
    vmax = args.tmax_couleur or float(np.ceil(carte.max() / 10) * 10)

    cfc = cfg.geometrie["cfc"]
    demi_x = cfc["largeur"] / 2.0 * 1e3          # 31,5 mm le long de x
    demi_y = cfc["longueur"] / 2.0 * 1e3         # 55 mm le long de y (déborde)

    ncol = 2
    nlig = int(np.ceil(len(temps) / ncol))
    fig, axes = plt.subplots(nlig, ncol, figsize=(11, 3.1 * nlig),
                             sharex=True, sharey=True, constrained_layout=True)
    axes = np.atleast_1d(axes).ravel()

    for k, (ax, t_k) in enumerate(zip(axes, temps)):
        i_t = int(np.argmin(np.abs(t_sol - t_k)))
        im = ax.pcolormesh(g.x * 1e3, g.y * 1e3, carte[:, :, i_t].T,
                           shading="gouraud", cmap="jet", vmin=20.0, vmax=vmax)
        # empreinte CFC du spot actif (ou dernier actif) en pointillés rouges
        i_spot = essai._spot_actif(t_k - 0.5)
        if i_spot is None:
            i_spot = min(range(len(essai.spots)),
                         key=lambda j: abs(float(essai.spots[j]["t_fin"]) - t_k))
        cx = float(essai.spots[i_spot]["centre_x"]) * 1e3
        cy = g.largeur / 2.0 * 1e3
        x0 = max(cx - demi_x, 0.0)
        x1 = min(cx + demi_x, g.longueur * 1e3)
        ax.add_patch(Rectangle((x0, max(cy - demi_y, 0.0)),
                               x1 - x0, min(2 * demi_y, g.largeur * 1e3),
                               fill=False, edgecolor="red", ls="--", lw=1.6))
        T_max_pan = carte[:, :, i_t].max()
        ax.set_title(f"t = {t_sol[i_t]:.0f} s — empreinte {i_spot + 1} "
                     f"(T$_{{max}}$ = {T_max_pan:.0f} °C)", fontsize=10)
        ax.set_aspect("equal")
        ax.set_xlim(0.0, g.longueur * 1e3)
        ax.set_ylim(0.0, g.largeur * 1e3)
        if k % ncol == 0:
            ax.set_ylabel("y (mm)")
        if k >= len(temps) - ncol:
            ax.set_xlabel("x (mm)")

    for ax in axes[len(temps):]:
        ax.axis("off")

    # flèche d'avance de la tête (le long de x)
    axes[0].add_patch(FancyArrow(8, 34, 18, 0, width=1.2, head_width=3.5,
                                 head_length=5, color="white"))
    axes[0].text(17, 30.2, "avance de la tête", color="white",
                 fontsize=8, ha="center")

    cb = fig.colorbar(im, ax=axes.tolist(), shrink=0.9, label="T (°C)")
    cb.ax.axhline(337.0, color="white", lw=1.5)
    cb.ax.text(1.4, 337.0, " Tf", color="black", fontsize=8, va="center",
               transform=cb.ax.get_yaxis_transform())
    consigne = essai.spec.get("consigne_interface")
    titre = (f"{nom} — cartes de température simulées à l'interface de soudure "
             f"(I = {essai.spec['courant']:.0f} A"
             + (f", coupure à {consigne:.0f} °C" if consigne else "") + ")")
    fig.suptitle(titre, fontsize=11)

    chemin = dossier / f"{nom}_empreinte_thermique_fig4{args.suffixe}.png"
    fig.savefig(chemin, dpi=150)
    print(f"Figure écrite : {chemin}")
    for t_k in temps:
        i_t = int(np.argmin(np.abs(t_sol - t_k)))
        print(f"  t={t_sol[i_t]:6.0f} s : T_max interface = {carte[:, :, i_t].max():5.1f} °C")


if __name__ == "__main__":
    principale()
