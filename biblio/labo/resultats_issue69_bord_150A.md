# Issue #69 Volet 2 — Résultats thermographie plein-champ, spot AU BORD, 150 A (Rec-0008)

Suite du Volet 1 (spot centré → `k_plan≈3`, cf. `resultats_issue69_150A.md`). Ici MFC+coil au
**bout de la plaque** (spot à x≈15 mm du chant libre x=0), comme la 1ʳᵉ/dernière passe de soudage.
Même pipeline (`.seq` flirpy+exiftool, recalage 4 fiduciaux).

## Données

- 3527 frames à 8 Hz, pic **t=20 s, max 179,8 °C** (⚠️ >Tg=159 ; le bord chauffe **plus vite** que le
  centre — accumulation, coupure à ~140 °C d'autant plus impérative).
- Fiduciaux (col,row) : (202,160)(374,168)(195,476)(370,475) → plaque 120×40 mm.
- Champ recalé : `figures/issue69/champ_mm_bord.png` — chaleur confinée à x≈0–50, froide au-delà,
  M en largeur visible, accumulation vers le chant x=0.

## Trouvaille principale : source longitudinale BIMODALE (non modélisée)

Le profil longitudinal mesuré (largeur-moyenné) a **DEUX bosses** (x≈15 et x≈37 mm, creux à x≈27),
alors que **les 4 configs modèle donnent un pic unique** (`figures/issue69/compare_bord.png`).
**Explication géométrique** : la bobine est un **hairpin à 2 jambes** (`entraxe_jambes=12,35 mm`,
brins le long de y) → deux concentrations de courant de Foucault en x → deux bosses de chaleur. La
source du jumeau (pic unique en x) ne les résout pas. Corrobore rétrospectivement le Volet 1 (bosses
~50/63 mm, écart ~13 mm ≈ l'entraxe, jusqu'ici attribué au marqueur). **Le plein-champ révèle une
structure de source en x invisible aux TC épars** → piste de raffinement de la source (2 pôles/jambes).

## Effet de bord (`h_bord_x0` / `lambda_bord_x`) — préliminaire

Valeur normalisée AU chant libre x=0 (mesure vs 4 configs, spot bord, BC libre, chauffe 20 s) :

| Config | x=0 (norm.) |
|---|---|
| **MESURE** | **0,41** |
| λ_bord AUTO + h_bord_x0=250 (**défaut**) | 0,34 (trop froid) |
| λ_bord AUTO + h_bord_x0=0 | 0,45 |
| λ_bord OFF + h_bord_x0=250 | 0,40 |
| λ_bord OFF + h_bord_x0=0 | 0,52 |

Lecture : le **défaut (h_bord_x0=250) SOUS-estime la température du chant libre** (0,34 vs 0,41) →
cohérent avec `h_bord_x0` **trop fort pour un chant libre** (fudge du montage soudage ; les chants sont
libres, cf. `reponses-terrain-2026-07-27`). Le retirer (0,45) va dans le bon sens. **MAIS confondu** par
l'erreur de forme de source (bimodale) → verdict de bord **non tranché** ; il faut d'abord une source
bimodale correcte avant de conclure sur `h_bord_x0`.

## Verdict Volet 2

1. **Acquis solide** : source longitudinale **bimodale** (2 jambes du hairpin) révélée par le plein-champ,
   absente du modèle à pic unique → raffinement de source identifié.
2. **Préliminaire** : `h_bord_x0=250` semble **sur-refroidir le chant libre** ; à reconfirmer une fois la
   source bimodale intégrée (les deux effets se confondent au bord).

## Réserves

- Placement du spot modèle (`centre_x=20 mm`) estimé → sensibilité de la valeur x=0.
- BC libre lumpée, modèle lumpé (face arrière), 1 courant.
- Chant libre ≠ CL de contact réelle du soudage.

## Reproductibilité

Scripts dans le scratchpad (décodage/recalage/extraction/comparaison) ; entrée `.seq`, à productioniser.
