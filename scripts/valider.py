#!/usr/bin/env python
"""Confrontation systématique simulation <-> mesures sur une liste d'essais.

Usage (modèle 3D, défaut) :
    python scripts/valider.py [--facteur F] [--h-contact H] [--h-bas H]
        [--essais chauffe_250A_3TC serieA_A-1 ...] [--nx 61 --ny 21 --nz 15]

Usage (modèle 2D lumpé à l'interface, cf. thermique/solveur2d.py) :
    python scripts/valider.py --modele 2D --facteur F --decalage-x DX \\
        --h-haut H_HAUT --h-bas-2d H_BAS_2D --essais serieA_A-1 ...

Calibrer d'abord (scripts/calibrer.py) puis valider ici SANS recalibrage.

Maillage par défaut (nx=61, ny=21, nz=15, dx=dy=2 mm) : cf. étude de
convergence 2026-07-21 (resultats_convergence_maillage.log, racine du dépôt)
-- scripts/calibrer.py garde délibérément 31x11x13 (grille de CALIBRATION,
non modifiée par cette étude, cf. rapport § verdict theta*).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from jumeau.materiaux import Config
from jumeau.procede import Essai
from jumeau.thermique.solveur2d import SolveurThermique2D
from jumeau.validation.chargement import charger_mesures, recaler_a_la_chauffe
from jumeau.validation.confrontation import rapport_essai


def sauver_sorties(essai, sol, series, df, dossier, modele):
    """Séries simulées (CSV) + figures de confrontation, style simuler_essai.

    ``modele`` : "3D" (carte extraite au plan d'interface iz_interface) ou
    "2D" (le champ EST déjà la carte d'interface, une seule maille dans
    l'épaisseur — cf. thermique/solveur2d.py).
    """
    dossier.mkdir(exist_ok=True)
    nom = essai.spec["nom"]

    pd.DataFrame({"t (s)": sol.t, **{tc: T for tc, T in series.items()}}) \
        .to_csv(dossier / f"{nom}_series_sim.csv", index=False)

    g = essai.grille
    if modele == "2D":
        carte = sol.y.reshape(g.nx, g.ny, -1)
    else:
        Y4 = sol.y.reshape(g.nx, g.ny, g.nz, -1)
        carte = Y4[:, :, g.iz_interface, :]
    i_pic = int(np.argmax(carte.max(axis=(0, 1))))
    plt.figure(figsize=(10, 4))
    plt.pcolormesh(g.x * 1e3, g.y * 1e3, carte[:, :, i_pic].T,
                   shading="gouraud", cmap="inferno")
    plt.colorbar(label="T (°C)")
    plt.xlabel("x (mm)"); plt.ylabel("y (mm)")
    plt.title(f"{nom} — carte T interface [{modele}] à t={sol.t[i_pic]:.0f} s "
              f"(max {carte[:, :, i_pic].max():.0f} °C)")
    plt.tight_layout()
    plt.savefig(dossier / f"{nom}_carte_interface_validation.png", dpi=140)
    plt.close()

    plt.figure(figsize=(11, 6))
    couleurs = plt.cm.tab10.colors
    tcol = df.columns[0]
    for i, tc in enumerate(essai.spec.get("tc_valides", [])):
        col = next((c for c in df.columns if c.startswith(tc)), None)
        if col:
            plt.plot(df[tcol], df[col], color=couleurs[i % 10], alpha=0.4,
                     label=f"{tc} mesuré")
    for i, (tc, T) in enumerate(series.items()):
        plt.plot(sol.t, T, color=couleurs[i % 10], lw=2, ls="--", label=f"{tc} simulé")
    plt.axhline(337, color="blue", lw=1, ls=":", label="Tf 337 °C")
    plt.xlabel("t (s)"); plt.ylabel("T (°C)"); plt.legend(fontsize=8)
    plt.title(f"{nom} — validation croisée [{modele}] (paramètres calibrés, sans recalage)")
    plt.tight_layout()
    plt.savefig(dossier / f"{nom}_courbes_validation.png", dpi=140)
    plt.close()


def principale():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modele", choices=["3D", "2D"], default="3D",
                    help="'3D' (défaut) ou '2D' (modèle lumpé à l'interface, "
                         "cf. thermique/solveur2d.py) — seuls les TC 'z: interface' "
                         "sont alors comparés (les autres n'apparaissent pas dans "
                         "'series', cf. Essai.series_tc)")
    ap.add_argument("--essais", nargs="+",
                    default=["chauffe_250A_3TC", "serieA_A-1", "serieA_A-3", "serieB_B-2"])
    ap.add_argument("--facteur", type=float, default=1.0)
    ap.add_argument("--decalage-x", type=float, default=0.0,
                    help="décalage bobine<->montage le long de x (m), calibré (amplitude non signée)")
    ap.add_argument("--h-contact", type=float, default=None, help="(modèle 3D)")
    ap.add_argument("--h-bas", type=float, default=None, help="(modèle 3D)")
    ap.add_argument("--h-haut", type=float, default=None, help="(modèle 2D)")
    ap.add_argument("--h-bas-2d", type=float, default=None, help="(modèle 2D)")
    ap.add_argument("--h-bord-x0", type=float, default=None,
                    help="(modèle 2D) puits de bord additionnel au chant x=0 (montage), W/m².K")
    ap.add_argument("--nx", type=int, default=61,
                    help="défaut 61 (dx=2 mm, cf. étude de convergence maillage "
                         "2026-07-21, rapport resultats_convergence_maillage.log) "
                         "-- 31 était la grille de CALIBRATION, volontairement "
                         "grossière ; le RMSE (métrique de calibration) y est déjà "
                         "convergé à <1 °C près, mais delta_T_max (pic) dérive "
                         "encore de 10-20 °C entre 31x11 et 121x41 selon le TC. "
                         "61x21 est le meilleur compromis coût/résiduel de "
                         "discrétisation identifié (~2-4 min/essai, cf. rapport).")
    ap.add_argument("--champ-reaction", action="store_true",
                    help="active le champ de reaction EM auto-coherent complexe "
                         "(jumeau.em.source_joule.source_spot, defaut False = "
                         "chemin historique inchange) -- cf. resultats_champ_reaction_em.log")
    ap.add_argument("--thermostat-capteurs", action="store_true",
                    help="coupe le thermostat sur le MAX de T aux positions TC "
                         "d'interface reelles (au lieu du centre du spot ; defaut "
                         "False = chemin historique). NECESSITE un theta* recalibre "
                         "avec ce flag -- cf. resultats_diag_b2_thermostat_capteurs.log")
    ap.add_argument("--ny", type=int, default=21)
    ap.add_argument("--nz", type=int, default=15,
                    help="défaut 15 (= défaut Essai/construire_grille) ; nz n'a "
                         "qu'un effet négligeable (<1.5 °C) sur le modèle 2D via la "
                         "quadrature de profondeur de la source EM (procede.py, "
                         "Q.sum(axis=2)*dz) -- cf. rapport de convergence.")
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

    for nom in args.essais:
        chemin = RACINE / "config" / "essais" / f"{nom}.yaml"
        print(f"\n=== {nom} [{args.modele}] ===")
        essai = Essai(cfg, chemin, nx=args.nx, ny=args.ny, nz=args.nz,
                      facteur_couplage=args.facteur, decalage_x=args.decalage_x,
                      racine=RACINE, champ_reaction=args.champ_reaction,
                      thermostat_capteurs=args.thermostat_capteurs)
        solveur, sol = essai.simuler(modele=args.modele)
        series = essai.series_tc(solveur, sol)
        df = recaler_a_la_chauffe(charger_mesures(essai.fichier_mesures))
        duree = float(essai.spec.get("duree_totale", essai.spec["duree_chauffe"]))
        tcol = df.columns[0]
        df = df[df[tcol] <= duree].reset_index(drop=True)
        tc_attendus = essai.spec.get("tc_valides", [])
        if isinstance(solveur, SolveurThermique2D):
            exclus = [tc for tc in tc_attendus if tc not in series]
            if exclus:
                print(f"  (TC exclus, non 'interface' -> non représentables en 2D : {exclus})")
        rapport = rapport_essai(series, sol.t, df, tc_attendus)
        print(rapport.round(1).to_string())
        print(f"RMSE moyen : {rapport['rmse'].mean():.1f} °C ; "
              f"écart T_max moyen : {rapport['delta_T_max'].abs().mean():.1f} °C")
        sauver_sorties(essai, sol, series, df, RACINE / "resultats", args.modele)


if __name__ == "__main__":
    principale()
