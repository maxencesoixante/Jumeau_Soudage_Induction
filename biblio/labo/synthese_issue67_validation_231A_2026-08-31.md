# Archive — Issue #67 : validation 231 A et raffinements du jumeau

> **Source** : GitHub issue #67 (« Synthèse opérateur — validation 231 A et raffinements du jumeau »).
> **Archivé le** : 2026-08-31. Récit chronologique et factuel de tout le travail mené sur
> le jumeau thermique CF/PEKK depuis les essais réels du 26/08. Tout ce qui suit est **acquis**.
> Figures locales : `biblio/labo/figures/`.

---

## TL;DR

- ✅ **Jumeau fiable** sur les TC **intérieurs TC2/TC3/TC4** (x = 30 / 60 / 90 mm) : pics à **±12–20 °C**. Base de validation et de pilotage.
- ⚠️ **TC1 et TC5** (bords x = 0 et x = 120 mm) **non prédictibles** de façon fiable : physique de bord 2D + effets de coin. Ne pas piloter dessus.
- ✅ **Point chaud d'interface plafonné ~500 °C** par la fusion du PEKK (le calcul « brut » sans fusion montait à 865 °C = non physique).
- ✅ Deux corrections physiques **adoptées par défaut** (effet de coin + artefact de source au bord), **sans dégrader l'intérieur** (held-out neutre). Recalibration globale **testée puis rejetée** (NO-GO held-out).
- ➡️ **Prochaine action banc** : campagne **275 A** (hors-domaine), 2 tirs, layout v2, prédictions figées à l'avance, **held-out pur**. Couper les TC de bord à 390 °C. Marge à la dégradation étroite à 275 A.

---

## Glossaire

| Terme | Signification concrète |
|---|---|
| **Jumeau / modèle** | Simulation thermique 2D de la plaque CF/PEKK (120 × 40 mm), soudage semi-statique 4 passes ; le MFC + bobine avance de 30 mm. |
| **θ\*** | Jeu de paramètres calibrés « canonique » (facteur de couplage 6,0123 ; k_plan = 3,0 ; h_bas_2d = 37,4 ; h_bord_x0). Configuration de référence. |
| **Calibration** | Ajuster ces paramètres sur UN essai de référence. |
| **Held-out** | Essais **non utilisés** pour calibrer, servant à juger honnêtement le modèle. Amélioration de l'essai calibré + dégradation du held-out → rejet (surapprentissage). |
| **NO-GO** | Modif rejetée parce qu'elle dégrade le held-out. |
| **Point chaud** | Température **à l'interface** de soudage (au cœur), plus chaude que les TC de bord. |
| **Profil « M »** | En largeur, la chaleur induite est plus forte **sur les bords** (bosses du M) qu'au centre : les courants de Foucault s'écrasent au bord. |
| **Dwell** | Durée de maintien (temps de séjour) de chaque passe sur une position. |
| **Tg** | Transition vitreuse du PEKK (159 °C). |
| **Tf / fusion** | Fusion du PEKK, ~337 °C (seuil). Consigne procédé = 390 °C ; dégradation = 450 °C. |
| **Layout v1 / v2** | Disposition des TC. **v1** : tous les TC au **bord** (y = 0), x = 0/30/60/90/120. **v2** : TC1 (x = 0) et TC5 (x = 120) déplacés au **centre** de la largeur (y = 20 mm) ; TC2/3/4 restent au bord. |
| **TC** | Thermocouple. |

---

## Récit chronologique (8 étapes)

### Étape 1 — ✅ Essai réel 231 A v1 (26/08) : le jumeau est validé sur le procédé

Premier essai réel exploitable, tous les TC au bord (y = 0), x = 0/30/60/90/120 mm. Confrontation directe modèle ↔ mesure.

**Chiffres.** Pics des TC **intérieurs** (TC2/3/4) reproduits à **±12–20 °C**. RMSE de cycle **36–70 °C**, dominé par un **décalage temporel** (le modèle refroidit ~10 % trop lentement), pas par les pics. Résidus : refroidissement lent, coin x = 0 sous-capté, TC5 (x = 120) sur-prédit.

**Interprétation.** Le jumeau reproduit correctement le **niveau thermique** vu par le procédé sur les capteurs intérieurs. Les écarts restants = cinétique de refroidissement un peu lente + effets de bord, pas une erreur sur l'échauffement.

- `figures/fig_exp_231A_mesure.png` — mesure brute 231 A v1
- `figures/fig_compare_230A_vs_reel.png` — confrontation modèle vs réel 231 A v1

### Étape 2 — ✅ Correction de l'effet de coin (h_bord_x0 : 250 → 100)

Le « puits de bord » du modèle (h_bord_x0) refroidissait trop le coin x = 0, alors que les chants sont **libres**. Valeur ramenée de 250 à 100.

**Chiffres.** TC1 passe de **302 → 399 °C** (mesuré : **392 °C**). Le coin froid disparaît.

- `figures/fig_compare_230A_vs_reel_coin.png` — correction du coin, 231 A

### Étape 3 — ⚠️ Recalibration jointe coin + refroidissement : NO-GO (issue #65)

Tentative de recaler globalement pour corriger AUSSI le refroidissement lent : θ\* recalibré (facteur 6,54 / h_bas_2d 125 / h_bord_x0 ~0).

**Chiffres.** Améliore le cycle 231 A (RMSE moyen **77,6 → 63,5**), **MAIS** held-out **NO-GO** : régresse les séries A/B de **+15 à +19 °C**, dégradation globale **+4,9**. → **Non adopté.**

**Interprétation.** Le refroidissement rapide observé sur le 231 A est **spécifique à ce montage/jour**, pas une propriété générale. Le forcer casse tous les autres essais. On garde le θ\* canonique.

- `figures/fig_valider_recalibration_231A.png` — validation recalibration sur 231 A
- `figures/fig_heldout_recalibration_231A.png` — held-out recalibration (NO-GO)

### Étape 4 — ✅ Le plateau ~350–390 °C = fusion du PEKK

Le réel montre un **plateau** vers 350–390 °C. Modèle de fusion physique : chaleur latente **L_f = 40 J/g** (au lieu de 130 J/g, qui supposerait 100 % cristallin) + transport du **bain fondu** (k_plan(T) rehaussé au-dessus de Tf).

**Chiffres.** Reproduit le **plateau** et **plafonne le point chaud d'interface de 865 → 508 °C** (valeur physique). Held-out quasi neutre (**+0,6**). Analyse de rampe : le réel **sature** près de la consigne (le « genou » de fusion absorbe l'énergie), le modèle canonique sans fusion **ne sature pas et dépasse**.

**Interprétation.** La fusion du PEKK agit comme un **thermostat physique** : l'énergie sert à fondre, pas à monter en température. Le **vrai point chaud d'interface est ~500 °C**, pas 865. Important pour juger le risque de dégradation (450 °C).

- `figures/fig_valider_fusion_231A.png` — validation fusion 231 A
- `figures/fig_rampe_231A.png` — analyse de la rampe 231 A

### Étape 5 — ⚠️ « TC5 s'emballe » : découverte d'un artefact de SOURCE au bord x

Le modèle faisait « s'emballer » TC5 (x = 120). Diagnostic en deux temps :
1. **Thermique** : les **deux** coins (x = 0 et x = 120) sur-chauffent, mais le puits h_bord_x0 n'agit qu'en x = 0 → asymétrie.
2. **Électromagnétique (plus profond)** : au bord réel de la plaque (x = 0 et x = 120), la condition **ψ = 0** du solveur de courants de Foucault force Jx = 0 et **concentre artificiellement la source au centre de la largeur (y = 20)**, au lieu du profil « M ». Les TC1/TC5 posés là deviennent **non prédictibles**.

- `figures/fig_diag_tc5_bord.png` — diagnostic TC5 au bord

### Étape 6 — ✅ Essai réel 231 A v2 (27/08) : le layout confirme tout

Nouvel essai, **layout v2** : TC1 (x = 0) et TC5 (x = 120) au **centre de la largeur (y = 20)** ; TC2/3/4 au bord (y = 0). But : mesurer directement ce que l'étape 5 prédit.

**Chiffres.** Confirme les trois points :
- **Profil M réel** : TC5 au centre = **340 °C** < TC5 au bord = 387 °C → profil M validé.
- **Artefact de source** : modèle TC5 = **754 °C** vs réel = **340 °C** (le modèle surchauffe massivement au centre du bord x).
- **Emballement canonique amplifié** aux dwells plus longs de la v2.

**Interprétation.** La physique de bord de l'étape 5 est **mesurée**, pas supposée.

- `figures/fig_compare_231A_v2.png` — confrontation 231 A v2 (source canonique, avant correction)

### Étape 7 — ✅ Correction de l'artefact de source, activée par défaut (30/08)

Correction développée (agent EM spécialisé). **Recadrage important** : le pic au centre est **en grande partie de la vraie physique** (fermeture des boucles de courant loin de la bobine) ; **seul le collapse EXACT de la source à zéro au chant** était pathologique. Correction = **effet 3D d'épaisseur** (extension du domaine en x), **aucun paramètre libre nouveau**, flag `lambda_bord_x_mm`.

**Activée par DÉFAUT** parce que l'**intérieur reste strictement intact** : held-out exp7/exp9 **Δ RMSE = 0,00** ; seules les séries A/B bougent de **+0,2 à +0,4** (via les TC de bord uniquement). `--lambda-bord-x-off` restaure l'ancien chemin. **123 tests verts.**

**Chiffres (OFF → ON).** TC1 (x = 0, centre) : **454 → 391 °C** = mesuré exact. TC5 : reste à **665 °C** (résidu = causes **thermiques**, pas la source).

- `figures/fig_compare_231A_v2_corrige.png` — correction artefact source, 231 A v2

### Étape 8 — ➡️ Prochaine campagne : 275 A hors-domaine (issue #66)

**Décision (multi-agents).** Répéter 230 A **n'apporte rien** (résidus déjà prouvés). **275 A** teste l'**extrapolation** : loi de source ∝ I² → **+43 % de flux**.

**Protocole.** ~2 tirs, **MÊME layout v2** (TC1/TC5 au centre y = 20), **prédictions figées a priori**, **held-out PUR** (on ne recalibre JAMAIS sur ces essais).

**Prédiction figée.** Dwells **58 / 45 / 45 / 58 s**, cycle **~16 min**, TC2/3/4 → **~396–400 °C** réel attendu.

**⚠️ Avertissements.** Marge à la **dégradation étroite** à 275 A (on approche 450 °C). **TC1/TC5** restent **peu prédictibles**.

- `figures/fig_cycle_275A_v2_prediction.png` — prédiction cycle 275 A v2

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
4. **Surveiller la marge à la dégradation** (450 °C) : étroite à 275 A.
5. Valider/piloter **uniquement sur TC2/3/4**. Traiter TC1/TC5 comme informatifs, pas décisionnels.

---

## Issues liées

- **#64** — Campagne d'essais 231 A (validation cycle).
- **#65** — Recalibration jointe coin + refroidissement : **held-out NO-GO** (non adoptée).
- **#66** — Campagne 275 A hors-domaine (extrapolation, held-out pur).
- **#67** — Synthèse opérateur (source de cette archive).

---

## Table des figures

| Fichier (`biblio/labo/figures/`) | Étape | Contenu |
|---|---|---|
| `fig_exp_231A_mesure.png` | 1 | Mesure brute 231 A v1 |
| `fig_compare_230A_vs_reel.png` | 1 | Validation 231 A — modèle vs réel (mesuré plein / prédit pointillé) |
| `fig_compare_230A_vs_reel_coin.png` | 2 | Correction du coin (h_bord_x0 250→100) |
| `fig_valider_recalibration_231A.png` | 3 | Recalibration sur 231 A |
| `fig_heldout_recalibration_231A.png` | 3 | Held-out recalibration (NO-GO) |
| `fig_valider_fusion_231A.png` | 4 | Validation fusion (plateau, plafond ~500 °C) |
| `fig_rampe_231A.png` | 4 | Analyse de la rampe (saturation de fusion) |
| `fig_diag_tc5_bord.png` | 5 | Diagnostic artefact de source TC5 au bord |
| `fig_compare_231A_v2.png` | 6 | Confrontation 231 A v2 (source canonique) |
| `fig_compare_231A_v2_corrige.png` | 7 | Correction artefact de source, 231 A v2 |
| `fig_cycle_275A_v2_prediction.png` | 8 | Prédiction cycle 275 A v2 |
| `fig_cycle_230A_TC390.png` | — | Cycle 230 A prédit seul (piloté sur TC, sans données banc) |
</content>
</invoke>
