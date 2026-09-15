<!--
SOURCE DE VÉRITÉ du corps de l'issue GitHub #70.
Éditer CE fichier, puis : .venv/bin/python code/scripts/gen/sync_issue.py 70
Ne pas éditer l'issue directement dans le navigateur : la prochaine synchro
écraserait la modification sans avertir.
Ce commentaire HTML est invisible dans l'issue rendue.
-->
> ### En bref
>
> **Le concentrateur sert la puissance, pas l'uniformité.** Le contraste bord/centre vaut déjà **2,40 sans aucun MFC** ; le MFC 55 mm le porte à **2,77**. Raccourcir le bloc à 31,75 mm retire de l'amplification, pas la cause — l'effet de bord vient de la **plaque**, pas du concentrateur.
> Le bénéfice réel et robuste est ailleurs : le chant passe de **322 °C à 175 °C (famille A) ou 220 °C (famille B)**.
> Deux familles de modèle s'opposent sur le devenir du flux supprimé : contraste **1,03 (A)** contre **2,49 (B)**.
> **Ce que la campagne tranche :** la date du maximum au TC1. **~7 s après la coupure** → le flux se reconcentre (A) ; **à la coupure** → il ne se reconcentre pas (B). Ce discriminant ne dépend ni de θ\*, ni de la calibration.
> À 200 A, **aucune configuration n'atteint la fusion** (337 °C).

---

## Objectif — des prédictions figées, avant la moindre mesure

**Prédire, avant la campagne, ce que le MFC raccourci (31,75 mm) va donner** — comparé au MFC du banc (55 mm, plus large que l'échantillon) et au cas **Sans MFC**. Les prédictions ci-dessous sont figées : elles servent de held-out aux mesures de #55, #56 et #58.

- **Condition simulée :** **200 A, 18 s**, spot fixe `x = 60 mm`, 5 TC d'interface à `y = 0/10/20/30/40 mm` — exactement `exp7_200A`, la condition que #55 mesurera.
- **Modèle :** 2D, θ\* = 6,0123 (non recalibré pour les géométries réduites).
- **Reproduire :** `.venv/bin/python code/scripts/gen/gen_mfc_comparaison_figures.py`

---

## 1. Le champ EM — le bloc canalise le flux, mais l'image ne « voit » pas sa longueur

Trois configurations, même échelle.

- **Coupe latérale :** lignes de champ autour des deux brins du hairpin (× et • = sens du courant), bloc MFC en gris, laminé coloré par la puissance Joule induite.
- **Vue de dessus :** l'empreinte de chauffe, avec le contour du MFC en cyan.

**Sans MFC** — le champ se referme librement des deux côtés.

![Champ EM sans MFC](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/modele/figures/fig_champ_em_1_bobine_seule.png?v=3)

*Sans concentrateur, les lignes de champ se referment librement de part et d'autre des deux brins du hairpin.*

**Avec MFC (55mm x 31,5mm)** — le bloc canalise le flux vers le bas. Noter qu'il **déborde largement de l'échantillon** (contour cyan, 55 mm contre 40 mm de largeur) : c'est le « MFC trop grand ».

![Champ EM avec MFC 55 mm](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/modele/figures/fig_champ_em_2_mfc_actuel.png?v=3)

*Le bloc gris canalise le flux vers le bas ; le contour cyan déborde de l'échantillon, 55 mm contre 40 mm de largeur.*

**Avec MFC (31,75mm x 31,5mm)** — contenu dans la largeur de l'échantillon.

![Champ EM avec MFC réduit](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/modele/figures/fig_champ_em_3_mfc_reduit.png?v=3)

*Même vue avec le bloc raccourci : le contour cyan est cette fois contenu dans la largeur de l'échantillon.*

⚠️ **Réserve sur ces trois vues** : la méthode des images ne dépend que de µ_r et d'un plan infini. Le champ tracé est donc **identique** entre les configurations 2 et 3 — seule l'empreinte change. C'est précisément la limite que le reste de cette issue lève, par deux troncatures de l'image au niveau du champ (§6).

Sur la vue de dessus, la **bande sombre au centre** de l'empreinte est la ligne nodale de dissipation : j'y reviens au §2 bis.

## 2. À la source — le MFC amplifie le profil en M, il ne le crée pas

![Puissance déposée en largeur](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/modele/figures/fig_mfc_cmp_1_puissance.png?v=3)

*Puissance déposée en largeur : le creux central est présent dans toutes les configurations, et la courbe orange culmine à 375 kW/m² avant de tomber à zéro net au bord de l'empreinte.*

La puissance déposée creuse au centre dans **toutes** les configurations : c'est le profil en M, et il vient de l'écrasement des courants de Foucault aux bords libres de la plaque (`ψ = 0`), **pas** du concentrateur. Le MFC ne crée pas le M, il l'amplifie.

Noter la courbe orange : un pic à 375 kW/m² puis **un zéro brutal** au bord de l'empreinte. Cette discontinuité est un artefact du modèle de masque, pas de la physique — j'y reviens au §5.

## 2 bis. Puissance Joule — le twill porte tout, et le centre exact est une ligne nodale

![Source sans MFC](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/modele/figures/fig_mfc_cmp_5a_sans_mfc.png?v=3)

![Source MFC 55 mm](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/modele/figures/fig_mfc_cmp_5b_mfc_55.png?v=3)

![Source MFC réduit A](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/modele/figures/fig_mfc_cmp_5c_reduit_A.png?v=3)

![Source MFC réduit B](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/modele/figures/fig_mfc_cmp_5d_reduit_B.png?v=3)

*Échelle de couleur commune aux quatre (0–430 kW/m²).*

Le pendant « source » des cartes thermiques. **Sous A, la source est littéralement un rectangle à bords francs** — l'artefact du masque se voit à l'œil nu. Les trois autres montrent deux lobes séparés par une bande sombre au centre, sur laquelle je reviens juste en dessous.

![Puissance Joule dans l'épaisseur](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/modele/figures/fig_mfc_cmp_6_joule_epaisseur.png?v=3)

*Dans l'épaisseur, le pic à l'interface de soudure écrase la surface et le fond, et la hiérarchie entre configurations reste la même à toutes les profondeurs.*

**Le twill suscepteur porte toute l'affaire.** À l'interface de soudure, la puissance volumique atteint 455 MW/m³ contre 59 en surface et 13 en fond de laminé — soit ~8× son voisinage immédiat et ~35× le fond. C'est lui qui fait que l'**interface** chauffe et non la surface, malgré une bobine posée sur la face supérieure. La hiérarchie entre configurations est la même à toutes les profondeurs : le MFC multiplie, il ne redistribue pas dans l'épaisseur.

### Un résultat qui n'était sur aucune figure du dépôt

**Au centre exact de la largeur (`y` = 20 mm), la puissance induite est nulle — à la précision machine.** Pas faible : `4 × 10⁻²⁸` kW/m² contre `4,3 × 10²` au chant. C'est une **ligne nodale** de la dissipation, visible comme la bande sombre au milieu de chaque carte ci-dessus.

Conséquence directe : **le centre de la largeur ne chauffe que par conduction latérale** depuis les lobes. Cela explique d'un seul coup deux choses :

- pourquoi le centre n'atteint jamais la fusion dans aucune configuration ;
- pourquoi c'est `k_plan` — et non la source — qui gouverne sa température.

Le résidu d'étalement in-plane du projet trouve ici son origine géométrique.

⚠️ C'est aussi pourquoi **aucune** géométrie de concentrateur ne peut, à elle seule, souder le centre : déplacer ou rétrécir le MFC ne déplace pas la ligne nodale, qui tient aux bords libres de la plaque.

## 3. Profil en largeur — le MFC sert la puissance, pas l'uniformité

![Profil T(y)](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/modele/figures/fig_mfc_cmp_2_profils.png?v=3)

*Profils T(y) prédits : seule la configuration A relève le centre et déplace son maximum hors du chant.*

Températures en °C.

| configuration | TC1 (y=0) | TC2 | TC3 (centre) | TC4 | TC5 (y=40) | contraste bord/centre | pic réel |
|---|---|---|---|---|---|---|---|
| **Sans MFC** | 154 | 83 | 64 | 83 | 154 | 2,40 | 154 °C au chant |
| **Avec MFC (55mm x 31,5mm)** | 322 | 162 | 116 | 162 | 322 | 2,77 | 322 °C au chant |
| **Avec MFC (31,75mm x 31,5mm) A** | 175 | 213 | 169 | 213 | 175 | 1,03 | **240 °C à y = 5 mm** |
| **Avec MFC (31,75mm x 31,5mm) B** | 220 | 116 | 89 | 116 | 220 | 2,49 | 220 °C au chant |

**Premier résultat, contre-intuitif : le MFC sert la puissance, pas l'uniformité.** Il double la température au chant (154 → 322 °C) tout en **aggravant** le contraste (2,40 → 2,77).

⚠️ Le « contraste bord/centre » **ne mesure pas ce que son nom dit pour la configuration A**, dont le maximum a migré à `y = 5 mm` : 1,03 au chant, mais 1,42 au pic réel. Comparer les configurations sur ce seul ratio induit en erreur.

## 4. Empreinte thermique — une zone continue sur toute la largeur (A) contre deux lobes (toutes les autres)

![Empreinte sans MFC](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/modele/figures/fig_mfc_cmp_3a_sans_mfc.png?v=3)

![Empreinte MFC 55 mm](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/modele/figures/fig_mfc_cmp_3b_mfc_55.png?v=3)

![Empreinte MFC réduit, famille A](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/modele/figures/fig_mfc_cmp_3c_reduit_A.png?v=3)

![Empreinte MFC réduit, famille B](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/modele/figures/fig_mfc_cmp_3d_reduit_B.png?v=3)

*Échelle de couleur commune aux quatre (20–322 °C) : des échelles propres à chaque image les rendraient plus contrastées mais non comparables.*

La différence est **topologique**, pas graduelle : A produit **une zone chaude continue sur toute la largeur**, toutes les autres produisent **deux lobes séparés aux chants**. C'est reconnaissable au premier coup d'œil sur une thermographie.

À 200 A, **aucune configuration n'atteint la fusion** (337 °C). Le MFC raccourci ne « débloque » donc pas le soudage du centre à ce courant — c'est la question de #56 à 250 A.

## 5. Dynamique — le retard du pic au TC1, discriminant le plus franc

![Cycles temporels](https://raw.githubusercontent.com/maxencesoixante/Jumeau_Soudage_Induction/main/biblio/modele/figures/fig_mfc_cmp_4_cycles.png?v=3)

*Cycles temporels : sous A, le maximum au chant arrive nettement après la coupure du courant, alors que les autres configurations culminent à la coupure.*

**C'est la prédiction la plus exploitable de cette issue.** Sous la configuration A, le chant est *hors* de l'empreinte du concentrateur : il ne reçoit aucune puissance directe et ne chauffe que par conduction latérale. Son pic arrive donc **~7 s après la coupure du courant**, quand toutes les autres configurations culminent à la coupure.

**Un décalage temporel ne dépend ni de θ\*, ni du niveau absolu, ni de la calibration.** Là où le rapport de contraste peut être brouillé par un couplage mal calé, la date du maximum au TC1 est une observation quasi brute.

---

## 6. A contre B — le flux manquant se reconcentre-t-il ?

A et B ne diffèrent pas par leur finesse mais par une **hypothèse physique sur le devenir du flux** que le raccourcissement supprime :

| | mécanisme | affirmation |
|---|---|---|
| **A** — masque d'empreinte, puissance conservée | la puissance totale est redistribuée sur l'empreinte restante | le flux manquant **se reconcentre** |
| **B** — image tronquée | seule la contribution image est pondérée ; le champ de la bobine nue reste entier | le flux **ne se reconcentre pas**, on retombe au cas sans MFC |

Deux façons indépendantes de tronquer l'image — pondérer l'observateur, ou pondérer la source — donnent 2,62 et 2,49. **A est l'intrus, pas un troisième point de la même famille.** Robuste aussi à la marge d'adoucissement : sur un facteur 4 (6→24 mm), B reste dans 2,48–2,68.

Détail : `prediction_mfc_familles.md`. Prédiction figée antérieure, non réécrite : `prediction_mfc_reduit.md`.

---

## 7. COMPAAM — bords plus froids confirmés, mécanisme contesté

La recommandation (Romain Martin, mai 2025, cf. #63) enchaîne quatre maillons :

1. *un concentrateur ~½ pouce plus étroit que la largeur de soudure* →
2. **limite les effets de bord** →
3. **chauffe homogène** →
4. **réduit la déconsolidation**.

Attendus annoncés : dépôt central, bords plus froids, moins de squeeze-out latéral.

Le modèle ne valide pas cette chaîne en bloc. Il en confirme une moitié et en conteste l'autre — et surtout, il conteste le **mécanisme** invoqué.

| attendu COMPAAM | verdict du modèle | détail |
|---|---|---|
| **bords plus froids** | ✅ **confirmé par les deux familles** | 322 → 175 °C (A) ou 220 °C (B) au chant |
| **moins de squeeze-out latéral** | ✅ **plausible**, découle des bords plus froids | mais jamais vérifié expérimentalement — c'est #57 |
| **chauffe homogène** | ⚠️ **dépend entièrement de la famille** | contraste 1,03 (A) contre 2,49 (B), pour 2,77 au départ |
| **dépôt central** | ❌ **impossible au sens strict** | au centre exact, la puissance induite est **nulle** quelle que soit la géométrie |
| **« limite les effets de bord »** *(le mécanisme)* | ❌ **mal attribué** | l'effet de bord vient de la **plaque**, pas du concentrateur |

### Le point de désaccord qui compte

**L'effet de bord n'est pas créé par le MFC.** Sans aucun concentrateur, le contraste bord/centre vaut déjà **2,40** ; le MFC 55 mm le porte à 2,77. Le concentrateur ne contribue donc que **0,37 de contraste sur 2,77** — les 2,40 restants sont une propriété géométrique de la plaque (annulation du courant de Foucault à ses bords libres), qu'**aucune géométrie de concentrateur ne peut retirer**.

Raccourcir le MFC retire de l'**amplification**, pas la **cause**. C'est pourquoi la borne basse atteignable en rétrécissant le concentrateur est le cas « sans MFC » — contraste 2,40 — et non un profil plat. La famille B le dit explicitement : 2,49, c'est-à-dire presque le cas sans MFC. Seule la famille A prédit mieux, et seulement parce qu'elle suppose que le flux manquant se reconcentre (§6).

### Ce qui reste solide dans la recommandation

Le bénéfice le plus tangible n'est pas l'homogénéité mais **la baisse de température aux chants** — 100 à 150 °C selon la famille — précisément là où le squeeze-out se produit. Les deux familles s'accordent sur ce point. Si la déconsolidation est pilotée par la température maximale atteinte au bord plutôt que par l'uniformité du profil, la recommandation tient, mais **par un autre mécanisme que celui invoqué**.

Ce déplacement d'explication est testable : #57 (squeeze-out) et #55 (profil) mesurent deux choses différentes, et la recommandation prédit que les deux s'améliorent ensemble. Le modèle prédit que **seule la première** s'améliore franchement.

### Réserve

Rien de ce qui précède ne repose sur une mesure : les trois modèles de MFC sont de 1er ordre (§9), et l'attendu « moins de déconsolidation » n'a **jamais** été vérifié sur ce banc. Le désaccord porte sur des prédictions, pas sur des résultats — c'est la campagne qui tranche.

## 8. Énoncés réfutables — ce que la campagne peut invalider

1. **Le MFC aggrave le contraste au lieu de l'améliorer.** Réfuté si le contraste mesuré sans MFC dépasse celui à 55 mm.
2. **Le pic au TC1 arrive après la coupure, ou non.** Après → le flux se reconcentre (famille A). À la coupure → il ne se reconcentre pas (famille B). *Le discriminant le plus robuste.*
3. **Le contraste mesuré du MFC réduit tombe vers 1,0 (A) ou reste vers 2,5 (B).**
4. **Le maximum quitte le chant, ou non.** A le déplace à `y ≈ 5 mm` ; B le laisse au chant.
5. **À 200 A, rien n'atteint la fusion**, quelle que soit la configuration.

## 9. Limites — à lire avant d'utiliser un chiffre

- Les trois modèles de MFC sont des approximations de **1er ordre**. **Aucun ne résout le bloc de ferrite fini.** Jusqu'à ce travail, la méthode des images traitait le concentrateur comme un demi-espace **infini** : le champ était rigoureusement identique entre 55 et 31,75 mm.
- Le masque (A) est un rectangle dur sans frange : ses valeurs **aux chants** sont les moins crédibles, alors que ce sont elles qui portent le plus grand écart.
- θ\* n'est recalibré pour **aucune** géométrie réduite — c'est l'objet de #60, après mesure.
- **Aucune source du corpus documentaire ne fait varier la longueur d'un concentrateur.** Mohan 2022, longtemps attendue comme la référence décisive, teste la *présence/absence* d'un concentrateur et la position de la bobine — pas sa longueur, sur un Fluxtrol 50 µr = 45 (≠ Ferrotron 559H µr = 16), et sans validation expérimentale. **Il n'existe aucun appui bibliographique externe à ces prédictions.**
- Le modèle 2D est exactement symétrique en `y`, alors que la mesure ne l'est pas (sur `exp7_200A` : TC2 = 216 contre TC4 = 179 °C). Comparer de préférence les moyennes appariées (TC1,TC5) et (TC2,TC4).

## Liens

Campagne #55 (profil en largeur) · #56 (fusion au centre à 250 A) · #58 (fenêtre de soudage) · #60 (recalibration θ\*) · #63 (comparatif COMPAAM). Lève la condition de réouverture (a) de #39.




