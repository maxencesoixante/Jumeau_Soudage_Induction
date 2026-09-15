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

## Ce que fait la vessie — et la question que cela déplace

**Réponse confirmée : la vessie pousse la plaque contre l'outil supérieur.** La pression de consolidation s'applique donc **sur la plaque**, la réaction étant fournie par l'outil au-dessus. Ce n'est pas la vessie qui referme les soudures des ailes.

Deux conséquences.

**Les soudures d'ailes ne sont pas consolidées par la vessie.** La plaque étant poussée vers le haut et retenue par l'outil, les ailes travaillent en **traction** : la vessie tend à écarter la plaque du U, non à la plaquer sur les ailes. Ce qui met ces interfaces-là en compression pendant la soudure reste à identifier — c'est une question distincte de celle posée ici, mais elle ne peut pas rester ouverte indéfiniment.

**Et surtout, la nature de la cellule redevient incertaine.** Deux montages sont compatibles avec ce qui est décrit, et ils n'ont pas le même problème :

| montage | rôle de la cellule | le partage d'effort dans les ailes |
|---|---|---|
| **A — presse au-dessus** : un vérin pousse l'outil vers le bas, la vessie pousse vers le haut ; la plaque est prise en étau | la cellule **transmet** l'effort de la presse | **pollue la mesure** — l'analyse de cette issue s'applique intégralement |
| **B — vessie seule actionneur** : la vessie pousse, l'outil supérieur ne fait que réagir | la cellule **mesure la réaction** de l'outil | ne la pollue **pas** : la cellule lit $p \cdot A_{\text{plaque}}$, le circuit des ailes est séparé (vessie → âme → bâti) |

⚠️ **Dans le montage B, le problème posé par cette issue n'existe pas.** La cellule n'est plus en parallèle avec les ailes mais en série avec la vessie — ce que la piste 2 cherchait précisément à obtenir, et qui serait déjà acquis. La figure de cette issue suppose le montage A.

**C'est donc la question à trancher en premier :** la cellule transmet-elle l'effort d'une presse, ou mesure-t-elle la réaction d'un outil que seule la vessie sollicite ?

## Ce montage est une conception neuve, pas une adaptation

**Le montage actuel ne comporte pas de vessie.** Le prochain en introduit deux choses à la fois : la **vessie** et le **tube en U**. Il n'existe donc aucune chaîne d'effort existante dont s'inspirer ou qu'il suffirait d'adapter — le cheminement est à concevoir de zéro, ce qui est précisément pourquoi la question se pose maintenant et non après coup.

Conséquence pratique : le choix entre les pistes ci-dessus n'est contraint par aucun existant. Il peut se faire sur les seuls critères de mesure et de pression d'interface, ce qui est plutôt une liberté.

⚠️ Un commentaire de `code/config/essais/chauffe_250A_3TC.yaml` annote la face opposée « côté tube/vessie ». Il décrit la face **destinée** au futur montage, pas un équipement en place — il m'a induit en erreur une fois, il peut le refaire.

Figure reproductible : `.venv/bin/python code/scripts/gen/gen_schema_substitut_tube.py`
