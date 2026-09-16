# 7 passes au MFC réduit, pas de 15 mm

Généré le 2026-09-16. Séquence réelle du procédé : 7 dwells au pas de 15 mm (`x` = 15.9 → 105.9 mm), spot centré en largeur (`y` = 20 mm), 235 A, 20 s par passe, chaleur résiduelle incluse.

⚠️ **Hypothèse la plus favorable, pas la plus crédible.** Le calcul est fait dans la famille « le flux se reconcentre » — la seule des quatre où le MFC réduit produit un point chaud déplaçable, donc la seule qui vaille d'être regardée passe par passe. Mais c'est **l'intrus** des trois familles (cf. `prediction_mfc_familles.md`) : ce qui suit est une **borne optimiste**, pas une prédiction.

![Séquence de passes](figures/fig_sequence_passes_mfc_reduit_pas15mm.png)

| après | soudé | dégradé | T max (°C) |
|---|---|---|---|
| 1 passe | 1.2 % | 0.0 % | 345.1 |
| 3 passes | 20.8 % | 2.0 % | 524.5 |
| 5 passes | 30.5 % | 13.7 % | 554.8 |
| 7 passes | 43.0 % | 23.9 % | 559.2 |

À séquence identique, le **MFC labo 55 mm** donne 43.9 % soudé / 9.1 % dégradé, et le MFC réduit sous l'**hypothèse corroborée** 39.2 % / 0.0 %.

La dégradation est jugée en **temps × température** (`jumeau.thermique.dose_degradation`), pas au seuil de pic.

Reproduire : `.venv/bin/python code/scripts/gen/gen_sequence_4passes_mfc_reduit.py --pas-mm 15`
