**Destinataire** : directrice de recherche &nbsp;·&nbsp; **Dépôt logiciel** : `Jumeau_Soudage_Induction` (Python, 34 tests automatisés) &nbsp;·&nbsp; **État au** : 2026-07-24

---

## Résumé exécutif

Ce document décrit le jumeau numérique développé en soutien de la campagne expérimentale de
soudage par induction semi-statique de composites carbone/PEKK. Le modèle prédit l'empreinte
thermique, la carte de température à l'interface de soudure que crée l'ensemble bobine
d'induction et concentrateur de flux. Les thermocouples ne donnent que quelques points de
mesure ; le jumeau reconstruit la distribution complète, puis se confronte aux essais réels
pour établir sa validité.

Le calcul enchaîne trois maillons physiques. D'abord le champ magnétique de la bobine et de
son concentrateur de flux. Ensuite les courants de Foucault induits dans le laminé et son
pli suscepteur. Enfin le transfert thermique transitoire avec fusion du PEKK. Trois
paramètres physiques mal connus sont calibrés sur un seul essai, puis le modèle est validé
en aveugle sur les autres, y compris à un courant différent (200 A au lieu de 250 A). Le
jumeau reproduit les niveaux de température à 30 à 65 °C près en moyenne et capture la
séquence spatio-temporelle du procédé.

Un épisode de juillet 2026 mérite d'être signalé d'emblée, car il oriente la suite du
travail. L'écart le plus tenace du modèle, un dépassement de pic présenté jusqu'ici comme un
déficit de physique, s'est révélé provenir de **cotes de bobine fausses**, non de mécanismes
manquants : d'abord l'entraxe des brins (19 mm supposés contre 12,35 mm réels), puis leur
hauteur au-dessus du laminé (6,8 contre 5,0 mm), toutes deux dérivées d'un diamètre de tube
erroné plutôt que mesurées. Une fois la géométrie électromagnétique rendue correcte — cotes
et plan image du concentrateur vérifiés sur la CAO — l'écart résiduel ne se recale plus par
un simple facteur d'échelle : il tient à la **forme** de la source, trop concentrée. La
section 9 en tire la leçon de méthode et situe ce résidu.

Le document précise chaque hypothèse simplificatrice avec sa source bibliographique, ce que
le modèle simule et ce qu'il laisse de côté (bobine, concentrateur, céramique, laminé,
suscepteur), les méthodes numériques, la démarche de calibration et de validation, les
limites identifiées, et l'ensemble des outils d'intelligence artificielle mobilisés pour le
développement. Il se termine sur les mesures et les développements de modélisation à venir.

---

## 1. Contexte et objectifs

Le soudage par induction assemble les composites à matrice thermoplastique (CFRTP) sans
apport de matière étrangère durable, en continu, et rapidement. Il atteint aujourd'hui un
niveau de maturité élevé pour les grandes pièces (Bayerl, Duhovic, Mitschang &
Bhattacharyya, 2014). Le procédé repose sur une chaîne multiphysique : un champ magnétique
alternatif induit des courants de Foucault dans le réseau de fibres de carbone conductrices,
dont les pertes résistives (effet Joule) échauffent le matériau jusqu'à la fusion de la
matrice à l'interface de soudure.

Le pilotage se heurte à une fenêtre de mise en œuvre étroite. Le PEKK fond à 337 °C, la cible
de soudage se situe entre 355 et 390 °C, et la dégradation commence vers 450 °C. Quelques
thermocouples ne donnent accès qu'à un petit nombre de points. La distribution spatiale
complète de la température, celle qui gouverne la qualité de la soudure sur toute la surface,
reste hors de portée de l'instrumentation.

Le jumeau numérique poursuit trois objectifs :

1. Prédire la carte de température (l'empreinte thermique) sur toute la zone de soudure, là
   où aucun capteur ne se trouve.
2. Servir de modèle de procédé (« plant model ») en vue d'un futur contrôle prédictif du
   courant en temps réel.
3. Documenter la démarche de modélisation et de validation pour un chapitre du mémoire.

Le jumeau s'appuie sur la campagne expérimentale. Il s'y calibre, s'y valide, et produit des
prédictions falsifiables qui orientent les prochaines mesures.

---

## 2. Le problème physique et le montage modélisé

Le montage de référence est le banc de soudage par induction semi-statique du laboratoire,
hérité et instrumenté par plusieurs générations de travaux (O'Shaughnessey, 2014 ; Côté,
2018). La chaîne d'efforts et la géométrie se lisent de haut en bas :

| Élément | Rôle physique | Dimensions / propriétés |
|---|---|---|
| **Bobine hairpin (épingle)** | Génère le champ magnétique alternatif | Deux brins de cuivre parallèles, **section carrée de 6 mm**, **gap de 6,35 mm** entre brins, soit un **entraxe centre-à-centre de 12,35 mm** ; axe des brins à **5,0 mm** au-dessus du laminé (céramique 2 mm + demi-tube 3 mm) ; générateur Ambrell EASYHEAT 4,2 kW ; 388 kHz (relevé machine), 200 à 250 A |
| **Concentrateur de flux (CFC)** | Canalise le flux magnétique vers l'échantillon | Fluxtrol Ferrotron 559H, µr ≈ 16 ; 55 × 31,5 × 12 mm ; grand côté (55 mm) parallèle à la largeur de l'échantillon |
| **Céramique d'espacement** | Fixe le gap bobine–laminé ; transparente au champ | Pamitherm, 2 mm ; sert aussi de chemin de pression |
| **Laminé supérieur** | Adhérent à souder ; porte le suscepteur | CF/PEKK `[45/-45/0/90]₃ₛ`, 120 × 40 × 3,36 mm |
| **Pli twill (sergé) suscepteur** | Concentre les courants de Foucault à l'interface | Tissu carbone à l'interface de soudure |
| **Film PEKK** | Apport de matrice à l'interface | environ 0,10 mm |
| **Laminé inférieur** | Second adhérent | CF/PEKK `[45/-45/0/90]₃ₛ`, 120 × 40 × 3,36 mm |

Deux faits géométriques gouvernent tout le comportement thermique.

La bobine et le concentrateur débordent de la largeur de l'échantillon. Le grand côté du CFC
(55 mm) et les brins de la bobine dépassent des deux côtés du plan de l'échantillon (40 mm de
large). Le champ magnétique devient alors quasi uniforme sur toute la largeur, une
configuration qui pèse sur la forme de l'empreinte thermique (section 9).

Le pli twill conduit l'électricité dans le plan environ 40 fois mieux que le laminé. Il porte
l'essentiel des courants de Foucault et concentre la chaleur à l'interface de soudure. Le
choix d'un tissu plutôt qu'un pli unidirectionnel a une raison physique : un renfort tissé
referme les boucles de courant dans les deux directions du plan, alors que dans un
unidirectionnel la formation des boucles reste largement stochastique (van den Berg,
Luckabauer, Wijskamp & Akkerman, 2024 ; Fink, McCullough & Gillespie, 1992).

Le procédé est semi-statique. La bobine reste fixe, la table translate, et l'opérateur réalise
la soudure par quatre empreintes successives le long des 120 mm de longueur (pas de 30 mm).
Entre deux empreintes, le générateur est coupé le temps du repositionnement.

---

## 3. La chaîne physique en trois maillons

Le jumeau résout les trois maillons ci-dessous à la suite. Chacun forme un module logiciel
indépendant, vérifié séparément par des tests analytiques.

### 3.1 Champ magnétique : bobine hairpin et concentrateur de flux

Ce maillon calcule le champ magnétique alternatif `Bz(x, y)` que la bobine crée dans le plan
de chaque couche conductrice du laminé.

La bobine hairpin devient une polyligne de segments de courant, et le calcul emploie la loi
de Biot–Savart. L'entraxe des deux brins constitue l'entrée géométrique dominante de ce
maillon : il fixe la position des deux filaments de courant, donc la forme de `Bz` et, en
cascade, celle de la source Joule. La section 9 documente ce qu'a coûté une erreur sur
cette seule cote. Le champ d'un segment rectiligne fini `a → b` parcouru par un courant `I`, au
point d'observation `P`, s'écrit :

```
B = (µ₀·I / 4π) · (û × r₁) / |û × r₁|²  · (û·r̂₁ − û·r̂₂)
```

où `û` est le vecteur unitaire du segment, `r₁ = P − a`, `r₂ = P − b`. Le calcul se vectorise
sur l'ensemble des points de la grille. Vérification : le champ au centre d'une boucle
circulaire discrétisée en 200 côtés reproduit la formule analytique `B_centre = µ₀·I / 2R` à
10⁻³ près, et le champ sur l'axe reproduit `B = µ₀·I·R² / [2(R² + d²)^{3/2}]` (tests
`test_champ_coil.py`).

Le concentrateur de flux (CFC) passe par la méthode des courants images. Le bloc de Ferrotron
559H (µr ≈ 16) devient un demi-espace perméable : chaque segment de la bobine se réfléchit à
travers le plan inférieur du CFC avec un courant `η·I`, où le coefficient de raccord aux
interfaces vaut :

```
η = (µr − 1) / (µr + 1) ≈ 0,88   pour µr = 16
```

Cette approximation capture au premier ordre l'intensification du champ sous l'empreinte du
concentrateur, l'effet même pour lequel on utilise un CFC. Elle laisse de côté la géométrie
exacte du bloc fini, une limite assumée (section 9).

**Sources.** O'Shaughnessey (2014) établit le principe du concentrateur de flux magnétique et
son intérêt pour homogénéiser le chauffage. Il note qu'aucun modèle de la littérature
antérieure ne prend en compte l'effet d'un concentrateur de flux magnétique. Les travaux
COMPAAM (Martin et al., 2024) recommandent de dimensionner le concentrateur plus étroit que la
zone de soudure pour limiter les effets de bord. Les propriétés du Ferrotron 559H viennent de
la fiche technique constructeur (Fluxtrol Inc.).

**Auto-échauffement du concentrateur.** Le modèle laisse de côté les pertes propres du CFC
(Joule et hystérésis dans le Ferrotron). Un chiffrage justifie cette omission. À partir de la
courbe de pertes constructeur (`Pv = 4,1·f^{1,1}·B^{2,5}` W/cm³) et du champ calculé dans le
volume du bloc à 250 A et 388 kHz, la puissance totale dissipée dans tout le concentrateur
(20,8 cm³) ne dépasse pas 0,6 à 1,4 W, soit 1 à 2 ordres de grandeur en dessous du seuil qui
influencerait le bilan thermique. Le mécanisme existe mais reste négligeable à cette échelle.

### 3.2 Courants de Foucault : formulation plaque mince

Ce maillon calcule la densité de courants de Foucault que le champ `Bz` variable induit dans
chaque couche conductrice.

**Le régime « plaque mince ».** À 388 kHz, la profondeur de pénétration du champ (effet de
peau) dans le laminé, `δ = √(2ρ / µ₀ω) ≈ 6 mm`, dépasse l'épaisseur du laminé (3,36 mm). Le
champ reste donc quasi uniforme dans l'épaisseur de chaque couche, et les courants induits
deviennent plans. Cette hypothèse justifie une analyse bidimensionnelle par couche. Lin
(1993) la formule ainsi : si le composite est mince et si la convection reste bien plus lente
que la conduction à travers l'épaisseur, on peut supposer la température uniforme dans
l'épaisseur, ce qui autorise une analyse en deux dimensions. Duhovic et al. (2012) fournissent
la valeur de la profondeur de peau pour du CF/PEEK et la règle pratique associée (au moins
deux éléments de maillage dans l'épaisseur de peau pour une erreur inférieure à 5 %).

**Formulation par fonction de courant.** Pour garantir que le courant induit reste à
divergence nulle (conservation de la charge, `∇·J = 0`), le calcul introduit une fonction de
courant `ψ` telle que `J = ∇×(ψ ẑ)`, c'est-à-dire `Jx = ∂ψ/∂y` et `Jy = −∂ψ/∂x`. La loi de
Faraday en régime harmonique, combinée à la loi d'Ohm anisotrope `E = ρ̃·J`, donne l'équation
aux dérivées partielles que vérifie `ψ` :

```
∂/∂x (ρyy · ∂ψ/∂x) + ∂/∂y (ρxx · ∂ψ/∂y) = ω · Bz
```

avec la condition aux limites `ψ = 0` sur tout le pourtour de la plaque. Cette condition
traduit un fait simple : aucun courant ne traverse le chant de l'échantillon, les boucles de
Foucault se referment à l'intérieur du matériau. `ρxx` et `ρyy` désignent les résistivités du
plan de la couche considérée, `ω = 2πf` la pulsation, `Bz` le champ (valeur efficace).
L'équation se résout par différences finies sur la grille du plan, avec un système linéaire
creux (`scipy.sparse`).

**Sources.** Lin (1993) établit la formulation par pertes résistives (`q = J·E`, `J = σE`,
`∇·J = 0`) et la résolution par différences finies 2D de la répartition des courants de
Foucault sous une bobine de forme quelconque. Il montre aussi que les fibres de graphite
portent tous les courants de Foucault (leur conductivité, σ ≈ 10⁵ S/m, dépasse infiniment
celle de la matrice, σ ≈ 10⁻¹⁵ S/m), et qu'un circuit fermé de fibres reste nécessaire.
L'application au tenseur de conductivité anisotrope mesuré d'un laminé C/PEKK, avec `µr = 1`
pour le laminé, suit Grouve et al. (2020).

**Le champ de réaction (blindage).** Le champ que les courants induits créent en retour, et
qui s'oppose au champ excitateur, reste négligé par défaut. Une implémentation explicite l'a
ensuite évalué (section 9 et annexe) : son effet propre reste faible (0,2 à 0,6 % par couche),
et le facteur d'échelle calibré absorbe l'écart résiduel.

**Vérification.** Cinq tests couvrent le solveur de fonction de courant
(`test_foucault.py`) : nullité de `ψ` au bord, conservation des symétries dans le cas isotrope,
lois d'échelle exactes en `ω` et en `ρ`, positivité de la dissipation, et satisfaction de
l'équation aux nœuds intérieurs.

### 3.3 Source de chaleur : effet Joule par couche

Ce maillon calcule la puissance volumique dissipée `q(x, y)` dans chaque couche, à partir de
la fonction de courant.

Une fois `ψ` connu, la dissipation Joule moyenne (valeur efficace) s'écrit :

```
q(x, y) = ρxx · Jx²  +  ρyy · Jy²     [W/m³]
```

Le calcul traite trois couches conductrices séparément, chacune avec son propre tenseur de
résistivité : le pli twill suscepteur (à l'interface, le plus conducteur, qui domine la
chaleur), le laminé supérieur et le laminé inférieur (homogénéisés). Un facteur d'atténuation
par effet de peau `e^{−2t/δ}` s'applique aux couches situées sous une couche écran, pour
représenter le blindage inter-couches. La source volumique totale `Q(x, y, z)` se dépose sur
la grille avec conservation de la puissance surfacique.

Un facteur d'échelle unique, `facteur_couplage`, multiplie l'ensemble de la source. Il
absorbe les incertitudes physiques non résolues : blindage négligé, qualité des contacts
fibre-fibre, incertitude sur la conductivité effective. C'est l'un des trois paramètres
calibrés (section 7). Ce choix suit la logique du jumeau 1D antérieur et de son test de
vérification « boîte noire » (Samanis et al., 2026), qui a montré une contrainte : calibrer
la fréquence et le facteur d'échelle ensemble ne fonctionne pas, ils sont totalement corrélés.
La fréquence reste donc figée à sa valeur mesurée.

**Vérification.** La source croît bien en `I²` (linéarité de Biot–Savart multipliée par la
dépendance quadratique de la dissipation), le pli twill porte plus de puissance que la face
opposée, et la source se localise sous l'empreinte active (`test_source_et_procede.py`).

### 3.4 Transfert thermique transitoire avec fusion

Ce maillon calcule l'évolution du champ de température `T(x, y, t)` sous l'effet de la source
Joule, de la conduction, des pertes de surface, et de la fusion.

L'équation de la chaleur résolue s'écrit :

```
ρ·cp(T) · ∂T/∂t = ∇·(k·∇T) + Q(x, y, z, t)
```

avec les termes de perte aux frontières : convection et rayonnement sur les faces libres (loi
de Stefan–Boltzmann, en kelvins), et conductance vers un puits thermique sous l'empreinte du
concentrateur, là où la bobine et le CFC refroidis à l'eau maintiennent une température basse.
Le modèle COMSOL d'O'Shaughnessey (2014) traite cette zone comme une température imposée ; le
jumeau la représente par une conductance de contact.

**La fusion du PEKK passe par une capacité thermique apparente.** Le pic endothermique de
fusion devient une gaussienne ajoutée à la capacité thermique de base :

```
cp(T) = cp_base + (L_f / (σ_f·√(2π))) · exp[ −½·((T − Tf)/σ_f)² ]
```

avec `Tf = 337 °C` (fusion PEKK), `L_f = 130 kJ/kg` (chaleur latente) et `σ_f = ΔT_fusion /
2`. Cette approche « statistique » du pic de fusion (distribution de températures de fusion
des lamelles cristallines) suit Greco & Maffezzoli, telle que Lionetto et al. (2017, éq. 8-9)
et le jumeau 1D antérieur (Samanis et al., 2026) l'implémentent. Le degré de fusion `Xm(T)`
s'en déduit comme la fonction de répartition de cette gaussienne. C'est la grandeur qui permet
de tracer, comme dans la Figure 5 de Lionetto et al. (2017), l'évolution du degré de fusion et
le « temps à l'état fondu ».

**La méthode des lignes.** Le domaine se discrétise en espace par différences finies, ce qui
transforme l'équation aux dérivées partielles en un grand système d'équations différentielles
ordinaires en temps. Un schéma implicite BDF (adapté aux problèmes raides) intègre ce système
avec jacobien creux (`scipy.integrate.solve_ivp`, méthode `BDF`). Le jumeau 1D validé
antérieurement et la référence de procédé (Samanis et al., 2026, éq. 2-3) emploient la même
approche.

**Deux variantes de solveur coexistent** dans le code :

- Un solveur 3D (plan et épaisseur) qui résout le gradient dans l'épaisseur du stack. Il sert
  à produire les cartes d'empreinte et à étudier le gradient d'épaisseur.
- Un solveur 2D « lumpé » (le modèle de travail quotidien) qui réduit le stack à une seule
  maille dans l'épaisseur et ne résout que la température de l'interface. Une raison le
  justifie : tous les thermocouples des essais se trouvent à l'interface. Résoudre l'épaisseur
  ne servirait qu'à alimenter un écart structurel non corrigeable (le déficit de chauffe en
  surface, section 9), au prix d'un facteur environ 10 sur le temps de calcul (2 à 4 min par
  essai en 2D contre environ 30 min en 3D).

**Vérification.** Des bilans exacts couvrent le solveur thermique : équilibre sans source,
conservation de l'énergie en régime adiabatique (ΔT = ∫Q·dt / ρcp, à 10⁻⁴ près), et une
régression du modèle 3D contre le modèle 1D antérieur (colonne centrale d'une grande plaque,
écart inférieur à 1,5 °C sur les deux faces). Voir `test_thermique.py`.

---

## 4. Ce que le modèle simule, et ce qu'il laisse de côté

Le périmètre exact du jumeau se répartit en trois catégories.

**Éléments simulés explicitement :**

| Élément | Modélisation |
|---|---|
| **La bobine (coil)** | Polyligne de segments de courant ; champ par Biot–Savart. Dimensions mesurées sur la CAO du montage. |
| **Le concentrateur de flux (CFC)** | Courants images d'un demi-espace perméable (µr = 16), qui intensifient le champ sous l'empreinte. |
| **Le laminé (2 adhérents)** | Milieu conducteur homogénéisé (tenseurs σ et k) pour l'EM et la thermique ; siège de courants de Foucault et de conduction thermique. |
| **Le pli twill suscepteur** | Couche conductrice distincte à l'interface, la plus conductrice, siège principal de la chaleur. |
| **La fusion du PEKK** | Capacité thermique apparente (pic gaussien), d'où le degré de fusion. |
| **Le procédé** | 4 empreintes successives, coupure de source sur consigne de température. |

**Éléments modélisés de façon simplifiée (effectif, pas résolu) :**

| Élément | Traitement |
|---|---|
| **La céramique d'espacement** | Le modèle ne la traite pas comme un domaine de calcul. Elle reste électromagnétiquement transparente (elle fixe seulement le gap de 2 mm) et n'intervient qu'à travers la conductance de contact vers le puits thermique froid (bobine et CFC refroidis). Ce choix a un fondement physique : la céramique Pamitherm a une perméabilité négligeable et une faible conductivité, et le modèle COMSOL de référence (O'Shaughnessey, 2014) la traite de même. |
| **Le refroidissement bobine/CFC** | Un puits thermique à température imposée (20 °C) sous l'empreinte le représente. |
| **Les pertes de convection/rayonnement** | Coefficients effectifs calibrés (les valeurs de la littérature vont de 5 à 15 W/m²·K). |

**Éléments hors périmètre actuel :**

- Les pertes propres du concentrateur (chiffrées négligeables, section 3.1).
- La mécanique : pression de consolidation, squeeze-out, déformation.
- La cinétique de cristallisation au refroidissement. Le modèle traite le degré de fusion, pas
  le degré de cristallinité (une extension possible via le modèle d'Ozawa, comme chez Lionetto
  et al., 2017).
- La dépendance en température des propriétés (σ, cp restent constants ; voir la limite et la
  piste en sections 9 et 11).
- Les pertes diélectriques (négligées, conformément à O'Shaughnessey, 2014, §3.1.3).

---

## 5. Propriétés matériaux et leurs sources

Un fichier de configuration unique (`config/materiaux.yaml`) consigne toutes les propriétés,
chaque valeur portant sa source. Les valeurs marquées « incertain » entrent dans la
calibration.

**CF/PEKK (laminé homogénéisé)**

| Propriété | Valeur | Source |
|---|---|---|
| Densité | 1600 kg/m³ | CF/PEKK Solvay APC |
| Capacité thermique (hors fusion) | 1200 J/kg·K | jumeau 1D antérieur |
| Température de fusion Tf | 337 °C | PEKK Solvay APC |
| Chaleur latente de fusion L_f | 130 kJ/kg | Lionetto et al. (2017) |
| Température de transition vitreuse Tg | 159 °C | (repère) |
| Conductivité thermique, plan | 3 W/m·K (incertain) | homogénéisation quasi-iso |
| Conductivité thermique, transverse | 0,64 W/m·K | Buser (thèse Twente) |
| Conductivité électrique, sens fibre σ₀ | 2,2·10⁴ S/m | Grouve et al. (2020), Table 1 (Solvay) |
| Conductivité électrique, travers σ₉₀ | 3,4 S/m | Grouve et al. (2020), Table 1 |
| Conductivité électrique, transverse σz | 0,64 S/m | Grouve et al. (2020), Table 1 |
| Perméabilité relative µr | 1 | Grouve et al. (2020) ; Lionetto et al. (2017) |
| Émissivité | 0,96 | émissivité d'un composite carbone |

Pour la conductivité électrique de boucle du laminé quasi-isotrope, le modèle emploie la
moyenne géométrique `√(σ₀·σ₉₀)` des conductivités de pli plutôt que la moyenne arithmétique.
Une boucle de courant dans un empilement croisé a besoin d'un trajet aller et retour, donc la
conductivité effective tombe bien en dessous de la moyenne directe. Cette hypothèse
d'homogénéisation s'accorde avec la faible sensibilité à σ₉₀ que note Grouve et al. (2020) et
avec le rôle dominant du twill dans la chaleur.

**Pli twill suscepteur**

| Propriété | Valeur | Source |
|---|---|---|
| Épaisseur | environ 0,28 mm (incertain) | environ 2 CPT tissé |
| Conductivité plan σ | 1,1·10⁴ S/m (incertain) | ordre σ₀/2 (tissé équilibré) |

**Concentrateur de flux** : Ferrotron 559H, µr ≈ 16, ρ > 15 kΩ·cm (fiche Fluxtrol Inc.).

**Céramique** : Pamitherm, 2 mm, électromagnétiquement transparente ; intervient seulement via
la conductance de contact vers le puits froid.

---

## 6. Le procédé semi-statique : passes successives et asservissement

Le procédé réel n'enchaîne pas une chauffe unique. L'opérateur indexe la tête (bobine et CFC)
sur quatre empreintes successives le long des 120 mm, avec un pas de 30 mm, chaque empreinte
restant entièrement sur la zone de soudure. Le générateur coupe entre les passes le temps du
repositionnement de la table.

Le jumeau reproduit ce déroulé. Le calcul précalcule la source Joule de chaque empreinte (le
champ EM reste quasi statique à l'échelle des temps thermiques), puis l'active par morceaux
selon les fenêtres d'impulsion réelles, lues sur les courbes de thermocouples. Le masque du
puits thermique (là où le concentrateur appuie) suit l'empreinte active.

**L'asservissement sur consigne.** Dans la réalité, le générateur chauffe jusqu'à la
température de mise en œuvre, puis coupe. Le modèle reproduit cette coupure de source sur une
consigne de température à l'interface (400 °C pour les essais Série A, 360 °C pour l'essai
B-2). Cette caractéristique s'est révélée indispensable. Sans elle, appliquer le courant
pendant toute la fenêtre d'impulsion faisait diverger la température simulée (environ 1000 °C
simulés contre environ 400 °C mesurés). La fidélité au procédé a ici plus d'effet que le
réglage fin des paramètres.

---

## 7. Calibration et validation : la démarche de crédibilité

La crédibilité du jumeau tient à un principe strict : calibrer sur un seul essai, valider en
aveugle sur les autres, sans jamais y retoucher.

**Trois paramètres seulement entrent dans la calibration**, les entrées physiques mal connues :

1. `facteur_couplage`, le facteur d'échelle de la source Joule (blindage, contacts, σ) ;
2. `h_haut`, la conductance de perte vers le puits céramique/concentrateur ;
3. `h_bas_2d`, la conductance de perte vers la face opposée / le bâti.

Deux paramètres restent figés faute de mesure : `decalage_x` (position relative
bobine/montage, non mesurée) et `h_bord_x0` (puits conductif au chant bridé du montage).

**Méthode.** Un hypercube latin échantillonne l'espace des paramètres pour trouver un bon
point de départ, puis un ajustement par moindres carrés non linéaires (algorithme de
Gauss–Newton) affine la solution, avec des résidus pondérés par le bruit capteur (`σ =
écart-type(différences)/√2`). Ce pipeline reprend celui du jumeau 1D et de son test « boîte
noire » (Samanis et al., 2026).

**Résultat de la calibration** (sur l'essai A-1, modèle 2D, 5 thermocouples) :

| Paramètre | Valeur | Écart-type |
|---|---|---|
| `facteur_couplage` | 6,01 | ± 0,07 |
| `h_haut` | 30,1 W/m²·K | ± 1,3 |
| `h_bas_2d` | 37,4 W/m²·K | ± 0,5 |

Ce jeu de valeurs date du 2026-07-27. Il succède à deux recalibrations liées aux corrections
de géométrie de bobine (entraxe puis hauteur, section 9) et remplace les jeux antérieurs
(7,42 / 26,4 / 41,9 à hauteur 6,8 mm ; 4,10 / 11,3 / 51,6 en géométrie encore antérieure).
Le `h_haut` de 30 W/m²·K correspond à une conductance de contact réaliste, là où la valeur
la plus ancienne de 11 W/m²·K était artificiellement basse : les recalibrations successives
ont rendu le modèle plus juste et plus physique à mesure que la géométrie se corrigeait.

**Identifiabilité vérifiée.** Les corrélations entre paramètres restent toutes inférieures ou
égales à 0,57, sans paramètres redondants : les données déterminent chaque paramètre de façon
indépendante. Ce point compte. Le jumeau 1D antérieur avait révélé le piège inverse, deux
paramètres `f_I`/`r_I` totalement corrélés, « identifiables » avec un excellent ajustement
mais faux. Le paramètre `decalage_x` a dû rester figé pour la même raison (corrélation 0,985
avec le facteur d'échelle sur un ajustement conjoint). Cette vigilance sur l'identifiabilité
offre une garantie méthodologique forte.

---

## 8. Résultats obtenus

**Validation croisée.** θ\* calibré sur A-1 uniquement, appliqué tel quel aux essais aveugles
(maillage de validation 61 × 21, dx = dy = 2 mm) :

| Essai | Conditions | RMSE moyen | Écart de pic moyen | *(hauteur 6,8 mm, obsolète)* |
|---|---|---|---|---|
| **A-1** (calibration) | 250 A, coupure 400 °C | 36 °C | 26 °C | *37 / 15* |
| **A-3** (aveugle) | 200 A, coupure 400 °C | 32 °C | 41 °C | *32 / 28* |
| **B-2** (aveugle) | 250 A, coupure 360 °C | 65 °C | 45 °C | *66 / 35* |

Quatre enseignements se dégagent.

Le modèle transfère à un courant différent sans retouche. L'essai aveugle à 200 A (A-3)
obtient le meilleur RMSE, donc la loi en `I²` et l'asservissement sur consigne tiennent hors
du point de calibration. Ce résultat pèse le plus lourd pour la validité externe du modèle.

Les corrections de géométrie de bobine (section 9) ont convergé vers une leçon nette. La
première, l'entraxe des brins, améliorait le RMSE et divisait par trois l'écart de pic. La
seconde, la hauteur des brins ramenée à sa valeur physique de 5,0 mm, améliore encore
légèrement le RMSE mais **dégrade** l'écart de pic sur les trois essais. Cette régression
n'est pas un argument pour revenir à une cote fausse : elle établit qu'une fois la géométrie
électromagnétique correcte, le modèle concentre trop sa source, si bien que la calibration
doit en réduire l'amplitude pour tenir le RMSE, ce qui fait sous-chauffer les points
intérieurs. L'écart résiduel n'est donc plus une affaire d'échelle ni de cote, mais de forme.
Aucun paramètre effectif n'a été introduit à aucune étape.

La séquence spatio-temporelle sort correcte. Sur les courbes de validation, chaque
thermocouple devient le plus chaud à son tour, au bon moment, au passage de l'empreinte devant
lui. Le modèle suit la position de la tête.

Deux figures se comparent à la littérature. La première reproduit en semi-statique la Figure 4
de Lionetto et al. (2017) : les cartes de température à l'interface à la fin de chaque
empreinte. La seconde reprend leur Figure 5 : température et degré de fusion à l'interface,
avec un « temps à l'état fondu » mesuré de 19 s, proche des environ 19 s que Lionetto et al.
rapportent à 300 A et 2 mm/s. Ce temps de 19 s est déduit de la mesure, donc indépendant du
modèle.

Sur cette seconde figure, tracée au jeu de paramètres de référence sans aucun ajustement
propre à l'essai de chauffe, la courbe simulée sous-estime le pic d'interface au point de
mesure (environ 292 °C simulés contre 395 °C mesurés) et ne franchit donc pas la fusion. Ce
n'est pas un déficit d'énergie global : le thermocouple d'interface de cet essai est au centre
de la largeur, exactement dans le creux du profil en « M ». Au même instant, le modèle prédit
708 °C sur les bords et 292 °C au centre, tandis que la mesure au centre (395 °C, qui a fondu)
tombe entre les deux. Cette donnée ponctuelle indique que le creux central du profil en « M »
est trop prononcé — la même conclusion que la réserve du point 9(a), ici étayée par une mesure.
La figure antérieure « fondait » parce que son facteur d'échelle avait été calé sur le pic de
ce seul essai, un ajustement sur mesure désormais écarté.

Une réserve s'impose. Un RMSE de 30 à 65 °C sur une fenêtre de mise en œuvre d'environ 35 °C
signifie que le modèle ordonne et explique correctement les niveaux de température, sans encore
piloter le procédé au degré près.

---

## 9. Limites connues et questions ouvertes

La démarche a consisté à tester chaque écart, le chiffrer, et l'attribuer, plutôt qu'à
recalibrer à l'aveugle. Plusieurs pistes ont été écartées avec des chiffres, ce qui constitue
un capital de résultats négatifs documentés.

**(a) Le profil en « M », une prédiction falsifiable.** Le modèle prédit une empreinte
thermique en forme de « M » : deux lobes chauds sur les chants de l'échantillon (y = 0 et
y = 40 mm) et un creux au centre de la largeur. Le mécanisme a été démontré numériquement. La
bobine et le concentrateur débordent de la largeur de l'échantillon (section 2), le champ `Bz`
reste donc quasi uniforme sur la largeur, et les boucles de courant ne peuvent se refermer
qu'en longeant les deux bords. C'est le *transverse-flux edge effect* classique du chauffage
par induction de bandes plus étroites que l'inducteur. Le calcul confirme qu'aucun courant ne
traverse le chant (les composantes de courant normales aux bords sont exactement nulles). Ce
profil s'accorde avec l'observation : squeeze-out festonné localisé sur les chants,
recommandation COMPAAM de réduire le concentrateur pour limiter les effets de bord. Une mesure
le falsifierait directement : la cartographie bord→centre proposée au cahier de laboratoire
(une ligne de 3 à 5 thermocouples sur la largeur). Un premier point la met déjà en défaut : le
thermocouple d'interface de l'essai de chauffe se trouve au centre de la largeur et y mesure
395 °C, alors que le modèle y prédit 292 °C (creux) contre 708 °C sur les bords. Le centre réel
est donc nettement plus chaud que le creux prédit : l'amplitude du profil en « M » est
vraisemblablement surestimée, ce qui reste à confirmer par la cartographie complète.

**(b) Le « déficit structurel » était une donnée d'entrée fausse.** Ce rapport présentait
jusqu'ici un diagnostic central : le modèle concentrerait trop la puissance, avec des pics
simulés trop hauts de 40 à 60 °C, un défaut jugé structurel et non paramétrique. Ce
diagnostic était exact dans son constat et faux dans sa cause. Le fichier de configuration
géométrique supposait des brins de bobine tubulaires d'environ 9,5 mm, soit un entraxe de
19 mm. Les brins réels sont de section carrée de 6 mm, séparés d'un gap de 6,35 mm, soit un
entraxe de 12,35 mm : une erreur de 35 % sur l'entrée électromagnétique dominante. Corriger
cette cote et recalibrer ramène l'écart de pic sur l'essai de calibration de 46 à 15 °C, à
conductivité de plan physique, sans introduire de paramètre effectif. Une longue chaîne de
diagnostics (capacité thermique apparente, conductivité de plan, forme de la source
électromagnétique, puits thermique de l'outillage, blindage inter-couches, bloc céramique)
poursuivait donc un artefact d'entrée. Aucun correctif erroné n'a été inscrit dans le code :
toutes ces pistes avaient été testées à paramètres calibrés figés, en mode diagnostic. La
leçon vaut le résultat : vérifier les cotes d'entrée avant de postuler un mécanisme
manquant, et ne rien graver dans le modèle tant qu'une hypothèse n'est pas tranchée.

La même leçon s'est vérifiée une seconde fois sur la hauteur des brins au-dessus du laminé.
La valeur employée, 6,8 mm, n'avait jamais été mesurée : elle se déduisait du diamètre de
tube erroné (2 mm de céramique plus un demi-tube de 4,76 mm). La cote physique, lue sur la
photo du montage, est 5,0 mm (2 mm plus un demi-tube de 3 mm). L'appliquer et recalibrer
améliore légèrement le RMSE mais dégrade l'écart de pic — signe, cette fois, non d'une
nouvelle erreur mais du fait que la source du modèle est trop concentrée une fois la
géométrie juste. La position du concentrateur au-dessus des brins, dont dépend le traitement
électromagnétique par courants images, a par ailleurs été vérifiée sur la CAO et confirmée :
elle reste inchangée. La géométrie électromagnétique est donc désormais entièrement cadrée,
et l'écart résiduel pointe sans ambiguïté vers la forme de la source — le profil en « M » du
point (a) et le contraste spatial trop marqué qui en découle.

**(b bis) Le résidu ouvert : le régime à basse consigne.** L'essai B-2 partage la géométrie
d'A-1 ; seule sa consigne de coupure diffère (360 °C au lieu de 400). Le modèle y sous-chauffe
les capteurs situés entre deux empreintes de 30 à 55 °C. Le diagnostic est établi : en durée
pleine, sans coupure, ces points atteignent bien 530 à 560 °C, donc la chaleur les atteint si
on lui laisse le temps. Le modèle coupe la chauffe lorsque le centre de l'empreinte, le point
le plus chaud, atteint la consigne ; le procédé réel coupait vraisemblablement sur un
thermocouple d'interface plus froid, d'où des impulsions plus longues et un meilleur
étalement en longueur. À consigne haute (A-1), les impulsions sont assez longues pour que
l'écart ne se voie pas. Trois correctifs ont été prototypés, recalibrés et validés en croisé,
puis tous réfutés : déplacer le point de contrôle casse A-1 ; une marge sur la consigne
échange A-1 contre B-2, les deux essais exigeant des marges de signes opposés ; la force de
contact reste neutralisée par la régulation. La limite est assumée telle quelle. Elle se
tranchera par une mesure, celle du point de coupure réel du thermostat, plutôt que par un
modèle plus fin.

**(c) Le déficit de chauffe en surface (TC1).** Sur l'essai instrumenté en épaisseur, le
thermocouple de surface chauffe 5 à 6 fois trop lentement dans le modèle. Quatre explications
ont été testées et écartées avec des chiffres : condition limite thermique, diffusion depuis
l'interface, auto-échauffement du concentrateur (0,6 à 1,4 W, négligeable), et décalage de
position de bobine. L'origine suspectée tient à la répartition de puissance entre couches ou à
un effet de champ proche que la plaque mince ne capture pas. Aucune mesure actuelle ne
tranche, car aucun essai ne mesure la température du concentrateur lui-même.

**(d) Le champ de réaction EM, implémenté puis écarté.** Le champ de réaction (blindage) a été
implémenté rigoureusement (auto-cohérent, complexe) et vérifié par 8 tests dédiés. Son effet
propre s'est révélé petit (0,2 à 0,6 % par couche), loin de l'ordre de grandeur initialement
espéré. Il n'explique donc pas le résidu de pic. Il reste dans le code derrière une option
désactivée par défaut, pour archivage et étude ultérieure.

**(e) Artefacts numériques corrigés.** Une étude de convergence de maillage a montré que le
résidu antérieurement attribué à un thermocouple venait à 85 à 95 % d'un artefact de lecture
(interpolation au nœud le plus proche sur une grille grossière), désormais corrigé par
interpolation bilinéaire. Avec le point (b), cela fait deux des plus gros écarts du modèle
attribués à des artefacts, l'un numérique et l'autre métrologique. Tous les écarts ne sont
pas physiques : c'est le principal enseignement de méthode de ces dernières semaines.

**Autres limites assumées.** Le modèle prend les propriétés matériaux indépendantes de la
température. O'Shaughnessey (2014) et Duhovic et al. (2012) mettent en garde sur ce point ;
cela expliquerait qu'un facteur d'échelle unique ne colle pas simultanément à la montée, au
pic et à la décroissance. Le modèle laisse aussi de côté la mécanique et la cristallisation.

---

## 10. Les outils d'intelligence artificielle utilisés

Le développement du jumeau a mobilisé des outils d'IA à deux niveaux distincts : des agents IA
d'assistance au développement (ils ont aidé à écrire, vérifier et documenter le code) et une
couche IA embarquée dans le produit (une interface conversationnelle pour piloter le jumeau).
Dans les deux cas, les sources scientifiques établissent et valident la physique, les
équations et les décisions de modélisation ; les agents assistent, sans faire autorité sur la
physique.

### 10.A Agents IA d'assistance au développement

Le projet s'organise autour d'une équipe de dix agents spécialisés (fichiers
`.claude/agents/`), chacun « propriétaire » d'un module et porteur d'un mandat précis, avec sa
propre discipline méthodologique. Cette organisation garantit qu'une expertise dédiée raisonne
chaque partie du code, et que les décisions transversales restent tracées.

| Agent | Domaine de responsabilité |
|---|---|
| **induction-em-engineer** | Électromagnétisme : Biot–Savart, courants de Foucault en plaque mince, effet de peau, concentrateur, source Joule (modules `em/`). |
| **thermal-solver-engineer** | Solveur thermique transitoire : méthode des lignes, intégration BDF, jacobien creux, cp apparent, conditions aux limites (module `thermique/`). |
| **cf-pekk-thermoplastic-specialist** | Thermophysique du CF/PEKK : conductivités homogénéisées, fusion/cristallisation, twill suscepteur, sourçage de chaque propriété (module `materiaux.py`). |
| **calibration-uq-specialist** | Problème inverse : LHS, moindres carrés pondérés, identifiabilité, quantification d'incertitude (module `identification/`). Porteur de la règle « ne jamais calibrer fréquence et facteur d'échelle ensemble ». |
| **validation-data-engineer** | Données expérimentales : ingestion des thermocouples (CSV/TXT LabVIEW), nettoyage des aberrants, modèle de bruit, confrontation modèle↔mesure (module `validation/`). |
| **simulation-verification-engineer** | Vérification : bilans de conservation, benchmarks analytiques, solutions manufacturées, tests de régression (dossier `tests/`). |
| **scientific-python-reviewer** | Revue de code : vectorisation NumPy, matrices creuses, stabilité numérique, performance ; transverse à tout `src/jumeau/`. |
| **composites-engineer** | Ingénierie des composites FRP : micromécanique des plis, théorie des stratifiés, physique de mise en œuvre. |
| **matagent** | Pilote du framework MatAgent (informatique des matériaux) : prédiction de propriétés, revue de littérature, analyse de données. |
| **matclaw-solver** | Pilote de calculs de science des matériaux (DFT, MD, MC), disponible pour des besoins ponctuels de propriétés. |

Ces agents fonctionnent sous contrôle humain. Ils proposent, chiffrent et documentent, et
chaque décision de modélisation reste tracée à une source et validée. La rigueur de la
démarche (résultats négatifs chiffrés, vérifications analytiques, tests de non-régression)
découle de cette organisation.

Une suite d'agents dédiée à la recherche documentaire (« Academic Research Skills », ARS) a
produit la section d'état de l'art (`docs/etat_art_induction.md`) : un corpus de 13 sources
vérifiées, chaque affirmation attribuée, sans référence hors corpus vérifié, avec vérification
de l'existence réelle des citations (protection contre les citations hallucinées). Cette suite
comprend des modes de revue de littérature, de vérification des faits, et de revue par les
pairs simulée.

### 10.B Couche IA embarquée dans le produit

Une surcouche conversationnelle (dossier `ai_framework/`) s'ajoute par-dessus le solveur
physique, sans le modifier, selon une architecture multi-agents inspirée du framework MatAgent
(Purdue). Ses caractéristiques :

- **100 % locale.** Le modèle de langage tourne sur la machine (via Ollama), sans aucun appel
  réseau externe ni clé API. Les données du projet restent sur le poste.
- **Trois outils orchestrés.** Générer une configuration d'essai, lancer la simulation, tracer
  les résultats. L'utilisateur formule sa demande en langage naturel et l'orchestrateur
  enchaîne les étapes.
- **Vérifications physiques embarquées.** Le système contrôle les bornes physiques des
  paramètres avant tout calcul ; un rejet remonte à l'orchestrateur qui corrige.
- **Auto-correction.** Si un outil renvoie une erreur, le modèle la lit et rappelle l'outil
  avec des paramètres corrigés.

Cette couche reste un démonstrateur exploratoire. Elle abaisse la barrière d'usage du jumeau
et préfigure un pilotage assisté, sans constituer un résultat scientifique en soi.

---

## 11. Perspectives : mesures et modélisation à venir

Le modèle pose désormais des questions expérimentales précises. La priorité passe autant par
la mesure que par le code.

**Mesures discriminantes (par rapport valeur/effort décroissant) :**

1. **Cartographie bord→centre.** Une ligne de 3 à 5 thermocouples sur la largeur de 40 mm, à
   l'interface. Cette mesure tranche le profil en « M » : le modèle prédit bord chaud / centre
   froid. Le cahier de laboratoire la décrit déjà.
2. **Température du concentrateur.** Un thermocouple ou une caméra infrarouge sur sa face
   active pendant une chauffe. Seule mesure capable d'attaquer le déficit de surface (TC1).
3. **Relevé métrologique complet de la tête.** Position relative bobine / concentrateur /
   thermocouples, en particulier le décalage longitudinal `decalage_x`, aujourd'hui figé
   faute de mesure. Les cotes de section, d'entraxe et de hauteur des brins ont, elles, déjà
   été corrigées à partir de la CAO et de la photo du montage (section 9) ; un relevé au pied
   à coulisse les confirmerait et refermerait définitivement le sujet géométrie.
4. **Point de coupure réel du thermostat.** Quel capteur pilotait l'arrêt de chauffe, et à
   quelle position. Cette information tranche le résidu à basse consigne, section 9(b bis).

**Développements de modélisation (par priorité) :**

1. **Adoucissement du profil en « M » en largeur.** Un diagnostic du 27 juillet a localisé la
   source de l'écart de pic résiduel : le champ magnétique est déjà uniforme sur la largeur,
   et le profil en « M » naît entièrement de l'écrasement du courant de Foucault contre les
   chants libres, où le modèle de plaque mince impose un courant nul. Ce constat réoriente le
   développement. Le modèle de concentrateur fini, un temps envisagé comme correctif
   principal, agit sur la répartition du champ ; il ne corrigera donc pas ce « M » en largeur
   (il vaut pour le profil en longueur). Les mécanismes qui adouciraient le contraste
   bord/centre sont les courants de retour dans l'épaisseur près des chants et la résistance
   de contact du tissu tissé, absents du modèle de nappe continue idéalisée. Aucun ne se
   calibre sans la cartographie bord→centre : cette mesure conditionne ce développement, d'où
   sa priorité expérimentale (section perspectives, mesures).
2. **Propriétés dépendantes de la température** σ(T), cp(T). O'Shaughnessey (2014) et Duhovic
   et al. (2012) le recommandent explicitement ; cela expliquerait qu'un facteur unique ne
   colle pas simultanément à la montée, au pic et à la décroissance.
3. **Cinétique de cristallisation** (modèle d'Ozawa, comme chez Lionetto et al., 2017) pour
   compléter la Figure 5 avec le degré de cristallinité au refroidissement, un critère de
   qualité de joint.

**Horizon.** Le simulateur actuel forme déjà le modèle de procédé (« plant model ») d'une
future boucle de contrôle prédictif. Il lui manque la fidélité spatiale (point 1 ci-dessus),
pas l'architecture. Le coût de calcul (2 à 4 min par essai) constitue un verrou pour le temps
réel, à lever par un modèle réduit.

---

## 12. Bibliographie

Les sources ci-dessous sont celles effectivement mobilisées dans la modélisation (fichiers de
configuration, docstrings du code, section d'état de l'art vérifiée). La section d'état de
l'art complète (`docs/etat_art_induction.md`) contient le corpus vérifié de 13 sources avec
attribution systématique.

**Modélisation électro-thermique du soudage par induction**

- **Lin, W. (1993).** *Induction heating model of graphite fiber/thermoplastic matrix
  composites.* Modèle par différences finies 2D des courants de Foucault sous une bobine de
  forme quelconque ; hypothèse de plaque mince ; courants portés par les fibres. Source du
  maillon « courants de Foucault » (section 3.2).
- **Lionetto, F., Pappadà, S., Buccoliero, G., & Maffezzoli, A. (2017).** *Finite element
  modeling of continuous induction welding of thermoplastic matrix composites.* Materials &
  Design, 120, 212–221. Modèle FE 3D couplant électromagnétisme et transfert thermique avec
  fusion et cristallisation. Référence des Figures 4 et 5 reproduites ; source du degré de
  fusion et de la chaleur latente.
- **O'Shaughnessey, P. G. (2014).** *Modélisation et investigation expérimentale du soudage
  par induction de composites thermoplastiques.* Mémoire, ÉTS (même laboratoire). Modèle
  COMSOL 3D avec élément chauffant à l'interface et concentrateur de flux ; homogénéisation ;
  analyse de sensibilité (courant, fréquence, distance, conductivité). Source des conditions
  aux limites thermiques, de l'homogénéisation, et de la prise en compte du concentrateur.
- **Duhovic, M., et al. (2012).** Comparaison de modèles (COMSOL / LS-DYNA) du chauffage par
  induction de CF/PEEK ; profondeur de peau, règles de maillage, coefficients de convection,
  importance de la dépendance en température de la conductivité électrique. Source de la
  justification du régime plaque mince et de la mise en garde sur σ(T).
- **Grouve, W., et al. (2020).** *Induction heating of cross-ply C/PEKK laminates.* Modèle
  COMSOL ; tenseur de conductivité électrique anisotrope mesuré ; µr = 1 ; coefficient de
  convection. Source des conductivités électriques du laminé (Table 1).
- **Samanis, et al. (2026).** *Digital Twin for the control of induction cure in composites
  manufacturing.* Méthode des lignes 1D, identification LHS et moindres carrés, test de
  vérification « boîte noire ». Source du pipeline de calibration et de la structure du solveur
  transitoire.

**Mécanismes de chauffe et architecture des composites**

- **Fink, B. K., McCullough, R. L., & Gillespie, J. W. (1992).** Théorie « locale » de la
  dissipation par induction : conduction le long des fibres, résistance des jonctions, pertes
  diélectriques. Cadre d'interprétation de l'origine de la chaleur.
- **Bayerl, T., Duhovic, M., Mitschang, P., & Bhattacharyya, D. (2014).** Revue des mécanismes
  de chauffe par induction des CFRTP. Contexte général du procédé.
- **van den Berg, Luckabauer, Wijskamp, & Akkerman (2024).** Étude expérimentale du chauffage
  par induction d'un renfort tissé (fabric) à conductivité anisotrope. Justification du rôle du
  twill (référence la plus proche du montage).
- **Martin, R., et al. (2024), travaux COMPAAM.** Recommandation de dimensionnement du
  concentrateur (plus étroit que la zone de soudure pour limiter les effets de bord). Source du
  dimensionnement du CFC.

**Propriétés matériaux**

- **Fluxtrol Inc.** *Ferrotron 559H* datasheet. µi = 16, ρ > 15 kΩ·cm, courbe de pertes
  `Pv = 4,1·f^{1,1}·B^{2,5}`. Source des propriétés du concentrateur et du chiffrage de son
  auto-échauffement.
- **Buser** (thèse Twente) et **Solvay APC** (fiche PEKK-FC). Conductivité transverse du
  laminé, densité, températures caractéristiques.

**Filiation du banc expérimental**

- **Côté (2018).** Description du banc de soudage par induction du laboratoire (bobine hairpin,
  générateur Ambrell, vérin pneumatique) et ajout de la table à motion linéaire. Filiation
  O'Shaughnessey (2014) → Côté (2018) → présents travaux.

---

## 13. Annexes

### Annexe A. Nomenclature

| Symbole | Grandeur | Unité |
|---|---|---|
| `B`, `Bz` | Champ magnétique (valeur efficace) | T |
| `I` | Courant de bobine | A |
| `f`, `ω = 2πf` | Fréquence / pulsation | Hz / rad·s⁻¹ |
| `µ₀`, `µr` | Perméabilité du vide / relative | H·m⁻¹ / — |
| `σ`, `ρ = 1/σ` | Conductivité / résistivité électrique | S·m⁻¹ / Ω·m |
| `δ = √(2ρ/µ₀ω)` | Profondeur de peau | m |
| `ψ`, `J` | Fonction de courant / densité de courant | A·m⁻¹ / A·m⁻² |
| `q`, `Q` | Puissance Joule surfacique / volumique | W·m⁻² / W·m⁻³ |
| `T`, `Tf`, `Tg` | Température / fusion / transition vitreuse | °C |
| `cp`, `L_f` | Capacité thermique / chaleur latente | J·kg⁻¹·K⁻¹ / J·kg⁻¹ |
| `k` | Conductivité thermique | W·m⁻¹·K⁻¹ |
| `h` | Coefficient de perte (convection/contact) | W·m⁻²·K⁻¹ |
| `Xm` | Degré de fusion | — |
| `η = (µr−1)/(µr+1)` | Coefficient de courant image du concentrateur | — |

### Annexe B. Structure logicielle

```
Jumeau_Soudage_Induction/
├── config/
│   ├── materiaux.yaml       ← toutes les propriétés, avec source
│   ├── geometrie.yaml       ← bobine, CFC, laminé, empreintes
│   └── essais/*.yaml        ← un fichier par campagne d'essai
├── src/jumeau/
│   ├── em/                  ← maillons 1-2-3 : champ, Foucault, source Joule
│   │   ├── champ_coil.py    ← Biot–Savart + courants images du CFC
│   │   ├── foucault.py      ← fonction de courant ψ (plaque mince)
│   │   └── source_joule.py  ← assemblage Q(x,y,z) par couche
│   ├── thermique/           ← maillon 4 : transfert thermique
│   │   ├── solveur3d.py     ← plan + épaisseur (cartes, gradient)
│   │   └── solveur2d.py     ← lumpé à l'interface (modèle de travail)
│   ├── materiaux.py         ← propriétés, cp apparent, degré de fusion
│   ├── geometrie.py         ← construction de la scène et des couches
│   ├── procede.py           ← 4 empreintes + asservissement sur consigne
│   ├── identification/      ← calibration LHS + moindres carrés
│   └── validation/          ← ingestion mesures + métriques
├── scripts/                 ← simuler / calibrer / valider / figures
├── tests/                   ← 34 tests (analytiques, conservation, régression)
├── ai_framework/            ← couche IA conversationnelle locale (démonstrateur)
└── docs/                    ← état de l'art, rapports
```

### Annexe C. Reproductibilité

```bash
# Environnement
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                       # 34 tests, environ 3 min

# Calibration (essai A-1)
python scripts/calibrer.py --modele 2D --essai serieA_A-1 --n-lhs 25 --figer-decalage-x 0

# Validation croisée (paramètres calibrés, sans recalibrage)
python scripts/valider.py --modele 2D --facteur 6.0123 --decalage-x 0 \
    --h-haut 30.087 --h-bas-2d 37.424 --h-bord-x0 250

# Figures type Lionetto (modèle 2D, cohérent avec la validation)
python scripts/figure_empreinte.py config/essais/serieA_A-1.yaml --modele 2D \
    --facteur 6.0123 --decalage-x 0 --h-haut 30.087 --h-bas-2d 37.424 --h-bord-x0 250 \
    --tmax-couleur 480 --suffixe _plafonne          # Fig. 4 (empreinte)
python scripts/figure_fusion.py config/essais/chauffe_250A_3TC.yaml --modele 2D \
    --facteur 6.0123 --decalage-x 0 --h-haut 30.087 --h-bas-2d 37.424 --h-bord-x0 250  # Fig. 5
```

Ces paramètres supposent la géométrie corrigée (`config/geometrie.yaml` :
`entraxe_jambes: 0.01235`, `rayon_tube: 0.003`, `hauteur: 0.005`). Les journaux antérieurs
aux corrections de géométrie, et les valeurs de paramètres qu'ils contiennent, se rapportent
à une géométrie antérieure : leurs raisonnements restent valides, leurs chiffres non.

Chaque exécution se journalise dans `journaux/` (`journaux/resultats_*.log`), et les figures
s'écrivent dans `resultats/`. Journaux de référence pour l'état courant :
`journaux/resultats_hauteur_5mm_recalibration.log` (correction de hauteur et recalibration courante),
`journaux/resultats_geometrie_corrigee_recalibration.log` (correction d'entraxe, étape précédente),
`journaux/resultats_diag_hauteur_bobine.log` (diagnostic hauteur + plan image du CFC vérifié sur CAO),
`journaux/resultats_validation_reference_figures.log` (validation au jeu de paramètres courant) et
`journaux/resultats_diag_b2_longueur.log` (résidu à basse consigne et correctifs réfutés).

---

*Document rédigé avec l'assistance d'agents IA sous contrôle humain. Chaque affirmation
physique renvoie à une source scientifique référencée en section 12. Les données
expérimentales proviennent du vault de recherche du projet (`Memoire_Soudage_Induction`), qui
reste la source de vérité.*
