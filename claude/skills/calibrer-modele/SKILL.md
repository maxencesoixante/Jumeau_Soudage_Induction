---
name: calibrer-modele
description: Calibre les entrées incertaines du jumeau (facteur_couplage, h_contact, h_bas) par LHS+NLSQ contre UN essai mesuré, puis prépare la validation croisée. À utiliser pour caler le modèle sur un essai de référence avant toute prédiction.
---
# Calibrer le modèle sur un essai de référence

Cale les trois paramètres incertains du jumeau contre **un seul** essai mesuré, puis renvoie la
commande de validation croisée. Pipeline LHS (Latin Hypercube) → NLSQ (Gauss-Newton) pondéré par
le bruit capteur, porté du notebook 1D validé (Samanis 2026 §2.3).

## Quand l'utiliser
- Après un changement de physique/matériaux, pour recaler le modèle.
- Pour établir un jeu `[facteur_couplage, h_contact, h_bas]` de référence à valider ensuite.

## Procédure
1. **Activer le venv** puis lancer la calibration sur l'essai de référence (défaut : `chauffe_250A_3TC`, l'essai de chauffe simple spot avec gradient d'épaisseur — le plus propre) :
   ```bash
   .venv/bin/python scripts/calibrer.py --essai chauffe_250A_3TC --n-lhs 12
   ```
   Grille **grossière par défaut** (31×11×13) : chaque évaluation = une simulation 3D complète, donc on garde la grille légère pendant le fit.
2. Lire la sortie : paramètres calibrés, `Coût final`, `succès`. Le script imprime directement la commande `valider.py` à lancer ensuite.
3. **Passer à la validation croisée** avec ces paramètres via la skill `valider-croise` (ou la commande imprimée) — **SANS recalibrer**.

## Garde-fous (non négociables)
- **Calibrer sur UN essai, valider en aveugle sur les autres.** C'est tout l'argument de validité externe. Ne jamais ajuster contre un essai de validation.
- **Ne jamais calibrer la fréquence avec le facteur d'échelle.** Ils sont totalement corrélés (leçon black-box f_I/r_I). La fréquence est FIGÉE ; seul `facteur_couplage` porte l'échelle de la source. N'ajoute aucun paramètre à `Calibrateur.NOMS` sans argumenter son identifiabilité séparée.
- **Pondération par le bruit réel** σ = std(diff(mesure))/√2 (plancher 0,1 °C) — déjà dans le code, ne pas la remplacer par des poids unitaires.
- **Un fit qui bute sur une borne** (bornes défaut (0.05,5,2)–(30,500,300)) signale un modèle incomplet, pas un succès — le signaler.
- **Un fit non convergé n'est pas une calibration** : rapporter le message solveur.

## Aller plus loin
Pour l'analyse d'incertitude/identifiabilité (covariance (JᵀWJ)⁻¹, corrélations, sensibilité),
déléguer à l'agent `calibration-uq-specialist`.
