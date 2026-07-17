---
name: ajouter-essai
description: Intègre une nouvelle campagne d'essai (fichier de mesures + YAML config/essais/) dans le jumeau, avec le bon schéma de spots et thermocouples, puis le simule/valide. À utiliser quand de nouvelles données thermocouples arrivent.
---
# Ajouter un nouvel essai au jumeau

Onboarde une campagne expérimentale : place le fichier de mesures, écrit son YAML d'essai avec le
schéma exact attendu par `Essai`, puis lance une simulation de contrôle. Encode les pièges de
positionnement TC et de découpage temporel des empreintes.

## Étapes
1. **Déposer le fichier de mesures** dans `data/` (CSV corrigé ou TXT LabVIEW). Le chargeur
   auto-détecte séparateur (tab/virgule) et décimale, remet le temps à zéro, et interpole les
   aberrants (> `seuil_aberrant`, défaut 400 °C : un TC débranché lit ~2295 °C ; < −20 °C aussi).
2. **Créer `config/essais/<nom>.yaml`** avec ce schéma (voir `chauffe_250A_3TC.yaml` et `serieA_A-1.yaml`) :
   ```yaml
   nom: <nom>
   fichier_mesures: data/<fichier>.csv
   courant: 250.0            # A (consigne créneau)
   duree_chauffe: 30.0       # s (durée de chauffe active)
   duree_totale: 300.0       # s simulés (>= couverture du fichier)
   spots:                    # une empreinte, OU plusieurs (Séries A/B = 4 spots séquentiels)
     - {centre_x: 0.060, t_debut: 0.0, t_fin: 30.0}
   thermocouples:
     TC1: {x: 0.060, y: 0.020, z: surface}      # z ∈ {surface, interface, opposee}
     TC2: {x: 0.060, y: 0.020, z: interface}
   tc_valides: [TC1, TC2]    # seulement les voies branchées/fiables
   ```
3. **Découpage temporel des spots** : pour un essai multi-empreintes, caler les fenêtres `t_debut/t_fin` sur les vagues de chauffe réelles vues dans les courbes TC (≈350 s/spot en A/B, à ajuster), pas sur une division théorique.
4. **Vérifier par simulation** :
   ```bash
   .venv/bin/python scripts/simuler_essai.py config/essais/<nom>.yaml --facteur <F>
   ```
   Comparer les courbes simulées/mesurées et la carte interface.

## Pièges à ne pas rater
- **`z` symbolique** : `surface` (côté bobine), `interface` (soudure, tissu PW), `opposee` (face opposée). Respecter la convention.
- **Affectation TC↔position variable par essai** (constat 2026-07-12) : la voie du pic change d'un essai à l'autre. Tant que l'affectation n'est pas confirmée au cahier de labo, ne mettre dans `tc_valides` que des voies dont la position est sûre, et réserver l'essai à la validation **qualitative** (cf. `valider-croise`).
- **`tc_valides` ⊂ voies fiables** : exclure les TC débranchés ou majoritairement interpolés — ils ne sont pas des voies de validation.
- **`duree_totale`** doit couvrir la durée du fichier (ex. CSV 1423 pts à 1 Hz → ~1420 s).

## Ensuite
Ajouter `<nom>` à la liste `--essais` de `valider-croise`, et déléguer les questions de nettoyage/
bruit capteur à l'agent `validation-data-engineer`.
