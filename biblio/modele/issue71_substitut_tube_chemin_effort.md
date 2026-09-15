<!--
SOURCE DE VÉRITÉ du corps de l'issue GitHub #71.
Éditer CE fichier, puis : .venv/bin/python code/scripts/gen/sync_issue.py 71
Ne pas éditer l'issue directement dans le navigateur : la prochaine synchro
écraserait la modification sans avertir.
Ce commentaire HTML est invisible dans l'issue rendue.
-->
## Contexte

Le tube CF/PEKK ne sera pas disponible pour le projet. Le substitut envisagé :

- un **U en fibre de verre**,
- refermé par une **plaque CF/PEKK consolidée 120 × 40 mm** (presse chauffante, comme les échantillons actuels),
- soudée sur les deux ailes du U — l'ensemble formant un tube,
- une **vessie** gonflable dans la cavité (référence à venir de **RCF Technologies**).

## La question

**Comment faire passer les efforts transmis par la cellule de force dans la vessie, et non dans les parois du U ?**

![Cheminement de l'effort](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_substitut_tube_chemins_effort.png)

*À gauche : la coupe transverse et les deux trajets possibles de l'effort. À droite : le même montage réduit à deux raideurs en parallèle.*

## Pourquoi ce n'est pas un réglage mais un problème de conception

Il y a **deux chemins en parallèle** entre la cellule et le bâti :

| chemin | trajet | effet |
|---|---|---|
| **voulu** | cellule → plaque → vessie → interfaces | met les interfaces en pression |
| **parasite** | cellule → plaque → ailes du U → bâti | court-circuite la vessie |

Deux raideurs en parallèle se partagent l'effort **au prorata de leur raideur** :

$$\frac{F_{\text{paroi}}}{F_{\text{vessie}}} = \frac{k_{\text{paroi}}}{k_{\text{vessie}}}$$

Or une paroi de verre en compression est **raide**, une vessie sous pression est **souple**. Le rapport est donc très supérieur à 1, et par défaut **presque tout l'effort part dans les ailes**.

⚠️ **Le chemin qu'on veut privilégier est précisément le plus souple — donc celui qui refuse naturellement l'effort.** « De préférence dans la vessie » ne peut pas s'obtenir par un réglage : il faut agir sur la topologie du montage. Tant que les deux chemins coexistent, la cellule mesure surtout la raideur du U.

### La cellule est au-dessus de l'empilement — et cela décide de tout

**Position confirmée : la cellule est au-dessus de l'empilement.** Elle est donc en série avec l'ensemble, et en parallèle avec les deux chemins réunis :

$$F_{\text{cellule}} = F_{\text{vessie}} + F_{\text{paroi}}$$

Elle mesure la **somme**, sans pouvoir la répartir. Or, $k_{\text{paroi}} \gg k_{\text{vessie}}$ donnant $F_{\text{paroi}} \approx F_{\text{cellule}}$ et $F_{\text{vessie}} \approx 0$ :

⚠️ **Telle qu'elle est placée, la cellule mesure presque exclusivement le chemin parasite — c'est-à-dire précisément la grandeur dont on ne veut pas.** Elle est quasi aveugle à l'effort qui atteint les interfaces, qui est pourtant le seul qui compte pour la soudure.

Deux conséquences pour les pistes ci-dessous. La piste 1 devient celle qui **rend la cellule utile** : sans contact des ailes, $F_{\text{cellule}} = F_{\text{vessie}}$ exactement, et la mesure redevient celle de l'interface. La piste 2 n'est plus une option de câblage mais un **déplacement de la cellule**, puisqu'on sait maintenant qu'elle n'est pas en série avec la vessie.

## Pistes à évaluer

Rien de ce qui suit n'est vérifié — ce sont les familles de solutions à instruire, pas une recommandation.

1. **Supprimer le chemin parasite par un jeu.** La plaque ne repose pas sur les ailes : un jeu les sépare, la vessie seule porte, et les ailes ne servent que de butée au-delà d'une course donnée. Demande de maîtriser ce jeu à chaud, alors que la soudure le referme.
2. **Mettre la cellule en série avec la vessie et non en parallèle avec la structure.** La cellule mesure la réaction de la vessie (piston, ligne de pression) plutôt que l'effort global du bâti. Le partage cesse d'être un problème : on ne mesure que ce qui traverse la vessie.
3. **Piloter en pression plutôt qu'en effort.** La pression d'interface vaut la pression vessie (à la géométrie près), indépendamment du chemin parasite ; la cellule ne sert plus que de sécurité. Demande de connaître la pression réellement transmise par la vessie.
4. ~~**Assouplir localement les ailes**~~ — **écartée.** Le U doit tenir la géométrie sous pression pendant la soudure (confirmé) : il ne peut pas être rendu souple. La piste est close, pas en attente.

## Ce qu'il faut savoir avant de trancher

- **Référence et caractéristiques de la vessie** — attendues de RCF Technologies. Sans sa raideur et sa plage de pression, le rapport $k_{\text{paroi}}/k_{\text{vessie}}$ n'est pas chiffrable, et aucune piste ne peut être comparée.
- **Section du U** : hauteur, largeur intérieure, épaisseur des ailes. Seule la plaque est cotée (120 × 40 mm).

## ⚠️ Une question préalable, que je ne sais pas trancher

Le U doit tenir la géométrie **sous pression** : il travaille donc déjà, indépendamment de la cellule. Or ses deux rôles chargent les ailes **dans des sens opposés** :

- la **vessie**, en se gonflant, écarte la plaque du U — elle met les ailes en **traction** ;
- la **cellule**, en poussant vers le bas, met les ailes en **compression**.

D'où une question que je n'ai pas les éléments pour trancher, et qui précède le choix d'une piste : **qu'est-ce qui referme les interfaces de soudure ?**

Si la vessie pousse la plaque **vers le haut**, elle tend à **ouvrir** le joint plutôt qu'à le consolider — à moins qu'un appui extérieur au-dessus de la plaque ne fournisse la réaction, auquel cas c'est cet appui, et non la vessie, qui met l'interface en compression. Le rôle de la vessie serait alors d'appliquer la pression de consolidation **sur la plaque elle-même** contre un outil, et non de refermer les soudures des ailes.

Selon la réponse, « faire passer l'effort dans la vessie » ne désigne pas la même chose :

| si la vessie… | alors l'objectif est… |
|---|---|
| referme les interfaces des ailes | maximiser $F_{\text{vessie}}$ — la formulation initiale s'applique telle quelle |
| consolide la plaque contre un outil | maîtriser la **pression** vessie, la cellule mesurant la réaction de l'outil ; le partage d'effort dans les ailes devient secondaire |

**Cette clarification conditionne le reste** : elle décide si la piste 1 est la bonne cible ou si le problème est en réalité celui de la piste 3.

## Ce montage est une conception neuve, pas une adaptation

**Le montage actuel ne comporte pas de vessie.** Le prochain en introduit deux choses à la fois : la **vessie** et le **tube en U**. Il n'existe donc aucune chaîne d'effort existante dont s'inspirer ou qu'il suffirait d'adapter — le cheminement est à concevoir de zéro, ce qui est précisément pourquoi la question se pose maintenant et non après coup.

Conséquence pratique : le choix entre les pistes ci-dessus n'est contraint par aucun existant. Il peut se faire sur les seuls critères de mesure et de pression d'interface, ce qui est plutôt une liberté.

⚠️ Un commentaire de `code/config/essais/chauffe_250A_3TC.yaml` annote la face opposée « côté tube/vessie ». Il décrit la face **destinée** au futur montage, pas un équipement en place — il m'a induit en erreur une fois, il peut le refaire.

Figure reproductible : `.venv/bin/python code/scripts/gen/gen_schema_substitut_tube.py`
