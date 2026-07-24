**Projet** : jumeau numérique du soudage par induction CF/PEKK &nbsp;·&nbsp; **Objet** : relevés et expériences à réaliser pour améliorer la simulation &nbsp;·&nbsp; **Date** : 23 juillet 2026

---

## Pourquoi ces mesures

Le jumeau reproduit aujourd'hui les niveaux de température à 25 à 50 °C près et capture la
séquence spatio-temporelle du procédé. Deux écarts restent ouverts. Le modèle concentre trop
la puissance (pics simulés trop hauts de 40 à 60 °C, plateau inter-passes trop froid), et le
thermocouple de surface chauffe 5 à 6 fois trop lentement.

Un diagnostic du 23 juillet 2026 a identifié le levier principal : la conduction thermique
dans le plan du laminé. La donnée réclame une diffusivité latérale effective d'environ 3 fois
la valeur homogénéisée actuelle (k passe de 3 à 6-9 W/m·K). Ce changement améliore à la fois
le RMSE et le dépassement de pic, ce qu'un simple facteur d'échelle ne sait pas faire. Le
diagnostic a aussi écarté trois autres pistes avec des chiffres (capacité thermique haute
température, bloc céramique, outillage métallique).

Les mesures ci-dessous visent les entrées du modèle encore incertaines ou figées. Chacune
précise son objectif, la méthode rapide, le paramètre du modèle qu'elle résout, et le gain
attendu. Elles sont classées par rapport valeur/effort décroissant.

---

## Niveau 1. Relevés triviaux (quelques minutes chacun)

### Relevé 1. Métrologie des positions bobine / CFC / thermocouples

**Objectif.** Mesurer les positions relatives de la bobine, du concentrateur et des
thermocouples sur le montage, et extraire les cotes exactes de la bobine hairpin.

**Méthode.** Un pied à coulisse sur le montage pour les distances relatives. Les cotes de la
bobine (diamètre du tube de cuivre, entraxe des jambes, longueur utile) se lisent sur la CAO
SolidWorks du montage.

**Paramètre du modèle résolu.** Le paramètre `decalage_x`, aujourd'hui figé faute de mesure,
et la géométrie de bobine qui alimente tout le calcul électromagnétique.

**Gain attendu.** Lève un paramètre figé de la calibration et fiabilise la source EM.

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
chant x = 0), aujourd'hui fragilisée. Le levier k_plan pourrait le rendre inutile.

**Gain attendu.** Tranche si `h_bord_x0 = 250` correspond à une condition physique réelle ou
compense en réalité le déficit de conduction latérale.

**Temps estimé.** Une photo par essai.

---

## Niveau 2. Expériences rapides (un essai chacune, même banc)

### Expérience 5. Cartographie latérale de la diffusivité dans le plan

**Objectif.** Mesurer la diffusivité thermique effective dans le plan du laminé. C'est le
levier principal identifié le 23 juillet.

**Méthode.** Chauffer un seul spot. Placer 3 ou 4 thermocouples en ligne à distances
croissantes du centre du spot, à profondeur constante. Mesurer la décroissance latérale de
température. La longueur de décroissance donne la diffusivité effective dans le plan.

**Paramètre du modèle résolu.** La conductivité `k_plan`, aujourd'hui à 3 W/m·K et marquée
« incertain ». La donnée du modèle en réclame 6 à 9.

**Gain attendu.** Si la mesure confirme une diffusivité d'environ 3 fois l'homogénéisée, elle
justifie k_plan ≈ 9 par la mesure au lieu de l'assumer. Ce seul changement divise par deux le
dépassement de pic sur A-1 et baisse le RMSE sur les trois essais.

**Temps estimé.** Un essai de chauffe instrumenté en ligne.

### Expérience 6. Cartographie bord vers centre (le profil en « M »)

**Objectif.** Tester la prédiction du modèle sur la répartition de température dans la largeur.

**Méthode.** Une ligne de 3 à 5 thermocouples sur la largeur de 40 mm, à l'interface, mêmes
paramètres qu'un essai B-2. Cette expérience se combine avec l'expérience 5, même type de
montage.

**Paramètre du modèle résolu.** Le profil en « M » prédit (bord chaud, centre froid), dont
l'amplitude reste incertaine.

**Gain attendu.** Confirme ou falsifie le contraste spatial du modèle, l'écart le plus
structurant. Le modèle prédit des lobes chauds sur les chants et un creux au centre.

**Temps estimé.** Un essai.

### Expérience 7. Température de la face active du concentrateur

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

### Mesure 8. Conductivité thermique dans le plan du laminé

**Objectif.** Mesurer directement la conductivité thermique dans le plan du CF/PEKK.

**Méthode.** Flash laser ou disque chaud (hot-disk) sur un échantillon de laminé.

**Paramètre du modèle résolu.** La conductivité `k_plan`, la même que l'expérience 5 attaque
sur le banc.

**Gain attendu.** Transforme un k_plan « effectif assumé » en propriété sourcée. Confirme ou
infirme l'écart d'un facteur 3 trouvé le 23 juillet.

**Temps estimé.** Préparation d'échantillon plus appareil dédié. L'expérience 5 en est le
substitut rapide sur le banc du laboratoire.

### Mesure 9. Conductivité électrique en fonction de la température σ(T)

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

Si le temps de laboratoire est limité, trois actions attaquent directement le levier k_plan
identifié le 23 juillet et la question spatiale ouverte :

1. Les relevés 1 et 2, triviaux, qui lèvent deux paramètres figés.
2. L'expérience 5 combinée à l'expérience 6, une seule session de thermocouples en ligne qui
   teste à la fois la diffusivité latérale et le profil en « M ».

Ces trois actions représentent un temps de banc minimal pour le gain le plus élevé.

---

## Tableau de synthèse

| # | Mesure | Niveau | Paramètre résolu | Temps |
|---|---|---|---|---|
| 1 | Métrologie positions bobine/CFC/TC | 1 | `decalage_x` + géométrie bobine | 15 min |
| 2 | Fréquence générateur à 200 A | 1 | fréquence EM de A-3 | 1 lecture |
| 3 | Épaisseur du pli twill | 1 | épaisseur/conductivité twill | 10 min |
| 4 | Condition aux bords de l'échantillon | 1 | justification `h_bord_x0` | 1 photo |
| 5 | Cartographie latérale (diffusivité) | 2 | `k_plan` (levier principal) | 1 essai |
| 6 | Cartographie bord vers centre | 2 | profil en « M » | 1 essai |
| 7 | Température face active du CFC | 2 | déficit de surface TC1 | 1 essai |
| 8 | Conductivité thermique in-plane | 3 | `k_plan` (mesure directe) | labo |
| 9 | Conductivité électrique σ(T) | 3 | dépendance σ(T) | labo |
