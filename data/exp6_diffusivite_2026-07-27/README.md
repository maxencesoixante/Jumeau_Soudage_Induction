# Exp 6 — Cartographie latérale de la diffusivité (caméra thermique)

**Date** : 2026-07-27 &nbsp;·&nbsp; **Opérateur** : Maxence &nbsp;·&nbsp; **Objectif** : mesurer la
décroissance latérale de température en surface → `k_plan` effectif.

> Dépose ici les fichiers exportés (CSV radiométrique de préférence — voir plus bas — ou
> frames PNG avec échelle) et remplis la description ci-dessous. Claude analysera à partir de
> ce dossier.

---

## Description de l'essai (à remplir)

- **Courant** : ______ A  (fréquence associée : 250 A → 388 kHz, 200 A → 383 kHz)
- **Durée de chauffe / maintien** : ______ s
- **Céramique d'espacement** : présente / retirée (entoure) → si retirée, gap bobine-laminé ≈ 0
- **Système de pression** : présent / retiré
- **Position de la caméra** : au-dessus, distance ______ , champ de vue ______
- **Zone imagée** : surface du laminé au-delà de l'empreinte du CFC, côté ______ (x croissant)
- **Repère spatial** : où est le centre du spot dans l'image (px ou mm) ? échelle mm/px ? ______
- **Émissivité réglée** : ______  (le carbone/PEKK ~0,9 ; à confirmer)
- **Température ambiante** : ______ °C
- **Cadence d'acquisition** : ______ Hz

## Ce que j'ai fait (ton texte libre)

_(décris le déroulé : montage, ce que tu observes, particularités, aléas…)_

---

## Format des données exportées (pour l'analyse)

Idéalement, exporte depuis FLIR Tools / ResearchIR l'un de ces formats (préférence
décroissante) :

1. **CSV ROI vs temps** : une ligne de mesure dans l'axe x (ou ~5 points à distances
   croissantes du spot) → colonnes `temps, T@d1, T@d2, …` avec les distances d1..dn notées.
2. **CSV température par image** : matrices T(x,y) par frame (ou au moins la frame au pic).
3. **Frames PNG avec la barre d'échelle** de température visible.

Fichiers déposés :
- ______

## Résultat (rempli par l'analyse)

_(à compléter : longueur de décroissance, k_plan estimé, confrontation au modèle 3D surface)_
