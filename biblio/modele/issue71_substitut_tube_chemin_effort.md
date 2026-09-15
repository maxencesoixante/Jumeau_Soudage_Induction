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

![Cheminement de l'effort](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/fig_substitut_tube_chemins_effort.png?v=2)

*À gauche : la coupe transverse et les deux trajets possibles de l'effort. À droite : le même montage réduit à deux raideurs en parallèle.*

## Le problème se dissout — sous une condition

Les plaques sont **simplement posées** sur les ailes, non solidaires. Ce contact est donc **unilatéral** : il transmet de la compression, jamais de traction. Et la vessie pousse la plaque **vers le haut**, c'est-à-dire *loin* des ailes.

**Le chemin parasite ne se contente pas d'être faible : il se déconnecte de lui-même.** Dès la mise en pression, le contact plaque/aile s'ouvre, les ailes ne portent plus rien, et la totalité de $p \cdot A$ traverse l'interface de soudure jusqu'à l'outil.

Le circuit est alors simple et sans dérivation :

**vessie → plaque inférieure → interface → plaque supérieure → outil → cellule**

Ce qui a deux conséquences favorables :

- **la pression d'interface vaut la poussée de la vessie**, sans rendement inconnu ;
- **la cellule mesure exactement l'effort qui traverse la soudure** — elle est en série avec le chemin utile, pas en parallèle avec une dérivation.

### La seule chose qui reste à garantir : les cotes

Le raisonnement ci-dessus tombe si les ailes **portent la plaque avant que l'outil ne la touche**. Dans ce cas l'outil plaque l'empilement sur les ailes, le contact passe en compression, et elles court-circuitent la vessie — le problème initial réapparaît intégralement.

C'est donc une **condition d'empilement de cotes**, pas un problème de raideur :

$$h_U + e_{\text{plaques}} < \text{course disponible sous l'outil}$$

Autrement dit, le U doit être **légèrement trop court**, de sorte que ce soit la vessie — et non les ailes — qui amène les plaques au contact de l'outil.

⚠️ **À vérifier au montage, et à re-vérifier à chaud** : le U en verre, les plaques et l'outil ne se dilatent pas de la même façon, et la soudure fait fondre l'interface donc réduit l'épaisseur de l'empilement pendant le cycle. Une cote juste à froid peut devenir une interférence à chaud, ou l'inverse.

## Ce qu'il reste des quatre pistes

1. **Découpler les ailes de l'empilement** — **déjà acquis par construction.** Les plaques sont posées, pas fixées : le découplage est obtenu par la nature du contact, sans pièce supplémentaire. Il ne reste qu'à le préserver par les cotes.
2. ~~**Mettre la cellule en série avec la vessie**~~ — **sans objet.** Elle l'est déjà.
3. **Piloter en pression plutôt qu'en effort** — **devenu redondant** si les cotes sont correctes, puisque effort mesuré et pression vessie deviennent équivalents. Garde son intérêt comme **contrôle croisé** : un écart entre les deux signalerait précisément qu'une aile porte.
4. ~~**Assouplir localement les ailes**~~ — **écartée.** Le U doit tenir la géométrie sous pression.

**Le travail se déplace donc de la conception mécanique vers le contrôle dimensionnel.**

## Ce qu'il faut savoir avant de trancher

- **Référence et caractéristiques de la vessie** — attendues de RCF Technologies. La raideur n'est plus l'enjeu ; ce qu'il faut désormais, c'est la **plage de pression** et l'**épaisseur de la vessie gonflée**, qui entre dans l'empilement de cotes.
- **Hauteur du U et épaisseur des ailes**, pour écrire la condition de cotes. Seules les plaques sont cotées (120 × 40 mm).
- **Comportement à chaud de l'empilement** : dilatations différentielles et perte d'épaisseur à la fusion de l'interface.

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
