# Diagnostic du refroidissement inter-passes — cycle 231 A (issue #68, Suite #1)

Question : le déficit de refroidissement du modèle (fusion, config ④) est-il concentré à HAUTE température (signe d'une perte radiative de FACE manquante : le solveur 2D n'applique le rayonnement T⁴ qu'aux chants, pas aux grandes faces haut/bas) ou UNIFORME en T (accélérer = perte globale = territoire held-out NO-GO de #65) ?

Métrique décisive **intra-segment** (pas de biais de sur-accumulation) : sur chaque refroidissement d'un TC intérieur depuis SON pic (T0>250 °C), on compare la vitesse de refroidissement mesuré/modèle à HAUTE T (premières 15 s du gap) vs à BASSE T (bande 150-230 °C). `déficit>1` = modèle trop lent.

Script : `code/scripts/gen/gen_diag_refroidissement_231A.py`. Pics modèle (contrôle emballement connu ≈462/513) : TC1=419, TC2=409, TC3=412, TC4=462, TC5=513 °C.

## Segments propres (refroidissement depuis le pic)

| TC | passe | T0 (°C) | tau_meas (s) | tau_mod (s) | déficit HAUTE T | déficit BASSE T |
|---|:---:|---:|---:|---:|---:|---:|
| TC2 | 1 | 271 | 34.6 | 139.7 | 1.25 | 0.98 |
| TC2 | 2 | 349 | 36.9 | 117.0 | 1.52 | 0.60 |
| TC4 | 4 | 373 | 33.3 | 71.6 | 1.44 | 0.67 |
| TC3 | 3 | 380 | 40.9 | 125.2 | 1.61 | 0.63 |
| TC3 | 2 | 381 | 35.3 | 104.5 | 1.76 | 0.81 |
| TC4 | 3 | 383 | 35.6 | 110.2 | 1.89 | 0.81 |

**Déficit de vitesse médian : HAUTE T = 1.57× , BASSE T = 0.74×.** (tau_mod/tau_meas médian sur segment entier = 3.08×.)

Note méthodo : les segments à T0<250 °C sont ÉCARTÉS — le mesuré y est déjà froid alors que le modèle, sur-accumulé, y est encore chaud (comparaison biaisée). Les tau élevés (modèle 2-3× trop lent sur segment entier) confirment un déficit de refroidissement bien supérieur au « ~10 % » folklorique.

## Verdict : **DÉFICIT CONCENTRÉ À HAUTE T → GO (piste rayonnement de face)**

Le déficit de refroidissement est **concentré à haute T** (médian 1.57× à haute T contre 0.74× à basse T) : le modèle rate surtout la chute rapide juste après le pic. C'est la signature d'une **perte à haute T manquante** → **piste rayonnement de FACE (T⁴) à implémenter puis valider en held-out** (exp7/exp9). Ce levier n'agissant qu'à haute T, il n'a pas la pathologie du h_bas global de #65 (qui sur-refroidit les zones froides). Prochaine étape = implémenter le terme radiatif de face (émissivité·σ·(T⁴−T_amb⁴) sur faces haut/bas) en variante, et vérifier : (a) rapproche la cinétique, (b) abaisse TC4/TC5, (c) held-out exp7/exp9 neutre.
