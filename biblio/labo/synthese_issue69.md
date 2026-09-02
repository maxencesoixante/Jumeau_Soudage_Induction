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

## Ré-ouverture k_plan (2026-09-02) — source + tilt traités → k_plan ÉLEVÉ confirmé

Une fois la **source bimodale** (`bimodal_sigma_mm=2,5`) ET le **tilt** (symétrisation) retirés, la
**largeur longitudinale** mesurée (FWHM 30–34 mm) exige un **k_plan ÉLEVÉ (≥7,5–9)** et **décisivement
PAS 3** (k=3 → FWHM 22–24 mm, bien trop étroit ; cf. `figures/issue69/kplan_reouvert.png`). RMSE décroît
monotone de k=3 (0,35) à k=9 (0,20).

**Conséquence : l'effectif `k_plan ≈ 7,5+` pour l'étalement in-plane est RÉEL, pas un artefact de source.**
Ça **CORRIGE le « k≈3 » du jour 1** (fondé sur le contraste M, métrique confondue par l'erreur de source
et le tilt) et **reconfirme le résidu structurel / la tension anisotrope** : le **M transverse** veut un
k modéré, l'**étalement longitudinal** veut un k élevé — aucun scalaire ne ferme les deux (cf.
`residu-unifie-etalement-in-plane`). Valeur exacte **dégénérée avec la perte de face** (optimum au bord de
grille k≥9) → énoncer **≥7,5**, pas un chiffre précis.

**Bilan de l'arc issue #69** : le plein-champ a (1) révélé + corrigé un défaut de **source bimodale**
(flag livré), (2) identifié un **tilt d'image** (symétrisation), et (3) une fois ces deux confondants
retirés, **reconfirmé le k_plan effectif élevé** — le jumeau 2D lumpé à `k_plan=3` physique garde sa
**limite structurelle** d'étalement in-plane, désormais mesurée en plein champ.

## Prochaines étapes (par priorité)

1. **Source bimodale** (2 pôles, entraxe) dans le jumeau → re-comparer les 3 runs. C'est le levier
   propre issu de ces données.
2. Une fois la source correcte : **ré-évaluer `k_plan`** puis **`h_bord_x0`** (aujourd'hui confondus).
3. Éventuel 200 A bord + répétitions, coupure ~140 °C.

Figures : `figures/issue69/` (champ_mm_pic, transverses_pic, longitudinaux_pic, compare_rigoureux_longi,
champ_mm_bord, compare_bord, compare_200_longi).

## Ré-ouverture h_bord_x0 (2026-09-02) — sur le run bord, avec source+k traités

Modèle bord (150A, spot ~x=15) avec source bimodale (σ=2,5) + k=7,5, BC plaque libre, pic aligné :
`figures/issue69/hbord_reouvert.png`.

- ⚠️ Le **pixel du chant x=0 est un artefact** (chute brutale 0,75→0,41 sur le dernier pixel = fond froid
  au-delà de la plaque). Valeur fiable au près-bord (x≈2-3 mm) ≈ **0,75**.
- Comparaison au près-bord : **h_bord_x0=0 → 0,73** (colle) ; 100 → 0,68 ; **250 (défaut) → 0,61** (trop
  froid). → **la donnée soutient h_bord_x0 ≈ 0** (chant libre, PAS de puits conductif), cohérent avec le
  fait terrain « 4 chants libres » (`reponses-terrain-2026-07-27`). **Le fudge de 250 sur-refroidit** le près-bord.

**Réserves** : le run bord est la donnée la PLUS FAIBLE (recalage foreshortené — espacement des bosses
22 mm vs entraxe 12,35 mm ; contamination du pixel de bord). Le modèle ne capture pas la 2ᵉ bosse large
mesurée (x≈37, = étalement + registration stretch). Verdict **suggestif, pas définitif** : h_bord_x0=250
n'est pas justifié par la donnée de bord ; candidat au **retrait** (le mettre à 0), à confirmer sur un run
bord mieux recalé (caméra sans tilt, marge autour de la plaque pour éviter la contamination de chant).
