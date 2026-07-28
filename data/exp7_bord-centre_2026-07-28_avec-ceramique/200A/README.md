# 200 A avec céramique — résultat (analyse Claude, 2026-07-28)

**Le profil en « M » est VALIDÉ, symétrique.** Trois essais (v2, v3, v4) ; TC1 (chant y=0) était
cassé en v2/v3, **réparé en v4** → tous les points fiables.

Profil ΔT au pic (°C au-dessus de l'ambiant) :

| y (mm) | 0 | 10 | 20 (centre) | 30 | 40 | contraste chant/centre |
|---|---|---|---|---|---|---|
| v2 | (TC1 mort) | 141 | **89** | 119 | 192 | 2,17 |
| v3 | (93, TC1 douteux) | 172 | **104** | 141 | 226 | 2,16 |
| **v4 (TC1 réparé)** | **215** | 157 | **93** | 124 | **201** | 2,31 |
| **modèle 200 A** | 468 | 276 | **207** | 276 | 468 | 2,43 |

## Conclusions

1. **M SYMÉTRIQUE** (v4) : chant y=0 (215) ≈ chant y=40 (201), ratio **1,07** — les deux chants
   sont des lobes chauds, comme le prédit le modèle. L'asymétrie de v2/v3 venait **entièrement
   du TC1 cassé**, pas du montage.
2. **Contraste reproduit et proche du modèle** : 2,16 / 2,17 / 2,31 mesurés vs 2,43 modèle. La
   forme normalisée se superpose au modèle sur toute la largeur (cf. `analyse_v2_v3_v4.png`).
3. **Taux de chauffe** (v4) : chants ~16-18 °C/s, centre ~6,5 °C/s — le centre monte lentement
   (alimenté par conduction), les chants vite (source directe) : cohérent M-vallée.

## Réserve

**Valeurs absolues non confrontées** : chauffe manuelle courte (pic à ~15-22 s, ΔT 90-215 °C)
alors que le modèle vise ~46 s / plus chaud. Seule la FORME (contraste, symétrie) est comparée.
→ pour confronter les absolus et la loi en I², refaire avec une **chauffe standardisée** (durée
fixe / plateau), cf. protocole du dossier parent.

## Fichiers

- `200A_v2.txt`, `200A_v3.txt`, `200A_v4_TC1ok.txt` — essais (5 TC en largeur).
- `analyse_v2.png`, `analyse_v2_v3.png`, `analyse_v2_v3_v4.png` — figures.
