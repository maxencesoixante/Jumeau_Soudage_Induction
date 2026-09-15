<!--
ARCHIVE du corps de l'issue GitHub #67, CLOSE le 2026-08-31.
Instantané versionné d'un record historique : on ne le republie pas, l'issue
close fait foi. Le script sync_issue.py refuse d'ailleurs de pousser vers une
issue close sans --forcer-close.
Ce commentaire HTML n'est pas présent dans l'issue elle-même.
-->
# Synthèse — Jumeau numérique CF/PEKK depuis les essais réels 231 A

> Note de relecture pour l'opérateur. Récit chronologique et factuel de tout le travail mené sur le jumeau thermique depuis les essais réels du 26/08. Tout ce qui suit est **acquis**. Les figures sont en bas de chaque étape.

---

## TL;DR

- ✅ **Le jumeau est fiable** sur les thermocouples **intérieurs TC2/TC3/TC4** (positions x = 30 / 60 / 90 mm) : pics reproduits à **±12–20 °C**. C'est sur eux qu'on valide et qu'on pilote le procédé.
- ⚠️ **TC1 et TC5** (aux bords x = 0 et x = 120 mm) **ne sont PAS prédictibles** de façon fiable : physique de bord 2D + effets thermiques de coin. Ne pas s'y fier pour piloter.
- ✅ Le **point chaud d'interface réel est plafonné vers ~500 °C** par la fusion du PEKK (le calcul « brut » sans fusion montait à 865 °C, ce qui était non physique).
- ✅ Deux corrections physiques adoptées par défaut (**effet de coin** + **artefact de source au bord**), **sans dégrader l'intérieur** (held-out neutre). Une recalibration globale a été **testée puis rejetée** (elle dégradait les autres essais).
- ➡️ **Prochaine action banc** : campagne **275 A** (hors-domaine), 2 tirs, **layout v2**, prédictions figées à l'avance, **held-out pur** (on ne recalibre pas). Couper les TC de bord à 390 °C. ⚠️ Marge à la dégradation étroite à 275 A.

---

## Glossaire (à lire une fois)

| Terme | Signification concrète |
|---|---|
| **Jumeau / modèle** | Simulation thermique 2D de la plaque CF/PEKK (120 × 40 mm), soudage semi-statique 4 passes, le MFC + bobine avance de 30 mm. |
| **θ\*** (« thêta étoile ») | Le jeu de paramètres calibrés « canonique » du modèle (facteur de couplage 6,0123 ; k_plan = 3,0 ; h_bas_2d = 37,4 ; h_bord_x0). C'est la configuration de référence. |
| **Calibration** | Ajuster ces paramètres sur UN essai de référence. |
| **Held-out** | Essais **non utilisés** pour calibrer, servant à juger honnêtement le modèle. Si une modif améliore l'essai calibré mais dégrade le held-out → on rejette (surapprentissage). |
| **NO-GO** | Modif rejetée parce qu'elle dégrade le held-out. |
| **Point chaud** | Température **à l'interface** de soudage (au cœur), plus chaude que les TC de bord. |
| **Profil « M »** | En largeur, la chaleur induite est plus forte **sur les bords** (les deux bosses du M) qu'au centre : les courants de Foucault s'écrasent au bord. |
| **Dwell** | Durée de maintien (temps de séjour) de chaque passe sur une position. |
| **Tg** | Température de transition vitreuse du PEKK (159 °C). |
| **Tf / fusion** | Fusion du PEKK, ~337 °C (seuil fusion). Consigne procédé = 390 °C ; dégradation = 450 °C. |
| **Layout v1 / v2** | Disposition des thermocouples. **v1** : tous les TC au **bord** (y = 0), x = 0/30/60/90/120. **v2** : TC1 (x = 0) et TC5 (x = 120) déplacés au **centre** de la largeur (y = 20 mm) ; TC2/3/4 restent au bord. |
| **TC** | Thermocouple (capteur de température). |

---

## Récit chronologique (8 étapes)

### Étape 1 — ✅ Essai réel 231 A v1 (26/08) : le jumeau est validé sur le procédé

**1. Prédiction (modèle seul).** Avant l'essai, le jumeau prédit le cycle 4 passes à 231 A (θ\* canonique, pilotage TC = 360 °C modèle ≈ 390 °C réel). C'est la prédiction que l'on va confronter au banc.

![Simulation 231 A — TC prédits seuls (modèle, sans données banc)](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_predit_231A_seul.png?v=20260831)

**2. Montage & essai réel.** On réalise le montage — tous les TC au **bord** (y = 0), positions x = 0/30/60/90/120 mm — et on applique **la même consigne en ampérage (231 A)** que la prédiction. Premier essai réel exploitable.

![Mesure brute 231 A v1](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_exp_231A_mesure.png?v=20260831b)

**3. Comparaison prédit ↔ mesuré.** Pics des TC **intérieurs** (TC2/3/4, x = 30/60/90) reproduits à **±12–20 °C**. RMSE de cycle 36–70 °C, **dominé par un décalage temporel** (le modèle refroidit ~10 % trop lentement) et non par les pics. Résidus identifiés : refroidissement lent, coin x = 0 sous-capté, TC5 (x = 120) sur-prédit.

![Validation 231 A — TC mesurés vs prédits](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_compare_230A_vs_reel.png?v=20260831)

**Ce que ça veut dire concrètement.** Le jumeau reproduit correctement le **niveau thermique** vu par le procédé sur les capteurs intérieurs. Les écarts restants sont surtout une **cinétique de refroidissement** un peu lente et des **effets de bord**, pas une erreur sur l'échauffement.

---

### Étape 2 — ✅ Correction de l'effet de coin (h_bord_x0 : 250 → 100)

**Fait.** Le « puits de bord » du modèle (paramètre h_bord_x0) refroidissait trop le coin x = 0, alors que les chants de la plaque sont **libres** (pas de refroidissement physique aussi fort). Valeur ramenée de 250 à 100.

**Résultat chiffré.** TC1 passe de **302 → 399 °C** (mesuré : **392 °C**). Le coin froid disparaît.

**Ce que ça veut dire concrètement.** Le modèle sous-estimait le coin d'entrée à cause d'un refroidissement de bord trop agressif et non physique. Corrigé, il colle à la mesure au coin x = 0.

![Correction du coin, 231 A](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_compare_230A_vs_reel_coin.png)

---

### Étape 3 — ⚠️ Recalibration jointe coin + refroidissement : NO-GO (issue #65)

**Fait.** Tentative de recaler globalement pour corriger AUSSI le refroidissement lent : θ\* recalibré (facteur 6,54 / h_bas_2d 125 / h_bord_x0 ~0).

**Résultat chiffré.** Améliore bien le cycle 231 A (RMSE moyen **77,6 → 63,5**), **MAIS** en held-out c'est un **NO-GO** : régresse les séries A/B de **+15 à +19 °C**, dégradation globale **+4,9**. → **Non adopté.**

**Ce que ça veut dire concrètement.** Le refroidissement rapide observé sur le 231 A est **spécifique à ce montage** (ce jour-là), pas une propriété générale. Le forcer dans le modèle casse tous les autres essais. On garde le θ\* canonique.

![Validation recalibration sur 231 A](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_valider_recalibration_231A.png)
![Held-out recalibration (NO-GO)](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_heldout_recalibration_231A.png)

---

### Étape 4 — ✅ Le plateau ~350–390 °C = fusion du PEKK

**Fait.** Le réel montre un **plateau** de température vers 350–390 °C. Ajout d'un modèle de fusion physique : chaleur latente **L_f = 40 J/g** (au lieu de 130 J/g qui supposerait 100 % cristallin) + transport du **bain fondu** (k_plan(T) rehaussé au-dessus de Tf).

**Résultat chiffré.** Reproduit le **plateau** et **plafonne le point chaud d'interface de 865 → 508 °C** (valeur physique). Held-out quasi neutre (**+0,6**). Analyse de rampe : le réel **sature** près de la consigne (le « genou » de fusion absorbe l'énergie), le modèle canonique sans fusion **ne sature pas et dépasse**.

**Ce que ça veut dire concrètement.** La fusion du PEKK agit comme un **thermostat physique** : l'énergie sert à faire fondre, pas à monter en température. Le **vrai point chaud d'interface est ~500 °C**, pas 865. C'est important pour juger le risque de dégradation (450 °C).

![Validation fusion 231 A](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_valider_fusion_231A.png)
![Analyse de la rampe 231 A](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_rampe_231A.png)

---

### Étape 5 — ⚠️ « TC5 s'emballe » : découverte d'un artefact de SOURCE au bord x

**Fait.** Le modèle faisait « s'emballer » TC5 (x = 120). Diagnostic en deux temps :
1. **Thermique** : les **deux** coins (x = 0 et x = 120) sur-chauffent, mais le puits h_bord_x0 n'agit qu'en x = 0 → asymétrie.
2. **Plus profond (électromagnétique)** : au bord réel de la plaque (x = 0 et x = 120), la condition **ψ = 0** du solveur de courants de Foucault force Jx = 0 et **concentre artificiellement la source au centre de la largeur (y = 20)**, au lieu du profil « M » (bord-piqué). Les TC1/TC5 posés là deviennent **non prédictibles**.

**Ce que ça veut dire concrètement.** Aux deux bords x, la façon dont le solveur ferme les courants crée un **échauffement non physique au centre de la largeur**. Tout capteur placé exactement à ces bords x est peu fiable dans le modèle.

![Diagnostic TC5 au bord](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_diag_tc5_bord.png)

---

### Étape 6 — ✅ Essai réel 231 A v2 (27/08) : le layout confirme tout

**Fait.** Nouvel essai, **layout v2** : TC1 (x = 0) et TC5 (x = 120) déplacés au **centre de la largeur (y = 20)** ; TC2/3/4 restent au bord (y = 0). But : mesurer directement ce que l'étape 5 prédit.

**Résultat chiffré.** Confirme les trois points :
- **Profil M réel** : TC5 au centre = **340 °C** < TC5 au bord = 387 °C (le bord est bien plus chaud → profil M validé).
- **Artefact de source** : modèle TC5 = **754 °C** vs réel = **340 °C** (le modèle surchauffe massivement au centre du bord x).
- **Emballement canonique amplifié** aux dwells plus longs de la v2.

**Ce que ça veut dire concrètement.** La physique de bord de l'étape 5 est **mesurée**, pas supposée. Le vrai profil en largeur est bien « M », et le modèle non corrigé surchauffe les capteurs de bord x.

![Confrontation 231 A v2](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_compare_231A_v2.png)

---

### Étape 7 — ✅ Correction de l'artefact de source, activée par défaut (30/08)

**Fait.** Correction développée (via agent EM spécialisé). **Recadrage important** : le pic au centre est **en grande partie de la vraie physique** (fermeture des boucles de courant loin de la bobine) ; **seul le collapse EXACT de la source à zéro au chant** était pathologique. La correction = **effet 3D d'épaisseur** (extension du domaine en x), **aucun paramètre libre nouveau**, flag `lambda_bord_x_mm`.

**Activée par DÉFAUT** parce que l'**intérieur reste strictement intact** : held-out exp7/exp9 **Δ RMSE = 0,00** ; seules les séries A/B bougent de **+0,2 à +0,4** (via les TC de bord uniquement). `--lambda-bord-x-off` restaure l'ancien chemin. **123 tests verts.**

**Résultat chiffré (OFF → ON).** TC1 (x = 0, centre) : **454 → 391 °C** = mesuré exact. TC5 : reste à **665 °C** (résidu = causes **thermiques**, pas la source).

**Ce que ça veut dire concrètement.** On a corrigé la partie pathologique de la source **sans toucher** à ce qui marche déjà (l'intérieur). TC1 est maintenant bon. TC5 garde un résidu multi-cause (thermique) → toujours peu fiable.

![Correction artefact source, 231 A v2](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_compare_231A_v2_corrige.png)

---

### Étape 8 — ➡️ Prochaine campagne : 275 A hors-domaine (issue #66)

**Décision (multi-agents).** Répéter 230 A **n'apporte rien** (résidus déjà prouvés). **275 A** teste l'**extrapolation** : loi de source ∝ I² → **+43 % de flux**.

**Protocole.** ~2 tirs, **MÊME layout v2** (TC1/TC5 au centre y = 20), **prédictions figées a priori**, **held-out PUR** (on ne recalibre JAMAIS sur ces essais).

**Prédiction figée.** Dwells **58 / 45 / 45 / 58 s**, cycle **~16 min**, TC2/3/4 → **~396–400 °C** réel attendu.

**⚠️ Avertissements.**
- Marge à la **dégradation étroite** à 275 A (on approche 450 °C).
- **TC1/TC5** (bords x) restent **peu prédictibles** (résidu multi-cause).

![Prédiction cycle 275 A v2](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_cycle_275A_v2_prediction.png)

---

## Acquis vs limites

| | Statut | Détail |
|---|---|---|
| TC intérieurs TC2/3/4 (x = 30/60/90) | ✅ Fiable | Pics à ±12–20 °C. Base de validation et de pilotage. |
| Point chaud d'interface | ✅ Compris | Plafonné ~500 °C par la fusion (pas 865). |
| Effet de coin (TC1, x = 0) | ✅ Corrigé | h_bord_x0 250→100 + correction source ; TC1 = mesuré. |
| Plateau de fusion | ✅ Modélisé | L_f = 40 J/g + transport bain fondu ; held-out neutre. |
| Artefact de source au bord x | ✅ Corrigé | Effet 3D d'épaisseur, 0 paramètre libre, défaut ON, intérieur intact. |
| Refroidissement de cycle | ⚠️ Léger biais | Modèle ~10 % trop lent (spécifique montage). Non corrigé (recalibration = NO-GO). |
| TC5 (x = 120) | ⚠️ Non fiable | Résidu thermique multi-cause. Ne pas piloter dessus. |
| TC1/TC5 en général (bords x) | ⚠️ Non prédictibles | Physique de bord 2D + coin. |
| Extrapolation en courant (>231 A) | ❓ À tester | Objet de la campagne 275 A (held-out pur). |

---

## Prochaines étapes (banc)

1. **Campagne 275 A**, ~2 tirs, **layout v2** (TC1/TC5 au centre y = 20 mm).
2. **Prédictions figées à l'avance** — held-out **pur**, on ne recalibre pas.
3. **Couper les TC de bord à 390 °C** (consigne procédé).
4. **Surveiller la marge à la dégradation** (450 °C) : elle est étroite à 275 A.
5. Valider/piloter **uniquement sur TC2/3/4**. Traiter TC1/TC5 comme informatifs, pas décisionnels.

---

## Issues liées

- **#64** — Campagne d'essais 231 A (validation cycle).
- **#65** — Recalibration jointe coin + refroidissement : **held-out NO-GO** (non adoptée).
- **#66** — Campagne 275 A hors-domaine (extrapolation, held-out pur).

