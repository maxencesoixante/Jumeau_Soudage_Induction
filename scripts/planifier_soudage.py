#!/usr/bin/env python3
"""Planificateur de soudage uniforme — génère un plan de passes couvrant toute
l'interface >= fusion sans dégradation, puis vérifie et trace la couverture.

Modèle 2D calibré (θ* figé, aucune recalibration). Sortie :
  - resultats/plan_soudage.yaml
  - docs/modele/figures/fig_plan_soudage_couverture.png
"""
import sys
from pathlib import Path

import numpy as np
import yaml
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / "src"))
sys.path.insert(0, str(R / "scripts"))
from _style import apply_style  # noqa: E402
apply_style(**{"font.size": 11, "axes.labelsize": 12, "savefig.pad_inches": 0.06})
from jumeau.materiaux import Config  # noqa: E402
from jumeau.planification.empreinte import bibliotheque  # noqa: E402
from jumeau.planification.planificateur import planifier, metriques, verifier_sequentiel  # noqa: E402

FUSION, DEGRAD = 337.0, 450.0

# Grille de candidats : positions en x (le long de la longueur) × y (en largeur)
# × courants (dans [150, 250]). Durée de passe fixe.
# Durées/courants choisis pour ATTEINDRE la fusion au point chaud (d'après les
# prédictions : ~20 s à 200-235 A ; 12 s ne soudait rien) tout en restant dans
# la fenêtre validée [150, 250] A.
X_CS = [0.030, 0.060, 0.090, 0.110]
Y_CS = [0.000, 0.010, 0.020, 0.030, 0.040]
COURANTS = [200.0, 235.0]
# Largeurs de MFC physiques (#39) : labo 55 mm (None) et réduit commandé 31,75 mm.
MFC_LONGUEURS = [None, 0.03175]
DUREE = 20.0


def main():
    cfg = Config.charger(R / "config")
    n_cand = len(X_CS) * len(Y_CS) * len(COURANTS) * len(MFC_LONGUEURS)
    print(f"Construction de la bibliothèque d'empreintes "
          f"({len(X_CS)}×{len(Y_CS)}×{len(COURANTS)}×{len(MFC_LONGUEURS)} = "
          f"{n_cand} passes candidates)…")
    grille, lib = bibliotheque(cfg, X_CS, Y_CS, COURANTS, DUREE,
                               mfc_longueurs=MFC_LONGUEURS)
    passes, Tc, m = planifier(lib, fusion=FUSION, degrad=DEGRAD)

    print(f"\nPlan glouton : {len(passes)} passe(s) — soudé {m['pct_soude']:.1f} %, "
          f"non soudé {m['pct_non_soude']:.1f} %, dégradé {m['pct_degrade']:.1f} %")
    passes_params = [{"x_c": k[0], "y_c": k[1], "courant": k[2],
                      "mfc_longueur": k[3], "duree": DUREE} for k in passes]
    for i, p in enumerate(passes_params, 1):
        mfc = "55" if p["mfc_longueur"] is None else f"{p['mfc_longueur']*1e3:.1f}"
        print(f"  {i}. x={p['x_c']*1e3:5.0f} mm  y={p['y_c']*1e3:4.0f} mm  "
              f"I={p['courant']:.0f} A  MFC={mfc} mm  t={p['duree']:.0f} s")

    (R / "resultats").mkdir(exist_ok=True)
    with open(R / "resultats" / "plan_soudage.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump({"passes": passes_params, "couverture_gloutonne": m,
                        "fusion": FUSION, "degradation": DEGRAD},
                       f, allow_unicode=True, sort_keys=False)

    if passes_params:
        print("\nVérification séquentielle (chaleur résiduelle incluse)…")
        _, T_seq = verifier_sequentiel(cfg, passes_params)
        m_seq = metriques(T_seq, fusion=FUSION, degrad=DEGRAD)
        print(f"  séquentiel : soudé {m_seq['pct_soude']:.1f} %, "
              f"non soudé {m_seq['pct_non_soude']:.1f} %, dégradé {m_seq['pct_degrade']:.1f} %")
    else:
        # aucune passe ne soude sans dégrader → carte = état gloutonne (ambiant)
        T_seq, m_seq = Tc, m
        print("\nAucune passe candidate ne soude sans dégrader → couverture 0 %.")
    uniforme = m_seq["pct_soude"] >= 99.9 and m_seq["pct_degrade"] == 0.0
    utilise_mfc_reduit = any(p["mfc_longueur"] is not None for p in passes_params)
    print(f"\nVERDICT — soudage uniforme : {'OUI' if uniforme else 'NON'}")
    if not uniforme:
        print("  Seules de fines bandes de bord (lobes du M) se soudent sans dégrader.")
        if not utilise_mfc_reduit:
            print("  Le MFC réduit (31,75 mm, masque 1er ordre) n'a PAS été retenu : il coupe "
                  "les lobes de bord sans réchauffer le centre (creux du M) -> n'améliore pas "
                  "la couverture. Un MFC vraiment localisant (non capturé par le masque dur) "
                  "serait nécessaire. Cf. spec §Risque de faisabilité + issue #39.")

    _tracer(grille, T_seq, passes_params, m_seq)


def _tracer(grille, Tmax, passes_params, m):
    X, Y = np.meshgrid(grille.x * 1e3, grille.y * 1e3, indexing="ij")
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    cmap = ListedColormap(["#D9E8F5", "#B7E4C7", "#F4C7C3"])  # bleu / vert / rouge
    norm = BoundaryNorm([-1e9, FUSION, DEGRAD, 1e9], cmap.N)
    ax.pcolormesh(X, Y, Tmax, cmap=cmap, norm=norm, shading="auto")
    cs = ax.contour(X, Y, Tmax, levels=[FUSION, DEGRAD],
                    colors=["#0072B2", "#C1272D"], linewidths=[1.3, 1.6])
    ax.clabel(cs, fmt={FUSION: "337", DEGRAD: "450"}, fontsize=7)
    for i, p in enumerate(passes_params, 1):
        reduit = p["mfc_longueur"] is not None
        ax.plot(p["x_c"] * 1e3, p["y_c"] * 1e3, "ko" if reduit else "kx",
                ms=7, mew=1.8, mfc="none" if reduit else "k")
        etiq = f"{i}R" if reduit else str(i)   # R = MFC réduit
        ax.annotate(etiq, (p["x_c"] * 1e3, p["y_c"] * 1e3), fontsize=7,
                    ha="left", va="bottom", xytext=(2, 2), textcoords="offset points")
    ax.set_xlabel("Longueur $x$ (mm)")
    ax.set_ylabel("Largeur $y$ (mm)")
    ax.set_title(f"Plan de soudage — couverture (bleu < fusion · vert soudé · rouge dégradé)\n"
                 f"soudé {m['pct_soude']:.0f} %  ·  non soudé {m['pct_non_soude']:.0f} %  ·  "
                 f"dégradé {m['pct_degrade']:.0f} %", fontsize=10.5)
    ax.set_aspect("equal")
    out = R / "docs" / "modele" / "figures" / "fig_plan_soudage_couverture.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    print("saved", out)


if __name__ == "__main__":
    main()
