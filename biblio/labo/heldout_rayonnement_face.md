# Held-out du rayonnement de face — exp7/exp9 (issue #68, critère d'adoption)

Critère d'adoption du flag `SolveurThermique2D(emissivite_face=)` : held-out **neutre ou meilleur** sur les 10 essais formels exp7/exp9 (modèle 2D, `facteur_couplage=6.0123` canonique, **aucun recalage**). Script : `code/scripts/gen/gen_heldout_rayonnement_face.py`.

| essai | RMSE ε=0.0 (OFF) | RMSE ε=0.6 | RMSE ε=0.9 | Δ (0.9−OFF) |
|---|---:|---:|---:|---:|
| exp7_150A | 25.4 | 25.3 | 25.2 | -0.3 |
| exp7_176A | 24.4 | 24.3 | 24.3 | -0.1 |
| exp7_200A | 21.8 | 21.8 | 21.8 | -0.1 |
| exp7_225A | 21.5 | 21.5 | 21.4 | -0.0 |
| exp7_250A | 22.6 | 22.5 | 22.5 | -0.0 |
| exp9_175A_monospot | 11.3 | 11.4 | 11.4 | +0.1 |
| exp9_200A_monospot | 12.1 | 12.2 | 12.2 | +0.1 |
| exp9_200A_y20_monospot | 17.7 | 17.5 | 17.5 | -0.2 |
| exp9_226A_monospot | 7.8 | 7.8 | 7.8 | -0.0 |
| exp9_250A_monospot | 10.1 | 10.2 | 10.2 | +0.1 |
| **MOYENNE** | **17.48** | **17.44** | **17.42** | **-0.05** |

## Verdict : ADOPTABLE (held-out neutre/meilleur)

RMSE moyen held-out : 17.48 (OFF) → 17.42 (ε=0.9), Δ = **-0.05 °C**. Le rayonnement de face est **neutre/positif en held-out** : ajout physique propre (défaut OFF bit-à-bit) adoptable comme amélioration mineure indépendante — décision d'activation par défaut à trancher (garder OFF par prudence, ou passer un défaut > 0 documenté).
