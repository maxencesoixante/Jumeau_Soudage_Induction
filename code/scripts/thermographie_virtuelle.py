#!/usr/bin/env python
"""Caméra thermique virtuelle — rejoue la vue d'une caméra FLIR à partir du
jumeau, et réciproquement génère le format CSV cible pour la manip
« thermographie plein-champ sur plaque libre »
(cf. biblio/labo/protocole_thermographie_plaque_libre.md, issue #69).

Principe : le solveur 2D expose ``serie_temporelle(sol, x, y)`` (interpolation
BILINÉAIRE en un point physique quelconque) et ``resultat_2d(sol, i)`` (champ
2D). On échantillonne le modèle EXACTEMENT aux ROI (points/lignes/aires) que la
caméra a mesurés, dans le même repère plaque et aux mêmes instants → comparaison
CSV↔CSV apples-to-apples.

⚠️ Modèle LUMPÉ dans l'épaisseur (une seule maille en z) : il ne distingue pas
face avant/arrière alors que la caméra voit la face ARRIÈRE. On compare donc la
FORME (profils normalisés) et la CINÉTIQUE, pas les °C absolus. Sans
céramique/pression les absolus ne sont de toute façon pas comparables aux essais
de soudage.

Deux modes :

    # 1) Auto-test + génération du format CSV cible (aucune donnée réelle requise) :
    python scripts/thermographie_virtuelle.py demo config/essais/exp7_200A.yaml \
        --sortie resultats/thermo_virtuelle_demo

    # 2) Rejeu de vraies CSV caméra (plus tard, après la manip) :
    python scripts/thermographie_virtuelle.py rejouer config/essais/<manip>.yaml \
        --csv-dir <dossier des CSV FLIR> --sortie resultats/thermo_virtuelle_manip
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

RACINE = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(RACINE / "code" / "src"))

from jumeau.materiaux import Config  # noqa: E402
from jumeau.procede import Essai  # noqa: E402

MM = 1e-3  # 1 mm en mètres — le CSV est en mm, le modèle en mètres.


# --------------------------------------------------------------------------
# Simulation
# --------------------------------------------------------------------------
def charger_simulation(essai_yaml: str, facteur: float, nx: int, ny: int,
                       dt_sortie: float):
    """Simule l'essai en 2D et rend (essai, solveur, sol)."""
    cfg = Config.charger(RACINE / "code" / "config")
    essai = Essai(cfg, essai_yaml, nx=nx, ny=ny, nz=15,
                  facteur_couplage=facteur, racine=RACINE)
    solveur, sol = essai.simuler(dt_sortie=dt_sortie, modele="2D")
    return essai, solveur, sol


# --------------------------------------------------------------------------
# Plan de ROI standard (le même pour la génération et le rejeu)
# --------------------------------------------------------------------------
def plan_roi_standard(essai, n_ligne: int = 41):
    """Construit le jeu de ROI standard du protocole, en MILLIMÈTRES, à partir
    de la géométrie de l'essai. Repère plaque : x = longueur, y = largeur,
    origine au coin (0, 0), centre de largeur = largeur/2.

    - LT : ligne transverse (profil M) à x = x_spot, y de 0 → largeur.
    - LL : ligne longitudinale (étalement hors-spot) à y = largeur/2, x de 0 → longueur.
    - P0..P4 : points aux positions TC exp7 (x = x_spot ; y = 0,10,20,30,40 mm).
    - C_spot : cercle sur l'empreinte du spot (rayon 10 mm).
    - A_plaque : plaque entière.
    """
    g = essai.grille
    Lx_mm = float(g.longueur) / MM
    Ly_mm = float(g.largeur) / MM
    x_spot_mm = float(essai.spec["spots"][0]["centre_x"]) / MM
    y_centre_mm = Ly_mm / 2.0

    # LT : transverse, s = abscisse le long de y
    ys = np.linspace(0.0, Ly_mm, n_ligne)
    LT = [(float(y), x_spot_mm, float(y)) for y in ys]  # (s_mm, x_mm, y_mm)

    # LL : longitudinale, s = abscisse le long de x
    xs = np.linspace(0.0, Lx_mm, n_ligne)
    LL = [(float(x), float(x), y_centre_mm) for x in xs]  # (s_mm, x_mm, y_mm)

    # P0..P4 aux positions TC exp7 (y bornée à la largeur réelle)
    points = [(f"P{i}", x_spot_mm, float(min(yv, Ly_mm)))
              for i, yv in enumerate((0.0, 10.0, 20.0, 30.0, 40.0))]

    return {
        "meta": {"Lx_mm": Lx_mm, "Ly_mm": Ly_mm,
                 "x_spot_mm": x_spot_mm, "y_centre_mm": y_centre_mm},
        "points": points,                         # [(roi_id, x_mm, y_mm)]
        "lignes": {"LT": LT, "LL": LL},           # {roi_id: [(s_mm, x_mm, y_mm)]}
        "aires": {                                # {roi_id: descripteur}
            "C_spot": ("cercle", x_spot_mm, y_centre_mm, 10.0),
            "A_plaque": ("plaque",),
        },
    }


# --------------------------------------------------------------------------
# Échantillonnage du MODÈLE aux ROI (le cœur de la « caméra virtuelle »)
# --------------------------------------------------------------------------
def _serie_interp(solveur, sol, x_mm, y_mm, t_s):
    """Série modèle bilinéaire en (x_mm, y_mm), rééchantillonnée aux instants t_s."""
    serie = solveur.serie_temporelle(sol, x_mm * MM, y_mm * MM)  # sur sol.t
    return np.interp(t_s, sol.t, serie)


def echantillonner_points(solveur, sol, points, t_s):
    lignes_csv = []
    for roi_id, x_mm, y_mm in points:
        T = _serie_interp(solveur, sol, x_mm, y_mm, t_s)
        for k, t in enumerate(t_s):
            lignes_csv.append((float(t), roi_id, x_mm, y_mm, float(T[k])))
    return lignes_csv  # (t_s, roi_id, x_mm, y_mm, T_C)


def echantillonner_lignes(solveur, sol, lignes, t_s):
    lignes_csv = []
    for roi_id, pts in lignes.items():
        for s_mm, x_mm, y_mm in pts:
            T = _serie_interp(solveur, sol, x_mm, y_mm, t_s)
            for k, t in enumerate(t_s):
                lignes_csv.append((float(t), roi_id, s_mm, x_mm, y_mm, float(T[k])))
    return lignes_csv  # (t_s, roi_id, s_mm, x_mm, y_mm, T_C)


def echantillonner_aires(solveur, sol, aires, t_s):
    """Min/Max/Moy du champ modèle sur chaque aire, sur les NŒUDS de la grille
    tombant dans la ROI, puis rééchantillonnés en temps."""
    g = solveur.g
    xg_mm = np.asarray(g.x) / MM
    yg_mm = np.asarray(g.y) / MM
    XX, YY = np.meshgrid(xg_mm, yg_mm, indexing="ij")  # (nx, ny)

    lignes_csv = []
    for roi_id, desc in aires.items():
        if desc[0] == "cercle":
            _, cx, cy, r = desc
            masque = (XX - cx) ** 2 + (YY - cy) ** 2 <= r ** 2
        elif desc[0] == "plaque":
            masque = np.ones_like(XX, dtype=bool)
        else:
            raise ValueError(f"aire {desc!r} inconnue")

        # stats par pas de temps de sol, puis interpolation vers t_s
        tmin = np.empty(sol.t.size)
        tmax = np.empty(sol.t.size)
        tmoy = np.empty(sol.t.size)
        for i in range(sol.t.size):
            champ = solveur.resultat_2d(sol, i)  # (nx, ny)
            vals = champ[masque]
            tmin[i], tmax[i], tmoy[i] = vals.min(), vals.max(), vals.mean()
        Tmin = np.interp(t_s, sol.t, tmin)
        Tmax = np.interp(t_s, sol.t, tmax)
        Tmoy = np.interp(t_s, sol.t, tmoy)
        for k, t in enumerate(t_s):
            lignes_csv.append((float(t), roi_id, float(Tmin[k]),
                               float(Tmax[k]), float(Tmoy[k])))
    return lignes_csv  # (t_s, roi_id, Tmin, Tmax, Tmoy)


# --------------------------------------------------------------------------
# I/O CSV (le schéma cible)
# --------------------------------------------------------------------------
EN_POINTS = ["t_s", "roi_id", "x_mm", "y_mm", "T_C"]
EN_LIGNES = ["t_s", "roi_id", "s_mm", "x_mm", "y_mm", "T_C"]
EN_AIRES = ["t_s", "roi_id", "Tmin_C", "Tmax_C", "Tmoy_C"]


def ecrire_csv(chemin: Path, entete, lignes):
    with open(chemin, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(entete)
        w.writerows(lignes)


def lire_geometrie_points(chemin: Path):
    """(roi_id, x_mm, y_mm) uniques — on IGNORE T_C (c'est ce que le modèle prédit)."""
    vus, out = set(), []
    with open(chemin, newline="") as f:
        for r in csv.DictReader(f):
            cle = (r["roi_id"], float(r["x_mm"]), float(r["y_mm"]))
            if cle not in vus:
                vus.add(cle)
                out.append(cle)
    return out


def lire_geometrie_lignes(chemin: Path):
    """{roi_id: [(s_mm, x_mm, y_mm)]} — T_C ignoré."""
    vus, out = set(), {}
    with open(chemin, newline="") as f:
        for r in csv.DictReader(f):
            rid = r["roi_id"]
            cle = (rid, float(r["s_mm"]), float(r["x_mm"]), float(r["y_mm"]))
            if cle not in vus:
                vus.add(cle)
                out.setdefault(rid, []).append((float(r["s_mm"]),
                                                float(r["x_mm"]), float(r["y_mm"])))
    return out


def lire_temps(chemin: Path):
    with open(chemin, newline="") as f:
        return np.array(sorted({float(r["t_s"]) for r in csv.DictReader(f)}))


# --------------------------------------------------------------------------
# Mode DEMO : génère le format cible + auto-test aller-retour
# --------------------------------------------------------------------------
def mode_demo(args):
    sortie = Path(args.sortie)
    sortie.mkdir(parents=True, exist_ok=True)

    essai, solveur, sol = charger_simulation(
        args.essai, args.facteur, args.nx, args.ny, args.dt_sortie)
    duree = float(sol.t[-1])
    t_cam = np.arange(0.0, duree + args.dt_cam / 2, args.dt_cam)
    plan = plan_roi_standard(essai)

    # (1) le modèle joue le rôle de la « caméra » -> écrit les CSV au format cible
    pts = echantillonner_points(solveur, sol, plan["points"], t_cam)
    lgn = echantillonner_lignes(solveur, sol, plan["lignes"], t_cam)
    air = echantillonner_aires(solveur, sol, plan["aires"], t_cam)
    ecrire_csv(sortie / "roi_points.csv", EN_POINTS, pts)
    ecrire_csv(sortie / "roi_lignes.csv", EN_LIGNES, lgn)
    ecrire_csv(sortie / "roi_aires.csv", EN_AIRES, air)
    recalage = {
        "commentaire": "DEMO synthétique — repère identité, pas de vrais fiduciaux.",
        "fiduciaux": [
            {"id": "F1", "px": 0, "py": 0, "x_mm": 0.0, "y_mm": 0.0},
            {"id": "F2", "px": 0, "py": 0, "x_mm": plan["meta"]["Lx_mm"], "y_mm": 0.0},
            {"id": "F3", "px": 0, "py": 0, "x_mm": plan["meta"]["Lx_mm"], "y_mm": plan["meta"]["Ly_mm"]},
            {"id": "F4", "px": 0, "py": 0, "x_mm": 0.0, "y_mm": plan["meta"]["Ly_mm"]},
        ],
        "emissivite": 0.90, "distance_mm": None, "ambiante_C": None,
        "dt_s": args.dt_cam, "courant_A": float(essai.spec.get("courant", 0.0)),
        "couplage_mm": None,
    }
    (sortie / "recalage.json").write_text(json.dumps(recalage, indent=2, ensure_ascii=False))

    # (2) REJEU : on relit UNIQUEMENT la géométrie et on ré-échantillonne le modèle
    geo_pts = lire_geometrie_points(sortie / "roi_points.csv")
    geo_lgn = lire_geometrie_lignes(sortie / "roi_lignes.csv")
    t_relu = lire_temps(sortie / "roi_points.csv")
    pts_sim = echantillonner_points(solveur, sol, geo_pts, t_relu)
    lgn_sim = echantillonner_lignes(solveur, sol, geo_lgn, t_relu)
    ecrire_csv(sortie / "roi_points_SIM.csv", EN_POINTS, pts_sim)
    ecrire_csv(sortie / "roi_lignes_SIM.csv", EN_LIGNES, lgn_sim)

    # (3) auto-test : le rejeu doit reproduire EXACTEMENT la « caméra » synthétique
    d_pts = max(abs(a[-1] - b[-1]) for a, b in zip(pts, pts_sim))
    d_lgn = max(abs(a[-1] - b[-1]) for a, b in zip(lgn, lgn_sim))
    ecart = max(d_pts, d_lgn)
    print(f"[demo] essai={essai.spec['nom']}  grille={args.nx}x{args.ny}  "
          f"t_cam=[0,{duree:.0f}]s pas {args.dt_cam}s")
    print(f"[demo] CSV format cible écrits dans {sortie}/ "
          f"(roi_points/roi_lignes/roi_aires + recalage.json + *_SIM.csv)")
    print(f"[demo] écart aller-retour max |Δ| = {ecart:.3e} °C")
    ok = ecart < 1e-6
    print("[demo] AUTO-TEST:", "PASS ✅ (chaîne d'échantillonnage exacte)" if ok
          else "FAIL ❌ (voir écart ci-dessus)")
    return 0 if ok else 1


# --------------------------------------------------------------------------
# Mode REJOUER : rejoue de vraies CSV caméra et compare
# --------------------------------------------------------------------------
def mode_rejouer(args):
    sortie = Path(args.sortie)
    sortie.mkdir(parents=True, exist_ok=True)
    csv_dir = Path(args.csv_dir)

    essai, solveur, sol = charger_simulation(
        args.essai, args.facteur, args.nx, args.ny, args.dt_sortie)

    fait = []
    if (csv_dir / "roi_points.csv").exists():
        geo = lire_geometrie_points(csv_dir / "roi_points.csv")
        t_s = lire_temps(csv_dir / "roi_points.csv")
        ecrire_csv(sortie / "roi_points_SIM.csv", EN_POINTS,
                   echantillonner_points(solveur, sol, geo, t_s))
        fait.append("roi_points")
    if (csv_dir / "roi_lignes.csv").exists():
        geo = lire_geometrie_lignes(csv_dir / "roi_lignes.csv")
        t_s = lire_temps(csv_dir / "roi_lignes.csv")
        ecrire_csv(sortie / "roi_lignes_SIM.csv", EN_LIGNES,
                   echantillonner_lignes(solveur, sol, geo, t_s))
        fait.append("roi_lignes")

    if not fait:
        print(f"[rejouer] aucun roi_points.csv / roi_lignes.csv trouvé dans {csv_dir}")
        return 1
    print(f"[rejouer] essai={essai.spec['nom']} — modèle rejoué pour : {', '.join(fait)}")
    print(f"[rejouer] SIM écrit dans {sortie}/ (comparer aux mesures : FORME normalisée "
          f"+ cinétique, PAS les absolus — modèle lumpé face arrière)")
    return 0


# --------------------------------------------------------------------------
def principale():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sous = ap.add_subparsers(dest="mode", required=True)

    d = sous.add_parser("demo", help="auto-test + génération du format CSV cible")
    d.add_argument("essai", help="chemin du YAML d'essai (repère/durée/courant)")
    d.add_argument("--sortie", default="resultats/thermo_virtuelle_demo")
    d.add_argument("--dt-cam", type=float, default=0.5, help="pas temporel caméra (s)")

    r = sous.add_parser("rejouer", help="rejoue de vraies CSV caméra")
    r.add_argument("essai", help="chemin du YAML d'essai correspondant à la manip")
    r.add_argument("--csv-dir", required=True, help="dossier des CSV FLIR (roi_*.csv)")
    r.add_argument("--sortie", default="resultats/thermo_virtuelle_manip")

    for p in (d, r):
        p.add_argument("--facteur", type=float, default=1.0)
        p.add_argument("--nx", type=int, default=49)
        p.add_argument("--ny", type=int, default=17)
        p.add_argument("--dt-sortie", type=float, default=0.5, help="pas de sortie solveur (s)")

    args = ap.parse_args()
    if args.mode == "demo":
        return mode_demo(args)
    return mode_rejouer(args)


if __name__ == "__main__":
    raise SystemExit(principale())
