# Réouverture de `h_bord_x0` en held-out — 250 → 125 (2026-09-06)

**Verdict en une ligne :** `h_bord_x0 = 0` (suggéré par le près-bord FLIR de l'issue #69) reste
**réfuté** en held-out, mais **250 n'est plus l'optimum** — la correction de bord en x activée par
défaut le 2026-08-30 a périmé sa calibration. Valeur adoptée en config : **125 W/m².K**.

## 1. Pourquoi rouvrir une question close

`h_bord_x0` (puits de chaleur additionnel au chant `x=0` **seul** du modèle 2D lumpé,
`solveur2d.py`) a été calibré à 250 W/m².K sur A-1 en juillet, puis figé dans le θ\* canonique
(consolidation 2026-07-29). Le 2026-07-30, `h_bord_x0 = 0` a été **explicitement réfuté** :
emballement d'environ +200 °C au chant sur la série A.

Deux éléments neufs justifiaient la réouverture :

1. **Donnée** — l'issue #69 (thermographie plein-champ, run bord 150 A) montre que le près-bord
   mesuré colle à `h_bord_x0 ≈ 0` et que 250 **sur-refroidit** ; verdict noté « suggestif, pas
   définitif » (run bord = la donnée la plus faible de l'arc : foreshortening + contamination de chant).
2. **Modèle** — la correction de bord en x (`lambda_bord_x_mm`, mode AUTO, commit `0dab38d` du
   2026-08-30) est **activée par défaut** et agit sur **le même nœud `x=0`** que `h_bord_x0`. Les deux
   termes sont donc partiellement redondants, et la valeur 250 avait été calibrée sur le modèle
   **non corrigé**. Le held-out `h_bord_x0` n'avait jamais été refait depuis.

## 2. Protocole

Modèle 2D, θ\* canonique par ailleurs inchangé (`facteur_couplage = 6,0123`, `decalage_x = 0`,
`h_haut = 30,087`, `h_bas_2d = 37,424`), maillage de production `61×21×15`, **aucune recalibration**.

- **Essais sensibles** : `serieA_A-1`, `serieA_A-3`, `serieB_B-2` — les seuls dont un TC (TC1) est
  exactement au chant `x = 0`, là où `h_bord_x0` agit (`solveur2d.py:161` et `:196` — le puits ne
  touche que le nœud `x=0`).
- **Contrôles d'insensibilité** : `exp7_150A/200A/250A`, `exp9_200A_monospot`, `exp9_200A_y20_monospot`
  (TC loin du chant).
- **Contrôle d'attribution** : matrice 2×2 `h_bord_x0 ∈ {0, 250}` × `lambda_bord_x ∈ {off, AUTO}` sur
  A-1, pour reproduire la réfutation de juillet avant de conclure quoi que ce soit.

Rejouer : `python code/scripts/valider.py --modele 2D --facteur 6.0123 --decalage-x 0 --h-bord-x0 <H> --essais serieA_A-1 serieA_A-3 serieB_B-2`

## 3. Contrôle d'attribution — la réfutation de juillet se reproduit

serieA_A-1, TC1 (chant `x=0`) :

| configuration | TC1 pic simulé (°C) | Δpic TC1 (°C) | RMSE moyen (°C) |
|---|---|---|---|
| `h=250`, `lambda_bord_x` **off** — modèle de juillet | 400,2 | **+2,2** | 36,3 |
| `h=0`, `lambda_bord_x` **off** — test de juillet | 583,3 | **+185,3** | 40,5 |
| `h=250`, `lambda_bord_x` **AUTO** — production actuelle | 327,9 | **−70,1** | 36,5 |
| `h=0`, `lambda_bord_x` **AUTO** | 495,6 | **+97,6** | 40,0 |

L'emballement historique est reproduit à l'identique (+185 °C). La correction de bord en x le
**divise par deux mais ne l'annule pas** : à `h_bord_x0 = 0`, TC1 dépasse encore de +98 °C.

→ **`h_bord_x0 = 0` reste réfuté.** Le près-bord FLIR ne suffit pas à l'imposer.

## 4. Balayage — optimum intérieur à ≈ 100–125

RMSE moyen par essai (°C), modèle de production (correction de bord x AUTO) :

| `h_bord_x0` | A-1 | A-3 | B-2 | moyenne 3 essais | held-out (A-3, B-2) |
|---|---|---|---|---|---|
| 0   | 40,0 | 32,8 | 69,1 | 47,30 | 50,95 |
| 50  | 36,5 | 31,4 | 66,2 | 44,70 | 48,80 |
| 100 | 35,2 | **31,4** | 65,2 | 43,93 | **48,30** |
| **125** | **35,0** | 31,6 | 65,1 | **43,90** | 48,35 |
| 150 | 35,1 | 31,9 | **65,0** | 44,00 | 48,45 |
| 200 | 35,7 | 32,6 | 65,2 | 44,50 | 48,90 |
| 250 *(ancienne config)* | 36,5 | 33,4 | 65,6 | 45,17 | 49,50 |
| 350 | 38,1 | 34,8 | 66,5 | 46,47 | 50,65 |

**Optimum intérieur retrouvé sur les trois essais séparément**, entre 100 et 150. En prenant A-1
comme point de réglage (c'est sur lui que 250 avait été calibré à l'origine), le held-out A-3 + B-2
passe de **49,50 à 48,35 °C** (−1,2). L'écart de pic de TC1 change de signe à `h ≈ 122` (A-1),
`≈ 75` (A-3), `≈ 40` (B-2).

**Contrôles — strictement insensibles** (h = 250 → 125) :

| essai | RMSE h=250 | RMSE h=125 |
|---|---|---|
| exp7_150A | 25,4 | 25,4 |
| exp7_200A | 21,8 | 21,8 |
| exp7_250A | 22,6 | 22,6 |
| exp9_200A_monospot | 12,1 | 12,0 |
| exp9_200A_y20_monospot | 17,7 | 17,6 |

Aucune régression sur les familles de calibration : le changement est **local au chant `x=0`**.

## 5. Le résultat de fond — une redondance non détectée à l'adoption

L'adoption de `lambda_bord_x` (2026-08-30) avait été jugée « quasi neutre » sur les essais de
soudage : **+0,2 à +0,4 °C** de RMSE moyen. Sous cet agrégat neutre se cachaient, sur A-1, **deux
déplacements de pic opposés et grands**, précisément sur les deux capteurs de chant :

- TC1 (`x=0`) : 400,2 → 327,9 °C, soit **−72 °C** — d'un écart de pic quasi nul à −70 ;
- TC5 (`x=L`) : 409,3 → 445,6 °C, soit **+36 °C**.

Autrement dit : la correction physique et le fudge `h_bord_x0` faisaient en partie le même travail au
chant `x=0`, et la valeur 250 — calibrée sur le modèle non corrigé — sur-refroidissait désormais.
La direction du correctif (**baisser** `h_bord_x0`) est cohérente avec le près-bord FLIR, sans aller
jusqu'à 0.

**Leçon transposable** : un RMSE agrégé quasi neutre n'est pas une preuve d'innocuité (il peut être la
somme d'effets locaux importants qui se compensent), et toute correction physique ajoutée périme la
calibration des paramètres effectifs qui agissent dans la même région.

## 6. Réserves

- Gain modeste : **−1,2 °C** de RMSE held-out moyen. C'est un recentrage, pas une levée du résidu
  structurel d'étalement in-plane (`k_plan`), qui reste la limite dominante.
- `h_bord_x0` **reste un paramètre effectif sans base physique** : les quatre chants sont à l'air
  libre (confirmé terrain le 2026-07-27). Le remplacement propre resterait une convection latérale
  faible et **uniforme sur les quatre chants**, à tester séparément.
- Les pics d'A-1/A-3/B-2 sont partiellement médiés par le thermostat sur consigne d'interface
  (400/400/360 °C) : l'écart de pic n'est donc pas une mesure pure du puits de bord ; le RMSE l'est
  davantage.
- Seuls trois essais de soudage portent un TC au chant `x=0` — la contrainte sur ce paramètre reste
  mince.

## 7. Ce qui change dans le dépôt

- `code/config/materiaux.yaml` : `h_bord_x0` 250,0 → **125,0**, bloc de commentaire réécrit (tableau
  du balayage + motif).
- `code/tests/test_planification.py` : le θ\* figé du gabarit de test suit la config (250 → 125).
- θ\* canonique désormais : `facteur_couplage = 6,0123` (runtime), `h_haut = 30,087`,
  `h_bas_2d = 37,424`, `h_bord_x0 = 125`.
