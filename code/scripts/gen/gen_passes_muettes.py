"""La séquence de passes recommandée, une image par passe, SANS AUCUN TEXTE.

Figure volontairement muette : ni titre, ni axes, ni graduations, ni légende, ni
annotation. Elle sert à montrer la progression d'un coup d'œil — l'état de
l'interface après chaque passe — là où les figures commentées servent à
argumenter. Tout le chiffrage vit dans `balayage_pas_mfc_reduit.md` et
`positions_passes_pas_optimal.md`.

Configuration tracée : MFC réduit 31,75 mm sous l'**hypothèse corroborée** (image
tronquée, la famille que deux troncatures indépendantes soutiennent), 235 A, 20 s
par passe. `--pas-mm` choisit le pas — **seule variable entre deux figures**, pour
que deux séquences se comparent panneau à panneau.

Deux pas valent d'être tracés : **15 mm**, le plus couvrant qui ne dégrade rien
dans cette hypothèse, et **22,5 mm**, qui est l'optimum propre des *deux autres*
configurations (MFC labo 55 mm et MFC réduit sous l'hypothèse favorable).

Trois états, trois aplats : sous la fusion / soudé / dégradé. La dégradation est
jugée en temps × température (`jumeau.thermique.dose_degradation`), pas au pic.
Le liseré marque l'empreinte du bloc à la passe courante.

Sortie : biblio/modele/figures/fig_passes_muettes_pas<N>mm.png
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Rectangle

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))
sys.path.insert(0, str(R / "code" / "scripts"))
from _style import apply_style, savefig                              # noqa: E402
from jumeau.materiaux import Config                                   # noqa: E402
from jumeau.planification.planificateur import verifier_sequentiel    # noqa: E402
from jumeau.thermique.dose_degradation import dose                    # noqa: E402

apply_style()

FIGURES = R / "biblio" / "modele" / "figures"
FUSION = 337.0
X_PREMIER, X_DERNIER, Y_C = 0.015875, 0.105875, 0.020
MFC_REDUIT = 0.03175
COURANT, DUREE, FAMILLE = 235.0, 20.0, "image_observation"
EMPREINTE_X, EMPREINTE_Y = 31.5, 31.75          # mm — cfc.largeur / cfc.longueur

ETATS = ListedColormap(["#D9E8F5", "#B7E4C7", "#F4C7C3"])
BORNES = BoundaryNorm([-0.5, 0.5, 1.5, 2.5], ETATS.N)


def centres(pas_mm: float) -> list[float]:
    n_int = max(1, round((X_DERNIER - X_PREMIER) * 1e3 / pas_mm))
    return [X_PREMIER + k * (X_DERNIER - X_PREMIER) / n_int for k in range(n_int + 1)]


def etat(champs, temps) -> np.ndarray:
    """0 = sous la fusion, 1 = soudé, 2 = dégradé (dose > 1)."""
    pic = champs.max(axis=0)
    degrade = dose(champs, temps) > 1.0
    return np.where(degrade, 2, np.where(pic >= FUSION, 1, 0))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pas-mm", type=float, default=15.0,
                    help="pas entre centres de passe (mm ; défaut 15)")
    a = ap.parse_args()
    cfg = Config.charger(R / "code" / "config")
    cs = centres(a.pas_mm)
    pas_eff = (X_DERNIER - X_PREMIER) * 1e3 / (len(cs) - 1)
    sortie = FIGURES / f"fig_passes_muettes_pas{pas_eff:.0f}mm.png"
    etats = []
    for n in range(1, len(cs) + 1):
        passes = [{"x_c": x, "y_c": Y_C, "courant": COURANT,
                   "mfc_longueur": MFC_REDUIT, "duree": DUREE} for x in cs[:n]]
        g, _, t, champs = verifier_sequentiel(cfg, passes, famille=FAMILLE,
                                              retour_historique=True)
        etats.append((g, etat(champs, t), cs[n - 1]))
        print(f"  passe {n}/{len(cs)}", flush=True)

    sortie.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(len(etats), 1, figsize=(7.2, 1.05 * len(etats)))
    for ax, (g, e, x_courant) in zip(np.atleast_1d(axes), etats):
        x_mm, y_mm = g.x * 1e3, g.y * 1e3
        ax.pcolormesh(x_mm, y_mm, e.T, cmap=ETATS, norm=BORNES, shading="auto")
        ax.add_patch(Rectangle((x_courant * 1e3 - EMPREINTE_X / 2.0,
                                Y_C * 1e3 - EMPREINTE_Y / 2.0),
                               EMPREINTE_X, EMPREINTE_Y, facecolor="none",
                               edgecolor="0.15", lw=1.4, zorder=3))
        # limites IDENTIQUES sur tous les panneaux : l'autoscale les rendait
        # incomparables (l'empreinte qui deborde la plaque etirait l'axe).
        ax.set_xlim(-1.0, x_mm[-1] + EMPREINTE_X / 2.0 + 1.0)
        ax.set_ylim(y_mm[0] - 1.0, y_mm[-1] + 1.0)
        ax.set_aspect("equal")   # 120 x 40 mm : ne pas laisser matplotlib etirer
        ax.axis("off")           # AUCUN TEXTE : ni axes, ni graduations, ni titre
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01, hspace=0.12)
    savefig(fig, sortie)
    plt.close(fig)
    print("ecrit :", sortie)


if __name__ == "__main__":
    main()
