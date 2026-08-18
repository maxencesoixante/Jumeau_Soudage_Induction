---
name: valider-croise
description: Confronte le modèle calibré aux essais mesurés SANS recalibrage et interprète les métriques par thermocouple (RMSE, ΔT_max, taux de chauffe). À utiliser après calibrer-modele pour juger la validité externe du jumeau.
---
# Valider le modèle en croisé (sans recalibrage)

Lance la simulation sur une liste d'essais avec un jeu de paramètres **déjà calibré** et produit
un tableau de métriques par thermocouple. C'est l'étape qui teste la validité externe : le modèle
n'a le droit de voir aucun de ces essais pendant la calibration.

## Quand l'utiliser
- Juste après `calibrer-modele`, avec les `[facteur_couplage, h_contact, h_bas]` obtenus.
- Pour vérifier qu'un changement n'a pas dégradé l'accord sur l'ensemble des essais.

## Procédure
1. **Reprendre les paramètres calibrés** (sortie de `calibrer-modele`) et lancer :
   ```bash
   .venv/bin/python code/scripts/valider.py \
       --facteur <F> --h-contact <Hc> --h-bas <Hb> \
       --essais chauffe_250A_3TC serieA_A-1 serieA_A-3 serieB_B-2
   ```
   Grille défaut 31×11×13 (cohérente avec la calibration). Ne PAS retoucher les paramètres entre essais.
2. Lire, **par essai**, le tableau `rapport_essai` : `rmse`, `T_max_sim`, `T_max_mes`, `delta_T_max`, `taux_sim`, `taux_mes`, plus le RMSE moyen et l'écart T_max moyen.

## Interpréter les métriques
- **Regarder par TC, pas seulement la moyenne** : un bon RMSE moyen peut masquer une voie mal reproduite.
- **Comparer pics ET taux, pas seulement le RMSE** : `delta_T_max` sonde l'amplitude de la source ; `taux_de_chauffe` (pente au passage de 75 °C, métrique Grouve 2020) sonde l'inertie/pertes. Un modèle peut matcher le RMSE en ratant le pic.
- **Métriques calculées sur la grille temporelle de la mesure** (simulation interpolée dessus) — ne jamais sur-échantillonner la mesure.

## Piège majeur — affectation TC↔position variable (Séries A/B)
La voie du pic **change d'un essai à l'autre** (constat 2026-07-12 : TC1 en A-1, TC4 en A-2, TC2 en A-3,
TC5 en B-1, TC3 en B-2). Tant que l'affectation n'est pas tranchée au cahier de labo :
- utiliser **`chauffe_250A_3TC` comme essai quantitatif de référence** (positions TC confirmées) ;
- traiter les **Séries A/B en validation QUALITATIVE** (T max globale, formes des courbes) plutôt qu'en RMSE par voie, sous peine de comparer une voie simulée à un mauvais thermocouple.

## Si un essai de validation échoue
Ne pas élargir le fit. Diagnostiquer la physique via les agents `thermal-solver-engineer` /
`induction-em-engineer`, ou vérifier les données via `validation-data-engineer`.
