**Projet** : jumeau numérique du soudage par induction CF/PEKK &nbsp;·&nbsp; **Objet** : mesures — réponses, précisions et RÉSULTATS (archive des avancées) &nbsp;·&nbsp; **Créé** : 27 juillet 2026

> Archive de tout ce qui a été **tranché ou mesuré** (pour ne garder dans
> `mesures_a_realiser.md` que ce qui reste à faire). Trois parties : (A) relevés résolus,
> (B) précisions sur les expériences, (C) résultats des manips déjà réalisées. Les corrections
> de modèle qui en découlent sont préparées en config et détaillées dans les journaux
> `resultats_*.log` cités.

---

# A. Relevés résolus (réponses terrain)

---

## Relevé 2 — Fréquence du générateur à 200 A ✔ (2026-07-27)

**Question.** Fréquence de travail de l'EASYHEAT à 200 A (le modèle suppose 388 kHz, valeur
250 A, pour tous les essais — dont A-3 à 200 A).

**Réponse utilisateur (2026-07-27).** « La fréquence à 200 A est de 383 kHz. »

**Relevé complet ✔ (2026-07-28) — infirme le point ci-dessus.** Fréquence relevée aux 5 courants :
**150→390, 176→387, 200→390, 225→388, 250→386 kHz**. → **constante à 388 ± 2 kHz** (variation 1 %,
aucune tendance avec I : corr. −0,63 = bruit). Le « 383 kHz à 200 A » du 27 juillet n'est pas
reproduit (200 A mesuré à 390).

**Conséquence modèle.** La fréquence NE varie PAS avec l'ampérage → **une seule valeur globale
suffit** ; la correction « fréquence par essai » est **abandonnée**. La valeur config `388e3`
reste bonne. Bénéfice de bord : ceci **confirme la loi en I² de la source** (pas de couplage
fréquence↔courant), cf. loi taux-courant `docs/figures_presentation/fig5`.

---

## Relevé 3 — Épaisseur réelle du pli twill ✔ (2026-07-27)

**Question.** Épaisseur du pli twill suscepteur (config : `twill_suscepteur.epaisseur = 0,28 mm`,
marquée « à confirmer »).

**Réponse utilisateur.** « Le pli de twill a une épaisseur de **0,20 mm**. »

**Conséquence modèle.** Correction préparée dans `config/materiaux.yaml` (commentaire) :
`0.00028 → 0.0002 m`. **À appliquer à la prochaine recalibration** — l'épaisseur du twill
change la répartition de puissance entre couches, donc impose un refit de θ\*. Non appliquée
immédiatement pour ne pas confondre avec l'expérience « thermostat capteurs ».

---

## Relevé 4 — Condition aux bords de l'échantillon ✔ (2026-07-27)

**Question.** Ce qui touche les quatre chants pendant un essai — justifie (ou non) le
paramètre `h_bord_x0` (puits de chaleur au chant x = 0).

**Réponse utilisateur.** « Les bords de l'échantillon sont à l'air libre pour les faces
latérales. La face inférieure (de l'assemblage soudé) est en contact avec le bloc céramique
du dessous. La face supérieure est en contact avec la céramique d'espacement, au-dessus de
laquelle se trouve le CFC. »

**Conséquence modèle.** Les quatre chants latéraux sont **à l'air libre** (aucune bride, aucun
appui, aucun puits au chant x = 0). Seuls échanges verticaux : face inférieure (bloc céramique
→ `h_bas`) et face supérieure (céramique d'espacement → CFC → `h_haut`). **`h_bord_x0 = 250`
n'a donc AUCUNE base physique** — c'est un paramètre EFFECTIF qui compense autre chose
(vraisemblablement le bord trop chaud du profil en « M » côté x = 0). Requalifié comme tel
dans `config/materiaux.yaml`. **Candidat au retrait** à la prochaine recalibration : le tester
à 0, ou le remplacer par une convection latérale faible et uniforme sur les quatre chants.
Contredit l'ancienne justification « montage bridé x=0 » (cf. mémoire `tc1-surchauffe-leviers`).

---

## Relevé 5 — Point de coupure réel du thermostat ✔ (2026-07-27)

**Question.** Sur quel signal la chauffe était coupée (quel TC / quelle voie pilotait la
régulation).

**Réponse utilisateur.** « Regarde le cahier de laboratoire. »

**Conséquence modèle.** Le cahier tranche : étape 6 de la procédure « chauffe à 250 A **jusqu'à
T = Tprocessing** », et la fiche B-1 formule la cible comme « **T max interface (TC fiables
1/3/5)** … jamais dépassé ~372 °C ». La coupure se faisait donc **quand le thermocouple
d'interface le plus chaud atteignait la consigne**, pas quand le centre du spot l'atteignait —
cohérent avec les données B-2 (chaque impulsion coupée par le TC le plus proche, alternant
devant/derrière). Le modèle, lui, coupe au **centre du spot** → trop tôt → sous-chauffe les
points inter-empreintes (résidu B-2). Correctif « loi capteurs » (couper sur le max de T aux
positions TC réelles) **implémenté derrière le flag `--thermostat-capteurs`** (défaut off,
commit `b50bd76`) : recale les pics (B-2 |ΔT_max| 45 → 23 après recalibration) mais dégrade le
RMSE (+5-6 °C), couplé au profil en « M ». Non adopté par défaut en attendant la cartographie
bord→centre (exp 7). Détail : `resultats_diag_b2_thermostat_capteurs.log`.

---

# B. Précisions sur les expériences (clarifications utilisateur)

**Relevé 1 — ce qu'il reste à mesurer.** Le décalage en x du centre de la bobine par rapport au
spot visé (`decalage_x`, figé à 0). Les cotes propres de la bobine (section, entraxe, hauteur,
plan image) sont déjà résolues. Peu critique.

**Exp 6 — protocole caméra (diffusivité).** Deux points de physique : (1) la caméra lit la
**surface**, pas l'interface — OK pour la *longueur de décroissance* latérale (propriété
matériau identique en surface), mais comparer à la surface du modèle 3D, pas à l'interface ;
(2) **retirer la céramique d'espacement ≠ se rapprocher du modèle** — le modèle la représente
comme le gap bobine-laminé de 2 mm (EM) ET la CL `h_haut` ; la retirer change les deux (source
EM plus forte, `h_haut` différent). Mode opératoire : spot unique 250/200 A sous Tf, décroissance
en **x au-delà de l'empreinte du CFC** (la largeur y est masquée par le CFC → TC noyés).

**Exp 7 — la caméra ne voit pas l'interface.** La cible est le profil **à l'interface** (le
« M ») ; la caméra de dessus est masquée par le CFC/céramique et ne montre qu'un M atténué en
surface. Il faut des **TC noyés à l'interface** aux 5 positions. La caméra reste un complément
(surface, face CFC).

**Mesure 9 (`k_plan` direct).** Appareil de labo (hot-disk/flash laser) sur un échantillon de
matière : impulsion de chaleur → vitesse d'étalement → `k_plan`. L'exp 6 en est le substitut
« maison ».

**Mesure 10 (σ(T)).** Mesure 4 pointes en montée en température → variation de la conductivité
électrique avec T (le modèle prend σ constante). La plus lourde des dix.

---

# C. Résultats des manips réalisées

## Exp 6/7 — Cartographie bord→centre, 1re série (2026-07-27)

Données : `data/exp7_bord-centre_2026-07-27_sans-ceramique/` (README = analyse complète). Manips étiquetées
« exp 6 » mais qui réalisent la cartographie en largeur (exp 7) : 5 TC en largeur au spot 3,
**150 / 200 / 250 A**, céramique + pression **retirées**.

**Résultat (reproduit sur 3 courants).** Profil ΔT au pic (TC fiables ; TC1 écarté) :

| essai | y10 | y20 (centre) | y30 | y40 | chant/centre |
|---|---|---|---|---|---|
| 150 A | 150 | **111** | 151 | 150 | 1,35 |
| 200 A | 116 | **78** | 124 | 146 | 1,88 |
| 250 A | 139 | **96** | 146 | 178 | 1,85 |
| modèle | 382 | **292** | 382 | 717 | **2,46** |

- **Vallée centrale du M CONFIRMÉE aux 3 courants** : le centre (y=20) est un creux (min local,
  plus froid que ses voisins) et le plus lent à monter (4-5 vs 9-19 °C/s).
- **Le modèle SUR-CONTRASTE** : chant/centre mesuré **1,35-1,88** vs **2,46 prédit** — même sens
  que le point du chauffe (395 mesuré vs 292 prédit).
- **TC1 écarté partout** (incohérent : ΔT 235 erratique à 150 A ; ~50 quasi mort à 200/250 A).
- **PAS de falsification quantitative de l'amplitude** : géométrie non standard (céramique +
  pression retirées → gap ≈ 0, source EM ≠ modèle), TC1 mort, profils un peu asymétriques,
  vidéo 200 A illisible. → **reprise propre** prévue le 2026-07-28 (checklist exp 7).
