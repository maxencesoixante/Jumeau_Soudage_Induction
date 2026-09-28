<!--
SOURCE DE VÉRITÉ du corps de l'issue GitHub #73.
Éditer CE fichier, puis : .venv/bin/python code/scripts/gen/sync_issue.py 73
Ne pas éditer l'issue directement dans le navigateur : la prochaine synchro
écraserait la modification sans avertir.
Ce commentaire HTML est invisible dans l'issue rendue.
-->
## Contexte

Nouveau montage, **plus fidèle au montage final** que la plaque posée à plat : on soude le connecteur sur un **tube substitut entièrement en CF/PEKK**, creux, sans contre-pression intérieure.

Il prolonge #71 (substitut en U fibre de verre + vessie) : si les parois du tube tiennent seules la pression de consolidation, la question du chemin d'effort vers la vessie ne se pose plus pour ce montage.

## Le montage

![Montage tube substitut](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_montage_tube_substitut.png?v=3)

*En haut : vue de dessus, connecteur centré sur le tube, ligne de TC d'interface et avance du spot. En bas : coupe transverse à l'échelle 1:1, avec le chemin d'effort (outil → plaque de dessus → murs → plaque de fond → bâti) et la cavité d'air fermée.*

**Fabrication du tube substitut**

1. Consolidation à la presse chauffante de plaques CF/PEKK **[45,−45,0,−45,45,0₃]ₛ** (16 plis, 1,68 mm).
2. Découpe d'échantillons aux dimensions du tube : **deux murs de 40 mm** de haut, **une plaque de dessus** et **une plaque de fond** de 50 mm de large.
3. Plaques de 50 mm **posées sur et sous les murs**, puis les rainures au contact des murs sont **fondues au fer à souder** (dessus et fond) pour que l'ensemble forme un caisson fermé, solidaire pendant le soudage.

**Soudage**

4. Soudage sur la plaque de dessus d'un **connecteur** identique aux essais précédents : **[45,−45,0,90]₃ₛ**, 120 × 40 mm, 3,36 mm.
5. **Cycle semi-statique** (même protocole que #64, pas ≈ 30 mm).

## Ce que l'expérience doit montrer

### Q1 — Les murs supportent-ils la pression de consolidation ?

Si oui, **pas besoin de contre-pression à l'intérieur du tube**. Et le résultat est conservateur : sur le montage réel, les murs porteront beaucoup plus que dans ce substitut.

Ce qu'il faut regarder :

- **les murs** : pas d'écrasement ni de flambement sous l'effort de la cellule ;
- **la plaque de dessus** : elle travaille en flexion sur une **portée libre de ≈ 46,6 mm** entre les murs, et elle est chaude pendant la chauffe. Mesurer sa flèche résiduelle après l'essai ;
- **la soudure** : consolidation comparable au montage à plat, sans déconsolidation ni porosité visibles en coupe. Une pression bien appliquée par l'outil mais perdue par la flexion du dessus se verrait ici, pas sur les murs.

### Q2 — La cavité creuse modifie-t-elle la thermique de la face opposée ?

L'idée : le tube étant creux, la face intérieure (côté cavité) pourrait refroidir un peu la plaque de dessus, et donc influer sur le soudage.

Ce qu'on sait déjà et ce qui reste ouvert :

- La face opposée est **déjà froide** sur le montage à plat : opposée/interface = **0,32–0,48** au pic sur 4 courants (campagne épaisseur de mai, `donnees/data/epaisseur_3TC_2026-05/`).
- Deux effets tirent en sens contraire. L'air confiné du caisson fermé échange peu (convection naturelle, quelques W/(m²·K)) : il isole plutôt qu'il ne refroidit, comparé à un laminé posé sur le bâti. À l'inverse, la plaque de dessus est deux fois plus mince (1,68 mm au lieu de 3,36 mm) et a moins d'inertie : la chaleur l'atteint plus vite.
- Le sens de l'effet n'est donc **pas acquis**. Il faut le mesurer plutôt que le supposer. **Proposition : un TC collé sur la face intérieure du dessus, à x = 60 mm** (cercle creux sur la figure), à comparer à la campagne épaisseur.
- Le jumeau peut donner une prédiction à l'aveugle avant l'essai (en 3D, avec la face inférieure passée en condition de cavité). Ce serait un test à la manière de #64.

## Points de vigilance

- **Les rainures fondues sont sous le spot.** Le MFC fait 55 mm dans la largeur, le tube 50 mm : les deux coins dessus/mur sont dans l'emprise du champ. Il faut vérifier après l'essai qu'ils n'ont pas refondu ou ne se sont pas ouverts.
- **La ligne de TC n'est plus au bord du substrat.** Le connecteur (40 mm) est centré sur un dessus de 50 mm, donc la ligne de TC y = 0 se trouve à 5 mm du bord du tube, au-dessus du mur. Les TC de bord ne sont donc pas directement comparables à exp9.

## Hypothèses de la figure, à confirmer

- [ ] faces extérieures des murs affleurant les bords de la plaque de 50 mm ;
- [ ] tube de 120 mm de long, comme le connecteur, qui est centré en largeur ;
- [ ] même instrumentation que le semi-statique (5 TC d'interface sur la ligne y = 0).

## À faire

- [ ] consolider les plaques [45,−45,0,−45,45,0₃]ₛ et relever leur épaisseur réelle
- [ ] découper et assembler le tube (rainures au fer)
- [ ] instrumenter : 5 TC d'interface + TC face intérieure
- [ ] (optionnel) prédiction du jumeau avant l'essai, face intérieure en condition de cavité
- [ ] soudage semi-statique ; relever l'effort de la cellule
- [ ] post-essai : flèche du dessus, état des murs et des rainures, coupe de la soudure
- [ ] conclure sur Q1 (contre-pression nécessaire ?) et Q2 (effet de la cavité)

Script de la figure : `code/scripts/gen/gen_schema_montage_tube_substitut.py`
