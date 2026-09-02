# Issue #69 — Flag source bimodale (`bimodal_sigma_mm`) : implémentation & validation

Correctif de la sous-bimodalité de la source (diagnostic : la chaîne ψ quasi-statique produit un
plateau ~plat, creux ~3 %, alors que la mesure plein-champ montre 2 pôles nets, creux thermique ~16 % ;
aucun paramètre physique — couplage/µr/fréquence — ne le reproduit, cf. `synthese_issue69.md`).

## Implémentation

`code/src/jumeau/em/source_joule.py` — `_bimodaliser_source(Q, grille, xc, entraxe, sigma_mm)` :
re-module la source en x par **deux gaussiennes** centrées en `xc ± entraxe/2` (jambes du hairpin,
`entraxe_jambes=12,35 mm`), largeur `sigma_mm`, **puissance conservée tranche z par tranche z**.
Paramètre `bimodal_sigma_mm` ajouté à `source_spot` **et** à `Essai` (défaut **0.0 = OFF, bit-à-bit**).

- Non-régression : `bimodal_sigma_mm=0` → source strictement inchangée (test dédié).
- Suite complète : **125 tests verts** (123 + 2 nouveaux).
- Facteur **EFFECTIF** (comme `lissage_sigma_mm`), à CALIBRER — pas une valeur physique dérivée.

## Validation (200 A centré, plaque libre)

`figures/issue69/valide_flag_bimodal.png` : `sigma` contrôle la profondeur du creux thermique.

| `bimodal_sigma_mm` | creux thermique |
|---|---|
| 0 (OFF) | 0 % (plateau) |
| 2,0 | 35 % |
| 2,5 | 27 % |
| 3,0 | 19 % |
| **mesure** | **16 %** |

→ **σ ≈ 3–3,3 mm** reproduit la profondeur mesurée. Le flag **recrée la double-bosse absente** du modèle.

## Reste

- **Asymétrie** mesurée (bosses 50/64, pic ~3 mm à gauche du centre) non capturée par le flag
  symétrique → c'est le **positionnement excentré du spot**, à traiter via `decalage_x` (séparé).
- **Calibration formelle** de `bimodal_sigma_mm` sur les 3 runs (multi-courant/position) à faire.
- Le flag est **phénoménologique** (impose la bimodalité sans re-dériver l'EM des 2 conducteurs) ; une
  version physique (skin/proximité dans la plaque) reste un chantier ouvert.

## Prochaine étape

Calibrer `bimodal_sigma_mm` (+ `decalage_x` pour l'asymétrie) conjointement sur les 3 runs plein-champ,
puis **ré-ouvrir k_plan / h_bord_x0** (qui étaient confondus par l'erreur de source, désormais corrigée).
