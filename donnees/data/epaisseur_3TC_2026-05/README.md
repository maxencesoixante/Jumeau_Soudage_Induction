# `epaisseur_3TC_2026-05/` — gradient dans l'épaisseur, 3 courants

Trois thermocouples **empilés au même point** (60, 20) : surface côté bobine,
interface de soudure (tissu PW), face opposée côté tube. C'est le montage de
`../chauffe_250A_3TC-epaisseur_2026-05-20.txt`, à d'autres courants.

| Fichier | Courant | Chauffe | Durée | Pic interface |
|---|---|---|---|---|
| `174A_v1.txt` | 174,4 A | 59 s | 228 s | 377,7 °C |
| `201A_v1.txt` | 201,6 A | 44 s | 203 s | 390,1 °C |
| `226A_v1.txt` | 226 A | 51 s | 288 s | 394,8 °C |
| `226A_v2.txt` | 226 A | 34 s | 184 s | 387,1 °C |

Les deux fichiers 226 A sont **deux répétitions du même essai**, pas deux
conditions. Leur écart est la donnée la plus utile du lot (voir plus bas).

## Protocole

Cycle de soudage complet dans une version **antérieure au semi-statique** : la
bobine et son MFC étaient posés fixes au centre de l'échantillon, sans
translation. C'est le même arrangement que l'essai 250 A, ce qui rend les quatre
courants directement comparables entre eux et avec lui.

La colonne de temps repart de zéro à l'acquisition. La chauffe démarre à t ≈ 1-2 s
et la coupure suit le pic d'interface ; la durée portée au tableau est mesurée de
l'onset au pic, pas déclarée. Le reste de chaque relevé est du refroidissement,
jusqu'à environ 30 % du pic.

## Ce que ces relevés apportent

Le rapport **face opposée / interface au pic** est la grandeur qui a servi à
recadrer la limite #2 du jumeau (gradient d'épaisseur trop faible, face opposée
sur-chauffée) et à calibrer `r_contact_interface`. Jusqu'ici elle ne reposait que
sur le seul essai 250 A, qui donne 0,42.

| Courant | opposée/interface | surface/interface |
|---|---|---|
| 174,4 A | 0,48 | 0,84 |
| 201,6 A | 0,42 | 0,88 |
| 226 A — v1 | 0,32 | 0,90 |
| 226 A — v2 | 0,44 | 0,87 |
| 250 A (`../chauffe_250A_3TC…`) | 0,39 | 0,94 |

**Les deux répétitions à 226 A s'écartent de 0,32 à 0,44.** Cet écart couvre
toute l'amplitude de la colonne : il n'y a pas de tendance en courant lisible
au-dessus de la répétabilité. Le nombre à retenir est donc une fourchette,
0,32-0,48, et non le 0,42 ponctuel — ce qui ne change pas le diagnostic (le
modèle sort ~0,9, très au-dessus de toute la fourchette) mais interdit de
calibrer un paramètre sur la troisième décimale de 0,42.

Le rapport surface/interface, lui, est stable (0,84-0,94) et confirme sur quatre
courants ce que le seul 250 A disait déjà : **la surface chauffe comme
l'interface**. L'ancienne cible `taux_TC1/TC2 ≈ 1,71` reste fausse.

## Provenance et réserves

Extraits de `MAX-WELDING-DATA-14_05_26.xlsx` (classeur créé le 14/05, enregistré
le 20/05), une feuille par courant. Deux réserves à connaître :

**Les courants viennent des cellules du classeur, pas des noms de feuille**, qui
les contredisent : la feuille `PW_interface_176.4A` porte la valeur 174,4 A, et
`PW_interface_225A` porte 226 A. Les noms de feuille sont faux, les cellules font
foi.

**La date des essais n'est pas établie.** Le classeur a été créé le 14/05 et
enregistré le 20/05 ; le relevé 250 A du même montage est daté du 20/05. Le
dossier porte donc le mois, pas le jour.

La cinquième feuille du classeur, `PW_interface_250A`, n'est pas reprise ici :
c'est exactement `../chauffe_250A_3TC-epaisseur_2026-05-20.txt` (lignes 11 à 195,
écart nul), dont le dépôt garde la version longue avec 152 points de
refroidissement en plus.

Format : texte tab-séparé, décimale virgule ; `TC1` = surface, `TC2` = interface,
`TC3` = face opposée.
