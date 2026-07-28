# 150 A avec céramique — résultat (analyse Claude, 2026-07-28)

1 essai (`150A_v1.txt`), TC1 fonctionnel. Confirme les conclusions du 200 A à un
courant différent.

Profil ΔT au pic (°C au-dessus de l'ambiant) :

| y (mm) | 0 | 10 | 20 (centre) | 30 | 40 |
|---|---|---|---|---|---|
| mesuré | 223 | 199 | **139** | 151 | 224 |

- **M SYMÉTRIQUE** : chants y=0 (223) ≈ y=40 (224), ratio **1,00**.
- Contraste chant/centre ~1,6 (plus bas qu'à 200 A car cet essai a chauffé plus longtemps →
  le centre a eu plus de temps pour se remplir → contraste plus faible : cohérent).

**Le résidu « centre trop lent » est REPRODUIT (indépendant du courant)** — centre à
chant = 80 / 120 / 160 :

| | 80 | 120 | 160 |
|---|---|---|---|
| mesuré 150 A | 24 | 44 | 73 |
| modèle 150 A | 2 | 11 | 23 |

Le centre réel se remplit ~3× plus vite que le modèle, comme à 200 A → le défaut est
**structurel** (forme de la source), pas dépendant du courant. Renforce le diagnostic
`resultats_diag_centre_transitoire.log` (source trop concentrée aux chants ; levier =
adoucissement de la source, cf. prototype `../200A/proto_source_adoucie.png`).
