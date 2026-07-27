# Exp 7 — Cartographie bord→centre, série SANS céramique (1re série)

**Date** : 2026-07-27 &nbsp;·&nbsp; **Opérateur** : Maxence &nbsp;·&nbsp; **Objectif** : profil de
température en travers de la largeur (le « M »).

> Manip d'abord étiquetée « exp 6 / diffusivité », mais elle réalise en fait la cartographie
> bord→centre (exp 7) : 5 TC EN LARGEUR au spot 3. **Céramique d'espacement + pression RETIRÉES**
> → géométrie non standard (gap ≈ 0). La reprise AVEC céramique est dans
> `../exp7_bord-centre_2026-07-28_avec-ceramique/`.

---

## Description de l'essai (à remplir)

- **Courant** : 200 A  (fréquence associée : 250 A → 388 kHz, 200 A → 383 kHz)
- **Durée de chauffe / maintien** : A voir sur le dossier .txt (il faudra enlever les données en trop dans le fichier .txt)
- **Céramique d'espacement** : retirée (entoure) → si retirée, gap bobine-laminé ≈ 0
- **Système de pression** : retiré
- **Position de la caméra** : de côté, distance 230mm , lens de 17mm 
- **Zone imagée** : surface du laminé au-delà de l'empreinte du CFC, côté (x croissant)
- **Repère spatial** : où est le centre du spot dans l'image (px ou mm) ? échelle mm/px ? Je ne sais pas
- **Émissivité réglée** : 0.6mm (le carbone/PEKK ~0,9 ; à confirmer)
- **Température ambiante** : 23°C °C
- **Cadence d'acquisition** : Je ne sais pas

## Ce que j'ai fait (ton texte libre)

J'ai placé ma caméra thermique de façon à observer la surface/ côté de mon échantillon 
puis j'ai ensuite placé mes thermocouples le long de la largeur de mon échantillon 
la largeur sélectionnée à était celle correspondant au spot numéro 3. Ils sont tous placés à équidistances avec TC1 et TC5 au bord 
du spot chauffé. J'ai ensuite appliqué un courant de 200A et quand je considérais que la température était allé assez loin en 
température j'ai arrêté de chauffé mes échantillons. Je te laisse remplir la suite de ce document. 

---

## Format des données exportées (pour l'analyse)

Idéalement, exporte depuis FLIR Tools / ResearchIR l'un de ces formats (préférence
décroissante) :

1. **CSV ROI vs temps** : une ligne de mesure dans l'axe x (ou ~5 points à distances
   croissantes du spot) → colonnes `temps, T@d1, T@d2, …` avec les distances d1..dn notées.
2. **CSV température par image** : matrices T(x,y) par frame (ou au moins la frame au pic).
3. **Frames PNG avec la barre d'échelle** de température visible.

Fichiers (3 essais, même montage, 5 TC en largeur au spot 3, format FR) :
- `150A.txt` — **150 A / 390 kHz**.
- `200A.txt` — **200 A / 383 kHz**.
- `250A.txt` — **250 A / 388 kHz**.
- `camera_200A.mp4` — **CORROMPU / illisible** (voir Résultat ; hors dépôt, gitignore).

## Résultat (analyse Claude, 2026-07-27)

**⚠ Cette manip est en fait la cartographie bord→centre (exp 7)**, pas la diffusivité : les
5 TC sont répartis EN LARGEUR au spot 3 (TC1..TC5 supposés à y = 0/10/20/30/40 mm, TC1/TC5
aux chants). Elle teste donc directement le profil en « M ».

**Vidéo : illisible.** Le MP4 est incomplet — l'atome `moov` (index, écrit à la clôture)
manque ; seules les frames brutes (`mdat`) sont présentes, non décodables. Enregistrement non
finalisé (caméra arrêtée avant clôture, ou export FLIR tronqué). À ré-exporter depuis la
source FLIR, ou fournir une vidéo de référence (même caméra/réglages) pour tenter une
reconstruction. La vidéo n'entre donc PAS dans ce résultat.

**Profil en largeur au pic — ΔT au-dessus de l'ambiant (TC fiables ; TC1 écarté) :**

| essai | y=10 | y=20 (**centre**) | y=30 | y=40 (chant) | chant/centre |
|---|---|---|---|---|---|
| 150 A / 390 kHz | 150 | **111** | 151 | 150 | 1,35 |
| 200 A / 383 kHz | 116 | **78** | 124 | 146 | 1,88 |
| 250 A / 388 kHz | 139 | **96** | 146 | 178 | 1,85 |
| **modèle (cible)** | 382 | **292** | 382 | 717 | **2,46** |

**Ce que ça établit (reproduit sur 3 courants) :**
1. **Le centre (y=20) est un CREUX aux trois courants** : minimum local, plus froid que ses
   voisins → **le profil en « M » est RÉEL**, pas un artefact numérique.
2. **Le centre chauffe le plus LENTEMENT** (4-5 °C/s vs 9-19 aux côtés) → alimenté par
   conduction latérale, pas par la source directe (cohérent M-vallée).
3. **Le modèle SUR-CONTRASTE** : contraste chant/centre mesuré **1,35 à 1,88** contre **2,46**
   prédit — même sens que le point du chauffe (395 mesuré vs 292 prédit). Le M mesuré est plus
   doux que le M du modèle. (Le 150 A est le plus doux : chauffe plus lente/longue → plus de
   temps pour que la conduction remplisse la vallée ; NB départ à chaud, ambiant 38 °C.)

**TC1 (y=0) écarté partout** : incohérent d'un essai à l'autre (ΔT 235 à 150 A — erratique,
pics à 275/197/167 = contact intermittent ; ~50, quasi mort, à 200/250 A).

**Réserves (empêchent la falsification QUANTITATIVE de l'amplitude) :**
- **Géométrie non standard** : céramique + pression retirées → gap ≈ 0 → source EM plus forte
  et de forme différente du modèle. Absolus non comparables à la cible 717/382/292 ; seule la
  FORME (contraste) est exploitée.
- **TC1 mort** (un des deux chants) → symétrie non vérifiable ; profils un peu asymétriques
  (montée vers y=40 à 200/250 A) → spot probablement non centré.
- Interface vs surface des TC non précisé (supposé interface).

**Conclusion.** Évidence directe et **reproduite sur 3 courants** que la **vallée centrale du M
est réelle** et que le modèle **sur-contraste** (1,35-1,88 mesuré vs 2,46). Solide sur la
FORME ; l'AMPLITUDE absolue reste à caler par une **reprise propre** (géométrie standard avec
céramique, 5 TC valides à l'interface, montage symétrique — checklist fiche exp 7 de
`mesures_a_realiser.md`).

**Figures** : `tc_courbes.png` (courbes des 5 TC, 3 essais), `profil_largeur.png`
(profil en largeur, 3 courants).
