# 150 A avec céramique — résultat (analyse Claude, 2026-07-28)

3 essais (`150A_v1/v2/v3.txt`), TC1 fonctionnel. Confirment les conclusions du 200 A à un
courant différent, et se répètent entre eux.

Profil ΔT au pic (°C au-dessus de l'ambiant) :

| y (mm) | 0 | 10 | 20 (centre) | 30 | 40 | symétrie | contraste |
|---|---|---|---|---|---|---|---|
| v1 | 223 | 199 | **139** | 151 | 224 | 1,00 | 1,61 |
| v2 | 238 | 219 | **161** | 175 | 240 | 0,99 | 1,49 |
| v3 | — | — | — | — | — | 1,00 | 1,46 |

- **M SYMÉTRIQUE** (ratio ~1,00 sur les deux).
- Contraste chant/centre ~1,5-1,6 (plus bas qu'à 200 A car ces essais ont chauffé plus
  longtemps → le centre a eu plus de temps pour se remplir : cohérent).

**Le résidu « centre trop lent » est REPRODUIT (v1≈v2, indépendant du courant)** — centre à
chant = 80 / 120 / 160 :

| | 80 | 120 | 160 |
|---|---|---|---|
| mesuré v1 | 24 | 44 | 73 |
| mesuré v2 | 27 | 51 | 77 |
| mesuré v3 | 26 | 48 | 76 |
| modèle 150 A | 2 | 11 | 23 |

Le centre réel se remplit ~3× plus vite que le modèle, comme à 200 A → le défaut est
**structurel** (forme de la source), pas dépendant du courant. Renforce le diagnostic
`resultats_diag_centre_transitoire.log` (source trop concentrée aux chants ; levier =
adoucissement de la source, cf. prototype `../200A/proto_source_adoucie.png`).
