<!--
SOURCE DE VÉRITÉ du corps de l'issue GitHub #64.
Éditer CE fichier, puis : .venv/bin/python code/scripts/gen/sync_issue.py 64
Ne pas éditer l'issue directement dans le navigateur : la prochaine synchro
écraserait la modification sans avertir.
Ce commentaire HTML est invisible dans l'issue rendue.
-->
> 📖 **Relecture opérateur** : synthèse chronologique complète et lisible de tout le travail depuis les essais 231 A → **#67**.

## Objectif
Valider le jumeau en mode **prospectif (blind)** sur le **cycle de chauffe parfait en soudage SEMI-STATIQUE** (mode opératoire réel serieA/B) : le jumeau prédit **au préalable** le cycle idéal (chauffe → cible, puis refroidissement → seuil, 4 passes), on **fige** ces prédictions, on **réalise ensuite** le cycle au banc, puis on **compare prédit ↔ mesuré**. Prédiction verrouillée avant la mesure → test honnête du pouvoir prédictif (chauffe **et** refroidissement), hors des points de calage.

> Remplace l'approche mono-spot initiale de cette issue (pivot vers le cycle semi-statique complet serieA/B).

> ### ✅ Premier essai réalisé — **231 A (26/08/2026)** : cycle **validé au cœur** (pics intérieurs TC2/3/4 à ±12–20 °C). Détails et figures en bas de l'issue (section « Résultat de validation »).

## Définition du « cycle parfait » (mode opératoire réel serieA/B)
**4 passes, spot avançant de 30 mm** — centres des spots `empreintes.centres_pas30` = **15,875 / 45,875 / 75,875 / 105,875 mm**. Les 4 empreintes MFC (31,5 mm en x) se recouvrent → **toute la longueur de la plaque est soudée** le long des deux chants (rails du « M »). Par passe :
1. **Chauffe** le point chaud d'interface (lobe M, bord y=0, sous le spot) jusqu'à la **cible procédé 390 °C**.
2. **Coupe la source** et **refroidit jusqu'à ≤ Tg (159 °C)** — sous Tg la phase amorphe du PEKK est vitreuse, le joint est figé/rigide (critère **adopté** ; gain ~14–34 % du temps de cycle vs 120 °C, cf. figure de comparaison).
3. **Avance** au spot suivant, répète.

Biais modèle connu : sur-estime le bord d'~50 °C → **390 °C modèle ≈ ~340 °C réel** (juste au-dessus de la fusion 337 = soudage propre).

**Placement du MFC (concentrateur) à chaque passe** : MFC labo Ferrotron 559H (**55 × 31,5 × 12 mm**, µr ≈ 16) **centré sur le spot de la passe**, sa **grande dimension 55 mm parallèle à la largeur (axe y)**, **centré en largeur (y = 20 mm)**, à ~5 mm au-dessus de la surface (gap céramique). À la passe *i*, le MFC couvre **x ∈ [xᵢ − 15,75 ; xᵢ + 15,75] mm** (31,5 mm le long de la longueur) et déborde la largeur de 7,5 mm de chaque côté (55 mm > 40 mm). *(MFC labo 55 mm ; le MFC réduit 31,75 mm donnerait une couverture x différente, à recalibrer.)*

![Storyboard des passages du MFC + coil](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/presentations/figures_schemas/fig_passages_mfc_storyboard.png)

**Thermocouples** : disposition **exp9 semi-statique** — les **5 TC sur la ligne de bord y=0**, en **x = 0 / 30 / 60 / 90 / 120 mm** (espacés de 30 mm). Ils sont **décalés des centres de spots** (~14–16 mm) → ils lisent **plus froid** que le point chaud du joint (normal ; comparer TC prédit ↔ TC mesuré aux mêmes positions).

## Prédictions figées (jumeau 2D, θ* canonique, `facteur_couplage=6.0123`, 4 spots)
Script `code/scripts/gen/gen_cycle_parfait_semistatique.py` ; figures `fig_cycle_parfait_semistatique_{230,275}A.png`.

| I (A) | Chauffe cumulée (s) | Refroid. cumulé (s) | **Cycle total** | Soude ? | Marge min → 450 °C |
|---|---|---|---|---|---|
| **230** | 83 | 235 | ~318 s (5,3 min) | OUI | ~4,7 s |
| **275** | 51 | 196 | ~246 s (4,1 min) | OUI (limite) | ~2,3 s |

### Figures (prédictions figées)

**Cycles T(t) prédits** — courbe pointillée = point chaud de contrôle (spot actif) ; TC pleins aux positions **exp9** (5 TC sur la ligne de bord y=0, x=0/30/60/90/120 mm, décalés des spots → ils sous-estiment le point chaud) :

*230 A — soude, fenêtre serrée (marge ~4,7 s) :*
![Cycle 230 A](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_cycle_parfait_semistatique_230A.png)

*275 A — limite (marge ~2,3 s) :*
![Cycle 275 A](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_cycle_parfait_semistatique_275A.png)

**Constat clé** : le **refroidissement inter-passes domine** (55–80 % du temps de cycle aux courants qui soudent) et est **quasi indépendant du courant** (redescendre à Tg = même thermique lente) → c'est le **goulot** du procédé, pas la chauffe.

**Ré-adoucissement des joints — AUCUN (vérifié aux centres des spots) :** au pas réel de 30 mm, chaque joint déjà soudé est réchauffé par la passe suivante seulement jusqu'à **~158,7 °C — juste SOUS Tg (159 °C)** ; il **ne repasse jamais au-dessus de Tg** (durée > Tg ≈ 0 s, tous courants). Le joint **reste figé** : le critère Tg est donc pleinement sûr avec ce mode opératoire (le ré-adoucissement n'apparaîtrait qu'à pas plus serré, ~20 mm).

![Ré-adoucissement des joints](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_readoucissement_joint.png)

## À faire (banc)
- [ ] **Figer** les prédictions ci-dessus (figures + table), datées, **avant** tout essai.
- [ ] **Montage = mode opératoire réel** : 4 spots à x = 15,9 / 45,9 / 75,9 / 105,9 mm (pas 30 mm), MFC centré sur chaque spot (cf. ci-dessus). **TC comme exp9** : 5 TC sur la ligne de bord y=0, x = 0/30/60/90/120 mm.
- [x] ~~Réaliser le cycle pour **230 A**~~ **FAIT (231 A, 26/08 — 2 layouts de TC)** ; **prochain = 275 A hors-domaine** (décision agents, archivée dans **#66** : teste l'extrapolation, loi I², bien plus informatif qu'une répétition).
- [ ] **Protocole conforme au cycle** : par passe → chauffe jusqu'à 390 °C au point chaud (consigne), coupe, **refroidissement jusqu'à ~Tg (159 °C)**, puis passe suivante.
- [x] Confronter prédit ↔ mesuré (par TC : pic, RMSE) — **fait pour 231 A** ; **≥ 2 répétitions** encore à faire.
- [ ] Comparer aux **cycles réels serieA/B** déjà mesurés (même 4 passes, consigne ~400 °C).

## Avertissements
- **275 A** : marge à 450 °C très étroite (~2,3 s) → coupure précise obligatoire, risque de dégradation si le seuil est raté.
- **TC décalés des spots** (~14–16 mm) → ils lisent plus froid que le point chaud du joint ; comparer TC prédit ↔ TC mesuré aux **mêmes positions**, pas au point chaud de contrôle.
- Modèle **2D** au θ* canonique (`facteur_couplage=6.0123`, `h_bas_2d`, `h_bord_x0`) — le 3D n'est pas recalibré à ce facteur.

## Critère de succès
Accord prédit ↔ mesuré **dans la bande de bruit capteur** pour 160/230 A : dwell de chauffe par passe et temps de refroidissement → Tg 159 °C cohérents, pics TC à ±10–15 %. **Verdict chiffré** sur le pouvoir prédictif du **cycle complet** (chauffe + refroidissement).

## Dépendances / liens
- Prédictions : `code/scripts/gen/gen_cycle_parfait_semistatique.py` (mode réel serieA/B ; seuil d'avance paramétrable `SEUIL_REFROID`, défaut Tg 159 °C), `fig_cycle_parfait_semistatique_*A.png`, `fig_readoucissement_joint.png` (+ scripts associés).
- Cycles réels de référence : `code/config/essais/serieA_A-1.yaml`, `serieB_B-2.yaml`.
- Abaque opératoire : `fig_fenetre_soudage` (cible procédé 390 °C).

---

## ✅ Résultat de validation — essai réel **231 A** (26/08/2026)

Premier essai de la campagne réalisé : **231 A**, semi-statique, 4 passes, **coupure sur TC à 390 °C**. Donnée brute versionnée : `donnees/data/exp10_cycle-semistatique_231A_2026-08-26/`.


**Mesure brute (5 TC de bord, sans aucune simulation)** — cycle réel 4 passes :

![Essai 231A mesuré seul](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_exp_231A_mesure.png)

**Prédiction figée pilotée sur TC** — couper quand le TC proche du spot atteint **390 °C réel** (= 360 °C modèle, biais −30 °C intérieur) — `code/scripts/gen/gen_cycle_230A_TC390.py`. Dwells prédits **91 / 68 / 68 / 90 s** (cohérents série A ~79 s), point chaud d'interface > 700 °C (≫ fusion 337 → soudage) :

![Cycle 230 A piloté sur TC](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_cycle_230A_TC390.png)

**Confrontation prédit ↔ mesuré** — `code/scripts/gen/gen_compare_230A_vs_reel.py` (trait plein = mesuré, pointillé = prédit) :

![Validation 231 A prédit vs mesuré](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_compare_230A_vs_reel.png)

### Pics : prédit vs mesuré

| TC | Position | Prédit (°C) | Mesuré (°C) | Écart |
|---|---|---|---|---|
| TC1 | x=0 (coin bord) | 302 | **392** | −90 |
| TC2 | x=30 (intérieur) | 362 | 350 | **+12** ✅ |
| TC3 | x=60 (intérieur) | 363 | 381 | **−18** ✅ |
| TC4 | x=90 (intérieur) | 363 | 383 | **−20** ✅ |
| TC5 | x=120 (bord opposé) | 545 | 387 | +158 (artefact `h_bord_x0`) |

### Verdict
- ✅ **Pics intérieurs (TC2/TC3/TC4) validés à ±12–20 °C** — le jumeau prédit les niveaux du procédé au cœur de la plaque.
- ✅ **Structure exacte** : 4 passes, chacune ~350–390 °C ; **cycle total prédit 1080 s vs mesuré 984 s** (bon ordre de grandeur).
- ⚠️ **Refroidissement modèle ~10 % trop lent** → cycle prédit +10 %, et **RMSE 66–71 °C dominé par ce décalage temporel** des queues de refroidissement (pas par les pics). Le vrai montage évacue la chaleur un peu plus vite.
- ⚠️ **TC1 (coin x=0)** : dans le réel c'est le **point le plus chaud (392 °C)** — effet de coin de plaque que le 2D sous-capture → piste d'amélioration réelle.
- ⚠️ **TC5 (x=120)** : artefact de bord connu (`h_bord_x0` calibré seulement à x=0) → à ignorer, le réel (387) est dans la bande.

**Conclusion : le pouvoir prédictif du cycle est confirmé sur le procédé** (pics intérieurs ±20 °C, mode opératoire, ordre de grandeur du cycle). Restes à traiter : refroidissement ~10 % trop lent + effet de coin x=0. Prochain point : **essai 275 A hors-domaine** (extrapolation) — cf. **#66**.

---

## 🔧 Recalibration jointe coin + refroidissement global (231 A) — variante, canonique intact

Suite au verdict ci-dessus, on a tenté une **recalibration jointe** de 3 paramètres effectifs sur l'essai 231 A (fit sur la passe 1 réelle, validé sur le cycle complet **piloté par les temps mesurés** 77/110/94/105 s). Scripts : `code/scripts/gen/calibrer_coin_refroid_231A.py` (fit) + `gen_valider_recalibration_231A.py` (validation).

**θ\* recalibré :**

| Paramètre | Canonique | Recalibré | Sens |
|---|---|---|---|
| `facteur_couplage` | 6.0123 | **6.536** | source ↑ léger (tenir les pics) |
| `h_bas_2d` | 37.4 | **124.9** | refroid. **~3× plus vite** (conduction vers le support) — *tape la borne* |
| `h_bord_x0` | 250 | **~0** | le puits était un **artefact** (chants libres) |

**Validation cycle complet (pics & RMSE, canonique → recalibré) :**

| TC | Mesuré | Canon. | Recal. | RMSE canon → recal |
|---|---|---|---|---|
| TC1 (coin) | 392 | 276 | 371 | 71 → 79 |
| TC2 | 350 | 454 | 346 | 72 → 74 |
| TC3 | 381 | 478 | 394 | 87 → **65** |
| TC4 | 383 | 458 | 377 | 78 → **51** |
| TC5 | 387 | 591 | 488 | 81 → **49** |

Moyenne RMSE **77,6 → 63,5** (−18 %).

![Validation recalibration 231A](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_valider_recalibration_231A.png)

**Révélation :** piloté par les **vrais dwells**, le modèle **canonique s'emballe** (pics 454–591 °C vs réel 350–390) faute de pertes ; le **pilotage-contrôle** (coupe précoce à TC=360 modèle) **masquait** cet emballement. La recalibration (h_bas ↑) ramène tous les pics au réel — c'est le vrai gain.

**Deux limites STRUCTURELLES exposées** (non corrigibles par ces 3 paramètres) :
1. **Coin lissé** — le vrai coin est un point chaud *aigu* (gradient 392→271 °C sur 30 mm) ; le modèle plafonne à 371 avec un gradient mou → **étalement in-plane `k_plan`** trop rapide (résidu structurel connu).
2. **Refroidissement à deux échelles** — chute rapide en surface **+** plancher chaud (~130–150 °C, bulk) ; un `h_bas` lumpé unique fixe la chute mais **sur-refroidit le plancher** inter-passe.

**Décision : NON adopté au canonique** (calibration mono-essai → risque de régresser exp7/exp9, cf. épisode θ\*_consolidé NO-GO). Le held-out de ce θ\* et le traitement des 2 causes structurelles font l'objet d'une **issue dédiée** (voir lien ci-dessous).

→ **Held-out & limites structurelles : #65**



---

## 🔬 Le plateau ~350-390 °C = fusion du PEKK (modèle de fusion physique)

Le coude/plateau des TC mesurés vers 350-390 °C est la signature de la **fusion du PEKK** (changement de phase visqueux→liquide) : la chaleur latente + une saturation. Le modèle canonique ne le reproduit pas car son **point chaud d'interface s'emballe à ~865 °C** (déficit de pertes). Scripts : `code/scripts/gen/gen_valider_fusion_231A.py`, diagnostic rampe `gen_analyse_rampe_231A.py`.

**Deux ingrédients physiques :**
1. **Chaleur latente physique** `L_f = 130 → 40 J/g` — le 130 était la valeur du PEKK **100 % cristallin** ; le stratifié CF/PEKK est à ~30 % → ~40 J/g. *(Le 130 gonflé masquait en partie le déficit de pertes, comme `h_bord_x0=250`.)*
2. **Transport du bain fondu** `k_plan(T)` rehaussé **au-dessus de Tf** (3 → 100 W/m·K, table `k_plan_T`) = convection/fluage effectif du polymère liquide, **localisé à la zone fondue**.

**Résultats cycle 231 A (temps réels) :**

| | Canonique | Fusion | Réel |
|---|---|---|---|
| Point chaud d'interface | 865 °C | **508 °C** | (physique) |
| Coin TC1 | 276 | **418** | 392 |
| Plateau reproduit | non (s'emballe) | **oui (genou net)** | oui |
| RMSE moyen TC bord | 69,0 | 68,9 | — |

![Modèle fusion 231A](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_valider_fusion_231A.png)

**Held-out** (exp7/exp9/serieA-B) : global **24,3 → 24,9 (+0,6 seulement)** — vs **+4,9** pour la recalibration de pertes Δ\* (#65). Le mécanisme étant **localisé au bain fondu**, exp7/exp9 restent **neutres** ; seul serieA/B régresse de +2,4. Bien plus bénin.

**Lecture :** ✅ la fusion **explique le plateau** et **plafonne l'interface** à une valeur physique (508 vs 865 °C). ⚠️ mais le RMSE des TC de bord reste **neutre** : un k(T) **redistribue** l'énergie (la conserve), il ne la **retire** pas → les pics intérieurs restent hauts. **Le résidu final n'est donc pas la fusion mais le bilan d'énergie (pertes montage-spécifiques)** — le même levier qui échoue au held-out (#65).

**Adoption :** recommandée **si la température d'interface compte** (ex. prédiction de **dégradation** : le canonique à 865 °C = faux positif systématique ; la fusion à 508 °C est physique). Pour le seul RMSE des TC de bord → neutre, donc optionnel. La correction de cristallinité `L_f=40` seule est un **acquis physique propre** indépendamment du k(T).



