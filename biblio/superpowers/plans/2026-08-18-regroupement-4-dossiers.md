# Regroupement du dépôt en 4 dossiers — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Regrouper l'arborescence du dépôt en 4 dossiers de premier niveau — `ia/`, `code/`, `biblio/`, `donnees/` — sans casser imports, packaging, CI, skills ni références documentaires.

**Architecture:** Approche A (déplacement + réécriture mécanique). `R`/`RACINE` gardent la sémantique « racine du dépôt » ; on normalise leur calcul (marqueur `.git`) pour supprimer les 10 chemins absolus, puis on réécrit les tokens de sous-dossier. Principe : *ce qui migre ensemble et se référence en relatif ne casse pas* ; on ne corrige que les références inter-conteneurs (code→données, code→biblio) et le lien config→data de `procede.py`.

**Tech Stack:** Python 3.10+ (setuptools src-layout), pytest, git, perl/grep pour les sweeps.

**Spec:** `docs/superpowers/specs/2026-08-18-regroupement-4-dossiers-design.md` (migre en `biblio/superpowers/specs/…` au Lot 1 ; garder la spec + ce plan en contexte pendant l'exécution, car ils se déplacent).

## Global Constraints

- Branche : `chore/regroupement-4-dossiers` (déjà créée). Un commit par lot ; PR à la fin.
- Restent à la racine, NE PAS déplacer : `.claude/`, `.github/`, `README.md`, `.gitignore`.
- Après Lot 1, `pytest`/`pip` se lancent **depuis `code/`** (pyproject y est).
- Ne JAMAIS réécrire les skills tiers `.claude/skills/{academic-paper,academic-paper-reviewer,academic-pipeline,deep-research}/` (ils référencent leurs propres `scripts/`).
- Shell : préférer `git grep -lZ … | xargs -0` ou des tableaux ; ne pas compter sur le word-splitting d'une variable-chaîne (échec silencieux en zsh).
- Ancre repo-root normalisée (motif à réutiliser) :
  ```python
  R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
  ```

---

### Task 1: Déplacements (structure)

**Files:** `git mv` de tous les dossiers ; aucun contenu édité.

**Interfaces produites (nouveaux chemins que les lots suivants réparent) :** `ia/`, `code/{src,scripts,tests,third_party,config,pyproject.toml}`, `biblio/…`, `donnees/{data,journaux,resultats}`.

- [ ] **Step 1: Créer les conteneurs et déplacer**

```bash
cd "$(git rev-parse --show-toplevel)"
mkdir -p code donnees
git mv ai_framework ia
git mv src code/src
git mv scripts code/scripts
git mv tests code/tests
git mv third_party code/third_party
git mv config code/config
git mv pyproject.toml code/pyproject.toml
git mv docs biblio
git mv data donnees/data
git mv journaux donnees/journaux
# resultats/ : gitignoré (0 fichier suivi) — rien à git mv ; sera recréé à l'exécution des scripts
```

- [ ] **Step 2: Vérifier l'arborescence racine**

Run: `ls -1` puis `git status --porcelain | grep '^R' | wc -l`
Expected : à la racine, uniquement `ia code biblio donnees .github README.md` (+ `.claude`, `.gitignore` cachés) ; ~200+ renames détectés par git. **Les tests sont cassés à ce stade — normal.**

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "chore(reorg): deplace en 4 conteneurs ia/code/biblio/donnees (structure)"
```

---

### Task 2: Réparer les chemins du code + lien config→data

**Files:**
- Modify: les 16 scripts `code/scripts/{gen,diag}/*.py` + `code/scripts/*.py` (ancres) et tout `code/src/**/*.py` construisant des chemins repo-relatifs.
- Modify: `code/src/jumeau/procede.py` (profondeur `parents`).
- Modify: `code/config/essais/*.yaml` (14 fichiers, `fichier_mesures`).

**Interfaces consommées:** nouveaux emplacements du Lot 1.
**Interfaces produites:** `R = <repo root via .git>` dans tout script déplacé ; `procede.Procede.racine == repo root` ; `fichier_mesures` pointant `donnees/data/…`.

- [ ] **Step 1: Auditer les ancres à corriger**

```bash
cd "$(git rev-parse --show-toplevel)"
# chemins absolus hardcodés (à normaliser) :
git grep -lF 'Path("/Users/maxencedubois/PycharmProjects/Jumeau_Soudage_Induction'
# ancres parents[N] et tokens de sous-dossier :
git grep -nE '(R|RACINE) ?/ ?"(src|scripts|config|third_party|docs|journaux|data|resultats)"' -- 'code/**/*.py'
git grep -nE 'Path\(__file__\)\.resolve\(\)\.parents\[[0-9]\]' -- 'code/**/*.py'
```

- [ ] **Step 2: Normaliser l'ancre repo-root (supprime les chemins absolus + la dépendance à la profondeur)**

Dans **chaque** script déplacé qui définit `R = Path("/Users/…/Jumeau_Soudage_Induction")` OU `RACINE = Path(__file__).resolve().parents[N]` **et qui vise la racine du dépôt**, remplacer la ligne de définition par le motif marqueur `.git` (en gardant le nom de variable) :

```python
R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
```

Ne PAS toucher les ancres qui visent volontairement `code/` via `parents[1]` dans les tests (`code/tests/conftest.py`, `code/tests/test_diag_pareto.py`) : elles pointent désormais `code/` et référencent du code-interne → elles fonctionnent inchangées (vérifié au Step 6).

- [ ] **Step 3: Réécrire les tokens de sous-dossier (mapping)**

Sweep idempotent sur le code déplacé (fichiers listés par git grep, boucle robuste) :

```bash
cd "$(git rev-parse --show-toplevel)"
git grep -lZ -E '(R|RACINE) ?/ ?"(src|scripts|config|third_party|docs|journaux|data|resultats)"' -- 'code' | \
while IFS= read -r -d '' f; do
  perl -i -pe '
    s{(/ ?)"docs"}{$1"biblio"}g;
    s{(/ ?)"journaux"}{$1"donnees" / "journaux"}g;
    s{(/ ?)"data"}{$1"donnees" / "data"}g;
    s{(/ ?)"resultats"}{$1"donnees" / "resultats"}g;
    s{(/ ?)"(src|scripts|config|third_party)"}{$1"code" / "$2"}g;
  ' "$f"
done
```

Note : l'ordre compte (traiter `docs|journaux|data|resultats` AVANT `src|scripts|config|third_party` n'est pas requis ici car les motifs sont disjoints, mais garder ce bloc unique). Vérifier ensuite qu'aucun `"code" / "code"` ou `"donnees" / "donnees"` n'a été produit (idempotence) :

```bash
git grep -nE '"code" ?/ ?"code"|"donnees" ?/ ?"donnees"' -- 'code' || echo "OK idempotent"
```

- [ ] **Step 4: Corriger `procede.py` (profondeur config→racine)**

`code/src/jumeau/procede.py` — l'essai est désormais `code/config/essais/*.yaml` (racine = `parents[3]`) :

```python
# AVANT
self.racine = Path(racine) if racine else Path(chemin_essai).resolve().parents[2]
# APRÈS
self.racine = Path(racine) if racine else Path(chemin_essai).resolve().parents[3]
```

- [ ] **Step 5: Re-préfixer `fichier_mesures` dans les 14 essais**

```bash
cd "$(git rev-parse --show-toplevel)"
git grep -lZ -E '^\s*fichier_mesures:\s*data/' -- 'code/config/essais' | \
while IFS= read -r -d '' f; do
  perl -i -pe 's{^(\s*fichier_mesures:\s*)data/}{${1}donnees/data/}' "$f"
done
git grep -nE 'fichier_mesures:\s*data/' -- 'code/config/essais' || echo "OK: tous re-prefixes en donnees/data/"
```

- [ ] **Step 6: Vérifier — tests + exécution réelle du lien config→data**

```bash
cd "$(git rev-parse --show-toplevel)/code"
python -m pytest -q
# Expected: 123 passed
python scripts/valider.py --modele 2D --facteur 6.0123 --decalage-x 0 --essais exp7_200A 2>&1 | tail -5
# Expected: s'exécute sans FileNotFoundError (charge donnees/data/exp7…/…txt via procede)
python scripts/diag/diag_pareto_source_conduction.py --help >/dev/null && echo "diag imports OK"
```
Expected : `123 passed` ; `valider.py` charge les mesures et produit des métriques ; `--help` sort en 0.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "chore(reorg): repare les ancres de chemin du code + lien config->data (procede parents[3], 14 essais)"
```

---

### Task 3: Packaging & CI

**Files:** Modify `.github/workflows/ci.yml`.

- [ ] **Step 1: Faire tourner la CI depuis `code/`**

Ajouter au job `tests` un bloc `defaults` (couvre `pip install -e .` ET `pytest -q`) :

```yaml
jobs:
  tests:
    name: pytest (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: code
    strategy:
      ...
```

(`actions/checkout` et `setup-python` ne sont pas des `run:` → non affectés ; ils checkout la racine, ce qui est correct.)

- [ ] **Step 2: Vérifier la validité YAML**

```bash
python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml')); print('YAML OK')"
```
Expected: `YAML OK`.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: execute install+pytest depuis code/ (pyproject y a demenage)"
```

---

### Task 4: Fichiers racine — .gitignore, skills .claude, README

**Files:** Modify `.gitignore`, `.claude/skills/{ajouter-essai,calibrer-modele,simuler-essai,valider-croise}/SKILL.md`, `.claude/agents/{calibration-uq-specialist,validation-data-engineer}.md`, `.claude/settings.local.json` (non suivi), `README.md`.

- [ ] **Step 1: Ré-adresser `.gitignore`**

Éditer les lignes de chemin (laisser génériques `__pycache__/`, `*.pyc`, `.venv/`, `.DS_Store`, `build/`, `dist/`, `*.egg-info/`) :

```
resultats/                          → donnees/resultats/
journaux/resultats_*.log (×7)       → donnees/journaux/resultats_*.log
docs/**/*.pptx  /  docs/**/*.mp4     → biblio/**/*.pptx  /  biblio/**/*.mp4
docs/figures/*.pdf|*.tif|*.tiff      → biblio/figures/*.pdf|*.tif|*.tiff
config/essais/_session_*.yaml        → code/config/essais/_session_*.yaml
ai_framework/.env                    → ia/.env
data/**/*.mp4                        → donnees/data/**/*.mp4
```

- [ ] **Step 2: Ré-adresser les skills/agents projet (préfixes code/ et donnees/)**

```bash
cd "$(git rev-parse --show-toplevel)"
files=(.claude/skills/ajouter-essai/SKILL.md .claude/skills/calibrer-modele/SKILL.md \
       .claude/skills/simuler-essai/SKILL.md .claude/skills/valider-croise/SKILL.md \
       .claude/agents/calibration-uq-specialist.md .claude/agents/validation-data-engineer.md \
       .claude/settings.local.json)
for f in "${files[@]}"; do
  perl -i -pe '
    s{(?<![\w/])scripts/}{code/scripts/}g;
    s{(?<![\w/])config/}{code/config/}g;
    s{(?<![\w/])data/}{donnees/data/}g;
    s{(?<![\w/])journaux/}{donnees/journaux/}g;
    s{(?<![\w/])docs/}{biblio/}g;
  ' "$f"
done
```
Puis vérifier qu'aucun préfixe n'a été doublé :
```bash
git grep -nE 'code/code/|donnees/donnees/|code/scripts/gen/gen/' -- '.claude/skills/ajouter-essai' '.claude/skills/calibrer-modele' '.claude/skills/simuler-essai' '.claude/skills/valider-croise' '.claude/agents/calibration-uq-specialist.md' '.claude/agents/validation-data-engineer.md' || echo "OK: pas de double prefixe"
```

- [ ] **Step 3: Mettre à jour le README (racine)**

Éditer §8 « Structure du dépôt » pour refléter `ia/ code/ biblio/ donnees/`, et §7 « Utilisation » : commandes `python code/scripts/…`, tests lancés depuis `code/`. Réécrire les mentions repo-relative du README (`docs/…`→`biblio/…`, `scripts/…`→`code/scripts/…`, `config/…`→`code/config/…`, `data/…`→`donnees/data/…`, `journaux/…`→`donnees/journaux/…`).

- [ ] **Step 4: Vérifier**

```bash
# resultats gitignoré au nouveau chemin :
mkdir -p donnees/resultats && touch donnees/resultats/_t.png && git check-ignore donnees/resultats/_t.png && rm -f donnees/resultats/_t.png
# pptx gitignoré sous biblio :
git check-ignore "biblio/presentations/x.pptx" >/dev/null && echo "pptx ignore OK"
```
Expected : les deux chemins sont ignorés.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore(reorg): re-adresse .gitignore, skills/agents .claude, README vers ia/code/biblio/donnees"
```

---

### Task 5: Références croisées documentaires (markdown)

**Files:** Modify tous les `.md` suivis sous `biblio/` (ex-`docs/`) qui citent des chemins repo-relatifs.

- [ ] **Step 1: Sweep global des mentions repo-relative dans la doc**

Réécrire les préfixes repo-relatifs. Le `(?<![\w/.])` évite de re-préfixer un chemin déjà migré (`code/scripts/…`) ou un lien relatif interne (`../modele/…`, `references/…`) :

```bash
cd "$(git rev-parse --show-toplevel)"
git grep -lZ -E '(^|[^\w/.])(docs|scripts|config|data|journaux|resultats)/' -- 'biblio/**/*.md' 'README.md' | \
while IFS= read -r -d '' f; do
  perl -i -pe '
    s{(?<![\w/.])docs/}{biblio/}g;
    s{(?<![\w/.])journaux/}{donnees/journaux/}g;
    s{(?<![\w/.])resultats/}{donnees/resultats/}g;
    s{(?<![\w/.])data/}{donnees/data/}g;
    s{(?<![\w/.])scripts/}{code/scripts/}g;
    s{(?<![\w/.])config/}{code/config/}g;
  ' "$f"
done
```

- [ ] **Step 2: Vérifier — aucune référence périmée, aucun double préfixe**

```bash
# doubles préfixes (bug) :
git grep -nE 'biblio/biblio/|donnees/donnees/|code/code/|code/scripts/gen/gen/|donnees/data/data/' -- 'biblio' 'README.md' && echo ">>> DOUBLE PREFIXE — corriger" || echo "OK: pas de double prefixe"
# anciens préfixes repo-root encore présents (hors liens relatifs ../ et hors CSV racine donnees) :
git grep -nE '(^|[^\w/.])(scripts|config)/' -- 'biblio' 'README.md' | grep -vE 'code/(scripts|config)' | head
```
Expected : « OK: pas de double prefixe » ; la 2ᵉ commande ne renvoie que des faux positifs éventuels (prose), à trancher à l'œil.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "docs(reorg): relie les references repo-relative des .md vers ia/code/biblio/donnees"
```

---

## Vérification finale & PR

- [ ] **Tests depuis `code/`** : `cd code && python -m pytest -q` → `123 passed`.
- [ ] **Exécution réelle** : `python code/scripts/gen/gen_fenetre_soudage.py` (ou un gen écrivant sous `biblio/…/figures` — vérifier qu'il n'écrit pas hors arbre) ; `python code/scripts/valider.py --modele 2D --facteur 6.0123 --essais exp7_200A`.
- [ ] **Aucune référence périmée** : `git grep -nE '(^|[^\w/.])(docs|journaux)/' -- ':!biblio/**' ':!.claude/skills/academic-paper*' ':!.claude/skills/deep-research*'` ne renvoie rien de pertinent.
- [ ] **Arborescence racine** = `ia/ code/ biblio/ donnees/ .github/ .claude/ README.md .gitignore` uniquement.
- [ ] **`git status` propre**.
- [ ] **Push + PR** :

```bash
git push -u origin chore/regroupement-4-dossiers
gh pr create --base main --head chore/regroupement-4-dossiers \
  --title "chore: regroupement du depot en 4 dossiers (ia/code/biblio/donnees)" \
  --body "Voir la spec biblio/superpowers/specs/2026-08-18-regroupement-4-dossiers-design.md. 123 tests verts, lien config->data verifie par execution reelle."
```

## Self-review (couverture spec)

- §1 déplacements → Task 1 ✓ · §2 ancres code → Task 2 (Steps 2-3) ✓ · §3 hotspot config→data → Task 2 (Steps 4-6) ✓ · §4 packaging/CI → Task 3 ✓ · §5 gitignore/skills/README → Task 4 ✓ · §6 refs docs → Task 5 ✓ · §7 vérification → gates de chaque task + section finale ✓ · §8 risques → un commit par lot + vérif par exécution ✓.
