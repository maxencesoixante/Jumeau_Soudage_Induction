#!/usr/bin/env python
"""Confrontation systématique simulation <-> mesures sur une liste d'essais.

Usage :
    python scripts/valider.py [--facteur F] [--h-contact H] [--h-bas H]
        [--essais chauffe_250A_3TC serieA_A-1 ...] [--nx 31 --ny 11 --nz 13]

Calibrer d'abord (scripts/calibrer.py) puis valider ici SANS recalibrage.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from jumeau.materiaux import Config
from jumeau.procede import Essai
from jumeau.validation.chargement import charger_mesures, recaler_a_la_chauffe
from jumeau.validation.confrontation import rapport_essai


def principale():
    ap = argparse.ArgumentParser()
    ap.add_argument("--essais", nargs="+",
                    default=["chauffe_250A_3TC", "serieA_A-1", "serieA_A-3", "serieB_B-2"])
    ap.add_argument("--facteur", type=float, default=1.0)
    ap.add_argument("--h-contact", type=float, default=None)
    ap.add_argument("--h-bas", type=float, default=None)
    ap.add_argument("--nx", type=int, default=31)
    ap.add_argument("--ny", type=int, default=11)
    ap.add_argument("--nz", type=int, default=13)
    args = ap.parse_args()

    cfg = Config.charger(RACINE / "config")
    if args.h_contact is not None:
        cfg.contact.h_contact = args.h_contact
    if args.h_bas is not None:
        cfg.ambiant.h_bas = args.h_bas

    for nom in args.essais:
        chemin = RACINE / "config" / "essais" / f"{nom}.yaml"
        print(f"\n=== {nom} ===")
        essai = Essai(cfg, chemin, nx=args.nx, ny=args.ny, nz=args.nz,
                      facteur_couplage=args.facteur, racine=RACINE)
        solveur, sol = essai.simuler()
        series = essai.series_tc(solveur, sol)
        df = recaler_a_la_chauffe(charger_mesures(essai.fichier_mesures))
        duree = float(essai.spec.get("duree_totale", essai.spec["duree_chauffe"]))
        tcol = df.columns[0]
        df = df[df[tcol] <= duree].reset_index(drop=True)
        rapport = rapport_essai(series, sol.t, df, essai.spec.get("tc_valides", []))
        print(rapport.round(1).to_string())
        print(f"RMSE moyen : {rapport['rmse'].mean():.1f} °C ; "
              f"écart T_max moyen : {rapport['delta_T_max'].abs().mean():.1f} °C")


if __name__ == "__main__":
    principale()
