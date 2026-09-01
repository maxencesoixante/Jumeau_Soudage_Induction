# Thermographie plein-champ sur plaque CF/PEKK découplée — imager la SOURCE et l'étalement longitudinal hors-spot

**Issue GitHub** : #69 (créée le 2026-09-01). Ce fichier = protocole de référence.
**Labels** : `labo`, `modele`, `residu`, `statut: à faire`
**Relié à** : #68 (résidu structurel `k_plan` / étalement in-plane), #15 (thermographie FLIR A700), #59 (empreinte IR plein champ MFC). **Ne double PAS** #15/#59 : voir « Positionnement ».
**Chaîne de rejeu VALIDÉE** : `code/scripts/thermographie_virtuelle.py` (auto-test aller-retour Δ=0 sur exp7_200A le 2026-09-01 ; génère aussi le format CSV cible via `demo`).

---

## 1. Contexte & positionnement

L'issue #68 a clos l'« arc modèle » : le résidu du jumeau se réduit à un **étalement de chaleur
dans le plan trop lent**, piloté par un `k_plan` **scalaire** qui ne peut être simultanément bas
sous le spot et haut hors-spot. La **répartition en largeur** (profil en M) est déjà **mesurée et
validée** par 5 TC noyés (exp7, contraste 2,17 ≈ 2,43 modèle). Ce qui reste **ouvert** :

- le **transitoire longitudinal hors-spot** (dissipation en x, −67 % en dT/dt) ;
- la **forme réelle de la source** (dépôt Joule), aujourd'hui seulement *calibrée* via
  `facteur_couplage`, jamais *mesurée* — désigné en mémoire comme le seul levier neuf restant
  (précédent van den Berg 2024 : six-probe + FLIR A65).

**Ce qui distingue cette issue de #15 / #59.** #15 vise la température du concentrateur MFC + le
champ de surface *en configuration de soudage* ; #59 compare deux tailles de MFC. Ici : une plaque
**suspendue, découplée** (pas de céramique, pas de pression, pas d'empilement) filmée sur la face
**opposée au MFC**. Le but n'est pas le procédé mais **d'isoler la source + la conduction in-plane**
des paramètres de contact/consolidation, et de produire des données **plein-champ 2D** (pas 5 points)
que le jumeau peut **rejouer point par point**.

## 2. Objectif (ce que ça apporte de neuf)

1. **Imager la source** : sur une plaque nue, l'empreinte thermique précoce (avant que la conduction
   n'ait tout étalé, ~premières secondes) est le dépôt Joule quasi-brut → test direct de la forme de
   source (le M vient *entièrement* de l'écrasement du courant de Foucault au chant, cf. mémoire).
2. **Mesurer la longueur d'étalement longitudinal** : le profil en x hors-spot décroît avec une
   longueur caractéristique fixée par `k_plan`. `k_plan = 3,0` (physique) vs ≈ 7,5 (effectif) donnent
   des longueurs de décroissance **mesurablement différentes** → la caméra tranche.
3. **Test 2D de l'hypothèse scalaire** : un `k_plan` scalaire peut-il ajuster EN MÊME TEMPS le
   contraste transverse (M, ~2,4×) ET la décroissance longitudinale, avec la MÊME valeur ? Le
   plein-champ le teste en 2D, là où 5 TC ne le pouvaient pas.

## 3. Montage expérimental

- **Configuration = MONOSPOT** : une seule empreinte, **fixe**, centrée en longueur à **x = 60 mm**
  (centre de largeur `y = largeur/2`), identique à la géométrie exp7 → les données se **recoupent
  directement** avec exp7 (mêmes positions TC / mêmes courants).
- Échantillon CF/PEKK (mêmes plaque/QI que exp7/exp9), **suspendu** (supports ponctuels aux coins,
  chants **libres** — cohérent avec le constat « 4 chants à l'air libre » de la mémoire terrain).
- **MFC + coil** d'un côté, **à la même distance de couplage** que les essais (≈ 5 mm — à relever et
  consigner ; sans céramique, le gap change le couplage EM → cf. Limites).
- **Caméra FLIR** de l'autre côté, axe optique ⟂ à la plaque, cadrage englobant la plaque entière +
  marge. Face imagée = **face opposée au MFC**.
- Balayage courant reproduisant exp7 (p. ex. 150 / 200 / 250 A), maintien assez long pour atteindre
  le **régime établi** (les essais précédents coupaient trop court : pic ~15–22 s vs ~46 s modèle).
- **Émissivité** : coller ≥1 pastille de référence d'émissivité connue OU un TC de contact ponctuel
  sur la face imagée pour ancrer le radiométrique (CF/PEKK ε ≈ 0,9 à confirmer).

## 3 bis. Courant admissible & plafond de température (anti-déconsolidation)

**Contrainte matériau.** PEKK `T_fusion = 337 °C` (onset ≈ 330 °C, largeur DSC 15 °C ; `config/materiaux.yaml`).
Sur une plaque **libre (sans pression)**, franchir la fusion = **déconsolidation** de la matrice.
`Tg = 159 °C` = ramollissement (repère, pas une limite dure). Le **point chaud** est le **chant**
(lobes du M, `y = 0`/`largeur` à l'interface) — c'est LUI qui doit rester sous le plafond, pas le centre.

**Le courant ne fixe pas la T max — la coupure la fixe.** Constat exp7 (avec céramique) : les pics
chants mesurés sont **~271–280 °C à TOUS les courants 150→250 A**, parce que la coupure était
**manuelle** au chant ~270–274 °C. Le courant fixe seulement la **vitesse de montée** (source ∝ I²) :
temps jusqu'au plafond ∝ 1/I² (indicatif avec céramique : ~30 s @150 A, ~18 s @200 A, ~11 s @250 A).

**Décision : rester SOUS Tg = 159 °C.** Double justification :
- **Sécurité** : sous Tg la matrice est vitreuse/rigide → **aucune mobilité, aucun risque de
  déconsolidation ni de warping** sur plaque libre (marge maximale ; on ne s'approche même pas de la
  fusion 337 °C).
- **Qualité de mesure** : sous Tg on reste dans le **régime linéaire** — pas de pic de `cp` de fusion,
  pas de dérive `k(T)` marquée → mesure **propre** de la forme de source et de la longueur d'étalement
  `k_plan`. Or la **répartition spatiale** (M, décroissance `LL`) est présente **dès les faibles ΔT** :
  pas besoin de monter en température.

**Règle de conduite (plaque libre) :**

- **Plafond de coupure sur le MAX live FLIR : ≈ 140 °C** (marge ~15–20 °C sous Tg=159 °C). ⚠️ la caméra
  lit la face **arrière**, un peu plus froide que le chant à l'interface → le vrai point chaud est
  **au-dessus** de la lecture → cette marge garantit l'interface < Tg.
- **Couper sur la température, PAS sur une durée figée.** La plaque libre n'a **pas** le puits céramique
  en face basse → elle chauffe **plus vite** qu'exp7 à courant-temps égal → coupure live obligatoire.
- **Courant** : **150 A recommandé** (montée la plus lente → coupure manuelle confortable) ; **200 A**
  avec vigilance ; **≥ 250 A uniquement avec coupure automatique** (temps-jusqu'au-plafond ∝ 1/I², très
  court à ce plafond bas). Balayer 150/200 A donne déjà le recoupement exp7 et le test `LL`.
- **Ne jamais viser un pic élevé** : inutile ici (la forme suffit) et dangereux sans pression.

## Mode opératoire — étapes claires

**A. Préparation (avant chauffe)**
1. **Échantillon** : plaque CF/PEKK consolidée ; relever QI, épaisseur, dimensions. Face imagée
   (opposée au MFC) matte / peu réfléchissante ; coller **1 pastille d'émissivité connue** (ou fixer
   **1 TC de contact** ponctuel hors zone chaude) pour ancrer le radiométrique.
2. **Fiduciaux** : marquer **4 repères** (les 4 coins, ou 4 pastilles) et **relever leurs mm** (repère
   plaque : origine au coin, x = longueur, y = largeur).
3. **Montage** : suspendre la plaque sur appuis **ponctuels** (4 chants libres). **MFC + coil** d'un
   côté à la **distance de couplage ≈ 5 mm** (la **relever et la consigner**). **FLIR** de l'autre côté,
   axe optique ⟂ plaque, plaque entière + marge dans le champ, mise au point faite.
4. **Réglage caméra** : renseigner **émissivité**, **température ambiante réfléchie**, **distance** ;
   cadence **≥ 10 Hz** ; **enregistrement radiométrique ON**. ⚠️ faire un **clip test de 5 s** et
   **vérifier qu'il s'ouvre** (piège du MP4 non finalisé / atome `moov` manquant déjà rencontré).
5. **Frame froide de référence** : enregistrer quelques secondes AVANT chauffe (fiduciaux + ambiante).

**B. Exécution (par courant : 150 A, puis 200 A)**
6. Régler le **courant** (commencer à **150 A**).
7. Démarrer **l'enregistrement FLIR** puis **la chauffe** ; noter `t0` (ou trigger synchronisé).
8. **Surveiller le MAX live FLIR** et **couper le courant dès ≈ 140 °C** (sous Tg). **Jamais** sur une
   durée figée.
9. **Continuer d'enregistrer le refroidissement** ~60–120 s (la décroissance `LL` et l'info
   inter-passes sont aussi dans le refroidissement).
10. Arrêter l'enregistrement, **confirmer que le fichier est finalisé/lisible**.
11. Laisser la plaque **revenir à l'ambiante**, puis **répéter à 200 A** (même plafond de coupure).

**C. Post-traitement (ROI → CSV → rejeu modèle)**
12. Dans FLIR Tools, sur la **frame de pic**, placer : `F1…F4`, lignes `LT`/`LL`, points `P0…P4`,
    cercle `C_spot`, aire `A_plaque` (détails §4).
13. **Exporter les CSV** au schéma §5 : `roi_points.csv`, `roi_lignes.csv`, `roi_aires.csv` +
    `recalage.json` (positions en **mm**, temps en **s**, T en **°C**).
14. **Me transmettre les CSV** → je lance
    `python code/scripts/thermographie_virtuelle.py rejouer code/config/essais/<manip>.yaml --csv-dir <dossier>`
    → superpositions `LT`/`LL` normalisées + séries `P0…P4` + **verdict sur la longueur d'étalement
    (`k_plan` 3 vs 7,5)**.

## 4. LE MOMENT « lignes / points / cercles » — placement des ROI et recalage

**Quand.** Après acquisition, dans le logiciel FLIR (FLIR Tools / ResearchIR), sur la **séquence
radiométrique**. On place les outils de mesure sur **une frame de référence** (le pic) ; comme la
plaque est fixe, les ROI restent aux mêmes pixels sur toutes les frames. Puis **Export → CSV**.

**Repère physique (obligatoire).** Le jumeau raisonne en `(x, y)` : `x` = **longueur**
(longitudinal, dissipation en x), `y` = **largeur** (0 → largeur, centre = largeur/2, profil M).
Origine choisie : **un coin de la plaque** ; on note aussi le **centre du spot** `(x_spot, y_spot)`.
Toutes les ROI seront converties en mm dans ce repère.

**Recalage pixel → mm (fiduciaux).** Avant/au début (frame froide), placer **4 spots fiduciaux**
`F1…F4` sur des repères à coordonnées connues (les 4 coins de la plaque, ou 4 pastilles
haute-émissivité aux mm relevés). Leurs coordonnées **pixel** + **mm** définissent une
homographie/affine pixel→mm (plaque plane, caméra ~frontale). **Sans ces 4 fiduciaux, aucune donnée
n'est rejouable par le modèle.**

**ROI à poser** (identifiants à réutiliser tels quels dans les CSV) :

| ROI | Type | Géométrie (repère plaque) | Ce que ça capte |
|-----|------|---------------------------|------------------|
| `F1…F4` | Spots | 4 coins / pastilles, mm connus | **Recalage** pixel→mm |
| `LT` | **Ligne** transverse | `x = x_spot`, `y` de 0 → largeur (bord→bord) | Profil **M** (largeur) |
| `LL` | **Ligne** longitudinale | `y = largeur/2`, `x` du bord d'attaque du spot → **≥ 3–4× la longueur du spot vers l'aval** | **Étalement hors-spot** (résidu ouvert) |
| `P0…P4` | **Points** | `x = x_spot`, `y = 0,10,20,30,40 mm` | Pont de comparaison avec les **TC exp7** |
| `C_spot` | **Cercle/ellipse** | sur l'empreinte du spot | Tmax/Tmin/Tmoy, saturation, homogénéité |
| `A_plaque` | **Aire** | plaque entière | Bilan, dérive ambiante |

> Les **points** `P0…P4` sont le pont de validation avec les 5 TC noyés de exp7 ; les **lignes**
> `LT`/`LL` sont la vraie nouveauté (profil continu au lieu de 5 points) ; le **cercle** `C_spot`
> donne le pic et l'homogénéité de la zone source.

## 5. Schéma CSV standardisé (exports FLIR) — pour que je puisse tout rejouer

Exporter dans **ce format** (unités : temps en s depuis le début de chauffe, positions en mm dans le
repère plaque, températures en °C) :

- `roi_points.csv` — colonnes : `t_s, roi_id, x_mm, y_mm, T_C`  (P0…P4, F1…F4)
- `roi_lignes.csv` — colonnes : `t_s, roi_id, s_mm, x_mm, y_mm, T_C`  (LT, LL ; `s_mm` = abscisse le long de la ligne)
- `roi_aires.csv`  — colonnes : `t_s, roi_id, Tmin_C, Tmax_C, Tmoy_C`  (C_spot, A_plaque)
- `recalage.json`  — `{ fiduciaux: [{id, px, py, x_mm, y_mm}×4], emissivite, distance_mm, ambiante_C, dt_s, courant_A, couplage_mm }`
- *(option, le plus riche)* `champ_t####.csv` — **matrice plein-champ** (°C) à quelques instants clés
  (p. ex. 1 s, mi-montée, pic, mi-refroidissement) + le même `recalage.json`.

Si le radiométrique brut FLIR `.seq/.csq` est le seul export disponible, il faut le décoder
(`flirpy` + `exiftool`) — **hors de portée en l'état** ; privilégier l'**export CSV depuis FLIR Tools**.
⚠️ Rappel du piège déjà rencontré : un **MP4 non finalisé** (sans atome `moov`) est **illisible** —
vérifier que l'enregistrement/export est bien clôturé.

## 5 bis. Mini-tuto export — **FLIR Research Studio**

> Logiciel confirmé : **FLIR Research Studio** (successeur de ResearchIR). Fonction phare :
> **« chaque frame exportable en CSV / 32-bit TIFF / Matlab »** → la **Méthode A ci-dessous est LA voie**
> (sans perte). ⚠️ Les libellés exacts peuvent varier d'une version à l'autre ; cherche l'équivalent
> (« Export », « CSV », « Frame range »).

**Préalable**
1. **Importer** l'enregistrement dans la **Library** (glisser le `.seq`/`.csq`/`.ats`/`.csm`).
2. Panneau **Parameters** (*Object/Measurement Parameters*) : régler **émissivité**, **reflected
   temperature**, **distance**, (atmosphère/humidité) — **avant** l'export, c'est ce qui donne les °C justes.
3. Noter **`t0`** (début de chauffe sur la timeline) et le **`fps`** (propriétés de l'enregistrement).

---

### Méthode A — champ complet par pixel (RECOMMANDÉE pour Research Studio, zéro perte)

Tu me donnes tout le champ, je recoupe **tes 10 lignes** (et n'importe quelle autre) moi-même — **aucune
ligne à tracer**.

1. Sélectionner l'enregistrement dans la **Library** (ou l'ouvrir dans le viewer).
2. **`Export`** (bouton d'export / menu **`File → Export`** / icône d'export).
3. Type de données : **CSV** en **température (radiométrique)** — *pas* image/vidéo.
4. **Frame range** : de `t0` à la fin du refroidissement. **Sous-échantillonner** le temps si proposé
   (garder **~2–5 Hz** suffit largement).
5. Si l'export propose de **restreindre la zone** (crop / région) : **cadrer sur la plaque** → allège
   fortement le volume.
6. Lancer → dossier de **`frame_00001.csv`, `frame_00002.csv`…** (chaque fichier = matrice de pixels en °C).

➕ **À fournir** : le **dossier de frames CSV** + les **4 fiduciaux** (pixel ↔ mm) + **`fps` + `t0` +
émissivité + courant** (un jeu par courant : 150 A, 200 A).
⚠️ **Volume** : plein-champ × N frames peut être lourd → le **crop plaque** + **2–5 Hz** gardent ça raisonnable.

---

### Méthode B — profils par ligne sur le temps (repli, si tu tiens à tes 10 lignes)

1. Outil **Line** → tracer la ligne, la **positionner** via ses coordonnées d'extrémités.
2. Panneau **Plot** : pour une Line, Research Studio affiche le **Line Profile** (T vs position) et les
   valeurs temporelles.
3. **Exporter le plot en CSV**. ⚠️ selon la version, l'export d'une Line peut ne rendre que **min/max/avg**
   (scalaire) — **insuffisant** (ça écrase le profil). Si tu ne trouves pas l'export du **profil complet
   sur toutes les frames**, **bascule sur la Méthode A** (qui rend B inutile).

➕ **À fournir** (si B) : les **10 `line*.csv`** (position × temps) + **extrémités en mm** de chaque ligne
(pour 6–10 : l'**étendue x du MFC**) + **`fps` + `t0` + émissivité + courant**.

---

**Conclusion Research Studio : prends la Méthode A.** Envoie-moi le **dossier CSV** + **4 fiduciaux** +
**`fps`/`t0`/émissivité/courant** ; je vérifie qu'un fichier **s'ouvre** (séparateur/décimale : je gère),
j'écris le lecteur calé sur ton format, je recoupe tes 10 lignes depuis le champ, et je lance le rejeu →
superpositions mesure/modèle + **verdict `k_plan`**.

## 6. « Caméra virtuelle » — comment je reproduis la vue caméra à partir des seuls CSV

Le jumeau expose déjà tout le nécessaire :
`SolveurThermique2D.serie_temporelle(sol, x, y)` (interpolation **bilinéaire** en `(x, y)`) et
`resultat_2d(sol, i)` (champ 2D). Pipeline (script `scripts/thermographie_virtuelle.py` à créer) :

1. **Simuler** l'essai correspondant (même courant, même durée) → objet `sol`.
2. **Lire la GÉOMÉTRIE** des CSV caméra (les colonnes `x_mm, y_mm, t_s` uniquement — pas les `T_C`).
3. **Échantillonner le modèle aux mêmes points** : pour chaque `(x_mm, y_mm)`, convertir mm→m et
   appeler `serie_temporelle(sol, x, y)`, puis **rééchantillonner en temps** sur les `t_s` caméra.
4. **Émettre le MÊME schéma** : `roi_points_SIM.csv`, `roi_lignes_SIM.csv`, `roi_aires_SIM.csv`.
5. **Diff CSV ↔ CSV** : superposition des profils `LT`/`LL` (mesure vs modèle), séries `P0…P4`, cartes
   d'écart. Pour le plein-champ : rééchantillonner `resultat_2d` sur la grille pixel via le recalage
   → **image synthétique** comparable pixel à pixel à `champ_t####.csv`.

**Contrainte modèle lumpé (cadrage obligatoire).** Le 2D n'a **qu'une température dans l'épaisseur**
(`z="surface"/"opposee"` lève une erreur) → il ne distingue pas face avant/arrière, alors que la
caméra voit la face **arrière**. Conséquences pour la comparaison :

- Comparer **la FORME** (profils **normalisés** `LT`/`LL`) et **la CINÉTIQUE** (`dT/dt`, temps
  caractéristiques, longueur de décroissance de `LL`), **pas les °C absolus**.
- Traiter l'écart traversant comme un **décalage vertical** (1 paramètre) OU l'ancrer via le TC de
  contact ponctuel sur la face imagée.
- Ne **pas** comparer les absolus aux cibles de soudage : sans céramique/pression, le couplage EM
  diffère (déjà constaté en mémoire : « absolus non comparables »).

## 7. Prédiction falsifiable du jumeau

- **Profil `LT` (M)** : contraste chant/centre ≈ 2,4× (forme normalisée superposable) — reconfirme
  l'acquis exp7 sur plaque découplée.
- **Profil `LL` (longitudinal)** : décroissance hors-spot avec une **longueur caractéristique**
  fixée par `k_plan`. `k_plan = 3,0` prédit une décroissance **plus raide** que `k_plan ≈ 7,5`
  (effectif). → **La caméra tranche entre les deux**, et teste si UNE seule valeur ajuste `LT` **et**
  `LL` simultanément (cœur du résidu #68).
- **Source précoce** (`C_spot`, premières secondes) : empreinte ≈ dépôt Joule → forme de source.

**Interprétation** : `LL` mesuré plus étalé que `k_plan=3` mais `LT` toujours à contraste ~2,4× ⇒
confirme le sur-étalement anisotrope irréductible (arc #68). `LL` compatible avec `k_plan=3` ⇒
rouvrirait la question (donnée nouvelle légitime, cf. clôture #68 « ne pas rouvrir sans donnée neuve »).

## 8. Livrables & critères d'acceptation

- [ ] Jeu de CSV au schéma §5 (≥ 3 courants), avec `recalage.json` + fiduciaux.
- [ ] `scripts/thermographie_virtuelle.py` (rejoue la vue caméra depuis les CSV).
- [ ] Figures : superposition mesure/modèle de `LT`, `LL` (normalisés), séries `P0…P4`, carte d'écart
      plein-champ (PNG, style article — cf. préférence figures).
- [ ] Verdict `LL` : longueur d'étalement mesurée vs `k_plan` 3,0 / 7,5 → confirme ou rouvre #68.

## 9. Limites assumées

1. **Absolus non comparables** aux essais soudage (pas de céramique/pression → couplage EM différent).
2. **Face arrière + modèle lumpé** : comparaison en forme/cinétique, offset traversant à ancrer.
3. **Émissivité** CF/PEKK à calibrer, sinon °C faux.
4. **Format** : export CSV FLIR requis (radiométrique `.seq/.csq` hors de portée sans flirpy+exiftool ;
   MP4 non finalisé = illisible).
