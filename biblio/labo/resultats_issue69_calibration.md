# Issue #69 — Calibration `bimodal_sigma_mm` (après dé-tilt)

## Dé-tilt (l'asymétrie était un tilt d'image, PAS physique — confirmé terrain)

Le pic mesuré décalé/asymétrique venait d'une **inclinaison d'image** (caméra ⟂ plaque OK, mais tilt au
niveau de l'image). Correction : **symétrisation** du profil longitudinal autour de son centre (la
déposition est physiquement symétrique, bobine centrée) → retire l'asymétrie sans imposer la réponse.
Résultat : gauche/droite se superposent, **centres cohérents ~58 mm** (150 A et 200 A).
`decalage_x` n'est donc PAS requis (l'asymétrie n'était pas une translation physique).
Figure `figures/issue69/detilt_calibration.png`.

## Calibration de `bimodal_sigma_mm` (sur le CREUX central, |x−centre|≤10 mm)

Minimum intérieur net : **`bimodal_sigma_mm ≈ 2,5 mm`**.

| run | creux mesuré | modèle σ=2,5 |
|---|---|---|
| 200 A centré (13 s) | 26 % | 27 % ✅ |
| 150 A centré (35 s) | 19 % | 7 % ⚠️ (sous-reproduit) |

→ σ≈2,5 mm reproduit bien le 200 A ; **sous-reproduit le 150 A** : à 35 s le modèle diffuse trop le
creux (un seul σ ne cale pas les 2 temps de chauffe) = **résidu de vitesse de diffusion (k_plan)**.

## Résidu SÉPARÉ : largeur

Après dé-tilt, le profil mesuré reste **plus large** que le modèle (à tout σ) → c'est la question
**k_plan / largeur de source**, distincte du creux, que le flag bimodal ne traite pas.

## Bilan

- `bimodal_sigma_mm ≈ 2,5 mm` = valeur calibrée (creux), défaut du flag reste OFF.
- `decalage_x` non requis (asymétrie = tilt, retiré par symétrisation).
- Deux résidus restants, tous deux liés à la **vitesse/largeur de diffusion = k_plan** : (1) creux
  150 A sous-reproduit, (2) largeur globale. → ré-ouvrir k_plan MAINTENANT que source (bimodalité) et
  tilt sont traités.
