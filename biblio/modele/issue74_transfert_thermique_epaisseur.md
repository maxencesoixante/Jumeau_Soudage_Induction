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

![Montage de la campagne à 3 TC](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/issue74/fig74_montage_3TC.png?v=1)

*Montage de la campagne « épaisseur ». En haut, vue de dessus : bobine et MFC fixes au centre de l'éprouvette, colonne des 3 TC en (60, 20), au centre de la boucle de la bobine. En bas, coupe x-z à 1:1 : TC1 en surface sous la céramique, TC2 à l'interface, TC3 sur la face opposée.*

![Mesures brutes des 5 essais](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/issue74/fig74_mesures_3TC.png?v=1)

*Les 5 essais mesurés, température brute. Zone grisée : chauffe. Valeur en gras : face opposée / interface au pic d'interface. La surface et l'interface montent ensemble ; la face opposée reste sous 180 °C.*

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

## Les trois représentations testées

![Schéma des mécanismes](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/issue74/fig74_mecanismes.png?v=1)

*Schéma sans échelle. Le modèle actuel laisse passer un flux fort vers la face opposée. Le k_z réduit freine la conduction dans le laminé inférieur. La résistance d'interface freine le passage tant que l'interface n'a pas fondu, puis disparaît (au niveau réel, cette forme est contredite par la mesure, voir le correctif du 2026-10-01).*

## Pistes ouvertes

1. ~~**Une source plus concentrée vers le haut.**~~ **Testée et close le 2026-09-29** (voir Résultats) : même sans aucune chaleur déposée sous l'interface, la face opposée reste à 0,88 × l'interface.
2. **Un Cp(T) mesuré.** Hamon (même consortium COMPAAM) donne un Cp mesuré de 939 à 1671 J/(kg·K) selon la température, alors que le modèle utilise 1200 constant. La diffusion transitoire dans l'épaisseur y est directement sensible.
3. **Une mesure qui départage les mécanismes** : la température de la face active du MFC (#15, Mesure A). Elle dirait si une part de la puissance passe par le concentrateur, en champ proche.

## Résultats (2026-09-29)

> **En bref.** Le symptôme est reproduit. La source n'y est pour rien : c'est le **transport** de la chaleur qui compte. Des pertes fortes par les deux faces reproduisent le gradient d'épaisseur sur les cinq essais, mais **aucun jeu de paramètres unique ne ferme les trois familles d'essais** (3 TC, exp9, séries A/B), et ces pertes refroidissent beaucoup trop vite. **Rien n'est adopté.**

### 1. Point de référence : le symptôme est reproduit

Modèle 3D dans la configuration du diagnostic du 2026-08-13 (`facteur_couplage` 6,0123, `h_contact` 5, `h_bas` 15, grille 31×11×15), rapports pris à l'instant du pic d'interface :

| Essai | Face opposée / interface, mesuré | Face opposée / interface, 3D | Surface / interface, mesuré | Surface / interface, 3D |
|---|---|---|---|---|
| 174 A | 0,48 | 0,89 | 0,84 | 1,03 |
| 201 A | 0,42 | 0,89 | 0,88 | 1,03 |
| 226 A | 0,32 | 0,89 | 0,90 | 1,02 |
| 226 A bis | 0,44 | 0,89 | 0,87 | 1,03 |
| 250 A | 0,39 | 0,89 | 0,94 | 1,03 |

### 2. La piste « source » est close

Avec **zéro chaleur déposée sous l'interface**, la face opposée reste à **0,88** × l'interface (0,89 avec la source normale). Ce n'est donc pas l'endroit où la chaleur est déposée qui compte, mais la vitesse à laquelle elle traverse l'empilement : dans le modèle, elle franchit les 3,36 mm du laminé inférieur en environ 30 s, pour une chauffe de 60 s.

### 3. Les deux rapports se règlent par les pertes aux deux faces

![Carte des pertes de face](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/issue74/fig74_carte_pertes.png?v=1)

*Rapports du 3D selon les pertes par la face haute (`h_contact`, vers la céramique, le MFC et la bobine) et par la face basse (`h_bas`, vers le support), essai 201 A. Traits noirs : bornes des fourchettes mesurées. Zone hachurée verte : les deux rapports dans leur fourchette. Rond : jeu 3D actuel. Étoile : `h_contact` 100 / `h_bas` 500. Pointillés : borne haute de `h_bas` dans la calibration 3D. Les rapports ne dépendent presque pas de `facteur_couplage` (face opposée / interface de 0,37 à 0,44 pour un facteur de 3,9 à 17), la carte vaut donc quel que soit le facteur.*

- `h_bas` règle la face opposée, `h_contact` règle la surface : les deux effets sont presque indépendants.
- La zone qui satisfait les deux rapports est **vers `h_contact` ≈ 100 et `h_bas` ≈ 500 W/(m²·K)**, loin du jeu actuel (5 / 15).
- **La calibration 3D ne pouvait pas la trouver** : la borne haute de `h_bas` est fixée à 300 W/(m²·K) (`Calibrateur.BORNES_PAR_MODELE`).

### 4. Validation sur les séries A/B et exp9 : NO-GO

Grille 61×21×15, `valider.py` sans recalage. Trois jeux : l'actuel ; les pertes fortes avec le facteur calé sur le point des 3 TC (201 A) ; les pertes fortes avec le facteur calé sur le TC3 d'exp9 à 200 A (TC d'interface au bord, à l'aplomb du spot).

![Validation 3D sur A/B et exp9](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/issue74/fig74_validation_3D.png?v=1)

*En haut : RMSE moyen par essai. En bas : écart de pic au TC de référence (moyenne de TC2 à TC4 pour les séries A/B, TC3 pour exp9) ; les barres hors échelle portent leur valeur. Chiffres : `biblio/labo/figures/issue74/validation_3D.csv`.*

| Jeu (facteur / `h_contact` / `h_bas`) | Épaisseur (3 TC) | exp9, TC3 au bord | A/B, TC2 à TC4 |
|---|---|---|---|
| 6,01 / 5 / 15 (actuel) | ✗ (0,89) | ✗ (+90 à +203 °C) | ≈ (−24 à −57 °C) |
| 17,1 / 100 / 500 (calé au point des 3 TC) | ✓ | ✗✗ (+678 à +1080 °C) | ≈ (−15 à −36 °C) |
| 3,93 / 100 / 500 (calé sur exp9) | ✓ (0,40–0,44 et 0,90–0,91) | ✓ (−34 à +49 °C ; au centre y = 20 : −59) | ✗ (−121 à −193 °C) |

- **Caler le facteur au point des 3 TC est une erreur de méthode.** Ce point (x = 60, y = 20) est au centre de la boucle de la bobine, où la source est presque nulle : il chauffe par conduction dans le plan. Y caler le niveau fait compenser ce déficit connu (limite #1) par 2,8 fois plus de puissance, qui explose partout où la source chauffe directement.
- **Calé sur exp9**, le jeu à pertes fortes tient l'épaisseur et exp9, mais sous-estime fortement les TC intérieurs des séries A/B : avec des pertes aussi fortes, les longues chauffes des cycles semi-statiques (environ 80 s par passe) plafonnent trop bas.

### 5. Deuxième métrique : ces pertes refroidissent beaucoup trop vite

![Courbes du 201 A](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/issue74/fig74_courbes_201A.png?v=1)

*Les 3 TC empilés du 201 A, mesurés (traits pleins) et simulés (tirets). À droite, le niveau est recalé sur ce point pour comparer les formes : ce recalage est illustratif, et rejeté en validation (section 4).*

À gauche, le jeu actuel donne une colonne presque isotherme. À droite, les pertes fortes creusent le bon gradient au pic, **mais toute la colonne se vide ensuite bien trop vite** : vers 200 s, le 3D est autour de 35 °C quand les trois TC mesurés sont encore vers 110–120 °C. La face opposée mesurée reste chaude longtemps, ce qu'une perte forte et constante par le dessous ne peut pas reproduire.

Le rapport au pic est donc bon **pour une mauvaise raison**. Ce que la mesure suggère plutôt, c'est une chaleur qui **atteint lentement** la face opposée (transport transverse ralenti), et non une chaleur **évacuée vite** par le support.

### Ce qui reste ouvert

- **Les pertes de face dépendent-elles du montage ?** Si l'éprouvette ne reposait pas sur le même support d'une campagne à l'autre (3 TC en mai, séries A/B en juillet, exp9 et 231 A en août), un `h_bas` unique est faux par construction. Le 231 A avait déjà demandé une perte par le bas trois fois plus forte, rejetée en 2D parce qu'elle dégradait les séries A/B. **Question terrain : sur quoi reposait l'éprouvette dans chaque campagne, et quelle céramique la séparait du MFC ?**
- *(Testé le 2026-09-30, voir la section suivante.)* **Un transport transverse ralenti sous l'interface** (k_z plus faible dans le laminé inférieur) est compatible avec la section 5 et reproduisait déjà les deux rapports le 2026-08-13. Attention : sa forme localisée à l'interface (`r_contact_interface`) est NO-GO, parce qu'elle faisait monter TC1. Une version répartie devra passer la même validation avant tout.
- **Le Cp(T) mesuré** (Hamon) reste à tester : il ralentit lui aussi la diffusion.

Scripts : `code/scripts/diag/diag_epaisseur_3d_reference.py` (rapports, options `--alpha-inf`, `--h-contact`, `--h-bas`, `--facteur`), `code/scripts/gen/gen_figures_issue74.py` (figures). Journaux de validation : `resultats/valid3d_*.log` (non versionnés).

## Résultats (2026-09-30) : transport ralenti sous l'interface

> **En bref.** Ralentir le passage de la chaleur sous l'interface (k_z du laminé inférieur 0,10 W/(m·K) au lieu de 0,64, avec `h_contact` = 40) reproduit le gradient d'épaisseur **et** la forme du refroidissement. À leur meilleur facteur respectif, cette configuration fait **mieux que l'actuelle sur les deux familles d'essais** (coût joint 33,3 → 30,9 °C, grille fine). C'est un **candidat sérieux, pas encore adopté** : le gain est modeste, et la forme retenue (k_z réduit dans tout le laminé inférieur) est probablement effective.

### 1. Le réglage et l'épaisseur

Seul le transport change : k_z du laminé inférieur réduit, `h_contact` porté de 5 à 40 pour ramener la surface, `h_bas` inchangé (15). Le k_z est imposé par le chemin « k variable » du solveur 3D. Contrôle : avec k_z inférieur = 0,64, ce chemin redonne exactement le résultat standard.

Au facteur retenu (4,0, voir § 3), sur les 5 essais à 3 TC :

- **face opposée / interface de 0,42 à 0,47 et surface / interface de 0,92 à 0,94** : les deux rapports sont dans leur fourchette sur les 5 essais, y compris le 226 A à chauffe longue qui sortait jusqu'ici ;
- **la forme du refroidissement est juste** : 100 s après le pic d'interface, la face opposée vaut 0,80 × l'interface en simulation, contre 0,78 mesuré (0,92 avec le modèle actuel). C'est la deuxième métrique qui faisait tomber les pertes fortes (Résultats du 2026-09-29, § 5).

Le niveau absolu au point des 3 TC reste trop bas (autour de 190 °C contre 390 °C) : ce point est au centre de la boucle et chauffe par conduction dans le plan (limite #1), il ne sert pas à juger le niveau.

### 2. À facteur égal, le conflit entre familles s'accentue

À `facteur_couplage` = 6,0123, sans recalage : séries A/B neutres ou légèrement meilleures (RMSE 41,7 / 31,2 / 66,6 → 38,6 / 31,4 / 64,1 °C), mais TC3 d'exp9, déjà trop chaud, encore plus chaud (+60 à +90 °C). Ce conflit existait déjà : le 3D actuel surestime exp9 et sous-estime les séries A/B avec le même facteur. La comparaison honnête porte donc sur **le meilleur compromis de facteur** de chaque configuration.

### 3. Meilleur compromis de facteur

![Compromis de facteur](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/issue74/fig74_compromis_facteur.png?v=1)

*Balayage de `facteur_couplage` pour les deux configurations (grille 31×11×15). À gauche : RMSE des TC intérieurs TC2 à TC4 sur A-1, A-3 et B-2. Au milieu : RMSE du TC3 d'exp9 (interface, à l'aplomb du spot) sur les 5 essais. À droite : coût joint, moyenne des deux familles à poids égal ; les étoiles marquent l'optimum. Les TC de coin et les TC froids loin du spot sont exclus du coût.*

Confirmation des deux optimums sur la grille fine (61×21×15) :

| | Actuelle (facteur 4,5) | k_z inférieur 0,10 · `h_contact` 40 (facteur 4,0) |
|---|---|---|
| RMSE A/B, TC2 à TC4 | 42,0 °C | **40,7 °C** |
| RMSE exp9, TC3 | 24,5 °C | **21,0 °C** |
| **Coût joint** | 33,3 °C | **30,9 °C** |

- **Séries A/B** : A-1 s'améliore nettement (RMSE de l'essai 42,1 → 37,7 °C) ; A-3 et B-2 sont neutres ou légèrement meilleurs.
- **exp9** : le gain vient surtout de l'essai au centre de la largeur (y = 20 : 39 → 23 °C). Au bord, le RMSE est inchangé mais les pics montent d'environ 20 °C.
- **Coins des séries A/B**, le piège qui avait fait rejeter `r_contact_interface` : au facteur de compromis, TC1 prend +4, +7 et +20 °C, et TC5 s'améliore de 3 à 4 °C. Le piège est presque absent.

Deux enseignements au passage :

- **Le 3D actuel est mal calé sur son facteur par défaut** : à 4,5 au lieu de 6,01, son coût tombe de 42 à 32 °C, avant même de toucher à l'épaisseur (étape 0).
- **Les séries A/B dépendent peu du facteur**, parce que leur chauffe est coupée par le thermostat : c'est exp9 qui fixe le facteur.

### 4. Vue de côté du flux de chaleur dans l'épaisseur

![Flux de chaleur dans l'épaisseur](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/issue74/fig74_flux_epaisseur.png?v=1)

*Vue de côté à l'échelle 1:1, dans le plan de la colonne des 3 TC (essai 201 A, y = 20 mm), centrée sur le spot. Au-dessus de l'empilement : brins de la bobine, MFC (tronqué) et céramique. Dans l'empilement : température en couleur et flux de chaleur en flèches blanches (direction du flux ; longueur proportionnelle à la racine de son intensité). Pastilles : les 3 TC mesurés, sur la même échelle de couleur. Colonnes : modèle 3D actuel et transport ralenti ; lignes : pic d'interface, puis 100 s après. À droite : profil T(z) de la colonne.*

- **Modèle actuel** : la colonne est presque isotherme ; la chaleur part surtout sur les côtés et le bas du laminé reste chaud, alors que la face opposée mesurée est froide.
- **Transport ralenti** : une frontière thermique apparaît juste sous l'interface, la chaleur y reste concentrée et le bas refroidit comme la mesure ; le profil T(z) suit les trois points mesurés. 100 s plus tard, le bas reste plus froid que le haut, comme mesuré.

⚠️ **Le niveau de chaque configuration est recalé sur le pic mesuré en ce point** (facteur 11,6 et 10,4), pour l'illustration seulement : ce point est au centre de la boucle de la bobine, son niveau absolu est faussé par la conduction dans le plan (limite #1). La figure compare la **forme** du gradient et du flux, pas le niveau ; c'est pourquoi, à +100 s, les deux modèles restent plus chauds que la mesure en surface et à l'interface. Sur cette grille fine (121×21×25), le modèle actuel donne face opposée / interface = 0,79 au lieu de 0,89 sur la grille 31×11×15 : il existe une sensibilité au maillage dans l'épaisseur, sans changer le constat.

Script : `code/scripts/gen/gen_fig74_flux_epaisseur.py`.

### Avant toute adoption

- **Le gain est modeste** (2,4 °C sur le coût joint) et repose surtout sur A-1 et sur l'essai exp9 au centre.
- **La forme est probablement effective.** Un k_z de 0,10 dans tout le laminé inférieur n'a pas de raison matérielle. L'hypothèse physique est une **interface non encore soudée** (film, contacts imparfaits entre deux pièces séparées) qui freine la chaleur jusqu'à la fusion ; une résistance qui disparaît à la fusion serait la forme à tester.
- **L'adoption doit passer par l'inventaire des paramètres effectifs** dont la calibration deviendrait périmée (`h_contact`, `facteur_couplage` du 3D), et par une vérification de l'effet là où la correction agit.

Scripts : `code/scripts/diag/diag_epaisseur_3d_reference.py` (option `--kz-inf`, métrique de refroidissement), `code/scripts/diag/diag_valider_kz_inf.py` (valider.py avec k_z inférieur réduit), `code/scripts/diag/diag_compromis_facteur.py` (coût joint et figure). Journaux : `resultats/compromis/` et `resultats/compromis_fin/` (non versionnés).

## Résultats (2026-09-30, après-midi) : convergence, Cp(T) et résistance levée à la fusion

> **En bref.** Les rapports d'épaisseur sont **convergés en maillage**. Le **Cp(T) mesuré n'agit pas** sur le gradient d'épaisseur. Une **résistance d'interface qui disparaît à la fusion** **corrige les coins des séries A/B d'environ 60 °C**, le défaut le plus tenace du modèle ; elle reproduit l'épaisseur sur 4 essais sur 5 au facteur de compromis, *mais pas au niveau de température réel (correctif du 2026-10-01, section suivante)*. Le k_z réduit reste meilleur à l'intérieur de la plaque. Prochaine étape : **combiner les deux**.

### 1. Convergence du maillage

Rapport face opposée / interface, essai 201 A :

| Configuration | nz de 15 à 51 (plan 31×11) | Plan 61×21 (nz 15 / 25) |
|---|---|---|
| Actuelle | 0,90 → 0,90 | 0,90 / 0,89 |
| k_z inférieur réduit | 0,44 → 0,40 | 0,43 / 0,40 |
| Résistance levée à la fusion | 0,46 → 0,46 | 0,45 / 0,44 |

Les rapports ne dépendent pas du maillage. Le 0,79 de la figure du flux (§ 4 des résultats du matin) vient du **facteur de recalage élevé** : à ce niveau, l'interface fond et la chaleur latente modifie le rapport.

### 2. Le Cp(T) mesuré n'est pas un levier de l'épaisseur

Avec le Cp(T) de Hamon 2025 (939 → 1671 J/(kg·K)) à la place de 1200 constant, la face opposée reste à 0,89 × l'interface ; seul le refroidissement ralentit un peu. C'est un acquis de propriété, pas une correction du gradient.

### 3. Résistance d'interface levée à la fusion

**La forme.** Une résistance R en série à l'interface, active tant que l'interface n'a pas fondu, nulle au-dessus de Tf (rampe sur 337 ± 5 °C). C'est la forme physique visée par l'hypothèse de l'interface non soudée : deux pièces séparées, avec un film et des contacts imparfaits, qui ne forment un seul solide qu'à la fusion. Elle se distingue de `r_contact_interface`, constante, rejetée le 2026-08-13.

**Épaisseur** (R = 0,04 m²·K/W, `h_contact` = 40, au facteur 4,0) : face opposée / interface de 0,46 à 0,51 et surface / interface de 0,91 à 0,92 sur 4 essais sur 5. *Corrigé le 2026-10-01 : ce résultat tient seulement parce qu'à ce facteur l'interface reste sous la fusion au point des 3 TC ; au niveau réel, la résistance se lève et la face opposée se réchauffe (voir le correctif dans la section suivante).* **Échec sur le 226 A à chauffe longue** (0,77 contre 0,32 mesuré) : dans le modèle, l'interface fond, la résistance disparaît et la face opposée se réchauffe ; la mesure montre au contraire sa face opposée la plus froide.

**Séries A/B et exp9**, au meilleur facteur de chaque configuration, confirmé sur la grille fine (61×21×15) :

| Configuration (meilleur facteur) | Coût joint (TC intérieurs) | Écart de pic TC1, coin : A-1 / A-3 / B-2 | Écart de pic TC5 : A-1 / A-3 | RMSE par essai : A-1 / A-3 / B-2 |
|---|---|---|---|---|
| Actuelle (4,5) | 33,3 °C | +106 / +80 / +40 °C | +68 / +70 °C | 42,1 / 32,8 / 63,7 °C |
| k_z inférieur réduit (4,0) | **30,9 °C** | +110 / +87 / +60 °C | +64 / +66 °C | 37,7 / 33,0 / 62,4 °C |
| Résistance levée à la fusion (3,5) | 31,8 °C | **+42 / +18 / −20 °C** | **+34 / +14 °C** | **36,4 / 33,8 / 61,4 °C** |

Au TC3 d'exp9, la résistance levée à la fusion donne des écarts plus homogènes (+51 / +64 / +2 / +58 / +57 °C, contre +10 / +40 / 0 / +79 / +97 pour l'actuelle).

![Compromis de facteur, trois configurations](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/issue74/fig74_compromis_facteur.png?v=2)

*Balayage de `facteur_couplage` (grille 31×11×15) pour les trois configurations ; mêmes conventions qu'au § 3 des résultats du matin. La résistance levée à la fusion atteint son optimum à un facteur plus bas (3,5).*

**Lecture.** Là où l'interface fond (les points les plus chauds, dont les coins), la résistance disparaît et la chaleur peut enfin descendre dans le laminé inférieur : la surchauffe est écrêtée. C'est l'inverse de la résistance constante, qui aggravait ces mêmes coins. Les deux formes du transport ralenti corrigent donc des choses différentes : **le k_z réduit l'intérieur et le 226 A à chauffe longue, la résistance levée à la fusion les coins**. D'où la suite : les combiner.

Scripts : `code/scripts/diag/variantes_epaisseur.py` (k_z inférieur, résistance levée à la fusion, Cp(T)), `code/scripts/diag/diag_valider_variante.py`, `code/scripts/diag/diag_compromis_facteur.py`.

## Résultats (2026-09-30, soir) : combinaison des deux mécanismes

> ### ⚠️ Correctif (2026-10-01) : au niveau de température réel, la résistance levée à la fusion ne tient pas l'épaisseur
>
> Les rapports d'épaisseur de la résistance levée à la fusion et de la combinaison A ont été obtenus **au facteur de compromis** (3,5 à 4,0). À ce facteur, le modèle sous-estime le niveau au point des 3 TC (limite #1), et l'interface y reste **sous la fusion** (190 à 300 °C) : la résistance y est donc toujours active. Or l'interface mesurée en ce point monte à **390 °C**, au-dessus de la fusion. Au niveau réel, le modèle lève la résistance et la face opposée se réchauffe :
>
> | Au niveau réel, point des 3 TC (201 A) | Face opposée / interface |
> |---|---|
> | Mesuré | **0,42** |
> | Modèle actuel | 0,79 |
> | Combinaison A | 0,63 |
> | k_z inférieur réduit seul | **0,41** |
>
> **La mesure montre une face opposée froide avec une interface fondue.** C'est le même contre-indice que le 226 A à chauffe longue, mais cette fois sur le point de mesure lui-même. L'hypothèse « la résistance disparaît à la fusion » est donc contredite à ce point. La correction des coins qu'elle apporte reste un fait du modèle, mais son mécanisme physique devient douteux. **Seul le k_z réduit, qui ne dépend pas de la température, tient l'épaisseur au niveau réel.** Les affirmations concernées plus bas et dans les résultats de l'après-midi sont corrigées et marquées.
>
> ![Flux dans l'épaisseur, combinaison A](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/issue74/fig74_flux_combinaison.png?v=1)
>
> *Même figure que la vue de côté du flux (résultats du matin, § 4), pour le modèle actuel et la combinaison A, niveau recalé sur le pic mesuré (facteur 11,6 et 11,3, illustratif). Au pic, la combinaison A crée un gradient sous l'interface, mais la face opposée reste vers 265 °C contre 167 °C mesuré.*

> **En bref** *(corrigé le 2026-10-01)*. Combiner le k_z réduit et la résistance levée à la fusion donne l'épaisseur juste sur les 5 essais **au facteur de compromis seulement** (au niveau réel : 0,63, voir le correctif), et **pas de synergie** sur les séries A/B et exp9 : la combinaison se place entre les deux mécanismes seuls. On est sur une **frontière de compromis**, aucune configuration ne gagne sur tous les critères. La combinaison A est la plus équilibrée ; la grille fine confirme ce classement.

### Dosage sur les 5 essais à 3 TC

Les deux mécanismes s'additionnent : chacun doit être moins fort que seul. Deux dosages (`h_contact` = 40, facteur 4,0) placent les 5 essais dans la fourchette :

| Dosage | Face opposée / interface : 174 A / 201 A / 226 A / 226 A bis / 250 A | Surface / interface |
|---|---|---|
| **A** : k_z inférieur 0,25 + R = 0,02 m²·K/W | 0,43 / 0,41 / 0,43 / 0,41 / 0,41 | 0,92 à 0,94 |
| B : k_z inférieur 0,15 + R = 0,01 m²·K/W | 0,44 / 0,41 / 0,42 / 0,40 / 0,40 | 0,93 à 0,95 |

Le dosage A réduit k_z d'un facteur 2,6 seulement (contre 6,4 pour le k_z réduit seul).

### Compromis de facteur sur A/B et exp9 (grille 31×11×15)

![Compromis de facteur, cinq configurations](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/labo/figures/issue74/fig74_compromis_combinaison.png?v=1)

| Configuration (meilleur facteur) | Coût joint (TC intérieurs) | TC1, coin : A-1 / A-3 / B-2 | Épaisseur, 5 essais, au facteur 4,0 (voir le correctif pour le niveau réel) |
|---|---|---|---|
| Actuelle (4,5) | 32,4 °C | +71 / +60 / +10 °C | ✗ (0,89) |
| k_z inférieur réduit (4,0) | **29,9 °C** | +73 / +68 / +20 °C | ✓ |
| Résistance levée à la fusion (3,5) | 30,8 °C | **+13 / −4 / −21 °C** | ✗ (226 A long : 0,77) |
| **Combinaison A** (3,5) | 31,1 °C | +45 / +24 / −20 °C | ✓ |
| Combinaison B (4,0) | 31,0 °C | +71 / +65 / +15 °C | ✓ |

**Lecture.** La correction des coins vient de la résistance levée à la fusion. Pour garder l'épaisseur juste quand on ajoute le k_z réduit, il faut diminuer cette résistance, et on perd une partie de la correction. Le choix dépend donc de ce qui compte le plus :

- **l'épaisseur juste partout** (face intérieure du tube de #73, vessie de #71) : ~~combinaison A~~ **k_z réduit seul**, le seul qui tient l'épaisseur au niveau réel *(corrigé le 2026-10-01)* ;
- **les coins des séries A/B** : résistance levée à la fusion seule ;
- **l'intérieur de la plaque** : k_z réduit seul.

La combinaison A est la plus équilibrée au facteur de compromis : coins corrigés par rapport à l'actuelle, coût joint meilleur que l'actuel. *Corrigé le 2026-10-01 : son épaisseur n'est juste qu'à ce facteur, pas au niveau réel.*

### Confirmation sur la grille fine (61×21×15)

| Configuration (facteur) | Coût joint | RMSE TC1 / TC5 (A/B) | TC1, coin : A-1 / A-3 / B-2 | TC5 : A-1 / A-3 | RMSE par essai : A-1 / A-3 / B-2 |
|---|---|---|---|---|---|
| Actuelle (4,5) | 33,3 °C | 55,8 / 42,0 °C | +106 / +80 / +40 °C | +68 / +70 °C | 42,1 / 32,8 / 63,7 °C |
| k_z inférieur réduit (4,0) | **30,9 °C** | 55,3 / 36,0 °C | +110 / +87 / +60 °C | +64 / +66 °C | 37,7 / 33,0 / 62,4 °C |
| Résistance levée à la fusion (3,5) | 31,8 °C | **48,9** / 36,7 °C | **+42 / +18 / −20 °C** | **+34 / +14 °C** | **36,4** / 33,8 / 61,4 °C |
| **Combinaison A** (3,5) | 31,9 °C | 50,6 / 37,1 °C | +81 / +56 / −3 °C | +57 / +49 °C | 37,4 / 34,4 / **61,3** °C |

La grille fine confirme la lecture de la grille grossière :

- **la combinaison A se place entre les deux mécanismes seuls** : coût joint équivalent à la résistance seule (31,9 contre 31,8 °C), coins corrigés d'environ 25 à 45 °C par rapport à l'actuelle, soit environ moitié moins que la résistance seule ;
- ~~c'est la seule des quatre qui tient aussi l'épaisseur sur les 5 essais~~ *(corrigé le 2026-10-01 : faux deux fois — le k_z réduit seul la tient aussi au facteur de compromis, et c'est le seul qui la tient au niveau réel)* ;
- TC3 d'exp9 : +43 / +62 / −6 / +58 / +62 °C, homogène comme avec la résistance seule.

**Pour la suite**, ce qui départagerait vraiment ces configurations n'est plus une simulation mais une mesure : la réponse sur le support de chaque campagne (pertes de face propres au montage ?), ou un essai à 3 TC empilés **près d'un coin** de l'éprouvette, là où les configurations divergent le plus.

## Démarche proposée

0. **Remettre le 3D à niveau.** *(Partiellement fait : le facteur ne se cale pas au point des 3 TC, voir Résultats du 2026-09-29 § 4 ; le 3D actuel est mieux calé à 4,5 qu'à 6,01, voir Résultats du 2026-09-30 § 3.)* Il n'est pas recalé sur le θ\* canonique du 2D (avec `facteur_couplage` = 6,0123, il surestime d'environ 130 °C). Il doit d'abord reproduire l'interface avant qu'on juge l'épaisseur. Vérifier aussi la convergence en z (nz = 15).
1. ✅ **Point de référence.** *(Fait le 2026-09-29.)* Rejouer les 5 essais à 3 TC en 3D, et relever face opposée / interface et surface / interface pour chacun.
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
