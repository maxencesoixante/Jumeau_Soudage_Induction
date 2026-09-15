# Y a-t-il un pas entre passes qui soude sans brûler ?

Généré le 2026-09-15. Étendue fixe (`x` = 15.9 → 105.9 mm, celle du procédé semi-statique réel), spot centré en largeur, 235 A, 20 s par passe. Seul le pas varie — donc le nombre de passes, donc l'énergie déposée.

![Balayage du pas](figures/fig_balayage_pas_mfc_reduit.png)

## Le pas le plus couvrant sans aucune dégradation

| configuration | pas | passes | soudé | dégradé |
|---|---|---|---|---|
| MFC réduit — hypothèse favorable (A) | 22.5 mm | 5 | 27.2 % | 0.0 % |
| MFC réduit — hypothèse corroborée (B) | 18.0 mm | 6 | 22.8 % | 0.0 % |
| MFC labo 55 mm | 30.0 mm | 4 | 7.5 % | 0.0 % |

## Le balayage complet

| pas (mm) | passes | MFC réduit — hypothèse favorable (A) — soudé / dégradé | MFC réduit — hypothèse corroborée (B) — soudé / dégradé | MFC labo 55 mm — soudé / dégradé |
|---|---|---|---|---|
| 45.0 | 3 | 3.5 % / 0.0 % | 1.7 % / 0.0 % | 4.5 % / 0.0 % |
| 30.0 | 4 | 8.0 % / 0.0 % | 3.3 % / 0.0 % | 7.5 % / 0.0 % |
| 22.5 | 5 | 27.2 % / 0.0 % | 9.2 % / 0.0 % | 14.7 % / 1.6 % |
| 18.0 | 6 | 43.2 % / 9.3 % | 22.8 % / 0.0 % | 27.6 % / 5.9 % |
| 15.0 | 7 | 37.2 % / 29.7 % | 34.5 % / 4.7 % | 37.3 % / 15.6 % |
| 12.9 | 8 | 32.9 % / 45.3 % | 43.6 % / 15.9 % | 41.8 % / 27.5 % |
| 11.2 | 9 | 25.6 % / 57.2 % | 41.3 % / 27.3 % | 33.6 % / 39.7 % |
| 10.0 | 10 | 13.3 % / 71.9 % | 33.4 % / 39.3 % | 18.0 % / 59.9 % |
| 9.0 | 11 | 10.1 % / 76.9 % | 18.3 % / 58.0 % | 16.5 % / 65.7 % |
| 8.2 | 12 | 8.9 % / 79.7 % | 16.3 % / 64.2 % | 15.1 % / 69.7 % |
| 7.5 | 13 | 7.6 % / 82.3 % | 15.6 % / 67.9 % | 14.5 % / 72.8 % |
| 6.9 | 14 | 6.9 % / 83.7 % | 14.8 % / 71.0 % | 13.0 % / 75.2 % |
| 6.4 | 15 | 6.5 % / 85.1 % | 13.9 % / 73.5 % | 10.7 % / 78.7 % |

## Réserves

- **Ce n'est pas une comparaison à énergie égale.** Resserrer le pas ajoute des passes : le pas le plus serré du tableau dépose plusieurs fois l'énergie du plus large.
- **Le critère de dégradation est conservateur.** Le seuil est appliqué à une interface calculée avec la config canonique (chaleur latente 130 J/g, sans plateau de fusion), qui surestime au-delà du point de fusion — 865 contre 508 °C sur le cycle 231 A. Un pas déclaré sans dégradation l'est donc à coup sûr ; un pas déclaré dégradant peut ne pas l'être.
- **Le résidu structurel du jumeau joue dans le sens conservateur** pour la couverture : le centre du modèle se remplit trop lentement, donc la couverture réelle devrait être un peu meilleure que celle calculée.
- Aucune des hypothèses de MFC réduit n'est de la physique établie ; c'est la campagne #55 qui dira laquelle décrit le concentrateur réel.

Reproduire : `.venv/bin/python code/scripts/gen/gen_balayage_pas_mfc_reduit.py`
