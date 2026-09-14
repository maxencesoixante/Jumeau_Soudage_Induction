# MFC raccourci — trois familles de modèles, et ce qui les sépare

Généré le 2026-09-14. Condition identique à la prédiction figée : **200 A, 18 s**, spot `x = 60 mm`, 5 TC d'interface — soit `exp7_200A`.

Ce document **complète** `prediction_mfc_reduit.md` (figé avant campagne) et ne le remplace pas. Les deux premières colonnes y sont identiques ; les deux dernières sont nouvelles, rendues calculables par la troncature de l'image au niveau du champ.

## Les trois familles

| famille | mécanisme | affirmation physique sur le flux manquant |
|---|---|---|
| **A — masque d'empreinte** | la puissance Joule totale est redistribuée sur l'empreinte restante | il **se reconcentre** sous le bloc plus petit |
| **B — image tronquée** (2 variantes) | seule la contribution image est pondérée ; le champ de la bobine nue reste entier | il **ne se reconcentre pas** : hors du bloc on retombe au cas sans MFC |

A et B ne diffèrent pas par leur finesse mais par une **hypothèse physique**. Aucun calcul ne tranche entre elles.

## Pics d'interface (°C)

| TC | y (mm) | MFC labo 55 mm | A — masque dur | B — image, observation | B — image, source |
|---|---|---|---|---|---|
| TC1 | 0 | 321.5 | 174.8 | 286.2 | 219.9 |
| TC2 | 10 | 161.6 | 212.8 | 150.8 | 116.4 |
| TC3 | 20 | 115.9 | 168.9 | 109.1 | 88.5 |
| TC4 | 30 | 161.6 | 212.8 | 150.8 | 116.4 |
| TC5 | 40 | 321.5 | 174.8 | 286.2 | 219.9 |
| **contraste bord/centre** | | **2.77** | **1.03** | **2.62** | **2.49** |

## Le résultat

**Les deux variantes de la famille B s'accordent** (2.49 et 2.62) alors qu'elles tronquent la même physique de deux façons indépendantes — l'une pondère l'observateur, l'autre la source. **La famille A est l'intrus** (1.03), pas un troisième point de la même famille.

Conséquence directe pour la campagne : selon que le contraste mesuré tombe vers **1.0** ou reste vers **2.5–2.6**, la mesure tranche entre « le flux se reconcentre » et « le flux disparaît localement ». L'issue #55 discrimine donc **trois familles au lieu de deux**.

Point chaud : il reste aux chants dans toute la famille B (TC1/TC5 > TC3 dans tous les cas), et ne se recentre que sous la famille A.

## Sensibilité à la marge d'adoucissement

La marge des variantes B vaut par défaut la hauteur du bloc (12 mm) — ordre de grandeur, non mesuré. Est-ce un paramètre libre qui décide du résultat ?

| marge (mm) | B — observation | B — source |
|---|---|---|
| 6 | 2.67 | 2.48 |
| 12 | 2.62 | 2.49 |
| 24 | 2.68 | 2.58 |

**Non.** Sur un facteur 4, les deux variantes restent dans la bande 2.48–2.68, sans jamais approcher la famille A ni inverser le profil. La marge est un paramètre libre assumé, mais elle ne décide pas du verdict.

## Limites

- Les trois familles sont des approximations de **1er ordre**. Aucune n'est de la physique établie : aucune ne résout le bloc de ferrite fini.
- La variante « observation » pondère le point d'observation, pas la position de chaque segment image le long du bloc ; la variante « source » corrige ce point mais suppose toujours η uniforme (valeur de demi-espace infini), sans correction de démagnétisation pour un bloc petit.
- θ* n'est recalibré pour aucune des géométries réduites (objet de #60, après mesure).
- **Aucune source du corpus documentaire ne fait varier la longueur d'un concentrateur** : il n'existe pas d'appui bibliographique externe à ces prédictions.

Reproduire : `.venv/bin/python code/scripts/gen/gen_prediction_mfc_familles.py`
