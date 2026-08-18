#!/usr/bin/env python
"""TEST DÉCISIF — le solveur 3D capture-t-il le taux (dT/dt) que le 2D lumpé
rate, sur exp7_200A, à théta* de référence ?

Contexte : resultats_diag_taux_chauffe.log §5 avait déjà testé un run 3D
(essai serieA_A-1, facteur=2D-calibré, h_contact=50, h_bas=15, 31x11x13) et
montré que le hors-spot ACCÉLÈRE en 3D (7.8->11.0 vs cible 16.1) mais que
l'interface directe (TC1) EXPLOSE (90.4 °C/s, pic 682 vs 398 mesuré) --
signe que le 3D au facteur 2D-calibré est mal calé côté source/contact, pas
que le mécanisme "lumping" est faux.

Ce script reprend le test sur l'essai NOMMÉMENT demandé (exp7_200A, campagne
bord-centre CLOSE), fenêtre courte (0-22 s, couvre la montée mesurée
0-18 s), maillage réduit (31x11x13, cf. calibration coût/temps ~16 s/run) :
compare TAUX mesuré vs 2D (théta* de référence complet) vs 3D (même
facteur_couplage=6.0123 ; h_contact/h_bas/T_puits = valeurs par défaut
config, NON calibrées pour le 3D -- le 3D n'a pas de théta* propre, cf.
docs/modele/README.md, seul le 2D est la référence canonique).

Usage : .venv/bin/python scripts/diag/diag_2d_vs_3d_taux_exp7_200A.py
Sortie : table stdout + journaux/archive/resultats_diag_2d_vs_3d_taux_exp7_200A.log
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(RACINE / "code" / "src"))
sys.path.insert(0, str(RACINE / "code" / "scripts"))

from jumeau.materiaux import Config
from jumeau.procede import Essai
from jumeau.validation.chargement import charger_mesures, recaler_a_la_chauffe
from diag_taux_dTdt_sous_hors_spot import fenetre_montee, pente_fenetre

FACTEUR = 6.0123
H_HAUT = 30.087
H_BAS_2D = 37.424
H_BORD_X0 = 250.0

NOM_ESSAI = "exp7_200A"
DUREE_TEST = 22.0     # s -- couvre la montee mesuree (0-18s) + marge
DT_SORTIE = 0.5

REGIMES = {
    "TC1": "sous-spot (chant y=0, lobe M)",
    "TC2": "lobe intermediaire (y=10)",
    "TC3": "centre-oeil (y=20, courant nul)",
    "TC4": "lobe intermediaire (y=30)",
    "TC5": "sous-spot (chant y=40, lobe M)",
}


def main():
    cfg2d = Config.charger(RACINE / "code" / "config")
    cfg2d.contact.h_haut = H_HAUT
    cfg2d.ambiant.h_bas_2d = H_BAS_2D
    cfg2d.ambiant.h_bord_x0 = H_BORD_X0

    chemin = RACINE / "code" / "config" / "essais" / f"{NOM_ESSAI}.yaml"

    t0 = time.time()
    essai_2d = Essai(cfg2d, chemin, nx=61, ny=21, nz=15,
                      facteur_couplage=FACTEUR, decalage_x=0.0, racine=RACINE)
    essai_2d.spec["duree_totale"] = DUREE_TEST
    solveur_2d, sol_2d = essai_2d.simuler(modele="2D", dt_sortie=DT_SORTIE)
    print(f"2D  (61x21x15, {DUREE_TEST}s) : {time.time()-t0:.1f} s")
    series_2d = essai_2d.series_tc(solveur_2d, sol_2d)

    cfg3d = Config.charger(RACINE / "code" / "config")   # h_contact/h_bas/T_puits = defaut config (pas de theta* 3D)
    t0 = time.time()
    essai_3d = Essai(cfg3d, chemin, nx=31, ny=11, nz=13,
                      facteur_couplage=FACTEUR, decalage_x=0.0, racine=RACINE)
    essai_3d.spec["duree_totale"] = DUREE_TEST
    solveur_3d, sol_3d = essai_3d.simuler(modele="3D", dt_sortie=DT_SORTIE)
    print(f"3D  (31x11x13, {DUREE_TEST}s) : {time.time()-t0:.1f} s "
          f"(h_contact={cfg3d.contact.h_contact}, h_bas={cfg3d.ambiant.h_bas}, "
          f"T_puits={cfg3d.contact.T_puits})")
    series_3d = essai_3d.series_tc(solveur_3d, sol_3d)

    df = recaler_a_la_chauffe(charger_mesures(essai_2d.fichier_mesures))
    tcol = df.columns[0]
    df = df[df[tcol] <= DUREE_TEST].reset_index(drop=True)
    t_mes = df[tcol].values

    lignes = []
    for tc, regime in REGIMES.items():
        col = next((c for c in df.columns if c.startswith(tc)), None)
        if col is None:
            continue
        T_mes = df[col].values
        t_lo, t_hi = fenetre_montee(t_mes, T_mes)
        taux_mes = pente_fenetre(t_mes, T_mes, t_lo, t_hi)

        T_2d = np.interp(t_mes, sol_2d.t, series_2d[tc])
        taux_2d = pente_fenetre(t_mes, T_2d, t_lo, t_hi)

        T_3d = np.interp(t_mes, sol_3d.t, series_3d[tc])
        taux_3d = pente_fenetre(t_mes, T_3d, t_lo, t_hi)

        pic_mes = float(np.max(T_mes))
        pic_2d = float(np.max(series_2d[tc]))
        pic_3d = float(np.max(series_3d[tc]))

        lignes.append({
            "TC": tc, "regime": regime,
            "taux_mes": round(taux_mes, 2),
            "taux_2D": round(taux_2d, 2),
            "taux_3D": round(taux_3d, 2),
            "deficit_2D_%": round((taux_2d - taux_mes) / taux_mes * 100, 1) if taux_mes else float("nan"),
            "deficit_3D_%": round((taux_3d - taux_mes) / taux_mes * 100, 1) if taux_mes else float("nan"),
            "pic_mes(@22s)": round(pic_mes, 1),
            "pic_2D(@22s)": round(pic_2d, 1),
            "pic_3D(@22s)": round(pic_3d, 1),
        })

    tbl = pd.DataFrame(lignes)
    pd.set_option("display.width", 160)
    texte = tbl.to_string(index=False)
    print("\n" + texte)

    out = RACINE / "donnees" / "journaux" / "resultats_diag_2d_vs_3d_taux_exp7_200A.log"
    with open(out, "w") as f:
        f.write("Test decisif -- taux dT/dt : 2D lumpe vs 3D complet vs mesure\n")
        f.write("=" * 78 + "\n")
        f.write(f"Essai : {NOM_ESSAI} ; fenetre 0-{DUREE_TEST}s ; theta* de reference 2D "
                f"(facteur={FACTEUR}, h_haut={H_HAUT}, h_bas_2d={H_BAS_2D}, h_bord_x0={H_BORD_X0}) ; "
                f"3D non calibre (h_contact/h_bas/T_puits = config par defaut).\n")
        f.write(f"Maillage : 2D 61x21x15 ; 3D 31x11x13 (reduit, cout ~15s/run).\n\n")
        f.write(texte + "\n")
    print(f"\n[log ecrit] {out}")


if __name__ == "__main__":
    main()
