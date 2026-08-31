# Test du rayonnement de face — cycle 231 A (issue #68, Suite #1, étape GO)

Nouveau paramètre `SolveurThermique2D(emissivite_face=)` (défaut 0.0 = OFF, bit-à-bit ; 123 tests verts) : rayonnement `ε·σ·(T_amb⁴−T⁴)` [W/m²] sur la face haut EXPOSÉE (hors MFC), qui n'avait sinon aucune perte. Cycle 231 A, modèle de fusion, dwells réels. Held-out exp7/exp9 = étape d'adoption suivante. Script : `code/scripts/gen/gen_test_rayonnement_face_231A.py`.

Pics mesurés : TC1=392, TC2=350, TC3=381, TC4=383, TC5=387 °C.

| emissivite_face | pic TC4 | pic TC5 | RMSE TC2 | RMSE TC3 | RMSE TC4 | RMSE TC5 | déficit refroid. haute T |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.0 | 462 | 513 | 67.2 | 82.8 | 67.7 | 67.5 | 1.57 |
| 0.3 | 456 | 509 | 63.8 | 76.3 | 63.0 | 60.6 | 1.57 |
| 0.6 | 452 | 505 | 61.7 | 70.3 | 58.8 | 55.3 | 1.58 |
| 0.9 | 448 | 502 | 60.6 | 64.6 | 55.2 | 51.0 | 1.59 |

## Lecture (critères GO)

- **(a) Cinétique — NON atteint.** Déficit de refroidissement à haute T 1.57× (baseline) -> 1.59× (ε=0.9) : **inchangé**. Exposer la face pendant le gap (MFC avancé) ne le corrige pas non plus (1.59×). La chute rapide juste après le pic n'est donc PAS due à une perte radiative de face manquante — cause probable = conduction latérale pendant le refroidissement (autre piste).
- **(b) Pics emballés — amélioration modeste.** TC4 462->448 °C, TC5 513->502 °C (mesuré 383/387) : baisse réelle mais partielle.
- **(c) Intérieurs — non cassés (améliorés).** RMSE TC2 67.2->60.6, TC3 82.8->64.6, TC4 67.7->55.2, TC5 67.5->51.0 : le RMSE de cycle BAISSE partout.

## Verdict : amélioration NETTE mais PARTIELLE — pas le remède à l'accumulation

Le rayonnement de face est un ajout physique **net-positif** (RMSE de cycle en baisse sur tous les TC, sans casser les intérieurs, pics emballés en légère baisse) et **propre** (défaut OFF, bit-à-bit, 123 tests verts). MAIS il **ne recale pas la cinétique de refroidissement rapide** (déficit haute T inchangé), y compris en exposant la face pendant l'avance. **L'attribution du diagnostic (déficit haute T = rayonnement de face manquant) n'est donc PAS confirmée** : le déficit haute T vient d'ailleurs (piste = conduction latérale / transport pendant le refroidissement). Le rayonnement de face reste un candidat mineur À VALIDER en held-out exp7/exp9 (seul critère d'adoption) ; la cause de l'accumulation TC4/TC5 reste ouverte.
