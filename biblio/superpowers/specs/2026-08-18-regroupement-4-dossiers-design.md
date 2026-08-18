# Spec — Regroupement du dépôt en 4 dossiers de premier niveau

**Date** : 2026-08-18 · **Type** : architectural (restructuration de l'arborescence) ·
**Approche retenue** : A (déplacement + réécriture mécanique des chemins, sans nouvelle abstraction).

## Contexte & objectif

Le dépôt `Jumeau_Soudage_Induction` expose aujourd'hui ~11 dossiers de premier niveau
(`src/`, `scripts/`, `tests/`, `config/`, `data/`, `journaux/`, `docs/`, `ai_framework/`,
`third_party/`, …). L'utilisateur veut une lecture plus fluide via **4 grands dossiers** :

```
racine/                     # .claude/, .github/, README.md, .gitignore RESTENT ici
├── ia/          ← ai_framework/                       (couche IA multi-agents)
├── code/        ← src/, scripts/, tests/, third_party/, config/, pyproject.toml
├── biblio/      ← tout docs/ (references/, modele/, labo/, presentations/, superpowers/, journal)
└── donnees/     ← data/, journaux/ (+archive/), resultats/
```

Décisions validées : `code/` est **auto-portant** (contient `pyproject.toml`) ; `biblio/`
regroupe **toute** la documentation (pas seulement la bibliographie) ; `donnees/` regroupe
mesures + journaux + sorties ; noms `ia · code · biblio · donnees`.

**Principe directeur** (constaté à l'exploration) : *ce qui migre ensemble et se référence par
ancre relative ne casse pas* ; seules cassent (a) les références **inter-conteneurs**
(code→données, code→biblio) et (b) les **10 chemins absolus** codés en dur. Cela borne le rayon.

## 1. Déplacements (git mv)

- `ai_framework/` → `ia/`
- `src/` → `code/src/` ; `scripts/` → `code/scripts/` ; `tests/` → `code/tests/` ;
  `third_party/` → `code/third_party/` ; `config/` → `code/config/` ;
  `pyproject.toml` → `code/pyproject.toml`
- `docs/` → `biblio/` (bloc entier ; les liens relatifs internes à docs restent valides)
- `data/` → `donnees/data/` ; `journaux/` → `donnees/journaux/` (avec `archive/`) ;
  `resultats/` → `donnees/resultats/` (gitignoré ; répertoire recréé si besoin)

Restent à la racine : `.claude/`, `.github/`, `README.md`, `.gitignore`.

## 2. Réécriture des ancres de chemin dans le code

`R`/`RACINE` conservent la sémantique **« racine du dépôt »**. Deux opérations :

1. **Normaliser le calcul de la racine** pour supprimer les 10 chemins absolus
   (`Path("/Users/maxencedubois/PycharmProjects/Jumeau_Soudage_Induction")`) : remplacer par un
   calcul relatif robuste — remontée jusqu'au marqueur `.git` (préféré, indépendant de la
   profondeur) OU `parents[N]` avec le N correct de la nouvelle profondeur du fichier.
   Fichiers concernés : les 10 listés par `git grep -lF 'Path("/Users/maxencedubois/…'`
   (9 `code/scripts/gen/*.py` + `code/scripts/update_deck_comments.py`).

2. **Réécrire les tokens de sous-dossier** (table de mapping) partout où une ancre construit un
   chemin (`code/scripts/**`, `code/src/**`, `code/tests/**`) :

   | Avant | Après |
   |---|---|
   | `R/"src"`, `R/"scripts"`, `R/"config"`, `R/"third_party"` | `R/"code"/…` |
   | `R/"docs"` | `R/"biblio"` |
   | `R/"journaux"` | `R/"donnees"/"journaux"` |
   | `R/"data"` | `R/"donnees"/"data"` |
   | `R/"resultats"` | `R/"donnees"/"resultats"` |

   Volumétrie indicative (occurrences actuelles) : config ×42, src ×22, docs ×13, scripts ×9,
   journaux ×6, resultats ×4, data ×2. Les refs `sys.path.insert(0, R/"src")` et `R/"scripts"`
   (imports `jumeau` + `_style`) suivent la même règle → `R/"code"/"src"`, `R/"code"/"scripts"`.

## 3. Hotspot config→data (`procede.py` + 14 essais)

`src/jumeau/procede.py:66` :
`self.racine = Path(racine) if racine else Path(chemin_essai).resolve().parents[2]`.
Après déplacement, un essai vit sous `code/config/essais/*.yaml` → la racine du dépôt est
`parents[3]` (essais→config→code→racine). **Corriger `parents[2]` → `parents[3]`.**

Les 14 essais `code/config/essais/*.yaml` ont `fichier_mesures: data/…`. Comme `data/` migre vers
`donnees/data/`, réécrire ces valeurs **`data/…` → `donnees/data/…`** (édition explicite : le YAML
documente où sont ses mesures ; `self.racine / "donnees/data/…"` résout alors correctement).
Vérifié par `tests/test_essais_consolides.py` et par un `valider.py` réel.

## 4. Packaging & CI

- `code/pyproject.toml` : `[tool.setuptools.packages.find] where = ["src"]` et
  `testpaths = ["tests"]` **restent valides relativement à `code/`** (aucune édition du contenu).
- Conséquence : **`pytest` et `pip install -e .` s'exécutent depuis `code/`.**
  - `.github/workflows/*.yml` : ajouter `working-directory: code` (ou `cd code`) aux étapes
    d'install/test.
  - README §7 « Utilisation » : exemples `python code/scripts/…` ; tests lancés depuis `code/`.

## 5. Fichiers racine à ré-adresser

- **`.gitignore`** — préfixer les chemins déplacés :
  `resultats/`→`donnees/resultats/` ; `journaux/…log`→`donnees/journaux/…` ;
  `docs/**/*.pptx|mp4`→`biblio/**/*.pptx|mp4` ; `config/essais/_session_*.yaml`→`code/config/…` ;
  `ai_framework/.env`→`ia/.env` ; `data/**/*.mp4`→`donnees/data/**/*.mp4`.
  (`__pycache__/`, `*.pyc`, `.venv/`, `.DS_Store`, `build/`, `dist/`, `*.egg-info/` restent
  génériques, inchangés.)
- **`.claude/` (skills & agents)** — les skills projet `ajouter-essai`, `calibrer-modele`,
  `simuler-essai`, `valider-croise` et les agents `calibration-uq-specialist`,
  `validation-data-engineer` lancent `python scripts/…` et lisent `config/`,`data/` → préfixer
  `code/`/`donnees/`. `.claude/settings.local.json` (non suivi) : mêmes préfixes pour cohérence.
  NB : ne PAS toucher aux skills tiers (`academic-paper`, `deep-research`, …) qui référencent
  leurs propres `scripts/` internes.
- **README** — §8 « Structure du dépôt » : refléter les 4 dossiers ; §7 exemples de commandes.

## 6. Références croisées documentaires (markdown)

Réécriture mécanique **globale** des mentions repo-relative dans les `.md` (désormais sous
`biblio/`) et partout :
`docs/…`→`biblio/…` ; `scripts/…`→`code/scripts/…` ; `config/…`→`code/config/…` ;
`data/…`→`donnees/data/…` ; `journaux/…`→`donnees/journaux/…` ; `resultats/…`→`donnees/resultats/…`.
Les **liens relatifs internes** à l'ancien `docs/` (ex. `../modele/…`, `references/…`) restent
valides car tout `docs/` migre en bloc vers `biblio/`. Attention à l'idempotence (ne pas
re-préfixer un chemin déjà migré) et à ne pas toucher `config/…`.csv` inexistants.

## 7. Vérification (end-to-end)

Sur branche `chore/regroupement-4-dossiers` → PR. Après déplacements + réécritures :

1. **Tests** : depuis `code/`, `python -m pytest -q` → **123 passed** attendus.
2. **Exécution réelle** (au-delà des tests) :
   - un `code/scripts/gen/*` (ex. `gen_fenetre_soudage`) et un `code/scripts/diag/* --help` →
     imports `_style`/`jumeau` OK ;
   - `python code/scripts/valider.py --modele 2D --facteur 6.0123 --essais exp7_200A` → valide
     le lien **config→data** (`procede.py` + essai YAML) de bout en bout.
3. **Aucune référence périmée** : `git grep` ne renvoie plus de `("^|[^/])(docs|journaux|data|resultats)/`
   ni `scripts/`/`config/` non préfixés dans les fichiers suivis (hors skills tiers `.claude/skills/{academic-paper,deep-research,…}`).
4. **`git status` propre** ; arborescence racine = exactement `ia/ code/ biblio/ donnees/` +
   `.claude/ .github/ README.md .gitignore`.

## 8. Risques & mitigations

- **Exhaustivité** des ~24 réécritures inter-conteneurs + 14 YAML + normalisation des 10 ancres
  absolues → mitigé par la vérif **par exécution réelle** (pas seulement `pytest`) et le scan de
  références périmées.
- **CI** cassée si `working-directory: code` oublié → vérifier le workflow après coup.
- **Skills tiers** faussement réécrits → exclusion explicite des dossiers `academic-paper` /
  `deep-research` / etc. dans les sweeps.
- Diff volumineux → **un commit par lot** (déplacements ; ancres code ; hotspot config→data ;
  packaging/CI ; gitignore/skills/README ; refs docs) pour relecture et réversibilité.
