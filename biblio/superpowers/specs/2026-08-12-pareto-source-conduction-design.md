# Spec — Carte de faisabilité source × conduction (réouverture du résidu in-plane)

**Date :** 2026-08-12
**Statut :** design validé, prêt pour plan d'implémentation
**Portée :** étape **C** d'une séquence **C → A**. Cette spec ne couvre QUE l'étape C
(carte de faisabilité, diagnostic). L'étape A (fit joint 6 paramètres) fera l'objet
d'une spec séparée, et n'est lancée QUE si C ouvre la porte.

---

## Contexte — pourquoi on rouvre

Le résidu structurel du jumeau (sur-contraste du profil « M » en largeur + déficit
transitoire hors-spot) a été déclaré **irréductible** et l'arc modèle **clos** le
2026-07-31 (`b84b462`), après avoir testé, **un levier à la fois**, la calibration
jointe scalaire, `lambda_bord`, la 3D, l'anisotropie `kx≠ky`, puis `k(T)` (`b3ba298`).

Or `biblio/modele/README.md` (l.157-158) diagnostique explicitement le résidu comme
ayant **deux ingrédients** :
1. **conduction in-plane** (`k(T)` décroissant) — possède le déficit d'étalement hors-spot ;
2. **raideur de source au chant** (`lambda_bord_mm`) — possède le sur-contraste du M.

et conclut que « `k(T)` **seul** ne peut porter » les deux. Faits vérifiés le 2026-08-12 :
- `k(T)` **seul** (`calibrer_joint.py --kT`) : améliore le contraste (3,13→2,46) mais
  **sur-étale les pics source-dominés** → **held-out régresse** (16,5→17,2). NON adopté.
- `lambda_bord` **seul** : ramène le contraste 3,15→~2,1 (= mesuré) mais « ne ferme pas TOUT ».
- **Les deux n'ont JAMAIS été ajustés ensemble.** `lambda_bord_mm` n'est qu'un
  passthrough **figé** (`lambda_bord_mm_fige`, jamais un paramètre calibré) dans
  `calibrer_joint.py`. La combinaison est **génuinement non testée**.

**Hypothèse physique de réouverture :** `lambda_bord` adoucit la **source** au chant
(tue l'excès de contraste à son origine), ce qui **libère** la conduction pour ne faire
QUE l'étalement des zones froides hors-spot — donc sans avoir à sur-aplatir le pic chaud
qui cassait le held-out. Chaque ingrédient traite le symptôme qu'il possède
physiquement, au lieu de forcer un seul levier à faire les deux travaux (ce qui créait
la multimodalité et l'échec held-out).

**Résultat attendu :** un go/no-go rigoureux et bon marché. Soit la carte montre une
région faisable (→ on lance A), soit elle confirme la clôture avec une preuve
bidimensionnelle (au lieu d'une accumulation de réfutations monodimensionnelles).

---

## But de l'étape C

Répondre à **une** question, sans lancer d'optimiseur multi-paramètre :

> Existe-t-il un couple *(lambda_bord_mm, k_hot)* qui satisfait **simultanément**
> (a) contraste M ≈ 2,08 (mesuré, exp7_200A) **ET** (b) RMSE held-out ≤ référence (~16,5 °C) ?

- **Oui** (région faisable non vide) → la porte est ouverte, on passe à l'étape A.
- **Non** (aucun nœud faisable) → clôture confirmée, on s'arrête.

---

## Design

**Nouveau script** `code/scripts/diag/diag_pareto_source_conduction.py` — **diagnostic pur** :
ne modifie AUCUN flag, config, ni `θ*` de référence ; n'écrit que ses propres sorties
(CSV + PNG). Réutilise la machinerie existante :
- `code/scripts/calibrer_joint.py` : classes `EssaiCalibre` / `Calibrateur`, passthrough
  `lambda_bord_mm`, mode `k(T)` (`--kT` → `cfg.materiau.k_plan_T`), fit `facteur_couplage`.
- `code/scripts/diag/diag_anisotropie_kx_ky.py` : recette de **contraste M** (moyenne des pics
  normalisés chants y=0/40 mm sur le pic centre y=20 mm, exp7_200A ; = recette
  `gen_figures_elsevier.py::fig2`).

### Grille 2D (les deux ingrédients)
- **axe 1** — `lambda_bord_mm` ∈ {0, 1, 2, 3, 4, 6} (raideur de source → contraste) ;
- **axe 2** — `k_hot` ∈ {2, 3, 4, 5, 6}, avec **`k_cold` FIGÉ = 7,5 W/m·K** (valeur
  froide physique corroborée 3× : fit scalaire ≈7,3, k(T) libre 8,52, `k_cold` figé 7,71).
  `k(T) = [[20 °C, 7,5], [340 °C, k_hot]]` (décroissant pour k_hot < 7,5).
- **repère** : le nœud isotrope de référence (`k_plan=3,0`, `lambda_bord=0`, `k(T)` OFF)
  est évalué et tracé comme point de comparaison.

### Traitement de l'amplitude (nécessaire)
À **chaque nœud**, **restaurer `facteur_couplage` par un fit 1-D** (`scipy`, borné) sur le
**lot d'ajustement**, avant de mesurer les métriques. Justification : le RMSE dépend de
l'amplitude, alors que le contraste en est ~invariant (README l.141-143) ; sans
restauration d'amplitude la carte confondrait erreur de **forme** et erreur d'**échelle**.
Restent **figés au canonique** : `h_bas_2d` (37,424), `h_bord_x0` (250,0), `h_haut` (30,087).

### Lots d'essais
- **Ajustement** (pour le fit 1-D `facteur_couplage` + RMSE lot) : `exp7_150A`,
  `exp7_200A`, `exp9_200A_y20_monospot` (famille centre/conduction).
- **Held-out** (garde-fou, JAMAIS vu par le fit d'amplitude) : `exp7_250A`,
  `exp9_200A_monospot` (bord y=0) — **identique au held-out du run k(T)** pour comparabilité.
- **Contraste** : mesuré sur `exp7_200A` (recette fig2).

### Métriques par nœud
`lambda_bord_mm`, `k_hot`, `facteur_couplage*` (restauré), `contraste_M`,
`rmse_holdout`, `rmse_fit`.

### Critère de faisabilité (verdict go/no-go)
Un nœud est **faisable** si :
`|contraste_M − 2,08| ≤ 0,15`  **ET**  `rmse_holdout ≤ 16,5 °C`.
Le script imprime `GO` (≥ 1 nœud faisable, avec la liste des nœuds) ou `NO-GO` (aucun).

### Sorties
1. `donnees/journaux/resultats_pareto_source_conduction_2026-08-12.csv` — tous les nœuds.
2. `biblio/modele/figures/pareto_source_conduction.png` — nuage **contraste_M (x) vs
   rmse_holdout (y)**, un point par nœud (couleur = `lambda_bord`, forme/taille = `k_hot`),
   boîte de faisabilité et point de référence isotrope tracés. Style article (`_style`).
3. Verdict `GO`/`NO-GO` en fin de console + court résumé.

---

## Non-objectifs (YAGNI)
- **Pas** de fit multi-paramètre ici (c'est l'étape A, spec séparée).
- **Pas** de 3ᵉ axe `k_cold` (figé ; on l'ouvrira seulement si la carte 2D est ambiguë).
- **Pas** de modification de `θ*`, des flags, ni de la config. Diagnostic en lecture seule
  côté modèle.
- **Pas** d'anisotropie `kx≠ky` ici (réfutée ; l'ingrédient de forme retenu est `lambda_bord`).

---

## Réutilisation (ne pas réécrire)
- `EssaiCalibre.simuler/residus/rapport(..., lambda_bord_mm=...)` — `code/scripts/calibrer_joint.py`.
- Application `k(T)` : `cfg.materiau.k_plan_T = [[T_lo, k_cold], [T_hi, k_hot]]` (mode `--kT`).
- Fit 1-D `facteur_couplage` : même pondération bruit-capteur σ que `Calibrateur`.
- Recette contraste : `code/scripts/diag/diag_anisotropie_kx_ky.py` (`--contraste`).
- Style figure : `code/scripts/_style.py` (`apply_style`, `savefig`).
- Chargement/recalage mesures : `jumeau.validation.chargement`.

---

## Vérification (end-to-end)
1. `python code/scripts/diag/diag_pareto_source_conduction.py` s'exécute en quelques minutes,
   sans toucher code/config/flags (vérifier `git status` : seuls CSV + PNG + le script).
2. **Sanity** : le nœud isotrope de référence reproduit les nombres connus
   (contraste ≈ 3,13 ; `rmse_holdout` ≈ 16,5) — sinon le pipeline diverge d'un run
   antérieur et il faut le corriger avant d'interpréter.
3. **Sanity** : `lambda_bord=6, k_hot=7,5` (≈ isotrope haut) reproduit l'ordre de
   grandeur du contraste `lambda_bord` seul (~2,1) documenté au README.
4. Le PNG est relu à l'échelle cible (boucle `figure-review-loop`) : lisible, boîte de
   faisabilité et repère visibles, aucun chevauchement.
5. Le verdict `GO`/`NO-GO` est cohérent avec le nuage tracé.

## Limite connue de la carte (conservatrice) et clause de quasi-faisabilité
La carte **fige `h_bas_2d`** au canonique et ne restaure que `facteur_couplage` ; l'étape A,
elle, **libère `h_bas_2d`**. C'est un choix **conservateur voulu** : il empêche la carte de
déclarer « faisable » des nœuds qui ne marcheraient qu'en **gonflant `h_bas_2d`** (le mode de
sur-ajustement qui a fait échouer k(T), cf. contrôle `--figer h_bas_2d`). Contrepartie : un
nœud légitime pourrait tomber **juste hors** de la boîte parce que `h_bas_2d` est figé.
→ **Clause de quasi-faisabilité :** si aucun nœud n'est strictement faisable MAIS qu'au moins
un nœud est en **quasi-faisabilité** (`|contraste−2,08| ≤ 0,15` ET `rmse_holdout ≤ 17,2`, la
valeur held-out qu'a atteinte k(T) seul), ce n'est **pas** un NO-GO franc : on passe quand même
à l'étape A (où `h_bas_2d` libre peut fermer l'écart), en le signalant. NO-GO franc = aucun nœud
même quasi-faisable.

## Décision en aval
- **GO** (≥ 1 nœud faisable) **ou quasi-GO** (clause ci-dessus) → rédiger la spec de l'étape A
  (fit joint `θ = [facteur_couplage, h_bas_2d, k_cold, k_hot, h_bord_x0, lambda_bord_mm]`,
  held-out identique) et l'exécuter.
- **NO-GO franc** (aucun nœud même quasi-faisable) → consigner le résultat (README §résidu +
  `leviers_refutes.md` : « combinaison source+conduction testée en 2D, région faisable vide »),
  corriger la note mémoire `residu-unifie-etalement-in-plane` (la combinaison n'est plus « non
  testée »), fermeture confirmée à deux ingrédients.
