# Jumeau numérique du soudage par induction CF/PEKK — rapport de présentation

**Objet** : trame de présentation (slides) de l'état d'avancement du jumeau numérique et
de la suite du travail.
**Date de l'état des lieux** : 2026-07-24 (branche `fix-coil-tube-geometry`, commit `b28239e`)
— **révisé après la correction de géométrie de bobine du 2026-07-23** (cf. slide 13).
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
- **Bobine hairpin** : deux brins de **section carrée 6 mm**, séparés d'un **gap de
  6,35 mm** → **entraxe centre-à-centre 12,35 mm** (relevé 2026-07-23 ; cf. slide 13).
- **Concentrateur de flux (CFC) Fluxtrol Ferrotron 559H** (µr ≈ 16),
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
écart non corrigeable — le déficit de chauffe en surface (cf. slide 14) — au prix d'un
facteur 10 sur le temps de calcul.

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
| `facteur_couplage` | **7,4172** | ± 0,071 | échelle de la source Joule (blindage, contacts, σ) |
| `h_haut` | **26,37** W/m²·K | ± 1,42 | perte vers le puits céramique/CFC |
| `h_bas_2d` | **41,91** W/m²·K | ± 0,52 | perte vers la face opposée / bâti |
| `decalage_x` | 0 (**figé**) | — | position bobine ↔ montage, non mesurée |
| `h_bord_x0` | 250 W/m²·K (figé) | — | puits au chant bridé x = 0 |

- **Corrélations toutes ≤ 0,57** → pas de quasi-non-identifiabilité (le piège `f_I`/`r_I`
  du jumeau 1D est évité).
- `decalage_x` a dû être **figé** : corrélation 0,985 avec `facteur_couplage` sur le fit
  joint, et railing sur sa borne — cas d'école de non-identifiabilité, documenté.
- ⚠ **Ce θ\* date du 2026-07-23** : il remplace le jeu antérieur (4,0975 / 11,32 / 51,64),
  obtenu avec une **géométrie de bobine fausse** (slide 13). Le nouveau `h_haut` de
  26 W/m²·K est en outre **plus plausible physiquement** qu'un 11 W/m²·K
  artificiellement bas pour une conductance de contact.

*À dire* : la discipline appliquée est « on calibre sur UN essai, on valide sur les autres
sans y retoucher ».

---

## Slide 10 — Validation croisée (sans recalibrage)

**θ\* calibré sur A-1 uniquement**, appliqué tel quel aux essais aveugles. Maillage de
validation 61 × 21 (dx = dy = 2 mm).

| Essai | Conditions | RMSE moyen | Écart de pic moyen | *(avant correction géométrie)* |
|---|---|---|---|---|
| **A-1** (calibration) | 250 A, coupure 400 °C | **36,8 °C** | **14,9 °C** | *39,2 / 46,0* |
| **A-3** (aveugle) | **200 A**, coupure 400 °C | **32,0 °C** | 28,4 °C | *32,7 / 31,0* |
| **B-2** (aveugle) | 250 A, coupure 360 °C | 66,2 °C | 34,8 °C | *68,0 / 12,3* |

*Figure* : `resultats/serieA_A-1_courbes_validation.png` (5 TC, 4 impulsions) — la plus
lisible ; `serieA_A-3_courbes_validation.png` en variante pour l'essai aveugle à 200 A.

- **Le modèle transfère à 200 A sans retouche** — l'essai aveugle à courant différent
  reste le mieux prédit en RMSE. La loi en I² et l'asservissement tiennent.
- **Le RMSE s'améliore sur les trois essais** et le dépassement de pic sur A-1 est
  **divisé par trois** (46 → 15 °C) après la correction de géométrie de bobine (slide 13).
- **Ce qui reste** : B-2 (basse consigne, 360 °C) sous-chauffe les capteurs
  inter-empreintes de 30 à 55 °C — le pic y régresse (12 → 35 °C). Limite assumée,
  diagnostiquée et non corrigeable sans casser A-1 (slide 13).

**Comment lire la figure (3 observations à commenter à l'oral)**

1. **La séquence spatio-temporelle est juste** : chaque thermocouple devient le plus chaud
   à son tour, dans le bon ordre et au bon instant, au passage de l'empreinte devant lui
   (TC1 → TC2/TC3 → TC4 → TC5). C'est le résultat le plus solide de la figure : le modèle
   « sait où est la tête ».
2. **Les pics sont désormais recalés à ±15 °C sur A-1** (ils dépassaient de 40 à 60 °C
   avant la correction de géométrie) ; l'écart de pic résiduel se concentre sur B-2.
3. **Le refroidissement simulé est trop rapide** : entre les passes, les courbes simulées
   retombent vers 20–40 °C alors que les mesures se stabilisent à 80–120 °C. C'est la
   signature « plateau trop froid » — le modèle évacue trop d'énergie entre les impulsions
   (ou n'en a pas assez déposé loin du spot actif).

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

## Slide 12 — Ce que les enquêtes ont **éliminé** (résultats négatifs)

Chaque piste a été testée à θ\* figé, chiffrée, et archivée dans le dépôt.

| Hypothèse testée | Verdict | Chiffre clé |
|---|---|---|
| Artefacts de **maillage** (lecture TC, nœud de contrôle) | **Confirmée et corrigée** | −77 °C sur le résidu TC4 ; −56 °C sur TC5 |
| **Géométrie de bobine** (entraxe des brins) | **Confirmée et corrigée** | entraxe faux de 35 % ; pic A-1 46 → 15 °C |
| **Auto-échauffement du CFC** | Écartée | 0,6–1,4 W, soit 1–2 ordres de grandeur trop faible |
| **Position de lecture du thermostat** | Écartée | contrôler au bord fait chuter l'écart de +46 à −107 °C |
| **Décalage de position bobine** `decalage_x` | Écartée pour TC1 | Q(TC1)/Q(TC2) ≤ 0,12 vs 1,71 requis |
| **Champ de réaction EM** (blindage auto-cohérent) | Implémenté, puis **écarté** | effet réel ~0,2–0,6 %, pas les ~100 % espérés |
| **`k_plan`, `cp`, masse d'outillage, bloc céramique** (déficit de pic A-1) | Toutes écartées | aucune ne reproduit le pic sans dégrader le reste |

*À dire* : la moitié du travail des dernières semaines est constituée de résultats
négatifs **documentés**. C'est ce qui empêche de tourner en rond et ce qui fait le contenu
d'un chapitre de mémoire honnête. Les deux lignes « confirmée et corrigée » montrent aussi
que **les écarts ne sont pas tous physiques** : deux des plus gros étaient des artefacts
(numérique, puis donnée d'entrée).

---

## Slide 13 — Le « déficit structurel » était une **donnée d'entrée fausse**

**Le diagnostic présenté jusqu'ici (« le modèle concentre trop la puissance ») s'est
révélé faux dans sa cause.** Il a été poursuivi pendant des semaines comme un manque de
physique, avant d'être attribué à une entrée géométrique erronée.

| | Supposé (config initiale) | Réel (relevé 2026-07-23) |
|---|---|---|
| Section des brins | tube rond ⌀ ~9,5 mm | **carré 6 mm** |
| Entraxe centre-à-centre | 19 mm | **12,35 mm** (−35 %) |

- L'entraxe est **le** paramètre EM dominant (il fixe la position des deux filaments de
  courant, donc la forme de `Bz` puis de la source Joule).
- Corriger la géométrie et recalibrer : **écart de pic A-1 46 → 15 °C**, RMSE meilleur sur
  les trois essais, et ce **à `k_plan = 3`, la valeur PHYSIQUE** — l'astuce d'un
  « `k_plan` effectif » envisagée pour forcer l'accord devient inutile.
- Toute une chaîne de diagnostics (`cp`, `k_plan`, source EM, puits d'outillage, blindage
  inter-couches, bloc céramique) poursuivait donc un artefact. **Aucun correctif erroné
  n'a été commité** : tout avait été testé à θ\* figé, en mode diagnostic.

**Ce qui reste ouvert : le régime basse consigne (B-2).** À consigne 360 °C, les capteurs
inter-empreintes restent 30 à 55 °C trop froids. Cause diagnostiquée : le modèle coupe la
chauffe quand **le centre de l'empreinte** atteint la consigne, alors que le procédé réel
coupait sur un thermocouple d'interface plus froid → impulsions réelles plus longues, donc
plus d'étalement en longueur. Trois correctifs ont été prototypés, recalibrés, validés en
croisé et **tous réfutés** (décaler la position de contrôle casse A-1 ; une marge de
consigne échange A-1 contre B-2 ; la force de contact est neutralisée par le thermostat).

*À dire* : la leçon méthodologique vaut le résultat. Un écart persistant de 40 à 60 °C a
été attribué à la physique manquante pendant des semaines ; c'était une cote. **Avant de
chercher un mécanisme, vérifier les entrées** — et la discipline « diagnostic à θ\* figé
avant tout correctif » a évité de graver l'erreur dans le code.

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
- **Correction d'une géométrie de bobine fausse de 35 %** : le principal écart résiduel
  (pic A-1) est tombé de 46 à 15 °C, à paramètres physiques (`k_plan = 3`).
- Sept pistes physiques testées et tranchées, dont cinq par résultat négatif chiffré.

**Limites assumées**

- Régime **basse consigne** (B-2) : capteurs inter-empreintes 30–55 °C trop froids,
  écart de pic 35 °C — diagnostiqué, trois correctifs réfutés.
- Plateau inter-passes trop froid.
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
3. **Relevé métrologique complet de la tête** (cotes de bobine, position relative bobine /
   CFC / thermocouples, hauteur bobine–laminé). ⟶ lève l'incertitude qui a forcé à figer
   `decalage_x`, **et prévient la répétition de l'épisode de la slide 13** : une cote fausse
   de 35 % a coûté des semaines de diagnostic. La cote `hauteur = 6,8 mm` reste d'ailleurs
   à réconcilier avec les tubes de 6 mm.
4. **Point de coupure réel du thermostat** (quel capteur pilotait l'arrêt de chauffe, et à
   quelle position). ⟶ tranche le résidu B-2 de la slide 13.

*À dire* : la priorité n'est plus de coder, elle est de mesurer. Le modèle est arrivé au
point où il pose des questions expérimentales précises — et la dernière en date était une
question de **métrologie**, pas de physique.

---

## Slide 18 — Suite : ce qu'il faut MODÉLISER

Par ordre de priorité, avec l'incertitude assumée :

1. **Modèle de CFC fini** (redistribution du flux par la semelle polaire) — remplacer
   l'approximation par courants images. *Il change la forme de la source, pas son échelle.*
   Nécessite un refit complet de θ\* derrière. ⚠ Effort : plusieurs jours de travail EM
   dédié (FEM/BEM ou modèle de semelle). **Priorité revue à la baisse** depuis la slide 13 :
   la géométrie corrigée a absorbé l'essentiel de l'écart que ce levier devait expliquer.
2. **Forme du blindage inter-couches** — l'écran actuel `e^(−2t/δ)` (onde plane) est-il
   adapté à une nappe de courant plane ? Le calcul rigoureux nappe-à-nappe suggère un
   blindage plus faible, ce qui redistribuerait la puissance entre couches — piste possible
   pour TC1.
3. **Propriétés dépendantes de la température** σ(T), cp(T) — mise en garde explicite
   d'O'Shaughnessey et Duhovic ; expliquerait qu'un facteur unique ne colle pas
   simultanément à la montée, au pic et à la décroissance.
4. **Cinétique de cristallisation** (Ozawa) — complèterait la Fig. 5 avec le degré de
   cristallinité, et donnerait un critère de qualité de joint au refroidissement.

*À dire* : depuis la correction de géométrie, aucun de ces quatre points n'est un
« correctif attendu » — ce sont des raffinements. Le résidu ouvert (B-2, basse consigne)
relève d'abord d'une **mesure** (point 4 de la slide 17), pas d'un modèle plus fin.

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

1. Le jumeau **reproduit les niveaux de température à 30–65 °C près** sur trois essais, dont
   deux aveugles, avec **trois paramètres calibrés une seule fois** — et les **pics à
   ±15 °C** sur l'essai de calibration.
2. Il fait une **prédiction falsifiable** — le profil en « M » — qu'une manip simple peut
   trancher.
3. Le principal écart résiduel s'est révélé être une **cote fausse**, pas une physique
   manquante : vérifier les entrées avant d'inventer un mécanisme.
4. Les écarts restants ont été **localisés** (régime basse consigne) et sept causes
   candidates ont été **tranchées avec des chiffres**.
5. La suite est autant **expérimentale** que numérique.

---

# Annexes (diapositives de réserve, pour les questions)

## Annexe A — Détail de la validation par thermocouple

Géométrie corrigée, θ\* de référence, grille 61 × 21 —
`resultats_validation_reference_figures.log` (2026-07-24).

**serieA_A-1** (calibration, 250 A)

| TC | RMSE (°C) | T_max sim | T_max mes | Δ pic |
|---|---|---|---|---|
| TC1 | 48,9 | 435,9 | 398,0 | **+37,9** |
| TC2 | 37,3 | 341,2 | 344,9 | −3,7 |
| TC3 | 36,4 | 386,8 | 383,5 | +3,3 |
| TC4 | 32,5 | 385,0 | 380,8 | +4,2 |
| TC5 | 28,9 | 425,0 | 399,3 | +25,7 |

→ **TC2 à TC4 sont désormais recalés à moins de 5 °C au pic** ; l'écart résiduel se
concentre sur TC1 (bord bridé x = 0, cf. `h_bord_x0`) et TC5 (dernière empreinte).

**serieA_A-3** (aveugle, 200 A) : RMSE 27,4–39,2 ; Δ pic −70,7 à +21,3 (le résidu se
déplace sur TC2, sous-chauffé).
**serieB_B-2** (aveugle, consigne 360 °C) : RMSE 63,3–71,4 ; Δ pic −53,0 à +14,0 — la
sous-chauffe croît vers les points inter-empreintes (pire à TC3, x = 60 mm), signature du
résidu de la slide 13.

*Pour mémoire, avant la correction de géométrie* (A-1) : RMSE 28,8–50,2 ; Δ pic +40,8 à
+60,3 — tous les TC dépassaient, de façon homogène.

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

⚠ **TC2–TC5 sont exactement sur les lobes chauds** du profil en « M » — les métriques de
pic sont donc très sensibles à la forme prédite de l'empreinte, ce qui explique l'ampleur
de l'effet de la correction de géométrie (slide 13).

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
  au total → aggrave le dépassement de pic (A-1 : 46,0 → 54,7 °C, *chiffres établis avant
  la correction de géométrie de la slide 13 ; le sens de l'effet est inchangé*).
- Livré derrière le flag `--champ-reaction` (défaut désactivé, chemin historique bit-à-bit
  inchangé) pour archivage et ablation.

## Annexe E — Reproductibilité

```bash
# Calibration (grille 31x11, essai A-1)
python scripts/calibrer.py --modele 2D --essai serieA_A-1 --n-lhs 25 --figer-decalage-x 0

# Validation croisée au θ* de référence (grille 61x21, sans recalibrage)
python scripts/valider.py --modele 2D --facteur 7.4172 --decalage-x 0 \
    --h-haut 26.367 --h-bas-2d 41.905 --h-bord-x0 250

# Figures de présentation
python scripts/figure_empreinte.py config/essais/serieA_A-1.yaml --facteur 7.4172 \
    --tmax-couleur 480 --suffixe _plafonne
python scripts/figure_fusion.py config/essais/chauffe_250A_3TC.yaml --facteur 7.4172

pytest    # 34 tests, ~3 min
```

⚠ Le θ\* ci-dessus suppose la **géométrie corrigée** (`config/geometrie.yaml` :
`entraxe_jambes: 0.01235`, `rayon_tube: 0.003`). Avec l'ancienne géométrie, il ne
reproduit rien.

Journaux de référence à la racine du dépôt :
`resultats_geometrie_corrigee_recalibration.log` (**correction de géométrie + θ\* courant**),
`resultats_validation_reference_figures.log` (validation au θ\* courant, figures associées),
`resultats_diag_b2_longueur.log` (résidu B-2 et les trois correctifs réfutés),
`resultats_convergence_maillage.log`, `resultats_diagnostic_profil_M_em.log`,
`resultats_champ_reaction_em.log`, `resultats_diag_cp_kplan.log`,
`resultats_test_position_thermostat.log`.
*Les journaux antérieurs au 2026-07-23 (`resultats_calibration_2d_postmaillage.log`,
`resultats_validation_2d_postcalib.log`, et la chaîne de diagnostics) sont établis sur
l'**ancienne géométrie** : leurs raisonnements restent valides, leurs chiffres non.*

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

**État des figures au 2026-07-24** : les trois figures de validation
(`serieA_A-1`, `serieA_A-3`, `serieB_B-2` — courbes et cartes d'interface) **ont été
régénérées à la géométrie corrigée et au θ\* de référence** ; elles reproduisent exactement
les chiffres du journal `resultats_validation_reference_figures.log`
(36,8/14,9 — 32,0/28,4 — 66,2/34,8). Elles sont donc utilisables telles quelles.

⚠ Les fichiers `resultats/*.png` sont **écrasés à chaque exécution** de `valider.py` : si
un run de diagnostic est lancé d'ici la présentation, relancer la commande de validation
de l'annexe E avant d'exporter les slides. La figure `chauffe_250A_3TC_fusion_fig5.png`
(slide 11) date, elle, du modèle 3D et n'a pas été régénérée.

**Message à ne pas diluer** : le modèle n'est pas encore prédictif au degré près, mais il
est **honnête, testé et falsifiable** — et il oriente désormais la campagne expérimentale.
