# Exp 6 — Cartographie latérale de la diffusivité (caméra thermique)

**Date** : 2026-07-27 &nbsp;·&nbsp; **Opérateur** : Maxence &nbsp;·&nbsp; **Objectif** : mesurer la
décroissance latérale de température en surface → `k_plan` effectif.

> Dépose ici les fichiers exportés (CSV radiométrique de préférence — voir plus bas — ou
> frames PNG avec échelle) et remplis la description ci-dessous. Claude analysera à partir de
> ce dossier.

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

Fichiers déposés :
- `200A résultats TC.txt` — 5 TC en largeur au spot 3, 611→760 s (~1 Hz), format FR.
- `250A 5TC Camera.txt` — **2e essai à 250 A**, même montage, 5 TC en largeur au spot 3.
- `thermal camera 200A.mp4` — **CORROMPU / illisible** (voir Résultat).

## Résultat (analyse Claude, 2026-07-27)

**⚠ Cette manip est en fait la cartographie bord→centre (exp 7)**, pas la diffusivité : les
5 TC sont répartis EN LARGEUR au spot 3 (TC1..TC5 supposés à y = 0/10/20/30/40 mm, TC1/TC5
aux chants). Elle teste donc directement le profil en « M ».

**Vidéo : illisible.** Le MP4 est incomplet — l'atome `moov` (index, écrit à la clôture)
manque ; seules les frames brutes (`mdat`) sont présentes, non décodables. Enregistrement non
finalisé (caméra arrêtée avant clôture, ou export FLIR tronqué). À ré-exporter depuis la
source FLIR, ou fournir une vidéo de référence (même caméra/réglages) pour tenter une
reconstruction. La vidéo n'entre donc PAS dans ce résultat.

**Thermocouples — profil en largeur (pics, données nettoyées des glitches) :**

| TC | y (mm) | T_pic (°C) | ΔT (°C) | taux (°C/s) | fiable |
|---|---|---|---|---|---|
| TC1 | 0 (chant) | 76 | 52 | — | **non** (retombe à l'ambiant, mauvais contact) |
| TC2 | 10 | 139 | 116 | 9,2 | oui |
| TC3 | 20 (**centre**) | **101** | **78** | **4,2** | oui |
| TC4 | 30 | 147 | 124 | 10,1 | ~ (bruité, glitche à 1969 °C) |
| TC5 | 40 (chant) | 170 | 146 | 13,8 | oui |

**Ce que ça établit (qualitatif, robuste) :**
1. **Le centre de la largeur (TC3, y=20) est un CREUX** : minimum local, plus froid que ses
   deux voisins (TC2=139, TC4=147 vs TC3=101). → **le profil en « M » est RÉEL**, ce n'est pas
   un artefact numérique.
2. **Le centre chauffe le plus LENTEMENT** (4,2 °C/s vs 9-14 aux côtés ; pic à 54 s vs 34-42 s)
   → il est alimenté par conduction latérale, pas par la source directe (cohérent M-vallée).
3. **Les lobes de bord semblent MOINS extrêmes que la prédiction** : le modèle prédit un chant
   ~2× plus chaud que le point voisin (717 vs 382) ; ici TC5 (chant) n'est que ~1,2× TC4. →
   indice que **le modèle sur-prédit les lobes de bord** (M trop contrasté), cohérent avec le
   point mesuré au centre de l'essai de chauffe (395 mesuré vs 292 prédit).

**Réserves (empêchent une falsification QUANTITATIVE propre) :**
- **Géométrie non standard** : céramique d'espacement ET pression retirées → gap bobine-laminé
  ≈ 0 → source EM plus forte et de forme différente du modèle calibré. Les valeurs absolues ne
  sont PAS comparables à la cible 717/382/292.
- **TC1 défaillant** (un des deux chants) → symétrie non vérifiable.
- **Profil asymétrique** (monte vers y=40) → spot probablement non centré en largeur, ou
  décalage bobine.
- Interface vs surface des TC non précisé (supposé interface).

### Confirmation à 250 A (2e essai) — le résultat est REPRODUIT

Même montage, 250 A. Profil ΔT au pic (200 A → 250 A) :

| y (mm) | 0 (chant)* | 10 | 20 (**centre**) | 30 | 40 (chant) |
|---|---|---|---|---|---|
| 200 A | 52 | 116 | **78** | 124 | 146 |
| 250 A | 49 | 139 | **96** | 146 | 178 |

*TC1 (y=0) défaillant dans les DEUX essais.

**La forme est identique aux deux courants** (même creux au centre, même montée vers y=40,
juste mise à l'échelle) : le M-vallée n'est pas un aléa d'un essai. Contraste chant/centre
(TC5/TC3) = **1,88 (200 A) et 1,85 (250 A)** — remarquablement stable, et **en-dessous du 2,46
prédit**. Le taux au centre reste le plus lent (4,2 puis 5,1 °C/s vs 9-19 aux côtés).
Figure : `profil_largeur_200vs250.png`.

**Conclusion.** Évidence directe et **reproduite sur deux courants** que la **vallée centrale
du M est réelle** et que le modèle **sur-contraste** (lobes de bord / contraste ~1,85 mesuré
vs 2,46 prédit) — même sens que le point du chauffe (395 vs 292). Solide sur la FORME. Mais
l'AMPLITUDE absolue reste non falsifiable ici (géométrie non standard : céramique + pression
retirées → gap ≈ 0 ; TC1 mort ; profil asymétrique). **Reprise propre à faire** : géométrie
standard (avec céramique), 5 TC valides à l'interface, montage symétrique. Cf. fiche exp 7 de
`mesures_a_realiser.md`.

**Figures** : `tc_courbes_brutes.png` (200 A), `profil_largeur_mesure.png` (profil 200 A),
`profil_largeur_200vs250.png` (comparaison 200/250 A).
