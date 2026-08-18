#!/usr/bin/env python
"""Simule un essai et produit la carte de température + courbes TC.

Usage :
    python scripts/simuler_essai.py config/essais/chauffe_250A_3TC.yaml \
        [--facteur 1.0] [--nx 49 --ny 17 --nz 15] [--sortie resultats/]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RACINE = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(RACINE / "code" / "src"))

from jumeau.materiaux import Config
from jumeau.procede import Essai
from jumeau.validation.chargement import charger_mesures, recaler_a_la_chauffe


def principale():
    ap = argparse.ArgumentParser()
    ap.add_argument("essai", help="chemin du YAML d'essai")
    ap.add_argument("--facteur", type=float, default=1.0, help="facteur de couplage source")
    ap.add_argument("--h-contact", type=float, default=None)
    ap.add_argument("--h-bas", type=float, default=None)
    ap.add_argument("--nx", type=int, default=49)
    ap.add_argument("--ny", type=int, default=17)
    ap.add_argument("--nz", type=int, default=15)
    ap.add_argument("--sortie", default="resultats")
    args = ap.parse_args()

    cfg = Config.charger(RACINE / "code" / "config")
    if args.h_contact is not None:
        cfg.contact.h_contact = args.h_contact
    if args.h_bas is not None:
        cfg.ambiant.h_bas = args.h_bas

    essai = Essai(cfg, args.essai, nx=args.nx, ny=args.ny, nz=args.nz,
                  facteur_couplage=args.facteur, racine=RACINE)
    print(f"Essai {essai.spec['nom']} — grille {args.nx}×{args.ny}×{args.nz}, "
          f"facteur={args.facteur}")
    solveur, sol = essai.simuler()
    series = essai.series_tc(solveur, sol)

    dossier = RACINE / args.sortie
    dossier.mkdir(exist_ok=True)
    nom = essai.spec["nom"]

    # --- carte de température à l'interface, au pic global
    g = essai.grille
    Y4 = sol.y.reshape(g.nx, g.ny, g.nz, -1)
    carte_interface = Y4[:, :, g.iz_interface, :]
    i_pic = int(np.argmax(carte_interface.max(axis=(0, 1))))
    plt.figure(figsize=(10, 4))
    plt.pcolormesh(g.x * 1e3, g.y * 1e3, carte_interface[:, :, i_pic].T,
                   shading="gouraud", cmap="inferno")
    plt.colorbar(label="T (°C)")
    plt.xlabel("x (mm)"); plt.ylabel("y (mm)")
    plt.title(f"{nom} — carte T interface à t={sol.t[i_pic]:.0f} s "
              f"(max {carte_interface[:, :, i_pic].max():.0f} °C)")
    plt.tight_layout()
    plt.savefig(dossier / f"{nom}_carte_interface.png", dpi=140)
    plt.close()

    # --- courbes TC simulées vs mesurées
    plt.figure(figsize=(11, 6))
    couleurs = plt.cm.tab10.colors
    try:
        df = recaler_a_la_chauffe(charger_mesures(essai.fichier_mesures))
        tcol = df.columns[0]
        for i, tc in enumerate(essai.spec.get("tc_valides", [])):
            col = next((c for c in df.columns if c.startswith(tc)), None)
            if col:
                plt.plot(df[tcol], df[col], color=couleurs[i % 10], alpha=0.4,
                         label=f"{tc} mesuré")
    except FileNotFoundError:
        print("(mesures introuvables — tracé simulation seule)")
    for i, (tc, T) in enumerate(series.items()):
        plt.plot(sol.t, T, color=couleurs[i % 10], lw=2, ls="--", label=f"{tc} simulé")
    plt.axhline(337, color="blue", lw=1, ls=":", label="Tf 337 °C")
    plt.xlabel("t (s)"); plt.ylabel("T (°C)"); plt.legend(fontsize=8)
    plt.title(f"{nom} — thermocouples simulés vs mesurés")
    plt.tight_layout()
    plt.savefig(dossier / f"{nom}_courbes_tc.png", dpi=140)
    plt.close()

    print(f"Figures écrites dans {dossier}/ :")
    print(f"  {nom}_carte_interface.png\n  {nom}_courbes_tc.png")
    for tc, T in series.items():
        print(f"  {tc}: T_max_sim = {T.max():.1f} °C")


if __name__ == "__main__":
    principale()
