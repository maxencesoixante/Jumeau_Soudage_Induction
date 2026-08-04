# Provenance — `eppy` vendoré (copie tierce)

Ce dossier contient une **copie partielle** du solveur électromagnétique `eppy`,
vendorée pour rendre la vérification croisée du solveur EM du jumeau rejouable
hors-ligne et sans intervention manuelle (cf.
[`docs/modele/verification_croisee_eppy.md`](../../docs/modele/verification_croisee_eppy.md)
et [`scripts/verif_eppy_reaction.py`](../../scripts/verif_eppy_reaction.py)).

## Source

- **Upstream** : <https://github.com/wjbg/eppy>
- **Auteur** : W.J.B. Grouve (University of Twente) — auteur de Grouve 2020 ; solveur
  validé contre Nagel 2019 (fig. 6).
- **Commit épinglé** : `62f0030111153a13a49e34e64f1783dbc3bf485e`
  (« Fixed a few small errors & updated examples. »)
- **Licence** : MIT — © 2021 Wouter Grouve (voir [`LICENSE.md`](LICENSE.md), conservée à
  l'identique).

## Fichiers vendorés (uniquement ceux utilisés par la vérif)

- `eppy.py` — assemblage plaque mince (`system_matrix`, `biot_savart_matrix`,
  `contour_matrices`, `derivative_matrices`, `rhs`, `mask_bc`, `biot_savart`).
- `coil_geom.py` — géométrie d'inducteur (`hairpin`, `coil_segments`).
- `LICENSE.md` — texte MIT upstream.

Non vendorés (inutiles à la vérif) : `examples/`, `validation/`, `img/`,
`requirements.txt` (épinglé numpy 1.x, obsolète), configs d'éditeur.

## Seule modification vs upstream : compatibilité NumPy ≥ 2.0

eppy est écrit pour NumPy 1.x. Les alias de type supprimés dans NumPy 2.0 ont été
remplacés, à l'identique de l'upstream par ailleurs :

```
np.float_    → np.float64
np.complex_  → np.complex128
'cfloat'     → 'complex128'   (chaîne de dtype dans eppy.system_matrix)
```

Aucune autre différence : le comportement numérique est celui du commit `62f0030`.
Pour régénérer ce vendor depuis zéro :

```bash
git clone https://github.com/wjbg/eppy && cd eppy && git checkout 62f0030
sed -i '' 's/np\.float_/np.float64/g; s/np\.complex_/np.complex128/g' *.py
sed -i '' "s/'cfloat'/'complex128'/g" eppy.py
# puis copier eppy.py, coil_geom.py, LICENSE.md dans third_party/eppy/
```

## Dépendances

Aucune nouvelle dépendance pour le jumeau : `numpy`, `scipy`, `matplotlib` (importés par
`eppy.py`) sont déjà des dépendances cœur du projet (`pyproject.toml`). `coil_geom.py` ne
dépend que de numpy.
