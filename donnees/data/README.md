# `data/` — données brutes (résultats **labo**)

Relevés thermocouples des essais physiques. Ces dossiers sont **référencés par les scripts et
les essais formels** (`config/essais/*.yaml`) — ne pas renommer/déplacer sans mettre à jour les
références. Index commenté : [`../docs/labo/README.md`](../docs/labo/README.md).

| Dossier | Campagne |
|---|---|
| `Serie A/` | Essais historiques (A-1 calibration, A-3 aveugle). |
| `Serie B/` | Basse consigne B-2 (loi thermostat « capteurs ») ; B-1 et B-2 sont deux extraits du relevé brut conservé à côté — voir le README du dossier. |
| `exp7_bord-centre_2026-07-28_avec-ceramique/` | Profil M en largeur, 5 courants, avec céramique (référence). |
| `exp9_dissipation-longitudinale_2026-07-28/` | Dissipation longitudinale, bord (y=0), 4 courants. |
| `exp9_dissipation-longitudinale_2026-07-30/` | Dissipation longitudinale, centre (y=20). |
| `epaisseur_3TC_2026-05/` | Gradient dans l'épaisseur (surface/interface/opposée empilés), 174/201/226 A + une répétition à 226 A. Même montage que le relevé 250 A ci-dessous. |
| `chauffe_250A_3TC-epaisseur_2026-05-20.txt`, `chauffe_250A_5TC_2026-05-25.txt` | Relevés isolés anciens. Le 3 TC est le point 250 A de la campagne `epaisseur_3TC_2026-05/`. |

Format des relevés : texte tab-séparé, décimale virgule, colonnes `Time (s)`, `TC1 (C)`… ; les
vidéos brutes caméra thermique (`*.mp4`) sont hors dépôt (gitignore).
