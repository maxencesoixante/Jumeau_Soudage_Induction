# `Serie B/` — essai basse consigne 250 A / 25 N (2026-07-08)

Trois fichiers, dont deux dérivent du troisième.

| Fichier | Rôle |
|---|---|
| `serieB_brut_250A_25N_2026-07-08.txt` | **Source d'acquisition**, telle que sortie du banc. |
| `serieB_B-1_250A_25N_2026-07-08.csv` | B-1, extrait nettoyé de la source (lignes 1–1150). |
| `serieB_B-2_250A_25N_360C_2026-07-08.csv` | B-2, extrait de la source (lignes 1151–2386). C'est ce fichier que lit `config/essais/serieB_B-2.yaml`. |

## Ce que la source garde et que les CSV ont perdu

Les deux CSV sont les exploitables : décimale point, virgule séparatrice, temps remis à
zéro au début de chaque essai. Ils ne remplacent pas la source sur deux points.

**L'horodatage absolu.** La source court de 3954 s à 17186 s pour 2387 points ; les trous
d'acquisition qui expliquent l'écart disparaissent une fois le temps réindexé de 0 à N−1
dans les CSV.

**Les points TC4 aberrants de B-1.** Vingt-six valeurs ont été écrasées au nettoyage : une
à la ligne 888 (954,7 °C → 156,1 °C) et les vingt-cinq dernières, lignes 1125 à 1149, où
TC4 décroche puis sature à 2295 °C, toutes ramenées à 298,874 °C. B-2, lui, reprend la
source sans aucune retouche (écart maximal nul sur les cinq voies).

Le décrochage à 2295 °C est la butée haute de la chaîne d'acquisition, pas une mesure :
c'est la signature d'un thermocouple qui lâche en fin d'essai. On le garde ici parce qu'il
date la défaillance de TC4, information qu'aucun des deux CSV ne porte plus.

Format de la source : texte tab-séparé, décimale virgule, colonnes `Time (s)`, `TC1 (C)`…`TC5 (C)`.
