# Résultats **labo** (mesures expérimentales)

Cette partie regroupe tout ce qui vient des **essais physiques** : relevés thermocouples bruts,
protocoles et décisions de terrain. Les données brutes sont dans **[`../../data/`](../../data/)**
(non déplacées : référencées par les scripts et les essais formels `config/essais/`).

## Campagnes de mesures (`data/`)

| Campagne | Dossier | Contenu |
|---|---|---|
| **Série A** | `data/Serie A/` | Essais historiques 3–5 TC (A-1 calibration, A-3 aveugle). |
| **Série B** | `data/Serie B/` | Essai basse consigne B-2 (loi thermostat « capteurs »). |
| **exp7 — profil M (largeur)** | `data/exp7_bord-centre_2026-07-28_avec-ceramique/` | Cartographie bord→centre, 5 TC, 5 courants (150/176/200/225/250 A), **avec céramique** (géométrie de référence). Profil en M validé. |
| **exp9 — dissipation (bord y=0)** | `data/exp9_dissipation-longitudinale_2026-07-28/` | Décroissance longitudinale, spot fixe, monospot 175/200/226/250 A + semi-statique. Forme de source en longueur invariante en courant. |
| **exp9 — dissipation (centre y=20)** | `data/exp9_dissipation-longitudinale_2026-07-30/` | Ligne centrale (conduction dominante) → sonde `k_plan` / résidu d'étalement. |

Chaque campagne récente a son propre `README.md` détaillé dans son dossier `data/…`.

## Documents labo

- [`protocole_exp_dissipation_longitudinale.md`](protocole_exp_dissipation_longitudinale.md) — fiche protocole exp 9.
- [`mesures_a_realiser.md`](mesures_a_realiser.md) — mesures encore **à réaliser** (feuille de route terrain).
- [`releves_resolus.md`](releves_resolus.md) — relevés/questions de terrain déjà **tranchés** (archive).

## Sécurité échantillon (rappel)
Les bords (y=0 / y=40) montent ~2× plus que le centre (profil M). Pour ne pas souder/dégrader
les bords, plafonner le pic au **centre** à ~150 °C (fusion PEKK 337 °C au bord) ou ~125 °C pour
garder l'échantillon réutilisable. Un TC témoin au bord mesure le contraste réel.

> Côté **modèle** (simulations, validation, figures, θ\*) : voir [`../modele/README.md`](../modele/README.md).
