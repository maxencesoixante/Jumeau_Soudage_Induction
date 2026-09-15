<!--
ARCHIVE du corps de l'issue GitHub #65, CLOSE le 2026-08-27.
Instantané versionné d'un record historique : on ne le republie pas, l'issue
close fait foi. Le script sync_issue.py refuse d'ailleurs de pousser vers une
issue close sans --forcer-close.
Ce commentaire HTML n'est pas présent dans l'issue elle-même.
-->
## Objectif
La recalibration jointe **coin + refroidissement global** menée sur le seul essai **231 A** (cf. #64) donne un θ\* qui améliore nettement le cycle 231 A (RMSE moyen 77,6 → 63,5). Avant toute adoption au **canonique**, il faut un **test held-out** : ce θ\* (calibré sur 231 A **uniquement**) **régresse-t-il** les familles qui n'ont PAS servi au fit — **exp7, exp9, serieA/B** ?

> Garde-fou historique : une précédente consolidation multi-familles (θ\*_consolidé) était **NO-GO** (régressait les courants intermédiaires held-out). Même prudence ici : un gain mono-essai ne vaut adoption que s'il **tient hors échantillon**.

## θ\* à tester (recalibré 231 A, variante — canonique intact)
| Paramètre | Canonique | Recalibré (Δ\*) |
|---|---|---|
| `facteur_couplage` | 6.0123 | **6.5358** |
| `h_haut` | 30.087 | 30.087 (inchangé) |
| `h_bas_2d` | 37.424 | **124.872** |
| `h_bord_x0` | 250 | **2.4 (~0)** |

Sauvé dans `code/scripts/gen/_theta_coin_refroid.npy`. Scripts d'origine : `calibrer_coin_refroid_231A.py`, `gen_valider_recalibration_231A.py`.

## Méthode (exécutable)
`valider.py` accepte tous les leviers en CLI. Lancer les **mêmes essais held-out** sous les deux jeux et comparer RMSE par essai / par TC :

```bash
ESSAIS="exp7_150A exp7_176A exp7_200A exp7_225A exp7_250A \
        exp9_175A_monospot exp9_200A_monospot exp9_226A_monospot exp9_250A_monospot \
        serieA_A-1 serieA_A-3 serieB_B-2"

# (a) canonique
python3 code/scripts/valider.py --modele 2D --facteur 6.0123 \
    --h-haut 30.087 --h-bas-2d 37.424 --h-bord-x0 250 --essais $ESSAIS

# (b) recalibré Δ*
python3 code/scripts/valider.py --modele 2D --facteur 6.5358 \
    --h-haut 30.087 --h-bas-2d 124.872 --h-bord-x0 2.4 --essais $ESSAIS
```

Held-out strict = **toutes** ces familles (le fit n'a vu QUE 231 A). Dresser un tableau RMSE (a) vs (b) par essai + par TC, et le ΔRMSE.

## Critère de décision
- **Adopter Δ\*** au canonique **seulement si** : RMSE global held-out **ne régresse pas** (idéalement s'améliore) sur exp7/exp9/serieA/B, sans détériorer un essai particulier de > ~10–15 °C.
- **Sinon** : garder Δ\* en variante 231 A documentée, et traiter les **causes structurelles** (ci-dessous) plutôt que les paramètres effectifs.

## Limites structurelles à traiter (révélées par la recalibration, cf. #64)
Ces deux points ne sont **pas** corrigibles par (fac, h_bas_2d, h_bord_x0) et sont la vraie raison du plafond de précision :
1. **Coin aigu lissé** — le vrai coin x=0 est un point chaud *aigu* (gradient 392→271 °C sur 30 mm) que le modèle aplatit → **étalement in-plane `k_plan`** trop rapide. Piste : `k_plan` réduit / anisotrope (kx≠ky) ; vérifier held-out (levier connu comme régressant — prudence).
2. **Refroidissement à deux échelles** — chute rapide de surface **+** plancher chaud du bulk (~130–150 °C) ; un `h_bas_2d` lumpé unique ne capte pas les deux (fixe la chute, sur-refroidit le plancher). Piste : perte à deux constantes de temps / capacité bulk, ou modèle 3D d'épaisseur pour le plancher.

## Livrables
- [x] Tableau RMSE held-out (a) canonique vs (b) Δ\* (+ figure de synthèse) — FAIT.
- [x] Verdict **GO / NO-GO** d'adoption de Δ\* au canonique, chiffré — **NO-GO** (voir ci-dessous).
- [x] Si NO-GO : note ciblant `k_plan` (coin) et le refroidissement 2 échelles comme vrais correctifs — voir « Suite ».

## Liens
- Parent : #64 (validation 231 A + section « Recalibration jointe »).
- Données réelles : `donnees/data/exp10_cycle-semistatique_231A_2026-08-26/`.
- Précédent NO-GO à ne pas rejouer aveuglément : consolidation θ\*_consolidé (courants intermédiaires held-out).

---

## ✅ Résultat du held-out — **VERDICT : NO-GO**

`valider.py` 2D sur les 12 essais, sous canonique vs Δ\* (`code/scripts/gen/gen_heldout_recalibration.py`).

| Essai | Canon. | Δ\* recal | ΔRMSE |
|---|---|---|---|
| exp7_150A | 25.4 | 25.3 | −0.1 |
| exp7_176A | 24.4 | 23.4 | −1.0 |
| exp7_200A | 21.8 | 19.8 | −2.0 |
| exp7_225A | 21.5 | 24.3 | +2.8 |
| exp7_250A | 22.6 | 23.0 | +0.4 |
| exp9_175A | 11.3 | 13.7 | +2.4 |
| exp9_200A | 12.1 | 15.4 | +3.3 |
| exp9_226A | 7.8 | 7.3 | −0.5 |
| exp9_250A | 10.1 | 12.5 | +2.4 |
| **serieA_A-1** | 36.3 | **54.8** | **+18.5** |
| **serieA_A-3** | 33.0 | **48.3** | **+15.3** |
| **serieB_B-2** | 65.3 | **82.2** | **+16.9** |

**Moyennes par famille** : exp7 23.1 → 23.2 (**+0.0**) · exp9 10.3 → 12.2 (**+1.9**) · **serieA/B 44.9 → 61.8 (+16.9)**. Held-out global : **24.3 → 29.2 (+4.9)**.

![Held-out canonique vs Δ*](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_heldout_recalibration_231A.png)

**Lecture** : exp7 est neutre, exp9 se dégrade un peu, mais les familles **les plus proches du 231A** — serieA/B, semi-statique multi-passes — **régressent de +15 à +19 °C**. Le fort refroidissement global (`h_bas_2d` 37→125) qui collait au 231A **sous-chauffe** les autres campagnes (pics serieB Δ\* ~290-305 vs mesuré 353-366). Confirme le pattern θ\*_consolidé : un gain mono-essai ne tient pas hors échantillon.

**Décision : Δ\* NON adopté au canonique.** La variante 231A reste documentée (#64). Le `h_bas_2d` élevé n'est pas universel → la vitesse de refroidissement rapide observée au 231A est probablement **spécifique au montage** (contact support), pas un paramètre modèle global.

## Suite — les vrais correctifs sont structurels
Le held-out confirme que les paramètres effectifs (fac, h_bas_2d, h_bord_x0) ne peuvent pas généraliser le gain 231A. Les deux causes de fond (cf. #64) restent à traiter :
1. **Coin aigu** → `k_plan` (étalement in-plane) : anisotrope kx≠ky ou k(T), **avec held-out obligatoire** (levier connu comme régressant).
2. **Refroidissement 2 échelles** (chute surface + plancher bulk) → perte à deux constantes de temps / capacité bulk, ou passage 3D d'épaisseur.
+ **Montage** : instrumenter/mesurer la condition de refroidissement réelle (contact support) pour savoir si `h_bas` varie d'un essai à l'autre.

