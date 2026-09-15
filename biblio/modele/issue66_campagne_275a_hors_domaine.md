<!--
SOURCE DE VÉRITÉ du corps de l'issue GitHub #66.
Éditer CE fichier, puis : .venv/bin/python code/scripts/gen/sync_issue.py 66
Ne pas éditer l'issue directement dans le navigateur : la prochaine synchro
écraserait la modification sans avertir.
Ce commentaire HTML est invisible dans l'issue rendue.
-->
## Objectif
Tester le **pouvoir prédictif en EXTRAPOLATION** du jumeau : réaliser un essai réel **hors du domaine de calibration (150-250 A)**, à **275 A**, et confronter au modèle en **held-out pur** (aucune recalibration). C'est le point le plus informatif restant — la loi source ∝ I² et le paramètre effectif `h_bord_x0` n'ont jamais été confrontés hors de la boîte 150-250 A.

> Décision prise via **analyse multi-agents** (`validation-data-engineer` + `calibration-uq-specialist`), tous deux concluant **275 A plutôt qu'une répétition à 230 A**. Cette issue archive leurs recommandations.

## Décision : 275 A hors-domaine, PAS une répétition 230 A
Pourquoi pas répéter 230 A :
- **2 essais 231 A déjà réalisés** (v1 tout au bord y=0 ; v2 TC1/TC5 au centre y=20) → les résidus se répètent dans le même sens et la même amplitude ⇒ **biais modèle systématique, pas du bruit capteur**. Le plancher de bruit capteur est ~2 ordres de grandeur sous les résidus (RMSE 36-71, pics ±12-20 °C).
- **230 A est déjà validé en aveugle** (issue #64) ; held-out intra-domaine (exp7 150-250 A, exp9 175-250 A, serieA/B 250 A) **saturé** (recalibration jointe NO-GO, #65).
- Une répétition réduirait un terme d'incertitude **qui n'est pas le facteur limitant**.

Pourquoi 275 A :
- **+10 % seulement** au-delà de la borne haute (250 A) → extrapolation **modeste**, proche de l'interpolation.
- Mais la **loi I² prédit ~+43 % de flux de chauffe vs 230 A** ((275/230)²) → **écart largement mesurable = test discriminant** de la loi I² ET du plafond de fusion (le modèle prédit-il toujours un plafond d'interface ~508 °C, ou un dépassement si le flux monte plus vite que la fusion ne peut absorber ?).
- Seule zone où l'incertitude prédictive du jumeau est **la moins contrainte**.

## Protocole recommandé (à suivre)
- [ ] **~2 tirs à 275 A** (pas 1 isolé, pas 3 répétitions 230 A) → donne simultanément (a) le test d'extrapolation et (b) une estimation minimale de la **dispersion tir-à-tir (process)**, non capturée par le σ bruit actuel.
- [ ] **Même layout de TC que l'essai v2** : TC1/TC5 au **centre y=20**, TC2/3/4 au **bord y=0** → ne pas confondre effet-courant et effet-layout.
- [x] **Prédictions figées A PRIORI (chiffrées) AVANT l'essai** — FAIT (ci-dessous) → test réellement falsifiable. À prédire : pic de chaque TC intérieur, position/amplitude du plateau de fusion, température d'interface (point chaud) plafonnée, ratio de flux I².
- [ ] **Held-out PUR** : quel que soit le résultat (tenue ou régression), **ne PAS élargir la boîte de calibration** ni retoucher `facteur_couplage`/`h_bord_x0`. En cas d'écart, diagnostiquer avec `thermal-solver-engineer` / `induction-em-engineer` (règle « une calibration, validation aveugle sur le reste »).

## ⚠️ Avertissement procédé
À 275 A la **marge à la dégradation (450 °C) est très étroite (~2,3 s au modèle)** → coupure précise obligatoire, risque de dégradation si le seuil est raté. Le protocole « couper sur TC=390 » fonctionne bien à haut courant (les TC de bord montent vite), mais surveiller de près.

## Critère de succès
Prédiction figée ↔ mesure 275 A **dans la bande** (pics TC intérieurs ±15-20 °C, plateau de fusion au bon niveau) **sans recalibration** = pouvoir prédictif en extrapolation confirmé. Écart net et systématique = borne supérieure du domaine de validité identifiée (résultat utile aussi).

## Liens
- Parent : #64 (validation 231 A, prédictions figées, modèle de fusion).
- Held-out intra-domaine : #65 (NO-GO recalibration).
- Données 231 A : `donnees/data/exp10_cycle-semistatique_231A_2026-08-26/` (v1 bord + v2 y20).
- Prédiction 275 A existante (layout y=0 à adapter en y=20) : `fig_cycle_parfait_semistatique_275A.png`, `gen_cycle_parfait_semistatique.py`.

---

## 🔒 Prédiction FIGÉE 275 A (a priori — layout v2)

Modèle 2D **canonique** (adopté), pilotage réel **couper quand le TC de bord proche du spot (TC2/TC3/TC4) atteint 390 °C réel** (= 360 °C modèle, biais −30 °C), puis refroid.→Tg, avance. Positions v2 : TC1/TC5 au centre y=20, TC2/3/4 au bord y=0. Script `code/scripts/gen/gen_cycle_275A_v2.py`.

![Prédiction figée 275A v2](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_cycle_275A_v2_prediction.png)

**A priori FIABLE (à confronter) :**

| Grandeur | Prédiction |
|---|---|
| Dwells de chauffe (P1/P2/P3/P4) | **58 / 45 / 45 / 58 s** |
| Cycle total | **986 s (~16 min)** |
| Pic **TC2/TC3/TC4** (bord intérieur) | **~396–400 °C réel** (ce sont les TC de contrôle) |
| Refroidissements inter-passes (→Tg) | 163 / 189 / 191 / 237 s |

**Température d'interface (point chaud, non mesurée)** : canonique **887 °C** (s'emballe, marge à 450 °C **négative**) ; le **modèle fusion la plafonnerait ~510 °C** — 275 A donnera un test discriminant de ce plafond.

**⚠️ Mises en garde :**
- **TC1 et TC5 NON fiables** : ils sont aux **bords en x (x=0 / x=120)** où la source du modèle est mal distribuée (artefact du solveur ψ=0 : source concentrée au centre y=20 au lieu du profil M bord-piqué). Le modèle les sur-prédit massivement (TC5 ~825 °C) — **à ignorer**. Confronter uniquement **TC2/3/4**.
- **Marge à la dégradation étroite/négative** à 275 A → coupure précise obligatoire, risque réel de dégradation si le seuil est raté.

**Critère falsifiable** : si TC2/3/4 réels ≈ 396–400 °C aux dwells ~45–58 s **sans recalibration** → extrapolation de la loi I² confirmée. Écart net → borne du domaine de validité identifiée.

