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
entre deux empreintes. **La cause est désormais confirmée par le cahier de laboratoire
(relevé 5 ci-dessous)** : le procédé coupait quand le thermocouple d'interface le plus chaud
atteignait la consigne, alors que le modèle coupe quand le centre de l'empreinte l'atteint —
donc trop tôt. Un correctif physiquement fondé (loi « capteurs ») est en cours de test et de
recalibration. Ensuite le **thermocouple de surface**, qui chauffe 5 à 6 fois trop lentement,
sans mécanisme identifié (exp 8, à réaliser).

> **Mise à jour du 27 juillet 2026 (réponses utilisateur).** Trois relevés sont tranchés :
> épaisseur du twill = **0,20 mm** (relevé 3, correction préparée) ; chants latéraux **à l'air
> libre** → `h_bord_x0` est un paramètre **effectif**, pas physique (relevé 4) ; point de
> coupure du thermostat = **max des TC d'interface** (relevé 5, via le cahier). Détail dans
> chaque fiche ci-dessous.

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

**Réponse (utilisateur, 2026-07-27) :** « Je ne comprends pas ce qu'il faut relever, précise la question. »

> → **Précision.** Il ne reste qu'à mesurer **de combien le centre de la bobine est décalé le
> long de x** (les 120 mm) par rapport à la position visée du spot : la bobine est-elle pile
> au-dessus du point d'indexation, ou décalée de quelques mm ? C'est le paramètre `decalage_x`,
> figé à 0 faute de mesure. **Peu critique** : s'il n'est pas mesurable facilement, on le laisse
> figé. (Les cotes de section/entraxe/hauteur de la bobine, elles, sont déjà résolues.)

### Relevé 2. Fréquence du générateur à 200 A

**Objectif.** Relever la fréquence de travail de l'EASYHEAT à 200 A.

**Méthode.** Lire l'afficheur du générateur pendant un essai à 200 A (type A-3). La fréquence
à 250 A vaut 388 kHz (relevé du 17 juillet). Le cahier note qu'elle varie avec l'ampérage.

**Paramètre du modèle résolu.** La fréquence EM de l'essai A-3, aujourd'hui supposée égale à
celle de 250 A.

**Gain attendu.** Entrée EM correcte pour l'essai aveugle à 200 A, celui qui teste la loi en
courant.

**Temps estimé.** Une lecture pendant un essai.

**Réponse (utilisateur, 2026-07-27) :** _(en attente)_

> **Relevés 3, 4 et 5 — RÉSOLUS (27 juillet 2026), archivés dans
> [`releves_resolus.md`](releves_resolus.md).** En bref : twill mesuré **0,20 mm** (corr.
> préparée) ; chants **à l'air libre** → `h_bord_x0` est un paramètre effectif, pas physique ;
> thermostat coupait sur le **max des TC d'interface** (cahier de labo) → loi « capteurs »
> implémentée derrière un flag. Les trois corrections s'intégreront à la prochaine
> recalibration.

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

**Réponse (utilisateur, 2026-07-27) :** « Expérience intéressante. Faut-il atteindre la Tfusion
du PEKK ? J'aimerais réutiliser mes échantillons. Quels ampérages sont intéressants pour
calibrer, et quel temps de maintien ? Idée : réaliser l'essai **sans le système de pression**
et mettre une **caméra thermique au-dessus** de l'échantillon. Motivation : le modèle ne tient
compte ni de la pression ni de la céramique d'espacement. »

> → **Précisions.**
> - **Pas besoin d'atteindre Tf.** La diffusivité latérale se lit sur un simple gradient ;
>   reste bien sous 337 °C (pic ~150-250 °C) → **tu réutilises tes échantillons**.
> - **Ampérages** : les mêmes que la calibration, **250 A et 200 A** (conditions A-1/A-3), pour
>   rester comparable au modèle. Un courant plus bas aide à rester sous Tf.
> - **Temps de maintien** : quelques secondes à ~30 s suffisent ; c'est la **longueur de
>   décroissance latérale** pendant le transitoire qui porte l'information, pas un long plateau.
> - **Caméra sans pression** : bonne idée, mais ⚠️ **la caméra de dessus ne voit PAS
>   l'interface** — le CFC et la céramique la masquent, elle ne lirait que la surface du laminé
>   supérieur (M atténué par la diffusion dans l'épaisseur). Utile quand même (champ de surface,
>   et parfaite pour l'exp 8, face du CFC), mais l'interface exige des TC noyés.
> - Le modèle ignore effectivement la **mécanique** de pression (son effet de contact est
>   absorbé dans `h_haut`) : retirer la pression pour ce test est sans conséquence.

> → **PROTOCOLE RETENU — caméra thermique de dessus (2026-07-27).**
>
> **Deux mises au point de physique** (suite à « chauffer sans céramique + caméra ») :
> 1. **La caméra lit la SURFACE, pas l'interface.** Pour la diffusivité latérale c'est OK — la
>    *longueur de décroissance* latérale est la même propriété matériau en surface qu'à
>    l'interface. Mais la T absolue de surface est plus basse/retardée (diffusion sur 3,36 mm)
>    → comparer à la prédiction de **surface du modèle 3D**, pas à l'interface.
> 2. **Retirer la céramique d'espacement ≠ se rapprocher du modèle.** Le modèle ne la néglige
>    PAS : il la représente comme le **gap bobine-laminé de 2 mm** (couplage EM) ET la condition
>    `h_haut`. La retirer supprime le gap (bobine 2 mm plus bas → **source EM plus forte et de
>    forme différente**) et change `h_haut`. La diffusivité reste mesurable (la décroissance
>    latérale est robuste à ces changements), mais **la géométrie n'est plus celle des essais
>    de calibration** : à documenter, et à re-représenter dans la config pour toute comparaison
>    quantitative.
>
> **Mode opératoire.**
> - Chauffer un **spot unique** (250 A puis 200 A), rester **sous Tf** (pic ~150-250 °C),
>   échantillons réutilisables ; maintien quelques s à ~30 s.
> - Caméra au-dessus : mesurer la **décroissance en LONGUEUR (x), au-delà de l'empreinte du
>   CFC** (55×31,5 mm) — c'est là qu'est l'info. En **largeur (y)**, le CFC déborde les 40 mm et
>   **masque la zone** → non mesurable à la caméra (réserver aux TC noyés, exp 7).
> - Si la céramique d'espacement couvre tout le laminé (cahier B-1 : 120×40 mm) et masque la
>   surface, la retirer est acceptable **pour ce seul but** — noter alors « gap nul » dans le
>   compte rendu.
> - Sortie utile : profil T_surface(x) à quelques instants → longueur de décroissance → `k_plan`
>   effectif, confronté à la surface du modèle 3D à même géométrie.

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

**Réponse (utilisateur, 2026-07-27) :** « Même réponse qu'à la question précédente. » (caméra
thermique de dessus, sans pression, échantillons réutilisés)

> → **Précision — point critique pour CETTE expérience.** Contrairement à l'exp 6, la cible
> ici est le profil **à l'interface** (le « M »), et la caméra de dessus **ne le voit pas**
> (masqué par le CFC/céramique ; la surface ne montre qu'un M très atténué). Il faut donc des
> **TC noyés à l'interface** aux 5 positions y = 0/10/20/30/40 mm, pas la caméra. La caméra
> reste un bon complément (surface + face CFC), mais ne remplace pas les TC d'interface pour
> falsifier la cible chiffrée ci-dessus.

### Expérience 8. Température de la face active du concentrateur

**Objectif.** Mesurer la température du concentrateur pendant une chauffe.

**Méthode.** La caméra FLIR A700 pointée sur la face active du CFC, ou un thermocouple posé
dessus.

**Paramètre du modèle résolu.** Le déficit de chauffe en surface (TC1). Aucun essai actuel ne
mesure la température du concentrateur lui-même.

**Gain attendu.** Seule mesure capable de discriminer les causes du déficit de surface. La
caméra est déjà disponible au laboratoire.

**Temps estimé.** Un essai avec la caméra.

**Réponse (utilisateur, 2026-07-27) :** « Je vais réaliser l'expérience demain ou cet
après-midi. »

> → Parfait. La caméra vue de dessus (ton idée pour les exp 6/7) est **idéale ici** : la face
> active du CFC est directement visible. Vise une acquisition pendant une chauffe simple spot ;
> compare la montée du CFC à celle de TC1 (surface) — c'est la seule mesure qui attaque le
> déficit de chauffe en surface.

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

**Réponse (utilisateur, 2026-07-27) :** « J'ai pas compris cette expérience. »

> → **Précision.** C'est une mesure d'**appareil de labo** (hot-disk ou flash laser), pas sur
> le banc de soudage : on dépose une impulsion de chaleur sur un petit **échantillon de
> matière** et on chronomètre sa vitesse d'étalement → on en déduit la conductivité thermique
> dans le plan `k_plan`. L'**expérience 6** (spot + TC en ligne sur le banc) en est le
> substitut « maison ». Non prioritaire : sers-toi de l'exp 6 si tu veux vérifier `k_plan`.

### Mesure 10. Conductivité électrique en fonction de la température σ(T)

**Objectif.** Mesurer la dépendance en température de la conductivité électrique du laminé et
du twill.

**Méthode.** Mesure quatre pointes en montée en température.

**Paramètre du modèle résolu.** La dépendance σ(T), aujourd'hui absente (σ pris constant).

**Gain attendu.** Explique qu'un facteur d'échelle unique ne colle pas simultanément à la
montée, au pic et à la descente. O'Shaughnessey (2014) et Duhovic et al. (2012) recommandent
cette prise en compte.

**Temps estimé.** Mesure plus difficile, à réserver si les niveaux 1 et 2 ne suffisent pas.

**Réponse (utilisateur, 2026-07-27) :** « J'ai pas compris cette expérience non plus. »

> → **Précision.** Mesure **4 pointes** (van der Pauw) sur un échantillon de laminé/twill que
> l'on chauffe progressivement : on lit la résistance électrique à chaque température, ce qui
> donne σ(T), la variation de la conductivité électrique avec la température. Le modèle prend
> aujourd'hui σ **constante** ; en réalité elle change avec T, ce qui explique en partie qu'un
> facteur d'échelle unique ne colle pas à la fois à la montée, au pic et à la descente. Mesure
> la plus lourde des dix, à réserver si les niveaux 1-2 ne suffisent pas.

---

## Recommandation

Les relevés 3, 4 et 5 sont tranchés (réponses du 27 juillet). Reste, par ordre de priorité :

1. **L'expérience 7** (cartographie bord→centre) : c'est désormais LA mesure clé. La
   géométrie EM étant entièrement cadrée, l'écart de pic résiduel vient de la forme de la
   source (profil en « M »), dont l'amplitude ne se calibre qu'avec cette cartographie —
   **par des TC noyés à l'interface** (la caméra de dessus ne voit pas l'interface). Un seul
   essai de chauffe, ligne de 5 TC, contre la cible chiffrée (2,46× de contraste bord/centre).
2. **L'expérience 8** (face du CFC, caméra thermique) : à réaliser prochainement ; seule
   mesure qui attaque le déficit de chauffe en surface (TC1).
3. **Le relevé 1** (position longitudinale de la bobine), trivial, qui lève le dernier
   paramètre de géométrie figé (`decalage_x`) — si mesurable facilement.

Côté modèle, trois corrections découlent des réponses : loi thermostat « capteurs »
(relevé 5, en test), épaisseur twill 0,20 mm (relevé 3) et requalification de `h_bord_x0`
(relevé 4) — à intégrer ensemble à la prochaine recalibration.

---

## Tableau de synthèse

| # | Mesure | Niveau | Paramètre résolu | Temps |
|---|---|---|---|---|
| 1 | Position longitudinale de la tête | 1 | `decalage_x` (cotes de bobine ✔ toutes faites) | 15 min |
| 2 | Fréquence générateur à 200 A | 1 | fréquence EM de A-3 | 1 lecture |
| 3 | Épaisseur du pli twill ✔ | 1 | **0,20 mm mesuré** (corr. préparée) | fait |
| 4 | Condition aux bords ✔ | 1 | **chants libres → `h_bord_x0` effectif** | fait |
| 5 | Point de coupure du thermostat ✔ | 1 | **max des TC d'interface** (cahier) — résidu B-2 | fait |
| 6 | Cartographie latérale (diffusivité) | 2 | `k_plan` (vérification, non prioritaire) | 1 essai |
| 7 | **Cartographie bord vers centre** | 2 | **profil en « M » — levier forme, PRIORITAIRE** | 1 essai |
| 8 | Température face active du CFC | 2 | déficit de surface TC1 | 1 essai |
| 9 | Conductivité thermique in-plane | 3 | `k_plan` (mesure directe) | labo |
| 10 | Conductivité électrique σ(T) | 3 | dépendance σ(T) | labo |
