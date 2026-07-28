**Projet** : jumeau numérique du soudage par induction CF/PEKK &nbsp;·&nbsp; **Objet** : mesures
**encore À FAIRE** &nbsp;·&nbsp; **Mis à jour** : 2026-07-28

> Ce fichier ne liste que **ce qui reste à faire**. Les réponses terrain, précisions et
> résultats des manips déjà réalisées sont dans **[`releves_resolus.md`](releves_resolus.md)**
> et les `data/exp*/README.md`.

> ✅ **Exp 7 — Cartographie bord→centre : CLOSE (2026-07-28).** Campagne aux **5 courants
> (150 / 176 / 200 / 225 / 250 A, avec céramique ; 3 essais aux 150/200/250, 1 aux 176/225)**.
> Le profil en « M » est **symétrique et de bonne forme d'équilibre** (contraste mesuré ~2,0-2,2
> vs modèle 2,4-2,55) ; seul résidu = **transitoire** (le centre du modèle se remplit trop
> lentement, indépendant du courant). Levier source-adoucie testé → flag off ; cp/k_plan/placement
> TC écartés ; 3D confirme le mécanisme mais surchauffe l'interface → 2D lumpé conservé avec limite
> documentée. **Loi taux-courant** : le taux de chauffe au chant croît **∝ I^2,4** (un peu plus
> vite que I² ; candidat = fréquence générateur montant avec I). Détail :
> `data/exp7_bord-centre_2026-07-28_avec-ceramique/README.md`. Figures : `docs/figures_presentation/`
> (fig1-5).

---

## À faire — par priorité

### 1. Exp 8 — Température de la face active du CFC

**Objectif.** Mesurer la température du concentrateur pendant une chauffe (caméra FLIR A700 sur
la face active, ou TC posé). Vue de dessus idéale ici (la face du CFC est directement visible).
**Résout** : le déficit de chauffe en surface (TC1) — seule mesure qui l'attaque. Comparer la
montée du CFC à celle de TC1. Un essai.

### 2. Relevé 1 — Position longitudinale de la bobine

**Objectif.** Mesurer le décalage en x du centre de la bobine par rapport au spot visé
(paramètre `decalage_x`, figé à 0 faute de mesure). Pied à coulisse, 15 min. **Peu critique** :
si non mesurable facilement, on le laisse figé. (Les cotes propres de la bobine sont déjà
résolues, cf. archive.)

### 3. Exp 6 — Diffusivité latérale (optionnel, non prioritaire)

**Objectif.** `k_plan` effectif via la décroissance latérale de T. Depuis la correction de
géométrie, le modèle s'accorde à `k_plan = 3 W/m·K` (physique) : cette mesure ne tranche plus
un écart ouvert, elle **vérifie** une propriété assumée. Protocole caméra détaillé dans
l'archive. Un essai, sous Tf, échantillons réutilisables.

### 4. Mesures de propriété au labo (optionnel, si les niveaux 1-3 ne suffisent pas)

- **Mesure 9 — `k_plan` direct** : hot-disk ou flash laser sur un échantillon de laminé.
- **Mesure 10 — σ(T)** : conductivité électrique en fonction de T (4 pointes en montée) ; le
  modèle prend σ constante aujourd'hui. La plus lourde des dix.

---

## Corrections modèle en attente (à intégrer ENSEMBLE à la prochaine recalibration)

Découlent des réponses terrain (détail : [`releves_resolus.md`](releves_resolus.md)). La reprise
exp 7 étant close, ces corrections ne sont plus bloquées et peuvent être recalibrées ensemble :

- **Loi thermostat « capteurs »** — flag prêt (`--thermostat-capteurs`, défaut off).
- **Épaisseur twill 0,28 → 0,20 mm** — préparée (commentaire config).
- **`h_bord_x0`** — requalifié effectif (chants libres) ; candidat au retrait.
- **Fréquence A-3 (200 A) 388 → 383 kHz** — fréquence par essai à ajouter.
- **Lissage de source** (`--source-sigma-mm`, défaut off) — testé exp 7 : remplit le centre mais
  abaisse les pics → **non retenu** tel quel ; à ré-arbitrer seulement si le centre-fill devient
  prioritaire.

---

## Tableau de synthèse — items ouverts

| # | Mesure | Priorité | Résout |
|---|---|---|---|
| Exp 8 | Température face active du CFC | moyenne | déficit de surface TC1 |
| Relevé 1 | Position longitudinale bobine | basse | `decalage_x` (figé) |
| Exp 6 | Diffusivité latérale | basse (vérif.) | `k_plan` |
| Mesure 9 | `k_plan` direct (labo) | basse | `k_plan` sourcé |
| Mesure 10 | σ(T) (labo) | basse | dépendance σ(T) |

*Items résolus (relevés 2-5, **exp 7**) et résultats des manips déjà faites : voir
[`releves_resolus.md`](releves_resolus.md) et les `data/exp*/README.md`.*
