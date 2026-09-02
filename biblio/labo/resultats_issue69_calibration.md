# Issue #69 — Calibration jointe `bimodal_sigma_mm` × `decalage_x` : résultat

Objectif : caler conjointement les 2 paramètres sur les 3 runs plein-champ (150A/200A centrés + 150A bord
en held-out), en ajustant le profil longitudinal (largeur-moyenné, normalisé). Grille
`decalage_x ∈ [-12,0] mm` × `bimodal_sigma_mm ∈ [2,4] mm`, RMSE sommé sur les 2 centrés.

## Résultat : NÉGATIF (les 2 paramètres ne suffisent pas)

Optimum **au bord de grille** (`decalage_x=-2 mm`, `bimodal_sigma_mm=4 mm`, RMSE 0,32) → mauvais fit
(`figures/issue69/calibration_bimodal.png`). **Diagnostic** :

- **`bimodal_sigma_mm` marche** pour la PROFONDEUR du creux (validé séparément : σ≈3,3 mm → creux 16 %).
- **`decalage_x` est le mauvais outil.** La mesure est **asymétrique** : pic décalé ~10 mm à gauche
  (x≈50 vs 60) et **plus large côté x=0**, alors que le bord droit (x≈70) colle déjà au modèle centré.
  `decalage_x` étant une **translation**, décaler à gauche casse le bord droit → la grille se rabat sur
  dx≈-2 (quasi centré) + σ=4 (creux le plus plat) = compromis qui rate le creux ET l'asymétrie.

**Conclusion** : le résidu dominant est une **asymétrie de déposition** (la source s'étale vers x=0),
qu'aucun des deux paramètres ne capture. Held-out bord (RMSE 0,31) confirme.

## Causes possibles de l'asymétrie (à trancher AVANT de re-calibrer)

1. **Physique** : jambe du hairpin plus couplée que l'autre (coil/plaque non parallèle, une jambe plus
   proche), OU asymétrie du MFC. → demanderait un poids de pôle **asymétrique** (pas juste σ+dx).
2. **Mesure/visée** : gradient d'émissivité-angle si la plaque est légèrement inclinée (le run bord
   montrait un fort raccourci vertical → inclinaison plausible). → corriger les images (flat-field /
   angle) avant calibration.

## Acquis / prochaine étape

- Acquis : `bimodal_sigma_mm` (le flag livré) **reproduit le creux** — le mécanisme est bon. Valeur
  provisoire σ≈3,3 mm (dip). `decalage_x` seul **NE convient PAS** pour l'asymétrie.
- Suite : **déterminer si l'asymétrie est physique ou un artefact de visée** (mesurer l'inclinaison
  plaque/caméra ; vérifier en pixels bruts si l'asymétrie suit un gradient de bord d'image). Selon le
  verdict : soit corriger les images, soit ajouter un **poids de pôle asymétrique** au flag. PUIS
  seulement finaliser la calibration et ré-ouvrir k_plan/h_bord_x0.
