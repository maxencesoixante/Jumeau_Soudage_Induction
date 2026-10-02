# Journal d'avancement — renvoi vers le cahier de laboratoire

Depuis le **2 octobre 2026**, ce journal est **fusionné dans le cahier de laboratoire unique** du
projet, qui réunit tout ce qui a été fait, mesuré et noté (protocoles, fiches de campagne avec
dates et données brutes, journal chronologique, notes d'analyse, figures) :

**→ [`cahier_laboratoire_soudage_induction.md`](https://github.com/maxencesoixante/Memoire_Cahier_Labo_archive/blob/main/cahier_laboratoire_soudage_induction.md)**
(dépôt `Memoire_Cahier_Labo_archive`, clone local `Memoire_Soudage_InductionV2/`).

| Ce que contenait ce journal | Où le trouver dans le cahier |
|---|---|
| État du projet, chronologie des avancées (17 juillet → 2 octobre), résidus ouverts, prochaines étapes, leçons de méthode, carte des documents | **Partie 7** — journal chronologique des avancées |
| Les 140 figures intégrées aux entrées | Partie 7, fichiers dans `images/jumeau/` |
| Données brutes des essais (épaisseur à 3 TC, série B, bord → centre, longitudinale, 231 A, thermographie) | **Partie 6** — fiches de campagne |

**Les nouvelles entrées s'écrivent directement dans la partie 7 du cahier.** Le script
`code/scripts/gen/fusion_cahier_laboratoire.py` rafraîchit les parties 5, 6 et 8 depuis les
fichiers de `biblio/labo/` et `donnees/data/`, et conserve la partie 7 telle quelle.

La dernière version complète de ce journal reste dans l'historique git (commit `2c06eab`).
