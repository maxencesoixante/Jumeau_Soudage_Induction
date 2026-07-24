# Jumeau numérique du soudage par induction CF/PEKK — rapport de présentation

**Objet** : trame de présentation (slides) de l'état d'avancement du jumeau numérique et
de la suite du travail.
**Date de l'état des lieux** : 2026-07-21 (commit `e4eb640`).
**Dépôt** : `~/PycharmProjects/Jumeau_Soudage_Induction` — 34 tests `pytest` verts (3 min).

> **Comment lire ce document** : une section `## Slide N` = une diapositive. Les puces
> sont rédigées pour être copiées telles quelles ; les blocs *Figure* indiquent le
> visuel à insérer ; les blocs *À dire* sont des notes d'orateur (ne pas mettre sur la
> diapo). Durée visée : ~20 min + questions, soit 18 diapositives utiles + annexes.

---

## Slide 1 — Titre

**Jumeau numérique du soudage par induction de composites CF/PEKK**
Prédiction de l'empreinte thermique bobine + concentrateur de flux, et confrontation aux
essais semi-statiques

Maxence Dubois — maîtrise, LIPEC / ÉTS
Date de la présentation

*À dire* : le jumeau est le volet numérique du projet ; il ne remplace pas la campagne
expérimentale, il l'exploite et la questionne.

---

## Slide 2 — Pourquoi un jumeau numérique

- **Le procédé est piloté à l'aveugle dans la largeur** : 5 thermocouples donnent 5 points ;
  la soudure, elle, se joue sur toute la surface 120 × 40 mm.
- **La fenêtre de mise en œuvre est étroite** : fusion PEKK 337 °C, cible 355–390 °C,
  dégradation ~450 °C. Quelques dizaines de °C séparent le joint réussi du joint dégradé.
- **Objectifs du modèle**
  1. prédire la **carte de température** (l'empreinte thermique) là où aucun capteur ne se
     trouve ;
  2. servir de **plant model** pour un futur contrôle prédictif (MPC) du procédé ;
  3. constituer un **chapitre de mémoire** à part entière.

*À dire* : la valeur du jumeau n'est pas de reproduire les thermocouples (on les a), mais
d'interpoler entre eux et d'extrapoler aux configurations non essayées.

---

## Slide 3 — Le montage modélisé (rappel)

- Coupons **CF/PEKK `[45/-45/0/90]₃ₛ`, 120 × 40 × 3,36 mm**, recouvrement plein.
- **Pli twill (sergé) suscepteur à l'interface** de soudure — siège principal des courants
  de Foucault.
- **Bobine hairpin + concentrateur de flux (CFC) Fluxtrol Ferrotron 559H** (µr ≈ 16),
  55 × 31,5 × 12 mm, **grand côté 55 mm parallèle à la largeur** de l'échantillon.
- Générateur **Ambrell EASYHEAT 4,2 kW — 388 kHz relevé machine**, 200 / 250 A.
- Gap bobine–laminé **2 mm** (céramique d'espacement), pression pneumatique.
- Procédé **semi-statique : 4 empreintes successives** le long des 120 mm (pas 30 mm).

*Figure* : schéma de la chaîne d'efforts (piston → CFC → céramique → laminé sup →
interface → laminé inf) ou photo de montage M2 du cahier.

*À dire* : deux faits géométriques structurent tout le reste — la bobine et le CFC
**débordent** de la largeur de 40 mm des deux côtés, et le twill est ~40× plus conducteur
que le laminé.

---

## Slide 4 — Architecture du jumeau (vue d'ensemble)

```
Bobine hairpin (Biot–Savart)  +  CFC (courants images, µr=16)
        │  Bz(x, y) à chaque couche
        ▼
Courants de Foucault, plaque mince anisotrope   ψ : ∇·(ρ∇ψ) = ω·Bz   (Lin 1993)
        │  q = ρxx·Jx² + ρyy·Jy²   par couche (twill / laminé sup / laminé inf)
        ▼
Source Joule volumique Q(x, y, z)
        │
        ▼
Thermique transitoire (méthode des lignes, BDF, jacobien creux)
   cp apparent avec pic de fusion  ·  convection + rayonnement  ·  puits céramique
        │
        ▼
Procédé : 4 empreintes séquentielles + coupure sur consigne de température
        │
        ▼
Carte de température  →  confrontation thermocouples  →  calibration LHS + NLSQ
```

*À dire* : chaque bloc est un module Python testé indépendamment ; c'est ce qui permet de
répondre « d'où vient cet écart ? » au lieu de recalibrer aveuglément.

---

## Slide 5 — Hypothèses simplificatrices (toutes sourcées)

| Hypothèse | Source |
|---|---|
| Plaque mince EM, courants plans (δ ≈ 6 mm > 3,36 mm) | Lin 1993 |
| Laminé homogénéisé, µr = 1 | O'Shaughnessey 2014 ; Grouve 2020 |
| CFC = demi-espace perméable (courants images) | approximation 1er ordre |
| Fusion par cp apparent gaussien (Tf 337 °C, Lf 130 kJ/kg) | Samanis 2026 ; Greco & Maffezzoli |
| Pertes propres du CFC négligées | **chiffré** : 0,6–1,4 W vs 50–260 W dans le twill (fiche Fluxtrol) |
| Pertes diélectriques négligées | O'Shaughnessey 2014 §3.1.3 |
| Fréquence figée à 388 kHz | relevé machine (corrélée au facteur d'échelle) |

*À dire* : insister sur la ligne CFC — c'est une hypothèse qui a été **vérifiée
numériquement avec la fiche constructeur**, pas supposée. C'est la marque de fabrique du
travail : chaque hypothèse écartée l'est avec un chiffre.

---

## Slide 6 — Deux modèles thermiques : 3D puis 2D

| | Modèle 3D | Modèle 2D lumpé (**modèle de travail**) |
|---|---|---|
| Domaine | 120 × 40 mm × épaisseur du stack | plan de l'interface uniquement |
| Résout | gradient dans l'épaisseur | température d'interface |
| Paramètres de perte | `h_contact`, `h_bas` | `h_haut`, `h_bas_2d` |
| Coût | ~30 min / essai | **~2–4 min / essai** |
| Usage | gradient d'épaisseur, cartes de Fig. 4 | calibration + validation quotidiennes |

**Pourquoi ce passage au 2D** : les 5 thermocouples des Séries A/B sont **tous à
l'interface** (confirmé 2026-07-20). Résoudre l'épaisseur ne sert alors qu'à alimenter un
écart structurel non corrigeable (cf. slide 13), au prix d'un facteur 10 sur le temps de
calcul.

*À dire* : ce n'est pas un abandon du 3D — le 3D reste dans le dépôt et sert aux cartes ;
c'est un choix de modèle adapté à la mesure disponible.

---

## Slide 7 — Ce que le modèle produit : l'empreinte thermique

*Figure* : `resultats/serieA_A-1_empreinte_thermique_fig4_plafonne.png`
(4 panneaux — carte de température à l'interface à la fin de chaque empreinte, cadre CFC
en pointillés rouges, échelle plafonnée à 480 °C)

- Analogue **semi-statique** de la Fig. 4 de Lionetto *et al.* (2017), qui présentait une
  bobine avançant en continu ; ici la tête est **indexée sur 4 empreintes**.
- La zone chaude progresse le long des 120 mm ; le refroidissement inter-passes est visible.
- Script réutilisable : `scripts/figure_empreinte.py` (cache `.npz`, échelle réglable).

*À dire* : c'est le livrable central — la carte que l'expérience ne donne pas.

---

## Slide 8 — Le résultat le plus discutable : le profil en « M »

*Figure* : une carte d'interface seule (zoom sur une empreinte), montrant les deux lobes
chauds en y = 0 / 40 mm et le creux central.

- Le modèle prédit **deux lobes chauds sur les chants** et un **creux au centre** de la
  largeur.
- **Mécanisme, démontré numériquement** : la bobine ET le CFC (55 mm) **débordent** de
  l'échantillon (40 mm) → Bz quasi uniforme sur la largeur → les boucles de courant ne
  peuvent se refermer qu'en longeant les deux bords. C'est le *transverse-flux edge effect*
  classique du chauffage par induction de bandes plus étroites que l'inducteur.
- **Vérifié** : aucun courant ne traverse le chant (`max|Jy|` = 0 exactement sur y = 0 et
  y = 40 mm ; `∇·J` ≈ 7·10⁻⁸). La condition limite n'est pas en cause.
- **Cohérent avec l'observation** : squeeze-out festonné localisé sur les chants ;
  recommandation COMPAAM de réduire le MFC pour limiter les effets de bord.
- **Réserve honnête** : l'amplitude du contraste est probablement **surestimée** (rapport
  T(bord)/T(centre) ≈ 2,3–4,6 en fin d'impulsion après diffusion).

*À dire* : c'est le point où le modèle apporte une **prédiction falsifiable** — et il
existe une manip simple pour la trancher (slide 17).

---

## Slide 9 — Calibration : 3 paramètres, une seule fois

**Méthode** : hypercube latin (25 points) → moindres carrés non linéaires pondérés par le
bruit capteur (σ = std(diff)/√2). Pipeline hérité du jumeau 1D et de son test « boîte
noire » (Samanis 2026 §2.3).

**θ\* identifié sur A-1** (modèle 2D, 5 TC, grille de calibration 31 × 11) :

| Paramètre | Valeur | Écart-type | Rôle |
|---|---|---|---|
| `facteur_couplage` | **4,0975** | ± 0,031 | échelle de la source Joule (blindage, contacts, σ) |
| `h_haut` | **11,32** W/m²·K | ± 1,42 | perte vers le puits céramique/CFC |
| `h_bas_2d` | **51,64** W/m²·K | ± 0,67 | perte vers la face opposée / bâti |
| `decalage_x` | 0 (**figé**) | — | position bobine ↔ montage, non mesurée |
| `h_bord_x0` | 250 W/m²·K (figé) | — | puits au chant bridé x = 0 |

- **Corrélations toutes ≤ 0,57** → pas de quasi-non-identifiabilité (le piège `f_I`/`r_I`
  du jumeau 1D est évité).
- `decalage_x` a dû être **figé** : corrélation 0,985 avec `facteur_couplage` sur le fit
  joint, et railing sur sa borne — cas d'école de non-identifiabilité, documenté.

*À dire* : la discipline appliquée est « on calibre sur UN essai, on valide sur les autres
sans y retoucher ».

---

## Slide 10 — Validation croisée (sans recalibrage)

**θ\* calibré sur A-1 uniquement**, appliqué tel quel aux essais aveugles. Maillage de
validation 61 × 21 (dx = dy = 2 mm).

| Essai | Conditions | RMSE moyen | Écart de pic moyen |
|---|---|---|---|
| **A-1** (calibration) | 250 A, coupure 400 °C | 39,2 °C | 46,0 °C |
| **A-3** (aveugle) | **200 A**, coupure 400 °C | **32,7 °C** | 31,0 °C |
| **B-2** (aveugle) | 250 A, coupure 360 °C | 68,0 °C | **12,3 °C** |

*Figure* : `resultats/serieA_A-1_courbes_validation.png` (5 TC, 4 impulsions) — la plus
lisible ; `serieA_A-3_courbes_validation.png` en variante pour l'essai aveugle à 200 A.

- **Le modèle transfère à 200 A sans retouche** — l'essai aveugle à courant différent est
  le mieux prédit en RMSE. La loi en I² et l'asservissement tiennent.
- **Ce qui reste** : un dépassement de pic homogène de +40 à +60 °C sur A-1, et un plateau
  trop froid. Structurel, pas paramétrique (cf. slide 12).

**Comment lire la figure (3 observations à commenter à l'oral)**

1. **La séquence spatio-temporelle est juste** : chaque thermocouple devient le plus chaud
   à son tour, dans le bon ordre et au bon instant, au passage de l'empreinte devant lui
   (TC1 → TC2/TC3 → TC4 → TC5). C'est le résultat le plus solide de la figure : le modèle
   « sait où est la tête ».
2. **Les pics simulés dépassent** systématiquement les pics mesurés de 40 à 60 °C.
3. **Le refroidissement simulé est trop rapide** : entre les passes, les courbes simulées
   retombent vers 20–40 °C alors que les mesures se stabilisent à 80–120 °C. C'est la
   signature « plateau trop froid » — le modèle évacue trop d'énergie entre les impulsions
   (ou n'en a pas assez déposé loin du spot actif).

*À dire* : ne pas survendre. Un RMSE de 30–70 °C sur une fenêtre de mise en œuvre de
35 °C signifie que le modèle **ordonne** et **explique** correctement, mais ne pilote pas
encore.

*À dire* : ne pas survendre. Un RMSE de 30–70 °C sur une fenêtre de mise en œuvre de
35 °C signifie que le modèle **ordonne** et **explique** correctement, mais ne pilote pas
encore.

---

## Slide 11 — Température et degré de fusion (analogue Lionetto Fig. 5)

*Figure* : `resultats/chauffe_250A_3TC_fusion_fig5.png`

- Panneau haut : température d'interface et de surface, simulée + mesurée.
- Panneau bas : **degré de fusion Xm(t)** et fenêtre « état fondu » (Xm ≥ 0,99).
- Xm = fonction de répartition du pic gaussien de fusion du cp apparent — même définition
  que l'éq. 8 de Lionetto (approche statistique Greco & Maffezzoli).
- **Résultat exploitable pour le mémoire : temps à l'état fondu mesuré = 19 s**
  (t = 23 → 42 s), très proche des ~19 s de Lionetto à 300 A / 2 mm/s.

> ⚠ **La figure existante date du modèle 3D** (2026-07-18, facteur calé sur le pic).
> Le chiffre de 19 s, lui, est **déduit de la mesure** et reste valable. Régénérer la
> figure au θ\* courant avant la présentation si la courbe simulée est montrée.

*À dire* : c'est le critère de qualité de soudure le plus directement comparable à la
littérature ; il ne dépend pas du modèle (il est déduit de la mesure), ce qui le rend
robuste.

---

## Slide 12 — Ce que trois enquêtes ont **éliminé** (résultats négatifs)

Chaque piste a été testée à θ\* figé, chiffrée, et archivée dans le dépôt.

| Hypothèse testée | Verdict | Chiffre clé |
|---|---|---|
| Artefacts de **maillage** (lecture TC, nœud de contrôle) | **Confirmée et corrigée** | −77 °C sur le résidu TC4 ; −56 °C sur TC5 |
| **Auto-échauffement du CFC** | Écartée | 0,6–1,4 W, soit 1–2 ordres de grandeur trop faible |
| **Position de lecture du thermostat** | Écartée | contrôler au bord fait chuter l'écart de +46 à −107 °C |
| **Décalage de position bobine** `decalage_x` | Écartée pour TC1 | Q(TC1)/Q(TC2) ≤ 0,12 vs 1,71 requis |
| **Champ de réaction EM** (blindage auto-cohérent) | Implémenté, puis **écarté** | effet réel ~0,2–0,6 %, pas les ~100 % espérés |

*À dire* : la moitié du travail des dernières semaines est constituée de résultats
négatifs **documentés**. C'est ce qui empêche de tourner en rond et ce qui fait le contenu
d'un chapitre de mémoire honnête.

---

## Slide 13 — Le diagnostic central : un contraste spatial trop fort

- **Dans la réalité** : la régulation coupe sur un capteur de bord à 400 °C, et **tous les
  autres capteurs de bord atteignent aussi ~400 °C**.
- **Dans le modèle** : couper au bord à 400 °C laisse les autres capteurs à **250–320 °C**.
- Conclusion : le modèle **concentre trop la puissance** — en largeur (lobes) *et* en
  longueur (les TC pénalisés sont à des x variés). La section active atteint la consigne et
  coupe la source avant que le reste de la plaque ait encaissé son énergie.
- Signature cohérente sur les trois essais : **pics trop hauts, plateau trop froid, biais
  global négatif** — directement visible sur les courbes de la slide 10 (les pointillés
  simulés dépassent au pic puis retombent bien en dessous des mesures entre les passes).

*À dire* : c'est LE point ouvert. Il ne se règle pas par calibration (aucune combinaison
des 3 paramètres n'abaisse les pics sans casser la trajectoire) : c'est la **forme** de la
source qui est en cause, pas son échelle.

---

## Slide 14 — Le déficit TC1 (surface) : mécanisme non identifié

- Sur l'essai de chauffe instrumenté en épaisseur, **TC1 chauffe 5–6× trop lentement** dans
  le modèle : 37,7 °C/s mesuré contre ~6,3 °C/s simulé.
- Trois explications testées et **écartées** : condition limite thermique, diffusion depuis
  l'interface (τ ≈ 28,5 s ≫ 1 s), auto-échauffement du CFC, décalage de bobine.
- Origine suspectée : **répartition de puissance entre couches** (le twill est ~40× plus
  conducteur que le laminé) ou effet de champ proche non capturé par la plaque mince.
- **Aucune mesure ne permet de trancher aujourd'hui** : aucun essai ne mesure la
  température du CFC lui-même.

*À dire* : c'est la limite qu'on assume et qui justifie le passage au modèle 2D — on ne
prétend pas prédire la surface.

---

## Slide 15 — Couche IA conversationnelle (démonstrateur)

*Figure* : capture d'écran de l'interface Gradio, si disponible.

- Surcouche multi-agents **100 % locale** (Ollama, aucun appel réseau) posée **par-dessus**
  le solveur, sans le modifier — architecture inspirée de MatAgent (Purdue).
- Un LLM local orchestre trois outils : `config_essai()` → `lancer_simulation()` →
  `tracer_resultats()`, avec **vérifications physiques embarquées** et **auto-correction**
  sur erreur.
- Intérêt : abaisser la barrière d'usage du jumeau (formuler un essai en langage naturel)
  et préfigurer le pilotage assisté.

*À dire* : à présenter comme un démonstrateur exploratoire, pas comme un résultat
scientifique — la valeur est dans l'accessibilité de l'outil.

---

## Slide 16 — Bilan de l'état d'avancement

**Acquis**

- Chaîne EM → thermique complète, modulaire, **34 tests automatisés** (vérifications
  analytiques : Biot–Savart vs formule de la boucle, conservation d'énergie, régression
  3D ↔ 1D).
- Calibration **identifiable** (corrélations ≤ 0,57) sur un seul essai, **validée sans
  retouche** sur deux essais aveugles, dont un à courant différent.
- Deux figures directement comparables à la littérature (Lionetto Fig. 4 et Fig. 5).
- Étude de convergence de maillage ayant **corrigé deux artefacts numériques réels**.
- Cinq pistes physiques testées et tranchées, dont trois par résultat négatif chiffré.

**Limites assumées**

- Contraste spatial trop fort → pics +40/+60 °C, plateau trop froid.
- Surface (TC1) non prédictible : mécanisme non identifié.
- Pas de mécanique (pression, squeeze-out) ni de cinétique de cristallisation.
- Propriétés matériaux **indépendantes de la température**.

---

## Slide 17 — Suite : ce qu'il faut MESURER

Trois manips discriminantes, par ordre de rapport valeur/effort :

1. **Cartographie bord → centre** (3–5 TC en ligne sur la largeur 40 mm, à l'interface,
   mêmes paramètres que B-2). ⟶ tranche directement le profil en « M » : le modèle prédit
   bord chaud / centre froid, les essais actuels suggèrent l'inverse. *La manip est déjà
   décrite au cahier §2.1.4.*
2. **Température du CFC** (thermocouple ou caméra IR sur sa face active pendant une
   chauffe). ⟶ seule mesure capable d'attaquer le déficit TC1.
3. **Position relative bobine / CFC / thermocouples** (relevé métrologique). ⟶ lève
   l'incertitude qui a forcé à figer `decalage_x`.

*À dire* : la priorité n'est plus de coder, elle est de mesurer. Le modèle est arrivé au
point où il pose des questions expérimentales précises.

---

## Slide 18 — Suite : ce qu'il faut MODÉLISER

Par ordre de priorité, avec l'incertitude assumée :

1. **Modèle de CFC fini** (redistribution du flux par la semelle polaire) — remplacer
   l'approximation par courants images. *C'est le levier principal identifié : il change la
   forme de la source, pas son échelle.* Nécessite un refit complet de θ\* derrière.
   ⚠ Effort : plusieurs jours de travail EM dédié (FEM/BEM ou modèle de semelle).
2. **Forme du blindage inter-couches** — l'écran actuel `e^(−2t/δ)` (onde plane) est-il
   adapté à une nappe de courant plane ? Le calcul rigoureux nappe-à-nappe suggère un
   blindage plus faible, ce qui redistribuerait la puissance entre couches — piste possible
   pour TC1.
3. **Propriétés dépendantes de la température** σ(T), cp(T) — mise en garde explicite
   d'O'Shaughnessey et Duhovic ; expliquerait qu'un facteur unique ne colle pas
   simultanément à la montée, au pic et à la décroissance.
4. **Cinétique de cristallisation** (Ozawa) — complèterait la Fig. 5 avec le degré de
   cristallinité, et donnerait un critère de qualité de joint au refroidissement.

*À dire* : le point 1 est celui qui, s'il fonctionne, résout le diagnostic de la slide 13.

---

## Slide 19 — Horizon : du jumeau au contrôle

```
Aujourd'hui          Court terme                 Objectif
────────────         ─────────────               ────────
Modèle validé   →    CFC fini + σ(T)        →    Plant model fiable
sur 3 essais         + manips discriminantes      ↓
                                                 Contrôle prédictif (MPC)
                                                 du courant en temps réel
```

- Le simulateur actuel est déjà le **plant model** de cette boucle ; ce qui manque est la
  fidélité spatiale, pas l'architecture.
- Verrou identifié : le temps de calcul (2–4 min/essai) devra descendre sous la seconde
  → modèle réduit (POD, ou surrogate entraîné sur le jumeau).

---

## Slide 20 — Ce que je retiens

1. Le jumeau **reproduit les niveaux de température à 30–70 °C près** sur trois essais, dont
   deux aveugles, avec **trois paramètres calibrés une seule fois**.
2. Il fait une **prédiction falsifiable** — le profil en « M » — qu'une manip simple peut
   trancher.
3. Les écarts restants ont été **localisés** (forme de la source, pas échelle) et cinq
   causes candidates ont été **éliminées avec des chiffres**.
4. La suite est autant **expérimentale** que numérique.

---

# Annexes (diapositives de réserve, pour les questions)

## Annexe A — Détail de la validation par thermocouple

**serieA_A-1** (calibration, 250 A) — `resultats_validation_2d_postcalib.log`

| TC | RMSE (°C) | T_max sim | T_max mes | Δ pic |
|---|---|---|---|---|
| TC1 | 50,2 | 458,2 | 398,0 | +60,3 |
| TC2 | 44,0 | 390,1 | 344,9 | +45,3 |
| TC3 | 39,1 | 424,3 | 383,5 | +40,8 |
| TC4 | 34,1 | 421,9 | 380,8 | +41,1 |
| TC5 | 28,8 | 441,8 | 399,3 | +42,5 |

**serieA_A-3** (aveugle, 200 A) : RMSE 27,6–40,2 ; Δ pic −38,6 à +35,6.
**serieB_B-2** (aveugle, consigne 360 °C) : RMSE 65,4–72,7 ; Δ pic −19,1 à +13,4.

## Annexe B — Positions des thermocouples (corrigées le 2026-07-20)

Les 5 TC sont **tous à l'interface** (confirmé par l'utilisateur ; remplace l'hypothèse
initiale « TC1 en surface »). Repère cahier (origine au milieu) → repère modèle (origine
au coin) :

| TC | x (mm) | y (mm) | Position |
|---|---|---|---|
| TC1 | 0 | 20 | bord de longueur, centre de largeur |
| TC2 | 30 | 0 | bord de largeur |
| TC3 | 60 | 0 | bord de largeur |
| TC4 | 90 | 0 | bord de largeur |
| TC5 | 120 | 0 | bord de largeur |

⚠ **TC2–TC5 sont exactement sur les lobes chauds** du profil en « M » — d'où la sensibilité
du diagnostic de la slide 13 à cette géométrie.

## Annexe C — Étude de convergence de maillage (2026-07-21)

- Le résidu « TC4 surestimé de +74 à +110 °C » était **à ~85–95 % un artefact de lecture**
  par nœud le plus proche : TC4 (x = 90 mm) tombait à mi-distance entre deux nœuds sur la
  grille 31 × 11 (dx = 4 mm).
- Correctif : interpolation **bilinéaire** en (x, y) pour la lecture des TC, et
  interpolation linéaire du nœud de contrôle du thermostat.
- Contrôle de cohérence : sur un maillage où TC4 tombe **exactement** sur un nœud, l'écart
  est **0,00 °C** ; sur les maillages « pire cas », l'écart décroît proportionnellement à
  dx/2 (rapport observé 3,34 pour un rapport de dx de 3,0) → mécanisme géométrique confirmé.
- Maillage retenu : **61 × 21 × 15** pour la validation ; 31 × 11 × 13 conservé pour la
  calibration.

## Annexe D — Champ de réaction EM : pourquoi le correctif a été écarté

- Implémenté rigoureusement (auto-cohérent, complexe, couplage inter-couches), vérifié par
  8 tests dédiés (cas limite basse fréquence, conservation de puissance, convergence du
  point fixe et du maillage).
- **La réaction physique est réelle mais petite** : 0,2–0,6 % de réduction de puissance par
  couche (l'estimation initiale « ordre unité » comportait une erreur de facteur π et une
  mauvaise couche de référence).
- Effet net mesurable **en sens inverse** : activer le champ de réaction désactive l'écran
  ad hoc `e^(−2t/δ)`, plus fort (−11,8 % sur le twill), d'où **+11 % de puissance déposée**
  au total → aggrave le dépassement de pic (A-1 : 46,0 → 54,7 °C).
- Livré derrière le flag `--champ-reaction` (défaut désactivé, chemin historique bit-à-bit
  inchangé) pour archivage et ablation.

## Annexe E — Reproductibilité

```bash
# Calibration (grille 31x11, essai A-1)
python scripts/calibrer.py --modele 2D --essai serieA_A-1 --n-lhs 25 --figer-decalage-x 0

# Validation croisée au θ* de référence (grille 61x21, sans recalibrage)
python scripts/valider.py --modele 2D --facteur 4.0975 --decalage-x 0 \
    --h-haut 11.323 --h-bas-2d 51.636

# Figures de présentation
python scripts/figure_empreinte.py config/essais/serieA_A-1.yaml --facteur 4.0975 \
    --tmax-couleur 480 --suffixe _plafonne
python scripts/figure_fusion.py config/essais/chauffe_250A_3TC.yaml --facteur 4.0975

pytest    # 34 tests, ~3 min
```

Journaux de référence à la racine du dépôt : `resultats_calibration_2d_postmaillage.log`,
`resultats_validation_2d_postcalib.log`, `resultats_convergence_maillage.log`,
`resultats_diagnostic_profil_M_em.log`, `resultats_champ_reaction_em.log`,
`resultats_test_position_thermostat.log`.

## Annexe F — Bibliographie mobilisée

- **Lionetto, Pappadà, Buccoliero, Maffezzoli (2017)**, *Materials & Design* 120:212–221 —
  modèle FE 3D du soudage par induction continu ; référence des figures 4 et 5.
- **O'Shaughnessey (2014)**, mémoire ÉTS (même laboratoire) — homogénéisation, conditions
  limites, analyse de sensibilité (I, f, gap, σ).
- **Grouve et al. (2020)** — propriétés C/PEKK, tenseur σ anisotrope, µr = 1.
- **Lin (1993)** — différences finies 2D, courants de Foucault portés par les fibres,
  hypothèse de plaque mince.
- **Duhovic et al. (2012)** — profondeur de peau, règles de maillage, coefficients de
  convection.
- **Samanis et al. (2026)** — méthode des lignes, identification LHS + NLSQ, test « boîte
  noire ».
- **Fluxtrol Inc.** — fiche technique *Ferrotron 559H* (µi = 16, courbe de pertes).

---

## Notes de préparation

**Ordre de priorité si le temps manque** : slides 2, 3, 4, 7, 9, 10, 13, 17, 18, 20.
Les slides 8, 11, 12 sont les plus « scientifiques » — à garder si l'auditoire est
technique.

**État des figures au 2026-07-22** : les trois figures de validation
(`serieA_A-1`, `serieA_A-3`, `serieB_B-2` — courbes et cartes d'interface) **ont été
régénérées au θ\* de référence** et reproduisent exactement les chiffres du journal
`resultats_validation_2d_postcalib.log` (39,2/46,0 — 32,7/31,0 — 68,0/12,3). Elles sont
donc utilisables telles quelles.

⚠ Les fichiers `resultats/*.png` sont **écrasés à chaque exécution** de `valider.py` : si
un run de diagnostic est lancé d'ici la présentation, relancer la commande de validation
de l'annexe E avant d'exporter les slides. La figure `chauffe_250A_3TC_fusion_fig5.png`
(slide 11) date, elle, du modèle 3D et n'a pas été régénérée.

**Message à ne pas diluer** : le modèle n'est pas encore prédictif au degré près, mais il
est **honnête, testé et falsifiable** — et il oriente désormais la campagne expérimentale.
