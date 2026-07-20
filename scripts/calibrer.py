#!/usr/bin/env python
"""Calibration LHS+NLSQ des entrées incertaines contre un essai mesuré.

Usage :
    python scripts/calibrer.py [--essai chauffe_250A_3TC] [--n-lhs 12]

    # reprise à chaud (saute le LHS) :
    python scripts/calibrer.py --theta0 F DX H_CONTACT H_BAS --max-nfev 40

    # facteur_couplage et decalage_x sont quasi-non-identifiables ensemble
    # (corr > 0.95, cf. jumeau.identification.calibration) : figer decalage_x
    # au bord physique de son enveloppe et ne calibrer que les 3 autres :
    python scripts/calibrer.py --figer-decalage-x 0.015 --theta0 5.2189 0.015 5.0 50.919

Sortie : paramètres [facteur_couplage, decalage_x, h_contact, h_bas] à passer
ensuite à scripts/valider.py pour la validation croisée SANS recalibrage.

Note sur decalage_x : borné à [0, decalage-x-max] et non signé — le résidu de
chauffe_250A_3TC (spot ET thermocouples centrés en x=0,060 sur un domaine
symétrique) est pair en decalage_x (vérifié numériquement : ±5 mm et ±10 mm
donnent des séries TC strictement identiques), le signe n'est donc pas
identifiable depuis cet essai. Voir la docstring de
``jumeau.identification.calibration`` pour le détail.

Note sur --figer-decalage-x : le fit joint à 4 paramètres sur
chauffe_250A_3TC (2026-07-18/19) donne corr(facteur_couplage, decalage_x) =
0.985 > 0.95 ET decalage_x railé exactement sur sa borne haute — signal de
quasi-non-identifiabilité (même famille de piège que f_I/r_I). La
recommandation de calibration.py est de FIGER decalage_x (par ex. au bord
physique de l'enveloppe bobine/CFC, 0,015 m — une hypothèse, pas une mesure)
et de ne calibrer que [facteur_couplage, h_contact, h_bas], dont les
corrélations post-fit repassent alors toutes sous 0.95.
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
    ap.add_argument("--max-nfev", type=int, default=60)
    ap.add_argument("--nx", type=int, default=31)
    ap.add_argument("--ny", type=int, default=11)
    ap.add_argument("--nz", type=int, default=13)
    ap.add_argument("--decalage-x-max", type=float, default=0.015,
                    help="borne haute (m) de |decalage_x| ; borne basse fixée à 0 "
                         "(signe non identifiable, cf. docstring calibration.py)")
    ap.add_argument("--theta0", type=float, nargs=4, default=None,
                    metavar=("FACTEUR", "DECALAGE", "H_CONTACT", "H_BAS"),
                    help="démarrage à chaud : saute le LHS et lance le NLSQ depuis "
                         "ce point complet (reprise d'une calibration interrompue)")
    ap.add_argument("--figer-decalage-x", type=float, default=None, metavar="VALEUR",
                    help="fige decalage_x à VALEUR (m) et calibre seulement "
                         "[facteur_couplage, h_contact, h_bas] — à utiliser si "
                         "corr(facteur_couplage, decalage_x) > 0.95 sur le fit joint")
    args = ap.parse_args()

    cfg = Config.charger(RACINE / "config")
    chemin = RACINE / "config" / "essais" / f"{args.essai}.yaml"
    cal = Calibrateur(cfg, chemin, nx=args.nx, ny=args.ny, nz=args.nz,
                      bornes_basses=(0.05, 0.0, 5.0, 2.0),
                      bornes_hautes=(30.0, args.decalage_x_max, 500.0, 300.0))
    print(f"Calibration sur {args.essai} — TC : {cal.tc_valides}")
    print(f"Paramètres : {cal.NOMS}")
    print(f"Bornes basses  : {cal.bornes[0].tolist()}")
    print(f"Bornes hautes  : {cal.bornes[1].tolist()}")

    figer = {"decalage_x": args.figer_decalage_x} if args.figer_decalage_x is not None else None
    res = cal.calibrer(n_lhs=args.n_lhs, max_nfev=args.max_nfev, theta0=args.theta0, figer=figer)

    print("\nParamètres calibrés + figés :")
    for nom in cal.NOMS:
        val = res.parametres[nom]
        if nom in res.parametres_figes:
            print(f"  {nom} = {val:.5g}  (FIGÉ, non calibré)")
        else:
            se = res.erreurs_std.get(nom, float("nan")) if res.erreurs_std else float("nan")
            print(f"  {nom} = {val:.5g} ± {se:.3g}")
    print(f"Coût final : {res.cout:.1f} | succès : {res.succes} "
          f"({res.nfev} évaluations NLSQ) | message solveur : {res.message}")
    if res.correlation is not None:
        print(f"Corrélations paramétriques (ordre {res.noms_calibres}) :")
        print(res.correlation)
        # avertissement explicite si deux paramètres CALIBRÉS (figés exclus)
        # sont quasi-non-identifiables ensemble (|r| > 0.95) — en particulier
        # facteur_couplage <-> decalage_x, la paire à risque signalée par
        # l'agent EM (même famille de piège que f_I/r_I).
        noms = res.noms_calibres
        for i in range(len(noms)):
            for j in range(i + 1, len(noms)):
                r = res.correlation[i, j]
                if abs(r) > 0.95:
                    print(f"  ATTENTION : |corr({noms[i]}, {noms[j]})| = {abs(r):.3f} > 0.95 "
                          f"— quasi-non-identifiabilité, à ne pas calibrer conjointement "
                          f"sans figer l'un des deux (--figer-decalage-x par ex.).")

    print("\nValidation croisée :")
    print(f"  python scripts/valider.py --facteur {res.parametres['facteur_couplage']:.5g} "
          f"--decalage-x {res.parametres['decalage_x']:.5g} "
          f"--h-contact {res.parametres['h_contact']:.5g} "
          f"--h-bas {res.parametres['h_bas']:.5g}")


if __name__ == "__main__":
    principale()
