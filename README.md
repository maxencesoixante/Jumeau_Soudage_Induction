# Jumeau numérique — soudage par induction CF/PEKK

Simulation Python de l'**empreinte thermique** créée par la bobine hairpin +
concentrateur de flux (MFC Fluxtrol Ferrotron 559H) sur les laminés CF/PEKK
du montage semi-statique (maîtrise, LIPEC/ÉTS). Le modèle produit une **carte
de température 3D** (plan 120×40 mm × épaisseur du stack) confrontée aux
mesures thermocouples des essais (Séries A/B + essais de chauffe).

## Montage & géométrie

Cotes du montage (coupon CF/PEKK, concentrateur MFC, bobine hairpin) et
positions des thermocouples à l'interface, vues de dessus (plan x–y) et en
coupe (échelle 1:1). Coupon **120 × 40 mm**, MFC Ferrotron 559H **31,5 mm (x)
× 55 mm (y)**, bobine hairpin en tube Cu **6 × 6 mm**, entraxe brins
**12,35 mm**, interface à **z = 3,36 mm**, film twill 0,10 mm.

**exp7 — cartographie en largeur (profil « M »), 5 TC à x = 60 mm, y = 0/10/20/30/40 mm :**

![Montage exp7 — cartographie en largeur](docs/figures/schema_montage_exp7.png)

**exp9 — dissipation longitudinale, 5 TC au bord (y = 0), x = 0/30/60/90/120 mm :**

![Montage exp9 — dissipation longitudinale](docs/figures/schema_montage_exp9.png)

## Chaîne physique

1. **Champ magnétique** — Biot-Savart analytique de la bobine hairpin
   (polyligne de segments) ; MFC traité par **courants images** à travers un
   demi-espace perméable, facteur (µr−1)/(µr+1) ≈ 0,88 (µr = 16).
2. **Courants de Foucault** — plaque mince (δ ≈ 6 mm à 300 kHz > épaisseur),
   fonction de courant ψ résolue par différences finies 2D par couche
   conductrice (formulation Lin 1993) : twill suscepteur à l'interface +
   laminés homogénéisés (σ_eff quasi-iso, Grouve 2020 Table 1).
3. **Source Joule** — q = ρxx·Jx² + ρyy·Jy² par couche, déposée sur la grille
   3D avec conservation de la puissance surfacique.
4. **Thermique 3D transitoire** — méthode des lignes (BDF, jacobien sparse),
   cp apparent avec pic gaussien de fusion (Tf = 337 °C, Lf = 130 kJ/kg,
   porté du notebook 1D validé), CL : convection + rayonnement faces libres,
   conductance vers le puits céramique/concentrateur refroidi sous l'empreinte
   active (O'Shaughnessey 2014), passes séquentielles 4 empreintes.
5. **Calibration** — LHS + NLSQ pondéré par bruit capteur (pipeline du
   notebook 1D) sur [facteur_couplage, h_contact, h_bas], calibré sur UN
   essai, validé sur les autres SANS recalibrage.

## Hypothèses simplificatrices (assumées, sourcées)

| Hypothèse | Source / justification |
|---|---|
| Plaque mince EM, courants plans | Lin 1993 ; δ(300 kHz, σ0) ≈ 6 mm > 3,36 mm |
| Champ de réaction (blindage) négligé | absorbé par `facteur_couplage` ; **justifié quantitativement** par vérif croisée `eppy` : réaction ≤ 0,03 % du contraste au régime twill (`docs/modele/verification_croisee_eppy.md`) |
| MFC = demi-espace perméable (images) | approx. 1er ordre de la concentration de flux |
| Laminé homogénéisé (σ, k quasi-iso plan) | O'Shaughnessey 2014 (Annexes I-II) ; Grouve 2020 |
| µr = 1 pour le laminé | Grouve 2020 (Lionetto 2017) |
| Fusion via cp apparent gaussien | notebook 1D / Samanis et al. 2026 éq. 2-3 |
| Fréquence FIGÉE à 388 kHz | relevé machine du 2026-07-17 (EASYHEAT à 250 A) ; elle reste corrélée au facteur d'échelle → seul le facteur est calibré (leçon black-box f_I/r_I) |
| Bobine + MFC refroidis → puits 20 °C | O'Shaughnessey 2014 (COMSOL, refroidissement eau) |
| Pertes diélectriques négligées | O'Shaughnessey 2014 §3.1.3 |
| Pertes propres du MFC (Joule + hystérésis, Ferrotron 559H) non modélisées | négligeable : vérifié 2026-07-20 via la courbe de pertes constructeur (Fluxtrol *Ferrotron 559H* datasheet, µᵢ=16, ρ>15 kΩ·cm, Pv=4,1·f¹·¹·B²·⁵ W/cm³) — ≈0,6–1,4 W dissipés dans tout le bloc MFC à 250 A/388 kHz, contre ~50–260 W dans le twill ; 1 à 2 ordres de grandeur sous le déficit local requis à TC1 (cf. « Limites connues ») |

## Limites connues

- Les **dimensions de la bobine hairpin** : tubes carrés de **6 mm de côté**,
  **gap 6,35 mm** entre brins (entraxe centre-à-centre **12,35 mm**), brins le
  long du grand côté du MFC. **Orientation MFC confirmée** (2026-07-17) : 55 mm
  parallèle à la largeur y des échantillons. **CORRECTION 2026-07-23** : la
  valeur antérieure (tubes ~9,5 mm, entraxe ~19 mm) était fausse ; la corriger a
  résolu l'essentiel du dépassement de pic A-1 (|ΔT_max| 46→15 °C à `k_plan=3`
  physique — cf. `journaux/resultats_geometrie_corrigee_recalibration.log`) : ce
  « déficit structurel » était en grande partie un artefact de cette entrée.
- Les **positions des TC des Séries A/B** ont été confirmées par l'utilisateur
  (2026-07-20) : les 5 TC sont TOUS à l'interface (repère cahier origine-milieu
  converti au repère modèle origine-coin) — TC1 au bord de longueur / centre de
  largeur (x=0, y=20 mm), TC2–TC5 au bord de largeur (y=0). Remplace l'ancienne
  hypothèse « TC1 surface / TC alignés sur les spots ». **Position TC1 re-confirmée
  terrain le 2026-08-04 (issue #8) : y=20 mm, centre de largeur.** L'hypothèse
  « TC1 au coin y=0 » (que la donnée *simulée* semblait favoriser, coin plus froid ≈
  mesuré) est **rejetée** : elle n'aurait fait que *fitter* l'erreur de profil en M.
  La surestimation du pic TC1 (A-1 : 671 simulé vs 398 mesuré au centre de largeur)
  est donc un **vrai déficit modèle** (M en largeur trop contrasté, cf. étalement
  in-plane), pas un artefact de position.
- **Puits de bord `h_bord_x0` (montage bridé x=0)** : le modèle 2D lumpé
  surchauffait TC1 (+185 à +273 °C au pic) car la chaleur du spot 1 (~16 mm du
  bord x=0) restait piégée contre le chant quasi-adiabatique. Un puits conductif
  additionnel au chant x=0 SEUL (`Ambiant.h_bord_x0`, représentant le
  bridage/appui du montage, asymétrie confirmée par l'utilisateur) calibré à
  **250 W/m²·K** (balayage sur A-1, validation A-3/B-2) ramène le pic TC1 dans
  ±25–70 °C sans dégrader les autres TC.
- **Résidu B-2 (sous-étalement en x à basse consigne)** : après la correction de
  géométrie, B-2 (consigne 360 °C vs 400 pour A-1, même géométrie) sous-chauffe
  les TC inter-spots TC2-4 de 30–55 °C (|ΔT_max| ~35). À basse consigne, les
  impulsions coupent tôt (le centre du spot atteint la consigne vite) → la
  chaleur s'étale moins en x → les TC à ~15 mm restent froids ; le vrai process
  coupait quand le TC lui-même atteignait la consigne (impulsions plus longues).
  Trois correctifs prototypés + recalibrés + validés croisés ont été **réfutés**
  (`journaux/resultats_diag_b2_longueur.log`) : décalage de la position de contrôle
  (casse A-1), marge de consigne `consigne+Δ` (échange A-1 contre B-2, sens
  opposés — total constant), et `h_haut`/force 25 N (neutralisé par le
  thermostat). **Limite structurelle connue** du modèle 2D lumpé au régime
  basse-consigne / impulsions courtes ; non corrigeable sans casser A-1.
- **Le résidu TC4 documenté auparavant (+74 à +110 °C) était très majoritairement
  un artefact de discrétisation, pas un déficit physique** (étude de convergence
  maillage 2026-07-21, `journaux/resultats_convergence_maillage.log`). Décomposition
  chiffrée sur la grille de calibration 31×11 (A-1/A-3/B-2) :
  - **Snapping de la LECTURE des TC** (`Grille3D.indice_xy`, nœud le plus
    proche) : TC4 (x=90 mm) tombait pile à mi-distance entre deux nœuds à
    dx=4 mm → lecture décalée de 2 mm sur un profil pointu. Isolé sans
    resimuler (lecture nœud-le-plus-proche vs bilinéaire sur le même champ) :
    **-77,4 °C (A-1), -60,4 °C (A-3), -61,9 °C (B-2)** sur `delta_T_max` TC4 à
    lui seul — la quasi-totalité du résidu. Corrigé : `serie_temporelle` des
    deux solveurs interpole désormais bilinéairement en (x, y) (`bracket_lineaire`,
    `thermique/solveur3d.py`).
  - **Snapping du NŒUD DE CONTRÔLE du thermostat** (`Essai._T_ctrl`, ancien
    nœud le plus proche de `centre_x`) : effet quasi nul sur TC4 lui-même
    (<0,3 °C) mais **important sur TC5** (A-1 : -56,2 °C sur `delta_T_max`,
    81,4→25,1 °C — l'instant de coupure de la dernière passe dépendait du
    maillage). Corrigé : `Essai._T_ctrl` interpole désormais linéairement en x
    entre les deux nœuds encadrant `centre_x` (`Essai.interp_ctrl=True` par
    défaut ; `False` conservé pour ablation/comparaison) — la sparsité du
    jacobien (`_noeuds_controle`/`_noeuds_controle_2d`) déclare bien les DEUX
    colonnes désormais couplées, pour ne pas réintroduire la régression BDF du
    2026-07-20.
  - **`h_bord_x0` n'explique PAS le résidu TC4** : `delta_T_max` TC4 est
    identique à ±1 °C près avec `h_bord_x0=250` et `h_bord_x0=0`, à tous les
    maillages testés (31×11 à 121×41) — c'est un puits strictement local au
    chant x=0 (loin de TC4, x=90 mm), sa calibration n'est PAS contaminée par
    le résidu TC4.
  - **Résidu restant après les deux corrections** (discrétisation thermique
    nx,ny vraie + quadrature EM nz, cf. ci-dessous) : `delta_T_max` TC4 va de
    +32,7 °C (31×11) à +50,5 °C (121×41) sur A-1 (dérive encore de quelques
    dizaines de °C, ordre de convergence non propre sur ce pic — cf. rapport) ;
    RMSE TC4, lui, est convergé à <1,5 °C près dès 31×11. **`nz` (nombre de
    nœuds dans l'épaisseur) a un effet négligeable en 2D** (<1,5 °C sur
    `chauffe_250A_3TC`, <0,3 °C sur A-1, nz de 9 à 41) : `SolveurThermique2D`
    lui-même l'ignore, mais `Essai` l'utilise pour échantillonner la
    profondeur de la source EM (`procede.py`, `P_surf = Σ_z Q·dz`) — effet réel
    mais mineur.
  - **Maillage par défaut retenu pour `scripts/valider.py` : 61×21×15** (dx=dy=
    2 mm, ~2-4 min/essai) — meilleur compromis coût/résiduel identifié ; 31×11
    reste la grille de CALIBRATION (`scripts/calibrer.py`, volontaire, non
    modifiée par cette étude — θ* n'a PAS été recalibré).
- Le **découpage temporel des 4 passes** (t_debut/t_fin par spot) est un
  découpage uniforme par défaut — à ajuster en lisant les vagues de chauffe
  sur les courbes TC mesurées.
- Modèle sans mécanique (pression, squeeze-out) ni cristallisation.
- **Profil en « M » prédit** : la carte d'interface montre deux lobes chauds
  vers les bords libres (y = 0/40 mm) et un creux au centre (J = 0 au centre
  de la boucle de courants induits ; retours de courant confinés aux chants).
  Qualitativement cohérent avec le squeeze-out observé sur les chants et la
  reco COMPAAM (réduire le MFC pour limiter les effets de bord), mais
  l'amplitude du contraste bord/centre est probablement exagérée.
  **Diagnostic 2026-07-27** (`journaux/resultats_diag_forme_source.log`) : le champ `Bz`
  est déjà UNIFORME sur la largeur (0,95→1,00) — le M ne vient donc PAS de la
  forme du champ ni de la semelle du MFC, mais **entièrement de l'écrasement du
  courant de Foucault** contre les chants (`ψ = 0` au bord d'une nappe continue
  idéalisée). Contraste bord/centre ~2,4× en source intégrée ; le « q ≈ 0 au
  centre » est l'œil de boucle (point de courant nul), un minimum ponctuel sur
  la ligne de symétrie où tombe justement TC2 de l'essai de chauffe. Corollaire :
  un modèle de MFC fini n'y changera rien (il vaut pour le profil en longueur) ;
  les leviers d'adoucissement sont les courants de retour 3D et la résistance de
  contact du twill tissé — non calibrables sans mesure.
  **Vérification croisée EM 2026-08-04** (`docs/modele/verification_croisee_eppy.md`) :
  un second solveur indépendant (`eppy`, Grouve/Nagel 2019, isotrope, sans MFC) reproduit
  le **même contraste** (~3,0 ≈ notre 3,15) → le M sur-contrasté est de la **vraie physique
  plaque-mince** (écrasement du courant au chant), **pas** un artefact de notre anisotropie,
  des images MFC ni de la discrétisation. L'écart au contraste mesuré (2,09, réduction requise
  ~ −34 %) est la limite d'**étalement in-plane** documentée, pas un bug EM. Code vendoré :
  `third_party/eppy/`.
  **Test expérimental direct : la cartographie bord→centre** (5 TC d'interface à
  y = 0/10/20/30/40 mm, x = 60 mm), cible chiffrée 717/382/292/382/717 °C au pic.
- **TC1 (surface côté bobine) chauffe 5–6× trop lentement dans le modèle** (diagnostic thermal-solver-engineer, 2026-07-18/20 : 37,7 °C/s mesuré vs ~6,3 °C/s simulé, essai `chauffe_250A_3TC`). Trois explications ont été testées et **écartées** :
  - condition limite thermique (`h_contact=0` ne change quasiment rien, 6,38→6,42 °C/s) et diffusion (couper la source dans le laminé sup. fait chuter TC1 à 0,98 °C/s, τ_diffusion≈28,5 s ≫ 1 s) ;
  - auto-échauffement du MFC (Ferrotron 559H) : ≈0,6–1,4 W chiffrés via la fiche constructeur, 1–2 ordres de grandeur trop faible même dans l'hypothèse la plus généreuse ;
  - artefact de positionnement `decalage_x` (le hairpin a un zéro de dissipation exact sur son plan de symétrie près de TC1) : balayage EM de `decalage_x` sur [0, 0.015] m (diagnostic jusqu'à 0.050 m), le rapport `Q(TC1)/Q(TC2)` culmine à **0,12** vers 7 mm et reste 5–50× sous 1 sur tout le domaine, alors que la cible mesurée est `taux_TC1/taux_TC2 ≈ 1,71`. Décaler la bobine déplace le zéro de champ mais ne peut pas inverser la hiérarchie de résistivité inter-couches (TC1 dans `lamine_sup` ρ≈3,7 mΩ·m, TC2 dans `twill_suscepteur` ρ≈0,09 mΩ·m, ~40× plus conducteur).

  **Mécanisme manquant non identifié** — le déficit est structurel (répartition de puissance entre couches, ou effet de champ proche à cette hauteur z non capturé par le modèle de plaque mince), pas un artefact de positionnement ni une perte au contact. Aucune mesure de la température du MFC lui-même n'existe dans les essais actuels (TC1-3 sont tous sur le laminé, TC4/TC5 débranchés). Mesure discriminante proposée : thermocouple ou caméra IR sur la face active du MFC pendant un essai de chauffe.

## Utilisation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                                   # vérifications analytiques + régression 1D

# simulation d'un essai + figures (resultats/)
python scripts/simuler_essai.py config/essais/chauffe_250A_3TC.yaml

# calibration sur l'essai de chauffe, puis validation croisée sans recalibrage
python scripts/calibrer.py --essai chauffe_250A_3TC
python scripts/valider.py --facteur <F> --h-contact <H> --h-bas <H>
```

## Données

`data/` contient des **copies** des mesures du vault Obsidian
(`~/Obsidian/Memoire_Soudage_Induction/40_donnees/`) — la source de vérité
reste le vault. TC de l'essai de chauffe : TC1 = surface côté bobine,
TC2 = interface (tissu PW), TC3 = face opposée (README essais_chauffe).

## Sources bibliographiques (vault)

- O'Shaughnessey 2014 (même labo) — homogénéisation, CL, sensibilité (I, f, gap, σ).
- Grouve 2020 — propriétés C/PEKK, µr=1, tenseur σ, h=10 W/m²K.
- Lionetto et al. 2017 (*Materials & Design* 120, 212–221, doi:10.1016/j.matdes.2017.02.024)
  — modèle EF du soudage induction continu CF/PAEK : propriétés homogénéisées, µr=1,
  σ(T), fusion (Greco–Maffezzoli) et cristallisation (Ozawa). **Référence de l'audit du
  modèle** (`docs/modele/audit_lionetto_2017.md`).
- Buser et al. 2025 (*Composites Part A* 188, 108550) — mesure de la conductivité
  électrique **longitudinale** des rubans CFRP UD ; sous-jacente à la question `k_plan`.
- Buser et al. 2026 (*Composites Part A* 209, 109986) — conductivité électrique
  **transverse** (dans le plan), méthode à six pointes.
- Bard et al. — revêtement Cu/Ni des fibres de carbone pour composites thermiquement /
  électriquement conducteurs ; référence d'homogénéisation σ/k.
- Van Otterloo — « How isotropic are quasi-isotropic laminates » : anisotropie in-plane
  des quasi-iso (piste `k_plan` anisotrope).
- Lin 1993 — différences finies 2D, courants dans les fibres, plaque mince.
- Grouve — solveur **`eppy`** (github.com/wjbg/eppy, MIT, commit épinglé `62f0030`, validé
  contre **Nagel 2019** fig. 6) : 2ᵉ solveur EM plaque mince indépendant (potentiel vecteur
  électrique `T` ≡ notre `ψ`), **vendoré** sous `third_party/eppy/` (copie MIT patchée
  numpy ≥ 2, provenance `third_party/eppy/NOTICE.md`) pour la vérification croisée code-à-code
  de `em/foucault.py` (`docs/modele/verification_croisee_eppy.md`, script
  `scripts/verif_eppy_reaction.py`).
- Duhovic 2012 — skin depth, ≥2 éléments dans la peau, convection.
- Brassard et al. 2020 (*J. Composite Materials*, doi:10.1177/0021998320957055) — modèle EF
  COMSOL 3D du **soudage par résistance** CF/PEEK à élément chauffant nanocomposite :
  couplage électro-thermique one-way, propriétés k(T)/cp(T) **mesurées** (MTPS/MDSC),
  résistance de contact ≈ facteur d'échelle. Dépôt de référence analysé dans
  [`docs/reference_brassard.md`](docs/reference_brassard.md) (modèle + méthodo figures).
- Fluxtrol Inc. — *Ferrotron 559H* datasheet (rev. 06/02/15, fluxtrol.com) — propriétés matériau constructeur (µᵢ=16, ρ>15 kΩ·cm, courbe de pertes Pv=4,1·f¹·¹·B²·⁵) utilisée le 2026-07-20 pour chiffrer l'auto-échauffement du MFC (négligeable, cf. tableau des hypothèses).
- Samanis et al. 2026 — méthode des lignes 1D, identification, test black-box.
