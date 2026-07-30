# Résultats **modèle numérique** (jumeau)

Cette partie regroupe tout ce qui vient du **jumeau** : θ\* de référence, sorties de simulation,
journaux de validation/calibration, figures et rapports. Le code est dans `src/jumeau/` et
`scripts/` ; la config dans `config/`.

## θ\* de référence (canonique, dans `config/materiaux.yaml`)
Modèle **2D**, consolidation 2026-07-30 :

| Paramètre | Valeur | Note |
|---|---|---|
| `facteur_couplage` | **6,0123** | argument runtime (par modèle×essai) |
| `h_haut` | **30,087** W/m²·K | config |
| `h_bas_2d` | **37,424** W/m²·K | config |
| `h_bord_x0` | **250** W/m²·K | effectif (chants libres), `=0` réfuté |
| twill | **0,20 mm** | mesuré |

Rejouer une validation : `python scripts/valider.py --modele 2D --facteur 6.0123 --decalage-x 0 --essais <nom>`.

## Où sont les résultats

| Type | Emplacement | Contenu |
|---|---|---|
| **Sorties de simulation** | `resultats/` (gitignoré, régénérable) | courbes/cartes de validation + `*_series_sim.csv` par essai. |
| **Journaux** | `journaux/resultats_*.log` | validation, calibration (`_calibration_exp7_200A_*`, `_phase3_*`), diagnostics, convergence/MMS. Cf. §6 du journal pour référence vs archive. |
| **Figures** | `../figures_elsevier/`, `../figures_presentation/` | figures modèle+mesures (PNG 600 dpi), générées par `scripts/gen_figures_elsevier.py`, `gen_schemas_montage.py`, `gen_prediction_courant.py`, `gen_animation_chauffe.py`. |

## Documents modèle
- [`rapport_directrice_jumeau.md`](rapport_directrice_jumeau.md) — rapport complet pour la direction.
- [`rapport_slides_jumeau.md`](rapport_slides_jumeau.md) — trame de présentation.
- [`figures_catalogue.md`](figures_catalogue.md) — catalogue des figures.
- Spec de consolidation : `../superpowers/specs/2026-07-29-consolidation-jumeau-design.md`.

## État & résidu ouvert
Profil M et dissipation en longueur reproduits. Résidu structurel : au **centre** le modèle
sur-chauffe le spot (+30 °C) et sous-étale (`k_plan` trop faible, ~6 referme les extrémités mais
pas le pic). **Prochaine étape** : calibration jointe multi-familles (bord + centre). Prédictions
à courants non mesurés : `../figures_elsevier/fig_prediction_chauffe_courant.png`.

> Côté **labo** (mesures, données brutes) : voir [`../labo/README.md`](../labo/README.md).
