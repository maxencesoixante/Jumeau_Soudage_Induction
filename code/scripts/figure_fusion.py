#!/usr/bin/env python
"""Figure façon Lionetto et al. 2017 (Fig. 5) — évolution de la température et
du degré de fusion à l'interface de soudure.

Panneau haut : T simulée à l'interface et en surface (côté bobine) au point de
contrôle + mesures thermocouples correspondantes (cercles). Panneau bas :
degré de fusion Xm(t) simulé et déduit de la mesure, avec le « temps à l'état
fondu » (Xm ≥ 0,99) marqué par des pointillés — l'analogue direct de la Fig. 5.

Xm est le degré de fusion quasi-statique du modèle (CDF du pic gaussien de
fusion du cp apparent, cf. Materiau.degre_de_fusion). La cinétique de
cristallisation (Ozawa chez Lionetto) n'est pas modélisée : sur le
refroidissement, Xm redescend à l'équilibre — le temps à l'état fondu simulé
est donc une estimation par équilibre local.

Usage :
    python scripts/figure_fusion.py [config/essais/chauffe_250A_3TC.yaml] \
        --facteur 3.849 --h-contact 5.0 --h-bas 45.87 \
        [--tc-interface TC2 --tc-surface TC1] [--x 0.060 --y 0.020]
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


def fenetre_fondue(t: np.ndarray, Xm: np.ndarray, seuil: float = 0.99):
    """(t_debut, t_fin) de la plus longue fenêtre continue où Xm >= seuil."""
    au_dessus = Xm >= seuil
    if not au_dessus.any():
        return None
    bords = np.diff(au_dessus.astype(int))
    debuts = list(np.where(bords == 1)[0] + 1)
    fins = list(np.where(bords == -1)[0] + 1)
    if au_dessus[0]:
        debuts.insert(0, 0)
    if au_dessus[-1]:
        fins.append(len(t) - 1)
    i_max = int(np.argmax([t[f] - t[d] for d, f in zip(debuts, fins)]))
    return float(t[debuts[i_max]]), float(t[fins[i_max]])


def principale():
    ap = argparse.ArgumentParser()
    ap.add_argument("essai", nargs="?", default="config/essais/chauffe_250A_3TC.yaml")
    ap.add_argument("--modele", choices=["2D", "3D"], default="2D",
                    help="2D lumpé à l'interface (défaut, cohérent avec la "
                         "validation) ou 3D avec gradient d'épaisseur ; en 2D la "
                         "courbe de surface n'a pas de sens (une maille en z) et "
                         "n'est pas tracée")
    ap.add_argument("--facteur", type=float, default=1.0)
    ap.add_argument("--decalage-x", type=float, default=0.0,
                    help="décalage bobine<->montage le long de x (m), calibré")
    ap.add_argument("--h-contact", type=float, default=None, help="(modèle 3D)")
    ap.add_argument("--h-bas", type=float, default=None, help="(modèle 3D)")
    ap.add_argument("--h-haut", type=float, default=None, help="(modèle 2D)")
    ap.add_argument("--h-bas-2d", type=float, default=None, help="(modèle 2D)")
    ap.add_argument("--h-bord-x0", type=float, default=None,
                    help="(modèle 2D) puits de bord au chant x=0, W/m².K")
    ap.add_argument("--x", type=float, default=None, help="x du point de contrôle (m)")
    ap.add_argument("--y", type=float, default=None, help="y du point de contrôle (m)")
    ap.add_argument("--tc-interface", default="TC2", help="voie mesurée à l'interface")
    ap.add_argument("--tc-surface", default="TC1", help="voie mesurée en surface (modèle 3D)")
    ap.add_argument("--nx", type=int, default=61)
    ap.add_argument("--ny", type=int, default=21)
    ap.add_argument("--nz", type=int, default=15)
    ap.add_argument("--sortie", default="resultats")
    args = ap.parse_args()

    cfg = Config.charger(RACINE / "code" / "config")
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
    mat = cfg.materiau

    essai = Essai(cfg, args.essai, nx=args.nx, ny=args.ny, nz=args.nz,
                  facteur_couplage=args.facteur, decalage_x=args.decalage_x,
                  racine=RACINE)
    nom = essai.spec["nom"]
    # point de contrôle : par défaut la position du TC interface de l'essai
    tc_pos = essai.spec.get("thermocouples", {}).get(args.tc_interface, {})
    x_pt = args.x if args.x is not None else float(tc_pos.get("x", 0.060))
    y_pt = args.y if args.y is not None else float(tc_pos.get("y", 0.020))

    print(f"Simulation {nom} [{args.modele}] — point de contrôle "
          f"({x_pt * 1e3:.1f}, {y_pt * 1e3:.1f}) mm, facteur={args.facteur}")
    solveur, sol = essai.simuler(modele=args.modele)
    T_interface = solveur.serie_temporelle(sol, x_pt, y_pt, "interface")
    # la surface (gradient d'épaisseur) n'existe qu'en 3D ; en 2D lumpé, une
    # seule maille en z = l'interface, la courbe de surface n'a pas de sens.
    T_surface = (solveur.serie_temporelle(sol, x_pt, y_pt, "surface")
                 if args.modele == "3D" else None)

    Xm_sim = mat.degre_de_fusion(T_interface)
    fen_sim = fenetre_fondue(sol.t, Xm_sim)

    # mesures
    df = None
    try:
        df = recaler_a_la_chauffe(charger_mesures(essai.fichier_mesures))
        tcol = df.columns[0]
        duree = float(essai.spec.get("duree_totale", essai.spec["duree_chauffe"]))
        df = df[df[tcol] <= duree].reset_index(drop=True)
    except FileNotFoundError:
        print("(mesures introuvables — tracé simulation seule)")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 8), sharex=True,
                                   height_ratios=[1.25, 1.0], constrained_layout=True)

    # --- panneau haut : températures
    if df is not None:
        pas = max(len(df) // 120, 1)
        for tc, coul, etiquette in ((args.tc_interface, "black", "interface"),
                                    (args.tc_surface, "gray", "surface")):
            col = next((c for c in df.columns if c.startswith(tc)), None)
            if col:
                ax1.scatter(df[tcol][::pas], df[col][::pas], s=14,
                            facecolors="none", edgecolors=coul,
                            label=f"Mesure {etiquette} ({tc})")
    ax1.plot(sol.t, T_interface, "k-", lw=2, label="Simulation — interface")
    if T_surface is not None:
        ax1.plot(sol.t, T_surface, "k-.", lw=1.6, label="Simulation — surface (côté bobine)")
    ax1.axhline(mat.T_fusion, color="tab:blue", ls=":", lw=1.2)
    ax1.text(0.99, mat.T_fusion + 6, f"Tf = {mat.T_fusion:.0f} °C", color="tab:blue",
             fontsize=9, ha="right", transform=ax1.get_yaxis_transform())
    ax1.set_ylabel("Température (°C)")
    ax1.legend(fontsize=9)
    ax1.grid(alpha=0.25)

    # --- panneau bas : degré de fusion
    ax2.plot(sol.t, Xm_sim, "k-", lw=2, label="Degré de fusion — simulation")
    if df is not None:
        col = next((c for c in df.columns if c.startswith(args.tc_interface)), None)
        if col:
            Xm_mes = mat.degre_de_fusion(df[col].values)
            ax2.plot(df[tcol], Xm_mes, color="tab:red", ls="--", lw=1.6,
                     label=f"Degré de fusion — déduit de la mesure ({args.tc_interface})")
            fen_mes = fenetre_fondue(df[tcol].values, Xm_mes)
        else:
            fen_mes = None
    else:
        fen_mes = None

    for fen, coul, dy in ((fen_sim, "black", 0.60), (fen_mes, "tab:red", 0.44)):
        if fen is None:
            continue
        t0, t1 = fen
        ax2.axvline(t0, color=coul, ls="--", lw=1.1)
        ax2.axvline(t1, color=coul, ls="--", lw=1.1)
        ax2.annotate("", xy=(t1, dy), xytext=(t0, dy),
                     arrowprops=dict(arrowstyle="<->", color=coul, lw=1.2))
        ax2.text(0.5 * (t0 + t1), dy + 0.045,
                 f"état fondu : {t1 - t0:.0f} s", color=coul,
                 fontsize=9, ha="center")
        ax1.axvline(t0, color=coul, ls="--", lw=0.9, alpha=0.6)
        ax1.axvline(t1, color=coul, ls="--", lw=0.9, alpha=0.6)

    ax2.set_xlabel("Temps (s)")
    ax2.set_ylabel("Degré de fusion X$_m$ (−)")
    ax2.set_ylim(-0.03, 1.08)
    ax2.legend(fontsize=9, loc="upper right")
    ax2.grid(alpha=0.25)

    consigne = essai.spec.get("consigne_interface")
    fig.suptitle(f"{nom} — température et degré de fusion à l'interface "
                 f"(I = {essai.spec['courant']:.0f} A"
                 + (f", coupure à {consigne:.0f} °C" if consigne else "")
                 + ")", fontsize=11)

    dossier = RACINE / args.sortie
    dossier.mkdir(exist_ok=True)
    chemin = dossier / f"{nom}_fusion_fig5.png"
    fig.savefig(chemin, dpi=150)
    print(f"Figure écrite : {chemin}")
    if fen_sim:
        print(f"  état fondu simulé  : {fen_sim[1] - fen_sim[0]:5.0f} s "
              f"({fen_sim[0]:.0f} → {fen_sim[1]:.0f} s)")
    if fen_mes:
        print(f"  état fondu mesuré  : {fen_mes[1] - fen_mes[0]:5.0f} s "
              f"({fen_mes[0]:.0f} → {fen_mes[1]:.0f} s)")


if __name__ == "__main__":
    principale()
