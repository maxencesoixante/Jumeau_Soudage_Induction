#!/usr/bin/env python
"""Calibration LHS+NLSQ des entrées incertaines contre un essai mesuré.

Usage :
    python scripts/calibrer.py [--essai chauffe_250A_3TC] [--n-lhs 12]

Sortie : paramètres [facteur_couplage, h_contact, h_bas] à passer ensuite à
scripts/valider.py pour la validation croisée SANS recalibrage.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from jumeau.identification.calibration import Calibrateur
from jumeau.materiaux import Config


def principale():
    ap = argparse.ArgumentParser()
    ap.add_argument("--essai", default="chauffe_250A_3TC")
    ap.add_argument("--n-lhs", type=int, default=12)
    ap.add_argument("--nx", type=int, default=31)
    ap.add_argument("--ny", type=int, default=11)
    ap.add_argument("--nz", type=int, default=13)
    args = ap.parse_args()

    cfg = Config.charger(RACINE / "config")
    chemin = RACINE / "config" / "essais" / f"{args.essai}.yaml"
    cal = Calibrateur(cfg, chemin, nx=args.nx, ny=args.ny, nz=args.nz)
    print(f"Calibration sur {args.essai} — TC : {cal.tc_valides}")
    res = cal.calibrer(n_lhs=args.n_lhs)

    print("\nParamètres calibrés :")
    for nom, val in res.parametres.items():
        print(f"  {nom} = {val:.4g}")
    print(f"Coût final : {res.cout:.1f} | succès : {res.succes}")
    print("\nValidation croisée :")
    print(f"  python scripts/valider.py --facteur {res.parametres['facteur_couplage']:.4g} "
          f"--h-contact {res.parametres['h_contact']:.4g} "
          f"--h-bas {res.parametres['h_bas']:.4g}")


if __name__ == "__main__":
    principale()
