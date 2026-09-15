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
- refermant le U pour en faire un **tube** — le U est **structurel**, pas un substrat de soudure,
- **une seconde plaque CF/PEKK de même longueur soudée sur la première** : c'est là qu'est l'interface étudiée, comme sur le montage plan actuel,
- une **vessie** gonflable dans la cavité (référence à venir de **RCF Technologies**).

## La question

**Comment faire passer les efforts transmis par la cellule de force dans la vessie, et non dans les parois du U ?**

![Cheminement de l'effort](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_substitut_tube_chemins_effort.png?v=1)

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

1. **Découpler les ailes de l'empilement.** Si les plaques ne sont pas solidaires des ailes, celles-ci ne peuvent plus tirer vers le bas : toute la poussée de la vessie traverse l'interface. C'est la piste la plus directe au vu du circuit établi. Reste à savoir comment le U tient alors la géométrie — les deux fonctions doivent être portées par des éléments distincts.
2. ~~**Mettre la cellule en série avec la vessie**~~ — **sans objet.** La cellule mesure déjà la réaction de l'outil, donc l'effort qui traverse l'interface, sous réserve du point de vérification ci-dessus.
3. **Piloter en pression plutôt qu'en effort.** La pression d'interface vaut la pression vessie (à la géométrie près), indépendamment du chemin parasite ; la cellule ne sert plus que de sécurité. Demande de connaître la pression réellement transmise par la vessie.
4. ~~**Assouplir localement les ailes**~~ — **écartée.** Le U doit tenir la géométrie sous pression pendant la soudure (confirmé) : il ne peut pas être rendu souple. La piste est close, pas en attente.

## Ce qu'il faut savoir avant de trancher

- **Référence et caractéristiques de la vessie** — attendues de RCF Technologies. Sans sa raideur et sa plage de pression, le rapport $k_{\text{paroi}}/k_{\text{vessie}}$ n'est pas chiffrable, et aucune piste ne peut être comparée.
- **Section du U** : hauteur, largeur intérieure, épaisseur des ailes. Seule la plaque est cotée (120 × 40 mm).

## Le circuit, maintenant établi

Trois réponses ont fermé les inconnues de conception :

1. la **cellule est au-dessus** de l'empilement ;
2. la **vessie pousse l'empilement vers le haut contre l'outil supérieur** ;
3. la soudure se fait **CF/PEKK sur CF/PEKK**, deux plaques de même longueur — le U ne porte aucune soudure.

Le circuit voulu est donc : **vessie → plaque inférieure → interface de soudure → plaque supérieure → outil → cellule**. La pression de consolidation vient de la vessie, et c'est l'outil supérieur qui fournit la réaction.

### Ce que les ailes du U détournent

Les ailes relient l'âme (poussée vers le bas par la vessie) aux plaques (retenues en haut par l'outil) : elles travaillent donc en **traction**, et cette traction **soustrait** à ce qui traverse l'interface. Sur la plaque inférieure :

$$p \cdot A = R_{\text{outil}} + T_{\text{ailes}}$$

Autrement dit, **plus les ailes sont raides, moins la pression de la vessie atteint la soudure** — il faut alors gonfler davantage pour une même pression d'interface, et le rapport entre les deux devient inconnu. C'est exactement la crainte formulée au départ, et elle est fondée.

### Un point favorable, qu'il faut vérifier

Si rien d'autre que l'outil ne touche la plaque supérieure, la cellule mesure $R_{\text{outil}}$, c'est-à-dire **l'effort qui traverse réellement l'interface** — pas la somme polluée. Dans ce cas l'instrumentation est saine, et le problème se réduit à un rendement : quelle fraction de $p \cdot A$ arrive à la soudure.

⚠️ **À confirmer sur le montage réel** : la plaque supérieure ne doit toucher que l'outil. Tout appui latéral ou toute reprise sur le U rouvrirait le problème de mesure.

## Ce montage est une conception neuve, pas une adaptation

**Le montage actuel ne comporte pas de vessie.** Le prochain en introduit deux choses à la fois : la **vessie** et le **tube en U**. Il n'existe donc aucune chaîne d'effort existante dont s'inspirer ou qu'il suffirait d'adapter — le cheminement est à concevoir de zéro, ce qui est précisément pourquoi la question se pose maintenant et non après coup.

Conséquence pratique : le choix entre les pistes ci-dessus n'est contraint par aucun existant. Il peut se faire sur les seuls critères de mesure et de pression d'interface, ce qui est plutôt une liberté.

⚠️ Un commentaire de `code/config/essais/chauffe_250A_3TC.yaml` annote la face opposée « côté tube/vessie ». Il décrit la face **destinée** au futur montage, pas un équipement en place — il m'a induit en erreur une fois, il peut le refaire.

Figure reproductible : `.venv/bin/python code/scripts/gen/gen_schema_substitut_tube.py`
