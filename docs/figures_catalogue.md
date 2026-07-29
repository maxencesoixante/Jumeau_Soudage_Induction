# Catalogue des figures — jumeau numérique soudage induction CF/PEKK

Description de chaque figure : ce qu'elle montre, les axes, le message clé et l'essai source.
Deux jeux existent : **`docs/figures_article/`** (format article, sans titre incrusté — les
légendes ci-dessous servent de base aux captions) et **`docs/figures_presentation/`** (variantes
« slides » avec titre, pour l'oral). Les figures d'analyse brute sont dans
`data/exp9_dissipation-longitudinale_2026-07-28/200A/`.

---

## A. Campagne exp 7 — profil en largeur (« M ») et loi en courant

### `figures_article/fig1_profil_M.png`
**Profil de température en largeur, au pic, aux trois courants.**
Abscisse : position en largeur *y* (0–40 mm). Ordonnée : élévation de température au pic
ΔT = T_pic − T_ambiante (°C). Une courbe par courant (150 / 200 / 250 A), moyenne de 3 essais,
bande = étendue min–max. **Message** : le profil en « M » (chaud aux chants *y*=0/40, creux au
centre *y*=20) est **symétrique et reproductible** aux trois courants.

### `figures_article/fig2_mesure_modele.png`
**Forme du profil en largeur, mesuré vs modèle (200 A).**
Abscisse : *y* (mm). Ordonnée : température normalisée par la valeur au centre (–). Mesuré
(moyenne 3 essais) vs modèle 2D. Contraste chant/centre = **2,18 mesuré / 2,43 modèle**.
**Message** : le modèle reproduit la **forme en M** ; il sur-contraste légèrement les chants.

### `figures_article/fig3_dynamique_centre.png`
**Dynamique centre vs chant, mesuré vs modèle (200 A).**
Trajectoire *paramétrique* : abscisse = ΔT des chants, ordonnée = ΔT du centre, le long de la
montée. Mesuré (3 essais) vs modèle 2D. **Message** : à ΔT chant équivalent, le modèle laisse le
centre **beaucoup plus froid** que la mesure (~14 °C vs ~65 °C au chant ≈ 190 °C) → **résidu de
remplissage transitoire du centre** (seul écart structurel ouvert).

### `figures_article/fig4_courbes_brutes.png`
**Courbes brutes des 5 thermocouples, un essai (200 A).**
Abscisse : temps (s). Ordonnée : température (°C). Les 5 TC groupés par symétrie de position
(chants *y*=0/40, intermédiaires *y*=10/30, centre *y*=20 ; trait plein / tirets = les deux côtés).
**Message** : cohérence chant-à-chant (symétrie) et contraste de pic chants > intermédiaires >
centre (le « M » vu sur la donnée brute).

### `figures_article/fig5_loi_courant.png`
**Loi taux de chauffe – courant (5 courants).**
Abscisse : courant générateur *I* (A). Ordonnée : taux de chauffe au chant dT/dt (°C/s ; pente sur
ΔT = 30→130 °C). Points mesurés (barres = étendue), ajustement **R = k·I² − L** (k ≈ 6,03·10⁻⁴,
L ≈ 3,47 °C/s, **R² = 0,999**), et référence I² pure. **Message** : la source suit la **loi en I²**
du modèle ; l'écart apparent vient de pertes ~constantes, pas de la source (fréquence mesurée
constante 388 ± 2 kHz → pas de couplage fréquence-courant).

### `figures_article/fig_essais_chant_superpose.png`
**Historiques T(t) du chant, tous les essais superposés.**
Abscisse : temps depuis le début de chauffe (s). Ordonnée : température au chant (°C). Une courbe
par essai, couleur = courant (rampe séquentielle 150→250 A). **Message** : plus le courant est
fort, plus la montée est rapide et le **pic précoce** (250 A ~8 s, 150 A ~55 s), puis refroidissement.

### `figures_article/fig_essais_par_courant.png`
**Petits multiples : un panneau par courant.** Même axes que ci-dessus, un panneau par courant
(150/176/200/225/250 A) montrant les essais de ce courant (chant). **Message** : **répétabilité**
essai-à-essai par courant.

### `figures_article/fig_essais_5TC_par_courant.png`
**Petits multiples : les 5 thermocouples, par courant.** Un panneau par courant, 5 TC d'un essai
représentatif (chants/intermédiaires/centre). **Message** : profil complet en largeur **et**
dynamique (montée + refroidissement) à chaque courant.

---

## B. Campagne exp 9 — dissipation longitudinale T(x)

TC alignés en **longueur** à *x* = 0/30/60/90/120 mm (pas 30 mm), au bord *y*=0, à 200 A.

### `…/analyse_200A_y0.png`
**Historique longitudinal, soudage semi-statique (4 dwells).** Abscisse : temps (s). Ordonnée :
température (°C). 5 TC (couleur = position *x*). **Message** : les 4 dwells du procédé établi ; le
point chaud **avance** le long de la longueur (pas ~30 mm) ; empreinte de chaque dwell **étroite**.

### `…/analyse_200A_y0_monospot.png`
**Spot unique (concentrateur centré sur TC3, *x*=60 mm).** Deux panneaux : historique T(t) des 5 TC
(gauche) ; profil longitudinal ΔT au pic vs *x* (droite). **Message** : décroissance longitudinale
**très raide** (< 15 % à ±30 mm, < 3 % à ±60 mm).

### `…/analyse_200A_y0_monospot_vs_modele.png`
**Décroissance longitudinale : modèle vs mesuré (spot unique, *y*=0).** Abscisse : *x* (mm).
Ordonnée : ΔT au pic normalisé au spot (–). Modèle 2D vs mesuré. **Message** : le modèle
**reproduit la décroissance longitudinale** ; l'écart à *x*=90 = asymétrie de montage (artefact).
→ **forme de la source en longueur validée**.

### `…/analyse_200A_y0_semistatique_vs_modele.png`
**Empreinte par dwell : modèle multi-spots vs mesuré.** 4 panneaux (un par dwell). Abscisse : *x*
(mm). Ordonnée : ΔT du dwell normalisé au max (–). **Message** : le **procédé** est reproduit (spots
avançant de 30 mm, bonne paire de TC chauffée, décroissance raide) ; la balance intra-paire n'est
pas fidèle (incertitude ±15 mm de position, pas un défaut).

---

## C. Variantes présentation (`docs/figures_presentation/`)
`fig1_profil_M_3courants`, `fig2_mesure_vs_modele`, `fig3_centre_dynamique`, `fig4_courbes_brutes`,
`fig5_loi_courant` — mêmes contenus que la section A (fig1–5) mais **avec titre incrusté** et style
« slides », destinés à l'oral (présentation directrice). À ne pas soumettre en article.
