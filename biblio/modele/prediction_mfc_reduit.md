# Prédiction figée — profil en largeur, MFC 55 mm vs 31,75 mm

**Figée le 2026-09-13, AVANT la campagne.** Issues #55 (mesure) et #60 (recalibration). Condition : **200 A, 18 s**, spot fixe `x = 60 mm`, 5 TC d'interface à `y = 0/10/20/30/40 mm` — soit exactement `exp7_200A`.

Ce document existe pour être **opposable après coup**. Il ne doit pas être réécrit une fois les mesures connues ; le confronter, et écrire le verdict ailleurs.

## 1. Ancrage — ce que le modèle vaut déjà sur cet observable

La passe A (MFC labo 55 mm) est déjà mesurée. L'erreur du modèle sur A est la barre à laquelle comparer tout écart prédit sur B.

| TC | y (mm) | mesuré A (°C) | modèle A (°C) | écart (°C) |
|---|---|---|---|---|
| TC1 | 0 | 274.1 | 321.5 | +47.5 |
| TC2 | 10 | 216.0 | 161.6 | -54.3 |
| TC3 | 20 | 144.7 | 115.9 | -28.8 |
| TC4 | 30 | 178.6 | 161.6 | -17.0 |
| TC5 | 40 | 269.0 | 321.5 | +52.6 |

Biais moyen **-0.0 °C**, écart absolu moyen **40.0 °C**. Contraste bord/centre : mesuré **1.89**, modèle **2.77**.

## 2. Prédiction — passe B (MFC réduit 31,75 mm)

| TC | y (mm) | modèle A (°C) | modèle B (°C) | Δ prédit (°C) | \|Δ\| vs erreur du modèle sur A |
|---|---|---|---|---|---|
| TC1 | 0 | 321.5 | 174.8 | -146.8 | ×3.1 — au-dessus du bruit |
| TC2 | 10 | 161.6 | 212.8 | +51.2 | ×0.9 — DANS le bruit |
| TC3 | 20 | 115.9 | 168.9 | +53.0 | ×1.8 — marginal |
| TC4 | 30 | 161.6 | 212.8 | +51.2 | ×3.0 — au-dessus du bruit |
| TC5 | 40 | 321.5 | 174.8 | -146.8 | ×2.8 — au-dessus du bruit |

Contraste bord/centre prédit : **2.77 → 1.03** (réduction ×2.68). Maximum du profil : **TC1 (y=0 mm) / TC5 (y=40 mm) → TC2 (y=10 mm) / TC4 (y=30 mm)**.

Le modèle part d'un contraste **sur-estimé** (2.77 contre 1.89 mesuré — c'est le résidu d'étalement in-plane documenté, issue #3). Si le raccourcissement agissait sur la mesure avec le même facteur ×2.68, le contraste réel passerait de 1.89 à **~0.71**, c'est-à-dire un profil **inversé** — centre plus chaud que les chants. C'est l'énoncé le plus discriminant de ce document, et le plus facile à lire sur la mesure.

À noter pour la lecture : le modèle 2D est **exactement symétrique** en y (TC1=TC5, TC2=TC4), alors que la mesure de A ne l'est pas (TC2=216 contre TC4=179 °C, 37 °C d'écart). Aucune prédiction par TC isolé ne peut donc être testée plus finement que cette asymétrie-là ; comparer de préférence les moyennes appariées (TC1,TC5) et (TC2,TC4).

## 3. Ce que la mesure peut RÉFUTER

Énoncés falsifiables, par ordre de robustesse décroissante.

1. **Le contraste bord/centre baisse.** Prédit 2.77 → 1.03. Réfuté si le contraste mesuré de B est supérieur ou égal à celui de A.
2. **Le maximum quitte le chant.** Prédit en TC2 (y=10 mm) / TC4 (y=30 mm). Réfuté si le maximum de B reste en TC1 ou TC5.
3. **Les chants refroidissent nettement.** Prédit TC1 -147 °C et TC5 -147 °C. **Énoncé le plus fragile** : le masque dur n'a pas de frange de bord, donc ces deux valeurs sont les moins crédibles de la sortie (limite 2 de l'en-tête).
4. **Le centre ne gagne pas la fusion.** Prédit TC3 = 169 °C, contre 337 °C de fusion — NON atteinte. Réfuté si le centre mesuré de B atteint la fusion à 200 A.

## 4. Portée et limites

- Le champ EM **n'est pas re-résolu** pour la géométrie réduite : la méthode des images ne dépend que de µ_r et d'un plan infini. Tout l'effet prédit vient du masque d'empreinte appliqué après coup.
- Le masque est un rectangle dur 0/1, sans frange : les valeurs aux chants sont les moins fiables.
- θ* n'est pas recalibré pour la géométrie réduite (objet de #60, après mesure).
- **Aucune source du corpus documentaire ne fait varier la longueur d'un concentrateur** (Mohan 2022 teste présence/absence et position de bobine, pas la longueur) : il n'y a pas d'appui bibliographique externe à cette prédiction.

Ce qui est prédit ici, ce sont des **tendances et des rapports**. Les niveaux absolus de la colonne B ne sont pas validés.

Reproduire : `.venv/bin/python code/scripts/gen/gen_prediction_mfc_reduit.py`
