# `data/` — données brutes (résultats **labo**)

Relevés thermocouples des essais physiques. Ces dossiers sont **référencés par les scripts et
les essais formels** (`config/essais/*.yaml`) — ne pas renommer/déplacer sans mettre à jour les
références. Index commenté : [`../docs/labo/README.md`](../docs/labo/README.md).

| Dossier | Campagne |
|---|---|
| `Serie A/` | Essais historiques (A-1 calibration, A-3 aveugle). |
| `Serie B/` | Basse consigne B-2 (loi thermostat « capteurs »). |
| `exp7_bord-centre_2026-07-28_avec-ceramique/` | Profil M en largeur, 5 courants, avec céramique (référence). |
| `exp9_dissipation-longitudinale_2026-07-28/` | Dissipation longitudinale, bord (y=0), 4 courants. |
| `exp9_dissipation-longitudinale_2026-07-30/` | Dissipation longitudinale, centre (y=20). |
| `chauffe_250A_3TC-epaisseur_2026-05-20.txt`, `chauffe_250A_5TC_2026-05-25.txt` | Relevés isolés anciens. |

Format des relevés : texte tab-séparé, décimale virgule, colonnes `Time (s)`, `TC1 (C)`… ; les
vidéos brutes caméra thermique (`*.mp4`) sont hors dépôt (gitignore).
