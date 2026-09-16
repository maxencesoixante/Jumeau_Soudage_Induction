# 4 passes au MFC réduit, pas de 30 mm

Généré le 2026-09-16. Séquence réelle du procédé : 4 dwells au pas de 30 mm (`x` = 15.9 → 105.9 mm), spot centré en largeur (`y` = 20 mm), 235 A, 20 s par passe, chaleur résiduelle incluse.

⚠️ **Hypothèse la plus favorable, pas la plus crédible.** Le calcul est fait dans la famille « le flux se reconcentre » — la seule des quatre où le MFC réduit produit un point chaud déplaçable, donc la seule qui vaille d'être regardée passe par passe. Mais c'est **l'intrus** des trois familles (cf. `prediction_mfc_familles.md`) : ce qui suit est une **borne optimiste**, pas une prédiction.

![Séquence de passes](figures/fig_sequence_4passes_mfc_reduit.png)

| après | soudé | dégradé | T max (°C) |
|---|---|---|---|
| 1 passe | 1.2 % | 0.0 % | 345.1 |
| 2 passes | 2.8 % | 0.0 % | 345.1 |
| 3 passes | 5.7 % | 0.0 % | 345.1 |
| 4 passes | 8.0 % | 0.0 % | 392.3 |

À séquence identique, le **MFC labo 55 mm** donne 7.5 % soudé / 0.0 % dégradé, et le MFC réduit sous l'**hypothèse corroborée** 3.3 % / 0.0 %.

La dégradation est jugée en **temps × température** (`jumeau.thermique.dose_degradation`), pas au seuil de pic.

Reproduire : `.venv/bin/python code/scripts/gen/gen_sequence_4passes_mfc_reduit.py`
