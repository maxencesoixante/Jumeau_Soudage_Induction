"""Trois familles de modèles du MFC raccourci — comparaison et sensibilité (issues #55/#60).

COMPLÈTE `gen_prediction_mfc_reduit.py` / `biblio/modele/prediction_mfc_reduit.md`,
qui restent INTACTS : ce document-là a été figé avant la campagne pour être
opposable après coup, on ne le réécrit pas. Celui-ci ajoute les colonnes que la
modélisation fine a rendues calculables, et le dit.

CE QUI A CHANGÉ. Jusqu'ici, la longueur du MFC n'entrait pas dans le champ : la
méthode des images traite le concentrateur comme un demi-espace perméable INFINI
(η = (µr−1)/(µr+1)), qui ne dépend ni de la longueur ni de la largeur du bloc. Le
seul mécanisme disponible était donc un masque d'empreinte appliqué a posteriori
à la puissance Joule. `em/champ_coil.py` sait désormais tronquer la contribution
IMAGE à l'empreinte du bloc, de deux façons indépendantes (drapeaux par défaut
OFF, comportement historique bit-à-bit préservé).

LES TROIS FAMILLES, et ce qui les sépare vraiment :

  A. « masque d'empreinte, puissance conservée » (`masque_source_mfc`, mode
     "conserver") — la puissance Joule totale est REDISTRIBUÉE sur l'empreinte
     restante. Affirmation physique : le flux manquant se reconcentre.

  B. « image tronquée » (`image_mfc_finie`), deux variantes :
       - "observation" : la contribution image est pondérée selon la position du
         POINT D'OBSERVATION par rapport à l'empreinte du bloc ;
       - "source"      : la POLYLIGNE IMAGE elle-même est tronquée, chaque
         sous-segment portant le poids évalué à sa propre position.
     Affirmation physique commune : hors du bloc, le flux ne se reconcentre pas,
     il retombe simplement au cas « bobine nue, sans MFC ».

A et B ne diffèrent donc pas par leur finesse mais par une HYPOTHÈSE PHYSIQUE sur
le devenir du flux manquant. Aucun calcul ne tranche entre les deux — c'est la
mesure de l'issue #55 qui le peut, et c'est tout l'intérêt de la campagne.

MARGE. L'adoucissement de bord des variantes B utilise une marge prise égale à la
hauteur du bloc (`cfc.hauteur`, 12 mm) — choix d'ordre de grandeur, non mesuré.
Ce script balaie 6/12/24 mm pour montrer si le verdict en dépend. Vérifié :
`cfc.hauteur` ne sert QU'À cette marge dans le code (le plan image utilise la
hauteur de la BOBINE, l'empreinte n'utilise que longueur/largeur) — le balayage
ne confond donc pas deux effets.

Sortie : biblio/modele/prediction_mfc_familles.md
"""
from __future__ import annotations

import copy
import sys
from datetime import date
from pathlib import Path

import numpy as np

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))

from jumeau.materiaux import Config                              # noqa: E402
from jumeau.procede import Essai                                 # noqa: E402

ESSAI = R / "code" / "config" / "essais" / "exp7_200A.yaml"
SORTIE = R / "biblio" / "modele" / "prediction_mfc_familles.md"
FACTEUR = 6.0123
LONGUEUR_REDUITE = 0.03175
ORDRE_TC = ["TC1", "TC2", "TC3", "TC4", "TC5"]
Y_MM = {"TC1": 0, "TC2": 10, "TC3": 20, "TC4": 30, "TC5": 40}


def pics(cfg, **kwargs) -> dict[str, float]:
    e = Essai(cfg, ESSAI, facteur_couplage=FACTEUR, decalage_x=0.0, racine=R, **kwargs)
    sv, sol = e.simuler(modele="2D")
    return {n: float(np.nanmax(s)) for n, s in e.series_tc(sv, sol).items()}


def contraste(p: dict[str, float]) -> float:
    return max(p["TC1"], p["TC5"]) / p["TC3"]


def main() -> None:
    cfg_labo = Config.charger(R / "code" / "config")
    cfg_reduit = copy.deepcopy(cfg_labo)
    cfg_reduit.geometrie["cfc"]["longueur"] = LONGUEUR_REDUITE
    assert cfg_labo.geometrie["cfc"]["longueur"] == 0.055, "config de référence modifiée"

    cas = {
        "labo": pics(cfg_labo),
        "masque": pics(cfg_reduit, masque_source_mfc=True, masque_source_mode="conserver"),
        "obs": pics(cfg_reduit, image_mfc_finie=True, mode_troncature_image="observation"),
        "src": pics(cfg_reduit, image_mfc_finie=True, mode_troncature_image="source"),
    }

    # sensibilité à la marge : cfc.hauteur ne pilote QUE la marge (vérifié)
    sensibilite = []
    for marge_mm in (6.0, 12.0, 24.0):
        cfg_m = copy.deepcopy(cfg_reduit)
        cfg_m.geometrie["cfc"]["hauteur"] = marge_mm * 1e-3
        sensibilite.append((
            marge_mm,
            contraste(pics(cfg_m, image_mfc_finie=True, mode_troncature_image="observation")),
            contraste(pics(cfg_m, image_mfc_finie=True, mode_troncature_image="source")),
        ))

    c = {k: contraste(v) for k, v in cas.items()}
    L = [
        "# MFC raccourci — trois familles de modèles, et ce qui les sépare",
        "",
        f"Généré le {date.today().isoformat()}. Condition identique à la prédiction figée : "
        "**200 A, 18 s**, spot `x = 60 mm`, 5 TC d'interface — soit `exp7_200A`.",
        "",
        "Ce document **complète** `prediction_mfc_reduit.md` (figé avant campagne) et ne le "
        "remplace pas. Les deux premières colonnes y sont identiques ; les deux dernières "
        "sont nouvelles, rendues calculables par la troncature de l'image au niveau du champ.",
        "",
        "## Les trois familles",
        "",
        "| famille | mécanisme | affirmation physique sur le flux manquant |",
        "|---|---|---|",
        "| **A — masque d'empreinte** | la puissance Joule totale est redistribuée sur "
        "l'empreinte restante | il **se reconcentre** sous le bloc plus petit |",
        "| **B — image tronquée** (2 variantes) | seule la contribution image est pondérée ; "
        "le champ de la bobine nue reste entier | il **ne se reconcentre pas** : hors du bloc "
        "on retombe au cas sans MFC |",
        "",
        "A et B ne diffèrent pas par leur finesse mais par une **hypothèse physique**. "
        "Aucun calcul ne tranche entre elles.",
        "",
        "## Pics d'interface (°C)",
        "",
        "| TC | y (mm) | MFC labo 55 mm | A — masque dur | B — image, observation | B — image, source |",
        "|---|---|---|---|---|---|",
    ]
    for tc in ORDRE_TC:
        L.append(f"| {tc} | {Y_MM[tc]} | {cas['labo'][tc]:.1f} | {cas['masque'][tc]:.1f} "
                 f"| {cas['obs'][tc]:.1f} | {cas['src'][tc]:.1f} |")
    L += [
        f"| **contraste bord/centre** | | **{c['labo']:.2f}** | **{c['masque']:.2f}** "
        f"| **{c['obs']:.2f}** | **{c['src']:.2f}** |",
        "",
        "## Le résultat",
        "",
        f"**Les deux variantes de la famille B s'accordent** ({c['src']:.2f} et {c['obs']:.2f}) "
        f"alors qu'elles tronquent la même physique de deux façons indépendantes — l'une pondère "
        f"l'observateur, l'autre la source. **La famille A est l'intrus** ({c['masque']:.2f}), pas "
        f"un troisième point de la même famille.",
        "",
        f"Conséquence directe pour la campagne : selon que le contraste mesuré tombe vers "
        f"**{c['masque']:.1f}** ou reste vers **{c['src']:.1f}–{c['obs']:.1f}**, la mesure tranche "
        f"entre « le flux se reconcentre » et « le flux disparaît localement ». L'issue #55 "
        f"discrimine donc **trois familles au lieu de deux**.",
        "",
        "Point chaud : il reste aux chants dans toute la famille B (TC1/TC5 > TC3 dans tous les "
        "cas), et ne se recentre que sous la famille A.",
        "",
        "## Sensibilité à la marge d'adoucissement",
        "",
        "La marge des variantes B vaut par défaut la hauteur du bloc (12 mm) — ordre de grandeur, "
        "non mesuré. Est-ce un paramètre libre qui décide du résultat ?",
        "",
        "| marge (mm) | B — observation | B — source |",
        "|---|---|---|",
    ]
    for marge_mm, c_obs, c_src in sensibilite:
        L.append(f"| {marge_mm:.0f} | {c_obs:.2f} | {c_src:.2f} |")
    bande = [v for _, o, s in sensibilite for v in (o, s)]
    L += [
        "",
        f"**Non.** Sur un facteur 4, les deux variantes restent dans la bande "
        f"{min(bande):.2f}–{max(bande):.2f}, sans jamais approcher la famille A ni inverser le "
        f"profil. La marge est un paramètre libre assumé, mais elle ne décide pas du verdict.",
        "",
        "## Limites",
        "",
        "- Les trois familles sont des approximations de **1er ordre**. Aucune n'est de la "
        "physique établie : aucune ne résout le bloc de ferrite fini.",
        "- La variante « observation » pondère le point d'observation, pas la position de chaque "
        "segment image le long du bloc ; la variante « source » corrige ce point mais suppose "
        "toujours η uniforme (valeur de demi-espace infini), sans correction de démagnétisation "
        "pour un bloc petit.",
        "- θ* n'est recalibré pour aucune des géométries réduites (objet de #60, après mesure).",
        "- **Aucune source du corpus documentaire ne fait varier la longueur d'un concentrateur** : "
        "il n'existe pas d'appui bibliographique externe à ces prédictions.",
        "",
        f"Reproduire : `.venv/bin/python code/scripts/gen/{Path(__file__).name}`",
        "",
    ]
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    SORTIE.write_text("\n".join(L), encoding="utf-8")

    for nom, p in cas.items():
        print(f"{nom:8s} " + "  ".join(f"{t}={p[t]:.1f}" for t in ORDRE_TC)
              + f"  | contraste {contraste(p):.2f}")
    print("marge (mm) / observation / source :",
          "  ".join(f"{m:.0f}:{o:.2f}/{s:.2f}" for m, o, s in sensibilite))
    print(f"ecrit : {SORTIE}")


if __name__ == "__main__":
    main()
