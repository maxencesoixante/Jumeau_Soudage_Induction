# Consolidation du jumeau numérique — design

**Date** : 2026-07-29 · **Décision utilisateur** : recalibration groupée complète, les 4
corrections repliées, choix de l'essai de référence délégué (« fais ce que tu penses le mieux »).

## Problème / motivation
Le jumeau est dans un état **divergent** et ses campagnes labo ne sont pas intégrées au
pipeline formel :
- **θ\* multiples** : les figures utilisent `facteur_couplage=6.0123, h_haut=30.087,
  h_bas_2d=37.424, h_bord_x0=250` (overrides fig3), alors que `config/materiaux.yaml` porte
  `facteur_couplage=1.0, h_bas_2d=50.919`. Pas de θ\* canonique unique.
- **Corrections préparées non appliquées** : twill 0,28→0,20 mm ; `h_bord_x0` (chants libres →
  effectif, non physique) ; loi thermostat « capteurs » (B-2) ; lissage source σ (centre-fill).
- **Campagnes labo hors validation formelle** : `calibrer.py`/`valider.py` tournent encore sur
  série A/B (3 TC). exp7 (profil M, 5 courants) et exp9 (dissipation, 4 courants) ne sont
  confrontés qu'inline dans des scripts de figure.

**Objectif** : un **θ\* canonique unique**, calibré sur le labo récent, corrections appliquées,
exp7/exp9 intégrés à la validation formelle, avec UQ et rapport de métriques — le tout adopté
dans la config **seulement si** la validation croisée montre une amélioration nette ou neutre
(discipline projet : pas de régression du RMSE global).

## Décisions figées
| Sujet | Décision |
|---|---|
| Modèle | **2D lumpé** (essais à TC d'interface ; ~2-4 min/essai) |
| Essai de référence calibration | **exp7 200 A avec céramique** (5 TC bord→centre, géométrie standard, profil M identifiable) |
| Paramètres calibrés | `facteur_couplage`, `h_haut`, `h_bas_2d`, `h_bord_x0` (effectif) ; **σ source en 5ᵉ param optionnel** pour ré-arbitrer avec les nouvelles données |
| twill | **0,28 → 0,20 mm** (mesure user) appliqué en config |
| h_bord_x0 | gardé **effectif**, re-fit ; tester aussi `h_bord_x0=0` (le twill 0,20 + géométrie corrigée le rendent-ils inutile ?) |
| Loi capteurs | activée pour la validation **B-2** (essai-spécifique) |
| Lissage σ | ré-arbitré par la calibration ; **défaut probable OFF** sauf gain net |
| Essais de validation croisée | exp7 150/200/250 A, exp9 200 A monospot, série A-1/A-3/B-2 |
| Adoption | θ\*_new + corrections écrits en config **ssi** métriques ≥ référence actuelle |

## Orchestration par agents (séquentielle — la calibration est un maillon unique)
1. **validation-data-engineer** — Intégration : créer les YAML `config/essais/` pour exp7
   (150/200/250 A) et exp9 (200 A monospot) sur le schéma de `serieA_A-1.yaml` ; appliquer
   twill 0,20 + doc `h_bord_x0` ; confronter le θ\* **actuel** à tous les essais → **table
   baseline** (métriques par TC).
2. **calibration-uq-specialist** — Recalibration : LHS+NLSQ 2D sur exp7 200 A des 4 (+σ opt.)
   paramètres, pondéré par le bruit capteur ; identifiabilité + UQ (CI/covariance) →
   **θ\*_new + recommandation** (dont σ on/off, h_bord_x0=0 ?).
3. **validation-data-engineer** — Validation croisée : `valider.py` avec θ\*_new sur tous les
   essais (capteurs pour B-2) → **table décision** vs baseline (adopter ou non).
4. **simulation-verification-engineer** — Vérif : bilans énergie/puissance + 38 tests verts +
   régression épinglant θ\*_new.
5. **Orchestrateur (moi)** — Si adopté : synchroniser config au θ\* canonique unique, MAJ
   `journal_avancees.md` (§θ\*, §3bis), README, mémoire ; commit.

## Garde-fous
- Ne **rien écrire** dans `config/materiaux.yaml` comme nouveau θ\* de référence avant la table
  décision (phase 3). Les agents rapportent ; l'orchestrateur adopte.
- Un seul agent modifie la config à la fois (pas de calibration parallèle).
- Chaque phase = un livrable vérifiable ; on s'arrête si une phase régresse sans explication.
