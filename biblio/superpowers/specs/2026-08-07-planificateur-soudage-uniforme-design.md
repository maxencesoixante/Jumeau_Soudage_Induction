# Spec — Planificateur de soudage uniforme

**Date : 2026-08-07.** Outil de planification, par-dessus le jumeau calibré, qui génère
une séquence de passes de chauffe couvrant **toute** l'interface de soudure et produit une
carte de couverture prouvant (ou réfutant) l'uniformité.

## Contexte & problème

Avec un spot fixe, le jumeau prédit un **profil en « M »** : les chants (y=0/40 mm)
chauffent fortement, le centre (y≈20 mm) reste froid (contraste ~3× — c'est l'« œil » de la
boucle de courants induits, `ψ=0` au bord de la plaque). Souder **tout** l'échantillon de
façon uniforme est donc physiquement tendu : au moment où le centre atteint la fusion, les
chants dépassent largement la dégradation.

Le procédé peut indexer la tête en **longueur (x)** ET la décaler en **largeur (y)** →
plusieurs passes à différents offsets. L'outil exploite ces leviers pour chercher une
couverture complète, et **rapporte honnêtement** ce qui est atteignable.

## Objectif (critère de réussite)

**Couverture** : chaque point de l'interface atteint **≥ fusion (337 °C)** au moins une fois,
sans qu'aucun point n'atteigne **≥ dégradation (450 °C)**. Souder 100 % de la surface.

## Leviers & contraintes

- **Leviers** : passes `{position (x_c, y_c), courant, durée}`. Nombre de passes libre.
- **Contraintes** : aucun point ≥ 450 °C (dur) ; courant ∈ **[150, 250] A** (fenêtre validée,
  interpolation) ; θ\* de référence **figé** (aucune recalibration).
- **Hors scope v1** : géométrie MFC comme levier (le levier retenu est x+y). Extension
  naturelle si x+y s'avère insuffisant (cf. « Risque de faisabilité »).

## Approche retenue

**A (plan glouton par empreintes) + vérification séquentielle** :
1. Pré-calculer la bibliothèque d'empreintes `Tmax(x,y)` de passes uniques (grille de
   positions × courants), **une fois**.
2. Glouton : sélectionner les passes qui couvrent la surface (combinaison par `max`), sous
   contrainte de dégradation + fenêtre de courant.
3. Rejouer le plan en **une simulation multi-passes réelle** pour confirmer le `Tmax(x,y)`.

Approximation gloutonne « passes indépendantes » (`Tmax = max` des empreintes) : elle ignore
l'accumulation de chaleur résiduelle inter-passes, qui **aide** la couverture → l'estimation
gloutonne est **conservatrice** (la vérif séquentielle donne une couverture ≥).

## Architecture & composants

Chaque unité a un but unique, une interface claire, et est testable seule.

### 1. Décalage en y de la source (`em/source_joule.py`)
Ajouter un paramètre `decalage_y` (m, défaut 0.0) à `source_spot`, câblé vers
`champ_coil.sommets_hairpin(centre_y=…)` (déjà supporté). **Non-régressif** : `decalage_y=0.0`
reproduit le comportement actuel bit-à-bit.

### 2. Empreinte d'une passe (`planification/empreinte.py`)
`empreinte(x_c, y_c, courant, duree, ...) -> Tmax(x,y)` : reconstruit la source au
`(x_c, y_c, courant)` demandé (θ\* figé), simule le solveur **2D**, et renvoie la carte du
**pic** de température à l'interface pendant la passe. Déterministe.

### 3. Bibliothèque d'empreintes (`planification/empreinte.py`)
Pré-calcule les empreintes sur une grille `(x_c × y_c)` et un jeu de courants ; mise en cache
(en mémoire, et optionnellement sur disque `donnees/resultats/`) pour éviter de re-simuler dans la
boucle gloutonne.

### 4. Planificateur glouton (`planification/planificateur.py`) — cœur, PUR
Logique de couverture indépendante du modèle (opère sur des cartes `Tmax` fournies), donc
**testable sur empreintes synthétiques** :
- État = carte `Tmax_combiné(x,y)` (init. ambiant).
- Candidats = empreintes de la bibliothèque.
- À chaque étape : choisir la passe qui **maximise la surface nouvellement couverte** (nœuds
  passant ≥ 337) telle que `max(Tmax_combiné, empreinte)` ne dépasse **450 nulle part**.
- Ajouter la passe (`Tmax_combiné ← max(…)`) ; répéter jusqu'à couverture complète **ou**
  aucune passe n'améliore.
- Sorties : liste ordonnée de passes, `Tmax_combiné`, métriques (% soudé / non soudé /
  dégradé), et zone non couverte le cas échéant.

### 5. Vérification séquentielle (`code/scripts/planifier_soudage.py`)
Construit une séquence temporelle réelle des passes du plan (patron `Essai`/multi-empreintes,
étendu aux offsets y) et simule → vrai `Tmax(x,y)`. Compare à l'estimation gloutonne (attendu
séquentiel ≥ glouton).

### 6. CLI & reporting (`code/scripts/planifier_soudage.py`)
- **Plan** : imprimé + sauvé `donnees/resultats/plan_soudage.yaml`.
- **Carte de couverture** : `biblio/modele/figures/fig_plan_soudage_couverture.png` — `Tmax(x,y)`,
  contours 337/450, zones bleu (non soudé) / vert (soudé) / rouge (dégradé), positions des
  passes, métriques annotées.
- **Verdict** : « X % soudé, Y % non atteint, Z % dégradé — uniforme : oui/non » ; si < 100 %,
  description de la zone non couverte.

## Sortie détaillée

Plan (console + YAML) :
```
# | x_c (mm) | y_c (mm) | courant (A) | durée (s)
```
Figure `fig_plan_soudage_couverture.png` (modèle pur → `biblio/modele/figures/`).

## Tests (`tests/test_planification.py`)

- **Source y-offset** : `decalage_y=0` byte-identique (non-régression) ; `decalage_y≠0`
  déplace le pic de source en y.
- **Empreinte** : forme de carte correcte ; courant ↑ → `Tmax` ↑ ; déterministe.
- **Glouton (synthétique, rapide)** : couvre un domaine tuilable ; **rejette** une passe
  dépassant 450 ; **s'arrête** proprement en couverture partielle ; métriques correctes ;
  combinaison = `max` élément par élément.
- **Bout-en-bout (lent, 1 cas)** : produit plan + carte ; couverture séquentielle ≥ gloutonne.

## Risque de faisabilité (assumé, intégré)

Avec le MFC actuel (large, 55 mm), le profil en M est piloté par les bords de la **plaque**
(`ψ=0`), pas par la position de la bobine — un décalage en y **pourrait ne pas** réchauffer le
centre sans cuire les chants. L'outil **ne présuppose pas** la faisabilité : il génère le
meilleur plan et **rapporte la couverture réelle**. Si 100 % est hors d'atteinte avec x+y, la
sortie l'explicite (zone centrale non couverte) — résultat en soi utile (indique qu'un MFC
plus étroit serait nécessaire, extension future).

## Structure du dépôt (fichiers)

- **Nouveau** `code/src/jumeau/planification/__init__.py`, `empreinte.py`, `planificateur.py`
- **Nouveau** `code/scripts/planifier_soudage.py`
- **Nouveau** `tests/test_planification.py`
- **Modifié (non-régressif)** `code/src/jumeau/em/source_joule.py` (param `decalage_y`)
- **Sorties** `donnees/resultats/plan_soudage.yaml` (gitignoré), `biblio/modele/figures/fig_plan_soudage_couverture.png`

## Vérification (bout-en-bout)

1. `pytest tests/test_planification.py` — unités (source non-régressive, empreinte, glouton).
2. `python code/scripts/planifier_soudage.py` — produit le plan, la vérif séquentielle et la carte.
3. Confirmer : couverture séquentielle ≥ gloutonne ; suite complète des tests toujours verte.

## Hors scope (v1)

Optimisation formelle (min. passes/temps), géométrie MFC comme variable, mécanique/pression,
cristallisation, 3D. La v1 est un **générateur de plan + carte de couverture** honnête.
