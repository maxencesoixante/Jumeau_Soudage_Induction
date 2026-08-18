# `facteur_couplage` — décomposition en contributions physiques ?

**Analyse (2026-08-05, issue #21).** Suite de l'analyse du dépôt Brassard (#16,
`../reference_brassard.md`), qui identifie *physiquement* une résistance de contact ≈ 50 %
là où nous laissons un facteur d'échelle agrégé. Question : peut-on décomposer notre
`facteur_couplage` en contributions nommées et chiffrées ?

## Ce que `facteur_couplage` est aujourd'hui
Un **scalaire multiplicatif unique** appliqué à la source Joule (`em/source_joule.py`,
`return facteur_couplage * _lisser_source(Q, …)`), valeur canonique **6,0123**
(`config/materiaux.yaml`). C'est **le seul facteur d'échelle libre de la source**. Il absorbe
un **produit** de contributions (docstrings `source_joule.py`, `foucault.py`, README) :

```
facteur_couplage ≈ η_géom × (σ_vrai / σ_config) × f_contact × f_blindage × …
```

- **η_géom** — efficacité du couplage bobine→plaque (approximations Biot-Savart + images MFC, µr=16 → facteur 0,88).
- **σ_vrai/σ_config** — incertitude sur la conductivité du **twill** (la puissance plaque-mince ∝ σ).
- **f_contact** — résistance de contact **fibre-fibre** du tissé (chemins de courant effectifs réduits).
- **f_blindage** — écrantage inter-couche (aujourd'hui : écran ad hoc `attenuation_blindage`).

## Verrou : la décomposition n'est PAS identifiable depuis la température
Depuis une calibration sur des températures, **seul le PRODUIT est identifiable** — les
facteurs individuels sont en **dégénérescence multiplicative exacte** (troquer une sous-estimation
de σ contre un `f_contact` plus faible laisse le résidu **rigoureusement inchangé**). C'est le
même mur que l'avertissement d'identifiabilité déjà acté `corr(facteur_couplage, decalage_x) =
0,985` (`identification/calibration.py`), mais en pire : ici la corrélation est **structurelle
et exacte**, pas seulement empirique. **Conclusion : on ne peut pas fitter 2-3 sous-facteurs ;
il faut mesurer indépendamment au moins l'un d'eux pour lever la dégénérescence.**

## Ce qui est déjà épinglé (réduit les inconnues)
| Contribution | État | Source |
|---|---|---|
| **f_blindage / réaction** | **≈ 1** (négligeable, 0,2–0,6 %) | vérif croisée eppy (`verification_croisee_eppy.md`), docstring `foucault.py`. *(NB : l'écran ad hoc `attenuation_blindage` reste actif par défaut = choix de modélisation, pas de la physique.)* |
| **Fréquence** | **mesurée** 388 kHz (figée) | relevé machine ; sinon totalement corrélée au facteur (leçon black-box f_I/r_I) |
| **η_géom** | **physique** depuis la correction de géométrie | entraxe 12,35 mm + hauteur 5,0 mm corrigés (issue #6), images MFC 0,88 |

→ Le blindage ne « gonfle » donc pas le facteur ; la fréquence et la géométrie sont
posées. **Le ~6× restant est dominé par `σ_vrai/σ_config` (twill) + `f_contact`.** Cohérent
avec le constat que les propriétés de config sont sous-estimées (~3× sur k_plan, issue #4) :
un facteur ~6 sur la source (∝ σ) est plausible si σ_config est plusieurs fois trop bas.

## Nuance vs Brassard (le signe diffère)
Chez Brassard, la résistance de contact **réduit** la puissance (facteur < 1, −45 %). Notre
`facteur_couplage > 1` (≈ 6) signifie au contraire que le modèle **sous-dépose** la puissance
*avant* mise à l'échelle → il est dominé par des **entrées sous-estimées** (σ), pas par des
pertes. L'analogie est **fonctionnelle** (une efficacité agrégée) mais **pas de même signe** :
le nôtre compense une sous-estimation d'entrée, le leur une perte physique.

## Décision (2026-08-05)
**Documenter l'agrégat, ne PAS décomposer en code pour l'instant.** Décomposer sans mesure
indépendante ne ferait que déplacer un paramètre libre parfaitement corrélé — et
réintroduirait la pathologie de corrélation déjà combattue (figer `decalage_x`, figer f).

**Déclencheur de réouverture nommé : la Mesure 10** (σ indépendant du twill/laminé, en plan et
vs T, 4-pointes / van der Pauw ; `../labo/mesures_a_realiser.md` §5). Une fois σ mesuré,
`σ_vrai/σ_config` s'effondre (→ ≈ 1) et le facteur résiduel **isole** l'efficacité
géométrique × contact — alors **physiquement interprétable et testable**, et le cas échéant
remplaçable par 1-2 facteurs nommés (dont certains posés par la mesure).

**Valeur de cette clôture :** interprétabilité pour la défense (on sait *ce que* le facteur
contient et *pourquoi* il vaut ~6), sans hack ni sur-paramétrage non identifiable.

## Références
`../reference_brassard.md` · `verification_croisee_eppy.md` (blindage ≈ 1) ·
`identification/calibration.py` (identifiabilité) · `em/source_joule.py` / `em/foucault.py`
(docstrings) · `config/materiaux.yaml` (`facteur_couplage`) · `../labo/mesures_a_realiser.md`
§5 (Mesure 10, déclencheur).
