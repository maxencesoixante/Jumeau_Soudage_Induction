# Exp 7 — Cartographie bord→centre AVEC céramique (campagne multi-ampérages)

**Objectif** : confronter le profil de température en largeur (le « M ») à la prédiction du
modèle, à **géométrie standard** (céramique en place = celle du modèle). Un **sous-dossier par
ampérage**.

```
150A/   200A/  (v2/v3/v4 — FAIT)   250A/   [300A/ non recommandé]
```

## Protocole (par essai)

- **Céramique d'espacement en place** + pression nominale (gap 2 mm = modèle).
- **5 TC valides à l'interface**, y = 0/10/20/30/40 mm, x = 60 mm (spot centré ou spot 3).
  Vérifier chaque voie AVANT : toutes doivent lire l'ambiant (même valeur à froid).
- **Montage centré en largeur** (viser TC1 ≈ TC5 à chaud → chants symétriques).
- **Chauffe STANDARDISÉE** : viser une durée fixe / un quasi-plateau (≈ 30-45 s), identique à
  tous les essais, pour pouvoir comparer aussi les **valeurs absolues** (les essais v2/v3/v4
  ont chauffé trop court → seule la forme était comparable).
- Nommer les fichiers `<I>A_v<n>.txt` et déposer dans le sous-dossier du courant.

## Cibles du modèle (θ\* de référence, spot centré, au pic)

| I (A) | y0 | y10 | y20 (centre) | y30 | y40 | contraste chant/centre |
|---|---|---|---|---|---|---|
| 150 | 303 | 174 | **127** | 174 | 303 | 2,69 |
| 200 | 468 | 276 | **207** | 276 | 468 | 2,43 |
| 250 | 708 | 382 | **292** | 382 | 708 | 2,55 |
| 300 | 962 | 546 | **348** | 546 | 962 | 2,89 |

⚠ **300 A : les chants atteignent ~962 °C** (bien au-dessus de la dégradation PEKK ~450 °C) →
**non recommandé** (dégradation des chants, pas exploitable).

## Ampérages à tester et répétitions — recommandation

- **150, 200 et 250 A** (la plage utile ; elle encadre les points de calibration : A-3 = 200 A,
  A-1/A-2 = 250 A, et teste la loi en I²). **Pas 300 A** (dégradation).
- **3 répétitions par ampérage.** Le trio 200 A (v2/v3/v4) a donné un contraste 2,16 / 2,17 /
  2,31 (dispersion ~0,07) : 3 essais donnent une moyenne solide et attrapent un TC défaillant.
  2 au minimum.
- **Priorité** : la FORME du M est déjà validée (200 A) ; ce qui reste à confronter, ce sont
  les **valeurs absolues** et la **loi en I²** → d'où l'importance d'une chauffe standardisée.

## Résultats

| Ampérage | Statut | M symétrique ? | Résidu centre-fill |
|---|---|---|---|
| 200 A | ✔ FAIT (v4/v5/v6 valides) | oui (ratio 1,07) | centre ~4× trop lent dans le modèle (cf. `200A/`) |
| 150 A | ✔ FAIT (v1/v2/v3 valides) | oui (ratio 1,00) | centre ~3× trop lent (idem → indépendant du courant, cf. `150A/`) |
| 250 A | ✔ FAIT (v1/v2/v3 valides) | oui (ratio 1,02-1,03) | contraste 2,05-2,19 ; même motif (cf. `250A/`) |

**Conclusion de la campagne (close)** : le profil en « M » est **symétrique et de bonne
forme d'équilibre**, confirmé aux **3 courants (150 / 200 / 250 A, 3 essais chacun)** ;
le seul résidu est **transitoire** — le centre du modèle se remplit trop lentement,
indépendamment du courant (structurel). Leviers testés et **écartés** : cp et masse
thermique (le taux fondamental sous spot est bon, ~15 % près — cf.
`resultats_diag_taux_chauffe.log`), k_plan (casse le contraste), placement TC. Le lissage
de source (gaussienne σ≈6 mm) remplit le centre **mais abaisse les pics** → posé derrière
le flag `--source-sigma-mm` (défaut off, non adopté). Le test **3D** confirme le mécanisme
(le lumping supprime une partie du taux hors-spot) mais **surchauffe l'interface** et
exigerait sa propre recalibration → **le 2D lumpé reste le modèle de travail, avec la
limite hors-spot/centre-fill documentée**. Figures de présentation :
`docs/figures_presentation/`.
