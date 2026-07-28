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

### (à venir) `200A/200A_y0_monospot.txt` — 200 A, y=0, **spot unique** (MFC centré sur TC3, x=60)
Source unique fixe à x=60 → décroissance longitudinale pure, stations symétriques (TC2/TC4 à
±30 mm, TC1/TC5 à ±60 mm). Complément propre à la mesure semi-statique.

### (à venir) phase 2 — ligne au **centre (y=20)** : conduction quasi pure (source ≈ 0), probe direct de `k_plan`.

## Exploitation prévue

Confronter au modèle 2D (spots multiples pour le semi-statique ; spot unique pour le mono-spot) :
le jumeau reproduit-il l'empreinte longitudinale et sa dynamique ? L'écart pointera `k_plan`
(phase centre) ou la forme de la source en longueur (phase bord).
