# Fiche protocole — Exp 9 : Dissipation longitudinale de la chaleur (cartographie T(x))

**Projet** : jumeau numérique du soudage par induction CF/PEKK · **Date de rédaction** : 2026-07-28
**Réalise l'objectif de** : Exp 6 (diffusivité latérale / `k_plan`) de `mesures_a_realiser.md`, sous
une forme directe (ligne de thermocouples le long de la longueur).

---

## 1. Objectif et ce que ça résout

Mesurer la **décroissance de température le long de la longueur** de l'échantillon, `T(x)`, en
s'éloignant du spot d'induction. C'est la mesure qui attaque **le seul résidu ouvert du jumeau** :
le modèle valide le profil en largeur (« M ») et la loi en I², mais **son étalement de chaleur
est trop lent** (le centre se remplit trop lentement, les points hors-spot chauffent trop
lentement — cf. `journaux/archive/resultats_diag_taux_chauffe.log`, résidu n°2 du `journal_avancees.md`).

`T(x)` donne :
- la **longueur de décroissance** de la chaleur en longueur (empreinte source + conduction) ;
- la **diffusivité effective dans le plan** `α = k_plan / (ρ·cp·e)` → validation directe de `k_plan`
  (aujourd'hui figé à 3 W/m·K, physique mais non mesuré) ;
- séparément, à la **montée** (source + conduction) et au **refroidissement** (conduction seule).

**Échantillons réutilisables** : aucune fusion n'est nécessaire. On reste **≤ 270 °C** au point le
plus chaud (le spot), très en dessous de la dégradation du PEKK (~450 °C) et de sa fusion. La
décroissance et la diffusivité se mesurent parfaitement en dessous de Tf.

---

## 2. Principe : deux configurations qui séparent source et conduction

On pose une **ligne de thermocouples orientée selon la longueur** (axe x), à une position en
largeur `y` fixée, et on répète pour deux valeurs de `y` :

| Phase | Ligne TC en x, à | Ce que ça mesure |
|---|---|---|
| **1 — bord (chant)** | `y = 0 mm` (bord, lobe chaud du M) | source EM forte + conduction → **empreinte de la source** en longueur |
| **2 — centre** | `y = 20 mm` (centre, œil de la boucle) | source EM ≈ 0 → **conduction quasi pure** → probe direct de `k_plan` |

Comparer les deux (et au modèle) dit si le défaut d'étalement vient de la **conduction**
(`k_plan` trop faible) ou de la **forme de la source** en longueur. Aucune mesure actuelle ne le
distingue.

---

## 3. Montage (identique à exp 7, sauf orientation des TC)

- **Échantillon** stratifié CF/PEKK, **twill suscepteur en surface** (côté induction), même stack
  qu'exp 7.
- **Céramique d'espacement en place** + pression nominale → gap 2 mm standard = géométrie du modèle.
  (C'est indispensable : sans elle, la source EM diffère et rien n'est comparable.)
- **Un seul spot d'induction, fixe et de position connue** (pas de multi-passes) → source ponctuelle
  propre pour mesurer la décroissance.
- **TC à l'interface** (comme exp 7 : le modèle 2D est lumpé à l'interface).
- Générateur Ambrell EASYHEAT, **fréquence 388 kHz** (constante, cf. relevé 2026-07-28).

---

## 4. Repère spatial et positions des thermocouples

- **Origine `x = 0` = centre du spot** (le point le plus chaud). Repérer et **mesurer au pied à
  coulisse** la position de chaque TC par rapport à ce centre (l'exploitation dépend directement
  de ces distances — les noter au mm près).
- **Positions recommandées en x** (à partir du centre, du plus chaud au plus loin) :

  `x = 0, 10, 20, 30, 40, 60 mm`

  Plus il y a de points sur la pente de décroissance, mieux la longueur de décroissance et `α`
  seront contraintes. 5–6 TC est un bon compromis. Si possible, un TC **au-delà** de la zone chaude
  (x = 60 mm) pour capter la queue.
- **Vérifier chaque voie à froid AVANT l'essai** : toutes les voies doivent lire la **même valeur
  ambiante**, sans saut ni voie morte (le TC1 défaillant d'exp 7 a coûté des essais).

---

## 5. Paramétrage de la chauffe

- **Courant** : commencer à **200 A** (proche des points de calibration, montée ni trop lente ni
  trop rapide). Optionnellement répéter à **150 et 250 A** : la diffusivité doit être
  **indépendante du courant** → excellent test de cohérence.
- **Consigne d'arrêt** : couper le spot à **≤ 270 °C** au TC le plus chaud (x = 0), pour ne pas
  dégrader l'échantillon et le garder réutilisable.
- **Chauffe reproductible** : même courant et même critère d'arrêt à chaque essai. Le **transitoire**
  (vitesse d'arrivée de la chaleur à chaque x) est justement ce que le modèle rate → il faut qu'il
  soit répétable pour le confronter.
- **⚠ Fréquence d'acquisition** : à 250 A le pic est atteint en ~8 s. **Échantillonner à ≥ 5 Hz**
  (idéalement 10 Hz) au lieu de 1 Hz : à 1 Hz la montée rapide n'est décrite que par ~8 points, trop
  peu pour ajuster la dynamique. C'est le point le plus important pour l'exploitation.

---

## 6. Déroulé d'un essai

1. Monter l'échantillon centré, céramique en place, pression nominale.
2. Poser la ligne de TC selon x à la position `y` de la phase (0 puis 20 mm), mesurer les x.
3. Vérifier toutes les voies à l'ambiant (même valeur, stables). **Noter l'ambiante.**
4. Lancer l'acquisition (≥ 5 Hz), attendre ~3–5 s de ligne de base ambiante (une courte base
   suffit — pas besoin d'un long préambule).
5. Démarrer le spot. **Chauffer** jusqu'à 270 °C au TC x = 0, puis **couper**.
6. **Laisser refroidir en acquisition** jusqu'à ~100 °C (le refroidissement est une donnée clé :
   conduction pure, source coupée, sans fusion).
7. Arrêter l'acquisition. Enregistrer le fichier.
8. **2–3 répétitions** par (phase, courant).

---

## 7. Ce qu'on extrait (exploitation)

- **Profil de décroissance `T(x)`** au pic et à divers instants → longueur de décroissance.
- **Diffusivité effective `α`** par deux voies indépendantes :
  - à la **montée** (temps d'arrivée / retard de la chaleur à chaque x) ;
  - au **refroidissement** (décroissance spatiale/temporelle sans source — le plus propre).
- **Confrontation au modèle 2D** : le jumeau reproduit-il la longueur de décroissance et sa
  dynamique ? Sinon, l'écart pointe `k_plan` (phase centre) ou la source en longueur (phase bord).

---

## 8. Livrable

- Déposer les fichiers dans **`data/exp9_dissipation-longitudinale_<date>/`**, avec sous-dossiers
  par phase (`bord_y0/`, `centre_y20/`) et par courant si plusieurs.
- **README** par campagne : courant, fréquence, positions x mesurées de chaque TC, `y` de la phase,
  ambiante, critère d'arrêt, fréquence d'acquisition.
- Format fichier identique à exp 7 (TAB, décimale virgule, en-tête `Time (s)\tTC1 (C)\t…`).

---

## 9. Points de vigilance (résumé)

- Céramique en place (sinon incomparable au modèle) · TC à l'interface · spot unique fixe.
- **Mesurer les x au pied à coulisse** (l'exploitation en dépend).
- **Acquisition ≥ 5 Hz** (sinon la montée rapide est sous-échantillonnée).
- **≤ 270 °C** au point chaud (réutilisabilité) · enregistrer **le refroidissement**.
- Vérifier toutes les voies à froid · 2–3 répétitions.
