# Comment le modèle calcule la source de chaleur — dérivation reproductible (x, y, z)

**But de ce document.** Réexpliquer, à partir des premiers principes, comment le jumeau
transforme le courant de la bobine en une densité de puissance de chauffe **q(x, y, z)** [W/m³]
déposée dans la plaque CF/PEKK, puis en terme source de l'équation de la chaleur. Chaque étape est
écrite pour être **refaite à la main** (ou suivie « par un jeu de pensée ») : on donne l'équation,
sa justification, et un **exemple chiffré** avec les vraies valeurs du modèle. Tout est tracé au
code réel (`code/src/jumeau/em/{champ_coil,foucault,source_joule}.py`, `thermique/solveur3d.py`,
`config/{geometrie,materiaux}.yaml`).

**Repère (le même que la grille thermique, `thermique/solveur3d.py`) :**
`x` = longueur du coupon (0 → 120 mm, direction des passes), `y` = largeur (0 → 40 mm),
`z` = épaisseur, **z = 0 à la surface côté bobine**, z croît vers le bas. Empilement
(6,82 mm) : laminé sup. 3,36 mm (le pli **twill suscepteur** 0,20 mm est à son extrémité côté
interface) + film PEKK 0,10 mm + laminé inf. 3,36 mm.

La logique du calcul se lit en trois temps : **A.** les lois de base que l'on tient pour acquises →
**B.** les réductions que l'on fait pour modéliser *ce que l'on veut* (une carte de chauffe utilisable)
→ **C.** les résultats que cela produit et comment on les valide.

---

## A. Ce que l'on connaît de base (premiers principes)

Quatre briques suffisent. Aucune n'est propre au projet : ce sont les lois de l'électromagnétisme
et de la thermique.

**A.1 — Champ d'un fil (Biot-Savart).** Un segment de fil `a → b` parcouru par un courant `I`
crée, au point d'observation `P`, un champ

$$\mathbf B = \frac{\mu_0 I}{4\pi}\,\frac{\hat u \times \mathbf r_1}{|\hat u \times \mathbf r_1|^2}\,(\hat u\cdot\hat r_1 - \hat u\cdot\hat r_2),\qquad \mathbf r_1=P-a,\;\mathbf r_2=P-b,\;\hat u=\tfrac{b-a}{|b-a|}.$$

C'est exactement `champ_coil.champ_segments` (vérifié dans les tests contre la boucle circulaire
`B_centre = µ0 I / 2R`). *Image mentale :* on additionne la contribution de chaque bout de fil.

**A.2 — Induction (Faraday) + Ohm.** Un champ **alternatif** `B(t)` induit un champ électrique :
en régime harmonique (phasor, `∂/∂t → jω`), `∇×E = −jωB`. Dans un conducteur, la loi d'Ohm locale
relie courant et champ : `J = σ̃ E` (ou `E = ρ̃ J`, `ρ̃ = 1/σ̃`), avec une résistivité **anisotrope**
(les fibres conduisent mieux dans leur sens).

**A.3 — Chaleur Joule.** La puissance dissipée par unité de volume dans un conducteur est
`q = J·E = ρ|J|²` [W/m³]. Avec un courant **RMS** en entrée, `q` est directement la puissance
**moyenne** (pas de facteur ½ à ajouter).

**A.4 — Équation de la chaleur.** Une fois `q` connu, la température obéit à

$$\rho\,c_p\,\frac{\partial T}{\partial t} = \nabla\!\cdot(k\,\nabla T) + q(x,y,z,t).$$

**A.5 — Épaisseur de peau.** Un champ alternatif ne pénètre un conducteur que sur une profondeur
caractéristique `δ = √(2ρ/µ₀ω)`. C'est le nombre qui décide si l'on peut traiter la plaque comme
« mince » (§B.4).

---

## B. Comment on modélise ce que l'on souhaite

On veut une **carte de chauffe q(x,y,z)** réaliste dans sa forme, calculable en une fraction de
seconde (pour boucler calibration et validation). D'où une chaîne de réductions, chacune justifiée.

### B.1 — Géométrie et repère (les entrées)

| Élément | Valeur (`config/geometrie.yaml`) |
|---|---|
| Plaque | 120 × 40 × 6,82 mm (x, y, z) |
| Bobine hairpin | 2 brins ∥ à y, longueur 55 mm, entraxe 12,35 mm, hauteur **5 mm** au-dessus de la surface |
| Concentrateur MFC | Ferrotron 559H, 55 × 31,5 × 12 mm, **µr ≈ 16** |
| Générateur | **388 kHz** (mesuré, constant 150–250 A), courant `I` RMS |

*Image mentale :* une épingle à cheveux en cuivre à plat 5 mm au-dessus de la plaque, coiffée d'un
bloc de ferrite qui rabat le champ vers le bas.

### B.2 — Champ magnétique Bz(x, y) : Biot-Savart + image du MFC

On calcule le champ de la bobine réelle (A.1), **plus** l'effet du concentrateur, traité par la
**méthode des images** : chaque segment est réfléchi sous la face inférieure du MFC avec un courant
`η·I`, où

$$\eta = \frac{\mu_r-1}{\mu_r+1} = \frac{16-1}{16+1} = \frac{15}{17} \approx 0{,}88.$$

(`champ_coil.bz_plan`, argument `mu_r_cfc`.) On ne garde que la composante **normale à la plaque,
`Bz`** : seul le flux qui *traverse* le plan de la plaque induit des courants utiles (Faraday).

> **Exemple chiffré (ordre de grandeur).** Sous un brin, à `d = 5 mm`, le champ d'un fil long vaut
> `B ≈ µ₀ I /(2π d)`. Pour `I = 200 A` : `B ≈ (1,2566·10⁻⁶ × 200)/(2π × 0,005) ≈ 8·10⁻³ T = 8 mT`
> — du bon ordre (3–28 mT crête selon le courant, cf. docstring `champ_coil`). L'image MFC
> rehausse ce champ d'un facteur ~(1+η) sous l'empreinte.

### B.3 — Courants de Foucault plans : la fonction de courant ψ

Dans la plaque, `Bz` induit des courants. Plutôt que de résoudre `Jx, Jy` séparément (il faudrait
imposer la conservation `∇·J = 0` à la main), on pose une **fonction de courant** `ψ(x, y)` :

$$J_x = \frac{\partial\psi}{\partial y},\qquad J_y = -\frac{\partial\psi}{\partial x}\quad\Longrightarrow\quad \nabla\!\cdot\mathbf J = 0\ \text{par construction.}$$

En injectant Ohm anisotrope et Faraday (A.2), avec `Bz` réel pris comme référence de phase (champ
de réaction négligé, §B.6), on obtient l'équation **réelle** résolue par le code
(`foucault.resoudre_psi`) :

$$\boxed{\;\rho_{yy}\,\frac{\partial^2\psi}{\partial x^2} + \rho_{xx}\,\frac{\partial^2\psi}{\partial y^2} = \omega\,B_z\;}\qquad \text{avec}\quad \psi = 0 \text{ sur tout le chant.}$$

La condition **`ψ = 0` au bord** dit simplement qu'*aucun courant ne peut traverser le bord physique
de l'échantillon*. C'est **elle**, et non une inhomogénéité du champ, qui écrase le courant près des
chants et crée le **profil en « M »** en largeur (§C).

> **Discrétisation reproductible (différences finies, 5 points).** Sur une grille de pas `dx, dy`,
> posons `ax = ρyy/dx²` et `ay = ρxx/dy²`. L'équation en chaque nœud intérieur `(i, j)` devient :
> $$ax\,(\psi_{i+1,j}+\psi_{i-1,j}) + ay\,(\psi_{i,j+1}+\psi_{i,j-1}) - 2(ax+ay)\,\psi_{i,j} = \omega\,B_{z,\,i,j}.$$
> C'est exactement l'assemblage de `resoudre_psi` (matrice creuse, diagonale `−2(ax+ay)`, voisins
> `ax`/`ay`), avec `ψ = 0` imposé sur la première/dernière ligne et colonne. On résout `A ψ = ω Bz`.
> Les courants s'obtiennent ensuite par `Jx = ∂ψ/∂y`, `Jy = −∂ψ/∂x` (gradients numériques).

### B.4 — Répartition dans l'épaisseur z : peau et régime plaque-mince

La réduction 2D (une équation par plan, pas de résolution du magnétisme *dans* z) n'est légitime que
si l'épaisseur de peau `δ` (A.5) dépasse l'épaisseur des couches conductrices.

> **Exemple chiffré.** Laminé, `σ₀ = 2,2·10⁴ S/m` → `ρ = 4,55·10⁻⁵ Ω·m` ; `ω = 2π·388·10³ = 2,44·10⁶ rad/s`.
> $$\delta = \sqrt{\frac{2\rho}{\mu_0\omega}} = \sqrt{\frac{2\times4{,}55\cdot10^{-5}}{1{,}2566\cdot10^{-6}\times2{,}44\cdot10^{6}}} \approx \sqrt{2{,}97\cdot10^{-5}} \approx 5{,}45\ \text{mm}.$$
> Pour le twill (`σ_plan = 1,1·10⁴`) : `δ ≈ 7,7 mm`. Les deux dépassent l'épaisseur d'une couche
> (0,20–3,36 mm) → **plaque mince valide**. C'est corroboré par l'anisotropie mesurée : conductivité
> transverse `σ_z = 0,64 S/m` ≪ dans le plan `2,2·10⁴` (Grouve 2020) — les courants tournent « à plat ».

Concrètement (`source_joule.source_spot`), `Bz` est échantillonné **nœud z par nœud z** de chaque
couche conductrice (une couche épaisse voit `Bz` décroître entre sa face haute et sa face basse), et
l'écran des couches sus-jacentes est appliqué par un facteur `att = ∏ e^(−2 t_écran/δ_écran)`
(`attenuation_blindage`, remède ad hoc pour le blindage inter-couches non résolu explicitement).

### B.5 — Densité de puissance q(x, y, z)

Une fois `ψ` connu à une profondeur, la dissipation (A.3), généralisée à l'anisotropie
(`foucault.densite_joule`) :

$$q(x,y) = \rho_{xx}\,J_x^2 + \rho_{yy}\,J_y^2\quad[\text{W/m}^3].$$

Répété à chaque nœud z retenu → `q` est bien fonction de `x, y` **et** `z`.

### B.6 — Report sur la grille + le seul paramètre calibré

- **Conservation.** Chaque couche peut couvrir plusieurs nœuds z ; le poids `épaisseur/(len(iz)·dz)`
  répartit la puissance surfacique `q·t` sans la dupliquer ni la perdre (`source_spot`).
- **Grille commune.** `source_spot` assemble `Q(nx, ny, nz)` sur **la même grille** que le solveur
  thermique (par défaut ≈ 49×17×15, soit `dx = dy ≈ 2,5 mm`) → pas de ré-interpolation EM→thermique.
- **Facteur de couplage.** Tout le calcul est multiplié par **un seul scalaire** `facteur_couplage`
  (calibré ≈ **6,0** dans le θ\* de référence ; défaut config 1,0). Il absorbe ce que le modèle EM
  simplifié ne capture pas (blindage réel, contacts fibre-fibre, incertitude sur σ). La **fréquence
  reste figée** à sa valeur mesurée (388 kHz) : sans mesure indépendante elle serait totalement
  corrélée à ce facteur d'échelle (leçon d'identifiabilité).

> **À retenir :** la *forme* de la chauffe est physique (où ça chauffe le plus/le moins) ; seule son
> *échelle absolue* est recalée par ce coefficient — comme on étalonne un thermomètre sans changer
> la physique qu'il mesure.

### B.7 — Terme source du solveur thermique 3D

`Q(x, y, z, t)` entre tel quel dans l'équation de la chaleur (A.4), résolue par
`thermique.solveur3d.SolveurThermique3D` : chaque nœud reçoit `(conduction + Q)/(ρ cp_app)`, où
`cp_app(T)` inclut le pic de chaleur latente de fusion du PEKK (337 °C). Conditions aux limites :
contact conducteur `h_contact` vers un puits refroidi sous l'empreinte MFC/céramique ; convection +
rayonnement ailleurs et en face inférieure ; conduction anisotrope `k_plan`/`k_z`.

---

## C. Résultats obtenus

- **Profil en « M » en largeur** (chants chauds, centre froid) : conséquence **directe** de `ψ = 0`
  au bord (§B.3). Contraste chant/centre ≈ **2,4×**, confirmé bord→centre sur 5 courants (exp7,
  campagne avec céramique) — forme validée, symétrie chant/chant TC1 ≈ TC5.
- **Loi de réglage** : le taux de chauffe suit `∝ I²` (source Joule en `q ∝ Bz² ∝ I²`), fréquence
  mesurée **constante** (388 kHz) sur 150–250 A — cohérent avec le report d'échelle unique.
- **Validation** : confronté sans recalibrage aux campagnes exp7 (largeur) et exp9 (longueur), le
  modèle reproduit la forme (M + décroissance longitudinale) ; le résidu restant est structurel
  (étalement in-plane un peu lent hors-spot), documenté et borné (k_plan effectif ≈ 7,5 vs 3,0
  physique). Le facteur de couplage ≈ 6,0 est le seul paramètre d'échelle de la source.

---

## Annexe — Constantes pour refaire les calculs

| Symbole | Valeur | Source |
|---|---|---|
| `µ₀` | 1,2566·10⁻⁶ T·m/A | constante |
| `f`, `ω = 2πf` | 388 kHz, 2,44·10⁶ rad/s | `generateur.frequence` |
| `σ₀` (sens fibre) | 2,2·10⁴ S/m | `cf_pekk.sigma_0` (Grouve 2020) |
| `σ_plan` (twill) | 1,1·10⁴ S/m | `twill_suscepteur.sigma_plan` |
| `σ_z` (transverse) | 0,64 S/m | `sigma_z` |
| `µr` (MFC) | 16 → `η ≈ 0,88` | `cfc.mu_r` |
| Bobine | jambe 55 mm, entraxe 12,35 mm, h 5 mm | `coil.*` |
| Plaque | 120 × 40 × 6,82 mm | `laminate.*` |
| `facteur_couplage` | ≈ 6,0 (calibré ; 1,0 par défaut) | `materiaux.yaml` |

**Trois calculs témoins :** `η = 15/17 ≈ 0,88` · `δ_laminé ≈ 5,45 mm`, `δ_twill ≈ 7,7 mm` ·
`B_fil(200 A, 5 mm) ≈ 8 mT`. Si vous retrouvez ces trois nombres, vous avez reproduit les briques
clés de la chaîne EM → Joule → thermique.
