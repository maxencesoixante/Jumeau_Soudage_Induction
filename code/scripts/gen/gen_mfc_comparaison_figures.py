"""Figures comparatives du concentrateur — sans MFC / MFC 55 mm / MFC 31,75 mm (#55, #60, #63).

Produit le jeu de figures de l'issue prédictive : on suit la chaîne du haut vers
le bas, source -> température -> dynamique, pour quatre configurations, afin que
le MÉCANISME soit lisible et pas seulement le résultat.

CONFIGURATIONS
  1. sans MFC          — µr = 1 (courant image nul) : bobine nue.
  2. MFC 55 mm         — le concentrateur du banc, plus large que l'échantillon.
  3. MFC 31,75 mm — A  — famille « masque d'empreinte, puissance conservée » :
                         le flux manquant SE RECONCENTRE sous le bloc plus petit.
  4. MFC 31,75 mm — B  — famille « image tronquée » : le flux ne se reconcentre
                         pas, il retombe au cas sans MFC hors du bloc.
     (variante "source" retenue pour les figures ; "observation" en donne un
     tracé quasi superposé, cf. prediction_mfc_familles.md)

Le contraste entre 3 et 4 n'est pas une affaire de finesse de modèle mais une
HYPOTHÈSE PHYSIQUE distincte sur le devenir du flux — c'est ce que les figures
doivent rendre visible.

CONDITION : exp7_200A (200 A, 18 s, spot fixe x = 60 mm), modèle 2D, θ* = 6,0123
— la condition que la campagne #55 mesurera, avec ses 5 TC à y = 0/10/20/30/40 mm.

CONVENTION D'AXE : températures en °C BRUTS partout, jamais de ΔT ni de profil
normalisé (règle du projet).

Sorties (biblio/modele/figures/) :
  fig_mfc_cmp_1_puissance.png   densité de puissance déposée, en largeur -> la CAUSE
  fig_mfc_cmp_2_profils.png     T(y) d'interface au pic + les 5 TC -> l'EFFET
  fig_mfc_cmp_3_cartes.png      cartes T(x,y) d'interface, 4 panneaux
  fig_mfc_cmp_4_cycles.png      T(t) au chant et au centre -> la DYNAMIQUE
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jumeau.materiaux import Config                                   # noqa: E402
from jumeau.procede import Essai                                      # noqa: E402
from _style import apply_style, savefig, OKABE_ITO                    # noqa: E402

apply_style(**{"font.size": 10.5, "axes.labelsize": 11, "axes.titlesize": 11})

ESSAI = R / "code" / "config" / "essais" / "exp7_200A.yaml"
FIGS = R / "biblio" / "modele" / "figures"
FACTEUR = 6.0123
X_SPOT = 0.060
T_FUSION = 337.0

CONFIGS = [
    ("sans MFC",            OKABE_ITO["noir"],      "-"),
    ("MFC 55 mm (banc)",    OKABE_ITO["bleu"],      "-"),
    ("MFC 31,75 mm — A",    OKABE_ITO["vermillon"], "-"),
    ("MFC 31,75 mm — B",    OKABE_ITO["vert"],      "-"),
]


def construire():
    """Les quatre Essai, dans l'ordre de CONFIGS."""
    labo = Config.charger(R / "code" / "config")
    sans = copy.deepcopy(labo)
    sans.geometrie["cfc"]["mu_r"] = 1.0            # eta = 0 -> image nulle
    reduit = copy.deepcopy(labo)
    reduit.geometrie["cfc"]["longueur"] = 0.03175
    kw = dict(facteur_couplage=FACTEUR, decalage_x=0.0, racine=R)
    return [
        Essai(sans, ESSAI, **kw),
        Essai(labo, ESSAI, **kw),
        Essai(reduit, ESSAI, masque_source_mfc=True, masque_source_mode="conserver", **kw),
        Essai(reduit, ESSAI, image_mfc_finie=True, mode_troncature_image="source", **kw),
    ]


def main() -> None:
    FIGS.mkdir(parents=True, exist_ok=True)
    essais = construire()
    y_tc = np.array([0.0, 10.0, 20.0, 30.0, 40.0])

    resultats = []
    for e in essais:
        sv, sol = e.simuler(modele="2D")
        champs = np.array([sv.resultat_2d(sol, i) for i in range(sol.t.size)])
        Tmax = champs.max(axis=0)                                   # (nx, ny)
        ix = int(np.argmin(np.abs(e.grille.x - X_SPOT)))
        resultats.append(dict(
            grille=e.grille, Tmax=Tmax, profil=Tmax[ix, :],
            P2d=e._P_spots_2d[0], t=sol.t, series=e.series_tc(sv, sol)))

    y_mm = resultats[0]["grille"].y * 1e3
    x_mm = resultats[0]["grille"].x * 1e3

    # --- 1. densité de puissance déposée, en largeur (la CAUSE) --------------
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    ix = int(np.argmin(np.abs(resultats[0]["grille"].x - X_SPOT)))
    for (nom, col, ls), r in zip(CONFIGS, resultats):
        ax.plot(y_mm, r["P2d"][ix, :] * 1e-3, color=col, ls=ls, lw=2.0, label=nom)
    ax.axvspan(20 - 15.875, 20 + 15.875, color=OKABE_ITO["vert"], alpha=0.07, lw=0)
    # L'étiquette posée en bas traversait les quatre courbes : au centre, la
    # colonne x=20 est vide entre les courbes (~0) et la légende (en haut).
    ax.annotate("empreinte du\nMFC 31,75 mm", xy=(20, ax.get_ylim()[1] * 0.55),
                ha="center", va="center", fontsize=9, color=OKABE_ITO["vert"])
    ax.set_xlabel("Position en largeur $y$ (mm)")
    ax.set_ylabel("Puissance déposée (kW/m²)")
    ax.set_title("Ce que le concentrateur change à la SOURCE (coupe au spot, $x$ = 60 mm)")
    ax.set_xlim(0, 40)
    ax.legend(frameon=False, fontsize=9, loc="upper center", ncol=2)
    ax.grid(alpha=0.25)
    savefig(fig, FIGS / "fig_mfc_cmp_1_puissance.png")
    plt.close(fig)

    # --- 2. profils T(y) d'interface au pic (l'EFFET) ------------------------
    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    for (nom, col, ls), r in zip(CONFIGS, resultats):
        ax.plot(y_mm, r["profil"], color=col, ls=ls, lw=2.0, label=nom)
        pics = np.interp(y_tc, y_mm, r["profil"])
        ax.plot(y_tc, pics, "o", color=col, ms=5, mec="white", mew=0.8, zorder=5)
    ax.axhline(T_FUSION, color=OKABE_ITO["rose"], ls="--", lw=1.3)
    ax.annotate(f"fusion {T_FUSION:.0f} °C", xy=(1.0, T_FUSION + 8), fontsize=9,
                color=OKABE_ITO["rose"])
    ax.set_xlabel("Position en largeur $y$ (mm)")
    ax.set_ylabel("Température d'interface au pic (°C)")
    ax.set_title("Profil en largeur prédit — 200 A, 18 s\n"
                 "points : les 5 thermocouples de la campagne #55", fontsize=10.5)
    ax.set_xlim(0, 40)
    ax.set_ylim(40, 380)
    # légende SOUS les axes : en interne elle recouvrait la courbe « sans MFC »
    ax.legend(frameon=False, fontsize=9, ncol=4, loc="upper center",
              bbox_to_anchor=(0.5, -0.16), handlelength=1.8, columnspacing=1.4)
    ax.grid(alpha=0.25)
    savefig(fig, FIGS / "fig_mfc_cmp_2_profils.png")
    plt.close(fig)

    # --- 3. cartes d'interface ----------------------------------------------
    vmax = max(r["Tmax"].max() for r in resultats)
    fig, axes = plt.subplots(1, 4, figsize=(12.6, 3.2), sharey=True)
    for ax, (nom, _, _), r in zip(axes, CONFIGS, resultats):
        im = ax.pcolormesh(x_mm, y_mm, r["Tmax"].T, cmap="inferno", vmin=20, vmax=vmax,
                           shading="auto")
        ax.contour(x_mm, y_mm, r["Tmax"].T, levels=[T_FUSION], colors="white", linewidths=1.2)
        ax.set_title(nom, fontsize=10)
        ax.set_xlabel("$x$ (mm)")
        ax.set_aspect("auto")
    axes[0].set_ylabel("$y$ (mm)")
    cb = fig.colorbar(im, ax=axes, fraction=0.020, pad=0.012)
    cb.set_label("Température d'interface au pic (°C)")
    # Le rendu a montré qu'AUCUN contour de fusion n'apparaît : à 200 A aucune
    # configuration n'y arrive. Annoncer un élément de légende absent trompe ;
    # le fait lui-même est le résultat, on l'écrit.
    atteint = [n for (n, _, _), r in zip(CONFIGS, resultats) if r["Tmax"].max() >= T_FUSION]
    mention = (f"contour blanc = fusion ({', '.join(atteint)})" if atteint
               else f"à 200 A, AUCUNE configuration n'atteint la fusion ({T_FUSION:.0f} °C)")
    fig.suptitle(f"Empreinte thermique à l'interface au pic — {mention}", y=1.02)
    savefig(fig, FIGS / "fig_mfc_cmp_3_cartes.png")
    plt.close(fig)

    # --- 4. dynamique au chant et au centre ---------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.0), sharey=True)
    for ax, tc, titre in zip(axes, ("TC1", "TC3"),
                             ("Au chant ($y$ = 0 mm)", "Au centre ($y$ = 20 mm)")):
        for (nom, col, ls), r in zip(CONFIGS, resultats):
            ax.plot(r["t"], r["series"][tc], color=col, ls=ls, lw=2.0, label=nom)
        ax.axhline(T_FUSION, color=OKABE_ITO["rose"], ls="--", lw=1.2)
        ax.axvspan(0, 18, color="0.85", alpha=0.5, lw=0)
        ax.set_title(titre)
        ax.set_xlabel("Temps (s)")
        ax.set_xlim(0, 60)
        ax.grid(alpha=0.25)
    axes[0].set_ylabel("Température d'interface (°C)")
    axes[0].annotate("chauffe", xy=(9, 34), ha="center", fontsize=9, color="0.35")
    # plafond relevé : à ylim=350 l'étiquette était coupée en deux par la ligne
    axes[0].set_ylim(top=400)
    axes[0].annotate(f"fusion {T_FUSION:.0f} °C", xy=(38, T_FUSION + 14), fontsize=9,
                     color=OKABE_ITO["rose"])
    # LE discriminant que la figure a révélé : sous la famille A le chant est hors
    # empreinte, il ne chauffe que par conduction latérale et culmine APRÈS la
    # coupure. Un décalage temporel ne dépend ni de θ*, ni du niveau absolu.
    axes[0].annotate("A : pic ~7 s APRÈS la coupure\n(le chant ne chauffe que\npar conduction)",
                     xy=(25.5, 176), xytext=(34, 250), fontsize=8.5,
                     color=OKABE_ITO["vermillon"], ha="left",
                     arrowprops=dict(arrowstyle="->", color=OKABE_ITO["vermillon"], lw=1.1))
    # légende sous les deux panneaux, comme la figure des profils
    axes[0].legend(frameon=False, fontsize=9, ncol=4, loc="upper center",
                   bbox_to_anchor=(1.03, -0.18), handlelength=1.8, columnspacing=1.4)
    fig.suptitle("Dynamique prédite — chauffe 18 s puis refroidissement", y=1.0)
    savefig(fig, FIGS / "fig_mfc_cmp_4_cycles.png")
    plt.close(fig)

    # Le rendu a montré que le maximum de la famille A n'est PAS au chant : un
    # ratio « bord/centre » y mesure autre chose que ce que son nom annonce.
    # On imprime donc AUSSI le pic réel du profil et sa position.
    for (nom, _, _), r in zip(CONFIGS, resultats):
        p = np.interp(y_tc, y_mm, r["profil"])
        i_pic = int(np.argmax(r["profil"]))
        print(f"{nom:22s} " + "  ".join(f"{v:6.1f}" for v in p)
              + f"   bord/centre {max(p[0], p[-1]) / p[2]:.2f}"
              + f"   pic {r['profil'][i_pic]:6.1f} °C a y={y_mm[i_pic]:5.1f} mm"
              + f"   pic/centre {r['profil'][i_pic] / p[2]:.2f}")
    print("figures ecrites dans", FIGS)


if __name__ == "__main__":
    main()
