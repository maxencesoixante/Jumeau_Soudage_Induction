# Dépôt de référence — Brassard : soudage par résistance à élément chauffant nanocomposite

**Analyse (2026-08-05, issue #16).** Ce qu'on retient du travail de D. Brassard pour le
jumeau, sur deux plans : la **confection des figures** et l'**approche de modélisation**.

- Dépôt : <https://github.com/dbrassard/Modelling-resistance-welding-of-thermoplastic-composites-with-a-nanocomposite-heating-element>
- Article : *Modelling resistance welding of thermoplastic composites with a nanocomposite
  heating element*, **J. Composite Materials**, DOI [10.1177/0021998320957055](https://doi.org/10.1177/0021998320957055).
- Structure : `Code_for_figures/` (script R + `Data/`), `Tikz/` (schémas vectoriels),
  `Manuscript.tex`/`.pdf`, `bibliography.bib`, classe SAGE `sagej.cls`.

---

## Axe 1 — Confection des figures

### Leur chaîne (`Code_for_figures/Graph_generation.R`)
- **R + `ggplot2`** exclusivement ; données lues en CSV depuis `./Data/` (`read_csv`).
- **Un seul thème réutilisé**, `elsevier_theme = theme_bw() + theme(...)` : police **Times
  (serif) size 16**, axes noirs, **sans grille** (`panel.grid = element_blank()`).
- **Palette colorblind = Okabe-Ito** (#000000, #D55E00 orange, #0072B2 bleu, …).
- **Types de trait** (`dotted` / `solid` / `twodash`) pour distinguer **mesuré vs simulé**.
- **Export multi-format par figure** : **PDF** + **SVG** + **TIFF** (3543 px, **res 500 dpi**,
  `compression = "lzw"`) — prêt pour soumission journal.
- Cartes de température : **raster `viridis`/`inferno`** ; « fenêtre de procédé » : nuage
  log-log + polygone de la zone admissible.
- Schémas de montage : **TikZ/pgfplots** (`Tikz/`), vectoriel LaTeX.

### Notre chaîne (`scripts/gen_figures_elsevier.py` + `gen_*.py`)
- **Python + matplotlib** ; `rcParams` avec **police sans-serif** (DejaVu Sans/Arial),
  **palette Okabe-Ito explicite** (#0072B2 / #E69F00 / #009E73 / #D55E00 / #56B4E9), 600 dpi.
- Deux presets (`elsevier` défaut, `presentation`) dans `gen_figures_elsevier.py`.
- Cartes : `inferno` (bien) mais colormaps **hétérogènes** ailleurs (`jet` dans
  `figure_empreinte.py`, `cividis`, `plasma`).
- **Export PNG uniquement** (préférence projet — bien pour slides).
- Schémas de montage : matplotlib (`gen_schemas_montage.py`).
- Fenêtre de soudage : **déjà présente** (`gen_fenetre_soudage.py`) — analogue de leur
  process window.

### Verdict — ce qu'on adopte / écarte

| Point | Constat | Décision |
|-------|---------|----------|
| **Palette Okabe-Ito + trait plein/pointillé mesuré↔simulé** | **Convergence** : mêmes choix qu'un article SAGE/Elsevier publié | ✅ **Confirme** nos conventions — rien à changer |
| **Thème unique réutilisé** | Eux : 1 `elsevier_theme`. Nous : chaque `gen_*.py` redéfinit son `rcParams` (~10 duplications) | 🔧 **Adopter** un module de style partagé `scripts/_style.py` (rcParams + palette + helper `savefig`) |
| **Export vectoriel multi-format** | Eux : PDF+SVG+TIFF 500 dpi LZW (journal-ready). Nous : PNG 600 dpi | ✅ **FAIT (#19)** : helper `_style.savefig` — `FIG_FORMATS="png,pdf,tiff"` produit PDF vectoriel + TIFF LZW ; PNG par défaut (byte-identique) |
| **Colormap perceptuel homogène** | Nous : `jet` (non perceptuel, non colorblind-safe) dans `figure_empreinte.py` | 🔧 **Corriger** : remplacer `jet` par `inferno`/`viridis` partout |
| **Schémas en TikZ** | Eux : TikZ vectoriel. Nous : matplotlib | ❌ **ÉCARTÉ (#20)** : matplotlib exporte déjà les schémas en PDF vectoriel (#19), pilotés par la config ; TikZ = nouvelle chaîne LaTeX + double maintenance pour un gain marginal. Cf. §Évaluation ci-dessous |
| **Fenêtre de procédé** | Déjà couverte de notre côté | ✅ Rien à faire |
| **Police serif** | Eux : Times. Nous : sans-serif (≠ préférence projet « serif ») | 🕓 À trancher dans le module de style (uniformiser sur le choix voulu) |

---

## Axe 2 — Modélisation (soudage par résistance vs notre induction)

Physique voisine : une **source Joule pilotée** dans un élément chauffant, un transfert
thermique transitoire, une fusion de matrice PAEK. Comparaison :

| Aspect | Brassard (résistance) | Jumeau (induction) |
|--------|-----------------------|--------------------|
| **Source de chaleur** | Joule direct `Q = J·E` dans l'élément nanocomposite | Joule via **courants de Foucault** dans le twill suscepteur |
| **Couplage EM↔thermique** | **one-way** (EM → Joule → thermique) | **one-way** aussi (Q calculé une fois par spot) — **même choix** |
| **Propriétés T-dépendantes** | k, cp, ρ = f(T), **MESURÉES** (MTPS pour k, MDSC pour cp) | **figées** (seul cp via fusion) — c'est exactement notre écart, cf. #13/#14 |
| **Résistance de contact** | **électrique**, ≈ 50 % de la résistance totale ; identifiée → **−45 % de puissance** pour fitter | absorbée en bloc par `facteur_couplage` (efficacité/blindage/contacts) |
| **Conditions aux limites** | convection h≈20, rayonnement ε=1, contact **Cooper-Mikic-Yovanovich** | convection + rayonnement (ε=0,96), conductance vers puits |
| **Fusion** | enthalpie de fusion, **Tm = 343 °C (PEEK)** | cp apparent gaussien, **Tf = 337 °C (PEKK)** |
| **Numérique** | **COMSOL 3D** FEM, 70–90k tétra, ~150–200k ddl, PARDISO | maison, **méthode des lignes BDF**, 2D/3D, jacobien sparse |
| **Validation** | 4 TC **entre l'adhérent sup. et l'isolant céramique** (pas dans le joint) ; interface non mesurable (interférence élec.) | nos TC à l'interface/surface ; interface aussi difficile à mesurer |

### Leçons transposables
1. **Le couplage one-way EM→thermique est un choix standard** — corrobore notre σ(T) différé
   (issue #5). Un article publié fait le même compromis.
2. **La résistance de contact identifiée (≈50 %, −45 % de puissance) est l'exact analogue de
   notre `facteur_couplage`.** Différence : eux l'attribuent physiquement (contact
   électrode/nanocomposite), nous la laissons en facteur d'échelle agrégé. → piste : notre
   facteur pourrait un jour être **décomposé** en contributions physiques nommées.
3. **Ils MESURENT k(T) et cp(T)/fusion par MTPS et MDSC** — méthodes concrètes qui valident
   la faisabilité de nos issues **#13** (k(T) par hot-disk/flash) et **#14** (DSC PEKK).
   *MTPS = Modified Transient Plane Source ; MDSC = Modulated DSC* — noms à citer dans #13/#14.
4. **Même contrainte de métrologie** : TC hors du joint, interface directe non mesurable
   (interférence). Conforte notre débat de placement TC (issue #8) et l'intérêt de la
   thermographie IR (issue #15) comme voie de contournement.
5. **Organisation « article-ready »** (`Code_for_figures` + `Data` + `Manuscript.tex`) — bon
   modèle de dépôt reproductible dont s'inspirer pour le rendu final du mémoire.

---

## Évaluation TikZ pour les schémas de montage (#20, 2026-08-05)

**Question** : porter `gen_schemas_montage.py` (vue de dessus + coupe, exp7/exp9) en
TikZ/pgfplots pour un rendu article ?

**Bénéfice TikZ** : 100 % vectoriel, typographie LaTeX cohérente avec le corps du mémoire,
cotation nette.

**Coûts / constats** :
- **Chaîne LaTeX absente** de l'environnement (ni `pdflatex`/`lualatex`/`tectonic`) — un
  prototype TikZ ne serait même pas compilable/vérifiable ici.
- **#19 a déjà réglé le vectoriel** : le schéma matplotlib s'exporte en **PDF vectoriel
  compact** (`schema_montage_exp7.pdf`, ~43 Ko avec polices embarquées, via `FIG_FORMATS`)
  — l'essentiel du bénéfice « vectoriel pour l'impression » sans nouvelle chaîne.
- **Perte du pilotage par config** : les cotes du schéma matplotlib sont **tirées de
  `config/geometrie.yaml`** (MFC 31,5×55, tubes 6 mm, interface z=3,36…) et se régénèrent si
  la géométrie change. Un schéma TikZ fige les cotes à la main → re-synchronisation manuelle à
  chaque changement (exactement la dette combattue en #17).
- **Double maintenance** : garder matplotlib pour les figures de données + TikZ pour les
  schémas = deux chaînes à entretenir.

Nuance : le PDF matplotlib garde un petit élément raster résiduel (`/Image`, aplats
semi-transparents) ; TikZ serait strictement vectoriel, mais l'écart est marginal à l'échelle
d'une figure d'article.

Esquisse illustrative (non compilée, sans LaTeX ici) — l'approche TikZ resterait du dessin
manuel coté :
```latex
% \draw[fill=mfc]  (-15.75,-27.5) rectangle (15.75,27.5); % MFC 31.5 x 55
% \draw[fill=coil] (-3.175,-30)  rectangle (-0.175,30);   % brin hairpin
% \node[tc] at (0,20) {TC1}; ...  % cotes à saisir/maintenir à la main
```

**Décision : ÉCARTER TikZ pour l'instant.** Garder matplotlib + export vectoriel (#19).
**Déclencheur de réouverture** : (a) une exigence de rendu impose le 100 % vectoriel LaTeX
avec typographie identique au corps, **ET** (b) une chaîne LaTeX est installée et maintenue.

---

## Sous-issues engendrées — toutes traitées
1. ✅ **Centraliser le style des figures** (`scripts/_style.py`, palette Okabe-Ito, fix `jet`) — **#17 mergé**.
2. ✅ **Export vectoriel des figures** (PDF + TIFF via `FIG_FORMATS`, PNG conservé) — **#19 mergé**.
3. ❌ **Schémas de montage en TikZ** — **#20 écarté** (matplotlib + export vectoriel suffit ; pas de LaTeX ; pilotage config à préserver — cf. §Évaluation ci-dessus).
4. ✅ **Décomposer `facteur_couplage`** — **#21 traité** : non identifiable depuis la température, verdict documenté (`../modele/facteur_couplage_decomposition.md`).
