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
Profil M et dissipation en longueur reproduits. Résidu : au **centre** le modèle sur-chauffe le
spot et sous-étale ; au **bord** le profil M est trop contrasté (lobes intermédiaires
sous-estimés, chants sur-estimés).

**Calibration jointe multi-familles (2026-07-30, `scripts/calibrer_joint.py`) — faite, NON
adoptée.** Fit conjoint bord (exp7) + centre (exp9 y=20). Résultats :
- ✅ **`k_plan` devient identifiable ≈ 7,3 W/m·K** (vs 3,0 en config) grâce à la famille centre —
  la conductivité dans le plan est probablement ~2× plus élevée. Fort indice physique.
- ✅ Famille CENTRE nettement améliorée (RMSE 16,9 → 8,0 ; pic TC3 +40 → +14 °C).
- ❌ Famille BORD régresse (le `h_bas_2d` élevé sur-refroidit les transitoires du bord) → **RMSE
  global 18,5 → 19,2** (régression) → non adopté (θ\* de référence inchangé).
- **Conclusion** : le résidu du bord est **structurel** (contraste spatial du M), qu'aucun
  coefficient uniforme ne corrige. Logs : `../../journaux/resultats_calibration_joint_*.log`.

**Forme du M — prototype `lambda_bord_mm` (2026-07-31, flag OFF, non adopté).** Le sur-contraste
vient de la CL `ψ=0` au chant (`em/foucault.py`), trop raide pour un twill à maille finie.
`lambda_bord_mm` (longueur d'extrapolation de bord) ramène le contraste **3,15 → ~2,1** (= mesuré)
mais n'est **pas conservatif en puissance** → ne débloque pas un θ\* joint gagnant. Archivé/testé.

**⚠️ Contraste réel du M** : le modèle **sur-contraste de ~50 %** (chant/centre **~3,15** vs mesuré
**~2,09**, exp7 200 A). L'ancienne `fig2` affichait 2,43/2,18 (codé en dur, périmé) — corrigée.

**Prochaine investigation = déficit de taux de chauffe / transitoire.** Deux résidus structurels
distincts subsistent : (1) sur-contraste du M (compris, non conservatif) ; (2) un déficit de taux
de chauffe indépendant qui bloque le θ\* joint. La calibration scalaire et la forme de source sont
épuisées ; le prochain levier est la dynamique (dépôt de puissance instantané / masse thermique).

Prédictions courants non mesurés : `../figures_elsevier/fig_prediction_chauffe_courant.png`.

> Côté **labo** (mesures, données brutes) : voir [`../labo/README.md`](../labo/README.md).
