**Projet** : jumeau numérique du soudage par induction CF/PEKK &nbsp;·&nbsp; **Objet** : relevés et expériences à réaliser pour améliorer la simulation &nbsp;·&nbsp; **Date** : 23 juillet 2026, **révisé le 24 juillet 2026**

---

## Pourquoi ces mesures

> ⚠ **Révision du 24 juillet 2026.** La version initiale de ce document désignait la
> conduction thermique dans le plan (`k_plan`) comme « levier principal », sur la foi du
> diagnostic du 23 juillet au matin. **Cette conclusion est caduque.** Le soir même, le
> relevé des cotes réelles de la bobine a montré que l'écart que `k_plan` devait expliquer
> venait d'une **erreur de 35 % sur l'entraxe des brins** dans la configuration du modèle.
> Une fois la cote corrigée, l'accord s'obtient à `k_plan = 3 W/m·K`, la valeur physique
> homogénéisée : plus rien ne réclame un facteur 3. Les mesures 6 et 9 restent utiles comme
> vérification d'une propriété matériau, mais **elles ne sont plus prioritaires**. Un relevé
> a été ajouté (n° 5, point de coupure du thermostat) et la numérotation décalée en
> conséquence.

Le jumeau reproduit aujourd'hui les niveaux de température à 30 à 65 °C près et capture la
séquence spatio-temporelle du procédé. Après correction complète de la géométrie de bobine
(entraxe, hauteur, plan image du CFC vérifié sur CAO), l'écart de pic résiduel n'est plus
imputable à une cote : il tient à la forme trop concentrée de la source (profil en « M »).

Deux écarts restent ouverts. D'abord le **régime à basse consigne** : sur l'essai B-2
(coupure à 360 °C au lieu de 400), le modèle sous-chauffe de 30 à 55 °C les capteurs situés
entre deux empreintes. La cause est identifiée — le modèle coupe la chauffe quand le centre
de l'empreinte atteint la consigne, alors que le procédé réel coupait vraisemblablement sur
un thermocouple d'interface plus froid, donc plus tard. Trois correctifs ont été essayés et
réfutés ; c'est désormais une question de mesure (relevé 5 ci-dessous). Ensuite le
**thermocouple de surface**, qui chauffe 5 à 6 fois trop lentement, sans mécanisme identifié.

L'épisode de la bobine oriente aussi la priorité : la mesure qui a le plus rapporté n'était
pas une propriété matériau mais une **cote**. Les relevés de niveau 1 passent donc en tête.

Les mesures ci-dessous visent les entrées du modèle encore incertaines ou figées. Chacune
précise son objectif, la méthode rapide, le paramètre du modèle qu'elle résout, et le gain
attendu. Elles sont classées par rapport valeur/effort décroissant.

---

## Niveau 1. Relevés triviaux (quelques minutes chacun)

### Relevé 1. Métrologie des positions bobine / CFC / thermocouples

> ✔ **En grande partie fait (23–27 juillet 2026), avec un gain majeur.** Les cotes de bobine
> ont été corrigées à partir de la CAO et de la photo de montage : section des brins (carré
> 6 mm), gap (6,35 mm), entraxe (12,35 mm), **hauteur au-dessus du laminé (5,0 mm** = céramique
> 2 mm + demi-tube 3 mm, l'ancienne valeur 6,8 mm étant dérivée d'un tube erroné), et
> **position du concentrateur au-dessus des brins** (plan image du CFC, vérifié). L'entraxe a
> divisé par trois l'écart de pic ; la hauteur a été appliquée pour la justesse physique.
> **Ne reste à relever que la POSITION longitudinale de la tête.**

**Objectif.** Mesurer la position longitudinale de la bobine par rapport au montage (les
cotes propres de la bobine sont désormais fixées, cf. encadré).

**Méthode.** Un pied à coulisse sur le montage pour la distance bobine ↔ repère des
thermocouples. Confirmerait au passage les cotes déjà lues en CAO.

**Reste à relever.** La position longitudinale de la bobine par rapport au montage, qui
détermine `decalage_x`, aujourd'hui figé faute de mesure. C'est le dernier point de géométrie
ouvert.

**Gain attendu.** Lève un paramètre figé de la calibration et fiabilise la source EM. Le
précédent du 23 juillet montre le rapport valeur/effort de ce relevé : quinze minutes de
pied à coulisse contre plusieurs semaines de diagnostic sur une cote fausse.

**Temps estimé.** 15 minutes.

### Relevé 2. Fréquence du générateur à 200 A

**Objectif.** Relever la fréquence de travail de l'EASYHEAT à 200 A.

**Méthode.** Lire l'afficheur du générateur pendant un essai à 200 A (type A-3). La fréquence
à 250 A vaut 388 kHz (relevé du 17 juillet). Le cahier note qu'elle varie avec l'ampérage.

**Paramètre du modèle résolu.** La fréquence EM de l'essai A-3, aujourd'hui supposée égale à
celle de 250 A.

**Gain attendu.** Entrée EM correcte pour l'essai aveugle à 200 A, celui qui teste la loi en
courant.

**Temps estimé.** Une lecture pendant un essai.

### Relevé 3. Épaisseur réelle du pli twill

**Objectif.** Mesurer l'épaisseur du pli twill suscepteur.

**Méthode.** Un micromètre sur un pli twill seul, ou une mesure sur une coupe polie d'un
échantillon soudé.

**Paramètre du modèle résolu.** L'épaisseur du twill (0,28 mm, marquée « à confirmer ») et,
par cohérence, sa conductivité.

**Gain attendu.** Le twill porte l'essentiel de la chaleur. Fiabiliser son épaisseur affine la
répartition de puissance entre couches, au cœur du déficit de surface.

**Temps estimé.** 10 minutes.

### Relevé 4. Condition aux bords de l'échantillon

**Objectif.** Documenter ce qui touche les quatre chants de l'échantillon pendant un essai.

**Méthode.** Photographier et décrire l'appui, la bride ou l'absence de contact sur chaque
chant.

**Paramètre du modèle résolu.** La justification du paramètre `h_bord_x0` (puits de chaleur au
chant x = 0), aujourd'hui fragilisée.

**Gain attendu.** Tranche si `h_bord_x0 = 250` correspond à une condition physique réelle ou
n'est qu'un paramètre effectif, auquel cas le rapport doit le présenter comme tel.

**Temps estimé.** Une photo par essai.

### Relevé 5. Point de coupure réel du thermostat

**Objectif.** Établir sur quel signal la chauffe était coupée pendant les essais des séries
A et B : quel thermocouple ou quelle voie pilotait la régulation, et à quelle position sur
l'échantillon.

**Méthode.** Relire la configuration LabVIEW ou le cahier de laboratoire de la campagne, et
identifier la voie de consigne. Aucune manipulation de banc n'est nécessaire.

**Paramètre du modèle résolu.** Le nœud de contrôle du thermostat simulé. Le modèle coupe
aujourd'hui quand le **centre de l'empreinte** atteint la consigne ; s'il s'agissait en
réalité d'un thermocouple d'interface situé à une quinzaine de millimètres, les impulsions
réelles étaient plus longues.

**Gain attendu.** C'est la mesure qui tranche le résidu ouvert à basse consigne (essai B-2,
sous-chauffe de 30 à 55 °C entre empreintes). Trois correctifs numériques ont été prototypés
et réfutés faute de savoir où le procédé coupait réellement : la donnée manque, pas le code.

**Temps estimé.** Une relecture de configuration, quelques minutes.

---

## Niveau 2. Expériences rapides (un essai chacune, même banc)

### Expérience 6. Cartographie latérale de la diffusivité dans le plan

> ⚠ **Priorité revue à la baisse le 24 juillet.** Cette expérience visait un `k_plan` de 6 à
> 9 W/m·K que la donnée semblait réclamer. Après correction de la géométrie de bobine, le
> modèle s'accorde à `k_plan = 3 W/m·K`, la valeur homogénéisée physique, et un balayage
> jusqu'à k = 6 ne corrige pas le résidu restant. La mesure garde sa valeur de
> **vérification** d'une propriété assumée, mais elle ne tranche plus un écart ouvert.

**Objectif.** Mesurer la diffusivité thermique effective dans le plan du laminé.

**Méthode.** Chauffer un seul spot. Placer 3 ou 4 thermocouples en ligne à distances
croissantes du centre du spot, à profondeur constante. Mesurer la décroissance latérale de
température. La longueur de décroissance donne la diffusivité effective dans le plan.

**Paramètre du modèle résolu.** La conductivité `k_plan`, utilisée à 3 W/m·K (valeur
homogénéisée) et marquée « incertain ».

**Gain attendu.** Transforme une propriété assumée en propriété vérifiée, et fixe une borne
sur l'étalement latéral que le modèle peut produire.

**Temps estimé.** Un essai de chauffe instrumenté en ligne.

### Expérience 7. Cartographie bord vers centre (le profil en « M ») — PRIORITAIRE

> ★ **C'est LA mesure qui débloque le levier « forme de la source ».** Le diagnostic du
> 27 juillet (`resultats_diag_forme_source.log`) a établi que l'écart de pic résiduel, une
> fois la géométrie EM entièrement corrigée, vient du profil en « M » en largeur — un effet
> de courants de Foucault en nappe idéalisée, PAS du champ. Son amplitude ne peut être
> calibrée qu'avec cette cartographie. Tant qu'elle manque, tout correctif de la forme
> serait un ajustement à l'aveugle.

**Objectif.** Mesurer le profil de température d'interface en travers de la largeur et le
confronter point par point à la prédiction du modèle.

**Méthode.** Une ligne de 5 thermocouples d'interface à **y = 0, 10, 20, 30, 40 mm**, au
centre de la longueur (**x = 60 mm**), sur un essai de chauffe simple spot centré (même
montage que l'essai `chauffe_250A_3TC`, qui a déjà son TC d'interface au centre).

**Cible falsifiable (modèle courant, θ\* h=5,0, au pic ≈ 47 s) :**

| y (mm) | 0 | 10 | 20 (centre) | 30 | 40 |
|---|---|---|---|---|---|
| T_pic prédite (°C) | 717 | 382 | **292** | 382 | 717 |

Contraste bord/centre prédit = **2,46×**. Le seul point déjà mesuré, TC2 au centre, donne
**395 °C** contre 292 prédits (modèle trop froid de 103 °C) : indice que **le creux du M est
trop prononcé**, à confirmer sur toute la largeur.

**Interprétation selon le résultat.** Si le contraste réel est nettement inférieur à 2,46×
(centre plus chaud, bords moins), le M est confirmé trop creusé → il faut un mécanisme
d'adoucissement (courants de retour 3D par l'épaisseur, ou résistance de contact du tissu
twill ; cf. `resultats_diag_forme_source.log` §5). Si le contraste est proche de 2,46×, le
modèle tient et l'écart au centre s'explique par l'« œil de boucle » (le TC central tombe au
point de courant nul) — un effet de lecture, pas de physique.

**Temps estimé.** Un essai (se combine avec l'expérience 6, même ligne de TC).

### Expérience 8. Température de la face active du concentrateur

**Objectif.** Mesurer la température du concentrateur pendant une chauffe.

**Méthode.** La caméra FLIR A700 pointée sur la face active du CFC, ou un thermocouple posé
dessus.

**Paramètre du modèle résolu.** Le déficit de chauffe en surface (TC1). Aucun essai actuel ne
mesure la température du concentrateur lui-même.

**Gain attendu.** Seule mesure capable de discriminer les causes du déficit de surface. La
caméra est déjà disponible au laboratoire.

**Temps estimé.** Un essai avec la caméra.

---

## Niveau 3. Mesures de propriété (appareil de laboratoire)

### Mesure 9. Conductivité thermique dans le plan du laminé

**Objectif.** Mesurer directement la conductivité thermique dans le plan du CF/PEKK.

**Méthode.** Flash laser ou disque chaud (hot-disk) sur un échantillon de laminé.

**Paramètre du modèle résolu.** La conductivité `k_plan`, la même que l'expérience 6 attaque
sur le banc.

**Gain attendu.** Transforme un `k_plan` assumé en propriété sourcée. L'écart d'un facteur 3
qui semblait requis le 23 juillet au matin ne l'est plus (voir l'encadré de tête), mais la
valeur homogénéisée de 3 W/m·K reste, elle, non vérifiée expérimentalement.

**Temps estimé.** Préparation d'échantillon plus appareil dédié. L'expérience 6 en est le
substitut rapide sur le banc du laboratoire.

### Mesure 10. Conductivité électrique en fonction de la température σ(T)

**Objectif.** Mesurer la dépendance en température de la conductivité électrique du laminé et
du twill.

**Méthode.** Mesure quatre pointes en montée en température.

**Paramètre du modèle résolu.** La dépendance σ(T), aujourd'hui absente (σ pris constant).

**Gain attendu.** Explique qu'un facteur d'échelle unique ne colle pas simultanément à la
montée, au pic et à la descente. O'Shaughnessey (2014) et Duhovic et al. (2012) recommandent
cette prise en compte.

**Temps estimé.** Mesure plus difficile, à réserver si les niveaux 1 et 2 ne suffisent pas.

---

## Recommandation

Par ordre de priorité pour l'avancement du modèle :

1. **L'expérience 7** (cartographie bord→centre) : c'est désormais LA mesure clé. La
   géométrie EM étant entièrement cadrée, l'écart de pic résiduel vient de la forme de la
   source (profil en « M »), dont l'amplitude ne se calibre qu'avec cette cartographie. Un
   seul essai de chauffe instrumenté d'une ligne de 5 TC, contre une cible chiffrée
   (2,46× de contraste bord/centre). L'expérience 6 s'y ajoute sans coût sur le même montage.
2. **Le relevé 5** (point de coupure du thermostat) : aucune manipulation, une relecture de
   configuration, et c'est la seule information qui tranche le résidu à basse consigne.
3. **Les relevés 1 et 2**, triviaux, qui lèvent deux paramètres figés — l'épisode de
   juillet a montré ce que rapporte un quart d'heure de métrologie.

Ces actions représentent un temps de banc minimal pour le gain le plus élevé.

---

## Tableau de synthèse

| # | Mesure | Niveau | Paramètre résolu | Temps |
|---|---|---|---|---|
| 1 | Position longitudinale de la tête | 1 | `decalage_x` (cotes de bobine ✔ toutes faites) | 15 min |
| 2 | Fréquence générateur à 200 A | 1 | fréquence EM de A-3 | 1 lecture |
| 3 | Épaisseur du pli twill | 1 | épaisseur/conductivité twill | 10 min |
| 4 | Condition aux bords de l'échantillon | 1 | justification `h_bord_x0` | 1 photo |
| 5 | **Point de coupure du thermostat** | 1 | nœud de contrôle — **résidu B-2** | relecture |
| 6 | Cartographie latérale (diffusivité) | 2 | `k_plan` (vérification, non prioritaire) | 1 essai |
| 7 | **Cartographie bord vers centre** | 2 | **profil en « M » — levier forme, PRIORITAIRE** | 1 essai |
| 8 | Température face active du CFC | 2 | déficit de surface TC1 | 1 essai |
| 9 | Conductivité thermique in-plane | 3 | `k_plan` (mesure directe) | labo |
| 10 | Conductivité électrique σ(T) | 3 | dépendance σ(T) | labo |
