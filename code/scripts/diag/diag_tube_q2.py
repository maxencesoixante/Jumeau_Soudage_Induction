#!/usr/bin/env python
"""Issue #73, question Q2 (et enjeu de Q1) — la face intérieure du tube substitut.

Le tube substitut remplace le laminé inférieur de 3,36 mm posé sur le bâti par une
paroi de 1,68 mm au-dessus d'une cavité d'air fermée. Question : la face
intérieure est-elle plus chaude ou plus froide que la face opposée à plat, et
combien de temps passe-t-elle au-dessus de Tg (159 °C), sous pression et sans
contre-pression (enjeu de Q1) ?

Modèle 3D, deux représentations de l'épaisseur (#74) :
  - « ralenti » : k_z du laminé inférieur réduit à 0,10 + h_contact 40 — la seule
    qui tient le gradient d'épaisseur mesuré au niveau réel ;
  - « actuel »  : k_z uniforme, h_contact 5 — pour montrer ce qui dépend du modèle.
Géométries : à plat (laminé inférieur 3,36 mm, h_bas 15) et tube (paroi 1,68 mm,
h_bas de la cavité 2, 5 ou 10 W/(m²·K) : la perte d'une cavité d'air fermée n'est
pas connue, on l'encadre).

Deux protocoles :
  1. spot fixe de la campagne à 3 TC (essai 201 A), niveau recalé sur le pic
     d'interface mesuré au point des 3 TC (facteurs 10,4 / 11,6, cf. #74) ;
  2. cycle semi-statique à 4 spots (spécification de l'essai A-1, coupure du
     modèle), facteur de compromis A/B + exp9 (4,0 / 4,5, cf. #74) ; on suit la
     face intérieure sous chaque spot, au centre de la largeur (y = 20).

Limites : le tube est représenté par sa seule paroi de dessus, sur 40 mm de large
(pas de murs, pas de largeur 50 mm) ; la cavité est une perte linéaire h_bas.
Sortie : resultats/tube_q2/*.npz (séries) et resultats/tube_q2/synthese.csv
"""
from __future__ import annotations

import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

OUT = R / "resultats" / "tube_q2"
T_G, T_F = 159.0, 337.0
MODELES = {"ralenti": dict(kz_inf=0.10, h_contact=40.0, f_spot=10.4, f_cycle=4.0),
           "actuel": dict(kz_inf=None, h_contact=5.0, f_spot=11.6, f_cycle=4.5)}
GEOMS = {"plat": (0.00336, 15.0), "tube_h2": (0.00168, 2.0),
         "tube_h5": (0.00168, 5.0), "tube_h10": (0.00168, 10.0)}
CENTRES = [0.015875, 0.045875, 0.075875, 0.105875]


def run(args):
    modele, geom, protocole = args
    from jumeau.materiaux import Config
    from jumeau.procede import Essai
    from diag_epaisseur_3d_reference import appliquer_kz_inf
    m = MODELES[modele]
    ep, hb = GEOMS[geom]
    cfg = Config.charger(R / "code" / "config")
    cfg.geometrie["laminate"]["epaisseur_inf"] = ep
    cfg.contact.h_contact = m["h_contact"]
    cfg.ambiant.h_bas = hb
    if protocole == "spot":
        e = Essai(cfg, R / "code" / "config" / "essais" / "chauffe_201A_3TC.yaml",
                  nx=31, ny=11, nz=15, facteur_couplage=m["f_spot"], racine=R)
    else:
        e = Essai(cfg, R / "code" / "config" / "essais" / "serieA_A-1.yaml",
                  nx=31, ny=11, nz=15, facteur_couplage=m["f_cycle"], racine=R)
        tcs = {}
        for k, xc in enumerate(CENTRES, start=1):
            tcs[f"I{k}"] = {"x": xc, "y": 0.0, "z": "interface"}
            tcs[f"O{k}"] = {"x": xc, "y": 0.020, "z": "opposee"}
        e.spec["thermocouples"] = tcs
    if m["kz_inf"] is not None:
        appliquer_kz_inf(cfg.materiau, e.grille, cfg.geometrie["laminate"], m["kz_inf"])
    solveur, sol = e.simuler(modele="3D")
    ser = e.series_tc(solveur, sol)
    nom = f"{protocole}_{modele}_{geom}"
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez(OUT / f"{nom}.npz", t=sol.t, **ser)
    return nom


def au_dessus(t, v, seuil):
    dt = np.diff(t, prepend=t[0])
    return float(np.sum(dt[v > seuil]))


def synthese():
    lignes = ["protocole,modele,geometrie,T_interface_max,T_face_bas_max,bas_sur_interface_au_pic,"
              "duree_bas_au_dessus_Tg_s"]
    for f in sorted(OUT.glob("*.npz")):
        d = np.load(f)
        proto, modele, geom = f.stem.split("_", 2)
        t = d["t"]
        if proto == "spot":
            i, o = d["TC2"], d["TC3"]
            k = int(np.argmax(i))
            lignes.append(f"{proto},{modele},{geom},{i.max():.0f},{o.max():.0f},{o[k] / i[k]:.2f},"
                          f"{au_dessus(t, o, T_G):.0f}")
        else:
            imax = max(d[f"I{k}"].max() for k in range(1, 5))
            omax = max(d[f"O{k}"].max() for k in range(1, 5))
            duree = max(au_dessus(t, d[f"O{k}"], T_G) for k in range(1, 5))
            lignes.append(f"{proto},{modele},{geom},{imax:.0f},{omax:.0f},,{duree:.0f}")
    (OUT / "synthese.csv").write_text("\n".join(lignes) + "\n", encoding="utf-8")
    print("\n".join(lignes))


if __name__ == "__main__":
    taches = [(m, g, p) for p in ("spot", "cycle") for m in MODELES for g in GEOMS]
    with ProcessPoolExecutor(6) as ex:
        for nom in ex.map(run, taches):
            print("fait :", nom, flush=True)
    synthese()
