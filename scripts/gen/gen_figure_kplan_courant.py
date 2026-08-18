"""Figure de synthèse : k_plan identifié par courant (indépendance au courant).

Lit journaux/resultats_kplan_courant_2026-08-14.csv (produit par
scripts/tester_kplan_courant.py) et trace k_plan(I) ± σ avec la bande
horizontale de la moyenne pondérée ± IC. Illustre que k_plan effectif est
indépendant du courant (χ²/ddl ≪ 1) et vaut ≈2,5× la valeur physique de config.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "scripts"))
from _style import apply_style, OKABE_ITO, GRIS_MODELE  # noqa: E402

CSV = R / "journaux" / "resultats_kplan_courant_2026-08-14.csv"
K_CONFIG = 3.0  # valeur physique en config (materiaux.yaml)


def lire():
    I, k, s = [], [], []
    meta = {}
    for ligne in CSV.read_text().splitlines():
        if ligne.startswith("courant") or not ligne.strip():
            continue
        if ligne.startswith("#"):
            for tok in ligne[1:].split():
                key, _, val = tok.partition("=")
                meta[key] = float(val)
            continue
        a, b, c = ligne.split(",")
        I.append(float(a)); k.append(float(b)); s.append(float(c))
    return np.array(I), np.array(k), np.array(s), meta


def main():
    apply_style(**{"font.size": 12, "legend.fontsize": 10, "savefig.pad_inches": 0.03})
    I, k, s, meta = lire()
    k_moy, sig_moy = meta["k_moy"], meta["sig_moy"]
    chi2, ddl = meta["chi2"], meta["ddl"]

    fig, ax = plt.subplots(figsize=(6.4, 4.2))

    # bande = moyenne pondérée ± IC
    ax.axhspan(k_moy - sig_moy, k_moy + sig_moy, color=GRIS_MODELE, alpha=0.18, zorder=0)
    ax.axhline(k_moy, color=GRIS_MODELE, lw=1.6, zorder=1,
               label=f"moyenne = {k_moy:.1f}".replace(".", ","))

    # valeur physique de config
    ax.axhline(K_CONFIG, color=OKABE_ITO["vermillon"], lw=1.6, ls="--", zorder=1,
               label=f"valeur du modèle = {K_CONFIG:.0f},0")

    # points par courant
    ax.errorbar(I, k, yerr=s, fmt="o", ms=7, color=OKABE_ITO["bleu"],
                ecolor=OKABE_ITO["bleu"], elinewidth=1.5, capsize=4, zorder=3,
                label="mesuré (un point par essai)")

    ax.set_title("Étalement latéral de la chaleur, mesuré à chaque courant",
                 fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel("Courant d'induction (A)")
    ax.set_ylabel("k_plan — vitesse d'étalement latéral\n(W·m⁻¹·K⁻¹)")
    ax.set_xlim(160, 265)
    ax.set_ylim(0, 12)
    ax.set_xticks([175, 200, 226, 250])

    # message en clair, dans une zone vide (bas droite)
    ax.text(0.97, 0.06, "Points alignés → ne dépend pas du courant",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=9.5,
            style="italic",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=GRIS_MODELE, alpha=0.9))

    ax.legend(loc="upper left", framealpha=0.9, title="k_plan par essai")
    ax.grid(True, alpha=0.25)

    out_dir = R / "docs" / "modele" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "fig_kplan_courant.png"
    fig.savefig(out)
    print("saved", out)


if __name__ == "__main__":
    main()
