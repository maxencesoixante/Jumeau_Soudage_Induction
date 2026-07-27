**Projet** : jumeau numérique du soudage par induction CF/PEKK &nbsp;·&nbsp; **Objet** : mesures
**encore À FAIRE** &nbsp;·&nbsp; **Mis à jour** : 2026-07-27

> Ce fichier ne liste que **ce qui reste à faire**. Les réponses terrain, précisions et
> résultats des manips déjà réalisées sont dans **[`releves_resolus.md`](releves_resolus.md)**
> et les `data/exp*/README.md`.

---

## À faire — par priorité

### 1. ★ Exp 7 — Cartographie bord→centre (REPRISE PROPRE, prévue 2026-07-28)

**Pourquoi.** Mesure clé du levier « forme de la source ». Une 1re série (200/250 A) a confirmé
la vallée du M et montré que le modèle **sur-contraste** (chant/centre ~1,85 mesuré vs 2,46
prédit), mais sans céramique → amplitude non falsifiable. La reprise doit **caler l'amplitude**
contre la cible.

**Cible falsifiable** (modèle, 250 A, au pic) :

| y (mm) | 0 | 10 | 20 (centre) | 30 | 40 |
|---|---|---|---|---|---|
| T_pic prédite (°C) | 717 | 382 | **292** | 382 | 717 |

Contraste bord/centre prédit = **2,46×**.

**Checklist (corrige les 4 réserves de la 1re série) :**
1. **Céramique d'espacement EN PLACE** (+ pression nominale) → gap 2 mm standard = géométrie du
   modèle. C'est LE point : sans ça, la source EM diffère et les absolus ne comparent pas.
2. **5 TC valides à l'INTERFACE**, y = 0/10/20/30/40 mm, x = 60 mm. **Remplacer TC1**
   (défaillant les deux fois). Vérifier chaque voie avant (toutes à l'ambiant, sans saut).
3. **Montage CENTRÉ en largeur** (le profil montait vers y=40 → décalage). Viser TC1↔TC5
   symétriques.
4. **250 A** ; noter la fréquence (388 kHz).
5. **Caméra** (optionnelle) : **finaliser l'enregistrement** (la vidéo 200 A était tronquée) ou
   exporter un **CSV radiométrique** (ligne/points ROI).
6. Déposer dans `data/exp7_bord-centre_2026-07-28_avec-ceramique/` + README (courant, géométrie, positions TC,
   repère spatial) → analyse + confrontation à la cible.

### 2. Exp 8 — Température de la face active du CFC

**Objectif.** Mesurer la température du concentrateur pendant une chauffe (caméra FLIR A700 sur
la face active, ou TC posé). Vue de dessus idéale ici (la face du CFC est directement visible).
**Résout** : le déficit de chauffe en surface (TC1) — seule mesure qui l'attaque. Comparer la
montée du CFC à celle de TC1. Un essai.

### 3. Relevé 1 — Position longitudinale de la bobine

**Objectif.** Mesurer le décalage en x du centre de la bobine par rapport au spot visé
(paramètre `decalage_x`, figé à 0 faute de mesure). Pied à coulisse, 15 min. **Peu critique** :
si non mesurable facilement, on le laisse figé. (Les cotes propres de la bobine sont déjà
résolues, cf. archive.)

### 4. Exp 6 — Diffusivité latérale (optionnel, non prioritaire)

**Objectif.** `k_plan` effectif via la décroissance latérale de T. Depuis la correction de
géométrie, le modèle s'accorde à `k_plan = 3 W/m·K` (physique) : cette mesure ne tranche plus
un écart ouvert, elle **vérifie** une propriété assumée. Protocole caméra détaillé dans
l'archive. Un essai, sous Tf, échantillons réutilisables.

### 5. Mesures de propriété au labo (optionnel, si les niveaux 1-2 ne suffisent pas)

- **Mesure 9 — `k_plan` direct** : hot-disk ou flash laser sur un échantillon de laminé.
- **Mesure 10 — σ(T)** : conductivité électrique en fonction de T (4 pointes en montée) ; le
  modèle prend σ constante aujourd'hui. La plus lourde des dix.

---

## Corrections modèle en attente (à intégrer ENSEMBLE à la prochaine recalibration)

Découlent des réponses terrain (détail : [`releves_resolus.md`](releves_resolus.md)) :

- **Loi thermostat « capteurs »** — flag prêt (`--thermostat-capteurs`, défaut off).
- **Épaisseur twill 0,28 → 0,20 mm** — préparée (commentaire config).
- **`h_bord_x0`** — requalifié effectif (chants libres) ; candidat au retrait.
- **Fréquence A-3 (200 A) 388 → 383 kHz** — fréquence par essai à ajouter.

Idéalement recalibrées **après** la reprise exp 7 (elles sont couplées au profil en M).

---

## Tableau de synthèse — items ouverts

| # | Mesure | Priorité | Résout |
|---|---|---|---|
| Exp 7 | Cartographie bord→centre (reprise propre) | ★ **haute** (28/07) | amplitude du profil en « M » |
| Exp 8 | Température face active du CFC | moyenne | déficit de surface TC1 |
| Relevé 1 | Position longitudinale bobine | basse | `decalage_x` (figé) |
| Exp 6 | Diffusivité latérale | basse (vérif.) | `k_plan` |
| Mesure 9 | `k_plan` direct (labo) | basse | `k_plan` sourcé |
| Mesure 10 | σ(T) (labo) | basse | dépendance σ(T) |

*Items résolus (relevés 2-5) et résultats des manips déjà faites : voir
[`releves_resolus.md`](releves_resolus.md).*
