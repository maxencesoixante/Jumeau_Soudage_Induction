# Vérification croisée du solveur EM — jumeau (Lin 1993) vs `eppy` (Nagel 2019)

**Date : 2026-08-04.** Script : [`code/scripts/verif_eppy_reaction.py`](../../scripts/verif_eppy_reaction.py) ·
Log : [`donnees/journaux/archive/resultats_verif_eppy_reaction.log`](../../journaux/archive/resultats_verif_eppy_reaction.log).

**Reproduction (hors-ligne, une commande) :** `eppy` est vendoré (copie MIT au commit
`62f0030`, patchée numpy ≥ 2) sous [`code/third_party/eppy/`](../../third_party/eppy/) — rien à
cloner. Provenance et régénération : [`code/third_party/eppy/NOTICE.md`](../../third_party/eppy/NOTICE.md).

```bash
.venv/bin/python code/scripts/verif_eppy_reaction.py
```

## Contexte

[`eppy`](https://github.com/wjbg/eppy) (W.J.B. Grouve — auteur de Grouve 2020 et des
Buser ; MIT ; commit épinglé `62f0030` ; **validé contre Nagel 2019 fig. 6**) résout les
courants de Foucault en plaque mince par le **potentiel vecteur électrique `T`**. C'est un
**second solveur indépendant** du régime que couvre notre `em/foucault.py` — l'occasion
d'une vérification code-à-code au-delà de nos formes closes (boucle circulaire).

## Trois constats de l'audit du code d'eppy

1. **`T` (Nagel) ≡ `ψ` (Lin).** Même physique plaque-mince. eppy est **isotrope**
   (`system_matrix(rho …)`, `rho` scalaire) ; notre solveur est **anisotrope** (ρxx≠ρyy
   par couche) — donc *plus général*. Formulation corroborée par une méthode publiée.
2. **Condition de bord identique.** eppy impose `T = 0` sur tout le chant
   (`mask_bc` → nœuds de bord exclus du solve) = **exactement notre `ψ = 0`**. Il n'existe
   **aucune CL de chant plus douce** à emprunter : le sur-contraste du M n'est pas un bug de
   CL, et l'adoucissement `lambda_bord` était bien un écart *ad hoc* à la physique correcte.
3. **eppy inclut le champ de réaction (self-inductance) que nous négligeons :**
   `K = M + Cx·N·Dy − Cy·N·Dx`, où `N` est le Biot-Savart du champ **induit par les
   courants de Foucault eux-mêmes**. Notre modèle le néglige (absorbé par `facteur_couplage`).
   eppy résout aussi `M` seul = **sans réaction = notre hypothèse** → isolation propre.

## Expérience : le champ de réaction adoucit-il le M ?

On résout le **même cas** (coupon 120×40 mm, hairpin, f = 388 kHz) deux fois — `M` seul vs
`K` complet — et on compare le contraste chant/centre du courant en largeur.

**Balayage épaisseur** (σ = 1,1·10⁴ S/m) :

| t (mm) | contraste M | contraste K | Δ |
|--------|-------------|-------------|-----|
| **0,20** (twill, seat principal) | 3,029 | 3,028 | **−0,0 %** |
| 0,50 | 3,029 | 3,024 | −0,2 % |
| 1,00 | 3,029 | 3,010 | −0,6 % |
| 2,00 | 3,029 | 2,959 | −2,3 % |
| 3,36 (stack entier) | 3,029 | 2,849 | −5,9 % |

**Balayage conductivité** (t = 0,2 mm) : même à σ = 10⁵ S/m (≈10× le twill), Δ ne dépasse
pas **−2 %**. Or fermer le résidu (3,15 → 2,09) demanderait **~−34 %**.

## Conclusions

- **Le champ de réaction est négligeable au régime du jumeau** (−0,03 % au twill). Mécanisme
  correct mais ∝ σ·t (magnitude du courant induit) : nos couches sont trop minces/résistives
  pour que l'auto-blindage morde. → **Pas un correctif du résidu #3**, et négliger la
  réaction (via `facteur_couplage`) est **justifié quantitativement**.
- **Corroboration externe forte** : un code indépendant, isotrope, sans MFC, reproduit un
  contraste ≈ **3,0** ≈ notre **3,15**. Le M sur-contrasté est donc de la **vraie physique
  plaque-mince** (écrasement du courant au chant), **pas** un artefact de notre anisotropie,
  des images MFC ni de la discrétisation.
- **Bilan** : aucun levier de correction n'émerge, mais la **limite du domaine de validité**
  (contraste M irréductible, cf. §résidu du [README modèle](README.md)) est désormais
  **appuyée par une vérification code-à-code indépendante** — position scientifique durcie,
  sans hack ajouté.

> Réserve : eppy étant isotrope / mono-plaque / sans MFC, l'égalité de valeur (3,03 vs 3,15)
> est une concordance d'**ordre et de mécanisme**, pas un appariement géométrique exact.
