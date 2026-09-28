<!--
SOURCE DE VÉRITÉ du corps de l'issue GitHub #74.
Éditer CE fichier, puis : .venv/bin/python code/scripts/gen/sync_issue.py 74
Ne pas éditer l'issue directement dans le navigateur : la prochaine synchro
écraserait la modification sans avertir.
Ce commentaire HTML est invisible dans l'issue rendue.
-->
## Objectif

Simuler correctement le **transfert thermique dans l'épaisseur** de l'empilement, de la surface côté bobine jusqu'à la **face opposée** (côté tube ou vessie), et le valider sur les mesures à 3 TC empilés.

Le jumeau de travail est un modèle **2D lumpé** : il ne voit que l'interface, et la face opposée n'y existe pas. Le modèle 3D existe (`thermique/solveur3d.py`), mais il reproduit mal le gradient d'épaisseur. C'est la « limite #2 » du README.

## Pourquoi maintenant

Le prochain montage déplace la question vers la face opposée :

- **Tube substitut (#73)** : la paroi fait 1,68 mm, deux fois moins que le laminé inférieur des essais à plat. Sa face intérieure est-elle au-dessus de Tg (159 °C) pendant le soudage, sous pression et sans contre-pression ? Et la cavité fermée la refroidit-elle, ou l'isole-t-elle (question Q2 de #73) ?
- **Vessie (#71)** : la température au contact de la vessie fixe la marge thermique du matériau.
- **Déconsolidation** du substrat sous l'interface : elle dépend de la température atteinte dans l'épaisseur, pas seulement à l'interface.

Le modèle 2D ne peut répondre à aucune de ces trois questions.

## Ce qu'on sait déjà

**Les mesures.** Cinq essais à 3 TC empilés à (x = 60, y = 20) : surface, interface et face opposée, avec la bobine et le MFC fixes au centre.

| Essai | Face opposée / interface (au pic) |
|---|---|
| 174 A | 0,48 |
| 201 A | 0,42 |
| 226 A (deux répétitions) | 0,32 et 0,44 |
| 250 A | 0,39 |

Surface / interface vaut **0,84 à 0,94** sur les quatre courants : la surface côté bobine est à peu près à la température de l'interface.

Données : `donnees/data/epaisseur_3TC_2026-05/` et `chauffe_250A_3TC-epaisseur_2026-05-20.txt`. Configurations : `code/config/essais/chauffe_*_3TC*.yaml`.

⚠️ **La cible est une fourchette, 0,32–0,48, pas une valeur.** À 226 A, les deux répétitions couvrent à elles seules toute l'amplitude, et il n'y a pas de tendance avec le courant au-delà de la répétabilité. Calibrer sur 0,42 à la décimale reviendrait à ajuster du bruit d'essai.

**Le diagnostic** (2026-08-13) :

- Le modèle 3D donne une colonne presque isotherme : face opposée / interface ≈ **0,9**, loin de la fourchette mesurée. Il **surchauffe la face opposée**.
- Surface ≈ interface est bien reproduit. L'ancienne cible « taux TC1/TC2 ≈ 1,71 » (docstring de `source_joule`) est **fausse**.
- Mécanisme identifié : un **confinement transverse insuffisant**. L'interface est trop couplée au laminé inférieur.
- Un **k_z uniforme est écarté** : pour refroidir la face opposée, il faut k_z ≈ 0,08, ce qui casse surface/interface (0,75).
- Un **découplage asymétrique** (k_z = 0,64 au-dessus de l'interface, ≈ 0,08 en dessous) reproduit les deux rapports à la fois. C'est une reproduction, pas encore une explication physique.

**Déjà testé et réfuté :** une **résistance de contact à l'interface** (`r_contact_interface`, flag conservé mais désactivé par défaut). Elle refroidit bien la face opposée (face opposée / interface 0,40), mais en validation croisée elle déplace le résidu sur l'interface de bord : TC1 prend **+43 à +90 °C**, dans le mauvais sens. Verdict : NO-GO, ne pas la rouvrir sans élément nouveau.

## Pistes ouvertes

1. **Une source plus concentrée vers le haut.** Le modèle dépose déjà plus de puissance au-dessus de l'interface, mais seulement environ 2× (laminé supérieur 85 W, twill 138 W, laminé inférieur 40 W). L'orthotropie électrique transverse est de « plusieurs ordres de grandeur » (Buser), ce qui ferait déposer encore moins de chaleur sous l'interface. **Jamais testée** : seule la voie thermique l'a été.
2. **Un Cp(T) mesuré.** Hamon (même consortium COMPAAM) donne un Cp mesuré de 939 à 1671 J/(kg·K) selon la température, alors que le modèle utilise 1200 constant. La diffusion transitoire dans l'épaisseur y est directement sensible.
3. **Une mesure qui départage les mécanismes** : la température de la face active du MFC (#15, Mesure A). Elle dirait si une part de la puissance passe par le concentrateur, en champ proche.

## Démarche proposée

0. **Remettre le 3D à niveau.** Il n'est pas recalé sur le θ\* canonique du 2D (avec `facteur_couplage` = 6,0123, il surestime d'environ 130 °C). Il doit d'abord reproduire l'interface avant qu'on juge l'épaisseur. Vérifier aussi la convergence en z (nz = 15).
1. **Point de référence.** Rejouer les 5 essais à 3 TC en 3D, et relever face opposée / interface et surface / interface pour chacun.
2. **Tester les pistes une par une** (source, puis Cp(T)), en mesurant l'effet là où elles agissent, c'est-à-dire dans l'épaisseur. Pour chacune, contrôler la validation croisée des TC d'interface. C'est précisément le piège qui a fait tomber `r_contact_interface` : un levier qui corrige l'épaisseur mais déplace le résidu ailleurs.
3. **Appliquer au montage.** Prédire la face intérieure du tube substitut (paroi de 1,68 mm, cavité fermée) pour #73, et la face au contact de la vessie pour #71.

## Critère de succès

- face opposée / interface **dans la fourchette 0,32–0,48** et surface / interface **dans 0,84–0,94**, sur les cinq essais ;
- **sans régression** de la validation croisée sur les TC d'interface (référence : #65) ;
- ou, à défaut, un diagnostic clair de ce qui manque au modèle, avec les leviers écartés et leur raison.

## Liens

- #73 : tube substitut, question Q2 (la cavité refroidit-elle la face intérieure ?)
- #71 : vessie, température au contact
- #15 : Mesure A, température du MFC, pour la répartition de puissance en champ proche
- #14 : DSC du PEKK, à étendre au Cp(T)
- #65 : référence de validation croisée
- README § Limites connues (limite #2, gradient d'épaisseur)
