---
name: simuler-essai
description: Simule un essai unique et produit la carte de température 3D à l'interface + les courbes thermocouples simulées vs mesurées. À utiliser pour inspecter visuellement un scénario ou l'effet d'un paramètre.
---
# Simuler un essai (carte T + courbes TC)

Lance une simulation 3D d'un essai et écrit deux figures : la carte de température à l'interface de
soudure (au pic global) et la comparaison thermocouples simulés vs mesurés. Sert à *voir* un
scénario, pas à produire des métriques agrégées (pour ça → `valider-croise`).

## Quand l'utiliser
- Inspecter l'empreinte thermique d'un essai donné.
- Voir l'effet d'un `facteur_couplage` / `h_contact` / `h_bas` sur les courbes.
- Vérifier qualitativement un nouvel essai après l'avoir ajouté (`ajouter-essai`).

## Procédure
```bash
.venv/bin/python scripts/simuler_essai.py config/essais/<nom>.yaml \
    [--facteur 1.0] [--h-contact <Hc>] [--h-bas <Hb>] \
    [--nx 49 --ny 17 --nz 15] [--sortie resultats]
```
- Passer les **paramètres calibrés** (`--facteur/--h-contact/--h-bas`) pour un rendu réaliste ; sans eux, valeurs par défaut du YAML.
- Grille **fine par défaut** (49×17×15) ici, contrairement à la calibration/validation (grossière) — c'est un rendu, pas une boucle d'optimisation.
- Sorties dans `resultats/` : `<nom>_carte_interface.png`, `<nom>_courbes_tc.png`, + `T_max_sim` par TC imprimé.

## À lire sur les figures
- **Carte interface** : localisation et amplitude du point chaud ; la ligne Tf = 337 °C (PEKK) sur les courbes repère l'atteinte de la fusion.
- **Courbes TC** : mesuré (trait plein, α=0.4) vs simulé (tireté, épais), recalés au début de chauffe (`recaler_a_la_chauffe`). Si les mesures manquent, le script trace la simulation seule.
- **Grille de convergence** : ne pas conclure sur une valeur de pic sans avoir vérifié qu'elle ne bouge plus en raffinant (nx,ny,nz) — déléguer les tests de convergence à `simulation-verification-engineer`.

## Notes
- `matplotlib` est en backend `Agg` (pas d'affichage interactif, écriture fichier directe).
- Un essai à plusieurs empreintes (Séries A/B, 4 spots séquentiels) montre 4 vagues de chauffe ; vérifier que le découpage temporel des `spots` du YAML colle aux vagues réelles des courbes.
