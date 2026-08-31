# Ablation du modèle de fusion — cycle 231 A (issue #68, Axe 1)

Ablation 2×2 (L_f × transport `k_plan(T>Tf)`) + balayage L_f, confrontée au réel 231 A (held-out, aucun recalage). Fenêtres de passe pilotées aux dwells mesurés (identique à `gen_valider_fusion_231A.py`). Script : `code/scripts/gen/gen_ablation_fusion_231A.py`.

Pics mesurés : TC1=392 °C, TC2=350 °C, TC3=381 °C, TC4=383 °C, TC5=387 °C.

## Ablation 2×2

| config | L_f (J/g) | transport | RMSE TC2 | RMSE TC3 | RMSE TC4 | RMSE TC5 | pic TC4 (écart) | pic TC5 (écart) | point chaud max |
|---|---:|:---:|---:|---:|---:|---:|---:|---:|---:|
| ① canonique | 130 | OFF | 67.3 | 72.1 | 66.8 | 72.6 | 433 (+50) | 581 (+194) | 866 |
| ② fusion seule | 40 | OFF | 69.7 | 71.7 | 67.5 | 76.8 | 463 (+79) | 597 (+210) | 884 |
| ③ transport seul | 130 | ON | 70.0 | 83.5 | 70.4 | 54.0 | 447 (+63) | 499 (+112) | 497 |
| ④ complet | 40 | ON | 67.2 | 82.8 | 67.7 | 67.5 | 462 (+78) | 513 (+126) | 512 |

RMSE moyen intérieur (TC2/TC3) et global (TC1-5) :

| config | RMSE moy TC2/TC3 | RMSE moy global (TC1-5) |
|---|---:|---:|
| ① canonique | 69.7 | 69.8 |
| ② fusion seule | 70.7 | 71.1 |
| ③ transport seul | 76.7 | 67.5 |
| ④ complet | 75.0 | 69.4 |

## Balayage L_f (transport ON, K_HOT=100)

| L_f (J/g) | RMSE TC2 | RMSE TC3 | RMSE TC4 | RMSE TC5 | pic TC4 (écart) | pic TC5 (écart) | point chaud max |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 67.7 | 81.5 | 70.0 | 78.3 | 468 (+85) | 520 (+132) | 518 |
| 20 | 67.0 | 82.1 | 68.2 | 73.4 | 465 (+82) | 516 (+129) | 515 |
| 40 | 67.2 | 82.8 | 67.7 | 67.5 | 462 (+78) | 513 (+126) | 512 |
| 130 | 70.0 | 83.5 | 70.4 | 54.0 | 447 (+63) | 499 (+112) | 497 |

## Lecture

- **Point chaud / plateau : porté par le transport, pas par L_f.** L_f seul (② vs ①) laisse le point chaud quasi inchangé, même légèrement plus haut (866 -> 884 °C, Δ=+18) — L_f seul ne plafonne donc pas le point chaud. Le transport seul (③ vs ①), lui, le fait chuter de 866 à 497 °C (Δ=-369), soit l'essentiel de la baisse obtenue par le modèle complet (④ : 512 °C, Δ=-354). Le RMSE global suit la même hiérarchie : 69.8 (①) -> 71.1 (②, +1.4) -> 67.5 (③, -2.3) -> 69.4 (④).

- **TC4 (intérieur, x=90) quasi insensible aux deux leviers ; TC5 (bord, x=120) répond fortement au transport.** Le pic TC4 varie peu et dans le mauvais sens avec L_f seul (433 -> 463 °C, Δ=+29) comme avec le transport seul (433 -> 447 °C, Δ=+13) ; il reste surestimé de +50 à +79 °C dans toutes les configs, avec un RMSE quasi constant (66.8-70.4 °C) — ni L_f ni le transport ne corrigent ce résidu. Le pic TC5, au contraire, chute nettement sous transport seul (581 -> 499 °C, Δ=-82, RMSE 72.6 -> 54.0 °C) alors que L_f seul l'aggrave légèrement (581 -> 597 °C, Δ=+16) ; le modèle complet (④) reste au-dessus du plateau mesuré sur les deux capteurs (462 / 513 °C vs mesuré 383 / 387 °C). Ce plafonnement de TC5 par le transport se paie d'une dégradation de TC3 (intérieur, passe 2) : RMSE 72.1 -> 83.5 °C avec le transport seul.

- **Balayage L_f (transport ON) : effet de réglage fin, pas de bascule qualitative.** Point chaud et pics TC4/TC5 varient de façon monotone avec L_f croissant (point chaud : 518 -> 515 -> 512 -> 497 °C pour L_f=0/20/40/130 J/g), sur une plage modeste (< 21 °C) comparée à l'écart transport ON/OFF (369 °C). Le RMSE TC5 s'améliore avec L_f croissant (78.3 -> 54.0 °C) tandis que le RMSE TC3 se dégrade légèrement (81.5 -> 83.5 °C) — L_f, une fois le transport actif, ajuste le niveau plutôt qu'il ne change le comportement qualitatif.

- Recoupement : ① canonique et ④ complet ci-dessus doivent reproduire les pics/point chaud imprimés par `gen_valider_fusion_231A.py` (canon vs fusion) — vérifié dans la sortie console du script.
