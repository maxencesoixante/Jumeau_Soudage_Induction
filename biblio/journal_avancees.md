# Journal d'avancement — jumeau numérique soudage induction CF/PEKK

**Projet** : simulation de l'empreinte thermique bobine + concentrateur de flux (MFC) sur
laminés CF/PEKK, soudage par induction semi-statique (maîtrise, LIPEC / ÉTS).
**Dépôt** : `Jumeau_Soudage_Induction` (Python) &nbsp;·&nbsp; **Dernière mise à jour** : 2026-10-02.

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
`code/config/materiaux.yaml`** (canonique, consolidation 2026-07-30 ; `facteur_couplage` reste un
argument runtime par modèle×essai) :

| Paramètre | Valeur | Rôle |
|---|---|---|
| `facteur_couplage` | **6,0123** ± 0,07 | échelle de la source Joule |
| `h_haut` | **30,09** W/m²·K ± 1,3 | perte vers céramique/MFC |
| `h_bas_2d` | **37,42** W/m²·K ± 0,5 | perte vers face opposée/bâti |
| `decalage_x` | 0 (figé) | position bobine↔spot, non mesurée |
| `h_bord_x0` | **125** (recalibré le 2026-09-06, `fc92052`) | puits de bord x=0 — **effectif, pas physique** (§4) ; `=0` reste réfuté |

**Validation croisée** (grille 61×21, θ\* de référence + twill 0,20 mm, sans recalibrage) —
RMSE / |ΔT_max| moyen (°C), 7 essais formels (`code/config/essais/`) :

| Essai | Rôle / conditions | RMSE | \|ΔT_max\| | RMSE au 30-07 |
|---|---|---|---|---|
| **exp7 150 A** | validation, profil M en largeur (5 TC) | 25,4 | 36,3 | 25,4 |
| **exp7 200 A** | validation, profil M en largeur (5 TC) | 21,8 | 40,6 | 21,8 |
| **exp7 250 A** | validation, profil M en largeur (5 TC) | 22,6 | 51,4 | 22,6 |
| **exp9 200 A** | validation, dissipation longitudinale (spot fixe) | 12,0 | 15,8 | 12,1 |
| **A-1** | calibration, 250 A coupure 400 °C | 35,0 | 26,6 | 36,3 |
| **A-3** | validation aveugle, 200 A coupure 400 °C | 31,6 | 47,3 | 33,0 |
| **B-2** | validation, 250 A coupure 360 °C | 65,1 | 55,3 | 72,3 |

**Recalculée le 2026-09-16** — deux changements de modèle l'avaient périmée : correction de
bord en x active par défaut (2026-08-30) et `h_bord_x0` 250 → 125 (2026-09-06). Le résultat
confirme ce qui était annoncé : **exp7 et exp9 sont strictement inchangés** (l'intérieur du
domaine n'est pas touché), et **les séries A/B s'améliorent** (A-1 36,3 → 35,0 ; A-3 33,0 →
31,6 ; B-2 72,3 → 65,1). La colonne `|ΔT_max|` de B-2 n'est pas comparable à celle de juillet :
l'ancienne était calculée sous la loi « capteurs », **rejetée définitivement depuis** (§2, 3 août).

Le modèle **ordonne et explique** les niveaux de température (profil M validé, dissipation
longitudinale reproduite, séquence spatio-temporelle juste) mais ne pilote pas encore au degré
près ; le résidu du RMSE reste **structurel** (profil M trop contrasté hors-spot, cf. §3). La
**recalibration groupée (2026-07-30) a confirmé ce θ\* comme optimum** : aucun recalibrage sur
un seul essai (exp7 200 A) ne le bat sur le jeu tenu à l'écart ; `h_bord_x0=0` réfuté
(emballement +200 °C au chant série A) et lissage σ sur-ajuste un seul régime (cf. §2, 30 juil.).
**142 tests** automatisés verts (~25 s ; dont un bilan d'énergie 2D, résidu 0,6 %).

**Ce que le modèle a gagné depuis juillet** (détail en §2) :

- **Source bimodale** (`bimodal_sigma_mm` ≈ 2,5 mm) — les deux jambes du hairpin sont résolues
  séparément ; le pic unique était un défaut de source, révélé par la thermographie plein champ.
- **Correction de bord en x** (`lambda_bord_x_mm`, **active par défaut** depuis le 2026-08-30) —
  supprime l'effondrement non physique de la source aux extrémités, sans paramètre libre.
- **Modèle de fusion** (L_f = 40 J/g physique + `k_plan(T>Tf)`, **derrière flag, non adopté**) —
  plafonne l'interface à 508 °C au lieu de 865 et reproduit le plateau mesuré.
- **Planificateur de passes** (`code/scripts/planifier_soudage.py`) — plan glouton, vérification
  séquentielle, carte de couverture et verdict.
- **Critère de dégradation en temps × température** (`jumeau.thermique.dose_degradation`,
  2026-09-16) — remplace un seuil de pic qui n'avait aucune provenance.

**Reproduire** (les `h` sont maintenant les défauts de `code/config/materiaux.yaml`) :
```bash
python code/scripts/valider.py --modele 2D --facteur 6.0123 --decalage-x 0 \
    --essais exp7_200A exp9_200A_monospot serieA_A-1 serieA_A-3 serieB_B-2
```

---

## 2. Chronologie des avancées

### 17 juillet — Fondations
Chaîne EM → thermique complète (`code/src/jumeau/em`, `thermique`), config géométrie/matériaux,
première calibration. Revue de littérature (`biblio/references/etat_art_induction.md`).

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

**Figures**

![Série A, essai A-2 (250 A, 9 juin 2026) : les 5 TC d'interface pendant le cycle semi-statique à 4 passes — format de référence des relevés.](labo/figures/serieA_A-2_250A_2026-06-09.png)
*Série A, essai A-2 (250 A, 9 juin 2026) : les 5 TC d'interface pendant le cycle semi-statique à 4 passes — format de référence des relevés.*

![Procédé semi-statique : positions successives de la bobine et du MFC sur l'échantillon (4 passes au pas de 30 mm).](presentations/figures_schemas/fig_passages_mfc_storyboard.png)
*Procédé semi-statique : positions successives de la bobine et du MFC sur l'échantillon (4 passes au pas de 30 mm).*

![Procédé semi-statique, vue d'ensemble des passages du MFC.](presentations/figures_schemas/fig_passages_mfc.png)
*Procédé semi-statique, vue d'ensemble des passages du MFC.*

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
  `donnees/data/exp7_bord-centre_2026-07-27_sans-ceramique/`) : **vallée centrale du M confirmée** (le
  centre est un creux, le plus lent à monter, même forme aux 3 courants). Contraste mesuré
  ~1,35-1,88 vs 2,46 prédit — mais géométrie non standard (céramique retirée).

**Figures**

![Montage de la campagne bord → centre (exp7) : 5 TC répartis en largeur, du chant y = 0 au chant y = 40, sous le spot.](presentations/figures_schemas/schema_montage_exp7.png)
*Montage de la campagne bord → centre (exp7) : 5 TC répartis en largeur, du chant y = 0 au chant y = 40, sous le spot.*

### 28 juillet — Le profil en « M » est VALIDÉ et SYMÉTRIQUE (avec céramique)
- **Reprise AVEC céramique (200 A, géométrie standard), 3 essais v2/v3/v4** : contraste
  chant/centre mesuré **2,16 / 2,17 / 2,31 ≈ 2,43 modèle** (REPRODUIT), forme quasi superposée
  au modèle (`donnees/data/exp7_bord-centre_2026-07-28_avec-ceramique/200A/`). **v4 avec TC1 réparé** :
  chant y=0 (215) ≈ chant y=40 (201), ratio **1,07** → **M SYMÉTRIQUE**, les deux chants sont des
  lobes chauds comme le prédit le modèle. L'asymétrie de v2/v3 venait entièrement du TC1 cassé.
  **Le modèle a raison sur l'amplitude ET la symétrie du M** ; le « sur-contraste » de la série
  sans céramique était un artefact du gap 0. → **Le levier « adoucir le M » est ÉCARTÉ.**
- **Campagne exp 7 CLOSE — 3 courants × 3 essais (150 / 200 / 250 A, avec céramique).** Le M est
  **symétrique** (ratios chant/chant 1,00-1,07) et de **bonne forme d'équilibre** (contraste
  mesuré ~2,0-2,2) aux trois courants ; le seul résidu est **transitoire** — le centre du modèle
  se remplit trop lentement, **indépendamment du courant** (motif centre-fill identique de 150 à
  250 A). Leviers testés puis **écartés** pour ce résidu : cp / masse thermique / e_eff (taux
  fondamental sous spot bon à ~15 %, `donnees/journaux/archive/resultats_diag_taux_chauffe.log`), k_plan (casse le
  contraste), placement TC. Le **lissage de source** (gaussienne σ≈6 mm) remplit le centre mais
  abaisse les pics → posé derrière `--source-sigma-mm` (défaut off, **non adopté**). Le test **3D**
  confirme le mécanisme (le lumping supprime une partie du taux hors-spot : TC2 7,8 → 11,0 °C/s)
  mais **surchauffe l'interface** (TC1 682 vs 398 °C) et exigerait sa propre recalibration → **le
  2D lumpé reste le modèle de travail, limite centre-fill/hors-spot documentée**. **Figures de
  présentation** pour la directrice : `biblio/labo/figures/` (profil M aux 3 courants ;
  mesuré vs modèle ; dynamique centre-vs-chant). Détail :
  `donnees/data/exp7_bord-centre_2026-07-28_avec-ceramique/README.md`.
- **Campagne densifiée à 5 courants (ajout 176 et 225 A, 1 essai chacun) → loi taux-courant :
  la source suit I².** Les pics ne se comparant pas (chauffe manuelle non standardisée, arrêt
  ~240 °C au chant), l'observable est le **taux de chauffe au chant** (ΔT 30→130, sous le spot) :
  9,7 / 15,7 / 20,8 / 26,9 / 34,2 °C/s à 150 / 176 / 200 / 225 / 250 A. Une loi de puissance pure
  donne I^2,4, mais c'est un **artefact de pertes** : le modèle **R = k·I² − L** (source I² moins
  perte ~constante) fitte **R²=0,999**, L≈3,5 °C/s indépendant de I. **Fréquence mesurée CONSTANTE**
  (388±2 kHz sur 150-250 A, relevé user) → couplage fréquence↔courant **écarté** ; l'ancien relevé
  « 200 A=383 kHz » infirmé, correction « fréquence par essai » abandonnée (`code/config/geometrie.yaml`).
  → **La source suit bien la loi en I² du modèle** ; l'écart apparent = les pertes, pas la source.
  Deux figures ajoutées : `fig4_courbes_brutes` (5 TC d'un essai) et `fig5_loi_courant`.

**Figures**

![200 A avec céramique, essai v2 : profil en largeur mesuré (TC1 cassé).](../donnees/data/exp7_bord-centre_2026-07-28_avec-ceramique/200A/analyse_v2.png)
*200 A avec céramique, essai v2 : profil en largeur mesuré (TC1 cassé).*

![200 A avec céramique, v2 et v3 superposés.](../donnees/data/exp7_bord-centre_2026-07-28_avec-ceramique/200A/analyse_v2_v3.png)
*200 A avec céramique, v2 et v3 superposés.*

![200 A avec céramique, v2/v3/v4 : la forme normalisée se superpose au modèle sur toute la largeur ; v4 (TC1 réparé) montre le M symétrique.](../donnees/data/exp7_bord-centre_2026-07-28_avec-ceramique/200A/analyse_v2_v3_v4.png)
*200 A avec céramique, v2/v3/v4 : la forme normalisée se superpose au modèle sur toute la largeur ; v4 (TC1 réparé) montre le M symétrique.*

![Montée en température du centre et du chant : le centre du modèle se remplit trop lentement (résidu transitoire).](../donnees/data/exp7_bord-centre_2026-07-28_avec-ceramique/200A/dynamique_centre_vs_chant.png)
*Montée en température du centre et du chant : le centre du modèle se remplit trop lentement (résidu transitoire).*

![Balayage de k_plan : remplir le centre casse le contraste du M.](../donnees/data/exp7_bord-centre_2026-07-28_avec-ceramique/200A/diag_kplan_sweep.png)
*Balayage de k_plan : remplir le centre casse le contraste du M.*

![Prototype de source lissée (gaussienne σ ≈ 6 mm) : remplit le centre mais abaisse les pics (non adopté).](../donnees/data/exp7_bord-centre_2026-07-28_avec-ceramique/200A/proto_source_adoucie.png)
*Prototype de source lissée (gaussienne σ ≈ 6 mm) : remplit le centre mais abaisse les pics (non adopté).*

![Profil en « M » mesuré en largeur aux trois courants (150 / 200 / 250 A).](labo/figures/fig1_profil_M.png)
*Profil en « M » mesuré en largeur aux trois courants (150 / 200 / 250 A).*

![Dynamique centre vs chant, mesure et modèle.](labo/figures/fig3_dynamique_centre.png)
*Dynamique centre vs chant, mesure et modèle.*

![Courbes brutes des 5 TC d'un essai bord → centre.](labo/figures/fig4_courbes_brutes.png)
*Courbes brutes des 5 TC d'un essai bord → centre.*

![Taux de chauffe au chant en fonction du courant : loi R = k·I² − L (R² = 0,999).](labo/figures/fig5_loi_courant.png)
*Taux de chauffe au chant en fonction du courant : loi R = k·I² − L (R² = 0,999).*

Versions diapositives des figures 1 à 5 : `labo/figures/presentation_fig*.png` (même contenu, format 16:9).

![Toutes les courbes brutes de la campagne en largeur.](labo/figures/fig_courbes_largeur_brut.png)
*Toutes les courbes brutes de la campagne en largeur.*

![Essais en largeur regroupés par courant.](labo/figures/fig_essais_par_courant.png)
*Essais en largeur regroupés par courant.*

![Petits multiples : les 5 TC, un panneau par courant.](labo/figures/fig_essais_5TC_par_courant.png)
*Petits multiples : les 5 TC, un panneau par courant.*

![Température du chant, tous essais superposés.](labo/figures/fig_essais_chant_superpose.png)
*Température du chant, tous essais superposés.*

![Version poster de la campagne bord → centre.](labo/figures/poster_chauffe_exp7.png)
*Version poster de la campagne bord → centre.*

### 28 juillet (soir) — Exp 9 : dissipation longitudinale T(x) — phase 1 (bord y=0)
Nouvelle campagne (`donnees/data/exp9_dissipation-longitudinale_2026-07-28/`, fiche `biblio/protocole_exp_dissipation_longitudinale.md`) : 5 TC
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
  = **phase 2 à y=20 (centre, dominé par la conduction)** → probe direct de `k_plan`. FAITE le 30-07 (centre y=20, 200 + 175 A) : k_plan≈7,3 identifié via fit conjoint, résidu structurel confirmé (cf. §2 et issue #11). Figures : `donnees/data/exp9_dissipation-longitudinale_2026-07-28/200A/analyse_*.png`.

**Figures**

![Montage de la campagne longitudinale (exp9) : 5 TC alignés en longueur à x = 0/30/60/90/120 mm, au bord y = 0.](presentations/figures_schemas/schema_montage_exp9.png)
*Montage de la campagne longitudinale (exp9) : 5 TC alignés en longueur à x = 0/30/60/90/120 mm, au bord y = 0.*

![Spot fixe 200 A : historique des 5 TC (gauche) et profil longitudinal au pic (droite).](../donnees/data/exp9_dissipation-longitudinale_2026-07-28/200A/analyse_200A_y0_monospot.png)
*Spot fixe 200 A : historique des 5 TC (gauche) et profil longitudinal au pic (droite).*

![Spot fixe 200 A : profil longitudinal normalisé, mesure vs modèle — la forme de la source en longueur est reproduite.](../donnees/data/exp9_dissipation-longitudinale_2026-07-28/200A/analyse_200A_y0_monospot_vs_modele.png)
*Spot fixe 200 A : profil longitudinal normalisé, mesure vs modèle — la forme de la source en longueur est reproduite.*

![Semi-statique 200 A (4 passes) : historique longitudinal des 5 TC.](../donnees/data/exp9_dissipation-longitudinale_2026-07-28/200A/analyse_200A_y0.png)
*Semi-statique 200 A (4 passes) : historique longitudinal des 5 TC.*

![Semi-statique 200 A : mesure vs modèle multi-spots.](../donnees/data/exp9_dissipation-longitudinale_2026-07-28/200A/analyse_200A_y0_semistatique_vs_modele.png)
*Semi-statique 200 A : mesure vs modèle multi-spots.*

![Courbes brutes de la campagne longitudinale, spot fixe.](labo/figures/fig_courbes_longueur_statique_brut.png)
*Courbes brutes de la campagne longitudinale, spot fixe.*

![Courbes brutes de la campagne longitudinale, semi-statique.](labo/figures/fig_courbes_longueur_semistatique_brut.png)
*Courbes brutes de la campagne longitudinale, semi-statique.*

![Dissipation longitudinale en semi-statique (4 passes).](labo/figures/fig_dissipation_semistatique.png)
*Dissipation longitudinale en semi-statique (4 passes).*

### 29 juillet — Exp 9 monospot étendu à 4 courants (bord y=0)
Ajout des monospots **175 / 226 / 250 A** (+ 175 A semi-statique) à côté du 200 A. Tous coupés au
même pic (~270 °C au spot, échantillons réutilisables) → les **profils normalisés au spot se
superposent en une seule courbe** (0,02 / 0,08 / 1,00 / 0,14 / 0,03) : la **forme de la source en
longueur est INVARIANTE avec le courant**, et le modèle (forme symétrique) la reproduit. Figure de
présentation refondue en 2 panneaux (absolu °C + normalisé) : `biblio/labo/figures/fig_dissipation_monospot.png`.

**Figures**

![Spot fixe à 4 courants : profils absolus (°C) et normalisés — les profils normalisés se superposent en une seule courbe.](labo/figures/fig_dissipation_monospot.png)
*Spot fixe à 4 courants : profils absolus (°C) et normalisés — les profils normalisés se superposent en une seule courbe.*

### 30 juillet — Consolidation du jumeau (θ\* canonique, essais labo formels)
Consolidation groupée pilotée par agents (design : `biblio/superpowers/specs/2026-07-29-consolidation-jumeau-design.md`).
- **Campagnes labo intégrées au pipeline formel** : `code/config/essais/exp7_{150,200,250}A.yaml` et
  `exp9_200A_monospot.yaml` (schéma calqué sur série A) → confrontables directement par
  `valider.py`. Correction annexe : 3 chemins `fichier_mesures` périmés (série A/B) réparés.
- **Twill 0,20 mm** (mesuré) appliqué en config ; le test épinglé du taux TC2 recalé à ce régime
  (intention `taux_d > taux0` préservée).
- **θ\* de référence 2D écrit dans `code/config/materiaux.yaml`** (`h_haut=30.087`, `h_bas_2d=37.424`,
  `h_bord_x0=250`) : fin de la divergence config↔scripts, un seul θ\* canonique.
- **Recalibration groupée → θ\* actuel confirmé optimum.** Recalibrer sur exp7 200 A seul gagne
  sur cet essai (RMSE 21,8→8,2) mais **régresse sur tout le jeu tenu à l'écart** (RMSE moyen
  33,6→35,8) → non adopté (garde-fou « calibrer sur un, valider sur les autres »). Diagnostics :
  `h_bord_x0=0` **réfuté** (exp7 ne peut pas le contraindre — TC à 60 mm du chant ; et il cause
  +200 °C d'emballement au chant série A) ; lissage σ améliore le profil M mais **sur-ajuste**
  (dégrade le spot isolé exp9). Non-identifiabilité `h_haut`×`h_bas_2d` (corr 0,98) confirmée.
- **Prochaine expérience recommandée** : calibration **jointe multi-familles** (profil M exp7 +
  spot isolé exp9, `h_bord_x0` libre non nul) — seule voie pour un gain réel sans sur-ajuster un
  régime. Logs : `donnees/journaux/archive/resultats_{baseline_phase1,calibration_exp7_200A,phase3}_*.log`.

### 30 juillet (suite) — Calibration jointe multi-familles (faite, non adoptée)
`code/scripts/calibrer_joint.py` : fit conjoint bord (exp7 150/200/250 A) + centre (exp9 y=20), vecteur
`[facteur_couplage, h_bas_2d, k_plan, h_bord_x0]`, `h_haut` figé.
- **`k_plan` devient identifiable ≈ 7,3 W/m·K** (vs 3,0) grâce à la famille centre → conductivité
  dans le plan probablement ~2× plus élevée (fort indice physique, à confirmer).
- Centre nettement amélioré (RMSE 16,9→8,0 ; pic TC3 +40→+14 °C) MAIS bord régresse (h_bas_2d élevé
  sur-refroidit les transitoires) → **RMSE global 18,5→19,2** → **non adopté** (θ\* réf. inchangé).
- σ non identifiable en joint (jacobien singulier) → off. `h_bord_x0=0` toujours réfuté.
- **Verdict** : le résidu du bord est **STRUCTUREL** (contraste spatial du M) — aucun coefficient
  uniforme ne le corrige. Le vrai levier = **changement de modèle** (adoucir le M en largeur, forme
  de source), pas la calibration. Logs : `donnees/journaux/archive/resultats_calibration_joint_*.log`.

**Figures**

![Mesure directe de la conductivité dans le plan (campagne longitudinale, spot à x = 60) : (a) étalement en longueur, longueur caractéristique ≈ 26 mm ; (b) refroidissement après coupure, constante de temps ≈ 207 s.](labo/figures/fig_kplan_direct_exp9.png)
*Mesure directe de la conductivité dans le plan (campagne longitudinale, spot à x = 60) : (a) étalement en longueur, longueur caractéristique ≈ 26 mm ; (b) refroidissement après coupure, constante de temps ≈ 207 s.*

### 31 juillet — Forme du M (lambda_bord), contraste réel, piste taux-de-chauffe
Suite de la calibration jointe : on s'attaque à la FORME du M.
- **Le sur-contraste vient de la CL `ψ=0` au chant** (`em/foucault.py`) — exacte pour une nappe
  continue, fausse pour le twill à maille finie (le continuum casse au bord). Prototype
  **`lambda_bord_mm`** (longueur d'extrapolation de bord, analogie du problème de Milne) derrière
  **flag défaut OFF** (`source_spot`/`Essai`/`valider.py`/`calibrer_joint.py`, `lambda=0`
  bit-identique). `lambda≈4 mm` ramène le contraste **3,15 → ~2,1** (= mesuré) → **corrige la
  forme**. MAIS non conservatif en puissance → à θ\* fixe le RMSE global monte (18,5→~23) et un
  θ\* joint avec `lambda=4` reste perdant (27,3). → **prototype archivé, NON adopté**.
  Log : `donnees/journaux/archive/resultats_diag_lambda_bord_em.log`.
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

**Figures**

![Profil en largeur, mesure vs modèle, recalculé en direct : contraste modèle ~3,15 contre ~2,09 mesuré.](labo/figures/fig2_mesure_modele.png)
*Profil en largeur, mesure vs modèle, recalculé en direct : contraste modèle ~3,15 contre ~2,09 mesuré.*

### 31 juillet (suite) — Taux de chauffe : UN SEUL défaut d'étalement in-plane (3D écarté)
Investigation dédiée (`code/scripts/diag/diag_taux_dTdt_sous_hors_spot.py`, `diag_sensibilite_taux_leviers.py`,
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
`donnees/journaux/archive/resultats_calibration_joint_anisotrope*.log`.

**→ Arc modèle CLOS (option B).** Tous les leviers testés/documentés (calib scalaire jointe,
`lambda_bord`, 3D, anisotropie) : le résidu est **irréductible** par le modèle actuel. **Domaine de
validité acté** (cf. `biblio/modele/README.md`) : **valide** en pic/plateau + forme de source + loi
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
  `code/scripts/gen/gen_mfc_reduit.py`, `fig_mfc_reduit.png`.

**Figures**

![Prédiction T(t) au chant pour plusieurs courants.](modele/figures/fig_prediction_chauffe_courant.png)
*Prédiction T(t) au chant pour plusieurs courants.*

![Prédiction des 5 TC, un panneau par courant.](modele/figures/fig_prediction_chauffe_par_courant.png)
*Prédiction des 5 TC, un panneau par courant.*

![Profil en « M » prédit selon le courant.](modele/figures/fig_prediction_profil_M.png)
*Profil en « M » prédit selon le courant.*

![Distribution de température en longueur prédite selon le courant (extrapolation).](modele/figures/fig_prediction_profil_longueur.png)
*Distribution de température en longueur prédite selon le courant (extrapolation).*

![Carte de température à l'interface prédite par le jumeau (empreinte de soudure).](modele/figures/fig_empreinte_soudure.png)
*Carte de température à l'interface prédite par le jumeau (empreinte de soudure).*

![Procédé semi-statique à 4 passes prédit : soudure en deux rails le long des chants, centre non soudé.](modele/figures/fig_procede_semistatique.png)
*Procédé semi-statique à 4 passes prédit : soudure en deux rails le long des chants, centre non soudé.*

![Loi de réglage durée × courant (t ≈ 9,6·10⁵/I²).](modele/figures/fig_loi_reglage.png)
*Loi de réglage durée × courant (t ≈ 9,6·10⁵/I²).*

![MFC réduit (31,75 mm) avec masque de source : M adouci, points chauds vers l'intérieur (signal qualitatif).](modele/figures/fig_mfc_reduit.png)
*MFC réduit (31,75 mm) avec masque de source : M adouci, points chauds vers l'intérieur (signal qualitatif).*

---

### 3-4 août — Consolidation : six décisions actées, huit issues closes

Le mois s'ouvre par une purge de décisions en attente. **`k_plan`** : la config 3,0 est gardée
comme référence physique (#4) ; le `k(T)` décroissant est confirmé par la donnée (k_cold ≈ 8,5
→ k_hot = 2) mais **ne franchit pas le held-out** — il régresse le pic de bord, source-dominé →
#13 close *not planned*. **Écarts vs Lionetto 2017 tranchés** (#5), chacun assorti d'un
**déclencheur de réouverture nommé** — patron réutilisé depuis. **Cote hauteur bobine 5,0 mm**
(#6) et **position de TC1** au centre de la largeur, l'hypothèse « coin y=0 » réfutée (#8).
**Dette de code** (#9) : les leviers réfutés restent derrière flags, avec un registre
`biblio/modele/leviers_refutes.md` — supprimer aurait coûté plus que garder.

**La loi thermostat « capteurs » est rejetée définitivement.** Le fit joint pleine famille la
donne **pire partout** (held-out 30,0 → 41,2) : l'ancien gain « B-2 45 → 23 » tenait à un
facteur propre à B-2 et ne survit pas à un fit qui partage le facteur entre familles.

**Vérification croisée EM** : `eppy` (Grouve, Nagel 2019) sert de **second solveur indépendant**
et corrobore le contraste M ≈ 3 comme physique de plaque mince réelle, champ de réaction
négligeable au régime.

**Figures**

![Définitions de la loi de Biot-Savart, reproduites du dépôt eppy (W.J.B. Grouve) — second solveur EM de vérification.](presentations/figures_schemas/ext/biot_savart_grouve.png)
*Définitions de la loi de Biot-Savart, reproduites du dépôt eppy (W.J.B. Grouve) — second solveur EM de vérification.*

### 7 août — Planificateur de soudage uniforme (#31-#37) — verdict NON

Bibliothèque d'empreintes, planificateur glouton, vérification séquentielle avec chaleur
résiduelle, CLI et carte de couverture. **Verdict : seules de fines bandes de bord se soudent
sans dégrader**, 6-7 % de couverture. Le MFC réduit ajouté comme levier (#39) **ne débloque pas
le centre**. Ces deux verdicts seront rejoués et confirmés le 15 septembre, sous quatre
hypothèses au lieu d'une.

### 12-19 août — L'arc du résidu d'étalement se ferme

**Carte de faisabilité source × conduction** (`lambda_bord` + `k(T)` **ensemble**, la dernière
porte encore ouverte) : **NO-GO**, held-out ~26 °C bien au-delà de la barre. **Anisotropie
kx ≠ ky** (#12) : NO-GO décisif sur données complètes → close *not planned*.

**Quantification d'incertitude** sur toutes les données exp7/exp9 : `k_plan` est **identifiable
à 8,25 ± 0,09**, et le `k_plan` effectif est **constant en courant** (χ²/ddl = 0,18) à ≈ 2,5× la
valeur physique 3,0 — le résidu structurel est donc reconfirmé, pas expliqué. Le θ\* consolidé
est **NO-GO** en held-out (13,8 → 19,3) : la config reste inchangée.

**Six-probe** : l'extraction inverse de conductivité est codée (#49) puis la campagne est
abandonnée (#50, #51 *not planned*). Du code livré pour une mesure qui ne se fera pas.

**Figures**

![Carte de faisabilité source × conduction : aucun réglage n'amène le contraste du M dans la cible sans dégrader le RMSE hors-échantillon (~26 °C).](modele/figures/pareto_source_conduction.png)
*Carte de faisabilité source × conduction : aucun réglage n'amène le contraste du M dans la cible sans dégrader le RMSE hors-échantillon (~26 °C).*

![k_plan effectif identifié à chaque courant : constant (≈ 7,5), environ 2,5× la valeur physique 3,0.](modele/figures/fig_kplan_courant.png)
*k_plan effectif identifié à chaque courant : constant (≈ 7,5), environ 2,5× la valeur physique 3,0.*

### 22 août — La campagne MFC est écrite (#55-#63)

Neuf issues créées d'un bloc, protocole `biblio/labo/protocole_mfc_reduit.md`. **Aucune n'a
encore été exécutée au 16 septembre** — c'est le goulot du projet.

**Figures**

![Fiber flow sous un spot de pression localisé : la matière flue vers tous les bords libres, où les fibres sont expulsées (squeeze-out).](presentations/figures_schemas/fig_fiber_flow_spot_3d.png)
*Fiber flow sous un spot de pression localisé : la matière flue vers tous les bords libres, où les fibres sont expulsées (squeeze-out).*

### 26-31 août — L'essai 231 A valide le cycle, et révèle la fusion

**L'essai réel 231 A valide le cycle prédit** : pics intérieurs TC2/3/4 à ± 12-20 °C (#64).
Les écarts restants sont cadrés : refroidissement modèle ~10 % lent, TC1 coin sous-capté.

**Le plateau 350-390 °C des TC est la signature de la fusion du PEKK** — intuition de
l'utilisateur, validée. La chaleur latente en config valait **130 J/g** (100 % cristallin),
soit ~3× trop ; la valeur physique est **40 J/g** (cristallinité ~30 %). Le modèle de fusion
(L_f physique + transport du bain `k_plan(T>Tf)`) **plafonne l'interface de 865 à 508 °C** et
reproduit le plateau, à coût held-out quasi nul (+0,6). **Non adopté par défaut** (RMSE neutre
sur les TC de bord), mais décisif pour toute décision fondée sur la température d'interface :
la config canonique y produit un **faux positif systématique** de dégradation (#68).

**Correction de bord en x activée par défaut** (`0dab38d`) : l'effondrement de la source aux
extrémités était pathologique, le center-peaking ne l'était pas.

**Figures**

![Cycle semi-statique prédit à 130 A (avance dès que l'interface repasse sous Tg).](labo/figures/fig_cycle_parfait_semistatique_130A.png)
*Cycle semi-statique prédit à 130 A (avance dès que l'interface repasse sous Tg).*

![Cycle semi-statique prédit à 160 A.](labo/figures/fig_cycle_parfait_semistatique_160A.png)
*Cycle semi-statique prédit à 160 A.*

![Cycle semi-statique prédit à 230 A.](labo/figures/fig_cycle_parfait_semistatique_230A.png)
*Cycle semi-statique prédit à 230 A.*

![Cycle semi-statique prédit à 275 A.](labo/figures/fig_cycle_parfait_semistatique_275A.png)
*Cycle semi-statique prédit à 275 A.*

![Seuil de refroidissement entre passes, 120 °C contre Tg (159 °C) : repartir sous Tg raccourcit le cycle de 4 passes de 21 à 34 % (160-275 A) ; 130 A ne soude pas.](labo/figures/fig_cycle_parfait_comparaison_seuil.png)
*Seuil de refroidissement entre passes, 120 °C contre Tg (159 °C) : repartir sous Tg raccourcit le cycle de 4 passes de 21 à 34 % (160-275 A) ; 130 A ne soude pas.*

![Réchauffe maximale de chaque joint déjà soudé par les passes suivantes, rapportée à Tg : avec l'avance au seuil Tg, les joints restent juste sous Tg (−0,2 à −0,4 °C) à tous les courants.](labo/figures/fig_readoucissement_joint.png)
*Réchauffe maximale de chaque joint déjà soudé par les passes suivantes, rapportée à Tg : avec l'avance au seuil Tg, les joints restent juste sous Tg (−0,2 à −0,4 °C) à tous les courants.*

![Cycle 231 A prédit par le modèle seul, avant l'essai (sans données banc).](labo/figures/fig_predit_231A_seul.png)
*Cycle 231 A prédit par le modèle seul, avant l'essai (sans données banc).*

![Cycle 230 A prédit, coupure pilotée sur les TC à 390 °C.](labo/figures/fig_cycle_230A_TC390.png)
*Cycle 230 A prédit, coupure pilotée sur les TC à 390 °C.*

![Essai réel 231 A (26 août) : TC mesurés.](labo/figures/fig_exp_231A_mesure.png)
*Essai réel 231 A (26 août) : TC mesurés.*

![Validation 231 A : TC mesurés vs prédits — pics intérieurs TC2/3/4 à ± 12-20 °C.](labo/figures/fig_compare_230A_vs_reel.png)
*Validation 231 A : TC mesurés vs prédits — pics intérieurs TC2/3/4 à ± 12-20 °C.*

![Validation 231 A : correction du coin x = 0 (TC1).](labo/figures/fig_compare_230A_vs_reel_coin.png)
*Validation 231 A : correction du coin x = 0 (TC1).*

![Confrontation 231 A v2, source canonique, avant correction.](labo/figures/fig_compare_231A_v2.png)
*Confrontation 231 A v2, source canonique, avant correction.*

![Confrontation 231 A v2 après correction de l'artefact de source au bord.](labo/figures/fig_compare_231A_v2_corrige.png)
*Confrontation 231 A v2 après correction de l'artefact de source au bord.*

![Diagramme de parité mesuré / prédit, essai 231 A.](labo/figures/fig_parite_231A.png)
*Diagramme de parité mesuré / prédit, essai 231 A.*

![Analyse de la rampe 231 A : saturation à la fusion (plateau 350-390 °C).](labo/figures/fig_rampe_231A.png)
*Analyse de la rampe 231 A : saturation à la fusion (plateau 350-390 °C).*

![Modèle de fusion sur 231 A : reproduit le plateau, plafond d'interface ~500 °C.](labo/figures/fig_valider_fusion_231A.png)
*Modèle de fusion sur 231 A : reproduit le plateau, plafond d'interface ~500 °C.*

![Ablation chaleur latente × transport du bain : contribution de chaque ingrédient du modèle de fusion.](labo/figures/fig_ablation_fusion_231A.png)
*Ablation chaleur latente × transport du bain : contribution de chaque ingrédient du modèle de fusion.*

![TC4/TC5 : décorrélation accumulation de chaleur vs effet de bord.](labo/figures/fig_axe2_tc45_231A.png)
*TC4/TC5 : décorrélation accumulation de chaleur vs effet de bord.*

![Diagnostic de TC5 au bord : artefact de source.](labo/figures/fig_diag_tc5_bord.png)
*Diagnostic de TC5 au bord : artefact de source.*

![Recalibration sur l'essai 231 A.](labo/figures/fig_valider_recalibration_231A.png)
*Recalibration sur l'essai 231 A.*

![La recalibration sur 231 A, testée sur les essais tenus à l'écart : NO-GO.](labo/figures/fig_heldout_recalibration_231A.png)
*La recalibration sur 231 A, testée sur les essais tenus à l'écart : NO-GO.*

![Diagnostic du refroidissement entre passes (modèle ~10 % trop lent).](labo/figures/fig_diag_refroidissement_231A.png)
*Diagnostic du refroidissement entre passes (modèle ~10 % trop lent).*

![Diagnostic de la conduction latérale, 231 A.](labo/figures/fig_diag_conduction_laterale_231A.png)
*Diagnostic de la conduction latérale, 231 A.*

![Test d'un rayonnement de face sur 231 A.](labo/figures/fig_test_rayonnement_face_231A.png)
*Test d'un rayonnement de face sur 231 A.*

![Rayonnement de face testé sur les campagnes en largeur et en longueur (held-out).](labo/figures/fig_heldout_rayonnement_face.png)
*Rayonnement de face testé sur les campagnes en largeur et en longueur (held-out).*

![Prédiction du cycle à 160 A (volet bas de la campagne de validation).](labo/figures/fig_cycle_160A_prediction.png)
*Prédiction du cycle à 160 A (volet bas de la campagne de validation).*

![Prédiction du cycle à 275 A, disposition v2 (volet haut).](labo/figures/fig_cycle_275A_v2_prediction.png)
*Prédiction du cycle à 275 A, disposition v2 (volet haut).*

### 1-6 septembre — Thermographie plein champ : un défaut de SOURCE, pas de conduction (#69)

Campagne FLIR sur plaque CF/PEKK découplée, plafond sous Tg. Trois résultats, dans cet ordre :

1. **La source est bimodale.** Les deux jambes du hairpin (entraxe 12,35 mm) donnent une
   double bosse que le modèle à pic unique ne résolvait pas. Robuste sur trois conditions.
   Flag `bimodal_sigma_mm` livré, calibré ≈ 2,5 mm.
2. **L'asymétrie était un tilt d'image**, pas de la physique.
3. **Une fois source et tilt traités, `k_plan` ressort ÉLEVÉ (≥ 7,5, pas 3).** Le « k ≈ 3 » du
   premier jour était **confondu avec le défaut de source**. Le résidu structurel d'étalement
   in-plane est donc reconfirmé — et désormais **mesuré en plein champ**, plus seulement déduit
   de thermocouples.

**`h_bord_x0` recalibré en held-out : 250 → 125** (`fc92052`). `= 0` reste **réfuté** (+98 °C
sur TC1) malgré ce que suggérait le près-bord FLIR. L'agrégat « +0,2-0,4 °C » de la correction
de bord masquait en réalité TC1 −72 °C et TC5 +36 °C.

**Figures**

![Montage de la thermographie plein champ : caméra FLIR au-dessus d'une plaque CF/PEKK découplée.](labo/figures/issue69/schema_montage_flir.png)
*Montage de la thermographie plein champ : caméra FLIR au-dessus d'une plaque CF/PEKK découplée.*

![Même montage, format paysage.](presentations/figures_schemas/schema_montage_flir_paysage.png)
*Même montage, format paysage.*

![Champ thermique au pic, recalé en mm.](labo/figures/issue69/champ_mm_pic.png)
*Champ thermique au pic, recalé en mm.*

![Champ thermique à 200 A, recalé en mm.](labo/figures/issue69/champ_mm_200.png)
*Champ thermique à 200 A, recalé en mm.*

![Spot au bord : chaleur confinée à x ≈ 0-50 mm, froide au-delà.](labo/figures/issue69/champ_mm_bord.png)
*Spot au bord : chaleur confinée à x ≈ 0-50 mm, froide au-delà.*

![Profils transverses au pic.](labo/figures/issue69/transverses_pic.png)
*Profils transverses au pic.*

![Profils longitudinaux au pic.](labo/figures/issue69/longitudinaux_pic.png)
*Profils longitudinaux au pic.*

![Comparaison longitudinale rigoureuse mesure / modèle.](labo/figures/issue69/compare_rigoureux_longi.png)
*Comparaison longitudinale rigoureuse mesure / modèle.*

![Comparaison longitudinale à 200 A.](labo/figures/issue69/compare_200_longi.png)
*Comparaison longitudinale à 200 A.*

![Spot au bord : la mesure montre une double bosse, les 4 configurations du modèle un pic unique.](labo/figures/issue69/compare_bord.png)
*Spot au bord : la mesure montre une double bosse, les 4 configurations du modèle un pic unique.*

![Cartes de source, prototype bimodal (deux jambes du hairpin) vs pic unique.](labo/figures/issue69/proto_source_maps.png)
*Cartes de source, prototype bimodal (deux jambes du hairpin) vs pic unique.*

![Profils longitudinaux avec la source bimodale prototype.](labo/figures/issue69/proto_bimodal_longi.png)
*Profils longitudinaux avec la source bimodale prototype.*

![Robustesse de la source bimodale sur trois conditions.](labo/figures/issue69/robustesse.png)
*Robustesse de la source bimodale sur trois conditions.*

![Calibration de la largeur des jambes (σ ≈ 2,5 mm).](labo/figures/issue69/calibration_bimodal.png)
*Calibration de la largeur des jambes (σ ≈ 2,5 mm).*

![Validation du flag bimodal : σ contrôle la profondeur du creux thermique.](labo/figures/issue69/valide_flag_bimodal.png)
*Validation du flag bimodal : σ contrôle la profondeur du creux thermique.*

![Correction du tilt d'image (symétrisation).](labo/figures/issue69/detilt_calibration.png)
*Correction du tilt d'image (symétrisation).*

![k_plan ré-ouvert une fois source et tilt traités : élevé (≥ 7,5), k = 3 donne une largeur bien trop étroite.](labo/figures/issue69/kplan_reouvert.png)
*k_plan ré-ouvert une fois source et tilt traités : élevé (≥ 7,5), k = 3 donne une largeur bien trop étroite.*

![h_bord_x0 ré-ouvert sur le près-bord FLIR.](labo/figures/issue69/hbord_reouvert.png)
*h_bord_x0 ré-ouvert sur le près-bord FLIR.*

![Balayage de h_bord_x0 en held-out : 125 retenu, 0 réfuté.](labo/figures/issue69/hbord_sweep_heldout.png)
*Balayage de h_bord_x0 en held-out : 125 retenu, 0 réfuté.*

### 9-13 septembre — Infrastructure littérature

Zotero + Obsidian sur carte SD, et un **pipeline d'extraction local** (AutoGen + Ollama) sur le
corpus converti. Acquis principal : **l'enveloppe `k_plan` de la littérature est 2,2-2,5
W/(m·K), donc SOUS la config 3,0** — l'écart ×2,5 du modèle n'est **pas** une dispersion de
valeurs publiées, il est à expliquer autrement.

### 14-15 septembre — Le MFC réduit a trois modèles, pas un (#70)

Constat structurel : le MFC est modélisé par la **méthode des images**, c'est-à-dire un
**demi-espace infini** — la longueur du bloc n'entre tout simplement pas dans le calcul du
champ. Aucun raffinement ne fera parler une géométrie que le modèle ne voit pas.

Deux familles nouvelles sont rendues calculables en tronquant l'image, côté observateur et côté
source. Elles **s'accordent entre elles** (contraste 2,62 et 2,49) là où la famille « masque
conservatif » donne 1,03 : celle-ci est **l'intrus**, et elle ne diffère pas par sa finesse mais
par une **affirmation physique** — le flux hors du bloc se reconcentre-t-il, oui ou non ?
Prédiction figée avant campagne, douze figures, issue #70.

Découverte annexe qui éclaire tout le reste : **le centre de la largeur est une ligne nodale
exacte de la dissipation** (y = 20 mm, puissance Joule nulle par symétrie). Il ne chauffe que
par conduction latérale — aucune géométrie de concentrateur ne change cela.

**Figures**

![Champ EM de la bobine seule.](modele/figures/fig_champ_em_1_bobine_seule.png)
*Champ EM de la bobine seule.*

![Champ EM avec le MFC de 55 mm.](modele/figures/fig_champ_em_2_mfc_actuel.png)
*Champ EM avec le MFC de 55 mm.*

![Champ EM avec le MFC réduit.](modele/figures/fig_champ_em_3_mfc_reduit.png)
*Champ EM avec le MFC réduit.*

![Puissance déposée en largeur selon la configuration de MFC.](modele/figures/fig_mfc_cmp_1_puissance.png)
*Puissance déposée en largeur selon la configuration de MFC.*

![Profils d'interface selon la configuration de MFC.](modele/figures/fig_mfc_cmp_2_profils.png)
*Profils d'interface selon la configuration de MFC.*

![Carte de température d'interface au pic, sans MFC.](modele/figures/fig_mfc_cmp_3a_sans_mfc.png)
*Carte de température d'interface au pic, sans MFC.*

![Carte de température d'interface au pic, MFC 55 mm.](modele/figures/fig_mfc_cmp_3b_mfc_55.png)
*Carte de température d'interface au pic, MFC 55 mm.*

![Carte de température d'interface au pic, MFC réduit, famille A.](modele/figures/fig_mfc_cmp_3c_reduit_A.png)
*Carte de température d'interface au pic, MFC réduit, famille A.*

![Carte de température d'interface au pic, MFC réduit, famille B.](modele/figures/fig_mfc_cmp_3d_reduit_B.png)
*Carte de température d'interface au pic, MFC réduit, famille B.*

![Cycles prédits pour chaque configuration de MFC.](modele/figures/fig_mfc_cmp_4_cycles.png)
*Cycles prédits pour chaque configuration de MFC.*

![Carte de puissance déposée (kW/m²), sans MFC.](modele/figures/fig_mfc_cmp_5a_sans_mfc.png)
*Carte de puissance déposée (kW/m²), sans MFC.*

![Carte de puissance déposée (kW/m²), MFC 55 mm.](modele/figures/fig_mfc_cmp_5b_mfc_55.png)
*Carte de puissance déposée (kW/m²), MFC 55 mm.*

![Carte de puissance déposée (kW/m²), MFC réduit, famille A.](modele/figures/fig_mfc_cmp_5c_reduit_A.png)
*Carte de puissance déposée (kW/m²), MFC réduit, famille A.*

![Carte de puissance déposée (kW/m²), MFC réduit, famille B.](modele/figures/fig_mfc_cmp_5d_reduit_B.png)
*Carte de puissance déposée (kW/m²), MFC réduit, famille B.*

![Répartition de la puissance Joule dans l'épaisseur selon la configuration de MFC.](modele/figures/fig_mfc_cmp_6_joule_epaisseur.png)
*Répartition de la puissance Joule dans l'épaisseur selon la configuration de MFC.*

### 15-16 septembre — Plan de passes, pas optimal, et critère de dégradation

- **Le verdict « pas de soudage uniforme » tient dans les quatre hypothèses** de MFC réduit,
  courants élargis à 250 A. Deux défauts corrigés au passage dans le code du planificateur :
  un `h_bord_x0 = 250` figé en dur par-dessus la config, et un bloc de 55 mm passé au calcul de
  champ là où le masque utilisait le bloc réduit.
- **Le pas entre passes a un optimum, et il renverse la comparaison.** Comparées chacune à son
  propre pas, les configurations se classent autrement : le **MFC réduit triple la surface
  soudable sans dégradation** (22,8 % à un pas de 18 mm, contre 7,5 % à 30 mm pour le 55 mm) —
  non par son empreinte, mais parce qu'il **tolère un pas plus serré**.
- **Moduler le courant** ne peut pas changer le rapport chaud/froid de l'état stationnaire
  (vérifié : indépendant de l'amplitude), mais **déplace l'obstacle de la largeur vers les
  extrémités** — au stationnaire, la largeur est pratiquement plate.
- **Le critère de dégradation est refait en temps × température.** L'ancien seuil « pic >
  450 °C » n'avait **aucune provenance** dans le projet et ne voyait qu'un facteur. Une dose
  d'Arrhenius le remplace, **ancrée pour ne créer aucun seuil nouveau**. Conséquence immédiate :
  le résultat de modulation « 100 % de l'interface dans la fenêtre utile » **s'effondre** — le
  pic n'était qu'à 403 °C, mais tenu 1600 s, soit 10 à 19 fois la dose admissible.
- **Le critère de succès de #55 est réécrit** : il désignait une seule des trois familles, celle
  identifiée comme l'intrus. Table de verdict à quatre observables, tous en rapports.

**Figures**

![Carte de couverture du planificateur : seules des bandes de bord se soudent sans dégrader.](modele/figures/fig_plan_soudage_couverture.png)
*Carte de couverture du planificateur : seules des bandes de bord se soudent sans dégrader.*

![Plan de passes pour les familles de MFC réduit.](modele/figures/fig_plan_passes_familles.png)
*Plan de passes pour les familles de MFC réduit.*

![Balayage du pas entre passes : il existe un optimum, et il renverse la comparaison.](modele/figures/fig_balayage_pas_mfc_reduit.png)
*Balayage du pas entre passes : il existe un optimum, et il renverse la comparaison.*

![Positions des passes au pas optimal.](modele/figures/fig_positions_passes_pas_optimal.png)
*Positions des passes au pas optimal.*

![Séquence de 4 passes, MFC réduit.](modele/figures/fig_sequence_4passes_mfc_reduit.png)
*Séquence de 4 passes, MFC réduit.*

![Limite de la modulation du courant : le rapport chaud/froid stationnaire ne change pas.](modele/figures/fig_modulation_courant_limite.png)
*Limite de la modulation du courant : le rapport chaud/froid stationnaire ne change pas.*

![Les deux leviers de conduite (courant et durée).](modele/figures/fig_modulation_deux_leviers.png)
*Les deux leviers de conduite (courant et durée).*

![Critère de dégradation en dose d'Arrhenius (temps × température) à la place du seuil de pic.](modele/figures/fig_critere_dose_degradation.png)
*Critère de dégradation en dose d'Arrhenius (temps × température) à la place du seuil de pic.*

![Substitut de tube : chemins de l'effort de consolidation (issue #71).](labo/figures/fig_substitut_tube_chemins_effort.png)
*Substitut de tube : chemins de l'effort de consolidation (issue #71).*

### 16 septembre — Le critère de dégradation est refait, et les figures y sont migrées

**Le seuil « pic > 450 °C » n'avait aucune provenance** : littéral répété dans dix-sept
scripts, absent de la configuration et de toute référence du corpus ; aucune donnée de cinétique
sur le PEKK dans la bibliographie. Et il ne voyait qu'un facteur — il déclarait identiques une
brève excursion à 450 °C et une demi-heure de maintien à 400 °C.

Il est remplacé par une **dose d'Arrhenius** (`jumeau.thermique.dose_degradation`), **ancrée
pour ne créer aucun seuil nouveau** : `dose = 1` correspond exactement à l'ancien critère relu
comme une exposition — 450 °C pendant une durée de passe. La seule hypothèse ajoutée est `Ea`,
balayée de 100 à 250 kJ/mol faute d'être mesurée ; **un résultat qui change de signe sur ce
balayage est déclaré indécidable**, pas tranché.

**Migration.** Les dix-sept scripts se partageaient en deux usages. Six rendaient un *verdict* :
ils jugent maintenant à la dose (`verifier_sequentiel` gagne `retour_historique=True`, la carte
de pics seule ne permettant aucun verdict qui tienne compte de la durée). Quatre ne traçaient
qu'une *ligne de repère* en l'annonçant comme « la dégradation » : le libellé dit désormais ce
qu'elle est. La **fenêtre de soudage** était contradictoire — une abaque courant × *durée* dont
la borne haute était jugée au pic ; sa borne est l'instant où la dose cumulée atteint 1.

Le glouton du planificateur continue de **cribler** au pic (stocker l'historique de chaque
candidat coûterait ~1 Go) et c'est documenté comme conservateur : sur les cycles courts du
procédé, le pic est le critère *le plus sévère* des deux.

**Ce que la migration déplace.** Le verdict du planificateur ne bouge pas (7,0 % / 0 %) : cycle
court, dose très inférieure à 1. Mais **l'optimum du pas se déplace** — hypothèse corroborée
18,0 → **15,0 mm** (22,8 → **39,2 %** soudé propre), MFC labo 30,0 → **22,5 mm** (7,5 →
**16,2 %**). Le MFC réduit reste devant, et l'écart se creuse.

**Un fait de géométrie révélé au passage** : le bloc n'est pas réduit dans le sens où il avance.
Son empreinte vaut 31,5 mm le long de `x` (le déplacement) et 55 ou 31,75 mm le long de `y`.
Donc le **recouvrement ne dépend que du pas**, jamais de la taille du bloc ; et raccourcir le
MFC agit **en largeur**, laissant 4,1 mm de chant découvert de chaque côté. C'est la raison
géométrique, enfin visible, du « le MFC réduit coupe les lobes de bord » de #39.

⚠️ **Incident de méthode.** Régénérer une note a effacé 126 lignes de prose que j'y avais
ajoutées à la main : c'était un fichier **généré**. Contenu récupéré et déplacé dans les scripts
qui le produisent. Règle : ne jamais éditer à la main un fichier portant une ligne
« Reproduire : … ».

**Les séquences de passes, tracées sans commentaire, montrent ce que les pourcentages
cachaient.** Trois figures — bloc réduit au pas de 15 mm, le même au pas de 22,5 mm, et le bloc
labo 55 mm à 22,5 mm — un panneau par passe, à la même échelle, sans titre ni axes ; seules les
cotes figurent, sur les deux premiers panneaux.

**Au pas de 22,5 mm, les zones soudées restent des îlots disjoints**, un par zone de
recouvrement, qui ne se rejoignent jamais sur la longueur. **À 15 mm elles fusionnent en deux
cordons continus.** Le pas ne règle donc pas seulement *combien* de surface se soude : il décide
si le joint est **continu ou une rangée de points**. Aucun des deux chiffres — 9,2 % contre
39,2 % — ne dit cela, et c'est pourtant une question de tenue mécanique. Cela donne un critère
d'acceptation supplémentaire à **#61** : au pas large, la coupe devrait montrer une alternance
soudé / non-soudé le long de `x`, et non un joint uniforme plus faible.

Deuxième lecture, sur le bloc de 55 mm : **l'îlotage est le même**, donc c'est **le pas qui
commande, pas la géométrie du concentrateur**. L'argument en faveur du MFC réduit n'est pas
qu'il chauffe mieux — c'est qu'il autorise le pas serré qui rend le joint continu.

Et un fait de géométrie que la cotation rend évident : l'empreinte du bloc de 55 mm **déborde la
plaque en largeur** (55 mm pour 40), là où le bloc réduit laisse 4,1 mm de chant découvert de
chaque côté.

**Figures**

![Fenêtre de soudage courant × durée, borne haute jugée à la dose cumulée.](labo/figures/fig_fenetre_soudage.png)
*Fenêtre de soudage courant × durée, borne haute jugée à la dose cumulée.*

![Ce que coûte d'amener toute la matière au-dessus de la fusion en 4 passes.](modele/figures/fig_4passes_toute_matiere_337.png)
*Ce que coûte d'amener toute la matière au-dessus de la fusion en 4 passes.*

![Séquence de passes, MFC réduit au pas de 15 mm : les zones soudées fusionnent en deux cordons continus.](modele/figures/fig_passes_muettes_pas15mm.png)
*Séquence de passes, MFC réduit au pas de 15 mm : les zones soudées fusionnent en deux cordons continus.*

![MFC réduit au pas de 22,5 mm : îlots soudés disjoints.](modele/figures/fig_passes_muettes_pas22mm.png)
*MFC réduit au pas de 22,5 mm : îlots soudés disjoints.*

![MFC 55 mm au pas de 22,5 mm : même îlotage, c'est le pas qui commande.](modele/figures/fig_passes_muettes_mfc55_pas22mm.png)
*MFC 55 mm au pas de 22,5 mm : même îlotage, c'est le pas qui commande.*

![Séquence de passes au pas de 15 mm, MFC réduit.](modele/figures/fig_sequence_passes_mfc_reduit_pas15mm.png)
*Séquence de passes au pas de 15 mm, MFC réduit.*

### 22-23 septembre — La campagne « épaisseur » passe de un à quatre courants

Trois courants de plus sur le même montage à 3 TC empilés (174, 201 et 226 A deux fois),
extraits du classeur source livré par l'utilisateur (`donnees/data/epaisseur_3TC_2026-05/`).
**Le rapport face opposée / interface n'est plus 0,42 mais une fourchette 0,32–0,48** : les deux
répétitions à 226 A couvrent à elles seules toute l'amplitude, sans tendance avec le courant.
Toute calibration visant 0,42 à la décimale ajusterait du bruit d'essai. Surface / interface
vaut 0,84–0,94 sur les quatre courants : « surface ≈ interface » devient multi-condition.
Le relevé brut de la série B (dont B-1 et B-2 sont deux extraits) est archivé à côté.

**Données (essais réalisés en mai 2026 : classeur source `source_MAX-WELDING-DATA-14_05_26.xlsx`
daté du 14/05/26, essai 250 A du 20/05/26 ; intégrés au dépôt le 22/09).** Montage : 3 TC
empilés au même point (x = 60, y = 20 mm) — surface côté bobine, interface (tissu PW), face
opposée ; bobine + MFC fixes au centre, sans translation (protocole antérieur au semi-statique).
Durée de chauffe = de l'onset au pic d'interface (mesurée, pas déclarée).

| Fichier | Courant | Chauffe | Durée relevé | Pic interface | opposée / interface | surface / interface |
|---|---|---|---|---|---|---|
| `174A_v1.txt` | 174,4 A | 59 s | 228 s | 377,7 °C | 0,48 | 0,84 |
| `201A_v1.txt` | 201,6 A | 44 s | 203 s | 390,1 °C | 0,42 | 0,88 |
| `226A_v1.txt` | 226 A | 51 s | 288 s | 394,8 °C | 0,32 | 0,90 |
| `226A_v2.txt` (répétition) | 226 A | 34 s | 184 s | 387,1 °C | 0,44 | 0,87 |
| `chauffe_250A_3TC-epaisseur_2026-05-20.txt` | 250 A | 30 s | 300 s | — | 0,39 | 0,94 |

Rapports pris à l'instant du pic d'interface. Courant lu dans la cellule du classeur, pas
dans le nom de feuille. Fiches d'essai : `code/config/essais/chauffe_*_3TC*.yaml` ; détail et
durées de cycle saisies par l'opérateur : `donnees/data/epaisseur_3TC_2026-05/README.md`.

**Figures**

![Montage à 3 TC empilés au même point : surface, interface, face opposée.](labo/figures/issue74/fig74_montage_3TC.png)
*Montage à 3 TC empilés au même point : surface, interface, face opposée.*

![Les 5 essais à 3 TC : rapport face opposée / interface au pic de 0,32 à 0,48.](labo/figures/issue74/fig74_mesures_3TC.png)
*Les 5 essais à 3 TC : rapport face opposée / interface au pic de 0,32 à 0,48.*

### 28 septembre — Le montage « tube substitut » et le ménage des issues

**Nouveau montage (#73)** : un tube entièrement en CF/PEKK, assemblé à partir de plaques
[45,−45,0,−45,45,0₃]ₛ (murs de 40 mm, dessus et fond de 50 mm, rainures fondues au fer, paroi
**1,68 mm**, caisson fermé, **240 mm** de long, connecteur de 120 mm centré), **sans
contre-pression**. Deux questions : les murs tiennent-ils la pression de consolidation (Q1,
auquel cas la vessie de #71 devient inutile) ; la cavité creuse change-t-elle la thermique de la
face intérieure (Q2) ? Reste ouvert : la face soudée du vrai tube (40 ou 50 mm), qu'aucune note
ne tranche. Schéma à trois vues : `biblio/labo/figures/fig_montage_tube_substitut.png`.

**Ménage des issues : 17 → 13 ouvertes.** Fusions #56 → #58, #61 → #57 (qualité post-soudage),
#59 → #15 (Mesure C), #72 → #66 (validation 160 A et 275 A dans une seule campagne) ; #64 close
(volet 231 A fait) ; dépendances natives #71 ← #73 et #60 ← #55. Ouverture de **#74**
(transfert thermique dans l'épaisseur).

**Figures**

![Montage du tube substitut CF/PEKK (trois vues ; tube 240 mm, connecteur 120 mm).](labo/figures/fig_montage_tube_substitut.png)
*Montage du tube substitut CF/PEKK (trois vues ; tube 240 mm, connecteur 120 mm).*

![Tube substitut : mécanismes en jeu (Q1 tenue des murs, Q2 thermique de la face intérieure).](labo/figures/issue73/fig73_mecanismes.png)
*Tube substitut : mécanismes en jeu (Q1 tenue des murs, Q2 thermique de la face intérieure).*

![Mesures de référence à plat utilisées pour juger le tube.](labo/figures/issue73/fig73_references.png)
*Mesures de référence à plat utilisées pour juger le tube.*

![Instrumentation prévue sur le tube.](labo/figures/issue73/fig73_instrumentation.png)
*Instrumentation prévue sur le tube.*

### 29-30 septembre — Le gradient d'épaisseur : c'est le transport, pas la source (#74)

**Point de référence reproduit** : sur les 5 essais à 3 TC, le 3D donne face opposée /
interface = 0,89 (mesuré 0,32–0,48). **Piste « source » close** : même sans aucune chaleur
déposée sous l'interface, le rapport reste à 0,88 — c'est la vitesse de passage de la chaleur
qui compte (≈ 30 s pour traverser 3,36 mm, pour 60 s de chauffe).

**Pertes de face fortes** (`h_contact` ≈ 100, `h_bas` ≈ 500 W/(m²·K), hors de la borne de
calibration de 300) : les deux rapports tombent dans leur fourchette, mais **NO-GO** — la
validation sur A/B et exp9 casse, et **le refroidissement devient beaucoup trop rapide**
(201 A à +100 s : 35 °C simulés contre 120 °C mesurés). Bon rapport au pic pour une mauvaise
raison ; et caler le facteur sur le point des 3 TC (au centre de la boucle, chauffé par
conduction latérale) est une erreur de méthode.

**Transport ralenti sous l'interface** (k_z du laminé inférieur 0,10 au lieu de 0,64,
`h_contact` 40) : épaisseur dans la fourchette **et** refroidissement de bonne forme. Au meilleur
facteur de chaque configuration (exp9 fixe le facteur, A/B y sont peu sensibles à cause du
thermostat), coût joint **33,3 → 30,9 °C** sur grille fine. (coût joint = moyenne du RMSE TC2–TC4 des séries A/B et du
RMSE TC3 d'exp9 ; tableaux et scripts : `code/scripts/diag/diag_compromis_facteur.py`,
`biblio/labo/figures/issue74/validation_3D.csv`.) Au passage : **le 3D actuel est mieux
calé vers 4,5 que vers 6,01** (coût 42 → 32 °C).

**Variantes.** Convergence du maillage acquise (rapports stables de nz 15 à 51 et de 31×11 à
61×21). **Cp(T) mesuré (Hamon) : aucun effet sur le gradient** — acquis de propriété, pas
levier. **Résistance d'interface levée à la fusion** : corrige les coins des séries A/B
d'environ 60 °C (TC1 +106/+80/+40 → +42/+18/−20 °C), mais échoue sur le 226 A à chauffe longue.
Leur **combinaison** se place entre les deux, sans synergie : frontière de compromis.

**Figures**

![Mécanismes candidats du gradient d'épaisseur.](labo/figures/issue74/fig74_mecanismes.png)
*Mécanismes candidats du gradient d'épaisseur.*

![Essai 201 A à 3 TC : mesure vs 3D actuel.](labo/figures/issue74/fig74_courbes_201A.png)
*Essai 201 A à 3 TC : mesure vs 3D actuel.*

![Carte des pertes de face (h_contact × h_bas) : le bon rapport n'est atteint qu'avec des pertes fortes.](labo/figures/issue74/fig74_carte_pertes.png)
*Carte des pertes de face (h_contact × h_bas) : le bon rapport n'est atteint qu'avec des pertes fortes.*

![Validation du 3D sur les séries A/B et la campagne longitudinale pour chaque jeu de paramètres.](labo/figures/issue74/fig74_validation_3D.png)
*Validation du 3D sur les séries A/B et la campagne longitudinale pour chaque jeu de paramètres.*

![Coût joint en fonction du facteur de couplage, par configuration.](labo/figures/issue74/fig74_compromis_facteur.png)
*Coût joint en fonction du facteur de couplage, par configuration.*

![Combinaison des mécanismes : frontière de compromis, sans synergie.](labo/figures/issue74/fig74_compromis_combinaison.png)
*Combinaison des mécanismes : frontière de compromis, sans synergie.*

![Vue de côté du flux de chaleur, 3D actuel vs transport ralenti sous l'interface (pic et +100 s).](labo/figures/issue74/fig74_flux_epaisseur.png)
*Vue de côté du flux de chaleur, 3D actuel vs transport ralenti sous l'interface (pic et +100 s).*

> **Comment lire la figure.** Coupe verticale x-z à travers la colonne des 3 TC (essai 201 A,
> y = 20 mm), à l'échelle 1:1. Au-dessus de z = 0 : céramique (gris foncé, 2 mm) et les deux brins
> de la bobine (orange). En dessous : l'empilement — stratifié supérieur de 0 à −3,36 mm, interface
> (pointillé blanc) à −3,36 mm, stratifié inférieur jusqu'à la face opposée à −6,82 mm. Couleur =
> température simulée ; flèches blanches = sens du flux de chaleur (longueur ∝ √|q|) ; pastilles =
> les 3 TC mesurés, colorées à leur température mesurée (une pastille de même couleur que le fond =
> accord modèle-mesure). Ligne du haut : au pic d'interface ; ligne du bas : 100 s plus tard.
> Colonne de gauche : 3D actuel — la chaleur traverse tout le stratifié inférieur, la face opposée
> sort à ~330 °C contre 167 °C mesuré. Colonne du milieu : k_z du stratifié inférieur abaissé à
> 0,10 W/(m·K) — la chaleur reste au-dessus de l'interface et la face opposée tombe sur la mesure.
> Colonne de droite : profils T(z) des deux modèles contre les 3 points mesurés ; à +100 s, le
> modèle ralenti s'en rapproche nettement (+50 à +105 °C selon la face), le 3D actuel reste
> 160 à 185 °C trop chaud — aucun des deux ne refroidit encore assez vite au point des 3 TC,
> qui est au centre de la boucle et dont le niveau absolu est faussé par la limite d'étalement
> dans le plan (#74).

### 1er octobre — Correctif : au niveau réel, la résistance levée à la fusion ne tient pas

Les « 5 essais sur 5 » de la résistance levée à la fusion et de la combinaison n'étaient
obtenus qu'au facteur de compromis, où l'interface reste **sous** la fusion au point des 3 TC.
Au niveau réel (interface mesurée à 390 °C), le modèle lève la résistance et la face opposée se
réchauffe (combinaison : 0,63 contre 0,42 mesuré). **La mesure montre une face opposée froide
avec une interface fondue** : le mécanisme est contredit en ce point. **Seul le k_z réduit, qui
ne dépend pas de la température, tient l'épaisseur au niveau réel** — c'est lui qui est retenu
pour les prédictions de #73 et #71. Correctif publié dans #74 (encadré daté, affirmations
marquées « corrigé le 2026-10-01 »).

Figures de compréhension pour #74 : montage à 3 TC, mesures brutes des 5 essais, schéma des
mécanismes, vue de côté du flux de chaleur (`biblio/labo/figures/issue74/`).

**Figures**

![Flux de chaleur pour la combinaison des mécanismes.](labo/figures/issue74/fig74_flux_combinaison.png)
*Flux de chaleur pour la combinaison des mécanismes.*

### 1er-2 octobre — Ce que le jumeau prédit pour le tube substitut (#73)

**Le tube creux ne refroidit pas la face intérieure : il la réchauffe nettement.** Avec le k_z
réduit, spot fixe 201 A : face du bas 204 °C à plat → **299–316 °C** sur le tube (paroi 1,68 mm,
cavité d'air) ; cycle à 4 spots : 213 → 283–301 °C ; plus longtemps au-dessus de Tg. Peu
sensible à la perte de la cavité (h = 2 à 10 : 17 °C), même sens avec le modèle actuel. Pour Q1,
c'est le cas le plus défavorable : une paroi vers 300 °C, au-dessus de Tg et proche de Tf, sous
pression, sans contre-pression. Limites : paroi de dessus seule, 40 mm de large, sans les murs.

**Données de simulation** (`code/scripts/diag/diag_tube_q2.py`, 2 octobre ; grille 31×11×15 ;
« k_z réduit » = k_z 0,10 sous l'interface + h_contact 40 ; « actuel » = k_z uniforme +
h_contact 5 ; à plat = laminé 3,36 mm, h_bas 15 ; tube = paroi 1,68 mm, h_bas de cavité 2/5/10 ;
spot fixe = essai 201 A à 3 TC, facteur 10,4 / 11,6 recalé sur le pic d'interface ; cycle =
spécification A-1, facteur 4,0 / 4,5). Séries : `resultats/tube_q2/*.npz`, tableau
`resultats/tube_q2/synthese.csv`.

| Protocole | Modèle | Géométrie | T interface max | T face du bas max | bas / interface au pic | durée > Tg |
|---|---|---|---|---|---|---|
| spot | k_z réduit | à plat | 387 | 204 | 0,47 | 127 s |
| spot | k_z réduit | tube h = 2 / 5 / 10 | 415 / 413 / 412 | 316 / 309 / 299 | 0,74 / 0,73 / 0,71 | 178 / 177 / 172 s |
| spot | actuel | à plat | 389 | 330 | 0,83 | 179 s |
| spot | actuel | tube h = 2 / 5 / 10 | 469 / 465 / 458 | 437 / 431 / 421 | 0,93 / 0,93 / 0,92 | 186 s |
| cycle | k_z réduit | à plat | 858 | 213 | — | 174 s |
| cycle | k_z réduit | tube h = 2 / 5 / 10 | 871 / 872 / 873 | 301 / 294 / 283 | — | 237 / 224 / 205 s |
| cycle | actuel | à plat | 837 | 331 | — | 316 s |
| cycle | actuel | tube h = 2 / 5 / 10 | 855 / 856 / 857 | 371 / 368 / 362 | — | 325 / 323 / 322 s |

(°C. Le maximum d'interface du cycle, ~860 °C, est un maximum local du modèle, non représentatif
du niveau mesuré : seule la comparaison à plat / tube de la face du bas est exploitée.)

**Longueur du tube** (chiffrage non publié dans #73, à la demande) : par rapport à un tube de
120 mm, un tube allongé refroidit les extrémités du connecteur (TC1 −34 °C, TC5 −39 °C) sans
toucher l'intérieur ; 180 et 240 mm sont équivalents.

**Figures**

![Face intérieure du tube vs face opposée à plat : spot fixe, cycle à 4 passes, sensibilité à la perte de cavité.](labo/figures/issue73/fig73_simulation_face_interieure.png)
*Face intérieure du tube vs face opposée à plat : spot fixe, cycle à 4 passes, sensibilité à la perte de cavité.*

![Tube de 120 mm vs tube allongé : écart sur les TC (non publié dans #73).](labo/figures/fig_tube_allonge_ecart.png)
*Tube de 120 mm vs tube allongé : écart sur les TC (non publié dans #73).*

### 2 octobre — Figures de compréhension pour #73, #71 et #66

Pour chaque issue, trois figures dans le même esprit : schéma des mécanismes, mesures de
référence, instrumentation ou protocole (`biblio/labo/figures/issue73/`, `issue71/`,
`issue66/`). Deux constats en sont sortis :

- **#71** : la face au contact de la future vessie culmine entre 135 et 183 °C à plat — au-dessus
  de l'EPDM / nitrile, juste sous le silicone générique ; sous une paroi de 1,68 mm (≈ 300 °C
  prédits), **seul le Rishon conviendrait**.
- **#66** : la loi en I² est reconfirmée avec la définition d'origine (R² = 0,999, L = 3,4 °C/s ;
  12 °C/s prévus à 160 A, 42 °C/s à 275 A). Et **la disposition v2 n'a aucun TC au point chaud**
  où doit se faire la coupure à 160 A : ajouter des TC sous les spots, ou couper à durée fixe
  sur des durées figées avant la mesure.

**Figures**

![#71 : hauteur du U + plaques face à la course sous l'outil — jeu positif (la vessie porte) ou interférence (les parois court-circuitent la vessie), à froid puis à chaud.](labo/figures/issue71/fig71_condition_cotes.png)
*#71 : hauteur du U + plaques face à la course sous l'outil — jeu positif (la vessie porte) ou interférence (les parois court-circuitent la vessie), à froid puis à chaud.*

![#71 : contrôle croisé — cellule de force et manomètre de vessie ; F = p·A tant qu'aucune paroi ne porte.](labo/figures/issue71/fig71_controle_croise.png)
*#71 : contrôle croisé — cellule de force et manomètre de vessie ; F = p·A tant qu'aucune paroi ne porte.*

![#71 : température maximale mesurée à plat sur la face au contact de la future vessie, face aux limites de service (Rishon, silicone, EPDM/nitrile).](labo/figures/issue71/fig71_temperature_vessie.png)
*#71 : température maximale mesurée à plat sur la face au contact de la future vessie, face aux limites de service (Rishon, silicone, EPDM/nitrile).*

![#66 : essais réalisés par campagne sur l'axe du courant, boîte de calibration et deux cibles (160 / 275 A).](labo/figures/issue66/fig66_domaine.png)
*#66 : essais réalisés par campagne sur l'axe du courant, boîte de calibration et deux cibles (160 / 275 A).*

![#66 : loi en I² et extrapolation aux deux cibles.](labo/figures/issue66/fig66_loi_I2.png)
*#66 : loi en I² et extrapolation aux deux cibles.*

![#66 : TC de la disposition v2 et capteur qui commande la coupure à 160 A et à 275 A.](labo/figures/issue66/fig66_protocoles.png)
*#66 : TC de la disposition v2 et capteur qui commande la coupure à 160 A et à 275 A.*

---

## 3. Résidus ouverts (par priorité)

**1. Résidu structurel d'étalement in-plane — ARC CLOS, limite acceptée.** Le `k_plan` effectif
identifié (≈ 7,5-8,3) vaut ≈ 2,5× la valeur physique 3,0, et la littérature place l'enveloppe
publiée **encore en dessous** (2,2-2,5) : l'écart n'est donc pas une dispersion de valeurs. Tous
les leviers ont été essayés et réfutés — `k_plan` scalaire, `k(T)`, anisotropie kx≠ky, lissage
de source, 3D, et la combinaison source × conduction. La thermographie plein champ (#69) l'a
**mesuré** au lieu de le déduire. C'est une **limite documentée du 2D lumpé**, pas une piste.

**2. Gradient dans l'épaisseur (face opposée) — mécanisme localisé, candidat en main (#74).**
Le 3D sur-chauffe la face opposée (0,89 simulé vs 0,32–0,48 mesuré). C'est le **transport** sous
l'interface, pas la source. Un **k_z réduit dans le laminé inférieur** reproduit l'épaisseur, le
refroidissement et améliore le compromis A/B + exp9 (33,3 → 30,9 °C) ; il n'est **pas adopté** :
gain modeste, forme probablement effective, et l'adoption exige l'inventaire des paramètres
effectifs périmés (`h_contact`, facteur du 3D). Réfutés : `r_contact_interface` constante, pertes
de face fortes (refroidissement trop rapide), résistance levée à la fusion (contredite au niveau
réel), Cp(T). Ce qui départagerait : le support de chaque campagne, ou 3 TC empilés près d'un coin.

**3. Les trois familles de MFC réduit ne sont pas départagées.** Aucun calcul ne peut le faire :
la méthode des images suppose un demi-espace infini. **#55 est le discriminateur**, et son
critère de succès a été réécrit en conséquence le 2026-09-16.

**4. `Ea` de la dégradation n'est pas mesurée.** Le critère de dose est en place, ancré sans
seuil nouveau, et **toutes les figures à verdict y sont migrées** (2026-09-16). Mais son énergie
d'activation reste une hypothèse balayée de 100 à 250 kJ/mol. Tous les verdicts de dégradation
de la campagne MFC en dépendent — et l'optimum du pas s'est déjà déplacé une fois en changeant
de critère. Une TGA la fixerait, pour une rampe de plus sur l'échantillon de la DSC (#14).

**5. `h_bord_x0` reste un paramètre effectif sans base physique.** Recalibré à 125, `=0`
réfuté, mais les chants sont tous libres au montage : il compense autre chose, sans qu'on sache
quoi. Il est apparu le 2026-09-16 que le verdict « la modulation du courant ne peut pas
uniformiser » reposait entièrement sur lui — un signal qu'il mérite mieux qu'un rattrapage.

## 3 bis. Corrections préparées — toutes closes

| Correction | Verdict | Date |
|---|---|---|
| Épaisseur twill 0,28 → **0,20 mm** | **appliquée en config** | 2026-07-30 |
| Fréquence par essai (383 kHz A-3) | **abandonnée** — mesure 5 courants = 388 ± 2 kHz | 2026-07-28 |
| Loi thermostat « capteurs » | **rejetée** — pire partout en fit joint | 2026-08-03 |
| Lissage de source σ (centre-fill) | **non adopté** — sur-ajuste un seul régime | 2026-07-30 |
| `h_bord_x0` | **recalibré 250 → 125** ; `=0` réfuté | 2026-09-06 |
| `k(T)` décroissant | **non adopté** — held-out non franchi | 2026-08-03 |
| Anisotropie kx ≠ ky | **NO-GO décisif** | 2026-08-17 |
| Modèle de fusion (L_f = 40 + transport du bain) | **gardé derrière flag** — gain physique net, RMSE neutre | 2026-08-31 |
| Source bimodale | **livrée**, calibrée ≈ 2,5 mm | 2026-09-02 |
| Correction de bord en x | **active par défaut** | 2026-08-30 |

Il ne reste aucune correction en attente d'intégration. Les leviers réfutés sont conservés
derrière flags avec un registre (`biblio/modele/leviers_refutes.md`) : ils sont le **registre des
négatifs** du projet, et des capacités réutilisables.

---

## 3 ter. Prochaines étapes

**Le projet a un goulot unique : la campagne MFC (#63) n'a pas démarré.** Neuf issues créées le
22 août, le bloc réduit reçu, et tout le travail de modélisation de septembre qui attend une
mesure. Le jumeau a épuisé ce qu'il peut trancher seul — dix des treize issues ouvertes
(au 2026-10-02, après regroupement) sont des mesures.

| # | Étape | Pourquoi maintenant | Bloque |
|---|---|---|---|
| **1** | **#55 — profil en largeur, 5 TC** | le discriminateur des trois familles, critère réécrit, prédictions figées | #60, #62, tout le reste de la campagne |
| **2** | **#15 (absorbe #59) — thermographie des deux MFC** | même montage, même calibration d'émissivité : **une seule séance** | résidu #2 (face opposée) |
| **3** | **#14 — DSC du PEKK, et y ajouter une TGA** | la DSC est déjà planifiée ; la TGA est une rampe de plus sur le même échantillon, et elle fixe `Ea` | résidu #4, rouvre #5 |
| **4** | **#58 (absorbe #56) — fenêtre de soudage et fusion au centre à 250 A** | découle de #55 ; prédictions déjà figées en #70 | #57, #62 |
| ~~5~~ | ~~Propager le critère de dose~~ — **fait le 2026-09-16** | six scripts à verdict migrés, quatre lignes de repère relabellées, fenêtre de soudage passée en dose | — |
| **5** | **TGA sur le PEKK** (à greffer sur la DSC de #14) | `Ea` est la seule hypothèse libre du critère de dose, et tous les verdicts de dégradation en dépendent | résidu #4 |
| **6** | **#73 — tube substitut sans contre-pression** | prédiction faite : face intérieure ≈ 300 °C ; trancher la face soudée (40 / 50 mm) ; instrumenter la face intérieure | #71 (bloquée par #73) |
| **7** | **#66 — validation 160 A et 275 A** | volet bas : prévoir des TC au point chaud ou une coupure à durée figée | — |

**Ce qui n'est pas une prochaine étape** : rouvrir le résidu d'étalement in-plane (arc clos,
tous leviers réfutés), rouvrir `h_bord_x0 = 0` (réfuté, y compris contre le près-bord FLIR), ou
raffiner les familles de MFC par le calcul (structurellement impossible avec la méthode des
images).

---

## 4. Faits établis par l'utilisateur (réponses terrain, 27 juillet)

- **Twill = 0,20 mm** (mesuré) — config à corriger (0,28 → 0,20).
- **Les quatre chants latéraux sont à l'air libre** → `h_bord_x0` n'a aucune base physique,
  c'est un paramètre effectif (contredit l'ancien « bridage x=0 »). Contacts verticaux
  seulement : face inf → céramique (`h_bas`), face sup → céramique d'espacement → MFC (`h_haut`).
- **Le thermostat coupait sur le max des TC d'interface** (cahier de labo : « T max interface
  1/3/5 jamais dépassé ~372 °C ») — valide la loi « capteurs ».

Détail archivé dans `biblio/labo/releves_resolus.md`.

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
- **Une métrique au pic peut être juste pour une mauvaise raison** (2026-09-29) : les pertes de
  face fortes donnaient le bon rapport d'épaisseur au pic et vidaient la colonne en refroidissant.
  Toujours une deuxième métrique indépendante (ici le refroidissement).
- **Un mécanisme dépendant de la température se juge au niveau réel** (2026-10-01) : la
  résistance levée à la fusion « tenait » l'épaisseur à un facteur où l'interface ne fondait pas
  au point de mesure ; au niveau réel, elle se levait et contredisait la mesure.
- **Ne pas caler un niveau sur un point chauffé indirectement** : le point des 3 TC est au centre
  de la boucle (source ≈ 0) ; y caler le facteur fait compenser un autre déficit (×2,8 de puissance).
- **Reprendre la définition d'origine d'une métrique publiée** (2026-10-02) : une pente
  instantanée à 75 °C donnait R² = 0,92 pour la loi en I², la définition d'origine 0,999.

---

## 6. Carte des documents et journaux

**Organisation en deux parties** (2026-07-30) : `biblio/labo/` = côté mesures ;
`biblio/modele/` = côté simulation. Voir `biblio/README.md`, `biblio/labo/README.md`,
`biblio/modele/README.md`.

**Documents (`biblio/`)**
- `journal_avancees.md` — **ce document** (point d'entrée, transverse).
- **`biblio/references/`** (littérature & dépôts de référence) :
  - `references/etat_art_induction.md` — revue de littérature (état de l'art).
  - `references/reference_brassard.md` — dépôt de référence figures (Brassard).
- **`biblio/labo/`** (résultats labo / mesures) :
  - `labo/protocole_exp_dissipation_longitudinale.md` — fiche protocole exp 9.
  - `labo/mesures_a_realiser.md` — mesures encore À FAIRE.
  - `labo/releves_resolus.md` — relevés terrain déjà tranchés (archive).
- **`biblio/modele/`** (résultats modèle numérique) :
  - `modele/figures_catalogue.md` — catalogue des figures.
  - **Campagne MFC (septembre 2026)** : `modele/prediction_mfc_reduit.md` (prédiction figée),
    `modele/prediction_mfc_familles.md` (les trois familles), `modele/plan_passes_familles.md`
    (robustesse du plan de passes, pas resserré, « tout > 337 °C »),
    `modele/balayage_pas_mfc_reduit.md` (pas optimal),
    `modele/sequence_passes_mfc_reduit_pas30mm.md` et `…_pas15mm.md` (la séquence, passe par
    passe), `modele/positions_passes_pas_optimal.md` (où se pose le bloc),
    `modele/4passes_toute_matiere_337.md` (ce que coûte de tout amener au-dessus de la fusion),
    `modele/modulation_courant_limite.md` et `modele/modulation_deux_leviers.md` (conduite du
    courant), `modele/critere_dose_degradation.md` (critère temps × température).
  - **Épaisseur (#74)** : scripts `code/scripts/diag/diag_epaisseur_3d_reference.py`,
    `variantes_epaisseur.py`, `diag_valider_variante.py`, `diag_compromis_facteur.py` ; figures
    `biblio/labo/figures/issue74/`.
  - **Tube substitut (#73)** : `code/scripts/diag/diag_tube_q2.py` (face intérieure),
    `diag_tube_allonge.py` (longueur) ; figures `biblio/labo/figures/issue73/`.
  - **Figures de compréhension** : `biblio/labo/figures/issue71/`, `issue66/`.
  - **Corps d'issues versionnés** : `modele/issue<N>_*.md` — source de vérité du texte publié
    sur GitHub, synchronisé par `code/scripts/gen/sync_issue.py`. Ne pas éditer l'issue dans le
    navigateur : la synchro suivante écraserait sans avertir.
  - `modele/audit_lionetto_2017.md`, `modele/verification_croisee_eppy.md`, `modele/leviers_refutes.md`, `modele/facteur_couplage_decomposition.md`.
- **`biblio/presentations/`** (rapports & présentations) :
  - `presentations/rapport_directrice_jumeau.md` — rapport complet pour la direction.
  - `presentations/rapport_slides_jumeau.md` — trame de présentation (slides).
  - `presentations/synthese_consolidation_uq_2026-08-14.md` — synthèse consolidation UQ.
- `figures/` — **deux dossiers** : `biblio/modele/figures/` (modèle) et `biblio/labo/figures/` (mesures) ;
  variantes `presentation_*`, en place (référencées par les scripts ; PNG 600 dpi).

**Journaux de référence (`donnees/journaux/archive/resultats_*.log`) — état courant**
- `donnees/journaux/archive/resultats_hauteur_5mm_recalibration.log` — correction hauteur + θ\* courant.
- `donnees/journaux/archive/resultats_validation_reference_figures.log` — validation au θ\* courant.
- `donnees/journaux/archive/resultats_diag_forme_source.log` — profil en M (source, pas champ).
- `donnees/journaux/archive/resultats_diag_b2_thermostat_capteurs.log` — résidu B-2 + loi capteurs.
- `donnees/journaux/archive/resultats_diag_hauteur_bobine.log` — cote hauteur + plan image MFC (CAO).
- `donnees/journaux/archive/resultats_geometrie_corrigee_recalibration.log` — correction d'entraxe (étape précédente).

**Journaux d'archive (géométrie/θ\* antérieurs — raisonnements valides, chiffres périmés)**
- `donnees/journaux/archive/resultats_diag_b2_longueur.log`, `donnees/journaux/archive/resultats_diag_cp_kplan.log`,
  `donnees/journaux/archive/resultats_diag_blindage_intercouche.log`, `donnees/journaux/archive/resultats_convergence_maillage.log`,
  `donnees/journaux/archive/resultats_diagnostic_profil_M_em.log`, `donnees/journaux/archive/resultats_champ_reaction_em.log`,
  `donnees/journaux/archive/resultats_test_position_thermostat.log`, et les `resultats_validation_2d_*.log`.

**Code** : `code/src/jumeau/` (em, thermique, identification, validation) ; `code/scripts/` (simuler,
calibrer, valider, figures) ; `code/config/` (geometrie.yaml, materiaux.yaml, essais/) ;
`tests/` (38 tests). `README.md` résume la chaîne physique et les limites connues.
