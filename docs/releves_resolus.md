**Projet** : jumeau numérique du soudage par induction CF/PEKK &nbsp;·&nbsp; **Objet** : relevés et questions RÉSOLUS (archive) &nbsp;·&nbsp; **Créé** : 27 juillet 2026

> Ce document archive les relevés de `mesures_a_realiser.md` une fois tranchés, pour garder
> la trace de la donnée et de sa conséquence sur le modèle sans alourdir la liste des mesures
> encore à faire. Les corrections de modèle qui en découlent sont préparées en config
> (`config/materiaux.yaml`) et détaillées dans les journaux `resultats_*.log` cités.

---

## Relevé 2 — Fréquence du générateur à 200 A ✔ (2026-07-27)

**Question.** Fréquence de travail de l'EASYHEAT à 200 A (le modèle suppose 388 kHz, valeur
250 A, pour tous les essais — dont A-3 à 200 A).

**Réponse utilisateur.** « La fréquence à 200 A est de **383 kHz**. » (vs 388 kHz à 250 A)

**Conséquence modèle.** L'essai A-3 (200 A) devrait utiliser **383 kHz** au lieu de 388.
Effet faible (skin depth ∝ 1/√f → ~0,7 % ; le champ Bz est quasi inchangé), mais réel. La
fréquence est aujourd'hui GLOBALE (`config/geometrie.yaml : generateur.frequence: 388e3`) ;
appliquer 383 kHz à A-3 seul demande une **fréquence par essai** (petit ajout : champ
optionnel `frequence` dans le YAML d'essai, lu par `Essai`/`source_spot`). Correction préparée,
à intégrer à la prochaine recalibration (mineure).

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
