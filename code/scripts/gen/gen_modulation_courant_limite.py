"""Moduler le courant peut-il éviter la dégradation ET souder toute la plaque ?

L'IDÉE TESTÉE : plutôt qu'un courant constant, couper ou réduire dès qu'un point
approche le seuil de dégradation, et laisser la conduction remplir les zones
froides. Le jumeau a déjà la machinerie (`spec["consigne_interface"]`, thermostat
sigmoïde) — elle était simplement inactive dans les simulations de passes.

À NE PAS CONFONDRE avec la loi `thermostat_capteurs`, rejetée définitivement le
2026-08-03 : celle-là portait sur QUELLE température de contrôle reproduit le
procédé réel, pas sur l'intérêt d'une consigne comme stratégie de conduite.

L'ARGUMENT. À l'état stationnaire, avec des propriétés indépendantes de T et des
pertes linéaires, le champ vaut T - T_ambiant = amplitude x forme(x, y). Le
RAPPORT entre le point le plus chaud et le plus froid ne dépend donc pas de
l'amplitude — et moduler le courant n'agit que sur l'amplitude. Si ce rapport
dépasse (450-20)/(337-20) = 1,356, aucune conduite du courant ne peut mettre
toute la plaque entre fusion et dégradation. Le script vérifie d'abord cette
indépendance numériquement, puis mesure le rapport.

POURQUOI 80 A ET DE TRÈS LONGUES DURÉES. Bas courant = rien ne fond = pas de
chaleur latente = problème linéaire, donc le rapport obtenu vaut pour toute
amplitude. Les durées vont jusqu'à 3200 s parce que le champ met ~1500 s à
converger : c'est l'asymptote qui répond à la question, pas le transitoire.

RÉSERVE À LIRE AVEC LE RÉSULTAT. Le régime linéaire écarte justement le mécanisme
qui jouerait en faveur de l'idée : la fusion est elle-même un thermostat: la
chaleur latente absorbe l'énergie au point chaud pendant que le point froid
continue de monter. Le modèle de fusion existe (flag, non adopté) et plafonne le
point chaud de 865 à 508 °C sur le cycle 231 A. Le rapport calculé ici est donc
un MAJORANT.

Sorties : biblio/modele/modulation_courant_limite.md
          biblio/modele/figures/fig_modulation_courant_limite.png
"""
from __future__ import annotations

import copy
import sys
from datetime import date
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))
sys.path.insert(0, str(R / "code" / "scripts"))
from _style import apply_style, savefig, OKABE_ITO                  # noqa: E402
from jumeau.materiaux import Config                                  # noqa: E402
from jumeau.procede import Essai                                     # noqa: E402
from jumeau.geometrie import masque_empreinte_cfc                    # noqa: E402
from jumeau.em.source_joule import source_spot                       # noqa: E402

apply_style(**{"font.size": 9.5, "axes.titlesize": 10.5})

SORTIE_MD = R / "biblio" / "modele" / "modulation_courant_limite.md"
SORTIE_FIG = R / "biblio" / "modele" / "figures" / "fig_modulation_courant_limite.png"
GABARIT = R / "code" / "config" / "essais" / "exp7_200A.yaml"

FUSION, DEGRAD, AMBIANT = 337.0, 450.0, 20.0
SEUIL = (DEGRAD - AMBIANT) / (FUSION - AMBIANT)      # 1,356
CENTRES = [0.015875, 0.045875, 0.075875, 0.105875]
Y_C, MFC_REDUIT, COURANT = 0.020, 0.03175, 80.0
DUREES = [200.0, 400.0, 800.0, 1600.0, 3200.0]


def stationnaire(xs, duree, courant=COURANT):
    """Champ final pour la source MOYENNE des spots ``xs`` tenue ``duree``."""
    cfg = copy.deepcopy(Config.charger(R / "code" / "config"))
    cfg.geometrie["cfc"]["longueur"] = MFC_REDUIT
    cfg.contact.h_haut = 30.087
    cfg.ambiant.h_bas_2d = 37.424
    e = Essai(cfg, GABARIT, nx=61, ny=21, nz=15, facteur_couplage=6.0123,
              decalage_x=0.0, racine=R, masque_source_mfc=False)
    e.spots = [{"centre_x": xs[0], "t_debut": 0.0, "t_fin": duree}]
    e.spec["duree_chauffe"] = duree
    e.spec["duree_totale"] = duree
    Q_tot, masque_tot = None, None
    for x in xs:                     # source moyenne = somme des empreintes / n
        m = masque_empreinte_cfc(e.grille, cfg, x, centre_y=Y_C)
        Q = source_spot(e.grille, cfg, e.couches, courant, x,
                        facteur_couplage=6.0123, centre_y=Y_C)
        total = float(Q.sum())
        Q = Q * m[:, :, None]
        Q = Q * (total / float(Q.sum()))     # famille A : le flux se reconcentre
        Q_tot = Q if Q_tot is None else Q_tot + Q
        masque_tot = m if masque_tot is None else np.maximum(masque_tot, m)
    Q_tot = Q_tot / len(xs)
    e._masques = [masque_tot]
    e._Q_spots = [Q_tot]
    e._P_spots_2d = [Q_tot.sum(axis=2) * e.grille.dz]
    sv, sol = e.simuler(modele="2D")
    return e.grille, sv.resultat_2d(sol, sol.t.size - 1)


def rapport(T) -> float:
    return float((T.max() - AMBIANT) / (T.min() - AMBIANT))


def main() -> None:
    geometries = [("un spot fixe", [0.060], OKABE_ITO["vermillon"]),
                  ("quatre spots moyennés\n(balayage modulé)", CENTRES, OKABE_ITO["vert"])]

    courbes, champs = {}, {}
    for nom, xs, _ in geometries:
        rs = []
        for d in DUREES:
            g, T = stationnaire(xs, d)
            rs.append(rapport(T))
            champs[(nom, d)] = (g, T)
            print(f"  {nom.splitlines()[0]:22s} {d:6.0f} s : "
                  f"max {T.max():6.1f}  min {T.min():5.1f}  rapport {rs[-1]:6.2f}",
                  flush=True)
        courbes[nom] = rs

    # contrôle d'indépendance à l'amplitude : facteur 2 de puissance
    controles = []
    for I in (COURANT, COURANT * np.sqrt(2.0)):
        _, T = stationnaire(CENTRES, 1600.0, courant=I)
        controles.append((I, rapport(T)))
        print(f"  contrôle amplitude I={I:5.1f} A : rapport {controles[-1][1]:.3f}",
              flush=True)

    g, T = champs[(geometries[1][0], DUREES[-1])]
    i_froid, j_froid = np.unravel_index(int(np.argmin(T)), T.shape)
    i_chaud, j_chaud = np.unravel_index(int(np.argmax(T)), T.shape)

    SORTIE_FIG.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(11.0, 7.4))
    (ax_r, ax_c), (ax_l, ax_x) = axes

    for nom, _, couleur in geometries:
        ax_r.plot(DUREES, courbes[nom], "o-", lw=2.0, ms=5, color=couleur, label=nom)
    ax_r.axhline(SEUIL, color="0.3", lw=1.4, ls="--")
    ax_r.annotate(f"seuil {SEUIL:.2f} — en dessous, une fenêtre existe",
                  xy=(DUREES[0], SEUIL), textcoords="offset points", xytext=(4, 6),
                  fontsize=8.5, color="0.3")
    ax_r.set_xscale("log")
    ax_r.set_yscale("log")
    # graduations EXPLICITES : les labels mineurs du log par défaut se chevauchaient
    from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator
    ax_r.xaxis.set_major_locator(FixedLocator(DUREES))
    ax_r.xaxis.set_minor_locator(NullLocator())
    ax_r.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}"))
    ax_r.yaxis.set_major_locator(FixedLocator([1, 2, 5, 10, 20, 50]))
    ax_r.yaxis.set_minor_locator(NullLocator())
    ax_r.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax_r.set_xlabel("durée de maintien (s)")
    ax_r.set_ylabel("rapport chaud / froid")
    ax_r.set_title("Le rapport converge — au-dessus du seuil")
    ax_r.legend(fontsize=8.5, frameon=False, loc="upper right")
    ax_r.grid(alpha=0.25, which="both")

    x_mm, y_mm = g.x * 1e3, g.y * 1e3
    im = ax_c.pcolormesh(x_mm, y_mm, T.T, cmap="inferno", shading="auto")
    ax_c.plot(x_mm[i_froid], y_mm[j_froid], "o", ms=9, mfc="none",
              mec=OKABE_ITO["cyan"], mew=2.0)
    ax_c.annotate(f"point froid {T.min():.0f} °C",
                  xy=(x_mm[i_froid], y_mm[j_froid]), textcoords="offset points",
                  xytext=(14, 10), fontsize=9, color=OKABE_ITO["cyan"],
                  fontweight="bold", ha="left")
    ax_c.set_xlabel("x (mm)")
    ax_c.set_ylabel("y (mm)")
    ax_c.set_aspect("equal")     # 120 x 40 mm : ne pas laisser matplotlib etirer
    ax_c.set_title("Champ stationnaire, balayage modulé")
    fig.colorbar(im, ax=ax_c, label="T (°C)", fraction=0.03, pad=0.02)

    i_milieu = T.shape[0] // 2
    ax_l.plot(y_mm, T[i_milieu, :], "o-", lw=2.0, ms=4, color=OKABE_ITO["vert"])
    ax_l.set_xlabel("y — largeur (mm)")
    ax_l.set_ylabel("T (°C)")
    r_l = (T[i_milieu, :].max() - AMBIANT) / (T[i_milieu, :].min() - AMBIANT)
    ax_l.set_title(f"En largeur : pratiquement plat (rapport {r_l:.2f})")
    ax_l.grid(alpha=0.25)

    j_milieu = T.shape[1] // 2
    ax_x.plot(x_mm, T[:, j_milieu], "o-", lw=2.0, ms=4, color=OKABE_ITO["bleu"])
    ax_x.set_xlabel("x — longueur (mm)")
    ax_x.set_ylabel("T (°C)")
    r_x = (T[:, j_milieu].max() - AMBIANT) / (T[:, j_milieu].min() - AMBIANT)
    ax_x.set_title(f"En longueur : tout le déficit est aux bouts (rapport {r_x:.2f})")
    ax_x.grid(alpha=0.25)

    fig.suptitle("Moduler le courant déplace l'obstacle de la largeur vers les "
                 "extrémités — il ne le supprime pas", y=0.985)
    fig.tight_layout(rect=(0, 0, 1, 0.955))
    savefig(fig, SORTIE_FIG)
    plt.close(fig)

    L = [
        "# Moduler le courant peut-il éviter la dégradation et souder toute la plaque ?",
        "",
        f"Généré le {date.today().isoformat()}.",
        "",
        "## L'argument, et sa vérification",
        "",
        "À l'état stationnaire, avec des propriétés indépendantes de la température "
        "et des pertes linéaires, le champ s'écrit `T − T_ambiant = amplitude × "
        "forme(x, y)`. Le **rapport** entre le point le plus chaud et le plus froid "
        "ne dépend donc pas de l'amplitude — et moduler le courant n'agit que sur "
        "l'amplitude. Vérification numérique, à puissance doublée :",
        "",
        "| courant | rapport chaud/froid |",
        "|---|---|",
        *[f"| {I:.0f} A | {r:.3f} |" for I, r in controles],
        "",
        f"Si ce rapport dépasse **({DEGRAD:.0f} − {AMBIANT:.0f}) / ({FUSION:.0f} − "
        f"{AMBIANT:.0f}) = {SEUIL:.3f}**, aucune conduite du courant ne peut mettre "
        "toute la plaque entre fusion et dégradation.",
        "",
        "## Le rapport asymptotique",
        "",
        f"![Limite de la modulation](figures/{SORTIE_FIG.name})",
        "",
        "| durée de maintien | " + " | ".join(n.replace("\n", " ")
                                              for n, _, _ in geometries) + " |",
        "|---|---|---|",
        *[f"| {d:.0f} s | " + " | ".join(f"{courbes[n][i]:.2f}"
                                         for n, _, _ in geometries) + " |"
          for i, d in enumerate(DUREES)],
        "",
        "Le champ met environ 1500 s à converger. La deuxième colonne est le "
        "**meilleur cas atteignable** : la limite d'un balayage assez rapide et "
        "modulé pour que la plaque ne voie plus que la source moyenne.",
        "",
        "## Ce que le calcul dit vraiment",
        "",
        "**Non, la modulation ne ferme pas le problème** — mais elle en déplace le "
        "siège, et c'est le résultat utile.",
        "",
        f"- **En largeur, c'est résolu.** Le profil transverse au stationnaire vaut "
        f"{' / '.join(f'{T[i_milieu, j]:.0f}' for j in range(0, T.shape[1], 5))} °C "
        f"de `y` = 0 à 40 mm, soit un rapport de **{r_l:.2f}**. Tenir la plaque "
        "longtemps fait ce qu'aucun réglage transitoire n'obtenait : la conduction "
        "latérale remplit le centre.",
        f"- **L'obstacle est passé aux extrémités en longueur**, rapport {r_x:.2f}. "
        f"Le point le plus froid est le coin `x` = {x_mm[i_froid]:.0f} mm, "
        f"`y` = {y_mm[j_froid]:.0f} mm, à {T.min():.0f} °C contre {T.max():.0f} au "
        "point chaud.",
        "- **Étaler les passes n'aide pas** : portées jusqu'aux bouts de la plaque, "
        "elles font monter le rapport de 2,30 à 3,63 — la même puissance répartie "
        "plus mince perd davantage aux bords.",
        "",
        "## Deux raisons de ne pas clore la question",
        "",
        "- **Le point froid limitant est là où le modèle est le plus faible.** "
        "`h_bord_x0 = 125` au chant `x` = 0 est un paramètre *effectif, sans base "
        "physique* — au montage, les chants sont tous libres. Le verrou de ce calcul "
        "repose donc sur l'élément le moins fiable du jumeau.",
        "- **La fusion est elle-même un thermostat, et il est absent de ce calcul.** "
        "Le régime linéaire retenu ici pour rendre le rapport indépendant de "
        "l'amplitude écarte précisément le mécanisme qui jouerait en faveur de "
        "l'idée : la chaleur latente absorbe l'énergie au point chaud pendant que le "
        "point froid continue de monter. Le modèle de fusion (flag, non adopté) "
        "plafonne le point chaud de 865 à 508 °C sur le cycle 231 A. **Le rapport "
        "calculé ici est donc un majorant.**",
        "",
        "Reproduire : `.venv/bin/python code/scripts/gen/gen_modulation_courant_limite.py`",
    ]
    SORTIE_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("ecrit :", SORTIE_MD)
    print("ecrit :", SORTIE_FIG)


if __name__ == "__main__":
    main()
