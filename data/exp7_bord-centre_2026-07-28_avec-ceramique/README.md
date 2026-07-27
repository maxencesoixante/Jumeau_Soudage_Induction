# Exp 7 — Cartographie bord→centre AVEC céramique (reprise propre)

**Date** : 2026-07-28 &nbsp;·&nbsp; **Opérateur** : Maxence &nbsp;·&nbsp; **Objectif** : caler
l'**amplitude** du profil en « M » (falsification quantitative contre la cible du modèle).

> Reprise contrôlée de la série `../exp7_bord-centre_2026-07-27_sans-ceramique/` (qui avait la
> céramique retirée → géométrie non standard, amplitude non comparable). Ici : **céramique en
> place** = géométrie du modèle. Dépose les fichiers ici et remplis la description.

---

## Checklist (corrige les 4 réserves de la 1re série)

- [ ] **Céramique d'espacement EN PLACE** (+ pression nominale) → gap 2 mm standard.
- [ ] **5 TC valides à l'INTERFACE**, y = 0/10/20/30/40 mm, x = 60 mm. **TC1 remplacé** ;
      chaque voie vérifiée avant l'essai (toutes à l'ambiant, sans saut).
- [ ] **Montage CENTRÉ en largeur** (viser TC1↔TC5 symétriques à l'ambiant).
- [ ] **200 A** ; fréquence **383 kHz**.
- [ ] **Caméra** (optionnelle) : enregistrement **bien finalisé**, ou export **CSV radiométrique**.

## Cible du modèle **à 200 A** (spot centré, θ\* de référence, au pic ≈ 46 s) — à confronter

| y (mm) | 0 | 10 | 20 (centre) | 30 | 40 |
|---|---|---|---|---|---|
| T_pic prédite (°C) | 468 | 276 | **207** | 276 | 468 |

**Contraste bord/centre prédit = 2,26×** (à 250 A ce serait 2,46 ; cible 717/382/292).
La 1re série sans céramique donnait un contraste 1,35-1,88 (modèle sur-contraste) mais en
géométrie non standard → cette série AVEC céramique doit le trancher quantitativement.
NB : cible calculée avec la fréquence globale du modèle (388 kHz) ; l'écart à 383 kHz est
négligeable (~1 % sur la profondeur de peau).

## Description de l'essai (à remplir)

- **Courant / fréquence** : ______ A / ______ kHz
- **Céramique** : en place ✔ / retirée &nbsp;·&nbsp; **Pression** : ______
- **Durée de chauffe** : ______ s
- **Positions TC** (interface, y en mm) : TC1=___ TC2=___ TC3=___ TC4=___ TC5=___
- **Vérification des voies avant essai** (toutes propres ?) : ______
- **Caméra** : position ______ , émissivité ______ , export : vidéo finalisée / CSV radiométrique

## Ce que j'ai fait (texte libre)

_(déroulé, observations, aléas…)_

## Fichiers déposés

- `200a v2 ceram.txt` — 200 A, céramique en place, 5 TC en largeur au spot 3.
- `analyse_200A_ceramique.png` — courbes + comparaison de forme mesuré/modèle.

## Résultat (analyse Claude, 2026-07-28)

**En bref : avec la géométrie standard, le modèle a RAISON sur l'amplitude du profil en « M ».**

Profil ΔT au pic (TC1 encore mort — voir plus bas) :

| y (mm) | 0 | 10 | 20 (centre) | 30 | 40 | contraste chant/centre |
|---|---|---|---|---|---|---|
| **mesuré** | (TC1 mort) | 141 | **89** | 119 | 192 | **2,17** |
| **modèle 200 A** | 444 | 252 | **183** | 252 | 444 | **2,43** |

- **Le contraste mesuré (2,17) est PROCHE du modèle (2,43)** ; la *forme normalisée* se superpose
  presque sur y = 10/20/30/40 (cf. `analyse_200A_ceramique.png`, panneau droit).
- **Révision majeure** : le « sur-contraste » observé dans la série SANS céramique
  (1,35-1,88 vs 2,46) venait surtout du **retrait de la céramique** (gap ≈ 0 → source aplatie),
  PAS d'un défaut du modèle. Avec la céramique = géométrie du modèle, le M est bien reproduit.
  → **Le levier « adoucir le M » n'est donc plus justifié** ; l'amplitude du M est ~correcte.

**Réserves.**
- **TC1 (y=0, un chant) toujours mort** (reste à l'ambiant) → le point d'extrémité y=0 manque ;
  le contraste s'appuie sur TC5 (y=40), fiable. Symétrie non vérifiable.
- **Absolus non confrontés** : la chauffe manuelle s'est arrêtée tôt (pic mesuré ~15-25 s,
  TC5 ~219 °C ; le modèle vise ~46 s / plus chaud) → seule la FORME (contraste) est comparée,
  pas l'amplitude en °C.
- Léger reste d'asymétrie (côté y=10 un peu plus chaud que y=30) + essai unique → à confirmer,
  idéalement avec TC1 réparé et une chauffe plus longue/standardisée.
