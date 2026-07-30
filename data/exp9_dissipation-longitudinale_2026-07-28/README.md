# Exp 9 — Dissipation longitudinale de la chaleur (cartographie T(x))

**Objectif** : mesurer la décroissance / dynamique de la température **le long de la longueur**
(axe x) pour tester l'étalement longitudinal du modèle (résidu n°1 : étalement trop lent) et
valider `k_plan`. Protocole : `docs/protocole_exp_dissipation_longitudinale.md`.

## Géométrie (commune)

- **5 thermocouples alignés selon la longueur**, espacés de **30 mm** :
  **TC1 = x=0, TC2 = x=30, TC3 = x=60, TC4 = x=90, TC5 = x=120 mm**.
- Twill suscepteur en surface, céramique en place, TC à l'interface (comme exp 7).
- Phase 1 = ligne au **bord (y=0)** ; phase 2 (à venir) = ligne au **centre (y=20)**.

## Fichiers

### `200A/200A_y0_semistatique.txt` — 200 A, y=0, **soudage semi-statique** (4 dwells)
Reproduit le **procédé semi-statique établi** : la bobine s'arrête successivement le long du
joint (4 dwells), le point chaud avance le long de la longueur. Acquisition 1 Hz, ~373 s
(chauffes + refroidissements). À 200 A la montée dure ~15-20 s → 1 Hz suffit. Pic ≤ ~230 °C
(pas de fusion, échantillon réutilisable).

**Empreinte par dwell** (ΔT au-dessus de la ligne de base juste avant, par position) :

| dwell | ~instant | x=0 | x=30 | x=60 | x=90 | x=120 | spot ~ |
|---|---|---|---|---|---|---|---|
| 1 | 22 s | 169 | **209** | 11 | 1 | 5 | x≈15 mm |
| 2 | 141 s | 4 | **141** | 116 | 9 | 16 | x≈45 mm |
| 3 | 236 s | 0 | 2 | **127** | 99 | 13 | x≈75 mm |
| 4 | 333 s | 0 | 0 | 2 | **117** | 110 | x≈105 mm |

→ **Empreinte longitudinale étroite** : chaque dwell chauffe fortement les 2 TC qui l'encadrent
(±15 mm) et ~rien au-delà (±45 mm ≈ 0-16 °C). Spots ~x=15/45/75/105 (pas de 30 mm). Figure :
`200A/analyse_200A_y0.png`.

**Confrontation au modèle multi-spots** (4 spots x=15/45/75/105, aux instants mesurés, 200 A, sans
consigne). Footprint normalisé par dwell (l'absolu n'est pas confronté : énergie/durée de dwell
inconnue) :

| dwell | modèle (x=0/30/60/90/120) | mesuré |
|---|---|---|
| 1 | 1 / 0,87 / 0,02 / 0 / 0 | 0,81 / **1** / 0,05 / 0 / 0,02 |
| 2 | 0 / 0,89 / **1** / 0,03 / 0 | 0,03 / **1** / 0,82 / 0,06 / 0,11 |
| 3 | 0 / 0 / 0,86 / **1** / 0,05 | 0 / 0,02 / **1** / 0,78 / 0,10 |
| 4 | 0 / 0 / 0 / 0,5 / **1** | 0 / 0 / 0,02 / **1** / 0,94 |

→ **Le procédé est reproduit** : à chaque dwell le modèle chauffe la **bonne paire de TC adjacents**
(le spot avance bien de 30 mm) avec une **décroissance longitudinale raide** (négligeable au-delà de
la paire), comme mesuré. La **balance intra-paire** (lequel des 2 TC est le plus chaud) n'est pas
reproduite fidèlement — attendu : les deux sont à ~15 mm du spot, la balance est sensible à la
position exacte (inconnue à ±15 mm), à l'asymétrie de montage et à l'accumulation ; ce n'est pas un
défaut du modèle. Figure : `200A/analyse_200A_y0_semistatique_vs_modele.png`.

### `200A/200A_y0_monospot.txt` — 200 A, y=0, **spot unique** (MFC centré sur TC3, x=60) ✔
Source unique fixe à x=60 → décroissance longitudinale pure, stations symétriques. Pic TC3
235,9 °C (≤ 270, réutilisable), 1 Hz, ~250 s (avec refroidissement).

**Profil longitudinal au pic** (ΔT au-dessus de l'ambiant) :

| x (mm) | 0 | 30 | **60 (spot)** | 90 | 120 |
|---|---|---|---|---|---|
| ΔT (°C) | 3,6 | 19,2 | **235,9** | 32,8 | 7,1 |
| /centre | 0,02 | 0,08 | 1,00 | 0,14 | 0,03 |

→ **Décroissance longitudinale très raide** : < 15 % à ±30 mm, < 3 % à ±60 mm — la chaleur ne
s'étale quasiment pas en longueur pendant le dwell. **Asymétrie** : côté +x (TC4=32,8) ~1,7×
côté −x (TC2=19,2) → spot probablement décalé vers +x (~x=70-75) ou concentrateur asymétrique.
Figure : `200A/analyse_200A_y0_monospot.png`. C'est le cas propre pour confronter la forme de la
source en longueur au modèle (spot unique).

**Confrontation au modèle 2D** (spot unique x=60, 200 A, θ\* de référence) — profil normalisé au
spot (l'absolu n'est pas confronté : chauffe arrêtée tôt à 236 °C vs pic modèle ~448 °C) :

| x (mm) | 0 | 30 | 60 | 90 | 120 |
|---|---|---|---|---|---|
| Modèle /centre | 0,013 | 0,094 | 1,00 | 0,094 | 0,027 |
| Mesuré /centre | 0,015 | 0,081 | 1,00 | 0,139 | 0,03 |

→ **Le modèle reproduit la décroissance longitudinale** (raide : ~9 % à ±30 mm, ~3 % à ±60 mm).
L'écart à x=90 (mesuré 0,139 vs modèle 0,094) = l'**asymétrie du montage** (+x plus chaud), que le
modèle symétrique ne peut pas rendre — artefact expérimental, pas du modèle. **Conclusion : la
forme de la source en longueur (au bord, y=0, dominé par la source) est validée.** Le vrai test du
résidu d'étalement est la **phase 2 (y=20, centre, dominé par la conduction)**, à venir. Figure :
`200A/analyse_200A_y0_monospot_vs_modele.png`.

### `175A/` , `226A/` , `250A/` — monospot à d'autres courants (spot fixe x=60, y=0) ✔
Mêmes conditions que le monospot 200 A, à 175, 226 et 250 A (175 A a aussi un semi-statique).
Chaque essai est **coupé au même pic** (~270 °C au spot TC3, échantillon réutilisable), donc
l'absolu ne trace pas la loi en I² (bridé par l'arrêt manuel) — l'intérêt est la **forme
longitudinale**.

**Pics absolus atteints (°C) et profil normalisé au spot** :

| I (A) | ambiant | TC1 (x=0) | TC2 (x=30) | **TC3 (x=60)** | TC4 (x=90) | TC5 (x=120) | normalisé (÷ TC3) |
|---|---|---|---|---|---|---|---|
| 175 | 26,4 | 31,4 | 46,8 | **274,5** | 62,4 | 33,7 | 0,02 / 0,08 / 1,00 / 0,14 / 0,03 |
| 200 | 30,7 | 33,4 | 49,1 | **265,4** | 64,7 | 39,5 | 0,01 / 0,08 / 1,00 / 0,14 / 0,04 |
| 226 | 21,0 | 26,8 | 42,4 | **272,1** | 55,7 | 29,4 | 0,02 / 0,08 / 1,00 / 0,14 / 0,03 |
| 250 | 28,6 | 31,4 | 47,2 | **268,3** | 59,2 | 39,7 | 0,01 / 0,08 / 1,00 / 0,13 / 0,05 |

→ **Forme de la source en longueur invariante avec le courant** : les 4 profils normalisés se
superposent (décroissance raide, asymétrie +x systématique = artefact de montage). Figure de
présentation 2 panneaux : `docs/figures_elsevier/fig_dissipation_monospot.png`.

### (à venir) phase 2 — ligne au **centre (y=20)** : conduction quasi pure (source ≈ 0), probe direct de `k_plan`.

## Exploitation prévue

Confronter au modèle 2D (spots multiples pour le semi-statique ; spot unique pour le mono-spot) :
le jumeau reproduit-il l'empreinte longitudinale et sa dynamique ? L'écart pointera `k_plan`
(phase centre) ou la forme de la source en longueur (phase bord).
