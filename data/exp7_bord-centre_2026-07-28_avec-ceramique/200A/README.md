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

## v5 (chauffe plus longue, jusqu'à chant ~264 °C) — NOUVEAU RÉSIDU : le centre du modèle
se remplit trop lentement

v5 (TC1 fonctionnel) confirme la forme (chants symétriques 239/229, contraste au pic ~2,1) ET
permet la **dynamique**. En comparant *le centre en fonction du chant* pendant la CHAUFFE
(mesuré vs modèle) — reproductible sur v4 et v5 :

| chant ΔT (°C) | centre v4 | centre v5 | **centre MODÈLE** |
|---|---|---|---|
| 100 | 31 | 34 | **3** |
| 150 | 50 | 48 | **10** |
| 200 | 77 | 76 | **18** |

**Le centre RÉEL se remplit ~4× plus vite (relativement aux chants) que dans le modèle**
(chant=200 : centre 76 mesuré vs 18 modèle ; cf. `dynamique_centre_vs_chant.png`). Au **pic** le
contraste se recale (~2,1 vs 2,4) → **c'est un défaut du TRANSITOIRE**, pas de la forme
d'équilibre : le couplage centre↔chants est trop lent dans le modèle. **Candidats** :
conduction latérale `k_plan` trop faible, ou taux de chauffe des chants trop rapide (source de
bord trop forte / cp trop bas). → thread diagnostic distinct.

## Fichiers

- `200A_v2.txt`, `200A_v3.txt`, `200A_v4_TC1ok.txt`, `200A_v5.txt` — essais (5 TC en largeur ;
  v4/v5 = TC1 fonctionnel).
- `analyse_v2*.png`, `dynamique_centre_vs_chant.png` — figures.
