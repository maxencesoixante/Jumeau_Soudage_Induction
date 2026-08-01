# Journal d'avancement — jumeau numérique soudage induction CF/PEKK

**Projet** : simulation de l'empreinte thermique bobine + concentrateur de flux (MFC) sur
laminés CF/PEKK, soudage par induction semi-statique (maîtrise, LIPEC / ÉTS).
**Dépôt** : `Jumeau_Soudage_Induction` (Python) &nbsp;·&nbsp; **Dernière mise à jour** : 2026-07-30.

> **But de ce document** : point d'entrée unique. Sa lecture donne l'état complet du projet —
> ce que fait le modèle, où il en est, ce qui a été fait et pourquoi, ce qui reste ouvert, et
> où trouver le détail. Les autres documents (`rapport_directrice_jumeau.md`,
> `rapport_slides_jumeau.md`, `mesures_a_realiser.md`, journaux `resultats_*.log`) sont les
> sources détaillées, indexés en fin de document.

---

## 1. État actuel en un coup d'œil

**Ce que le modèle fait.** Chaîne EM → thermique : champ magnétique de la bobine hairpin +
MFC (Biot-Savart + courants images) → courants de Foucault en plaque mince (fonction de
courant ψ, Lin 1993) → source Joule par couche → transfert thermique 3D transitoire avec
fusion (cp apparent). Deux solveurs : **2D lumpé à l'interface** (modèle de travail, ~2-4
min/essai) et 3D complet (cartes, gradient d'épaisseur, ~30 min/essai). Calibration LHS +
NLSQ pondérée par le bruit capteur sur **un** essai (A-1), validée en aveugle sur les autres.

**Géométrie de référence** (corrigée, cf. §2) : brins carrés 6 mm, gap 6,35 mm, **entraxe
12,35 mm**, **hauteur d'axe 5,0 mm** au-dessus du laminé, plan image du MFC au sommet des
brins. Fréquence 388 kHz, `k_plan = 3 W/m·K` (physique), twill suscepteur **0,20 mm** (mesuré).

**θ\* de référence** (modèle 2D, calibré sur A-1, grille 31×11) — **désormais écrit dans
`config/materiaux.yaml`** (canonique, consolidation 2026-07-30 ; `facteur_couplage` reste un
argument runtime par modèle×essai) :

| Paramètre | Valeur | Rôle |
|---|---|---|
| `facteur_couplage` | **6,0123** ± 0,07 | échelle de la source Joule |
| `h_haut` | **30,09** W/m²·K ± 1,3 | perte vers céramique/MFC |
| `h_bas_2d` | **37,42** W/m²·K ± 0,5 | perte vers face opposée/bâti |
| `decalage_x` | 0 (figé) | position bobine↔spot, non mesurée |
| `h_bord_x0` | 250 (figé) | puits de bord x=0 — **effectif, pas physique** (§4) |

**Validation croisée** (grille 61×21, θ\* de référence + twill 0,20 mm, sans recalibrage) —
RMSE / |ΔT_max| moyen (°C), 7 essais formels (`config/essais/`) :

| Essai | Rôle / conditions | RMSE | \|ΔT_max\| |
|---|---|---|---|
| **exp7 150 A** | validation, profil M en largeur (5 TC) | 25,4 | 36,4 |
| **exp7 200 A** | validation, profil M en largeur (5 TC) | 21,8 | 40,7 |
| **exp7 250 A** | validation, profil M en largeur (5 TC) | 22,6 | 51,4 |
| **exp9 200 A** | validation, dissipation longitudinale (spot fixe) | 12,1 | 15,9 |
| **A-1** | calibration, 250 A coupure 400 °C | 36,3 | 20,8 |
| **A-3** | validation aveugle, 200 A coupure 400 °C | 33,0 | 48,9 |
| **B-2** | validation, 250 A coupure 360 °C (loi capteurs) | 72,3 | 14,2 |

Le modèle **ordonne et explique** les niveaux de température (profil M validé, dissipation
longitudinale reproduite, séquence spatio-temporelle juste) mais ne pilote pas encore au degré
près ; le résidu du RMSE reste **structurel** (profil M trop contrasté hors-spot, cf. §3). La
**recalibration groupée (2026-07-30) a confirmé ce θ\* comme optimum** : aucun recalibrage sur
un seul essai (exp7 200 A) ne le bat sur le jeu tenu à l'écart ; `h_bord_x0=0` réfuté
(emballement +200 °C au chant série A) et lissage σ sur-ajuste un seul régime (cf. §2, 30 juil.).
**39 tests** automatisés verts (~4-5 min ; dont un bilan d'énergie 2D, résidu 0,6 %).

**Reproduire** (les `h` sont maintenant les défauts de `config/materiaux.yaml`) :
```bash
python scripts/valider.py --modele 2D --facteur 6.0123 --decalage-x 0 \
    --essais exp7_200A exp9_200A_monospot serieA_A-1 serieA_A-3 serieB_B-2
```

---

## 2. Chronologie des avancées

### 17 juillet — Fondations
Chaîne EM → thermique complète (`src/jumeau/em`, `thermique`), config géométrie/matériaux,
première calibration. Revue de littérature (`docs/etat_art_induction.md`).

### 18 juillet — Asservissement + comparaison littérature
Thermostat de coupure sur consigne (« chauffe jusqu'à T_processing »). Figures type Lionetto
2017 (Fig. 4 empreinte, Fig. 5 fusion). Constat : **TC1 (surface) chauffe 5-6× trop lentement**
(37,7 °C/s mesuré vs ~6,3 simulé) — déficit ouvert.

### 20 juillet — Modèle 2D + corrections structurelles
- **Solveur 2D lumpé à l'interface** créé (les 5 TC des séries A/B sont tous à l'interface).
- **Positions TC corrigées** (confirmé user) : les 5 TC à l'interface, TC1 au centre de
  largeur (y=20), TC2-5 au bord (y=0, lobes du profil M).
- **Thermostat mixte** point+section (`POIDS_POINT_THERMOSTAT`) pour réduire le dépassement.
- **Puits de bord `h_bord_x0 = 250`** ajouté au chant x=0 (justifié à l'époque par un
  « bridage » — **depuis infirmé**, cf. §4).
- Déficit TC1 : auto-échauffement du MFC (0,6-1,4 W) et `decalage_x` **écartés** avec chiffres.
- Couche IA multi-agents locale (`ai_framework`) posée sur le jumeau (démonstrateur).

### 21 juillet — Convergence de maillage
Le résidu « TC4 surestimé +74/+110 °C » était à **85-95 % un artefact de lecture** (nœud le
plus proche sur grille grossière). Corrigé par interpolation bilinéaire des TC et du nœud de
contrôle. Maillage retenu : 61×21 (validation), 31×11 (calibration). Position de lecture du
thermostat **écartée** comme cause (résultat négatif).

### 23 juillet — LE tournant : géométrie de bobine fausse
Le « déficit structurel » du pic A-1 (+40/+60 °C), poursuivi des semaines comme un manque de
physique (cp, k_plan, blindage, source EM, outillage — tous réfutés), était **un artefact de
géométrie** : l'entraxe des brins était faux de 35 % (0,019 supposé → **0,01235 m** réel).
Corriger + recalibrer résout l'essentiel du pic **à `k_plan = 3` physique**. Aussi : résidu
B-2 documenté, champ de réaction EM ajouté derrière un flag (petit, non recommandé), premiers
livrables docs.

### 24 juillet — Docs alignés + diagnostic hauteur
Rapports/slides/mesures régénérés au θ\* corrigé. Diagnostic de la cote `hauteur` : elle était
**dérivée du tube faux** (2 + demi-tube 9,5 mm), jamais mesurée.

### 27 juillet — Cadrage complet de la géométrie EM + réorientation
- **Plan image du MFC vérifié sur CAO** (coupe + photo de montage) : le concentrateur est bien
  au-dessus des brins, semelle au sommet des brins — la formule reste inchangée.
- **Hauteur corrigée 6,8 → 5,0 mm** (cote physique) + recalibration → θ\* de référence courant.
  Arbitrage : la cote juste **dégrade l'écart de pic** — signe que la source est trop
  concentrée, pas une raison de garder une cote fausse.
- **Diagnostic du profil en « M »** : le champ `Bz` est uniforme en largeur ; le M vient
  **entièrement de l'écrasement du courant de Foucault** (`ψ=0` au bord), pas du champ. Le
  levier « MFC fini » est donc mal dirigé pour la largeur. Contraste ~2,4×.
- **Réponses terrain user** intégrées (§4).
- **Loi thermostat « capteurs »** (couper sur le max des TC d'interface) implémentée derrière
  un flag `--thermostat-capteurs` (défaut off) : recale les pics (B-2 45→23) mais dégrade le
  RMSE — pas adoptée par défaut (§4).
- Figures Lionetto portées sur le modèle 2D ; docs et archive réorganisés.
- **Fréquence à 200 A = 383 kHz** (relevé user ; correction A-3 préparée). Paquets de lecture
  vidéo ajoutés (`imageio`, `opencv`) pour dépouiller les manips caméra.
- **Cartographie bord→centre, 3 courants (150/200/250 A) SANS céramique** (données user,
  `data/exp7_bord-centre_2026-07-27_sans-ceramique/`) : **vallée centrale du M confirmée** (le
  centre est un creux, le plus lent à monter, même forme aux 3 courants). Contraste mesuré
  ~1,35-1,88 vs 2,46 prédit — mais géométrie non standard (céramique retirée).

### 28 juillet — Le profil en « M » est VALIDÉ et SYMÉTRIQUE (avec céramique)
- **Reprise AVEC céramique (200 A, géométrie standard), 3 essais v2/v3/v4** : contraste
  chant/centre mesuré **2,16 / 2,17 / 2,31 ≈ 2,43 modèle** (REPRODUIT), forme quasi superposée
  au modèle (`data/exp7_bord-centre_2026-07-28_avec-ceramique/200A/`). **v4 avec TC1 réparé** :
  chant y=0 (215) ≈ chant y=40 (201), ratio **1,07** → **M SYMÉTRIQUE**, les deux chants sont des
  lobes chauds comme le prédit le modèle. L'asymétrie de v2/v3 venait entièrement du TC1 cassé.
  **Le modèle a raison sur l'amplitude ET la symétrie du M** ; le « sur-contraste » de la série
  sans céramique était un artefact du gap 0. → **Le levier « adoucir le M » est ÉCARTÉ.**
- **Campagne exp 7 CLOSE — 3 courants × 3 essais (150 / 200 / 250 A, avec céramique).** Le M est
  **symétrique** (ratios chant/chant 1,00-1,07) et de **bonne forme d'équilibre** (contraste
  mesuré ~2,0-2,2) aux trois courants ; le seul résidu est **transitoire** — le centre du modèle
  se remplit trop lentement, **indépendamment du courant** (motif centre-fill identique de 150 à
  250 A). Leviers testés puis **écartés** pour ce résidu : cp / masse thermique / e_eff (taux
  fondamental sous spot bon à ~15 %, `journaux/resultats_diag_taux_chauffe.log`), k_plan (casse le
  contraste), placement TC. Le **lissage de source** (gaussienne σ≈6 mm) remplit le centre mais
  abaisse les pics → posé derrière `--source-sigma-mm` (défaut off, **non adopté**). Le test **3D**
  confirme le mécanisme (le lumping supprime une partie du taux hors-spot : TC2 7,8 → 11,0 °C/s)
  mais **surchauffe l'interface** (TC1 682 vs 398 °C) et exigerait sa propre recalibration → **le
  2D lumpé reste le modèle de travail, limite centre-fill/hors-spot documentée**. **Figures de
  présentation** pour la directrice : `docs/figures_presentation/` (profil M aux 3 courants ;
  mesuré vs modèle ; dynamique centre-vs-chant). Détail :
  `data/exp7_bord-centre_2026-07-28_avec-ceramique/README.md`.
- **Campagne densifiée à 5 courants (ajout 176 et 225 A, 1 essai chacun) → loi taux-courant :
  la source suit I².** Les pics ne se comparant pas (chauffe manuelle non standardisée, arrêt
  ~240 °C au chant), l'observable est le **taux de chauffe au chant** (ΔT 30→130, sous le spot) :
  9,7 / 15,7 / 20,8 / 26,9 / 34,2 °C/s à 150 / 176 / 200 / 225 / 250 A. Une loi de puissance pure
  donne I^2,4, mais c'est un **artefact de pertes** : le modèle **R = k·I² − L** (source I² moins
  perte ~constante) fitte **R²=0,999**, L≈3,5 °C/s indépendant de I. **Fréquence mesurée CONSTANTE**
  (388±2 kHz sur 150-250 A, relevé user) → couplage fréquence↔courant **écarté** ; l'ancien relevé
  « 200 A=383 kHz » infirmé, correction « fréquence par essai » abandonnée (`config/geometrie.yaml`).
  → **La source suit bien la loi en I² du modèle** ; l'écart apparent = les pertes, pas la source.
  Deux figures ajoutées : `fig4_courbes_brutes` (5 TC d'un essai) et `fig5_loi_courant`.

### 28 juillet (soir) — Exp 9 : dissipation longitudinale T(x) — phase 1 (bord y=0)
Nouvelle campagne (`data/exp9_dissipation-longitudinale_2026-07-28/`, fiche `docs/protocole_exp_dissipation_longitudinale.md`) : 5 TC
alignés en **longueur** à x=0/30/60/90/120 mm (pas 30 mm), y=0. Deux essais 200 A, ≤ 236 °C
(réutilisables) :
- **Monospot** (spot fixe x=60) → **confrontation modèle** (profil normalisé, absolu non confronté
  car chauffe courte) : le modèle **reproduit la décroissance longitudinale** (mod 0,094 / mes
  0,081-0,139 à ±30 mm ; ~0,03 à ±60 mm). → **la forme de la source EN LONGUEUR au bord (dominé par
  la source) est VALIDÉE**. Asymétrie de montage (+x plus chaud) non reproductible (artefact).
- **Semi-statique** (4 dwells, procédé établi) → **confrontation modèle multi-spots** : le procédé
  est reproduit (spots avançant de 30 mm, bonne paire de TC chauffée par dwell, décroissance raide) ;
  la balance intra-paire n'est pas fidèle (±15 mm d'incertitude sur la position, pas un défaut).
- **Portée** : ceci valide la SOURCE en longueur, pas encore le résidu d'étalement. Le test décisif
  = **phase 2 à y=20 (centre, dominé par la conduction)** → probe direct de `k_plan`. À venir (+
  autres courants). Figures : `data/exp9_dissipation-longitudinale_2026-07-28/200A/analyse_*.png`.

### 29 juillet — Exp 9 monospot étendu à 4 courants (bord y=0)
Ajout des monospots **175 / 226 / 250 A** (+ 175 A semi-statique) à côté du 200 A. Tous coupés au
même pic (~270 °C au spot, échantillons réutilisables) → les **profils normalisés au spot se
superposent en une seule courbe** (0,02 / 0,08 / 1,00 / 0,14 / 0,03) : la **forme de la source en
longueur est INVARIANTE avec le courant**, et le modèle (forme symétrique) la reproduit. Figure de
présentation refondue en 2 panneaux (absolu °C + normalisé) : `docs/figures_elsevier/fig_dissipation_monospot.png`.

### 30 juillet — Consolidation du jumeau (θ\* canonique, essais labo formels)
Consolidation groupée pilotée par agents (design : `docs/superpowers/specs/2026-07-29-consolidation-jumeau-design.md`).
- **Campagnes labo intégrées au pipeline formel** : `config/essais/exp7_{150,200,250}A.yaml` et
  `exp9_200A_monospot.yaml` (schéma calqué sur série A) → confrontables directement par
  `valider.py`. Correction annexe : 3 chemins `fichier_mesures` périmés (série A/B) réparés.
- **Twill 0,20 mm** (mesuré) appliqué en config ; le test épinglé du taux TC2 recalé à ce régime
  (intention `taux_d > taux0` préservée).
- **θ\* de référence 2D écrit dans `config/materiaux.yaml`** (`h_haut=30.087`, `h_bas_2d=37.424`,
  `h_bord_x0=250`) : fin de la divergence config↔scripts, un seul θ\* canonique.
- **Recalibration groupée → θ\* actuel confirmé optimum.** Recalibrer sur exp7 200 A seul gagne
  sur cet essai (RMSE 21,8→8,2) mais **régresse sur tout le jeu tenu à l'écart** (RMSE moyen
  33,6→35,8) → non adopté (garde-fou « calibrer sur un, valider sur les autres »). Diagnostics :
  `h_bord_x0=0` **réfuté** (exp7 ne peut pas le contraindre — TC à 60 mm du chant ; et il cause
  +200 °C d'emballement au chant série A) ; lissage σ améliore le profil M mais **sur-ajuste**
  (dégrade le spot isolé exp9). Non-identifiabilité `h_haut`×`h_bas_2d` (corr 0,98) confirmée.
- **Prochaine expérience recommandée** : calibration **jointe multi-familles** (profil M exp7 +
  spot isolé exp9, `h_bord_x0` libre non nul) — seule voie pour un gain réel sans sur-ajuster un
  régime. Logs : `journaux/resultats_{baseline_phase1,calibration_exp7_200A,phase3}_*.log`.

### 30 juillet (suite) — Calibration jointe multi-familles (faite, non adoptée)
`scripts/calibrer_joint.py` : fit conjoint bord (exp7 150/200/250 A) + centre (exp9 y=20), vecteur
`[facteur_couplage, h_bas_2d, k_plan, h_bord_x0]`, `h_haut` figé.
- **`k_plan` devient identifiable ≈ 7,3 W/m·K** (vs 3,0) grâce à la famille centre → conductivité
  dans le plan probablement ~2× plus élevée (fort indice physique, à confirmer).
- Centre nettement amélioré (RMSE 16,9→8,0 ; pic TC3 +40→+14 °C) MAIS bord régresse (h_bas_2d élevé
  sur-refroidit les transitoires) → **RMSE global 18,5→19,2** → **non adopté** (θ\* réf. inchangé).
- σ non identifiable en joint (jacobien singulier) → off. `h_bord_x0=0` toujours réfuté.
- **Verdict** : le résidu du bord est **STRUCTUREL** (contraste spatial du M) — aucun coefficient
  uniforme ne le corrige. Le vrai levier = **changement de modèle** (adoucir le M en largeur, forme
  de source), pas la calibration. Logs : `journaux/resultats_calibration_joint_*.log`.

### 31 juillet — Forme du M (lambda_bord), contraste réel, piste taux-de-chauffe
Suite de la calibration jointe : on s'attaque à la FORME du M.
- **Le sur-contraste vient de la CL `ψ=0` au chant** (`em/foucault.py`) — exacte pour une nappe
  continue, fausse pour le twill à maille finie (le continuum casse au bord). Prototype
  **`lambda_bord_mm`** (longueur d'extrapolation de bord, analogie du problème de Milne) derrière
  **flag défaut OFF** (`source_spot`/`Essai`/`valider.py`/`calibrer_joint.py`, `lambda=0`
  bit-identique). `lambda≈4 mm` ramène le contraste **3,15 → ~2,1** (= mesuré) → **corrige la
  forme**. MAIS non conservatif en puissance → à θ\* fixe le RMSE global monte (18,5→~23) et un
  θ\* joint avec `lambda=4` reste perdant (27,3). → **prototype archivé, NON adopté**.
  Log : `journaux/resultats_diag_lambda_bord_em.log`.
- **Correction d'une figure périmée** : `fig2` (« mesuré vs modèle », slide 9) affichait un
  contraste **modèle 2,43 ≈ mesuré 2,18** codé EN DUR, d'avant les corrections twill/hauteur. Le
  **vrai** contraste du modèle actuel est **~3,15** (mesuré ~2,09) : le modèle **sur-contraste le M
  de ~50 %**, ce n'est PAS l'accord serré affiché. `fig2` recalculée en direct (mesuré+modèle) ;
  texte de la slide 9 corrigé. ⚠️ Revise partiellement le « M validé » : la FORME est bonne mais
  l'AMPLITUDE du contraste est sur-estimée.
- **Résidu(s) restant(s) — leviers épuisés côté calibration/forme.** Deux déficits STRUCTURELS
  distincts : (1) sur-contraste du M en largeur (compris, corrigeable via `lambda_bord` mais non
  conservatif) ; (2) **déficit de taux de chauffe / transitoire** (indépendant), qui bloque un θ\*
  joint gagnant même une fois le M adouci. **Prochaine investigation = le taux de chauffe /
  transitoire** (dépôt de puissance instantané, masse thermique effective, dynamique de source) —
  hors calibration scalaire.

### 31 juillet (suite) — Taux de chauffe : UN SEUL défaut d'étalement in-plane (3D écarté)
Investigation dédiée (`scripts/diag_taux_dTdt_sous_hors_spot.py`, `diag_sensibilite_taux_leviers.py`,
`diag_2d_vs_3d_taux_exp7_200A.py`). Déficit de dT/dt par régime : **sous-spot +14 %** (pas de
déficit, source OK), lobes −9 %, **centre-œil −22 %**, **hors-spot longitudinal −67 %** → croît avec
la distance au spot = déficit d'**étalement in-plane**, pas de dépôt.
- **Test décisif 2D vs 3D** (exp7_200A) : le 3D **ne ferme PAS** le déficit (TC3 −40 % en 2D comme
  en 3D) → ce n'est **PAS** un effet de lumping d'épaisseur / 3D. cp, e_eff, h : écartés.
- `k_plan` = levier dominant sur le taux aussi, mais **aucune valeur scalaire** ne ferme les 3
  régimes (k≈6 ferme le hors-spot, sur-corrige le sous-spot).
- **UNIFICATION** : taux, pic et contraste du M = **trois symptômes du même défaut** — l'étalement
  in-plane piloté par un `k_plan` scalaire, incapable d'être bas (sous-spot) ET haut (hors-spot).
  Le 3D est écarté (gain nul, coût ×10).
- **Options** : A) `k_plan` **anisotrope** (kx≠ky, physiquement justifié : M en y, dissipation en x)
  — dernier levier, à prototyper derrière flag ; B) accepter/documenter la limite (2D lumpé +
  k_plan=3,0 valide en pic/plateau ; transitoire hors-spot rapide = hors domaine de validité).

### 31 juillet (fin) — `k_plan` anisotrope testé (NON) → domaine de validité acté
Option A prototypée (`k_plan_x`/`k_plan_y` dans `solveur2d.py`/`materiaux.py`, flag défaut isotrope,
45 tests verts ; `calibrer_joint.py --anisotrope`). Le fit donne `kx≈7,4` (= le `k_plan≈7,3` déjà
connu) mais l'objectif est **multimodal en `ky`** (2 optima opposés : l'un bat le RMSE en aggravant
le contraste M à 3,63, l'autre rapproche 2,50 mais rate le RMSE) → l'anisotropie **relocalise** le
conflit, ne le résout pas. **Verdict : NON adopté** (flag off). Logs :
`journaux/resultats_calibration_joint_anisotrope*.log`.

**→ Arc modèle CLOS (option B).** Tous les leviers testés/documentés (calib scalaire jointe,
`lambda_bord`, 3D, anisotropie) : le résidu est **irréductible** par le modèle actuel. **Domaine de
validité acté** (cf. `docs/modele/README.md`) : **valide** en pic/plateau + forme de source + loi
I² ; **limite caractérisée** = amplitude du contraste M (~3,15 vs ~2,09) et transitoire hors-spot
rapide (−67 %), un seul défaut = étalement in-plane scalaire. `k_plan=3,0` reste la référence.

### 31 juillet — Exploitation (abaques procédé) + MFC réduit
- **5 exploitations** du domaine validé (scripts versionnés + figures) : prédictions T(t) multi-courant,
  **fenêtre de soudage**, empreinte, **procédé semi-statique** (soudure en 2 rails le long des chants,
  centre non soudé), **loi de réglage** (t ≈ 9,6·10⁵/I²). Slide deck « Exploitation » ajoutée.
- **MFC réduit (31,75 mm)** : le modèle standard n'en voit pas l'effet (MFC = plan image + `mu_r` +
  masque de PERTES, pas la source). Flag **`masque_source_mfc`** (défaut OFF, no-op MFC labo,
  48 tests) confinant la source à l'empreinte MFC. Prédiction : contraste **4,10 → 1,69**, points
  chauds vers l'intérieur — mais masque dur = **puissance tronquée** → pics effondrés (0 % soudé),
  centre encore froid. **Signal qualitatif** (M adouci) ; absolu biaisé bas → **à mesurer au banc**.
  `scripts/gen_mfc_reduit.py`, `fig_mfc_reduit.png`.

---

## 3. Résidus ouverts (par priorité)

1. **Amplitude du profil en « M » — RÉSOLU / campagne close (28 juillet).** La cartographie
   bord→centre a d'abord semblé montrer un modèle qui sur-contraste (série SANS céramique,
   contraste ~1,85 vs 2,46). Mais la **reprise AVEC céramique** (géométrie standard,
   `data/exp7_bord-centre_2026-07-28_avec-ceramique/`) donne un contraste mesuré **2,17 ≈ 2,43
   modèle**, forme normalisée quasi superposée : **le modèle a raison sur l'amplitude du M**. Le
   « sur-contraste » venait du retrait de la céramique (gap 0), pas du modèle. → **Le levier
   « adoucir le M » (courants de retour 3D / contact twill) n'est plus justifié.** **Confirmé aux
   3 courants (150 / 200 / 250 A, 3 essais chacun) — campagne close** : M symétrique et de bonne
   forme d'équilibre partout. Reste ouvert seulement le résidu **transitoire** de centre-fill
   (résidu #2), indépendant du courant.
2. **Lobes A/B trop froids / montée lente hors-spot — LE résidu dominant du RMSE, DIAGNOSTIQUÉ.**
   Les TC A/B TC2-4 (sur les lobes y=0, mais HORS-SPOT en x) sont sous-estimés de 20-30 °C et
   montent ~2× trop lentement. **Diagnostic du taux** (`journaux/resultats_diag_taux_chauffe.log`) : ce
   N'EST PAS un défaut de taux fondamental — directement sous le spot (chants exp 7, 200 A) le
   modèle chauffe à 13,7 °C/s vs 16,1 mesuré (~15 % lent). cp / masse thermique / e_eff (stack
   complet) ÉCARTÉS (réduire e_eff sur-corrige). Le « 2× lent » est spécifique aux points
   HORS-SPOT (TC2 à ~15 mm du spot) → **étalement latéral trop lent**, même famille que le
   centre-fill. Aucun levier 2D simple (cp, k_plan, lissage) ne ferme A/B sans casser les
   pics/le contraste → **limite structurelle probable du 2D lumpé** au régime multi-passes
   hors-spot (piste : effet 3D, à vérifier en 3D si besoin, coûteux).

**Résidu résolu / tranché (28 juillet) — le remplissage du centre.** La cartographie 200 A
avec céramique (chauffe longue, v4/v5/v6) montrait le centre du modèle ~4× trop lent (à chant
ΔT=200 : centre 76 mesuré vs 18 modèle). Diagnostic (`journaux/resultats_diag_centre_transitoire.log`) :
ni `cp` (invariant), ni `k_plan` seul (mauvaise forme), ni placement TC3 (5 mm insuffisant) →
œil de boucle (source ≈0 au centre exact) + source trop concentrée. **Prototype « source
adoucie » (gaussienne σ, délocalisation twill) IMPLÉMENTÉ derrière `lissage_sigma_mm`
(défaut off) + recalibré σ=6 + validé croisé** : il reproduit bien la cible exp 7 mais
**n'améliore PAS le fit global A/B** (RMSE ~-1 °C, mais écart de pic +13 à +17 °C : il abaisse
les lobes A/B déjà sous-estimés). → **gardé derrière le flag, défaut OFF, θ\* de référence
inchangé** ; correctif physique valable pour le régime « spot unique/centre », pas pour A/B. Le
vrai verrou A/B est la vitesse de chauffe (résidu n°2 ci-dessus).
3. **Régime basse consigne (B-2).** Cause confirmée (le modèle coupe au centre du spot, le
   procédé coupait sur le max des TC d'interface) ; correctif « capteurs » prêt derrière flag,
   à activer conjointement avec la correction du M. Réf. `journaux/resultats_diag_b2_thermostat_capteurs.log`.
4. **Déficit de chauffe en surface (TC1).** 5-6× trop lent, mécanisme non identifié ; attaqué
   par la mesure de la face du MFC (exp 8).

## 3 bis. Corrections préparées (à intégrer ensemble à la prochaine recalibration)

| Correction | Source | Statut |
|---|---|---|
| Épaisseur twill 0,28 → **0,20 mm** | mesure user | **APPLIQUÉE en config** (2026-07-30), test recalé |
| `h_bord_x0` | chants libres (user) | **gardé effectif = 250** ; `h_bord_x0=0` **réfuté** (emballement +200 °C au chant série A, 2026-07-30) |
| Loi thermostat « capteurs » | cahier de labo + données B-2 | flag prêt (défaut off) ; utilisé pour valider B-2 |
| Lissage source σ (centre-fill) | diag centre transitoire | flag prêt (défaut off) ; **sur-ajuste** (améliore M, dégrade spot isolé) — à recalibrer conjointement |
| ~~Fréquence par essai (383 kHz A-3)~~ | ~~relevé user~~ | **ABANDONNÉE** : mesure 5 courants = 388±2 kHz constante (2026-07-28), ancien 383 infirmé |

Restant : le **recalage vraiment gagnant** passe par une **calibration jointe multi-familles**
(profil M exp7 + spot isolé exp9, `h_bord_x0` libre) — cf. §2, 30 juillet.

---

## 4. Faits établis par l'utilisateur (réponses terrain, 27 juillet)

- **Twill = 0,20 mm** (mesuré) — config à corriger (0,28 → 0,20).
- **Les quatre chants latéraux sont à l'air libre** → `h_bord_x0` n'a aucune base physique,
  c'est un paramètre effectif (contredit l'ancien « bridage x=0 »). Contacts verticaux
  seulement : face inf → céramique (`h_bas`), face sup → céramique d'espacement → MFC (`h_haut`).
- **Le thermostat coupait sur le max des TC d'interface** (cahier de labo : « T max interface
  1/3/5 jamais dépassé ~372 °C ») — valide la loi « capteurs ».

Détail archivé dans `docs/labo/releves_resolus.md`.

---

## 5. Leçons de méthode (capital du projet)

- **Vérifier les cotes d'entrée avant de postuler un mécanisme manquant.** Deux « déficits
  structurels » se sont révélés être des cotes fausses (entraxe, puis hauteur), toutes deux
  dérivées d'un diamètre de tube erroné plutôt que mesurées.
- **Diagnostic avant correctif, à θ\* figé.** Toute la chaîne de réfutations (cp, k_plan,
  blindage, source EM…) a été testée sans rien graver dans le code — aucun correctif erroné
  commité quand la vraie cause (géométrie) est apparue.
- **Une cote « confirmée » n'est pas forcément mesurée.** Retracer son origine (git a montré
  que 6,8 mm venait du tube faux).
- **La physique correcte peut dégrader une métrique** (hauteur 5,0 ; loi capteurs) : c'est un
  signal sur un autre déficit, pas une raison de garder une entrée fausse.
- **Balayer les docs destinés à des tiers en même temps que le code** : `mesures_a_realiser.md`
  a un temps transporté vers le banc une prémisse (`k_plan`) déjà réfutée.

---

## 6. Carte des documents et journaux

**Organisation en deux parties** (2026-07-30) : `docs/labo/` = côté mesures ;
`docs/modele/` = côté simulation. Voir `docs/README.md`, `docs/labo/README.md`,
`docs/modele/README.md`.

**Documents (`docs/`)**
- `journal_avancees.md` — **ce document** (point d'entrée, transverse).
- `etat_art_induction.md` — revue de littérature (transverse).
- **`docs/labo/`** (résultats labo / mesures) :
  - `labo/protocole_exp_dissipation_longitudinale.md` — fiche protocole exp 9.
  - `labo/mesures_a_realiser.md` — mesures encore À FAIRE.
  - `labo/releves_resolus.md` — relevés terrain déjà tranchés (archive).
- **`docs/modele/`** (résultats modèle numérique) :
  - `modele/rapport_directrice_jumeau.md` — rapport complet pour la direction.
  - `modele/rapport_slides_jumeau.md` — trame de présentation (slides).
  - `modele/figures_catalogue.md` — catalogue des figures.
- `figures_elsevier/` , `figures_presentation/` — figures (modèle + mesures), en place
  (référencées par les scripts ; PNG 600 dpi).

**Journaux de référence (`journaux/resultats_*.log`) — état courant**
- `journaux/resultats_hauteur_5mm_recalibration.log` — correction hauteur + θ\* courant.
- `journaux/resultats_validation_reference_figures.log` — validation au θ\* courant.
- `journaux/resultats_diag_forme_source.log` — profil en M (source, pas champ).
- `journaux/resultats_diag_b2_thermostat_capteurs.log` — résidu B-2 + loi capteurs.
- `journaux/resultats_diag_hauteur_bobine.log` — cote hauteur + plan image MFC (CAO).
- `journaux/resultats_geometrie_corrigee_recalibration.log` — correction d'entraxe (étape précédente).

**Journaux d'archive (géométrie/θ\* antérieurs — raisonnements valides, chiffres périmés)**
- `journaux/resultats_diag_b2_longueur.log`, `journaux/resultats_diag_cp_kplan.log`,
  `journaux/resultats_diag_blindage_intercouche.log`, `journaux/resultats_convergence_maillage.log`,
  `journaux/resultats_diagnostic_profil_M_em.log`, `journaux/resultats_champ_reaction_em.log`,
  `journaux/resultats_test_position_thermostat.log`, et les `resultats_validation_2d_*.log`.

**Code** : `src/jumeau/` (em, thermique, identification, validation) ; `scripts/` (simuler,
calibrer, valider, figures) ; `config/` (geometrie.yaml, materiaux.yaml, essais/) ;
`tests/` (38 tests). `README.md` résume la chaîne physique et les limites connues.
