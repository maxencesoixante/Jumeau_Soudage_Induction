#!/usr/bin/env python
"""Issue #74 — étape 1 : point de référence du gradient d'épaisseur en 3D.

Rejoue les 5 essais à 3 TC empilés (surface / interface / face opposée, en
x=60, y=20) avec le modèle 3D, dans la configuration du diagnostic du
2026-08-13 (facteur_couplage 6.0123, h_contact 5, h_bas 15, grille 31×11×15),
et compare aux mesures deux rapports :

    o/i = face opposée / interface        (mesuré : fourchette 0,32–0,48)
    s/i = surface / interface             (mesuré : 0,84–0,94)

C'est le CONTRÔLE D'ATTRIBUTION de #74 : avant de tester le moindre levier, on
doit retrouver le symptôme documenté (3D ≈ 0,9 sur o/i). Si on ne le retrouve
pas, c'est le résultat, et il porte sur le code ou sur la mémoire.

Deux définitions de « au pic » sont calculées, car elles ne donnent pas la même
chose sur la face opposée, qui culmine après l'interface :
  - « pics » : max(T_opposée) / max(T_interface) ;
  - « instant » : T_opposée / T_interface à l'instant du pic d'interface.

Option --alpha-inf : multiplie la source Joule sous l'interface (test de la piste
« source plus concentrée vers le haut » ; 0 = aucune chaleur déposée dessous).

Sortie : resultats/diag_epaisseur_3d_reference.log (ou _alpha_inf<α>.log)
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))

from jumeau.materiaux import Config  # noqa: E402
from jumeau.procede import Essai  # noqa: E402
from jumeau.validation.chargement import charger_mesures  # noqa: E402

ESSAIS = ["chauffe_174A_3TC", "chauffe_201A_3TC", "chauffe_226A_3TC",
          "chauffe_226A_3TC_bis", "chauffe_250A_3TC"]
NOMS = {"TC1": "surface", "TC2": "interface", "TC3": "opposee"}
OUT_DIR = R / "resultats"


def rapports(t, s, i, o):
    """(o/i pics, s/i pics, o/i instant, s/i instant, T_i max)."""
    k = int(np.nanargmax(i))
    return (np.nanmax(o) / i[k], np.nanmax(s) / i[k], o[k] / i[k], s[k] / i[k], i[k])


def mesure(essai: Essai):
    df = charger_mesures(essai.fichier_mesures, seuil_aberrant=2000.0)
    t = df.iloc[:, 0].to_numpy()
    duree = float(essai.spec.get("duree_totale", essai.spec["duree_chauffe"]))
    m = t <= duree + 60.0              # relevé utile (+ marge : la face opposée culmine tard)
    col = {c.split()[0]: c for c in df.columns[1:]}
    return (t[m], *(df[col[n]].to_numpy()[m] for n in ("TC1", "TC2", "TC3")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nx", type=int, default=31)
    ap.add_argument("--ny", type=int, default=11)
    ap.add_argument("--nz", type=int, default=15)
    ap.add_argument("--facteur", type=float, default=6.0123)
    ap.add_argument("--h-contact", type=float, default=5.0)
    ap.add_argument("--h-bas", type=float, default=15.0)
    ap.add_argument("--essais", nargs="+", default=ESSAIS)
    ap.add_argument("--alpha-inf", type=float, default=1.0,
                    help="facteur sur la source Joule SOUS l'interface (laminé inf) ; 1 = inchangé")
    a = ap.parse_args()

    lignes = []
    def log(s=""):
        print(s, flush=True); lignes.append(s)

    log(f"3D : facteur {a.facteur}, h_contact {a.h_contact}, h_bas {a.h_bas}, "
        f"grille {a.nx}×{a.ny}×{a.nz}, alpha_inf {a.alpha_inf}")
    log(f"{'essai':22s} {'':6s} {'o/i pics':>9s} {'s/i pics':>9s} {'o/i inst':>9s} "
        f"{'s/i inst':>9s} {'T_i max':>8s} {'durée':>6s}")
    for nom in a.essais:
        cfg = Config.charger(R / "code" / "config")
        cfg.contact.h_contact = a.h_contact
        cfg.ambiant.h_bas = a.h_bas
        e = Essai(cfg, R / "code" / "config" / "essais" / f"{nom}.yaml",
                  nx=a.nx, ny=a.ny, nz=a.nz, facteur_couplage=a.facteur, racine=R)
        if a.alpha_inf != 1.0:
            lam = cfg.geometrie["laminate"]
            dessous = e.grille.z > lam["epaisseur_sup"] + lam["epaisseur_film"] / 2
            for Q in e._Q_spots:
                Q[:, :, dessous] *= a.alpha_inf
        tm, sm, im, om = mesure(e)
        rm = rapports(tm, sm, im, om)
        t0 = time.time()
        solveur, sol = e.simuler(modele="3D")
        ser = e.series_tc(solveur, sol)
        rs = rapports(sol.t, ser["TC1"], ser["TC2"], ser["TC3"])
        dt = time.time() - t0
        log(f"{nom:22s} {'mesuré':6s} " + " ".join(f"{v:9.2f}" for v in rm[:4]) + f" {rm[4]:8.0f}")
        log(f"{'':22s} {'3D':6s} " + " ".join(f"{v:9.2f}" for v in rs[:4]) + f" {rs[4]:8.0f} {dt:5.0f}s")
    OUT = OUT_DIR / ("diag_epaisseur_3d_reference.log" if a.alpha_inf == 1.0
                     else f"diag_epaisseur_3d_alpha_inf{a.alpha_inf:g}.log")
    OUT.write_text("\n".join(lignes) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
