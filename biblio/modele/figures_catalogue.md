# Catalogue des figures — jumeau numérique soudage induction CF/PEKK

Description détaillée de chaque figure : fichier, titre incrusté, axes (unités et plage),
séries tracées, essais/données sources, méthode de calcul, lignes de référence, message clé
(avec chiffres) et une proposition de légende (« caption ») directement réutilisable.

---

## 0. Format commun (référence `serieA_A-2_250A_2026-06-09.png`)

Depuis la refonte du **2026-07-29**, tout le jeu `biblio/labo/figures/` suit le **format de
référence** de `serieA_A-2_250A_2026-06-09.png` :

| Élément | Convention |
|---|---|
| **Titre** | Descriptif, incrusté en haut de la figure (ou `suptitle` pour les figures multi-panneaux). |
| **Labels d'axes** | En **gras**, avec unité entre parenthèses ; notation mathématique pour les variables ($y$, $x$, $I$, $\Delta T$, $dT/dt$). |
| **Légende** | **Hors du cadre de données** — à droite (`bbox_to_anchor=(1.02, 0.5)`) pour les figures mono-panneau, dans la case vide 2×3 ou au-dessus des panneaux pour les figures multi-panneaux. **Aucun texte ne recouvre les courbes.** |
| **Étiquettes de panneau** | `(a) … (e)` placées **au-dessus** de chaque axe (`set_title(loc="left")`), jamais dans la zone de données. |
| **Palette** | Okabe-Ito (daltonien-safe) : bleu `#0072B2`, orange `#E69F00`, vert `#009E73`, bleu clair `#56B4E9`, vermillon `#D55E00`. Superposition multi-courants = rampe *viridis*. |
| **Lignes de référence T°** | Sur les figures à **ordonnée en température absolue (°C)** : fusion PEKK 337 °C, cible procédé 390 °C, dégradation 450 °C, étiquetées dans le blanc (voir § détails). |
| **Rendu** | PNG 600 dpi, `bbox_inches="tight"`. |

**Trois lignes horizontales de référence** (mêmes couleurs que la référence) :
`Fusion PEKK (337 °C)` bleu plein · `Cible procédé (390 °C)` orange tireté ·
`Dégradation (450 °C)` vermillon plein. La température de fusion (337 °C) est celle du modèle
(`code/config/materiaux.yaml : T_fusion`).

> **Choix assumé sur les lignes T° :** les essais exp 7 sont des runs de **caractérisation
> sous-fusion** (pics ≈ 270 °C au chant, bien en-dessous de la fusion). Les **trois** lignes
> (337/390/450) ne sont tracées que sur les deux figures de synthèse à grande dynamique verticale
> (`fig4_courbes_brutes`, `fig_essais_chant_superpose`). Sur les **petits multiples**
> (`fig_essais_par_courant`, `fig_essais_5TC_par_courant`) seule la ligne de **fusion (337 °C)**
> est tracée, pour ne pas écraser les courbes (ordonnée limitée à 360 °C). Les figures à ordonnée
> **normalisée** ou en **taux/élévation** (fig1, fig2, fig3, fig5, dissipation) ne portent pas de
> ligne T° (sans objet).

**Chaîne de traitement des données brutes** (identique pour toutes les figures issues de mesures,
fonction `clean()`) : ambiante = moyenne des 2 premières lignes des 5 TC · rejet des points
> 320 °C ou < ambiante − 6 °C · interpolation · filtre médian (fenêtre 5) · `t = Time − Time[0]`.
Le **début de chauffe** (`heating_onset_idx`) est le dernier point ambiant avant que le max des
TC dépasse ambiante + 2 °C ; les axes temporels sont recalés sur cet instant.

**Reproductibilité** : `code/scripts/gen/gen_figures_elsevier.py` régénère l'intégralité du jeu (variable
d'environnement `FIGOUT` pour la destination ; sans argument → `biblio/labo/figures/`).
Arguments positionnels optionnels pour ne régénérer qu'une figure :
`fig1 fig2 fig3 fig4 fig5 chant par 5tc mono semi`.

**Jeux de figures — dossier UNIQUE `biblio/labo/figures/`** (consolidé le 2026-08-03 ;
les anciens `figures_elsevier/` et `figures_presentation/` ont fusionné) :
- **Jeu de référence** — 10 figures + les figures dérivées + la figure de référence
  `serieA_A-2_250A_2026-06-09.png`. Noms inchangés (`fig1_profil_M.png`, …).
- **Variantes « slides »** de fig1–5 (§ C) — **même format de référence** avec polices
  agrandies pour la projection, préfixées **`presentation_`** (`presentation_fig1_profil_M_3courants.png`,
  …) pour cohabiter sans collision avec le jeu de référence dans le même dossier.
- **`donnees/data/exp9_dissipation-longitudinale_2026-07-28/200A/`** — figures d'analyse brute (§ B).

> L'ancien jeu `biblio/figures_article/` (sans titre incrusté) a été **supprimé** le 2026-07-29 :
> il faisait doublon avec le jeu de référence désormais que ce dernier porte des titres.

---

## A. Campagne exp 7 — profil en largeur (« M ») et loi en courant

**Source** : `donnees/data/exp7_bord-centre_2026-07-28_avec-ceramique/` (céramique en place = géométrie
standard du modèle). **5 TC valides à l'interface**, y = 0/10/20/30/40 mm, x = 60 mm (spot centré),
montage centré en largeur (TC1 ≈ TC5). Campagne **close** à 5 courants.

| I (A) | Essais valides | Taux chant (ΔT 30→130) | M symétrique |
|---|---|---|---|
| 150 | v1, v2, v3 | 9,7 °C/s | ratio 1,00 |
| 176 | v1 | 15,7 °C/s | ratio 1,00 |
| 200 | v4, v5, v6 | 20,8 °C/s | ratio 1,02–1,07 |
| 225 | v1 | 26,9 °C/s | ratio 1,01 |
| 250 | v1, v2, v3 | 34,2 °C/s | ratio 1,02–1,03 |

### `fig1_profil_M.png`
- **Titre** : « Profil de température en largeur au pic — 150 / 200 / 250 A »
- **Montre** : le profil en « M » (chaud aux chants $y$=0/40 mm, creux au centre $y$=20 mm), à
  trois courants.
- **Axes** : abscisse = position en largeur $y$ (0–40 mm, ticks 0/10/20/30/40) ; ordonnée =
  **élévation au pic** $\Delta T = T_\text{pic} - T_\text{amb}$ (°C).
- **Séries** : 1 courbe `-o` par courant (150 bleu / 200 orange / 250 vert), = **moyenne des
  3 essais** ; bande ombrée = **étendue min–max** essai-à-essai. Légende « Courant » à droite.
- **Méthode** : pour chaque essai, $\Delta T$ par TC = max temporel − ambiante ; moyenne/min/max
  sur les essais du courant.
- **Message** : « M » **symétrique et reproductible** aux 3 courants. Les pics au chant se
  regroupent (~225–235 °C) car la chauffe est standardisée en durée (150 A chauffe plus longtemps).
- **Caption** : *Profil de l'élévation de température en largeur au pic, aux trois courants
  (moyenne de 3 essais, bande = étendue min–max). Le profil en « M » — chants chauds, centre
  froid — est symétrique et reproductible.*

### `fig2_mesure_modele.png`
- **Titre** : « Forme du profil en largeur : mesuré vs modèle (200 A) »
- **Montre** : la **forme** du M, mesurée vs modèle, à 200 A.
- **Axes** : abscisse = $y$ (0–40 mm) ; ordonnée = **température normalisée par la valeur au
  centre** (–). Le centre vaut donc 1 par construction.
- **Séries** : mesuré `-o` orange (contraste 2,18) ; modèle `--s` gris (contraste 2,43).
- **Méthode** : profil au pic divisé par la valeur centre $y$=20.
- **Lignes de référence** : sans objet (ordonnée normalisée).
- **Message** : le modèle **reproduit la forme en M** mais **sur-contraste légèrement** les
  chants (**2,43** modèle vs **2,18** mesuré).
- **Caption** : *Forme normalisée (au centre) du profil en largeur à 200 A. Le modèle reproduit
  la forme en M avec un contraste chant/centre légèrement supérieur (2,43 vs 2,18).*

### `fig3_dynamique_centre.png`
- **Titre** : « Dynamique centre–chant : mesuré vs modèle (200 A) »
- **Montre** : trajectoire **paramétrique** de la montée : comment le centre se réchauffe *à
  mesure* que les chants montent.
- **Axes** : abscisse = $\Delta T$ des **chants** (0–235 °C) ; ordonnée = $\Delta T$ du **centre**
  (0–110 °C). Chaque point = un instant de la montée (jusqu'au pic des chants).
- **Séries** : mesuré (3 essais 200 A) `-` orange (α 0,6) ; modèle 2D `--` gris.
- **Méthode** : chants = max(TC1, TC5) − amb ; centre = TC3 − amb ; tracé jusqu'à l'argmax des
  chants. Modèle = solveur **2D** (facteur de couplage 6,0123, h_haut 30,09, h_bas_2d 37,42,
  h_bord_x0 250, ambiante modèle 23,9 °C).
- **Message** : à $\Delta T$ chant équivalent (~235 °C), le modèle laisse le centre **beaucoup
  plus froid** (~24 °C) que la mesure (~100 °C) → **résidu de remplissage transitoire du centre**,
  seul écart structurel encore ouvert (indépendant du courant ; leviers cp / masse / k_plan /
  placement / lissage / 3D testés et écartés).
- **Caption** : *Dynamique centre–chant à 200 A (trajectoire paramétrique jusqu'au pic). À
  échauffement des chants équivalent, le centre modélisé reste bien plus froid que le centre
  mesuré : le remplissage transitoire du centre est le résidu structurel restant.*

### `fig4_courbes_brutes.png`
- **Titre** : « Historiques des 5 thermocouples — un essai (200 A) »
- **Montre** : les 5 historiques T(t) bruts d'un essai (200A_v6), groupés par **symétrie de
  position**.
- **Axes** : abscisse = temps depuis le début de chauffe (0–72 s) ; ordonnée = **température
  absolue** (°C, 0–470).
- **Séries** : chants TC1/TC5 bleu (plein/tireté) ; intermédiaires TC2/TC4 orange (plein/tireté) ;
  centre TC3 vert. Légende à droite.
- **Lignes de référence** : **les 3** (fusion 337 / procédé 390 / dégradation 450 °C).
- **Message** : cohérence chant-à-chant (symétrie TC1≈TC5, TC2≈TC4) et hiérarchie des pics
  chants > intermédiaires > centre — le « M » lu directement sur la donnée brute. L'essai reste
  **sous la fusion** (pic ~270 °C).
- **Caption** : *Historiques bruts des 5 thermocouples (200 A, un essai), groupés par symétrie.
  Les voies symétriques se superposent et la hiérarchie chants > intermédiaires > centre reproduit
  le profil en M ; l'essai reste sous la température de fusion.*

### `fig5_loi_courant.png`
- **Titre** : « Loi taux de chauffe – courant (5 courants) »
- **Montre** : la relation entre le courant générateur et le taux de chauffe au chant.
- **Axes** : abscisse = courant $I$ (A) ; ordonnée = taux de chauffe au chant $dT/dt$ (°C/s), pente
  sur la plage $\Delta T$ = 30 → 130 °C.
- **Séries** : points mesurés (`o` bleu, barres = étendue min–max) annotés du courant ; ajustement
  **$R = k\,I^2 - L$** (orange plein) ; référence **$k\,I^2$ pur** (pointillé gris).
- **Méthode** : pour chaque essai, pente linéaire de $\Delta T$(t) sur 30–130 °C ; moyenne par
  courant ; régression de $R$ contre $I^2$.
- **Résultats** : $k \approx 6{,}03\cdot10^{-4}$, $L \approx 3{,}47$ °C/s, **$R^2 = 0{,}999$**.
  Taux mesurés : 9,7 / 15,7 / 20,8 / 26,9 / 34,2 °C/s pour 150/176/200/225/250 A.
- **Message** : la source suit la **loi en $I^2$** du modèle ; l'écart apparent à $I^2$ pur vient
  de **pertes ~constantes** (~3,5 °C/s), pas de la source. Fréquence mesurée constante 388 ± 2 kHz
  → **pas de couplage fréquence-courant** (hypothèse f(I) réfutée).
- **Caption** : *Taux de chauffe au chant en fonction du courant. L'ajustement $R = k\,I^2 - L$
  ($R^2 = 0{,}999$) confirme une source en $I^2$ décalée par des pertes quasi constantes ; la
  fréquence mesurée est constante (388 ± 2 kHz).*

### `fig_essais_chant_superpose.png`
- **Titre** : « Historiques T(t) au chant — tous essais, 5 courants »
- **Montre** : tous les historiques T(t) du chant superposés, colorés par courant.
- **Axes** : abscisse = temps depuis le début de chauffe (0–72 s) ; ordonnée = température au
  chant (°C, 0–470).
- **Séries** : 1 courbe par essai ; couleur = courant (rampe *viridis* 150→250 A). Légende
  « Courant » à droite.
- **Méthode** : chant = max(TC1, TC5) ; recalage sur le début de chauffe.
- **Lignes de référence** : **les 3** (337 / 390 / 450 °C).
- **Message** : plus le courant est fort, plus la montée est rapide et le **pic précoce** (250 A
  ~8–10 s, 150 A ~55 s), suivie du refroidissement. Tous les pics plafonnent ~270 °C (chauffe
  standardisée), sous la fusion.
- **Caption** : *Historiques de température au chant, tous les essais superposés (couleur =
  courant). Le pic est d'autant plus précoce que le courant est élevé ; tous les essais restent
  sous la fusion.*

### `fig_essais_par_courant.png`
- **Titre** (suptitle) : « Répétabilité au chant par courant »
- **Montre** : petits multiples 2×3, un panneau par courant, montrant la répétabilité
  essai-à-essai au chant.
- **Axes** (partagés) : abscisse = temps depuis le début de chauffe (0–72 s) ; ordonnée =
  température au chant (°C, 0–360).
- **Séries** : toutes les répétitions du courant, une couleur Okabe-Ito par courant. Étiquettes
  `(a)…(e)` au-dessus des panneaux ; case 6 = légende (essais + ligne de fusion).
- **Lignes de référence** : **fusion (337 °C) uniquement** dans chaque panneau.
- **Message** : **répétabilité** essai-à-essai serrée par courant (les répétitions se superposent,
  hors léger décalage temporel de montée).
- **Caption** : *Répétabilité au chant : un panneau par courant, toutes les répétitions
  superposées. La ligne bleue marque la fusion PEKK (337 °C).*

### `fig_essais_5TC_par_courant.png`
- **Titre** (suptitle) : « Les 5 thermocouples par courant »
- **Montre** : petits multiples 2×3, les 5 TC d'un essai représentatif par courant — profil en
  largeur **et** dynamique complète (montée + refroidissement).
- **Axes** (partagés) : abscisse = temps depuis le début de chauffe (0–72 s) ; ordonnée =
  température (°C, 0–360).
- **Séries** : TC1 ($y$=0) bleu plein · TC5 ($y$=40) bleu tireté · TC2 ($y$=10) orange plein ·
  TC4 ($y$=30) orange tireté · TC3 ($y$=20, centre) vert. Essais représentatifs : 150A_v3,
  176A_v1, 200A_v6, 225A_v1, 250A_v3. Légende (5 TC + fusion) dans la case 6.
- **Lignes de référence** : **fusion (337 °C) uniquement** dans chaque panneau.
- **Message** : hiérarchie chant > intermédiaire > centre conservée à tous les courants, avec
  symétrie TC1≈TC5 / TC2≈TC4 ; dynamique de refroidissement complète.
- **Caption** : *Historiques des 5 thermocouples pour un essai représentatif de chaque courant.
  La hiérarchie chant > intermédiaire > centre et la symétrie des voies se conservent sur toute
  la plage de courant.*

---

## B. Campagne exp 9 — dissipation longitudinale T(x)

**Source** : `donnees/data/exp9_dissipation-longitudinale_2026-07-28/`. 5 TC alignés en **longueur**
à $x$ = 0/30/60/90/120 mm (pas 30 mm), au bord $y$=0, à 200 A. Deux fichiers 200 A : spot unique
(`200A_y0_monospot.txt`) et soudage semi-statique 4 dwells (`200A_y0_semistatique.txt`).

### `fig_dissipation_monospot.png`
- **Titre** : « Décroissance longitudinale : mesuré vs modèle (spot unique, $y$=0) »
- **Montre** : la décroissance de $\Delta T$ le long de la longueur pour un **spot unique**
  (concentrateur centré sur TC3, $x$=60 mm).
- **Axes** : abscisse = position en longueur $x$ (0–120 mm, ticks 0/30/60/90/120) ; ordonnée =
  $\Delta T$ au pic **normalisée au spot** (–).
- **Séries** : modèle `--s` gris ; mesuré `-o` bleu. Repère vertical pointillé à $x$=60 (spot) ;
  annotation « asymétrie de montage » sur le point $x$=90.
- **Valeurs** : mesuré 0,015 / 0,081 / **1** / 0,139 / 0,03 ; modèle 0,013 / 0,094 / **1** /
  0,094 / 0,027.
- **Message** : décroissance longitudinale **très raide** (< 15 % à ±30 mm, < 3 % à ±60 mm) ;
  le modèle la **reproduit**. L'écart à $x$=90 = asymétrie de montage (artefact, pas un défaut).
  → **forme de la source en longueur validée**.
- **Caption** : *Décroissance longitudinale de l'élévation au pic (spot unique, normalisée au
  spot). Le modèle reproduit la décroissance raide ; l'asymétrie résiduelle à x=90 mm est un
  artefact de montage.*

### `fig_dissipation_semistatique.png`
- **Titre** (suptitle) : « Empreinte par dwell : modèle multi-spots vs mesuré »
- **Montre** : 4 panneaux (un par dwell) du **procédé semi-statique** : la bobine s'arrête
  successivement (4 dwells), le point chaud avance de 30 mm.
- **Axes** (partagés) : abscisse = position en longueur $x$ (0–120 mm) ; ordonnée = $\Delta T$
  du dwell **normalisée** au max du dwell (–).
- **Séries** : modèle multi-spots `--s` gris ; mesuré `-o` bleu. Légende (Mesuré / Modèle)
  **au-dessus** des panneaux ; étiquettes `(a)…(d)` au-dessus de chaque axe.
- **Données** (empreinte normalisée par dwell) : modèle vs mesuré, spots à $x$≈15/45/75/105 mm,
  aux instants mesurés (22 / 141 / 236 / 333 s), 200 A, sans consigne (l'absolu n'est pas
  confronté : énergie/durée de dwell inconnue).
- **Message** : le **procédé est reproduit** — chaque dwell chauffe la bonne **paire de TC
  adjacents** (spot avançant de 30 mm), décroissance raide au-delà. La **balance intra-paire**
  (lequel des 2 TC est le plus chaud) n'est pas fidèle : les deux sont à ~15 mm du spot, la
  balance est sensible à la position exacte (incertitude ±15 mm), pas un défaut du modèle.
- **Caption** : *Empreinte longitudinale par dwell (normalisée), modèle multi-spots vs mesuré.
  Le modèle chauffe la bonne paire de thermocouples à chaque dwell ; la balance intra-paire
  dépend de la position exacte du spot (incertitude ±15 mm).*

### Figures d'analyse brute (`donnees/data/exp9_…/200A/`)
Figures de travail (non article), conservées pour traçabilité :
- **`analyse_200A_y0.png`** — historique longitudinal du soudage semi-statique (4 dwells), 5 TC
  couleur = position $x$ ; le point chaud avance le long de la longueur, empreinte de chaque
  dwell étroite.
- **`analyse_200A_y0_monospot.png`** — spot unique : historique T(t) des 5 TC (gauche) + profil
  longitudinal $\Delta T$ au pic vs $x$ (droite).
- **`analyse_200A_y0_monospot_vs_modele.png`** — version confrontée au modèle (source de
  `fig_dissipation_monospot`).
- **`analyse_200A_y0_semistatique_vs_modele.png`** — version confrontée au modèle (source de
  `fig_dissipation_semistatique`).

---

## C. Variantes présentation (`biblio/labo/figures/`)

`presentation_fig1_profil_M_3courants`, `presentation_fig2_mesure_vs_modele`,
`presentation_fig3_centre_dynamique`, `presentation_fig4_courbes_brutes`,
`presentation_fig5_loi_courant` — mêmes contenus que la section A (fig1–5), pour l'oral
(présentation directrice). À ne pas soumettre en article.

> **Format** : réalignées sur le format de référence (§ 0) le 2026-07-29 — mêmes titre / labels
> gras / légende hors cadre / lignes T°, avec **polices agrandies** pour la projection (canevas
> mis à l'échelle en conséquence). Depuis le 2026-08-03 le preset écrit directement dans le
> dossier unique `biblio/labo/figures/` avec le préfixe `presentation_` (plus besoin de `FIGOUT`).
> Régénération : `PRESET=presentation .venv/bin/python code/scripts/gen/gen_figures_elsevier.py
> fig1 fig2 fig3 fig4 fig5`.
