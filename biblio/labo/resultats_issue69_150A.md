# Issue #69 — Résultats thermographie plein-champ, run 150 A (Rec-0007)

Première campagne plein-champ (FLIR Research Studio, `.seq`) sur **plaque CF/PEKK libre**
(monospot x=60, cf. `protocole_thermographie_plaque_libre.md`). Décodage `.seq→°C` via
flirpy+exiftool, recalage pixel→mm par 4 fiduciaux, marqueur blanc (x≈60 mm) inpainté.

## Données

- 2508 frames à 8 Hz (313 s), pic à **t=35 s, max 177,6 °C** au chant (⚠️ **au-dessus de Tg=159 °C** :
  la coupure n'a pas été faite à ~140 °C ; sans conséquence pour l'analyse spatiale, à surveiller
  pour la déconsolidation).
- Champ recalé en mm : `figures/issue69/champ_mm_pic.png`.
- 10 lignes recoupées (5 transverses x=30/45/60/75/90 ; 5 longitudinales y=0/10/20/30/40) :
  `figures/issue69/transverses_pic.png`, `longitudinaux_pic.png`.

## Comparaison au modèle (BC plaque libre, chauffe appariée 35 s, largeur-moyenné)

Modèle 2D avec masque céramique OFF, pertes 2 faces (convection lumpée `h_bas_2d`, rayonnement
`emissivite_face`×2), source/géométrie exp7. Comparaison de FORME (absolus non comparables :
plaque découplée, couplage non calibré) — `figures/issue69/compare_rigoureux_longi.png`.

| Métrique | Mesure | modèle k_plan=3,0 | modèle k_plan=7,5 |
|---|---|---|---|
| **Contraste M (largeur, x=60)** | **3,04** | 2,85 | 1,75 |
| Queue longitudinale (x>80, x<30) | — | superposée à la mesure | trop grasse |
| FWHM longitudinale (largeur-moy.) | 33,5 mm | 30,0 | 34,0 |

Robustesse : contraste M et FWHM **insensibles** à la perte de face (h∈[8,24] W/m²K).

## Verdict (préliminaire, 150 A)

**La donnée plein-champ sur plaque libre favorise `k_plan≈3` (valeur physique), PAS le `7,5` effectif.**
- Le **contraste M** (sonde propre, peu sensible à la BC) donne 3,04 ≈ k=3 (2,85) ; k=7,5 effondre le M
  à 1,75 (bien trop lissé).
- La **queue longitudinale** (signature de conduction hors source) se superpose à k=3 ; k=7,5 sur-étale.
- La FWHM=34 de k=7,5 « colle » par artefact (creux du marqueur au centre + étendue en x de la source
  gonflent la mi-largeur — ce n'est pas la conduction).

**Interprétation.** Corrobore la mémoire projet (`residu-unifie-etalement-in-plane`,
`kt-residu-structurel-piste`) : le 3,0 est physique ; le 7,5 était une valeur *effective* de la
calibration en **configuration de soudage** — en isolant la conduction in-plane sur plaque nue, on
retrouve ≈3. Le mur « soudage » (hors-spot trop froid → besoin apparent de k élevé) n'est donc pas une
vraie conductivité mais un effet de montage/source non capté en 2D lumpé. La tension transverse↓/longi↑
(anisotropie kx≥ky) reste visible mais modérée.

## Réserves

1. Un seul courant (150 A) — le 200 A confirmera.
2. BC plaque libre lumpée (convection+rayonnement 2 faces) — mais verdict robuste à h.
3. Modèle lumpé (face arrière imagée vs interface) — comparaison en forme uniquement.
4. Artefacts : marqueur inpainté (x≈60), rayure y≈22, pixels de bord y=0/40.

## Reproductibilité

Scripts d'analyse (décodage/recalage/extraction/comparaison) dans le scratchpad de session ; à
productioniser dans `code/scripts/` (entrée = `.seq`, sorties = CSV lignes + figures). CSV des 10
lignes recoupées : `roi_lignes.csv` (949k lignes, non versionné — volumineux).
