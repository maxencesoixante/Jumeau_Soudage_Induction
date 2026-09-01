# Issue #69 — Prototype source BIMODALE (2 pôles hairpin)

Suite directe de la trouvaille des Volets 1&2 (`synthese_issue69.md`) : le profil longitudinal mesuré
a **deux bosses** que la source à pic unique du jumeau ne reproduit pas. Prototype pour tester si une
**source à 2 pôles** (les 2 jambes du hairpin, `entraxe_jambes=12,35 mm`) les reproduit.

## Méthode (prototype phénoménologique, sans toucher l'EM)

- On garde le **profil en largeur** M(y) et la **puissance totale** de la source EM actuelle.
- On remplace l'enveloppe en x (large, pôle MFC ~31 mm) par **deux gaussiennes étroites** centrées à
  `x = 60 ± entraxe/2` (= 53,8 / 66,2 mm), largeur `σ` balayée (2/3/4 mm), puissance conservée.
- Grille fine **nx=97** (dx=1,25 mm) pour résoudre l'entraxe. BC plaque libre, k_plan=3, chauffe 13 s
  (200 A centré). Comparaison au champ mesuré (largeur-moyenné).

## Résultat

| Source | Bosses (mm) | Creux central |
|---|---|---|
| **MESURE 200 A** | ~50 / 64 | oui (~0,73) |
| Modèle **source UNIQUE (actuel)** | plateau plat | **aucun** |
| Bimodale σ=2 mm | 54 / 66 | 0,65 (trop creusé) |
| **Bimodale σ=3 mm** | 55 / 65 | **0,82 (≈ mesuré)** |
| Bimodale σ=4 mm | 55 / 65 | 0,95 (trop plat) |

→ **La source bimodale crée le creux/double-bosse que la source unique (plateau) ne peut pas produire.**
Le σ optimal ≈ 2,5–3 mm. Léger écart d'espacement (mesuré 50/64 ~14 mm vs modèle 54/66 ~12 mm) et
asymétrie mesurée (lobe gauche plus haut) = raffinements. **Mécanisme confirmé.**

Figures : `figures/issue69/proto_bimodal_longi.png` (profils), `figures/issue69/proto_source_maps.png`
(cartes source unique vs bimodale).

## Conséquences

1. **La source du jumeau doit être bimodale en x** (2 pôles à l'entraxe), pas un pic unique. C'est un
   défaut de forme de source **révélé par le plein-champ**, invisible aux TC épars.
2. Le `k_plan` scalaire et `h_bord_x0` **absorbaient en partie** cette erreur → les ré-évaluer seulement
   **après** avoir intégré la source bimodale dans l'EM (implémentation propre = 2 jambes résolues dans
   le calcul de Foucault, pas ce wrapper phénoménologique).

## Limites du prototype

- Phénoménologique (split gaussien a posteriori), pas une re-dérivation EM des 2 jambes.
- σ et espacement non calibrés finement (1 courant) ; asymétrie non capturée (source symétrique).
- Mêmes réserves que la synthèse (BC lumpée, temps apparié, face arrière).

## Prochaine étape modèle

Implémenter la **bimodalité dans le calcul EM** (2 concentrations sous le MFC à l'entraxe) plutôt qu'en
post-traitement, puis re-valider sur les 3 runs et ré-ouvrir k_plan / h_bord_x0.
