"""Prédiction FIGÉE A PRIORI — profil en largeur, MFC 55 mm vs 31,75 mm (issues #55/#60).

Pourquoi ce script existe alors que `gen_mfc_reduit.py` prédit déjà le MFC réduit :
celui-ci tourne à 250 A / 15 s et produit une FIGURE. L'issue #55 mesurera
**200 A, ~18 s, 5 TC d'interface à y = 0/10/20/30/40 mm, spot x = 60 mm** — c'est
exactement la condition de `exp7_200A.yaml`. On prédit donc sur les observables
qui seront réellement relevés, et on écrit le résultat dans un document DATÉ pour
qu'il soit opposable après la campagne (held-out réel, pas ajustement a posteriori).

ANCRAGE — ce qui rend la prédiction interprétable. La passe A (MFC labo 55 mm) est
DÉJÀ MESURÉE : c'est exp7_200A. On calcule donc d'abord l'erreur du modèle sur A,
TC par TC, contre la mesure ; cette erreur est la barre à laquelle comparer l'écart
A→B prédit. Sans cet ancrage, un écart prédit de 50 °C ne signifie rien — on ne sait
pas s'il dépasse l'erreur propre du modèle. (Mesures relues depuis le fichier brut,
jamais depuis les valeurs recopiées en commentaire du YAML.)

MODÈLE DU MFC RÉDUIT — masque d'empreinte, mode "conserver" (cf.
`jumeau.procede.Essai.masque_source_mode`) : Q_masqué = Q · mask · (∫Q / ∫(Q·mask)).
La puissance Joule TOTALE est conservée et redéposée dans une empreinte plus petite,
un concentrateur réduit canalisant le même flux dans moins de surface.

LIMITES — à lire avant d'utiliser un seul chiffre de la sortie :
  1. La méthode des images (`champ_coil.bz_plan`) ne connaît que µ_r et un PLAN
     INFINI : le champ calculé est RIGOUREUSEMENT identique entre MFC 55 et 31,75 mm
     (verrouillé par `test_masque_source_mfc_off_est_non_regression`). Tout l'effet
     prédit vient donc du masque a posteriori, pas d'une re-résolution EM.
  2. Le masque est un rectangle DUR 0/1, sans frange de champ de bord. Un MFC réel
     de 31,75 mm ne fait pas s'annuler le champ à y = 4,1 et 35,9 mm : les valeurs
     prédites AUX CHANTS sont donc les moins crédibles de toute la sortie.
  3. θ* (facteur_couplage) n'est PAS recalibré pour la géométrie réduite — c'est
     précisément l'objet de l'issue #60, qui vient après la mesure.
Conséquence : ce qui est prédit ici, ce sont des TENDANCES et des RAPPORTS. Les
niveaux absolus de la colonne B ne sont pas validés.

Sortie : biblio/modele/prediction_mfc_reduit.md (écrase ; document daté)
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
from jumeau.validation.chargement import charger_mesures         # noqa: E402

ESSAI = R / "code" / "config" / "essais" / "exp7_200A.yaml"
SORTIE = R / "biblio" / "modele" / "prediction_mfc_reduit.md"
FACTEUR = 6.0123          # θ* canonique 2D — NON recalibré pour le MFC réduit
LONGUEUR_REDUITE = 0.03175
T_FUSION = 337.0
ORDRE_TC = ["TC1", "TC2", "TC3", "TC4", "TC5"]


def pics_simules(cfg, *, masque: bool) -> dict[str, float]:
    """Pic simulé à chaque thermocouple, modèle 2D (celui où vit θ* canonique)."""
    e = Essai(cfg, ESSAI, facteur_couplage=FACTEUR, decalage_x=0.0, racine=R,
              masque_source_mfc=masque, masque_source_mode="conserver")
    sv, sol = e.simuler(modele="2D")
    return {nom: float(np.nanmax(serie))
            for nom, serie in e.series_tc(sv, sol).items()}


def pics_mesures() -> dict[str, float]:
    """Pics MESURÉS de exp7_200A, relus depuis le fichier brut.

    Principe 7 : une cible chiffrée recopiée dans un commentaire est une
    affirmation, pas une donnée — on la reconstruit depuis la source primaire.
    """
    import yaml
    spec = yaml.safe_load(ESSAI.read_text(encoding="utf-8"))
    df = charger_mesures(R / spec["fichier_mesures"])
    pics = {}
    for col in df.columns[1:]:
        nom = col.split()[0].strip()
        if nom in ORDRE_TC:
            pics[nom] = float(np.nanmax(df[col].to_numpy(dtype=float)))
    return pics


def contraste(profil: dict[str, float]) -> float:
    """Contraste bord/centre : max des deux chants sur le centre de largeur."""
    return max(profil["TC1"], profil["TC5"]) / profil["TC3"]


def main() -> None:
    cfg_labo = Config.charger(R / "code" / "config")
    cfg_reduit = copy.deepcopy(cfg_labo)
    cfg_reduit.geometrie["cfc"]["longueur"] = LONGUEUR_REDUITE
    assert cfg_labo.geometrie["cfc"]["longueur"] == 0.055, "config de référence modifiée"

    mesure_A = pics_mesures()
    modele_A = pics_simules(cfg_labo, masque=False)
    modele_B = pics_simules(cfg_reduit, masque=True)

    y_mm = {"TC1": 0, "TC2": 10, "TC3": 20, "TC4": 30, "TC5": 40}
    ecarts_A = {tc: modele_A[tc] - mesure_A[tc] for tc in ORDRE_TC}
    biais = float(np.mean([ecarts_A[tc] for tc in ORDRE_TC]))
    ecart_abs_moyen = float(np.mean([abs(ecarts_A[tc]) for tc in ORDRE_TC]))

    lignes = [
        f"# Prédiction figée — profil en largeur, MFC 55 mm vs 31,75 mm",
        "",
        f"**Figée le {date.today().isoformat()}, AVANT la campagne.** Issues #55 (mesure) "
        f"et #60 (recalibration). Condition : **200 A, 18 s**, spot fixe `x = 60 mm`, "
        f"5 TC d'interface à `y = 0/10/20/30/40 mm` — soit exactement `exp7_200A`.",
        "",
        "Ce document existe pour être **opposable après coup**. Il ne doit pas être "
        "réécrit une fois les mesures connues ; le confronter, et écrire le verdict ailleurs.",
        "",
        "## 1. Ancrage — ce que le modèle vaut déjà sur cet observable",
        "",
        "La passe A (MFC labo 55 mm) est déjà mesurée. L'erreur du modèle sur A est la "
        "barre à laquelle comparer tout écart prédit sur B.",
        "",
        "| TC | y (mm) | mesuré A (°C) | modèle A (°C) | écart (°C) |",
        "|---|---|---|---|---|",
    ]
    for tc in ORDRE_TC:
        lignes.append(f"| {tc} | {y_mm[tc]} | {mesure_A[tc]:.1f} | {modele_A[tc]:.1f} "
                      f"| {ecarts_A[tc]:+.1f} |")
    lignes += [
        "",
        f"Biais moyen **{biais:+.1f} °C**, écart absolu moyen **{ecart_abs_moyen:.1f} °C**. "
        f"Contraste bord/centre : mesuré **{contraste(mesure_A):.2f}**, "
        f"modèle **{contraste(modele_A):.2f}**.",
        "",
        "## 2. Prédiction — passe B (MFC réduit 31,75 mm)",
        "",
        "| TC | y (mm) | modèle A (°C) | modèle B (°C) | Δ prédit (°C) | "
        "\\|Δ\\| vs erreur du modèle sur A |",
        "|---|---|---|---|---|---|",
    ]
    for tc in ORDRE_TC:
        delta = modele_B[tc] - modele_A[tc]
        err = abs(ecarts_A[tc])
        rapport = abs(delta) / err if err > 0 else float("inf")
        verdict = ("au-dessus du bruit" if rapport >= 2.0
                   else "DANS le bruit" if rapport < 1.0 else "marginal")
        lignes.append(f"| {tc} | {y_mm[tc]} | {modele_A[tc]:.1f} | {modele_B[tc]:.1f} "
                      f"| {delta:+.1f} | ×{rapport:.1f} — {verdict} |")

    c_A, c_B = contraste(modele_A), contraste(modele_B)

    def maxima(profil: dict[str, float], tol: float = 0.5) -> str:
        """TC portant le maximum — TOUS ceux qui l'atteignent.

        Le modèle 2D est exactement symétrique en y : TC1/TC5 et TC2/TC4 sont
        à égalité stricte. Nommer un seul gagnant laisserait croire que le
        modèle brise la symétrie, et rendrait l'énoncé infalsifiable du
        mauvais côté (la mesure, elle, n'est pas symétrique).
        """
        cible = max(profil.values())
        gagnants = [t for t in ORDRE_TC if abs(profil[t] - cible) <= tol]
        return " / ".join(f"{t} (y={y_mm[t]} mm)" for t in gagnants)

    max_A, max_B = maxima(modele_A), maxima(modele_B)
    lignes += [
        "",
        f"Contraste bord/centre prédit : **{c_A:.2f} → {c_B:.2f}** "
        f"(réduction ×{c_A / c_B:.2f}). Maximum du profil : **{max_A} → {max_B}**.",
        "",
        f"Le modèle part d'un contraste **sur-estimé** ({c_A:.2f} contre "
        f"{contraste(mesure_A):.2f} mesuré — c'est le résidu d'étalement in-plane "
        f"documenté, issue #3). Si le raccourcissement agissait sur la mesure avec le "
        f"même facteur ×{c_A / c_B:.2f}, le contraste réel passerait de "
        f"{contraste(mesure_A):.2f} à **~{contraste(mesure_A) / (c_A / c_B):.2f}**, "
        f"c'est-à-dire un profil **inversé** — centre plus chaud que les chants. "
        f"C'est l'énoncé le plus discriminant de ce document, et le plus facile à lire "
        f"sur la mesure.",
        "",
        f"À noter pour la lecture : le modèle 2D est **exactement symétrique** en y "
        f"(TC1=TC5, TC2=TC4), alors que la mesure de A ne l'est pas "
        f"(TC2={mesure_A['TC2']:.0f} contre TC4={mesure_A['TC4']:.0f} °C, "
        f"{abs(mesure_A['TC2'] - mesure_A['TC4']):.0f} °C d'écart). Aucune prédiction "
        f"par TC isolé ne peut donc être testée plus finement que cette asymétrie-là ; "
        f"comparer de préférence les moyennes appariées (TC1,TC5) et (TC2,TC4).",
        "",
        "## 3. Ce que la mesure peut RÉFUTER",
        "",
        "Énoncés falsifiables, par ordre de robustesse décroissante.",
        "",
        f"1. **Le contraste bord/centre baisse.** Prédit {c_A:.2f} → {c_B:.2f}. "
        f"Réfuté si le contraste mesuré de B est supérieur ou égal à celui de A.",
        f"2. **Le maximum quitte le chant.** Prédit en {max_B}. "
        f"Réfuté si le maximum de B reste en TC1 ou TC5.",
        f"3. **Les chants refroidissent nettement.** Prédit TC1 {modele_B['TC1'] - modele_A['TC1']:+.0f} °C "
        f"et TC5 {modele_B['TC5'] - modele_A['TC5']:+.0f} °C. "
        f"**Énoncé le plus fragile** : le masque dur n'a pas de frange de bord, donc ces deux "
        f"valeurs sont les moins crédibles de la sortie (limite 2 de l'en-tête).",
        f"4. **Le centre ne gagne pas la fusion.** Prédit TC3 = {modele_B['TC3']:.0f} °C, "
        f"contre {T_FUSION:.0f} °C de fusion — "
        f"{'ATTEINTE' if modele_B['TC3'] >= T_FUSION else 'NON atteinte'}. "
        f"Réfuté si le centre mesuré de B atteint la fusion à 200 A.",
        "",
        "## 4. Portée et limites",
        "",
        "- Le champ EM **n'est pas re-résolu** pour la géométrie réduite : la méthode des "
        "images ne dépend que de µ_r et d'un plan infini. Tout l'effet prédit vient du "
        "masque d'empreinte appliqué après coup.",
        "- Le masque est un rectangle dur 0/1, sans frange : les valeurs aux chants sont "
        "les moins fiables.",
        "- θ* n'est pas recalibré pour la géométrie réduite (objet de #60, après mesure).",
        "- **Aucune source du corpus documentaire ne fait varier la longueur d'un "
        "concentrateur** (Mohan 2022 teste présence/absence et position de bobine, pas la "
        "longueur) : il n'y a pas d'appui bibliographique externe à cette prédiction.",
        "",
        "Ce qui est prédit ici, ce sont des **tendances et des rapports**. Les niveaux "
        "absolus de la colonne B ne sont pas validés.",
        "",
        f"Reproduire : `.venv/bin/python code/scripts/gen/{Path(__file__).name}`",
        "",
    ]
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    SORTIE.write_text("\n".join(lignes), encoding="utf-8")

    print(f"mesure A  : " + "  ".join(f"{t}={mesure_A[t]:.1f}" for t in ORDRE_TC))
    print(f"modele A  : " + "  ".join(f"{t}={modele_A[t]:.1f}" for t in ORDRE_TC))
    print(f"modele B  : " + "  ".join(f"{t}={modele_B[t]:.1f}" for t in ORDRE_TC))
    print(f"contraste : mesure A {contraste(mesure_A):.2f} | modele A {c_A:.2f} | modele B {c_B:.2f}")
    print(f"ecrit : {SORTIE}")


if __name__ == "__main__":
    main()
