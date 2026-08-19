# Design — Protocole de verdict pré-enregistré pour l'anisotropie kx≠ky (issue #12)

**Date :** 2026-08-10
**Statut :** validé (brainstorming), prêt pour plan d'implémentation
**Issues :** #12 (anisotropie kx≠ky), débloquée par #11 (Exp 9 phase 2, acquisition propre y=20 mm)

## Contexte & problème

Le verdict d'adoption de l'anisotropie in-plane `(kx, ky)` (issue #12) est **bloqué par
#11** : sans une acquisition propre de la ligne y=20 mm (spot recentré, refroidissement,
multi-courant), le calage joint 2D est **multimodal en ky** (deux optima à ~3 % de coût,
réfutation du 2026-07-31, reproduite le 2026-08-09).

Le **harnais de calibration existe déjà** et fait ~90 % du travail :
`code/scripts/calibrer_joint.py --anisotrope` réalise le calage joint `(kx, ky)` avec held-out
(`--essais-holdout`), incertitudes, et table RMSE/ΔTmax ref-vs-new. La donnée n'existe pas
encore sous sa forme propre.

**Risque à neutraliser :** décider *après* avoir vu la donnée invite au biais post-hoc
(déplacer les poteaux). La valeur data-free restante est donc de **pré-enregistrer la règle
de décision** — figer la barre AUJOURD'HUI, avant l'acquisition propre — et de la rendre
mécanique via un wrapper « une commande ».

**Résultat visé :** deux artefacts (une pré-enregistration écrite + un wrapper qui applique
la règle et imprime ADOPTÉ/NON-ADOPTÉ), sans nouvelle physique, réutilisant le harnais.

## Décision pré-enregistrée (gravée le 2026-08-10)

**Règle multi-portes stricte — ADOPTER `(kx, ky)` si et seulement si les 4 portes tiennent
simultanément.** Sinon **NON-ADOPTÉ** = limite structurelle actée (comme issue #3).

Ancrages de référence (θ* isotrope canonique, code/config/materiaux.yaml) : held-out RMSE moyen
≈ 16,5 °C ; contraste M de référence 3,14 ; **contraste M mesuré cible = 2,09**.

| Porte | Métrique | Seuil (Standard, pré-enregistré) |
|---|---|---|
| 1. Held-out RMSE | RMSE moyen held-out `new` vs `ref` | `new < ref − 0,5 °C` |
| 2. Held-out ΔTmax | \|ΔTmax\| moyen held-out `new` vs `ref` | `new ≤ ref + 2,0 °C` |
| 3. Contraste M | contraste M `new` (exp7_200A) | strictement plus proche de 2,09 que ref **ET** `≤ 2,6` |
| 4. Non-régression bord | RMSE par-TC de la famille bord (exp7_*) | aucun TC : `rmse_new − rmse_ref > +2,0 °C` |

Ces seuils sont des **constantes nommées** en tête de `verdict_anisotropie.py`. La valeur
pré-enregistrée ci-dessus est la référence ; toute modification ultérieure doit être datée
et justifiée dans le protocole (traçabilité anti-biais).

## Composants

### 1. `biblio/modele/protocole_verdict_anisotropie.md` (pré-enregistration + runbook)
Contenu : la table de décision ci-dessus, le split d'essais, la commande exacte, et un
runbook « quand la donnée #11 propre arrive → déposer le .txt, recaler duree_chauffe/totale,
lancer `verdict_anisotropie.py`, coller la ligne de registre ». Mention explicite : barre
figée le 2026-08-10 avant l'acquisition propre.

### 2. `code/scripts/verdict_anisotropie.py` (wrapper « une commande »)
Assemble, sans nouvelle physique :
- **Calage** : importe `CalibrateurJoint`, `EssaiCalibre`, `table_comparaison` de
  `calibrer_joint.py` ; lance le calage `anisotrope=True` sur le split documenté.
- **Métriques** : held-out RMSE & |ΔTmax| moyens (via `table_comparaison` sur held-out) ;
  contraste M `new` via `diag_anisotropie.contraste_m(...)` au θ* trouvé ; régression
  par-TC de la famille bord (via `table_comparaison` sur la famille bord).
- **Décision** : appelle `evaluer_verdict(metriques, seuils)`.
- **Sortie** : ADOPTÉ/NON-ADOPTÉ, l'état de chaque porte, et la **ligne de registre
  `leviers_refutes.md` prête à coller** (datée, avec `(kx, ky)` retenu le cas échéant).

### 3. `evaluer_verdict(metriques, seuils) -> Verdict` (cœur testable — fonction pure)
Signature :
```python
@dataclass
class Verdict:
    adopte: bool
    portes: dict[str, bool]   # {"held_out_rmse": True, "held_out_dtmax": ..., "contraste_m": ..., "bord": ...}
    motif: str                # phrase résumant la/les porte(s) qui tranche(nt)

def evaluer_verdict(metriques: Metriques, seuils: Seuils) -> Verdict: ...
```
`Metriques` = dataclass des grandeurs déjà calculées (rmse_holdout_ref/new,
dtmax_holdout_ref/new, contraste_new, contraste_ref, {tc: (rmse_ref, rmse_new)} bord).
Aucune simulation : pure logique de seuils → déterministe.

## Séparation des responsabilités

- `evaluer_verdict` : décision pure, sans I/O ni simulation (unité, rapide).
- `verdict_anisotropie.py` (orchestration) : appelle le harnais, agrège les métriques,
  formate la sortie. Ne contient aucune règle de seuil en dur hors des constantes nommées.
- Harnais existant (`calibrer_joint.py`, `diag_anisotropie.py`) : inchangé, importé.

## Tests (TDD)

Unitaires sur `evaluer_verdict` (fonction pure, pas de simulation) :
1. 4 portes tenues → `adopte=True`.
2. Held-out RMSE insuffisant (new ≥ ref − 0,5) → `False`, motif porte 1.
3. Held-out ΔTmax régresse (new > ref + 2,0) → `False`, motif porte 2.
4. Contraste trop loin de 2,09 (ou > 2,6) → `False`, motif porte 3.
5. Un TC bord régresse (> +2,0 °C) → `False`, motif porte 4.

Nouveau fichier `tests/test_verdict_anisotropie.py`.

## Vérification

- `pytest tests/test_verdict_anisotropie.py -q` : 5 cas verts.
- `pytest -q` : suite complète non régressée.
- **Smoke-test optionnel** : lancer `verdict_anisotropie.py` end-to-end sur la donnée y20
  *actuelle* (imparfaite) pour prouver que le wrapper tourne de bout en bout — **sans**
  inscrire de verdict au registre (le verdict réel attend l'acquisition propre de #11).

## Hors périmètre

- Aucune inscription de verdict au registre aujourd'hui (données propres #11 requises).
- Pas de voie 3D pour la calibration (le 2D reste la référence documentée ; le prototype
  3D est câblé mais la calibration reste 2D, comme tout le harnais existant).
- Pas de modification du harnais `calibrer_joint.py`/`diag_anisotropie.py` (import seul).
