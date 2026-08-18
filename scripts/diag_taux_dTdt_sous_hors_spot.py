#!/usr/bin/env python
"""Diagnostic — déficit de TAUX de chauffe (dT/dt) au théta* de référence,
séparé SOUS-SPOT (courant direct, lobe M) vs HORS-SPOT (conduction/étalement).

Contexte : suite de resultats_diag_taux_chauffe.log (qui montrait, sur les
essais A/B, un taux "2x trop lent" mais UNIQUEMENT sur les TC hors-spot ;
sous le spot -- chants de exp7 -- le taux était déjà correct à ~15% près).
Ce script APPORTE l'angle NOUVEAU demandé : exp9 (y=0 bord, y=20 centre) +
classification systématique sous-spot / hors-spot / centre-oeil-de-boucle sur
TOUS les essais de la campagne "bord-centre"/"dissipation longitudinale".

Méthode par TC : fenêtre = 25%-75% de la montée MESURÉE (en température, entre
T_amb et le pic mesuré), régression linéaire de T(t) sur cette fenêtre
(mesuré ET simulé, sur les MÊMES bornes de temps -- pas de "taux au même seuil
absolu" qui échoue pour les TC hors-spot dont le pic est bas, cf.
confrontation.taux_de_chauffe(T_ref=75) -> NaN pour la plupart des TC hors-spot
d'exp9). Modèle 2D, théta* de référence FIGÉ (README docs/modele/README.md) :
facteur_couplage=6.0123, h_haut=30.087, h_bas_2d=37.424, h_bord_x0=250,
k_plan=3.0 (config), twill=0.20mm (config). AUCUN paramètre modifié.

Usage : .venv/bin/python scripts/diag_taux_dTdt_sous_hors_spot.py
Sortie : table sur stdout + journaux/archive/resultats_diag_taux_dTdt_sous_hors_spot.log
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from jumeau.materiaux import Config
from jumeau.procede import Essai
from jumeau.validation.chargement import charger_mesures, recaler_a_la_chauffe

# theta* de reference (docs/modele/README.md, 2026-07-30)
FACTEUR = 6.0123
H_HAUT = 30.087
H_BAS_2D = 37.424
H_BORD_X0 = 250.0

# essais + classification du regime par TC (position geometrique documentee
# dans chaque config/essais/*.yaml)
ESSAIS = {
    "exp7_150A": {
        "TC1": "sous-spot (chant y=0, lobe M)",
        "TC2": "lobe intermediaire (y=10)",
        "TC3": "centre-oeil (y=20, courant nul)",
        "TC4": "lobe intermediaire (y=30)",
        "TC5": "sous-spot (chant y=40, lobe M)",
    },
    "exp7_200A": {
        "TC1": "sous-spot (chant y=0, lobe M)",
        "TC2": "lobe intermediaire (y=10)",
        "TC3": "centre-oeil (y=20, courant nul)",
        "TC4": "lobe intermediaire (y=30)",
        "TC5": "sous-spot (chant y=40, lobe M)",
    },
    "exp7_250A": {
        "TC1": "sous-spot (chant y=0, lobe M)",
        "TC2": "lobe intermediaire (y=10)",
        "TC3": "centre-oeil (y=20, courant nul)",
        "TC4": "lobe intermediaire (y=30)",
        "TC5": "sous-spot (chant y=40, lobe M)",
    },
    "exp9_200A_monospot": {          # bord y=0 : ligne EN LONGUEUR au chant
        "TC1": "hors-spot (x=0, 60mm du spot)",
        "TC2": "hors-spot (x=30, 30mm du spot)",
        "TC3": "sous-spot (x=60,y=0 : spot ET chant)",
        "TC4": "hors-spot (x=90, 30mm du spot)",
        "TC5": "hors-spot (x=120, 60mm du spot)",
    },
    "exp9_200A_y20_monospot": {      # centre y=20 : ligne EN LONGUEUR au centre
        "TC1": "hors-spot (x=0, centre largeur)",
        "TC2": "hors-spot (x=30, centre largeur)",
        "TC3": "centre-oeil (x=60,y=20 : spot en x, courant nul en y)",
        "TC4": "hors-spot (x=90, centre largeur)",
        "TC5": "hors-spot (x=120, centre largeur)",
    },
}


def pente_fenetre(t: np.ndarray, T: np.ndarray, t_lo: float, t_hi: float) -> float:
    """Regression lineaire de T(t) sur [t_lo, t_hi] -> pente (degC/s)."""
    if t_hi <= t_lo:
        return float("nan")
    m = (t >= t_lo) & (t <= t_hi)
    if m.sum() < 2:
        return float("nan")
    p = np.polyfit(t[m], T[m], 1)
    return float(p[0])


def fenetre_montee(t_mes: np.ndarray, T_mes: np.ndarray, frac_lo=0.25, frac_hi=0.75):
    """Bornes de temps [t_lo, t_hi] correspondant a 25%/75% de la montee
    mesuree (entre T_amb=T_mes[0] et le PIC mesure), sur la portion croissante
    avant le pic (evite de capter le refroidissement)."""
    i_pic = int(np.argmax(T_mes))
    if i_pic < 2:
        return float("nan"), float("nan")
    t_m, T_m = t_mes[: i_pic + 1], T_mes[: i_pic + 1]
    T0, T1 = T_m[0], T_m[-1]
    if T1 - T0 < 5.0:
        return float("nan"), float("nan")
    seuil_lo = T0 + frac_lo * (T1 - T0)
    seuil_hi = T0 + frac_hi * (T1 - T0)
    i_lo = np.searchsorted(T_m, seuil_lo)
    i_hi = np.searchsorted(T_m, seuil_hi)
    i_lo = min(max(i_lo, 0), len(t_m) - 1)
    i_hi = min(max(i_hi, 0), len(t_m) - 1)
    return float(t_m[i_lo]), float(t_m[i_hi])


def main():
    cfg = Config.charger(RACINE / "config")
    cfg.contact.h_haut = H_HAUT
    cfg.ambiant.h_bas_2d = H_BAS_2D
    cfg.ambiant.h_bord_x0 = H_BORD_X0

    lignes = []
    for nom, regimes in ESSAIS.items():
        chemin = RACINE / "config" / "essais" / f"{nom}.yaml"
        essai = Essai(cfg, chemin, nx=61, ny=21, nz=15,
                      facteur_couplage=FACTEUR, decalage_x=0.0, racine=RACINE)
        solveur, sol = essai.simuler(modele="2D")
        series = essai.series_tc(solveur, sol)
        df = recaler_a_la_chauffe(charger_mesures(essai.fichier_mesures))
        duree = float(essai.spec.get("duree_totale", essai.spec["duree_chauffe"]))
        tcol = df.columns[0]
        df = df[df[tcol] <= duree].reset_index(drop=True)
        t_mes_full = df[tcol].values

        for tc, regime in regimes.items():
            col = next((c for c in df.columns if c.startswith(tc)), None)
            if col is None or tc not in series:
                continue
            T_mes = df[col].values
            t_lo, t_hi = fenetre_montee(t_mes_full, T_mes)
            taux_mes = pente_fenetre(t_mes_full, T_mes, t_lo, t_hi)
            T_sim_interp = np.interp(t_mes_full, sol.t, series[tc])
            taux_sim = pente_fenetre(t_mes_full, T_sim_interp, t_lo, t_hi)
            deficit_pct = (taux_sim - taux_mes) / taux_mes * 100.0 if taux_mes else float("nan")
            lignes.append({
                "essai": nom, "TC": tc, "regime": regime,
                "t_lo": round(t_lo, 1), "t_hi": round(t_hi, 1),
                "taux_mes (degC/s)": round(taux_mes, 2),
                "taux_sim (degC/s)": round(taux_sim, 2),
                "deficit_%": round(deficit_pct, 1),
            })

    tbl = pd.DataFrame(lignes)
    pd.set_option("display.width", 160)
    pd.set_option("display.max_rows", 200)
    texte = tbl.to_string(index=False)
    print(texte)

    # moyenne par regime agrege (sous-spot vs hors-spot vs centre-oeil)
    def famille(r):
        if r.startswith("sous-spot"):
            return "SOUS-SPOT"
        if r.startswith("centre-oeil"):
            return "CENTRE-OEIL"
        if r.startswith("hors-spot"):
            return "HORS-SPOT"
        return "LOBE-INTERMEDIAIRE"

    tbl["famille"] = tbl["regime"].apply(famille)
    resume = tbl.groupby("famille")[["deficit_%"]].mean().round(1)
    resume["n"] = tbl.groupby("famille").size()
    print("\nRésumé par famille (déficit % moyen = (sim-mes)/mes*100, <0 = modèle trop lent) :")
    print(resume.to_string())

    out = RACINE / "journaux" / "resultats_diag_taux_dTdt_sous_hors_spot.log"
    with open(out, "w") as f:
        f.write("Diagnostic -- deficit dT/dt sous-spot vs hors-spot (theta* de reference)\n")
        f.write("=" * 78 + "\n")
        f.write(f"facteur={FACTEUR} h_haut={H_HAUT} h_bas_2d={H_BAS_2D} "
                f"h_bord_x0={H_BORD_X0} k_plan=config twill=config, modele 2D 61x21x15\n\n")
        f.write(texte + "\n\n")
        f.write("Résumé par famille (déficit % moyen) :\n")
        f.write(resume.to_string() + "\n")
    print(f"\n[log ecrit] {out}")


if __name__ == "__main__":
    main()
