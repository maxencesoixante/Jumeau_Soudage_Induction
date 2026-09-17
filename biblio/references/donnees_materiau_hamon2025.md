# Hamon & Laberge Lebel 2025 — ce que ce manuscrit apporte au jumeau

**Référence.** Hamon E., Laberge Lebel L., « Multi-Die Thermoplastic Pultrusion of Carbon
Reinforced PolyEtherKetoneKetone Bars at 1 m/min using Preimpregnated Tape », **manuscrit soumis**
à *Composites Part B* (JCOMB-S-25-10854, 2025-10-09), **non publié**. ACFSlab / CREPEC,
Polytechnique Montréal. Clé : `Hamon2025`. Note de lecture complète dans le vault Obsidian
(`20_sources/lectures/Hamon2025.md`).

⚠️ **Même consortium, même matériau.** Remerciements à **CRIAQ / COMPAAM** ; support matériel
Syensqo ; et le matériau est le nôtre — ruban préimprégné **APC AS4D 12K**. Ce n'est pas une
source externe interchangeable, c'est un travail frère.

Le sujet du papier — la pultrusion — ne nous concerne pas. Ce qui nous concerne, c'est que sa
**simulation EF du procédé exige des propriétés thermiques du C/PEKK**, et qu'il les publie.

## Ce qu'il confirme

| grandeur | `materiaux.yaml` | Hamon 2025 | provenance invoquée |
|---|---|---|---|
| `T_fusion` | 337 °C | **337 °C** | fiche technique Syensqo |
| `T_glass` | 159 °C | **159 °C** | fiche technique Syensqo |
| cristallinité | 30 % *(hypothèse de `L_f = 40 J/g`)* | **30 %** | fiche technique |
| `k_z` | 0,64 W/(m·K) *(Buser)* | **≈ 0,65** | thèse Saffar 2019 |

Les deux premières valeurs étaient en config **sans source traçable** ; elles le sont maintenant.
Le `k_z` est corroboré par une voie **indépendante** de celle qui l'avait fixé — deux sources à 2 %
l'une de l'autre. Et la cristallinité de 30 %, qui fonde le `L_f ≈ 40 J/g` du modèle de fusion
contre les 130 000 J/kg encore en config, est confirmée.

## Ce qu'il contredit

`cp_base = 1200 J/(kg·K)` **constant**. Le papier publie un **Cp(T) mesuré**, sans pic de fusion —
donc directement comparable à notre ligne de base :

| T (°C) | 50 | 100 | 150 | 200 | 250 | 300 | 350 | 400 | 450 |
|---|---|---|---|---|---|---|---|---|---|
| Cp (J/kg·K) | 939 | 1090 | 1224 | 1341 | 1441 | 1524 | 1590 | 1639 | 1671 |

**+78 % sur la plage.** Aux températures d'interface qui comptent (300-400 °C), le vrai `cp` vaut
**1524-1639**, soit **27-37 % au-dessus** du 1200 utilisé ; sous Tg il est plus bas. Le 1200 est un
compromis de milieu de gamme — pas une valeur fausse, mais il aplatit une variation réelle.

**Non adopté, et pour une raison précise.** `cp` a été testé et écarté plusieurs fois comme levier
scalaire du résidu de centre-fill ; et `facteur_couplage`, étant calibré, absorbe déjà une part de
cette erreur. Il faut donc s'attendre au même sort en held-out que `k(T)` (issue #4) : un **acquis
de propriété**, pas un correctif adoptable. Sa valeur est ailleurs — dans toute affirmation sur la
**température absolue d'interface**, donc pour le modèle de fusion, où la config canonique produit
déjà un faux positif systématique de dégradation.

## Données secondaires

Ruban **tel que reçu** (17 échantillons sur 17,5 m) : épaisseur **0,220 ± 0,008 mm** contre 0,14
nominal consolidé — l'écart mesure l'état non consolidé ; masse surfacique 232 ± 2 g/m² ; **taux de
vides 16 ± 3 %vol** ; taux de fibres 64 ± 7 %vol (nominal 58). Densité PEKK 1,31 g/cm³ à 30 % de
cristallinité ; rapport fondu/solide 89 %. Température de mise en œuvre **370 °C**.

Le taux de vides passe de **16 %** (ruban brut) à **1,8-2,8 %** après pultrusion : un ordre de
grandeur de ce que la consolidation sous pression referme, utile au dossier déconsolidation.

## La source à aller chercher

Réf. [23] : **Saffar F.**, « Étude de la consolidation interpli de stratifiés thermoplastiques
PEKK/fibres de carbone en conditions de basse pression », thèse, **Mines-Télécom Lille Douai,
2019**, en français.

C'est de là que viennent **le Cp(T) ET la conductivité transverse** — Hamon ne fait que les citer.
Et son sujet propre, la consolidation interpli **sous basse pression**, est exactement la lacune
identifiée dans le corpus (cf. `biblio/references/` et la mémoire projet). C'est la référence la
plus rentable à acquérir.

## Où cela a été inscrit

- `code/config/materiaux.yaml` — provenance ajoutée en commentaire sur `T_fusion`, `T_glass`,
  `chaleur_latente`, `k_z`, et le Cp(T) mesuré en regard de `cp_base` (valeurs **inchangées**).
- Vault Obsidian : note `Hamon2025`, inscrite au MOC « Jumeau numérique — références du modèle »
  en Tier 2.
- Zotero : item *manuscript*, clé `Hamon2025`, PDF attaché.
