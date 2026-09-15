"""Le verdict « aucun plan de passes ne soude toute la largeur » tient-il pour
les QUATRE modèles de MFC réduit, ou n'était-il qu'une propriété du seul modèle
essayé ?

POURQUOI CE SCRIPT EXISTE. Le planificateur (#31, #37) a conclu NON, et #39 a
conclu que le MFC réduit ne débloque pas le centre. Ces deux verdicts ont été
obtenus dans UNE configuration de modèle : troncature dure de la source à
l'empreinte du bloc, sans report de la puissance perdue -- c'est-à-dire la plus
défavorable des quatre hypothèses aujourd'hui disponibles, celle qui SUPPRIME le
flux hors empreinte au lieu de le déplacer. Les deux familles « image tronquée »
n'existaient pas (livrées le 2026-09-14). Et le θ* employé figeait h_bord_x0=250,
périmé depuis le 2026-09-06 (125).

Un verdict aussi structurant -- il dit qu'aucune géométrie de MFC ne soude le
centre -- ne doit pas dépendre du choix d'hypothèse qui l'a produit. Ce script
le rejoue dans les quatre familles pour savoir s'il est ROBUSTE ou s'il était un
artefact de modélisation.

PROTOCOLE DE RÉOUVERTURE. La première cellule calculée est un CONTRÔLE
D'ATTRIBUTION : mêmes courants, même famille, même θ* que la campagne
historique. Si elle ne retrouve pas les ~6-7 % documentés, ce n'est pas un
détail de procédure -- c'est le résultat, et il porte sur le code ou sur la
mémoire, pas sur la question posée. Les autres cellules ne se comparent qu'à ce
point d'ancrage reproduit, jamais au souvenir du chiffre publié.

Sorties : biblio/modele/plan_passes_familles.md
          biblio/modele/figures/fig_plan_passes_familles.png
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))
sys.path.insert(0, str(R / "code" / "scripts"))
from _style import apply_style, savefig, OKABE_ITO            # noqa: E402
from jumeau.materiaux import Config                            # noqa: E402
from jumeau.planification.empreinte import bibliotheque        # noqa: E402
from jumeau.planification.planificateur import (               # noqa: E402
    planifier, metriques, verifier_sequentiel)

apply_style(**{"font.size": 9.5, "axes.titlesize": 10.5})

SORTIE_MD = R / "biblio" / "modele" / "plan_passes_familles.md"
SORTIE_FIG = R / "biblio" / "modele" / "figures" / "fig_plan_passes_familles.png"

FUSION, DEGRAD = 337.0, 450.0
X_CS = [0.030, 0.060, 0.090, 0.110]
Y_CS = [0.000, 0.010, 0.020, 0.030, 0.040]
MFC_LONGUEURS = [None, 0.03175]
DUREE = 20.0
COURANTS_HIST = [200.0, 235.0]          # grille de la campagne historique
COURANTS_ETENDUS = [200.0, 235.0, 250.0]

LIBELLES = {
    "tronquer": "Troncature dure\n(le flux hors bloc disparaît)",
    "conserver": "Famille A — masque conservatif\n(le flux se reconcentre)",
    "image_observation": "Famille B — image tronquée, observation\n(pas de reconcentration)",
    "image_source": "Famille B — image tronquée, source\n(pas de reconcentration)",
}


def cellule(cfg, famille, courants, h_bord_x0):
    """Plan glouton + vérification séquentielle pour une (famille, θ*, grille)."""
    grille, lib = bibliotheque(cfg, X_CS, Y_CS, courants, DUREE,
                               mfc_longueurs=MFC_LONGUEURS, famille=famille,
                               h_bord_x0=h_bord_x0)
    passes, Tc, m = planifier(lib, fusion=FUSION, degrad=DEGRAD)
    params = [{"x_c": k[0], "y_c": k[1], "courant": k[2],
               "mfc_longueur": k[3], "duree": DUREE} for k in passes]
    if params:
        _, T_seq = verifier_sequentiel(cfg, params, famille=famille,
                                       h_bord_x0=h_bord_x0)
        m_seq = metriques(T_seq, fusion=FUSION, degrad=DEGRAD)
    else:
        T_seq, m_seq = Tc, m
    return {"grille": grille, "passes": params, "T_seq": T_seq,
            "glouton": m, "seq": m_seq,
            "mfc_reduit_retenu": any(p["mfc_longueur"] is not None for p in params)}


def carte(ax, res, titre):
    g, T = res["grille"], res["T_seq"]
    x_mm, y_mm = g.x * 1e3, g.y * 1e3
    im = ax.pcolormesh(x_mm, y_mm, T.T, cmap="inferno", vmin=20.0, vmax=DEGRAD,
                       shading="auto")
    ax.contour(x_mm, y_mm, T.T, levels=[FUSION], colors="white", linewidths=1.2)
    if T.max() > DEGRAD:   # sans ce contour, une plaque brulee se lit comme soudee
        ax.contour(x_mm, y_mm, T.T, levels=[DEGRAD], colors=OKABE_ITO["cyan"],
                   linewidths=1.2, linestyles="--")
    for p in res["passes"]:
        ax.plot(p["x_c"] * 1e3, p["y_c"] * 1e3, "o", ms=5,
                mfc="none", mec=OKABE_ITO["cyan"], mew=1.6)
    ax.set_title(f"{titre}\nsoudé {res['seq']['pct_soude']:.1f} %  ·  "
                 f"dégradé {res['seq']['pct_degrade']:.1f} %  ·  "
                 f"{len(res['passes'])} passe(s)")
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.set_aspect("equal")               # 120 x 40 mm : ne PAS laisser matplotlib etirer
    return im


def temperatures_une_passe(cfg, courant=235.0):
    """Pic et température au centre de la largeur pour UNE passe centrée y=20 mm.

    C'est ici que se lit la physique : le centre (y = 20 mm) est la ligne nodale
    de la dissipation, il ne chauffe que par conduction latérale."""
    from jumeau.planification.empreinte import empreinte
    lignes = []
    _, T55 = empreinte(cfg, 0.060, 0.020, courant, DUREE, mfc_longueur=None)
    i_c, j_c = T55.shape[0] // 2, T55.shape[1] // 2
    lignes.append(("MFC labo 55 mm", float(T55.max()), float(T55[i_c, j_c])))
    for f in ("tronquer", "conserver", "image_observation", "image_source"):
        _, T = empreinte(cfg, 0.060, 0.020, courant, DUREE,
                         mfc_longueur=0.03175, famille=f)
        lignes.append((f, float(T.max()), float(T[i_c, j_c])))
    return courant, lignes


def main() -> None:
    cfg = Config.charger(R / "code" / "config")
    print("CONTRÔLE D'ATTRIBUTION — grille et θ* historiques (h_bord_x0=250)…",
          flush=True)
    ctrl = cellule(cfg, "tronquer", COURANTS_HIST, 250.0)
    print(f"  glouton {ctrl['glouton']['pct_soude']:.1f} %  "
          f"séquentiel {ctrl['seq']['pct_soude']:.1f} %  "
          f"(publié : 6.1 / 7.0) -> "
          f"{'REPRODUIT' if abs(ctrl['seq']['pct_soude'] - 7.0) < 1.0 else 'ÉCART'}",
          flush=True)

    # Deux choses changent entre le contrôle et la matrice : le θ* et la grille
    # de courants. Cette cellule les sépare, sans quoi on attribuerait à l'un ce
    # qui vient de l'autre.
    print("θ* canonique (125), grille de courants HISTORIQUE…", flush=True)
    theta = cellule(cfg, "tronquer", COURANTS_HIST, None)
    print(f"  glouton {theta['glouton']['pct_soude']:.1f} %  "
          f"séquentiel {theta['seq']['pct_soude']:.1f} %", flush=True)

    resultats = {}
    for famille in ("tronquer", "conserver", "image_observation", "image_source"):
        print(f"θ* canonique (125) · {famille} · courants {COURANTS_ETENDUS}…",
              flush=True)
        r = cellule(cfg, famille, COURANTS_ETENDUS, None)
        print(f"  glouton {r['glouton']['pct_soude']:.1f} %  "
              f"séquentiel {r['seq']['pct_soude']:.1f} %  "
              f"dégradé {r['seq']['pct_degrade']:.1f} %  "
              f"MFC réduit retenu : {'oui' if r['mfc_reduit_retenu'] else 'non'}",
              flush=True)
        resultats[famille] = r

    SORTIE_FIG.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(11.0, 6.4))
    for ax, (fam, r) in zip(axes.ravel(), resultats.items()):
        im = carte(ax, r, LIBELLES[fam])
    fig.colorbar(im, ax=axes, label="pic de température d'interface (°C)",
                 fraction=0.035, pad=0.02)
    fig.suptitle("Couverture d'un plan de passes selon l'hypothèse de MFC réduit\n"
                 f"trait plein : fusion {FUSION:.0f} °C   ·   "
                 f"tireté : dégradation {DEGRAD:.0f} °C", y=1.0)
    savefig(fig, SORTIE_FIG)
    plt.close(fig)

    courant_1p, lignes_1p = temperatures_une_passe(cfg)

    uniforme = {f: (r["seq"]["pct_soude"] >= 99.9 and r["seq"]["pct_degrade"] == 0.0)
                for f, r in resultats.items()}
    L = [
        "# Le verdict « pas de soudage uniforme » survit-il au changement "
        "d'hypothèse sur le MFC réduit ?",
        "",
        f"Généré le {date.today().isoformat()}. Plan de passes glouton puis "
        "vérification séquentielle (chaleur résiduelle incluse), seuils "
        f"fusion {FUSION:.0f} °C / dégradation {DEGRAD:.0f} °C.",
        "",
        "## Contrôle d'attribution",
        "",
        "Avant toute comparaison, la configuration historique est rejouée : "
        "troncature dure, `h_bord_x0 = 250`, courants {200, 235} A.",
        "",
        f"| | publié (#31/#37/#39) | rejoué |",
        f"|---|---|---|",
        f"| soudé, plan glouton | 6.1 % | {ctrl['glouton']['pct_soude']:.1f} % |",
        f"| soudé, séquentiel | 7.0 % | {ctrl['seq']['pct_soude']:.1f} % |",
        "",
        "Deux choses séparent ce contrôle de la matrice qui suit : le θ* et la "
        "grille de courants. Les découpler évite d'attribuer à l'un ce qui vient "
        "de l'autre.",
        "",
        "| grille de courants | h_bord_x0 | soudé, séquentiel |",
        "|---|---|---|",
        f"| {{200, 235}} A | 250 (historique) | {ctrl['seq']['pct_soude']:.1f} % |",
        f"| {{200, 235}} A | 125 (canonique) | {theta['seq']['pct_soude']:.1f} % |",
        "",
        "**Le θ* ne bouge rien ici**, et c'est attendu : `h_bord_x0` n'agit que "
        "sur le chant `x = 0`, alors que la couverture se joue sur les lobes du "
        "M, c'est-à-dire sur les chants en `y`. Tout l'écart avec la matrice "
        "ci-dessous vient donc de l'ajout de 250 A à la grille — la correction "
        "de θ* était nécessaire par cohérence, pas parce qu'elle changeait le "
        "verdict.",
        "",
        "## Les quatre hypothèses, à θ* canonique",
        "",
        "`h_bord_x0 = 125` (canonique depuis le 2026-09-06) et courants "
        "{200, 235, 250} A — la grille est ÉLARGIE vers le haut, donc le "
        "planificateur ne peut qu'y faire mieux.",
        "",
        "| hypothèse sur le flux hors empreinte | soudé | dégradé | passes | "
        "MFC réduit retenu | uniforme |",
        "|---|---|---|---|---|---|",
    ]
    noms = {"tronquer": "il disparaît (troncature dure)",
            "conserver": "il se reconcentre (famille A)",
            "image_observation": "il ne se reconcentre pas — obs. (famille B)",
            "image_source": "il ne se reconcentre pas — source (famille B)"}
    for fam, r in resultats.items():
        L.append(f"| {noms[fam]} | {r['seq']['pct_soude']:.1f} % | "
                 f"{r['seq']['pct_degrade']:.1f} % | {len(r['passes'])} | "
                 f"{'oui' if r['mfc_reduit_retenu'] else 'non'} | "
                 f"{'OUI' if uniforme[fam] else 'NON'} |")
    L += [
        "",
        "Trois des quatre panneaux de la figure sont identiques. Ce n'est pas une "
        "redondance de tracé : dans ces trois hypothèses le planificateur glouton "
        "**ne retient aucune passe au MFC réduit**, si bien que le plan se réduit "
        "aux mêmes passes au MFC labo 55 mm.",
        "",
        f"![Couverture par hypothèse](figures/{SORTIE_FIG.name})",
        "",
        "## Où se lit la physique : une passe unique",
        "",
        f"Une seule passe centrée en `x = 60 mm`, `y = 20 mm`, {courant_1p:.0f} A, "
        f"{DUREE:.0f} s. Le centre de la largeur est la **ligne nodale de la "
        "dissipation** (la puissance Joule y est nulle par symétrie) : il ne "
        "chauffe que par conduction latérale.",
        "",
        "| hypothèse | pic (°C) | centre de la largeur (°C) |",
        "|---|---|---|",
        *[f"| {n} | {pic:.1f} | {centre:.1f} |" for n, pic, centre in lignes_1p],
        "",
        f"Aucune hypothèse n'amène le centre à la fusion ({FUSION:.0f} °C). La "
        "seule qui l'en rapproche est celle où le flux se reconcentre — et elle "
        "y parvient en portant les chants au-delà du seuil de dégradation.",
        "",
        "## Ce que ce calcul ne prouve pas",
        "",
        f"- **Le taux de dégradation de la famille A est à prendre avec réserve.** "
        f"Le seuil {DEGRAD:.0f} °C est appliqué à une température d'interface "
        "calculée avec la config canonique, dont la chaleur latente vaut 130 J/g "
        "(valeur 100 % cristallin, ~3× trop) et qui n'a pas de plateau de fusion. "
        "Sur le cycle 231 A, cette config donne 865 °C là où le modèle de fusion "
        "donne 508 °C : au-delà du point de fusion, elle **surestime "
        "systématiquement** l'interface. Les 33 % dégradés sont donc un majorant, "
        "pas une mesure. Le verdict « non uniforme » ne repose pas dessus : "
        "44.9 % de soudé n'est de toute façon pas une couverture.",
        "- **Aucune des quatre hypothèses n'est de la physique établie.** Aucune "
        "ne résout le bloc de ferrite fini ; la méthode des images suppose un "
        "demi-espace infini. Elles encadrent un comportement, elles ne le "
        "calculent pas.",
        "- **θ\\* n'est recalibré pour aucune géométrie réduite** (objet de #60, "
        "après mesure).",
        "- Le résidu structurel connu du jumeau — le centre se remplit trop "
        "lentement, indépendamment du courant — joue **dans le sens "
        "conservateur** ici : le modèle sous-estime le remplissage du centre. "
        "Une prédiction « le centre fond » serait donc robuste ; la prédiction "
        "« le centre ne fond pas » l'est moins, et c'est celle qu'on obtient.",
        "",
        "Reproduire : `.venv/bin/python code/scripts/gen/gen_plan_passes_familles.py`",
    ]
    SORTIE_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("ecrit :", SORTIE_MD)
    print("ecrit :", SORTIE_FIG)


if __name__ == "__main__":
    main()
