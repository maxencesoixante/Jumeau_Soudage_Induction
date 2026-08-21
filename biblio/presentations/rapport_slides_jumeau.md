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
  6,35 mm** → **entraxe centre-à-centre 12,35 mm** (relevé 2026-07-23 ; cf. slide 13) ;
  axe des brins à **5,0 mm** au-dessus du laminé (céramique 2 mm + demi-tube 3 mm).
- **Concentrateur de flux (MFC) Fluxtrol Ferrotron 559H** (µr ≈ 16),
  55 × 31,5 × 12 mm, **grand côté 55 mm parallèle à la largeur** de l'échantillon.
- Générateur **Ambrell EASYHEAT 4,2 kW — 388 kHz relevé machine**, 200 / 250 A.
- Gap bobine–laminé **2 mm** (céramique d'espacement), pression pneumatique.
- Procédé **semi-statique : 4 empreintes successives** le long des 120 mm (pas 30 mm).

*Figure* : schéma de la chaîne d'efforts (piston → MFC → céramique → laminé sup →
interface → laminé inf) ou photo de montage M2 du cahier.

*À dire* : deux faits géométriques structurent tout le reste — la bobine et le MFC
**débordent** de la largeur de 40 mm des deux côtés, et le twill est ~40× plus conducteur
que le laminé.

---

## Slide 4 — Architecture du jumeau (vue d'ensemble)

```
Bobine hairpin (Biot–Savart)  +  MFC (courants images, µr=16)
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
| MFC = demi-espace perméable (courants images) | approximation 1er ordre |
| Fusion par cp apparent gaussien (Tf 337 °C, Lf 130 kJ/kg) | Samanis 2026 ; Greco & Maffezzoli |
| Pertes propres du MFC négligées | **chiffré** : 0,6–1,4 W vs 50–260 W dans le twill (fiche Fluxtrol) |
| Pertes diélectriques négligées | O'Shaughnessey 2014 §3.1.3 |
| Fréquence figée à 388 kHz | relevé machine (corrélée au facteur d'échelle) |

*À dire* : insister sur la ligne MFC — c'est une hypothèse qui a été **vérifiée
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
écart non corrigeable — le gradient dans l'épaisseur / face opposée (cf. slide 14) — au prix
d'un facteur 10 sur le temps de calcul.

*À dire* : ce n'est pas un abandon du 3D — le 3D reste dans le dépôt et sert aux cartes ;
c'est un choix de modèle adapté à la mesure disponible.

---

## Slide 7 — Ce que le modèle produit : l'empreinte thermique

*Figure* : `donnees/resultats/serieA_A-1_empreinte_thermique_fig4_plafonne.png`
(4 panneaux — carte de température à l'interface à la fin de chaque empreinte, cadre MFC
en pointillés rouges, échelle plafonnée à 480 °C)

- Analogue **semi-statique** de la Fig. 4 de Lionetto *et al.* (2017), qui présentait une
  bobine avançant en continu ; ici la tête est **indexée sur 4 empreintes**.
- La zone chaude progresse le long des 120 mm ; le refroidissement inter-passes est visible.
- Script réutilisable : `code/scripts/figure_empreinte.py` (cache `.npz`, échelle réglable).

*À dire* : c'est le livrable central — la carte que l'expérience ne donne pas.

---

## Slide 8 — Le résultat le plus discutable : le profil en « M »

*Figure* : une carte d'interface seule (zoom sur une empreinte), montrant les deux lobes
chauds en y = 0 / 40 mm et le creux central.

- Le modèle prédit **deux lobes chauds sur les chants** et un **creux au centre** de la
  largeur.
- **Mécanisme, démontré numériquement** : la bobine ET le MFC (55 mm) **débordent** de
  l'échantillon (40 mm) → Bz quasi uniforme sur la largeur → les boucles de courant ne
  peuvent se refermer qu'en longeant les deux bords. C'est le *transverse-flux edge effect*
  classique du chauffage par induction de bandes plus étroites que l'inducteur.
- **Vérifié** : aucun courant ne traverse le chant (`max|Jy|` = 0 exactement sur y = 0 et
  y = 40 mm ; `∇·J` ≈ 7·10⁻⁸). La condition limite n'est pas en cause.
- **Cohérent avec l'observation** : squeeze-out festonné localisé sur les chants ;
  recommandation COMPAAM de réduire le MFC pour limiter les effets de bord.
- **Réserve honnête** : l'amplitude du contraste est probablement **surestimée** (rapport
  T(bord)/T(centre) ≈ 2,3–4,6 en fin d'impulsion après diffusion).
- **Première évidence, sur UN point** : l'essai de chauffe a son thermocouple d'interface
  (TC2) **au centre de la largeur**. Le modèle y prédit 292 °C (creux) et 708 °C sur les
  bords ; la mesure au centre donne **395 °C** (et elle a fondu). Le centre réel est donc
  **bien plus chaud que le creux prédit** → le M est trop creusé. Un seul point, pas une
  cartographie, mais il pointe déjà dans le sens de la réserve (cf. slide 11).

*À dire* : c'est le point où le modèle apporte une **prédiction falsifiable** — et il
existe une manip simple pour la trancher (slide 17). Un premier point de mesure la
contredit déjà partiellement, ce qui rend la cartographie complète d'autant plus utile.

---

## Slide 9 — Calibration : 3 paramètres, une seule fois

**Méthode** : hypercube latin (25 points) → moindres carrés non linéaires pondérés par le
bruit capteur (σ = std(diff)/√2). Pipeline hérité du jumeau 1D et de son test « boîte
noire » (Samanis 2026 §2.3).

**θ\* identifié sur A-1** (modèle 2D, 5 TC, grille de calibration 31 × 11) :

| Paramètre | Valeur | Écart-type | Rôle |
|---|---|---|---|
| `facteur_couplage` | **6,0123** | ± 0,067 | échelle de la source Joule (blindage, contacts, σ) |
| `h_haut` | **30,09** W/m²·K | ± 1,30 | perte vers le puits céramique/MFC |
| `h_bas_2d` | **37,42** W/m²·K | ± 0,51 | perte vers la face opposée / bâti |
| `decalage_x` | 0 (**figé**) | — | position bobine ↔ montage, non mesurée |
| `h_bord_x0` | 250 W/m²·K (figé) | — | puits au chant bridé x = 0 |

- **Corrélations toutes ≤ 0,49** → pas de quasi-non-identifiabilité (le piège `f_I`/`r_I`
  du jumeau 1D est évité).
- `decalage_x` a dû être **figé** : corrélation 0,985 avec `facteur_couplage` sur le fit
  joint, et railing sur sa borne — cas d'école de non-identifiabilité, documenté.
- ⚠ **Ce θ\* date du 2026-07-27** : deux corrections de géométrie de bobine successives
  l'ont fait évoluer — l'entraxe (2026-07-23, slide 13), puis la **hauteur bobine**
  (0,0068 → **0,005 m**, cote physique = céramique 2 mm + demi-tube 3 mm, l'ancienne étant
  une séquelle du tube de 9,5 mm). Le `h_haut` de 30 W/m²·K reste une conductance de
  contact plausible. Les jeux antérieurs (7,4172 / 26,37 / 41,91 à h=6,8 ; 4,0975 / 11,32 /
  51,64 en ancienne géométrie) sont **obsolètes**.

*À dire* : la discipline appliquée est « on calibre sur UN essai, on valide sur les autres
sans y retoucher ».

---

## Slide 10 — Validation croisée (sans recalibrage)

**θ\* calibré sur A-1 uniquement**, appliqué tel quel aux essais aveugles. Maillage de
validation 61 × 21 (dx = dy = 2 mm).

| Essai | Conditions | RMSE moyen | Écart de pic moyen | *(géométrie h=6,8, obsolète)* |
|---|---|---|---|---|
| **A-1** (calibration) | 250 A, coupure 400 °C | **35,8 °C** | **25,9 °C** | *36,8 / 14,9* |
| **A-3** (aveugle) | **200 A**, coupure 400 °C | **31,7 °C** | 41,3 °C | *32,0 / 28,4* |
| **B-2** (aveugle) | 250 A, coupure 360 °C | 65,3 °C | 45,2 °C | *66,2 / 34,8* |

*Figure* : `donnees/resultats/serieA_A-1_courbes_validation.png` (5 TC, 4 impulsions) — la plus
lisible ; `serieA_A-3_courbes_validation.png` en variante pour l'essai aveugle à 200 A.

- **Le modèle transfère à 200 A sans retouche** — l'essai aveugle à courant différent
  reste le mieux prédit en RMSE. La loi en I² et l'asservissement tiennent.
- **Un arbitrage honnête à assumer** : la dernière correction de cote (hauteur bobine
  6,8 → 5,0 mm, la valeur **physique**) améliore un peu le RMSE mais **dégrade l'écart de
  pic** (+10 à +13 °C). À géométrie EM juste, la source du modèle est trop concentrée, donc
  la calibration doit baisser son amplitude pour tenir le RMSE → les capteurs intérieurs
  sous-chauffent. On garde la cote juste : compenser une erreur de **forme** par une cote
  fausse serait une régression méthodologique (slide 13).
- **Ce qui reste** : le défaut dominant est la **forme** de la source (contraste bord/centre
  et longueur trop marqués), pas son échelle ni sa géométrie EM — désormais correctes.

**Comment lire la figure (3 observations à commenter à l'oral)**

1. **La séquence spatio-temporelle est juste** : chaque thermocouple devient le plus chaud
   à son tour, dans le bon ordre et au bon instant, au passage de l'empreinte devant lui
   (TC1 → TC2/TC3 → TC4 → TC5). C'est le résultat le plus solide de la figure : le modèle
   « sait où est la tête ».
2. **Les capteurs intérieurs sous-chauffent** (TC2–TC4 : −20 à −30 °C sur A-1) tandis que
   TC1 (près du bord) dépasse encore de +29 °C : signature d'une source trop concentrée que
   la calibration ne peut pas redistribuer, seulement mettre à l'échelle.
3. **Le refroidissement simulé est trop rapide** : entre les passes, les courbes simulées
   retombent vers 20–40 °C alors que les mesures se stabilisent à 80–120 °C. C'est la
   signature « plateau trop froid » — le modèle évacue trop d'énergie entre les impulsions
   (ou n'en a pas assez déposé loin du spot actif).

*À dire* : ne pas survendre. Un RMSE de 30–70 °C sur une fenêtre de mise en œuvre de
35 °C signifie que le modèle **ordonne** et **explique** correctement, mais ne pilote pas
encore.

---

## Slide 11 — Température et degré de fusion (analogue Lionetto Fig. 5)

*Figure* : `donnees/resultats/chauffe_250A_3TC_fusion_fig5.png` (régénérée le 2026-07-27, modèle 2D,
θ\* de référence).

- Panneau haut : température d'interface, simulée + mesurée (interface TC2 / surface TC1).
- Panneau bas : **degré de fusion Xm(t)** et fenêtre « état fondu » (Xm ≥ 0,99).
- Xm = fonction de répartition du pic gaussien de fusion du cp apparent — même définition
  que l'éq. 8 de Lionetto (approche statistique Greco & Maffezzoli).
- **Résultat exploitable pour le mémoire : temps à l'état fondu mesuré = 19 s**
  (t = 23 → 42 s), très proche des ~19 s de Lionetto à 300 A / 2 mm/s. Ce chiffre est
  **déduit de la mesure**, indépendant du modèle : il reste solide quoi qu'il arrive.

> **Ce que la figure montre honnêtement, au θ\* de référence (aucun facteur ajusté sur cet
> essai) : la courbe simulée SOUS-ESTIME le pic d'interface au point de mesure** (≈292 °C
> simulé contre ≈395 °C mesuré) et ne franchit donc pas la fusion — pas de fenêtre d'état
> fondu simulée. La raison n'est pas un manque d'énergie global : TC2 est au **centre de la
> largeur**, exactement dans le **creux du profil en M**. Au même instant, le modèle prédit
> **708 °C sur les bords** (y = 0/40) et 292 °C au centre. La mesure au centre (395 °C, qui
> a fondu) tombe **entre les deux** → c'est une donnée ponctuelle qui dit que **le creux du
> M est trop profond** (cf. slides 8 et 17). L'ancienne figure (2026-07-18) « fondait »
> parce que son facteur avait été calé sur le pic de CET essai — une béquille sur mesure,
> écartée.

*À dire* : ne pas présenter ceci comme un échec. Le critère de qualité (19 s à l'état
fondu) est mesuré, donc robuste. Et le désaccord de la courbe simulée est LOCALISÉ et
INFORMATIF : il pointe le même défaut que la prédiction falsifiable du profil en « M ».
La figure fait donc double emploi — analogue Lionetto Fig. 5 ET première évidence, sur un
point unique, que le contraste bord/centre du modèle est exagéré.

---

## Slide 12 — Ce que les enquêtes ont **éliminé** (résultats négatifs)

Chaque piste a été testée à θ\* figé, chiffrée, et archivée dans le dépôt.

| Hypothèse testée | Verdict | Chiffre clé |
|---|---|---|
| Artefacts de **maillage** (lecture TC, nœud de contrôle) | **Confirmée et corrigée** | −77 °C sur le résidu TC4 ; −56 °C sur TC5 |
| **Géométrie de bobine** (entraxe des brins) | **Confirmée et corrigée** | entraxe faux de 35 % ; pic A-1 46 → 15 °C |
| **Auto-échauffement du MFC** | Écartée | 0,6–1,4 W, soit 1–2 ordres de grandeur trop faible |
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

| | Supposé (config initiale) | Réel (relevé 2026-07) |
|---|---|---|
| Section des brins | tube rond ⌀ ~9,5 mm | **carré 6 mm** |
| Entraxe centre-à-centre | 19 mm | **12,35 mm** (−35 %) |
| Hauteur d'axe / laminé | 6,8 mm | **5,0 mm** (2 + 3, cote physique) |

- L'entraxe est **le** paramètre EM dominant (il fixe la position des deux filaments de
  courant, donc la forme de `Bz` puis de la source Joule).
- Corriger l'entraxe et recalibrer : **écart de pic A-1 46 → 15 °C**, RMSE meilleur sur
  les trois essais, et ce **à `k_plan = 3`, la valeur PHYSIQUE** — l'astuce d'un
  « `k_plan` effectif » envisagée pour forcer l'accord devient inutile.
- **La hauteur (6,8 → 5,0 mm) était le même piège** : 6,8 était dérivé du tube de 9,5 mm
  (2 + 4,76), pas mesuré ; la photo de montage donne 5,0. La corriger améliore le RMSE mais
  **dégrade l'écart de pic** — on l'assume, car c'est la cote juste, et la régression
  confirme que la source est trop concentrée (slide 10). Le plan image du MFC, lui, a été
  **vérifié sur la CAO** et reste inchangé (concentrateur bien au-dessus des brins).
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

## Slide 14 — Le gradient dans l'épaisseur : face opposée sur-chauffée

- Sur l'essai de chauffe instrumenté en épaisseur, les **5 TC sont à l'interface** : recalculé,
  **surface ≈ interface** (ratio ≈ 0,97) — l'ancien « TC1 5–6× trop lent en surface » était **faux**.
- Le vrai écart : le modèle **sur-chauffe la face opposée** (opposée/interface ≈ 0,9 simulé vs
  ≈ 0,42 mesuré) → **confinement transverse insuffisant**.
- Explications testées et **écartées** : condition limite thermique, résistance de contact à
  l'interface (reproduit le profil mais NO-GO en validation croisée), auto-échauffement du MFC,
  décalage de bobine.
- Mécanisme fin (répartition de puissance entre couches / champ proche) **à confirmer par une
  mesure** (température du MFC).

*À dire* : c'est la limite qu'on assume et qui justifie le passage au modèle 2D (les TC A/B
sont à l'interface) — on ne prétend pas prédire le gradient dans l'épaisseur.

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
- Gradient dans l'épaisseur (face opposée) : mécanisme fin non confirmé.
- Pas de mécanique (pression, squeeze-out) ni de cinétique de cristallisation.
- Propriétés matériaux **indépendantes de la température**.

---

## Slide 17 — Suite : ce qu'il faut MESURER

Trois manips discriminantes, par ordre de rapport valeur/effort :

1. **Cartographie bord → centre — LA priorité** (5 TC d'interface à y = 0/10/20/30/40 mm,
   x = 60 mm, essai de chauffe simple spot). ⟶ c'est la mesure qui **débloque le levier n° 1**
   (forme de la source, slide 18) : elle seule cale l'amplitude du « M ». **Cible chiffrée du
   modèle** : 717 / 382 / **292** / 382 / 717 °C au pic (contraste bord/centre 2,46×) ; le
   seul point déjà mesuré, le centre à 395 °C, dépasse déjà les 292 prédits → le M est
   vraisemblablement trop creusé. *Manip décrite au cahier §2.1.4.*
2. **Température du MFC** (thermocouple ou caméra IR sur sa face active pendant une
   chauffe). ⟶ seule mesure capable d'attaquer le déficit TC1.
3. **Relevé métrologique de la position de la tête** (bobine / MFC / thermocouples, surtout
   le décalage longitudinal `decalage_x` aujourd'hui figé). ⟶ les cotes de section, entraxe
   et hauteur des brins sont **déjà corrigées** sur CAO + photo (slide 13) ; ne reste que la
   position à relever pour refermer le sujet géométrie.
4. **Point de coupure réel du thermostat** (quel capteur pilotait l'arrêt de chauffe, et à
   quelle position). ⟶ tranche le résidu B-2 de la slide 13.

*À dire* : la priorité n'est plus de coder, elle est de mesurer. Le modèle est arrivé au
point où il pose des questions expérimentales précises — et la dernière en date était une
question de **métrologie**, pas de physique.

---

## Slide 18 — Suite : ce qu'il faut MODÉLISER

Par ordre de priorité, avec l'incertitude assumée :

1. **Adoucir le profil en « M » en largeur** — le levier n° 1, mais **pas** celui qu'on
   croyait. Un diagnostic (27 juillet) a montré que le champ `Bz` est déjà uniforme en
   largeur : le M vient **entièrement** de l'écrasement du courant de Foucault contre les
   chants libres (`ψ = 0` au bord d'une nappe continue idéalisée), pas de la forme du champ.
   ⟹ Le **MFC fini** (redistribution du flux) n'y changera rien — il agit sur le profil en
   **longueur**. Les vrais mécanismes d'adoucissement : courants de retour 3D par l'épaisseur
   près des chants, résistance de contact du tissu twill. **Aucun ne se calibre sans la
   cartographie bord→centre** (slide 17) — d'où la priorité donnée à cette mesure.
2. **Forme du blindage inter-couches** — l'écran actuel `e^(−2t/δ)` (onde plane) est-il
   adapté à une nappe de courant plane ? Le calcul rigoureux nappe-à-nappe suggère un
   blindage plus faible, ce qui redistribuerait la puissance entre couches — piste possible
   pour TC1.
3. **Propriétés dépendantes de la température** σ(T), cp(T) — mise en garde explicite
   d'O'Shaughnessey et Duhovic ; expliquerait qu'un facteur unique ne colle pas
   simultanément à la montée, au pic et à la décroissance.
4. **Cinétique de cristallisation** (Ozawa) — complèterait la Fig. 5 avec le degré de
   cristallinité, et donnerait un critère de qualité de joint au refroidissement.

*À dire* : le point 1 est le vrai levier restant, mais le diagnostic a corrigé la cible —
ce n'est pas le MFC fini, c'est l'adoucissement du M en largeur, et il faut la mesure
(slide 17) avant de le coder. Les points 2–4 sont des raffinements. Message d'ensemble :
la modélisation est désormais **pilotée par la mesure**, pas l'inverse.

---

## Slide 19 — Horizon : du jumeau au contrôle

```
Aujourd'hui          Court terme                 Objectif
────────────         ─────────────               ────────
Modèle validé   →    MFC fini + σ(T)        →    Plant model fiable
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
   deux aveugles, avec **trois paramètres calibrés une seule fois**.
2. Il fait une **prédiction falsifiable** — le profil en « M » — qu'une manip simple peut
   trancher.
3. Deux « déficits structurels » se sont révélés être des **cotes fausses** (entraxe, puis
   hauteur), pas une physique manquante : vérifier les entrées avant d'inventer un mécanisme.
4. La **géométrie EM est maintenant juste** (cotes + plan image vérifiés) : l'écart de pic
   résiduel est désormais clairement imputable à la **forme** de la source (profil en M),
   pas à une entrée — ce qui pointe le prochain levier sans ambiguïté.
5. La suite est autant **expérimentale** que numérique.

---

# Annexes (diapositives de réserve, pour les questions)

## Annexe A — Détail de la validation par thermocouple

Géométrie corrigée (entraxe + hauteur 5,0 mm), θ\* de référence
(6,0123 / 30,09 / 37,42), grille 61 × 21 —
`donnees/journaux/archive/resultats_validation_reference_figures.log` (2026-07-27).

**serieA_A-1** (calibration, 250 A)

| TC | RMSE (°C) | T_max sim | T_max mes | Δ pic |
|---|---|---|---|---|
| TC1 | 48,6 | 427,3 | 398,0 | **+29,3** |
| TC2 | 36,5 | 324,4 | 344,9 | −20,4 |
| TC3 | 34,0 | 355,2 | 383,5 | −28,3 |
| TC4 | 29,8 | 350,7 | 380,8 | −30,1 |
| TC5 | 29,9 | 421,0 | 399,3 | +21,6 |

→ **TC1 (bord) dépasse encore de +29 °C tandis que TC2–TC4 (intérieur) sous-chauffent de
−20 à −30 °C** : la source est trop concentrée, la calibration ne peut que la mettre à
l'échelle, pas la redistribuer.

**serieA_A-3** (aveugle, 200 A) : RMSE 26,7–39,2 ; Δ pic −90,8 (TC2) à +16,8.
**serieB_B-2** (aveugle, consigne 360 °C) : RMSE 62,5–70,0 ; Δ pic −70,4 à −4,4 — la
sous-chauffe croît vers les points inter-empreintes (pire à TC3, x = 60 mm), signature du
résidu de la slide 13.

*Pour mémoire — géométrie h=6,8 (obsolète), A-1* : Δ pic +37,9 (TC1) à −3,7, RMSE 28,9–48,9.
*Encore avant (ancienne géométrie, entraxe 19 mm)* : Δ pic +40,8 à +60,3, tous les TC
dépassant de façon homogène. La trajectoire de ces trois jeux illustre le déplacement du
résidu : d'un sur-chauffage homogène (géométrie fausse) vers une sous-chauffe des points
intérieurs (géométrie juste, source trop concentrée).

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
python code/scripts/calibrer.py --modele 2D --essai serieA_A-1 --n-lhs 25 --figer-decalage-x 0

# Validation croisée au θ* de référence (grille 61x21, sans recalibrage)
python code/scripts/valider.py --modele 2D --facteur 6.0123 --decalage-x 0 \
    --h-haut 30.087 --h-bas-2d 37.424 --h-bord-x0 250

# Figures de présentation (modèle 2D, cohérent avec la validation ci-dessus)
python code/scripts/figure_empreinte.py code/config/essais/serieA_A-1.yaml --modele 2D \
    --facteur 6.0123 --decalage-x 0 --h-haut 30.087 --h-bas-2d 37.424 --h-bord-x0 250 \
    --tmax-couleur 480 --suffixe _plafonne
python code/scripts/figure_fusion.py code/config/essais/chauffe_250A_3TC.yaml --modele 2D \
    --facteur 6.0123 --decalage-x 0 --h-haut 30.087 --h-bas-2d 37.424 --h-bord-x0 250

pytest    # 34 tests, ~3 min
```

⚠ Le θ\* ci-dessus suppose la **géométrie corrigée** (`code/config/geometrie.yaml` :
`entraxe_jambes: 0.01235`, `rayon_tube: 0.003`, `hauteur: 0.005`). Avec une géométrie
antérieure, il ne reproduit rien.

Journaux de référence dans `donnees/journaux/` :
`donnees/journaux/archive/resultats_hauteur_5mm_recalibration.log` (**correction hauteur + θ\* courant**),
`donnees/journaux/archive/resultats_geometrie_corrigee_recalibration.log` (correction d'entraxe, étape précédente),
`donnees/journaux/archive/resultats_diag_hauteur_bobine.log` (diagnostic hauteur + plan image MFC vérifié sur CAO),
`donnees/journaux/archive/resultats_validation_reference_figures.log` (validation au θ\* courant, figures associées),
`donnees/journaux/archive/resultats_diag_b2_longueur.log` (résidu B-2 et les trois correctifs réfutés),
`donnees/journaux/archive/resultats_convergence_maillage.log`, `donnees/journaux/archive/resultats_diagnostic_profil_M_em.log`,
`donnees/journaux/archive/resultats_champ_reaction_em.log`, `donnees/journaux/archive/resultats_diag_cp_kplan.log`,
`donnees/journaux/archive/resultats_test_position_thermostat.log`.
*Les journaux antérieurs au 2026-07-23 (`donnees/journaux/archive/resultats_calibration_2d_postmaillage.log`,
`donnees/journaux/archive/resultats_validation_2d_postcalib.log`, et la chaîne de diagnostics) sont établis sur
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

**État des figures au 2026-07-27** : toutes les figures (validation `serieA_A-1`/`A-3`/
`serieB_B-2`, empreinte Fig. 4, fusion Fig. 5) **ont été régénérées à la géométrie corrigée
hauteur 5,0 mm et au θ\* de référence** (6,0123 / 30,09 / 37,42) ; les figures de validation
reproduisent exactement `donnees/journaux/archive/resultats_validation_reference_figures.log`
(35,8/25,9 — 31,7/41,3 — 65,3/45,2). Toutes utilisables telles quelles.

⚠ Les fichiers `donnees/resultats/*.png` sont **écrasés à chaque exécution** de `valider.py` : si
un run de diagnostic est lancé d'ici la présentation, relancer les commandes de l'annexe E
(validation + figures) avant d'exporter les slides.

**Message à ne pas diluer** : le modèle n'est pas encore prédictif au degré près, mais il
est **honnête, testé et falsifiable** — et il oriente désormais la campagne expérimentale.
