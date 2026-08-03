**Projet** : jumeau numérique du soudage par induction CF/PEKK &nbsp;·&nbsp; **Objet** : mesures
**encore À FAIRE** &nbsp;·&nbsp; **Mis à jour** : 2026-08-03

> Ce fichier ne liste que **ce qui reste à faire**. Les réponses terrain, précisions et
> résultats des manips déjà réalisées sont dans **[`releves_resolus.md`](releves_resolus.md)**
> et les `data/exp*/README.md`.

> ✅ **Exp 7 — Cartographie bord→centre : CLOSE (2026-07-28).** Campagne aux **5 courants
> (150 / 176 / 200 / 225 / 250 A, avec céramique ; 3 essais aux 150/200/250, 1 aux 176/225)**.
> Le profil en « M » est **symétrique et de bonne forme d'équilibre** (contraste mesuré ~2,0-2,2
> vs modèle 2,4-2,55) ; seul résidu = **transitoire** (le centre du modèle se remplit trop
> lentement, indépendant du courant). Levier source-adoucie testé → flag off ; cp/k_plan/placement
> TC écartés ; 3D confirme le mécanisme mais surchauffe l'interface → 2D lumpé conservé avec limite
> documentée. **Loi taux-courant** : la source suit **I²** (modèle `R=k·I²−L`, R²=0,999) ; la
> fréquence mesurée est constante (388±2 kHz sur 5 courants) → couplage fréquence↔courant écarté.
> Détail :
> `data/exp7_bord-centre_2026-07-28_avec-ceramique/README.md`. Figures : `docs/figures/`
> (fig1-5).

---

## À faire — par priorité

### 1. ★ Exp 9 — Dissipation longitudinale de la chaleur T(x) — EN COURS

**Fait (2026-07-28) — phase 1 au bord (y=0), 200 A** : TC à x=0/30/60/90/120 mm. Monospot (x=60) et
semi-statique confrontés au modèle → **la source en longueur est validée** (décroissance raide
reproduite). Détail : `data/exp9_dissipation-longitudinale_2026-07-28/README.md`.

**Reste à faire** :
- **Phase 2 — ligne au CENTRE (y=20)** : source ≈ 0 → conduction quasi pure → **probe direct de
  `k_plan`** et vrai juge du résidu d'étalement. **C'est la mesure décisive.**
- Recentrer le spot (offset de montage +x constaté) ; enregistrer le refroidissement.
- Optionnel : autres courants (150/250 A) pour vérifier l'indépendance de la diffusivité au courant.

**Résout** le résidu n°1 (étalement de chaleur trop lent) : donne la longueur de décroissance et la
diffusivité `α = k_plan/(ρ·cp·e)`. Échantillons réutilisables (≤ 270 °C). Réalise l'objectif d'Exp 6.
**Fiche : [`protocole_exp_dissipation_longitudinale.md`](protocole_exp_dissipation_longitudinale.md).**

### 2. Exp 8 — Température de la face active du MFC

**Objectif.** Mesurer la température du concentrateur pendant une chauffe (caméra FLIR A700 sur
la face active, ou TC posé). Vue de dessus idéale ici (la face du MFC est directement visible).
**Résout** : le déficit de chauffe en surface (TC1) — seule mesure qui l'attaque. Comparer la
montée du MFC à celle de TC1. Un essai.

### 3. Relevé 1 — Position longitudinale de la bobine

**Objectif.** Mesurer le décalage en x du centre de la bobine par rapport au spot visé
(paramètre `decalage_x`, figé à 0 faute de mesure). Pied à coulisse, 15 min. **Peu critique** :
si non mesurable facilement, on le laisse figé. (Les cotes propres de la bobine sont déjà
résolues, cf. archive.)

### 4. Exp 6 — Diffusivité latérale (→ désormais couverte par Exp 9)

**Objectif.** `k_plan` effectif via la décroissance latérale de T. **Réalisée sous une forme
directe par Exp 9** (ligne de TC en longueur, phase centre = conduction pure). Garder cette entrée
comme rappel de l'option « caméra » (protocole détaillé dans l'archive) si l'on préfère l'imagerie
aux thermocouples.

### 5. Mesures de propriété matériau au labo — ferment les propriétés GELÉES du modèle

> **Contexte (2026-08-03, suite audit Lionetto — [`../modele/audit_lionetto_2017.md`](../modele/audit_lionetto_2017.md)).**
> L'audit a montré que σ et k sont **figés** dans le jumeau (seul cp dépend de T), là où
> Lionetto (2017) prend σ(T) et k(T). La **capacité k(T)** vient d'être implémentée (forme
> flux-conservative derrière flag `k_plan_T`/`k_z_T`, défaut off) : ces mesures la transforment
> en **courbe mesurée**, évaluable en held-out. Elles **cassent aussi les corrélations de
> calibration** (σ ↔ `facteur_couplage`), première cause d'overfitting.

- **Mesure 9 — k_plan(T) et k_z(T)** (hot-disk ou flash laser sur un échantillon de laminé, à
  25 / 150 / 250 / 340 °C). **Alimente directement le flag k(T) implémenté** (audit §3.1) : la
  courbe mesurée passe le levier de « estimation littérature » à « donnée ». *Priorité relevée
  (feature prête).*
- **Mesure 10 — σ indépendant (twill + laminé), en plan ET vs T** (4 pointes / van der Pauw en
  montée). Verrouille `twill_suscepteur.sigma_plan` et `sigma_0/90` (« incertain ») et
  **découple σ ↔ `facteur_couplage` ↔ f** — f étant déjà mesurée (388 kHz), σ est le dernier
  inconnu corrélé au facteur d'échelle. Donne la courbe σ(T) de l'audit §2.3. **La plus
  structurante côté source EM.**
- **Mesure 11 — DSC du PEKK réel** (chauffe + refroidissement, 2-3 rampes). Donne la **forme du
  pic de fusion** (remplace la gaussienne symétrique `delta_T_fusion=15 °C` par la loi
  Greco–Maffezzoli, audit §4.1 / éq. 9), la cinétique de cristallisation (éq. 10-13), et Tf, Lf
  mesurés. *Peu coûteux, échantillon de matière.*
- **Mesure 12 — Émissivité de surface** (mesure IR à T connue). Verrouille `emissivite=0.96`
  supposée, qui pilote le rayonnement — terme que le jumeau inclut au-delà de Lionetto.

### 6. Validation de la FORME de source & des hypothèses structurelles — propositions 2026-08-03

Attaquent les résidus/hypothèses encore ouverts (profil « M », siège des courants, plaque mince),
au-delà des points TC. Complètent Exp 9 (qui reste la mesure décisive de `k_plan` par conduction).

- **Mesure 13 — ★ Thermographie IR plein champ en chauffe statique.** Le **champ 2D complet** de
  température de surface (pas 3-5 TC), confronté pixel-à-pixel au modèle → juge direct du profil
  « M » et du **résidu d'étalement in-plane**. Upgrade naturel des scans bord→centre (exp 7) :
  soit il confirme la limite structurelle, soit il révèle un biais de forme corrigible. **Haute
  valeur.** (Réutilise la FLIR A700 déjà prévue pour Exp 8.)
- **Mesure 14 — ★ Test décisif twill / sans-twill.** Même chauffe, un échantillon **avec** vs
  **sans** pli twill à l'interface. Valide (ou infirme) l'hypothèse « twill = siège **principal**
  des courants de Foucault » (Série A), fondation de toute la répartition de puissance
  inter-couches — et donc du déficit de chauffe TC1/surface.
- **Mesure 15 — Gradient dans l'épaisseur** (TC surface / interface / face opposée, même spot).
  Teste l'hypothèse **plaque mince** à 388 kHz (décroissance de Bz dans l'épaisseur, audit §2.1 —
  la validité « δ vs épaisseur » restait explicitement non re-vérifiée à cette fréquence).
- **Mesure 16 — Exploitation des traînées de refroidissement** (★ *gratuit, sur les essais
  déjà réalisés*). Ajuster la décroissance **après coupure de la source** sépare proprement
  `h_bas` / rayonnement / conduction support de la source — identification de coefficients de
  perte sans nouveau matériel.
- **Mesure 17 — Balayage de pression de contact MFC/céramique** → `h_contact` / `h_haut`
  (placeholders calibrés) et leur dépendance à la pression du procédé.
- **Mesure 18 — Campagne de répétabilité** (même essai nominal ×5-8) → **modèle de bruit
  capteur/procédé** : fixe le plancher RMSE sous lequel une amélioration = ajustement de bruit
  (garde-fou anti-overfitting pour `calibration-uq-specialist`).

---

## Corrections modèle — TOUTES RÉSOLUES (clôture 2026-08-03)

Découlaient des réponses terrain (détail : [`releves_resolus.md`](releves_resolus.md)). La recalibration
est **close** : aucune correction en attente ne survit au garde-fou held-out.

- **Épaisseur twill 0,28 → 0,20 mm** — ✅ **appliqué** en config ; θ\* déjà recalibré à cette valeur (consolidation 30/07).
- **`h_bord_x0=0`** — ❌ **réfuté** (emballement +200 °C au chant ; exp7 ne peut pas le contraindre). Garder 250 (effectif).
- **Loi thermostat « capteurs »** — ❌ **rejetée (2026-08-03)** : fit joint pleine famille dédié
  (`calibrer_joint.py --thermostat-capteurs`, essais exp7+exp9+serieB_B-2, held-out serieA_A-1/A-3)
  → **PIRE** que la référence OFF sur fit (31,6→42,2), held-out (30,0→41,2) et global (30,8→41,7) :
  le refit divise le facteur par ~2 et raile k_plan à 9,9 → pics effondrés. Le θ\* actuel (thermostat
  OFF) reste l'optimum. Log : `journaux/resultats_calibration_joint_thermostat.log`.
- ~~**Fréquence A-3 (200 A) 388 → 383 kHz**~~ — **abandonnée** : mesure 5 courants (2026-07-28)
  = 388±2 kHz constante, ancien relevé 383 infirmé ; une seule valeur globale suffit.
- **Lissage de source** (`--source-sigma-mm`, défaut off) — testé exp 7 : remplit le centre mais
  abaisse les pics → **non retenu** tel quel ; à ré-arbitrer seulement si le centre-fill devient
  prioritaire.

---

## Tableau de synthèse — items ouverts

| # | Mesure | Priorité | Résout |
|---|---|---|---|
| **Exp 9** | **Dissipation longitudinale T(x)** — phase 1 (y=0) FAITE, **phase 2 (y=20) à faire** | ★ **haute** | étalement trop lent + `k_plan` |
| **Mesure 13** | **Thermographie IR plein champ** (chauffe statique) | ★ **haute** | profil « M » / résidu d'étalement (champ 2D) |
| **Mesure 14** | **Twill / sans-twill** (test décisif) | ★ **haute** | hypothèse siège des courants (Série A), déficit TC1 |
| Mesure 16 | Traînées de refroidissement (essais existants) | moyenne (gratuit) | `h_bas` / rayonnement / conduction support |
| Exp 8 | Température face active du MFC | moyenne | déficit de surface TC1 |
| Mesure 9 | k_plan(T), k_z(T) direct (labo) | moyenne (flag prêt) | alimente le flag k(T) implémenté |
| Mesure 10 | σ indépendant (twill+laminé), σ(T) | moyenne | découple σ↔`facteur_couplage` ; σ(T) |
| Mesure 11 | DSC PEKK (fusion + cristallisation) | moyenne | loi Xm réelle (éq. 9), Tf/Lf |
| Mesure 15 | Gradient dans l'épaisseur | moyenne | hypothèse plaque mince à 388 kHz |
| Mesure 12 | Émissivité de surface | basse | `emissivite` (rayonnement) |
| Mesure 17 | Pression de contact MFC/céramique | basse | `h_contact` / `h_haut` |
| Mesure 18 | Répétabilité (×5-8) | basse (méta) | modèle de bruit / plancher RMSE |
| Relevé 1 | Position longitudinale bobine | basse | `decalage_x` (figé) |
| Exp 6 | Diffusivité latérale | → couverte par Exp 9 | `k_plan` |

*Items résolus (relevés 2-5, **exp 7**) et résultats des manips déjà faites : voir
[`releves_resolus.md`](releves_resolus.md) et les `data/exp*/README.md`.*
