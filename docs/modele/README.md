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
| **Figures** | `../figures/` | dossier UNIQUE (jeu de référence + variantes `presentation_*`), PNG 600 dpi, générées par `scripts/gen_figures_elsevier.py`, `gen_schemas_montage.py`, `gen_prediction_courant.py`, `gen_animation_chauffe.py`. |

## Documents modèle
- [`rapport_directrice_jumeau.md`](rapport_directrice_jumeau.md) — rapport complet pour la direction.
- [`rapport_slides_jumeau.md`](rapport_slides_jumeau.md) — trame de présentation.
- [`figures_catalogue.md`](figures_catalogue.md) — catalogue des figures.
- [`verification_croisee_eppy.md`](verification_croisee_eppy.md) — vérification code-à-code du solveur EM contre `eppy` (Grouve, Nagel 2019) : contraste M ~3 reproduit par un code indépendant ; champ de réaction négligeable au régime du jumeau.
- [`leviers_refutes.md`](leviers_refutes.md) — registre des leviers réfutés conservés derrière flags (thermostat_capteurs, k(T), k_plan anisotrope, lambda_bord) : verdict, réf, comment les rejouer (issue #9).
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

**Investigation taux de chauffe (2026-07-31) — RÉSULTAT UNIFIANT.** Le déficit de dT/dt n'est ni
sous le spot (source OK, +14 %), ni un effet de masse thermique/cp (écartés), ni du lumping
d'épaisseur : **test décisif 2D vs 3D → le 3D ne ferme PAS le déficit** (TC3 centre-œil −40 % en
2D comme en 3D). Le déficit croît avec la distance au spot (centre-œil −22 %, hors-spot longitudinal
**−67 %**) = un déficit de **conduction dans le plan (in-plane)**. `k_plan` est le levier dominant
mais **aucune valeur scalaire** ne ferme les 3 régimes (k≈6 ferme le hors-spot mais sur-corrige le
sous-spot). → **Taux, pic et contraste du M sont TROIS symptômes du MÊME défaut** : l'étalement
in-plane est piloté par un `k_plan` scalaire qui ne peut être à la fois bas (sous-spot) et haut
(hors-spot/centre). Logs : `../../journaux/resultats_diag_{taux_dTdt_sous_hors_spot,sensibilite_taux_leviers,2d_vs_3d_taux_exp7_200A}.log`.

**`k_plan` anisotrope (kx≠ky) — prototype 2026-07-31, flag OFF, NON adopté.** Dernière piste
testée (`solveur2d.py`/`materiaux.py` `k_plan_x`/`k_plan_y`, défaut isotrope, 45 tests verts ;
`calibrer_joint.py --anisotrope`). Le fit trouve `kx≈7,4` (= le `k_plan≈7,3` déjà connu, ferme le
longitudinal) mais l'objectif est **multimodal en `ky`** avec deux optima physiquement OPPOSÉS (l'un
bat le RMSE en **aggravant** le contraste M à 3,63, l'autre rapproche le contraste 2,50 mais **rate**
le RMSE) → l'anisotropie **relocalise le conflit** au lieu de le résoudre. Verdict : **NON**. Logs :
`../../journaux/resultats_calibration_joint_anisotrope*.log`.

**`k_plan(T)` décroissant — piste 2026-08-03, améliore les DEUX symptômes (candidat sérieux).**
Après implémentation de la capacité **k(T)** (conduction flux-conservative à k dépendant de T,
flag `k_plan_T`/`k_z_T`, cf. `audit_lionetto_2017.md` §3.1), un `k_plan(T)` **décroissant**
(testé 7,3→3,0 W/m·K, borné par le k≈7,3 identifié en calibration jointe côté froid, le k=3
config côté chaud) fournit le **modèle d'étalement in-plane non scalaire** que le résidu réclamait.
À θ\* de référence **figé** (`scripts/diag_kT_residu.py`) il améliore **SIMULTANÉMENT** :
- le **contraste du M** (exp7 200 A) : réf 3,13 → **2,46** (mesuré 2,08) ;
- le **déficit hors-spot** (exp9 centre y=20) : extrémités TC1 norm 0,03 → **0,09** (= mesuré),
  RMSE moyen 16,9 → **11,0**.

Mécanisme : k **bas là où c'est chaud** (lobes/sous-spot), **haut là où c'est froid** (creux
central, extrémités) — un seul champ réconcilie les deux régimes que le scalaire ne pouvait pas,
et que l'anisotropie relocalisait sans résoudre. **Correction de FORME, pas d'échelle** : le
contraste est ~invariant au `facteur_couplage` (il s'annule dans le ratio) et robuste à la pente ;
l'amplitude se restaure séparément par `facteur_couplage`.

**Limites (non adopté à ce stade) :** (1) ne ferme pas TOUT — contraste résiduel ~2,4 vs 2,08, le
reste = vraisemblablement la raideur de source au chant (ingrédient `lambda_bord`). (2) La courbe
k(T) est une **HYPOTHÈSE de forme** ; la mesure indépendante (Mesure 9, k_plan(T)) **ne sera pas
réalisée** → sa seule validation possible est une **calibration jointe avec k(T) actif évaluée en
HELD-OUT** (garde-fou anti-overfitting — la barre que l'anisotropie a ratée).

**Calibration jointe avec k(T) faite (2026-08-03, `calibrer_joint.py --kT`, held-out exp7_250A +
exp9 bord) — direction confirmée, held-out PAS franchi.** Le fit (pente LIBRE, non contrainte)
choisit une courbe **décroissante** k_cold(20°C)=8,52 → k_hot(340°C)=2,00 (k_hot raile la borne)
— `k_cold≈8,5` recoupe le `k≈7,3` scalaire → **`k_plan` réel ≈3× le config et décroissant : acquis
physique**. Mais RMSE **JOINT 19,8→15,7 (mieux)** vs **HELD-OUT 16,5→17,2 (régresse)** : k(T)
sur-étale le pic source-dominé du bord (exp9 bord TC3 11,4→25,3) et le fit gonfle `h_bas_2d` (37→83).
Même schéma que tous les leviers → **NON adopté**. Le résidu a deux ingrédients (conduction in-plane
= k(T) ; raideur de source au chant = `lambda_bord`) que k(T) seul ne peut porter.

**Test de contrôle `--figer h_bas_2d=37.424` (2026-08-03) — CLÔTURE de la piste.** Figer `h_bas_2d`
à la référence NE sauve PAS k(T) : tout empire (JOINT 19,8→22,0, HELD-OUT 16,5→**22,8**), les pics
source-dominés s'effondrent → l'échec held-out est **intrinsèque à k(T)**, pas un artefact de
`h_bas_2d`. La pente décroissante est robuste (k_cold=7,71 vs 8,52 libre vs 7,3 scalaire).
**Verdict final : le résidu est irréductible par TOUT modèle de `k_plan`** (scalaire, anisotrope,
T-dépendant — les 3 réfutés) : monter la conduction in-plane sur-étale toujours les pics. **Acquis
positif** : `k_plan` réel ≈ 7,5–8,5 W/m·K (≈2,5–3× le config 3,0) et décroissant, corroboré 3× —
correction de *propriété* défendable, pas un correctif de résidu adoptable. `k_plan=3,0` reste la
référence. Logs : `../../journaux/resultats_calibration_joint_kT{,_hbasfige}.log` ; mémoire :
`kt-residu-structurel-piste`.

---

## Domaine de validité du jumeau (bilan, 2026-07-31)

Tous les leviers du modèle actuel ont été testés et **documentés** (calibration scalaire jointe,
adoucissement de source `lambda_bord`, 3D complet, `k_plan` anisotrope) : aucun ne réduit le résidu
sans en casser un autre. Le résidu est **compris, quantifié et irréductible** par ces leviers.

**✅ Valide** (le 2D lumpé + θ\* de référence reproduit bien) :
- le régime **pic / plateau** (température d'équilibre — ce qui compte pour la soudure) ;
- la **forme spatiale** de la source, en longueur (dissipation exp9) et en largeur (M, forme) ;
- l'**ordre spatio-temporel** et la **loi en I²** (transfert entre courants, interpolation fiable).

**⚠️ Limite caractérisée** (hors domaine de validité) — un seul défaut, deux symptômes :
- l'**amplitude du contraste du M** est sur-estimée (~3,15 vs ~2,09 mesuré) ;
- le **transitoire hors-spot rapide** (dT/dt loin du spot) est sous-estimé (jusqu'à −67 %).
- Cause unique : **étalement in-plane trop lent, piloté par un `k_plan` scalaire** (ne peut être bas
  sous-spot ET haut hors-spot). **MAJ 2026-08-03** : le modèle d'étalement non scalaire requis
  existe désormais — un **`k_plan(T)` décroissant** (cf. §résidu ci-dessus) améliore les deux
  symptômes à la fois. **Candidat** en cours de validation par calibration jointe held-out (Mesure 9
  non réalisée) ; tant qu'il n'a pas battu la référence hors échantillon, `k_plan=3,0` reste la référence.

## Exploitation (domaine validé)
- **Prédictions T(t) à courants non mesurés** : `../figures/fig_prediction_chauffe_courant.png`
  (`scripts/gen_prediction_courant.py`).
- **Fenêtre de soudage — abaque opératoire** (courant × durée) : `../figures/fig_fenetre_soudage.png`
  (`scripts/gen_fenetre_soudage.py`). Point chaud (lobe M) : zones sous-chauffe / soudage
  (337-450 °C) / dégradation. Enseignements : **soudage impossible sous ~180 A** avec un spot fixe ;
  la **fenêtre se resserre quand le courant monte** (200 A : ~21-39 s ; 300 A : ~7-11 s).
- **Empreinte de soudure** (carte T(x,y) interface) : `../figures/fig_empreinte_soudure.png`
  (`scripts/gen_empreinte_soudure.py`). À spot fixe, **seuls les 2 lobes du M (bords) fondent**
  (~1-2 % de l'interface), le centre reste froid.
- **Procédé semi-statique** (4 dwells, pas 30 mm) : `../figures/fig_procede_semistatique.png`
  (`scripts/gen_procede_semistatique.py`). La soudure se forme en **deux rails le long des chants**
  sur toute la longueur ; **le centre ne soude jamais** (spot fixe en largeur) — enseignement procédé
  (il faudrait élargir/adoucir le M pour souder pleine largeur).
- **Loi de réglage atelier** (durée vs courant) : `../figures/fig_loi_reglage.png`
  (`scripts/gen_loi_reglage.py`). Durée recommandée (cible 390 °C) + fenêtre + ajustement
  `t ≈ 9,6·10⁵/I²` (taux ∝ I²) + table (200 A→30 s, 250 A→15 s, 300 A→9 s).
- Frontière dégradation conservatrice partout (modèle sur-estime le bord ~50 °C).
- **MFC réduit (31,75 mm) — prédiction exploratoire** : `../figures/fig_mfc_reduit.png`
  (`scripts/gen_mfc_reduit.py`). Le modèle standard **ne voit pas** l'effet d'un MFC plus petit (le
  MFC n'entre que via le plan image + `mu_r` + un masque de PERTES, pas la source). Flag
  **`Essai(masque_source_mfc=True)`** (défaut OFF, no-op sur le MFC labo validé) qui confine la
  source à l'empreinte MFC. Résultat MFC réduit : le contraste s'adoucit (**4,10 → 1,69**), les
  points chauds se déplacent des chants vers l'intérieur (y=0 → y~7 mm) — **mais** le masque dur
  **tronque** la puissance (pas de redistribution) → pics effondrés (0 % soudé au réglage testé) et
  le **centre reste le point froid**. **Signal fiable = qualitatif** (M adouci) ; l'absolu est
  biaisé bas. → à **mesurer au banc** dès réception du MFC réduit (le modèle EM image-current ne
  fait pas dépendre le champ des dimensions du MFC — extrapolation non validée).

> Côté **labo** (mesures, données brutes) : voir [`../labo/README.md`](../labo/README.md).
