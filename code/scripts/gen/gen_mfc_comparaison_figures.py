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
  fig_mfc_cmp_3{a,b,c,d}_*.png  cartes T(x,y) d'interface, UNE PAR CONFIGURATION
                                (echelle de couleur commune aux quatre)
  fig_mfc_cmp_4_cycles.png      T(t) au chant et au centre -> la DYNAMIQUE
  fig_mfc_cmp_5{a,b,c,d}_*.png  cartes de puissance Joule, UNE PAR CONFIGURATION
  fig_mfc_cmp_6_joule_epaisseur.png  Q(z) dans l'epaisseur -> ou la puissance se depose
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

# Cotes du bloc : longueur selon y (largeur de l'echantillon), largeur selon x.
# A et B designent deux MODELES du meme bloc physique 31,75 mm, pas deux blocs.
CONFIGS = [
    ("Sans MFC",                            OKABE_ITO["noir"],      "-"),
    ("Avec MFC (55 × 31,5 mm)",             OKABE_ITO["bleu"],      "-"),
    ("Avec MFC (31,75 × 31,5 mm) — A",      OKABE_ITO["vermillon"], "-"),
    ("Avec MFC (31,75 × 31,5 mm) — B",      OKABE_ITO["vert"],      "-"),
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
            P2d=e._P_spots_2d[0], Q3d=e._Q_spots[0],
            t=sol.t, series=e.series_tc(sv, sol)))

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
    ax.set_title("Puissance déposée en largeur ($x$ = 60 mm)")
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
    ax.set_title("Profil en largeur — 200 A, 18 s")
    ax.set_xlim(0, 40)
    ax.set_ylim(40, 380)
    # légende SOUS les axes : en interne elle recouvrait la courbe « sans MFC »
    ax.legend(frameon=False, fontsize=9, ncol=4, loc="upper center",
              bbox_to_anchor=(0.5, -0.16), handlelength=1.8, columnspacing=1.4)
    ax.grid(alpha=0.25)
    savefig(fig, FIGS / "fig_mfc_cmp_2_profils.png")
    plt.close(fig)

    # --- 3. cartes d'interface — UNE IMAGE PAR CONFIGURATION -----------------
    # Fichiers separes plutot qu'une grille : chacun se lit en pleine largeur,
    # et peut etre repris seul (issue, slide) sans recadrage. L'ECHELLE DE
    # COULEUR EST COMMUNE aux quatre — sinon les cartes ne seraient plus
    # comparables entre elles, ce qui est tout l'objet de la serie.
    vmax = max(r["Tmax"].max() for r in resultats)
    noms_fichiers = ["fig_mfc_cmp_3a_sans_mfc.png", "fig_mfc_cmp_3b_mfc_55.png",
                     "fig_mfc_cmp_3c_reduit_A.png", "fig_mfc_cmp_3d_reduit_B.png"]
    for (nom, _, _), r, fichier in zip(CONFIGS, resultats, noms_fichiers):
        fig, ax = plt.subplots(figsize=(7.8, 2.9))
        im = ax.pcolormesh(x_mm, y_mm, r["Tmax"].T, cmap="inferno", vmin=20, vmax=vmax,
                           shading="auto")
        ax.contour(x_mm, y_mm, r["Tmax"].T, levels=[T_FUSION], colors="white", linewidths=1.2)
        ax.set_aspect("equal")
        ax.set_xlabel("$x$ (mm)")
        ax.set_ylabel("$y$ (mm)")
        pic = r["Tmax"].max()
        ax.set_title(f"{nom} — pic {pic:.0f} °C", fontsize=10.5, pad=6)
        cb = fig.colorbar(im, ax=ax, fraction=0.030, pad=0.015)
        cb.set_label("T interface au pic (°C)", fontsize=9)
        cb.ax.tick_params(labelsize=8)
        savefig(fig, FIGS / fichier)
        plt.close(fig)
        print(f"  {fichier:32s} pic {pic:6.1f} °C   (echelle commune 20-{vmax:.0f} °C)")

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
    axes[0].annotate("A : pic après la coupure",
                     xy=(25.5, 176), xytext=(33, 262), fontsize=9,
                     color=OKABE_ITO["vermillon"], ha="left",
                     arrowprops=dict(arrowstyle="->", color=OKABE_ITO["vermillon"], lw=1.1))
    # légende sous les deux panneaux, comme la figure des profils
    axes[0].legend(frameon=False, fontsize=9, ncol=4, loc="upper center",
                   bbox_to_anchor=(1.03, -0.18), handlelength=1.8, columnspacing=1.4)
    fig.suptitle("Chauffe 18 s puis refroidissement", y=1.0)
    savefig(fig, FIGS / "fig_mfc_cmp_4_cycles.png")
    plt.close(fig)

    # Le rendu a montré que le maximum de la famille A n'est PAS au chant : un
    # ratio « bord/centre » y mesure autre chose que ce que son nom annonce.
    # On imprime donc AUSSI le pic réel du profil et sa position.
    # --- 5. cartes de puissance Joule — UNE IMAGE PAR CONFIGURATION ---------
    # Meme parti que les cartes de temperature : un fichier par configuration,
    # echelle de couleur COMMUNE pour qu'elles restent comparables.
    pmax = max(r["P2d"].max() for r in resultats) * 1e-3
    fichiers_q = ["fig_mfc_cmp_5a_sans_mfc.png", "fig_mfc_cmp_5b_mfc_55.png",
                  "fig_mfc_cmp_5c_reduit_A.png", "fig_mfc_cmp_5d_reduit_B.png"]
    for (nom, _, _), r, fichier in zip(CONFIGS, resultats, fichiers_q):
        fig, ax = plt.subplots(figsize=(7.8, 2.9))
        im = ax.pcolormesh(x_mm, y_mm, r["P2d"].T * 1e-3, cmap="viridis",
                           vmin=0, vmax=pmax, shading="auto")
        ax.set_aspect("equal")
        ax.set_xlabel("$x$ (mm)")
        ax.set_ylabel("$y$ (mm)")
        ax.set_title(f"{nom} — max {r['P2d'].max() * 1e-3:.0f} kW/m²",
                     fontsize=10.5, pad=6)
        cb = fig.colorbar(im, ax=ax, fraction=0.030, pad=0.015)
        cb.set_label("Puissance déposée (kW/m²)", fontsize=9)
        cb.ax.tick_params(labelsize=8)
        savefig(fig, FIGS / fichier)
        plt.close(fig)
        print(f"  {fichier:32s} max {r['P2d'].max() * 1e-3:6.1f} kW/m2")

    # --- 6. répartition de la puissance Joule DANS L'ÉPAISSEUR ---------------
    # ATTENTION, défaut attrapé par la boucle de revue : au CENTRE exact de la
    # largeur (y = 20 mm = largeur/2), la puissance déposée est nulle A LA
    # PRÉCISION MACHINE (~4e-28 kW/m² contre 4,3e+02 au chant) — c'est une ligne
    # nodale de la dissipation, pas une petite valeur. Tracer ce point sur une
    # échelle log affichait du bruit de virgule flottante sous la forme d'une
    # structure crédible. Le 2e panneau prend donc y = 5 mm, sous l'empreinte du
    # MFC réduit, où les quatre configurations existent réellement.
    z_mm = resultats[0]["grille"].z * 1e3
    z_interface = 3.36                       # mm — epaisseur_sup du laminé
    iy_bord = 0
    iy_lobe = int(np.argmin(np.abs(y_mm - 5.0)))
    p_centre = resultats[1]["P2d"][ix, int(np.argmin(np.abs(y_mm - 20.0)))] * 1e-3
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.8), sharey=True)
    for ax, iy, titre in zip(axes, (iy_bord, iy_lobe),
                             ("Au chant ($y$ = 0 mm)",
                              "Sous l'empreinte réduite ($y$ = 5 mm)")):
        for (nom, col, ls), r in zip(CONFIGS, resultats):
            q = r["Q3d"][ix, iy, :] * 1e-6                      # W/m3 -> MW/m3
            if q.max() <= 0:
                continue                                        # A hors empreinte
            ax.plot(q, z_mm, color=col, ls=ls, lw=2.0, marker="o", ms=3, label=nom)
        ax.axhline(z_interface, color=OKABE_ITO["rose"], ls="--", lw=1.3)
        ax.set_xscale("log")
        ax.set_xlabel("Puissance Joule volumique (MW/m³)")
        ax.set_title(titre, fontsize=10.5)
        ax.grid(alpha=0.25, which="both")
    axes[0].set_ylabel("Profondeur $z$ (mm)   —   0 = côté bobine")
    axes[0].invert_yaxis()
    # annotations posées À DROITE des courbes, qui montent vers la gauche
    axes[1].annotate("interface (twill)",
                     xy=(axes[1].get_xlim()[1] * 0.30, z_interface + 0.75),
                     fontsize=8.5, color=OKABE_ITO["rose"], va="top", ha="right")
    axes[0].annotate("A : puissance nulle ici", xy=(axes[0].get_xlim()[1] * 0.45, 6.4),
                     fontsize=9, color=OKABE_ITO["vermillon"], ha="right")
    # légende construite sur le panneau DROIT : le gauche omet la config A
    # (puissance nulle au chant), la légende y aurait montré 3 courbes sur 4.
    axes[1].legend(frameon=False, fontsize=9, ncol=4, loc="upper center",
                   bbox_to_anchor=(-0.05, -0.17), handlelength=1.8, columnspacing=1.4)
    fig.suptitle("Puissance Joule dans l'épaisseur", y=1.0)
    savefig(fig, FIGS / "fig_mfc_cmp_6_joule_epaisseur.png")
    plt.close(fig)

    for (nom, _, _), r in zip(CONFIGS, resultats):
        q = r["Q3d"][ix, iy_bord, :] * 1e-6
        if q.max() > 0:
            k = int(np.argmax(q))
            print(f"{nom:22s} Q max epaisseur {q[k]:8.1f} MW/m3 a z={z_mm[k]:.2f} mm"
                  f"  (surface {q[0]:7.1f}, fond {q[-1]:6.1f})")
        else:
            print(f"{nom:22s} Q nulle au chant (hors empreinte)")

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
