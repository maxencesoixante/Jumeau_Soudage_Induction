# Jumeau numérique — soudage par induction CF/PEKK

Simulation Python de l'**empreinte thermique** créée par la bobine hairpin +
concentrateur de flux (CFC Fluxtrol Ferrotron 559H) sur les laminés CF/PEKK
du montage semi-statique (maîtrise, LIPEC/ÉTS). Le modèle produit une **carte
de température 3D** (plan 120×40 mm × épaisseur du stack) confrontée aux
mesures thermocouples des essais (Séries A/B + essais de chauffe).

## Chaîne physique

1. **Champ magnétique** — Biot-Savart analytique de la bobine hairpin
   (polyligne de segments) ; CFC traité par **courants images** à travers un
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
| Champ de réaction (blindage) négligé | absorbé par `facteur_couplage` calibré |
| CFC = demi-espace perméable (images) | approx. 1er ordre de la concentration de flux |
| Laminé homogénéisé (σ, k quasi-iso plan) | O'Shaughnessey 2014 (Annexes I-II) ; Grouve 2020 |
| µr = 1 pour le laminé | Grouve 2020 (Lionetto 2017) |
| Fusion via cp apparent gaussien | notebook 1D / Samanis et al. 2026 éq. 2-3 |
| Fréquence FIGÉE à 388 kHz | relevé machine du 2026-07-17 (EASYHEAT à 250 A) ; elle reste corrélée au facteur d'échelle → seul le facteur est calibré (leçon black-box f_I/r_I) |
| Bobine + CFC refroidis → puits 20 °C | O'Shaughnessey 2014 (COMSOL, refroidissement eau) |
| Pertes diélectriques négligées | O'Shaughnessey 2014 §3.1.3 |

## Limites connues

- Les **dimensions de la bobine hairpin** sont mesurées sur la CAO du montage
  (`positionnement_CFC+coil.png`, échelle = CFC 55 mm) : tubes carrés ~9,5 mm,
  entraxe ~19 mm, brins le long du grand côté du CFC — à raffiner si la cote
  exacte de la CAO SolidWorks est extraite. **Orientation CFC confirmée**
  (2026-07-17) : 55 mm parallèle à la largeur y des échantillons.
- Les **positions plan (x, y) des TC des Séries A/B** sont une hypothèse
  documentée dans `config/essais/*.yaml` (TC1 surface / TC2–5 interface est
  confirmé par le notebook du vault ; la répartition sur les 4 empreintes
  reste à confirmer au cahier).
- Le **découpage temporel des 4 passes** (t_debut/t_fin par spot) est un
  découpage uniforme par défaut — à ajuster en lisant les vagues de chauffe
  sur les courbes TC mesurées.
- Modèle sans mécanique (pression, squeeze-out) ni cristallisation.
- **Profil en « M » prédit** : la carte d'interface montre deux lobes chauds
  vers les bords libres (y = 0/40 mm) et un creux au centre (J = 0 au centre
  de la boucle de courants induits ; retours de courant confinés aux chants).
  Qualitativement cohérent avec le squeeze-out observé sur les chants et la
  reco COMPAAM (réduire le MFC pour limiter les effets de bord), mais
  l'amplitude du contraste bord/centre est probablement exagérée : le modèle
  d'images ne capture pas la redistribution du flux par la semelle du CFC.
  **Test expérimental direct : la cartographie bord→centre proposée au cahier
  §2.1.4** (3–5 TC en ligne sur la largeur).

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
- Lin 1993 — différences finies 2D, courants dans les fibres, plaque mince.
- Duhovic 2012 — skin depth, ≥2 éléments dans la peau, convection.
- Samanis et al. 2026 — méthode des lignes 1D, identification, test black-box.
