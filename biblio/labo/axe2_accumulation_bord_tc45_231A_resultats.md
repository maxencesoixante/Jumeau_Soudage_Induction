# Décorrélation accumulation vs artefact de bord x — TC4/TC5, cycle 231 A (issue #68, Axe 2)

Plan 2×2 sur le cycle complet (4 passes, dwells RÉELS, modèle de fusion : L_f=40 J/g physique + transport `k_plan(T>Tf)`), pour décorréler deux causes candidates de l'emballement de TC4 (x=90 mm, intérieur) et TC5 (x=120 mm, bord) au-dessus du plateau mesuré : (A) l'accumulation de chaleur passe-à-passe (warm-start du champ 2D), (B) l'artefact de source au bord x (`lambda_bord_x_mm`). Script : `code/scripts/gen/gen_axe2_accumulation_bord_tc45_231A.py`.

Pics mesurés : TC1=392 °C, TC2=350 °C, TC3=381 °C, TC4=383 °C, TC5=387 °C.

## Plan 2×2

| config | accumulation | bord x | RMSE TC2 | RMSE TC3 | RMSE TC4 | RMSE TC5 | pic TC4 (écart) | pic TC5 (écart) | point chaud max |
|---|:---:|:---:|---:|---:|---:|---:|---:|---:|---:|
| ① accum ON / bord ON | ON | ON | 67.2 | 82.8 | 67.7 | 67.5 | 462 (+78) | 513 (+126) | 512 |
| ② accum OFF / bord ON | OFF (reset) | ON | 92.4 | 63.2 | 61.1 | 41.6 | 428 (+45) | 482 (+95) | 480 |
| ③ accum ON / bord OFF | ON | OFF | 66.3 | 81.4 | 67.1 | 66.8 | 458 (+75) | 511 (+124) | 508 |
| ④ accum OFF / bord OFF | OFF (reset) | OFF | 91.8 | 63.0 | 61.9 | 42.1 | 425 (+41) | 480 (+93) | 476 |

Recoupement : ① reproduit-il l'emballement connu (TC4≈460, TC5≈510 °C) ? pic TC4=462, pic TC5=513 -> **OK**.

## Décomposition des pics (°C)

Δ = pic(config ①) − pic(config comparée) : positif si couper le levier fait BAISSER le pic. TC1/TC2/TC3 = témoins intérieurs (n'excèdent pas le plateau mesuré, référence de bruit/échelle).

| TC | Δ accumulation (①−②) | Δ bord x (①−③) | Δ les deux (①−④) |
|---|---:|---:|---:|
| TC1 | +0.0 | +0.9 | +0.9 |
| TC2 | +11.8 | +0.3 | +11.8 |
| TC3 | +9.8 | +0.2 | +9.8 |
| TC4 | +33.6 | +3.8 | +36.9 |
| TC5 | +31.7 | +2.3 | +33.6 |

Ratio |Δaccumulation| / |Δbord| : TC4 = 8.9×, TC5 = 13.7×.

## Lecture décisive

- **Les deux capteurs répondent aux DEUX leviers, mais dans des proportions très inégales et quasi identiques entre TC4 et TC5.** Pic TC4 : ①=462 °C, ②(accum OFF)=428 °C (Δaccum=+33.6 °C), ③(bord OFF)=458 °C (Δbord=+3.8 °C), ④(les deux OFF)=425 °C (Δ=+36.9 °C). Pic TC5 : ①=513 °C, ②=482 °C (Δaccum=+31.7 °C), ③=511 °C (Δbord=+2.3 °C), ④=480 °C (Δ=+33.6 °C).

- **L'accumulation passe-à-passe domine très largement les deux capteurs** (Δaccum TC4=+33.6 °C, TC5=+31.7 °C — de l'ordre de 9× et 14× plus grand que l'effet du bord sur le même capteur). Couper l'accumulation seule (②) ramène déjà le pic TC4 de 462 à 428 °C et le pic TC5 de 513 à 482 °C, réduisant l'écart au mesuré d'environ un tiers sur les deux capteurs sans annuler le dépassement.

- **L'artefact de source au bord x est réel mais MINEUR sur TC4/TC5 dans cette configuration** (Δbord TC4=+3.8 °C, TC5=+2.3 °C, contre ~0.2-0.9 °C sur les témoins intérieurs TC1=+0.9/TC2=+0.3/TC3=+0.2 °C) — vérifié non-bug : la correction ne modifie que la puissance des spots proches des bords du domaine (spot 1 x=15,9 mm et spot 4 x=105,9 mm, +1.0 %/-1.5 % de puissance totale ; spots 2/3 quasi inchangés), donc n'affecte TC4/TC5 que marginalement en amplitude de pic dans ce cycle piloté aux dwells réels.

- **Témoins intérieurs TC1/TC2/TC3 (n'excèdent pas le plateau mesuré) :** Δ accumulation TC1=+0.0/TC2=+11.8/TC3=+9.8 °C, Δ bord TC1=+0.9/TC2=+0.3/TC3=+0.2 °C — l'accumulation bouge aussi TC2/TC3 (+12/+10 °C) mais sans les faire déborder du plateau mesuré (ils y sont déjà, contrairement à TC4/TC5), donc ce n'est pas un artefact spécifique à TC4/TC5 — c'est un biais générique du cycle qui devient visible/problématique seulement là où le modèle est déjà en surchauffe (TC4/TC5).

- **Conclusion : TC4 et TC5 partagent la MÊME cause dominante — l'accumulation passe-à-passe — et NON une cause distincte de bord.** L'hypothèse pré-enregistrée (TC4 = pur cumulatif ; TC5 = cumulatif + bord superposé) n'est PAS vérifiée par les chiffres : le bord contribue à TC5 (+2.3 °C) dans une proportion comparable — et du même ordre de grandeur que sur TC4 (+3.8 °C) — pas d'un effet « bord » qualitativement différent entre les deux positions. Couper les DEUX leviers (④) ne suffit pas non plus à ramener TC4/TC5 au plateau mesuré (④ : TC4=425 °C vs mesuré 383 °C, TC5=480 °C vs mesuré 387 °C) : un résidu structurel (~41/93 °C) subsiste au-delà des deux leviers testés ici, hors périmètre de cet axe.
