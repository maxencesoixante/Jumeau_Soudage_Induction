# Journal d'avancement — jumeau numérique soudage induction CF/PEKK

**Projet** : simulation de l'empreinte thermique bobine + concentrateur de flux (CFC) sur
laminés CF/PEKK, soudage par induction semi-statique (maîtrise, LIPEC / ÉTS).
**Dépôt** : `Jumeau_Soudage_Induction` (Python) &nbsp;·&nbsp; **Dernière mise à jour** : 2026-07-27.

> **But de ce document** : point d'entrée unique. Sa lecture donne l'état complet du projet —
> ce que fait le modèle, où il en est, ce qui a été fait et pourquoi, ce qui reste ouvert, et
> où trouver le détail. Les autres documents (`rapport_directrice_jumeau.md`,
> `rapport_slides_jumeau.md`, `mesures_a_realiser.md`, journaux `resultats_*.log`) sont les
> sources détaillées, indexés en fin de document.

---

## 1. État actuel en un coup d'œil

**Ce que le modèle fait.** Chaîne EM → thermique : champ magnétique de la bobine hairpin +
CFC (Biot-Savart + courants images) → courants de Foucault en plaque mince (fonction de
courant ψ, Lin 1993) → source Joule par couche → transfert thermique 3D transitoire avec
fusion (cp apparent). Deux solveurs : **2D lumpé à l'interface** (modèle de travail, ~2-4
min/essai) et 3D complet (cartes, gradient d'épaisseur, ~30 min/essai). Calibration LHS +
NLSQ pondérée par le bruit capteur sur **un** essai (A-1), validée en aveugle sur les autres.

**Géométrie de référence** (corrigée, cf. §2) : brins carrés 6 mm, gap 6,35 mm, **entraxe
12,35 mm**, **hauteur d'axe 5,0 mm** au-dessus du laminé, plan image du CFC au sommet des
brins. Fréquence 388 kHz, `k_plan = 3 W/m·K` (physique).

**θ\* de référence** (modèle 2D, calibré sur A-1, grille 31×11) :

| Paramètre | Valeur | Rôle |
|---|---|---|
| `facteur_couplage` | **6,0123** ± 0,07 | échelle de la source Joule |
| `h_haut` | **30,09** W/m²·K ± 1,3 | perte vers céramique/CFC |
| `h_bas_2d` | **37,42** W/m²·K ± 0,5 | perte vers face opposée/bâti |
| `decalage_x` | 0 (figé) | position bobine↔spot, non mesurée |
| `h_bord_x0` | 250 (figé) | puits de bord x=0 — **effectif, pas physique** (§4) |

**Validation croisée** (grille 61×21, sans recalibrage) — RMSE / |ΔT_max| moyen (°C) :

| Essai | Conditions | RMSE | \|ΔT_max\| |
|---|---|---|---|
| **A-1** (calibration) | 250 A, coupure 400 °C | 35,8 | 25,9 |
| **A-3** (aveugle) | 200 A, coupure 400 °C | 31,7 | 41,3 |
| **B-2** (aveugle) | 250 A, coupure 360 °C | 65,3 | 45,2 |

Le modèle **ordonne et explique** les niveaux de température (séquence spatio-temporelle
juste, transfert à 200 A sans retouche) mais ne pilote pas encore au degré près.
**36 tests** automatisés verts (~2 min).

**Reproduire** :
```bash
python scripts/calibrer.py --modele 2D --essai serieA_A-1 --n-lhs 25 --figer-decalage-x 0
python scripts/valider.py --modele 2D --facteur 6.0123 --decalage-x 0 \
    --h-haut 30.087 --h-bas-2d 37.424 --h-bord-x0 250
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
- Déficit TC1 : auto-échauffement du CFC (0,6-1,4 W) et `decalage_x` **écartés** avec chiffres.
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
- **Plan image du CFC vérifié sur CAO** (coupe + photo de montage) : le concentrateur est bien
  au-dessus des brins, semelle au sommet des brins — la formule reste inchangée.
- **Hauteur corrigée 6,8 → 5,0 mm** (cote physique) + recalibration → θ\* de référence courant.
  Arbitrage : la cote juste **dégrade l'écart de pic** — signe que la source est trop
  concentrée, pas une raison de garder une cote fausse.
- **Diagnostic du profil en « M »** : le champ `Bz` est uniforme en largeur ; le M vient
  **entièrement de l'écrasement du courant de Foucault** (`ψ=0` au bord), pas du champ. Le
  levier « CFC fini » est donc mal dirigé pour la largeur. Contraste ~2,4×.
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
  sans céramique était un artefact du gap 0. → **Le levier « adoucir le M » est ÉCARTÉ.** Reste :
  absolus non confrontés (chauffe manuelle courte) → campagne multi-ampérages avec chauffe
  standardisée à venir (150/200/250 A, 3 reps ; pas 300 A car chants ~962 °C > dégradation).

---

## 3. Résidus ouverts (par priorité)

1. **Amplitude du profil en « M » — LARGEMENT RÉSOLU (28 juillet).** La cartographie
   bord→centre a d'abord semblé montrer un modèle qui sur-contraste (série SANS céramique,
   contraste ~1,85 vs 2,46). Mais la **reprise AVEC céramique** (géométrie standard,
   `data/exp7_bord-centre_2026-07-28_avec-ceramique/`) donne un contraste mesuré **2,17 ≈ 2,43
   modèle**, forme normalisée quasi superposée : **le modèle a raison sur l'amplitude du M**. Le
   « sur-contraste » venait du retrait de la céramique (gap 0), pas du modèle. → **Le levier
   « adoucir le M » (courants de retour 3D / contact twill) n'est plus justifié.** Restes :
   TC1 (un chant) mort, absolus non confrontés (chauffe courte), essai unique → à confirmer.
2. **Vitesse de chauffe / lobes A/B trop froids — LE résidu dominant du RMSE.** Les taux
   simulés restent ~2× trop lents et les TC A/B (TC2-4, sur les lobes y=0) sont sous-estimés de
   20-30 °C. Distinct du profil en M (forme validée). **Le lissage de source NE le corrige PAS**
   (cf. ci-dessous) : il redistribue centre↑/lobes↓, ce qui baisse encore les lobes A/B. Cause
   probable : la source/le taux sur la montée, pas la répartition spatiale.

**Résidu résolu / tranché (28 juillet) — le remplissage du centre.** La cartographie 200 A
avec céramique (chauffe longue, v4/v5/v6) montrait le centre du modèle ~4× trop lent (à chant
ΔT=200 : centre 76 mesuré vs 18 modèle). Diagnostic (`resultats_diag_centre_transitoire.log`) :
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
   à activer conjointement avec la correction du M. Réf. `resultats_diag_b2_thermostat_capteurs.log`.
4. **Déficit de chauffe en surface (TC1).** 5-6× trop lent, mécanisme non identifié ; attaqué
   par la mesure de la face du CFC (exp 8).

## 3 bis. Corrections préparées (à intégrer ensemble à la prochaine recalibration)

| Correction | Source | Statut |
|---|---|---|
| Loi thermostat « capteurs » | cahier de labo + données B-2 | flag prêt (défaut off) |
| Épaisseur twill 0,28 → **0,20 mm** | mesure user | préparée (commentaire config) |
| Retrait/révision `h_bord_x0` | chants libres (user) | requalifié effectif, à retravailler |
| Fréquence A-3 (200 A) 388 → **383 kHz** | relevé user | préparée (fréquence par essai à ajouter) |

Ces trois se recalibrent **ensemble**, idéalement après la cartographie bord→centre (elles
sont couplées au profil en M).

---

## 4. Faits établis par l'utilisateur (réponses terrain, 27 juillet)

- **Twill = 0,20 mm** (mesuré) — config à corriger (0,28 → 0,20).
- **Les quatre chants latéraux sont à l'air libre** → `h_bord_x0` n'a aucune base physique,
  c'est un paramètre effectif (contredit l'ancien « bridage x=0 »). Contacts verticaux
  seulement : face inf → céramique (`h_bas`), face sup → céramique d'espacement → CFC (`h_haut`).
- **Le thermostat coupait sur le max des TC d'interface** (cahier de labo : « T max interface
  1/3/5 jamais dépassé ~372 °C ») — valide la loi « capteurs ».

Détail archivé dans `docs/releves_resolus.md`.

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

**Documents (`docs/`)**
- `journal_avancees.md` — **ce document** (point d'entrée).
- `rapport_directrice_jumeau.md` / `.docx` — rapport complet pour la direction.
- `rapport_slides_jumeau.md` — trame de présentation (slides).
- `mesures_a_realiser.md` / `.docx` — mesures encore À FAIRE.
- `releves_resolus.md` — relevés terrain déjà tranchés (archive).
- `etat_art_induction.md` — revue de littérature.

**Journaux de référence (`resultats_*.log`, racine) — état courant**
- `resultats_hauteur_5mm_recalibration.log` — correction hauteur + θ\* courant.
- `resultats_validation_reference_figures.log` — validation au θ\* courant.
- `resultats_diag_forme_source.log` — profil en M (source, pas champ).
- `resultats_diag_b2_thermostat_capteurs.log` — résidu B-2 + loi capteurs.
- `resultats_diag_hauteur_bobine.log` — cote hauteur + plan image CFC (CAO).
- `resultats_geometrie_corrigee_recalibration.log` — correction d'entraxe (étape précédente).

**Journaux d'archive (géométrie/θ\* antérieurs — raisonnements valides, chiffres périmés)**
- `resultats_diag_b2_longueur.log`, `resultats_diag_cp_kplan.log`,
  `resultats_diag_blindage_intercouche.log`, `resultats_convergence_maillage.log`,
  `resultats_diagnostic_profil_M_em.log`, `resultats_champ_reaction_em.log`,
  `resultats_test_position_thermostat.log`, et les `resultats_validation_2d_*.log`.

**Code** : `src/jumeau/` (em, thermique, identification, validation) ; `scripts/` (simuler,
calibrer, valider, figures) ; `config/` (geometrie.yaml, materiaux.yaml, essais/) ;
`tests/` (36 tests). `README.md` résume la chaîne physique et les limites connues.
