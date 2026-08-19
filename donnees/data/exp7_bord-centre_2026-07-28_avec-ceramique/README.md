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

| Ampérage | Statut | M symétrique ? | Taux chant (ΔT 30→130) |
|---|---|---|---|
| 150 A | ✔ FAIT (v1/v2/v3 valides) | oui (ratio 1,00) | 9,7 °C/s |
| 176 A | ✔ FAIT (v1) | oui (ratio 1,00) | 15,7 °C/s |
| 200 A | ✔ FAIT (v4/v5/v6 valides) | oui (ratio 1,02-1,07) | 20,8 °C/s |
| 225 A | ✔ FAIT (v1) | oui (ratio 1,01) | 26,9 °C/s |
| 250 A | ✔ FAIT (v1/v2/v3 valides) | oui (ratio 1,02-1,03) | 34,2 °C/s |

*176 A et 225 A (1 essai chacun) ajoutés pour densifier la loi taux-courant. Contraste
centre-fill du même type à tous les courants (structurel, cf. sous-dossiers).*

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
limite hors-spot/centre-fill documentée**.

**Loi taux-courant (5 courants) — la source suit I².** Comme la chauffe n'a pas été
standardisée (arrêt manuel vers ~240 °C au chant), les *pics* ne se comparent pas ; l'observable
propre est le **taux de chauffe au chant** (sous le spot) : 9,7 / 15,7 / 20,8 / 26,9 / 34,2 °C/s.
Un ajustement en loi de puissance pure donne I^2,4, mais c'est un **artefact de pertes** : le
modèle **`R = k·I² − L`** (source en I² moins une perte thermique ~constante) fitte
**R²=0,999** avec **L≈3,5 °C/s** (indépendant du courant), mieux que la loi de puissance. Et
surtout, la **fréquence mesurée est CONSTANTE** (388±2 kHz sur 150-250 A, cf. relevé user
2026-07-28), ce qui **écarte** le couplage fréquence↔courant. → **La source suit bien la loi en
I² du modèle** ; l'écart apparent venait des pertes, pas de la source. Cf.
`docs/labo/figures/presentation_fig5`.

**Figures de présentation** (`docs/labo/figures/`) : `fig1` profil M aux 3 courants ·
`fig2` mesuré vs modèle · `fig3` dynamique centre-vs-chant · `fig4` courbes brutes 5 TC d'un
essai · `fig5` loi taux-courant (I^2,4).
