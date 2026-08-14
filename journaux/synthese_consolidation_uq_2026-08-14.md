# Consolidation θ* + UQ du modèle 2D avec toutes les données exp7/exp9 — 2026-08-14

## Objectif
Replier TOUTES les batteries disponibles (exp7 150/176/200/225/250 A, exp9 y=20 200 A,
exp9 y=0 monospot 175/200/226/250 A) dans la calibration jointe, quantifier l'incertitude
et tester l'indépendance de k_plan au courant. **Pas** de tentative de battre le résidu
structurel d'étalement in-plane (arc de réfutations déjà clos).

## Phase A — données branchées
5 nouveaux YAML : `exp7_176A`, `exp7_225A`, `exp9_175A/226A/250A_monospot` (timings
auto-détectés via `charger_mesures`+`recaler_a_la_chauffe`). Test `tests/test_essais_consolides.py`
(structure spatiale : spot central pour exp9, profil M symétrique pour exp7) → 10/10 verts,
suite complète 113 passed (aucune régression).

## Phase B — θ* consolidé + UQ (`calibrer_joint.py`, held-out = courants intermédiaires)
Fit : exp7 150/176/200/250 + exp9 y=20 200 + exp9 y=0 175/200/250 (8 essais).
Held-out : exp7_225A + exp9_226A_monospot.

| param | θ*_consolidé | ± IC | canonique |
|---|---|---|---|
| facteur_couplage | 6.552 | ±0.077 | 6.012 |
| h_bas_2d | 68.84 | ±1.74 | 37.42 |
| **k_plan** | **8.252** | **±0.086** | 3.0 |
| h_bord_x0 | 50.64 | ±9.3 | 250 |

Corrélations toutes |r|<0,95 (max facteur–h_bas = 0,81) → **identifiable**.

- RMSE fit : réf 17,1 → new 18,5 °C (le σ-weighting troque RMSE contre ΔT_max)
- **RMSE held-out : réf 13,8 → new 19,3 °C (régression nette)**

**VERDICT : NO-GO pour l'adoption** de θ*_consolidé en config (régresse le held-out) —
cohérent avec tout l'historique. θ* canonique **inchangé** dans `config/materiaux.yaml`.
L'acquis est l'**UQ** + la confirmation que le fit réclame k_plan ≈ 8 (≈2,7× la valeur
physique 3,0), signature du déficit structurel d'étalement in-plane.

Log complet : `journaux/resultats_calibration_joint_consolide_2026-08-14.log`.

## Phase C — k_plan(I) indépendant du courant
Sur exp9 y=0 monospot (4 courants), fit de k_plan SEUL (autres params figés à θ*_consolidé),
cible = **profil longitudinal normalisé au spot** (robuste au cutoff manuel).

| courant | k_plan ± σ |
|---|---|
| 175 A | 6,73 ± 1,61 |
| 200 A | 7,41 ± 2,18 |
| 226 A | 8,23 ± 2,50 |
| 250 A | 8,58 ± 2,32 |

**k_plan moyen (pondéré) = 7,50 ± 1,03** ; test de constance **χ²/ddl = 0,18** →
**COMPATIBLE avec un k_plan constant**. Léger trend montant non significatif.

Driver : `scripts/tester_kplan_courant.py` ; CSV : `journaux/resultats_kplan_courant_2026-08-14.csv` ;
figure : `docs/modele/figures/fig_kplan_courant.png` (script `scripts/gen_figure_kplan_courant.py`).

## Conclusion
1. **k_plan effectif ≈ 7,5 W·m⁻¹·K⁻¹, indépendant du courant** (nouvelle donnée quantifiée
   avec incertitude, jamais établie auparavant) — soit ≈2,5× la valeur physique de config (3,0).
2. La consolidation **ne fournit pas** de meilleur θ* adoptable (held-out régresse) → confirme
   une fois de plus que le résidu est **structurel** (k_plan scalaire trop lent hors-spot),
   pas un défaut de calage.
3. L'apport net de la session = **UQ** (bornes serrées, identifiabilité) + **k_plan(I) constant**,
   pas un changement de config.

## Phase E — Affinage : anisotropie kx≠ky sur données complètes (test décisif) → NO-GO
Motivé par une vérif croisée forte : le fit anisotrope de juillet donnait kx=7,515 ; la
mesure longitudinale indépendante d'aujourd'hui (exp9 y=0, 4 courants) donne kx≈7,50±1,03.
On relance donc `calibrer_joint.py --anisotrope` sur le dataset complet (8 essais,
held-out courants intermédiaires).

Résultat : facteur 6.49 / h_bas_2d 67.2 / **kx 8.17±0.08 / ky 11.35±1.33** / h_bord_x0 50.2.
- ky **rail contre sa borne haute (12)** → le fit veut *encore plus* de conduction transverse
  (non-physique), clampé.
- **Held-out RÉGRESSE : réf 13,8 → new 19,9 °C** ; RMSE global 16,5 → 19,4.

Conclusions :
1. Le « kx=7,5 / ky=2,0 physiquement plausible » de juillet était un **artefact du dataset
   mince** (un seul essai conduction). Sur données complètes, ky va à la borne HAUTE, pas à 2,0.
2. Tension structurelle irréconciliable : la famille M réclame ky↑ (remplir le creux du M),
   la famille conduction un k modéré. Un seul (kx,ky) ne satisfait pas les deux.
3. kx≈8 reste cohérent avec la mesure longitudinale ; c'est **ky qui est non-physique/non
   identifiable**, pas kx.

**VERDICT : anisotropie NO-GO sur la meilleure donnée.** Dernier levier de forme ouvert clos.
La limite d'étalement in-plane est confirmée non-résoluble par les leviers paramétriques
(recalage isotrope, anisotropie, k(T), R_c, forme de source — tous NO-GO). Log :
`journaux/resultats_calibration_joint_anisotrope_consolide_2026-08-14.log`.
