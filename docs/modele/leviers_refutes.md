# Registre des leviers réfutés (flags OFF par défaut)

**Décision (issue #9, 2026-08-04) : garder derrière flags, PAS supprimer.**

Ces leviers ont été prototypés, calibrés et **évalués en held-out**, puis **non adoptés**.
Ils sont conservés parce qu'ils constituent (a) le **registre reproductible des résultats
négatifs** — le cœur défendable du travail — et (b) des **capacités physiques réutilisables**
avec une nouvelle donnée. Tous sont **OFF par défaut**, avec chemin historique **bit-à-bit
inchangé** et **tests on/off** (non-régression). Ne PAS les réactiver sans **nouvelle
donnée/physique** ET recalibration de θ\*.

| Levier (flag) | Où | CLI | Verdict | Réf |
|---|---|---|---|---|
| **`thermostat_capteurs`** | `procede.py`, `identification/calibration.py` | `--thermostat-capteurs` | **REJETÉ définitif** (2026-08-03). Fit joint pleine famille **pire partout** (JOINT 31,6→42,2 ; held-out 30,0→41,2 ; dTmax held-out 39,7→98,4). Le gain B-2 tenait à un facteur propre à B-2, ne survit pas au partage inter-familles. | `journaux/resultats_calibration_joint_thermostat.log` ; mémoire `b2-thermostat-capteurs` ; issue #9 |
| **`k_plan_T` / `k_z_T`** | `materiaux.py`, `solveur3d/2d` | `--kT` | **Évalué, NON adopté** (2026-08-03). Améliore le fit joint (19,8→15,7) mais **held-out régresse** (16,5→17,2 ; sur-étale le pic source-dominé). **Acquis physique** : k_plan réel ≈ 7,5–8,5 W/m·K décroissant (≈3× config). Correction de *propriété*, pas correctif de résidu. | `journaux/resultats_calibration_joint_kT{,_hbasfige}.log` ; mémoire `kt-residu-structurel-piste` ; issues #4, #9 |
| **`k_plan_x` / `k_plan_y`** (anisotrope) | `materiaux.py`, `solveur2d` | `--anisotrope` | **Réfuté** (2026-07-31). Fit trouve kx≈7,4 mais **multimodal en ky** (2 optima opposés : l'un bat le RMSE en aggravant le M, l'autre rapproche le M en ratant le RMSE) → relocalise le conflit sans le résoudre. | `journaux/resultats_calibration_joint_anisotrope*.log` ; issue #3 |
| **`lambda_bord_mm`** | `procede.py`, `em/source_joule.py` | `--lambda-bord-mm` | **Réfuté** (2026-07-31). Adoucit le contraste M (3,15→~2,1 = mesuré) MAIS **non conservatif en puissance** → ne débloque aucun θ\* joint gagnant. La CL `ψ=0` correcte est **corroborée par eppy** (Grouve/Nagel fait pareil). | `verification_croisee_eppy.md` ; issue #3 |

## Autres flags OFF par défaut — statut distinct (NON réfutés)

- **`source_sigma_mm`** (`procede.py`) — prototype pour le centre-fill transitoire (résidu exp7) ;
  non adopté faute de recalibration, **pas réfuté**.
- **`champ_reaction`** (`procede.py`) — motif d'implémentation interne (pas le champ de réaction EM
  d'eppy) ; off par défaut.
- **`masque_source_mfc`** (`procede.py`) — masque la source à l'empreinte MFC ; option physique, off.
- **`interp_ctrl`** — **ADOPTÉ** (défaut True) ; l'ablation `False` est conservée pour comparaison.

## Comment rejouer un levier réfuté
Chaque flag s'active par CLI (colonne ci-dessus) ou config YAML. Exemple :
`python scripts/calibrer_joint.py --kT` (held-out) ; `python scripts/valider.py --thermostat-capteurs`.
Les logs d'origine sont dans `journaux/`.
