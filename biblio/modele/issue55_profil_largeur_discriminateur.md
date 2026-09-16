<!--
SOURCE DE VÉRITÉ du corps de l'issue GitHub #55.
Éditer CE fichier, puis : .venv/bin/python code/scripts/gen/sync_issue.py 55
Ne pas éditer l'issue directement dans le navigateur : la prochaine synchro
écraserait la modification sans avertir.
Ce commentaire HTML est invisible dans l'issue rendue.
-->
## Objectif

Mesurer le **profil de température sur la largeur** `T(y)` à l'interface, avec le **MFC labo 55 mm** puis le **MFC réduit 31,75 mm**, à courant et durée identiques — et s'en servir pour **trancher entre trois modèles concurrents** du MFC réduit.

⚠️ **Le critère de succès de cette issue a été réécrit le 2026-09-16.** L'ancien disait : *« profil moins contrasté, avec point chaud recentré »*. C'était la prédiction d'**une seule** des trois familles de modèle — celle que l'analyse identifie comme l'intrus. Une mesure montrant un profil **resté contrasté** aurait été classée en échec, alors que c'est une **discrimination propre**. Voir `biblio/modele/prediction_mfc_familles.md`.

## Ce que la mesure doit trancher

Un MFC raccourci n'a pas un modèle mais trois, qui ne diffèrent pas par leur finesse mais par une **affirmation physique** : que devient le flux qui n'est plus sous le bloc de ferrite ?

| famille | affirmation | conséquence attendue |
|---|---|---|
| **Masque conservatif** | il **se reconcentre** sous le bloc restant, à puissance totale conservée | le profil s'aplatit et le point chaud se recentre |
| **Image tronquée — observation** | il **ne se reconcentre pas** : hors du bloc on retombe au cas sans MFC | le profil reste contrasté, point chaud aux chants |
| **Image tronquée — source** | idem, troncature duale (côté source) | idem, à niveau plus bas |

Les deux variantes « image tronquée » tronquent la même physique de deux façons indépendantes et **s'accordent entre elles** ; le masque conservatif est l'intrus. Aucun calcul ne tranche : c'est cette mesure qui le fait.

## Principe

Campagne en largeur (façon Exp 7) : ligne de **5 TC type K à l'interface**, `y = 0 / 10 / 20 / 30 / 40 mm`, spot fixe `x = 60 mm`. Seul le bloc MFC change ; tout le reste identique. Protocole `biblio/labo/protocole_mfc_reduit.md` §2–3.

> **Nommage.** Les deux passes sont désignées **« passe 55 »** et **« passe 31,75 »**, d'après la longueur du bloc. L'ancienne notation « passe A / passe B » entrait en collision avec les familles de modèle A et B et a produit exactement la confusion qu'on cherche à éviter ici.

## À faire

- **Passe 55** et **passe 31,75** à **200 A**, même durée (fenêtre ≈ 18 s). Réutiliser Exp 7 200 A pour la passe 55 si le montage est identique.
- Relever `T(y)` au pic aux 5 TC, en **°C bruts**.
- Calculer les quatre observables ci-dessous — **tous en rapport passe 31,75 / passe 55**, mesurés dans la même campagne.

## Critère de succès — table de verdict pré-enregistrée

Prédictions figées avant mesure (200 A, 18 s, `x = 60 mm`, θ\* canonique, source `prediction_mfc_familles.md`) :

| observable | aucun effet | masque conservatif | image — observation | image — source |
|---|---|---|---|---|
| **① position du max parmi les 5 TC** | chants (`y` = 0/40) | **`y` = 10 ou 30** | chants | chants |
| **② centre TC3, rapport / passe 55** | 1,00 | **1,46 (il MONTE)** | 0,94 | 0,76 |
| **③ contraste bord/centre, rapport / passe 55** | 1,00 | **0,37** | 0,95 | 0,90 |
| **④ chant TC1, rapport / passe 55** | 1,00 | 0,54 | **0,89** | **0,68** |

Valeurs absolues correspondantes (°C) : contraste bord/centre **2,77** (passe 55) contre **1,03** / **2,62** / **2,49**.

**Comment lire, dans cet ordre :**

1. **② est le discriminateur principal, et c'est un signe, pas une amplitude.** Le centre **monte** avec le MFC réduit sous le masque conservatif, il **descend** sous les deux variantes image. Un signe résiste aux erreurs de calibration comme aucun rapport ne le fait.
2. **③ confirme** : un contraste divisé par ~2,7 désigne le masque conservatif ; un contraste quasi inchangé désigne la famille image **ou** l'absence d'effet.
3. **④ sépare alors** ce que ③ ne sépare pas : absence d'effet (1,00), variante observation (0,89), variante source (0,68).
4. **① est le contrôle visuel** : si le max se déplace du chant vers `y` = 10/30, c'est le masque conservatif, sans calcul.

**Succès de la campagne = une ligne de la table est désignée sans ambiguïté**, quelle qu'elle soit. Un profil resté contrasté n'est pas un échec : c'est le verdict « le flux ne se reconcentre pas ».

## Pourquoi tout est écrit en rapports

Deux biais connus s'annulent au premier ordre quand on compare les deux passes **d'une même campagne** :

- le modèle **sur-contraste** d'environ 15-20 % (Exp 7 : mesuré 2,0-2,2 contre modèle 2,4-2,55) ;
- **θ\* n'est recalibré pour aucune géométrie réduite** (objet de #60, après cette mesure) — les niveaux absolus sont donc moins fiables que leurs rapports.

C'est pourquoi aucun seuil absolu n'apparaît dans la table de verdict.

## Ce que cette mesure ne tranchera pas

- **Elle ne valide aucune des trois familles comme physique.** Toutes sont des approximations de 1er ordre ; aucune ne résout le bloc de ferrite fini, la méthode des images supposant un demi-espace infini. La mesure désigne la moins fausse, pas la vraie.
- **Elle ne dit rien de la couverture de soudage.** Les calculs de plan de passes concluent NON dans les quatre hypothèses testées (`biblio/modele/plan_passes_familles.md`) — ce verdict ne dépend pas de l'issue de cette campagne.
- **Un résultat intermédiaire est possible** (contraste vers 1,8 par exemple, entre les deux groupes). Dans ce cas la conclusion à écrire est « aucune des trois familles ne décrit le MFC réel », pas « la plus proche gagne ».

## Dépendances / liens

Protocole `biblio/labo/protocole_mfc_reduit.md`. MFC réduit **reçu**. Prédictions figées : `biblio/modele/prediction_mfc_familles.md`, `biblio/modele/prediction_mfc_reduit.md`. Alimente la recalibration θ\* (#60). Campagne parente #63. Conséquences procédé : #62.
