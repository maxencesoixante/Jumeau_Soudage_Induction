<!--
SOURCE DE VÉRITÉ du corps de l'issue GitHub #66.
Éditer CE fichier, puis : .venv/bin/python code/scripts/gen/sync_issue.py 66
Ne pas éditer l'issue directement dans le navigateur : la prochaine synchro
écraserait la modification sans avertir.
Ce commentaire HTML est invisible dans l'issue rendue.
-->
> **Fusion du 2026-09-28** : cette issue absorbe **#72** (« Validation prospective — volet 160 A »). Les deux essais encadrent le 231 A déjà validé (#64), l'un en dessous, l'autre au-dessus, avec le même protocole et la même règle de validation à l'aveugle : une seule campagne, une seule mise en place au banc. Le contenu de #72 est le **volet bas** ci-dessous, celui de l'ancienne #66 le **volet haut**.

## Objectif

Tester le pouvoir prédictif du jumeau **de part et d'autre du 231 A**, déjà validé au cœur (pics intérieurs TC2/3/4 à ±12–20 °C, #64) :

| Volet | Courant | Ce qu'il teste |
|---|---|---|
| **Bas** (ex-#72) | **160 A** | la thermique pure, **sous la fusion** : montée, niveau et surtout **refroidissement**, sans l'écrêtage du plateau de fusion |
| **Haut** | **275 A** | l'**extrapolation** hors de la boîte de calibration (150–250 A) : loi en I², plafond de fusion |

Les deux volets partagent : le cycle semi-statique à 4 passes (mode opératoire serieA/B), des **prédictions figées avant la mesure**, et une validation **sans recalibration** (held-out pur).

![Domaine des essais réalisés](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/issue66/fig66_domaine.png?v=1)

*Tous les essais réalisés, par campagne, sur l'axe du courant. Zone grisée : boîte de calibration (150–250 A). Le 160 A est dans la boîte mais dans sa partie basse, où un seul essai existe (exp7 à 150 A) ; le 275 A est au-delà de tout ce qui a été mesuré.*

![Loi en I²](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/issue66/fig66_loi_I2.png?v=1)

*Ce que les deux volets testent sur la source : taux de chauffe mesuré au chant (exp7, élévation de 30 à 130 °C, min–max des répétitions) en fonction de I². L'ajustement R = k·I² − L (R² = 0,999, perte L = 3,4 °C/s) prévoit 12 °C/s à 160 A et 42 °C/s à 275 A.*

⚠️ **Les deux volets n'ont pas le même protocole de coupure** (voir le volet bas). Garder en revanche **la même disposition des TC** pour les deux, afin de ne pas confondre effet du courant et effet de la disposition : le volet haut prévoit la disposition v2 (TC1/TC5 au centre y = 20, TC2/3/4 au bord y = 0).

---

## Volet bas — 160 A (ex-#72)

Réaliser le **volet 160 A** de la validation prospective #64. Son critère de succès demande un accord prédit ↔ mesuré **pour 160 *et* 230 A** ; seul le **231 A** a été réalisé (26/08/2026).

### Pourquoi ce volet n'est pas redondant avec le 231 A

Le 231 A a validé le cycle **au cœur**, mais dans un régime où **le plateau de fusion écrête le point chaud** : la signature mesurée y est dominée par le changement de phase, ce qui masque une partie des écarts de pertes. À 160 A, l'interface reste **sous la fusion** sur la majeure partie du cycle — le modèle y est donc jugé sur sa thermique pure : montée, niveau, et surtout **refroidissement**, dont on sait qu'il est ~10 % trop lent.

C'est aussi le seul moyen de vérifier que la **loi en I²** tient en prédiction sur le cycle complet, et pas seulement sur le taux de chauffe au chant (où elle est déjà validée, R² = 0,999 sur cinq courants).

### ⚠️ Protocole de coupure : couper sur le point chaud, pas sur les TC de bord

Le protocole « couper quand le TC de bord atteint 390 °C » ne tient qu'**à haut courant**. D'après le jumeau (2026-08-27), à 160 A les TC de bord chauffent trop lentement : les amener à 390 °C demanderait 220 à 300 s de chauffe par passe, pendant lesquelles le point chaud d'interface monterait à **530–590 °C, bien au-delà de la dégradation**. À 160 A, il faut donc **piloter sur le point chaud** (couper à 390 °C au point chaud). Ordre de grandeur prédit : chauffes de 92 / 54 / 57 / 79 s, cycle d'environ 620 s, et TC de bord plafonnant vers 255–293 °C réels seulement.

![Protocoles de coupure](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/issue66/fig66_protocoles.png?v=1)

*Disposition des TC v2 et capteur qui commande la coupure de chaque passe (étoile) : point chaud au bord sous le spot à 160 A, TC de bord le plus proche à 275 A (TC2, TC3, TC4, TC4).*

⚠️ **Point pratique (2026-10-02) : la disposition v2 n'a aucun TC au point chaud.** À 160 A, la coupure doit se faire au bord sous chaque spot (x ≈ 16, 46, 76 et 106 mm, y = 0), alors que les TC de bord v2 sont entre les spots (x = 30, 60 et 90 mm). Deux options : **ajouter des TC sous les spots**, ou **couper à durée fixe** sur les durées de chauffe prédites (de l'ordre de 92 / 54 / 57 / 79 s d'après l'analyse du 27/08), à figer avec les autres prédictions avant la mesure.

### À faire

1. **Figer les prédictions AVANT la mesure** — c'est ce qui fait la valeur de #64 : durée de chauffe par passe, temps de refroidissement jusqu'à Tg (159 °C), pics aux 5 TC, pour le cycle 4 passes à 160 A. Prédictions publiées ici et **non modifiées ensuite**.
2. **Réaliser le cycle au banc**, même mode opératoire que le 231 A (serieA/B, 4 empreintes séquentielles), avec la coupure sur le point chaud.
3. **Comparer** prédit ↔ mesuré : durées de chauffe, refroidissement, pics, et l'écart au seuil de dégradation jugé à la **dose** (temps × température) et non au pic.

### Critère de succès du volet bas

Celui de #64, appliqué à 160 A : accord **dans la bande de bruit capteur**, pics TC à ±10–15 %, et un **verdict chiffré** sur le cycle complet — chauffe *et* refroidissement.

⚠️ **Le refroidissement est l'observable qui compte ici.** Le modèle refroidit ~10 % trop lentement (écart connu et cadré) ; à bas courant, sans l'écrêtage de la fusion, cet écart devient directement visible sur le temps de retour à Tg.

---

## Volet haut — 275 A

Tester le **pouvoir prédictif en EXTRAPOLATION** du jumeau : réaliser un essai réel **hors du domaine de calibration (150-250 A)**, à **275 A**, et confronter au modèle en **held-out pur** (aucune recalibration). C'est le point le plus informatif restant — la loi source ∝ I² et le paramètre effectif `h_bord_x0` n'ont jamais été confrontés hors de la boîte 150-250 A.

> Décision prise via **analyse multi-agents** (`validation-data-engineer` + `calibration-uq-specialist`), tous deux concluant **275 A plutôt qu'une répétition à 230 A**. Cette issue archive leurs recommandations.

### Décision : 275 A hors-domaine, PAS une répétition 230 A
Pourquoi pas répéter 230 A :
- **2 essais 231 A déjà réalisés** (v1 tout au bord y=0 ; v2 TC1/TC5 au centre y=20) → les résidus se répètent dans le même sens et la même amplitude ⇒ **biais modèle systématique, pas du bruit capteur**. Le plancher de bruit capteur est ~2 ordres de grandeur sous les résidus (RMSE 36-71, pics ±12-20 °C).
- **230 A est déjà validé en aveugle** (issue #64) ; held-out intra-domaine (exp7 150-250 A, exp9 175-250 A, serieA/B 250 A) **saturé** (recalibration jointe NO-GO, #65).
- Une répétition réduirait un terme d'incertitude **qui n'est pas le facteur limitant**.

Pourquoi 275 A :
- **+10 % seulement** au-delà de la borne haute (250 A) → extrapolation **modeste**, proche de l'interpolation.
- Mais la **loi I² prédit ~+43 % de flux de chauffe vs 230 A** ((275/230)²) → **écart largement mesurable = test discriminant** de la loi I² ET du plafond de fusion (le modèle prédit-il toujours un plafond d'interface ~508 °C, ou un dépassement si le flux monte plus vite que la fusion ne peut absorber ?).
- Seule zone où l'incertitude prédictive du jumeau est **la moins contrainte**.

### Protocole du volet haut (à suivre)
- [ ] **~2 tirs à 275 A** (pas 1 isolé, pas 3 répétitions 230 A) → donne simultanément (a) le test d'extrapolation et (b) une estimation minimale de la **dispersion tir-à-tir (process)**, non capturée par le σ bruit actuel.
- [ ] **Même layout de TC que l'essai v2** : TC1/TC5 au **centre y=20**, TC2/3/4 au **bord y=0** → ne pas confondre effet-courant et effet-layout.
- [x] **Prédictions figées A PRIORI (chiffrées) AVANT l'essai** — FAIT (ci-dessous) → test réellement falsifiable. À prédire : pic de chaque TC intérieur, position/amplitude du plateau de fusion, température d'interface (point chaud) plafonnée, ratio de flux I².
- [ ] **Held-out PUR** : quel que soit le résultat (tenue ou régression), **ne PAS élargir la boîte de calibration** ni retoucher `facteur_couplage`/`h_bord_x0`. En cas d'écart, diagnostiquer avec `thermal-solver-engineer` / `induction-em-engineer` (règle « une calibration, validation aveugle sur le reste »).

### ⚠️ Avertissement procédé
À 275 A la **marge à la dégradation (450 °C) est très étroite (~2,3 s au modèle)** → coupure précise obligatoire, risque de dégradation si le seuil est raté. Le protocole « couper sur TC=390 » fonctionne bien à haut courant (les TC de bord montent vite), mais surveiller de près.

### Critère de succès du volet haut
Prédiction figée ↔ mesure 275 A **dans la bande** (pics TC intérieurs ±15-20 °C, plateau de fusion au bon niveau) **sans recalibration** = pouvoir prédictif en extrapolation confirmé. Écart net et systématique = borne supérieure du domaine de validité identifiée (résultat utile aussi).

### 🔒 Prédiction FIGÉE 275 A (a priori — layout v2)

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

---

## Liens
- Parent : #64 (validation 231 A, prédictions figées, modèle de fusion ; volet 160 A demandé par son critère de succès).
- Held-out intra-domaine : #65 (NO-GO recalibration).
- Données 231 A : `donnees/data/exp10_cycle-semistatique_231A_2026-08-26/` (v1 bord + v2 y20).
- Prédiction 275 A existante (layout y=0 à adapter en y=20) : `fig_cycle_parfait_semistatique_275A.png`, `gen_cycle_parfait_semistatique.py`.
- Mode opératoire du volet bas : `biblio/labo/synthese_issue67_validation_231A_2026-08-31.md`. Critère de dégradation (dose) : `biblio/modele/critere_dose_degradation.md`.
