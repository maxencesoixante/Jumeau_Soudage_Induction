# Résultats **labo** (mesures expérimentales)

Cette partie regroupe tout ce qui vient des **essais physiques** : relevés thermocouples bruts,
protocoles et décisions de terrain. Les données brutes sont dans **[`../../data/`](../../data/)**
(non déplacées : référencées par les scripts et les essais formels `code/config/essais/`).

## Campagnes de mesures (`donnees/data/`)

| Campagne | Dossier | Contenu |
|---|---|---|
| **Série A** | `donnees/data/Serie A/` | Essais historiques 3–5 TC (A-1 calibration, A-3 aveugle). |
| **Série B** | `donnees/data/Serie B/` | Essai basse consigne B-2 (loi thermostat « capteurs »). |
| **exp7 — profil M (largeur)** | `donnees/data/exp7_bord-centre_2026-07-28_avec-ceramique/` | Cartographie bord→centre, 5 TC, 5 courants (150/176/200/225/250 A), **avec céramique** (géométrie de référence). Profil en M validé. |
| **exp9 — dissipation (bord y=0)** | `donnees/data/exp9_dissipation-longitudinale_2026-07-28/` | Décroissance longitudinale, spot fixe, monospot 175/200/226/250 A + semi-statique. Forme de source en longueur invariante en courant. |
| **exp9 — dissipation (centre y=20)** | `donnees/data/exp9_dissipation-longitudinale_2026-07-30/` | Ligne centrale (conduction dominante) → sonde `k_plan` / résidu d'étalement. |

Chaque campagne récente a son propre `README.md` détaillé dans son dossier `donnees/data/…`.

## Documents labo

- [`protocole_exp_dissipation_longitudinale.md`](protocole_exp_dissipation_longitudinale.md) — fiche protocole exp 9.
- [`mesures_a_realiser.md`](mesures_a_realiser.md) — mesures encore **à réaliser** (feuille de route terrain).
- [`releves_resolus.md`](releves_resolus.md) — relevés/questions de terrain déjà **tranchés** (archive).

## Figures (mesures) — `figures/`

Figures **utilisant les données expérimentales** (exp7/exp9, séries A/B). Le jeu complet
(dont les variantes `presentation_*` pour les slides, le poster et la figure de référence
`serieA_A-2_250A_2026-06-09.png`) est dans [`figures/`](figures/).

### exp7 — profil en « M » (largeur) et loi en courant

![Profil en M mesuré à 150/200/250 A](figures/fig1_profil_M.png)
*Profil de température en largeur au pic, mesuré à 3 courants — chants chauds (y=0/40 mm), creux au centre (y=20 mm).*

![Forme du M : mesuré vs modèle](figures/fig2_mesure_modele.png)
*Forme du M, mesuré vs modèle (200 A) — le modèle sur-contraste le rapport bord/centre.*

![Historiques bruts des 5 TC](figures/fig4_courbes_brutes.png)
*Les 5 historiques T(t) bruts d'un essai (200 A), groupés par symétrie de position.*

![Loi en courant](figures/fig5_loi_courant.png)
*Taux de chauffe au chant en fonction du courant (loi en I², R²=0,999).*

![Petits multiples : 5 TC par courant](figures/fig_essais_5TC_par_courant.png)
*Un panneau par courant, les 5 TC mesurés — profil M à chaque courant.*

### exp9 — dissipation longitudinale (bord y=0)

![Dissipation longitudinale — spot unique](figures/fig_dissipation_monospot.png)
*Décroissance de ΔT le long de la longueur, spot centré — la source en longueur est raide.*

![Dissipation semi-statique — 4 dwells](figures/fig_dissipation_semistatique.png)
*Procédé semi-statique : la tête s'indexe à 4 positions successives.*

### Fenêtre de soudage (abaque)

![Fenêtre de soudage](figures/fig_fenetre_soudage.png)
*Abaque opératoire courant × durée, ancré sur les durées mesurées exp7 (150/200/250 A).*

## Sécurité échantillon (rappel)
Les bords (y=0 / y=40) montent ~2× plus que le centre (profil M). Pour ne pas souder/dégrader
les bords, plafonner le pic au **centre** à ~150 °C (fusion PEKK 337 °C au bord) ou ~125 °C pour
garder l'échantillon réutilisable. Un TC témoin au bord mesure le contraste réel.

> Côté **modèle** (simulations, validation, figures, θ\*) : voir [`../modele/README.md`](../modele/README.md).
