# Diagnostic conduction latérale au refroidissement — cycle 231 A (issue #68)

Après réfutation du rayonnement de face, on teste si la chute rapide post-pic est de la **conduction latérale in-plane** sous-représentée : on rehausse `k_plan` **uniquement pendant les gaps** (chauffe = transport fusion normal), balayage `k_cool`. Script : `code/scripts/gen/gen_diag_conduction_laterale_231A.py`.

Pics mesurés : TC1=392, TC2=350, TC3=381, TC4=383, TC5=387 °C. Rappel : `k_cool=3` = config actuelle (k_plan retombe à 3 sous Tf).

| k_cool | pic TC4 | pic TC5 | RMSE TC2 | RMSE TC3 | RMSE TC4 | RMSE TC5 | déficit refroid. haute T |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | 462 | 514 | 67.9 | 77.4 | 69.7 | 62.1 | 1.73 |
| 10 | 459 | 511 | 57.4 | 68.7 | 73.5 | 82.7 | 1.97 |
| 30 | 456 | 508 | 50.4 | 58.7 | 73.9 | 96.6 | 1.61 |
| 100 | 453 | 505 | 53.8 | 54.0 | 75.5 | 102.7 | 1.01 |

## Lecture

- **Mécanisme CONFIRMÉ** : le déficit de refroidissement à haute T se recale bien (1.73× à k_cool=3 → 1.01× à k_cool=100), et la forme de la chute de TC4 (P4) épouse la mesure à k_cool élevé (cf. figure, panneau A). La chute rapide post-pic EST donc bien un phénomène de **conduction latérale in-plane** — que la config actuelle (`k_plan`=3 sous Tf) sous-représente.
- **MAIS le fix naïf échoue en aval** : RMSE TC5 se **dégrade** 62.1 → 102.7 (et TC4 69.7 → 75.5). Raison physique : la conduction latérale **REDISTRIBUE** la chaleur (elle refroidit le point chaud en la poussant vers l'aval → préchauffe TC5/le bord), elle ne l'**ÉVACUE** pas. Le vrai stratifié, lui, cool vers des T basses partout = la chaleur est bien PERDUE.
- **Mi-plaque aidée, aval pénalisé** : RMSE TC2 67.9→53.8, TC3 77.4→54.0 (améliorés) vs TC5 dégradé — signature d'une redistribution vers l'aval. Les pics restent quasi inchangés (TC4 462→453, TC5 514→505).

## Verdict : mécanisme identifié = le résidu structurel k_plan CONNU, vu sous l'angle du refroidissement

Le déficit de refroidissement rapide est une **nouvelle manifestation du résidu structurel déjà documenté** : `k_plan` in-plane trop faible (config 3.0 vs calibration ≈7,5–8,5). Le diagnostic **confirme** la conduction latérale comme mécanisme, mais montre qu'un `k_plan` **scalaire** relevé ne peut pas refroidir localement sans **sur-étaler vers l'aval** — exactement pourquoi la recalibration de k_plan est un held-out NO-GO récurrent (#65, [[residu-unifie-etalement-in-plane]]). Ni perte de surface (rayonnement de face, réfuté) ni conduction scalaire ne suffisent isolément. **Seul levier physique restant** cohérent avec tous les indices : un `k_plan` **anisotrope** (kx≠ky) — évacuer latéralement dans le sens utile sans sur-préchauffer l'aval — ou **acter la limite structurelle**. C'est la porte déjà identifiée comme dernière au niveau projet.
