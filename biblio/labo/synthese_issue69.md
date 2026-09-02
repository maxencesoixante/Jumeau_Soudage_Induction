# Issue #69 — Synthèse thermographie plein-champ (Volets 1 & 2)

3 runs plein-champ FLIR (`.seq`, plaque CF/PEKK libre) : **150 A centré** (Rec-0007), **200 A centré**
(200a centre), **150 A bord** (Rec-0008). Pipeline : flirpy+exiftool (°C), recalage 4 fiduciaux,
inpainting marqueur (x≈60). Détails : `resultats_issue69_150A.md`, `resultats_issue69_bord_150A.md`.

## Conclusion ROBUSTE (indépendante du courant)

**La source longitudinale réelle est BIMODALE ; le modèle a une source à pic unique.**
Profil longitudinal (largeur-moyenné) = **deux bosses** :
- 200 A centré : pics x≈50 et 65 mm (écart ~15 mm), dip x≈57 — **hors marqueur** (inpainté à x=60).
- 150 A bord : pics x≈15 et 37 mm.
- 150 A centré : « creux central » (initialement mis sur le compte du marqueur — en fait la même chose).

**Cause** : bobine hairpin à **2 jambes** (`entraxe_jambes=12,35 mm`, brins le long de y) → 2
concentrations de courant de Foucault en x → 2 bosses. Le jumeau (source à pic unique) ne les résout
pas. **C'est le défaut de modèle le plus net révélé par le plein-champ** (invisible aux TC épars).
→ **Action** : prototyper une **source à 2 pôles** (espacés de l'entraxe) et re-tester.

## Ce qui N'EST PAS tranché (et pourquoi)

- **`k_plan` (3 physique vs 7,5 effectif)** : à 150 A le contraste M penchait k≈3 ; mais à 200 A la
  métrique de contraste est **instable** (centre à peine chauffé à 13 s → dénominateur ~0), les queues
  longitudinales ne séparent pas k=3/7,5, et la **source bimodale non modélisée confond** la mesure.
  → **aucun k scalaire ne tranche proprement entre courants** — cohérent avec la tension structurelle
  déjà actée (`residu-unifie-etalement-in-plane` : « aucune valeur scalaire ne ferme les régimes »).
  Le k scalaire **absorbait en partie l'erreur de source**. À ré-évaluer **après** correction de la source.
- **`h_bord_x0`** (Volet 2) : le défaut (250) sous-estime le chant libre (0,34 vs 0,41) → probable
  sur-refroidissement, MAIS confondu par la source bimodale → non tranché.

## Acquis annexes

- **M en largeur** bien présent (contraste ~3–4, plus net à courant élevé / temps court = moins de
  diffusion). Symétrique (les « asymétries » étaient des pixels de bord).
- **Décodage `.seq` opérationnel** (flirpy 0.6.2 + exiftool + tifffile, Py3.14). Émissivité 0,95,
  réfléchie 20 °C, distance 1 m.
- ⚠️ Les 3 runs ont dépassé **Tg=159 °C** au chant (150c 178, 200c 178, bord 180) — coupure trop tardive ;
  sans effet sur l'analyse de forme, mais viser ~140 °C live à l'avenir.

## Réserves de méthode (à garder pour l'interprétation)

- **Temps apparié arbitraire** : la mesure pique quand l'opérateur coupe (~178 °C), pas à un temps
  physique → comparer le modèle « au même temps » est fragile.
- **Métrique de contraste M instable** à temps court (dénominateur → 0).
- BC libre lumpée, modèle lumpé (face arrière), chant libre ≠ CL soudage.

## Contrôle de robustesse + mécanisme (2026-09-02)

**Double-bosse CONFIRMÉE réelle** (`figures/issue69/robustesse.png`) : présente en **pixels bruts**
(pas un artefact d'homographie), **cohérente 150 A / 200 A** (bosses ~52/66 mm, espacement ~14–16 mm ≈
entraxe 12,35 mm), et **distincte du marqueur** (qui fait sa propre encoche ; le creux subsiste après
inpainting). Le « 22 mm » du run bord = distorsion de recalage, pas un vrai écart. Note : **asymétrie
réelle** (pic ~8–10 mm à gauche du repère → spot posé légèrement excentré), effet de positionnement à part.

**Mécanisme (sweep EM)** : la chaîne quasi-statique ψ produit la bimodalité **trop plate** à TOUS les
paramètres physiques. Le **couplage** est le levier dominant (2 mm→13 % de creux *source*) mais **≤3 %
thermique** (la diffusion l'écrase) vs **16 % mesuré** ; µr/fréquence/rayon négligeables → **pas l'effet
de proximité** dans cette formulation. Conclusion : le modèle manque réellement une structure de source ;
correctif justifié → **flag source bimodale calibrable** (défaut OFF, bit-identique).

## Prochaines étapes (par priorité)

1. **Source bimodale** (2 pôles, entraxe) dans le jumeau → re-comparer les 3 runs. C'est le levier
   propre issu de ces données.
2. Une fois la source correcte : **ré-évaluer `k_plan`** puis **`h_bord_x0`** (aujourd'hui confondus).
3. Éventuel 200 A bord + répétitions, coupure ~140 °C.

Figures : `figures/issue69/` (champ_mm_pic, transverses_pic, longitudinaux_pic, compare_rigoureux_longi,
champ_mm_bord, compare_bord, compare_200_longi).
