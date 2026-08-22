# Fiche protocole — MFC réduit (31,75 mm) : chauffe instrumentée en largeur & confrontation au jumeau

**Projet** : jumeau numérique du soudage par induction CF/PEKK · **Date de rédaction** : 2026-08-22
**Réalise l'objectif de** : documenter le passage au **MFC réduit recommandé par COMPAAM**
(Romain Martin, mai 2025 : un concentrateur ~½ pouce plus étroit que la largeur de soudure →
limite les effets de bord → chauffe homogène → réduit la déconsolidation, cite `Romain 2024`).
Fournit aussi la mesure qui **recalibre θ\*** et **valide le calcul EM conservatif** du MFC réduit.

---

## 1. Objectif et ce que ça résout

Deux inconnues, une seule campagne :

1. **Le MFC réduit chauffe-t-il plus uniformément sur la largeur ?** Le MFC labo (55 mm) **déborde
   des deux bords** de l'échantillon (largeur 40 mm) → chauffe concentrée aux bords (profil en
   « M ») → **squeeze-out latéral** observé sur les séries B. Le MFC réduit (31,75 mm) est
   **contenu dans la largeur** → on attend un dépôt **central**, des bords plus froids, un profil
   **aplati/centré**, et moins de squeeze-out. Cette campagne le **mesure** au lieu de le supposer.
2. **Le jumeau prédit-il correctement l'effet du MFC réduit ?** La prédiction actuelle est une
   extrapolation EM **1er ordre** (masque de source, flux conservé/concentré) **non recalibrée**
   pour cette géométrie : les niveaux absolus ne sont pas fiables. La mesure **recale θ\***
   (`facteur_couplage`) et confirme (ou corrige) le modèle.

**Enjeu procédé** : si le MFC réduit soude le **centre** de la largeur (aujourd'hui le point le
plus froid, non soudé au grand MFC), on obtient une **soudure pleine largeur plus homogène** avec
**moins d'expulsion de matrice** aux bords — c'est l'objet de la recommandation COMPAAM.

---

## 2. Principe : comparer deux MFC, tout le reste identique

On répète la **campagne en largeur (Exp 7)** — ligne de thermocouples **selon la largeur** (axe y),
à l'interface, spot centré — pour **deux concentrateurs**, à **courant et durée identiques** :

| Config | MFC | Empreinte (y × x) | Attendu sur la largeur |
|---|---|---|---|
| **A — référence** | labo **55 mm** | 55 × 31,5 mm (déborde des bords) | profil en **M** (bords chauds, centre froid) |
| **B — réduit** | **31,75 mm** | 31,75 × 31,5 mm (dans la largeur) | dépôt **central**, bords froids, profil aplati |

Le reste est **strictement inchangé** : empilement, film, céramique d'espacement (couplage 2 mm),
bobine hairpin, positions TC, courant, durée, séquence de coupure. Seul le **bloc MFC** change.
> La config A peut réutiliser les données **Exp 7 existantes** si le montage est identique ; sinon
> refaire une passe A le même jour pour une comparaison à conditions rigoureusement égales.

---

## 3. Montage (rappel) et instrumentation

- **Procédé** : soudage induction **semi-statique** (bobine fixe, table qui translate ; ici **un
  seul spot fixe**, centré à `x = 60 mm`).
- **Empilement** : laminé sup [45/-45/0/90]₃ₛ 3,36 mm + **pli twill suscepteur** à l'interface +
  film PEKK 0,004 po (0,1 mm) + laminé inf 3,36 mm. Plaque **120 × 40 mm**.
- **Concentrateur** : Fluxtrol **Ferrotron 559H** (µr ≈ 16). Config A = 55 mm ; config B = **31,75 mm**
  (grand côté **le long de la largeur y**), collé à la bobine (pâte thermique — cf. liste d'achats).
- **Couplage** : céramique d'espacement 2 mm (électromagnétiquement transparente), pression via
  piston pneumatique. **Noter la pression** (air ↔ interface, cf. classeur de calcul).
- **Thermocouples** : **5 TC type K à l'interface**, alignés **selon la largeur** à `x = 60 mm` :
  `y = 0 / 10 / 20 / 30 / 40 mm` (bord → centre → bord). Vérifier chaque voie (une voie débranchée
  lit ~2295 °C — à exclure). Acquisition LabVIEW, décimale point.

---

## 4. Plan d'essais

Balayer la **fenêtre de soudage** pour situer le seuil de fusion en fonction du courant :

| Passe | Courant | Durée | MFC | But |
|---|---|---|---|---|
| 1 | 200 A | fenêtre (≈ 18 s) | 55 mm (A) | référence M (ou réutiliser Exp 7 200 A) |
| 2 | 200 A | idem passe 1 | **31,75 mm (B)** | profil réduit à courant modéré |
| 3 | 250 A | fenêtre (≈ 15 s) | 55 mm (A) | référence M pleine chauffe |
| 4 | 250 A | idem passe 3 | **31,75 mm (B)** | **cas soudage** : le centre atteint-il Tf ? |

- **Durée** : caler sur la fenêtre de soudage (cf. `fig_loi_reglage` / `fig_fenetre_soudage`) pour
  viser l'interface juste au-dessus de **Tf ≈ 337 °C**, sous la **dégradation ≈ 450 °C**.
- **Répétabilité** : au moins **2 répétitions** de la passe 4 (le cas décisif).
- **Refroidissement** : laisser retomber < 100 °C entre passes (acquisition continue possible).

---

## 5. Grandeurs à relever (par passe)

1. **Profil en largeur** `T(y)` au pic (5 TC) → **contraste bord/centre**, position (y) du maximum.
2. **Pic d'interface** (max des 5 TC) et **T au centre** (`y = 20 mm`) — en **°C bruts**.
3. **Fraction soudée** en largeur : quels `y` dépassent **Tf = 337 °C** (largeur effectivement soudée).
4. **Squeeze-out latéral** : inspection visuelle des bords + **photos calibrées** (règle) après
   refroidissement ; noter la présence/ampleur du bourrelet aux **emplacements du spot** et la
   distorsion du twill (cf. `top.CR3`, séries B). Comparer A (55 mm) vs B (31,75 mm).
5. **Empreinte** thermique (le cas échéant, caméra IR — cf. issue #15) et **pression** appliquée.

---

## 6. Exploitation & confrontation au jumeau

1. **Comparaison directe A vs B** : le MFC réduit **aplatit-il** le profil (contraste ↓) et
   **déplace-t-il le point chaud** du bord vers le centre ? Le **centre atteint-il Tf** (passe 4) ?
   Le **squeeze-out latéral diminue-t-il** ?
2. **Recalibration θ\*** : ajuster `facteur_couplage` sur la **passe B** (mesure ↔ modèle, config
   `cfc.longueur = 0.03175`) — l'actuel θ\* = 6,0123 est calibré sur le MFC 55 mm.
   Commandes de référence :
   ```
   python code/scripts/gen/gen_mfc_reduit.py        # prédiction EM conservative (à comparer)
   python code/scripts/calibrer.py <essai_MFC_reduit>   # recale facteur_couplage sur la mesure B
   python code/scripts/valider.py <essai_MFC_reduit>    # confronte profil mesuré ↔ simulé
   ```
3. **Validation du calcul EM conservatif** : le modèle « flux conservé/concentré » (1er ordre)
   prédit-il le bon **niveau** et la bonne **forme** une fois θ\* recalé ? Si l'écart persiste, il
   faudra la **re-résolution complète de Bz** pour la géométrie de ferrite réduite (frange de champ
   proche, concentration réelle) — cf. `gen_mfc_reduit.py` (docstring) et `em/source_joule.py`.
4. **Créer l'essai** dans `code/config/essais/` (cf. skill `ajouter-essai`) : géométrie MFC réduit,
   5 TC à l'interface `y = 0/10/20/30/40`, spot `x = 60 mm`, courant/durée de la passe.

---

## 7. Critères de succès

- **Procédé** : le MFC réduit **soude le centre** (T_centre ≥ Tf à 250 A) avec un **contraste
  bord/centre nettement réduit** vs 55 mm, et **moins de squeeze-out latéral** (photos).
- **Modèle** : après recalibration θ\*, le jumeau reproduit le **profil B** (forme + niveau) à la
  barre habituelle ; sinon, diagnostic clair pointant la re-résolution EM.

---

## 8. Sécurité & notes

- PEKK au-dessus de **Tf ≈ 337 °C** : ventilation, gants, ne pas dépasser ~**450 °C** (dégradation).
- Vérifier la **pâte thermique** MFC ↔ bobine (contact thermique) avant la série.
- **Une seule variable à la fois** : ne changer QUE le MFC entre A et B (même courant, durée,
  céramique, pression, positions TC). Toute autre modification invalide la comparaison.
- Prochaine étape (hors périmètre) : répéter ce protocole pour le **MFC suivant** (spécifications à
  définir), même trame.
