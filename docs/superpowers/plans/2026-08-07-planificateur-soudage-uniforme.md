# Planificateur de soudage uniforme — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Générer une séquence de passes de chauffe (position x/y, courant, durée) qui couvre toute l'interface ≥ fusion sans dégradation, et prouver la couverture par une carte `Tmax(x,y)`.

**Architecture:** Sur le jumeau 2D calibré (θ\* figé) : (A) une fonction d'**empreinte** simule une passe unique → carte du pic `Tmax(x,y)` ; (B) une **bibliothèque** pré-calcule ces empreintes sur une grille de positions/courants ; (C) un **planificateur glouton pur** combine des empreintes (`Tmax=max`) pour couvrir la surface sous contrainte de non-dégradation ; (D) une **vérification séquentielle** rejoue le plan en une simulation multi-passes réelle ; (E) un **CLI** produit plan + carte de couverture.

**Tech Stack:** Python, NumPy, matplotlib, pytest ; modules `src/jumeau/` (em, thermique, procédé), style figures `scripts/_style.py`.

## Global Constraints

- **θ\* de référence figé** (aucune recalibration) : `facteur_couplage=6.0123`, `h_haut=30.087`, `h_bas_2d=37.424`, `h_bord_x0=250`.
- **Fusion = 337.0 °C**, **dégradation = 450.0 °C** (constantes du domaine).
- **Courant ∈ [150, 250] A** (fenêtre validée ; interpolation seulement).
- **Non-régression** : toute modif du cœur physique (`source_spot`) doit être **bit-à-bit** identique par défaut (les 81 tests existants restent verts).
- **Sorties figures modèle pur** → `docs/modele/figures/` ; plan → `resultats/` (gitignoré).
- Grille 2D de référence : `nx=61, ny=21, nz=15` (comme `gen_prediction_courant.py`).

---

### Task 1: Décalage en y de la source (`source_spot centre_y`)

**Files:**
- Modify: `src/jumeau/em/source_joule.py` (signature de `source_spot` ~ligne 282 + appel `sommets_bobine` ~ligne 332)
- Test: `tests/test_planification.py`

**Interfaces:**
- Consumes: `geometrie.sommets_bobine(cfg, centre_x, centre_y=None)` (existe déjà ; `centre_y=None` → `laminate.largeur/2`).
- Produces: `source_spot(grille, cfg, couches, courant, centre_x, facteur_couplage=1.0, decalage_x=0.0, centre_y=None, champ_reaction=False, lissage_sigma_mm=0.0, lambda_bord_mm=0.0) -> np.ndarray` — `centre_y` (m, absolu ; `None` = centre de largeur) positionne la bobine en largeur.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_planification.py
import sys
from pathlib import Path
import numpy as np
import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
from jumeau.materiaux import Config
from jumeau.procede import Essai
from jumeau.em.source_joule import source_spot


def _essai():
    """Essai gabarit exp7 (grille + couches), θ* figé — pour les tests source."""
    cfg = Config.charger(RACINE / "config")
    cfg.contact.h_haut = 30.087
    cfg.ambiant.h_bas_2d = 37.424
    cfg.ambiant.h_bord_x0 = 250.0
    e = Essai(cfg, RACINE / "config/essais/exp7_200A.yaml", nx=61, ny=21, nz=15,
              facteur_couplage=6.0123, decalage_x=0.0, racine=RACINE)
    return cfg, e


def test_source_spot_centre_y_defaut_non_regressif():
    """centre_y=None reproduit bit-à-bit l'appel historique (sans centre_y)."""
    cfg, e = _essai()
    Q0 = source_spot(e.grille, cfg, e.couches, 200.0, 0.060, facteur_couplage=6.0123)
    Q1 = source_spot(e.grille, cfg, e.couches, 200.0, 0.060, facteur_couplage=6.0123,
                     centre_y=None)
    assert np.array_equal(Q0, Q1)


def test_source_spot_centre_y_deplace_le_pic_en_y():
    """Décaler centre_y déplace le barycentre en y de la source déposée."""
    cfg, e = _essai()
    y = e.grille.y
    def barycentre_y(Q):
        P = Q.sum(axis=(0, 2))            # puissance par bande y
        return float((P * y).sum() / P.sum())
    Q_haut = source_spot(e.grille, cfg, e.couches, 200.0, 0.060,
                         facteur_couplage=6.0123, centre_y=0.010)
    Q_bas = source_spot(e.grille, cfg, e.couches, 200.0, 0.060,
                        facteur_couplage=6.0123, centre_y=0.030)
    assert barycentre_y(Q_haut) < barycentre_y(Q_bas) - 1e-3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_planification.py -k centre_y -v`
Expected: FAIL — `source_spot() got an unexpected keyword argument 'centre_y'`.

- [ ] **Step 3: Add the `centre_y` parameter and thread it through**

Dans `src/jumeau/em/source_joule.py`, ajouter le paramètre à la signature de `source_spot` (après `decalage_x`) :

```python
    decalage_x: float = 0.0,
    centre_y: float | None = None,
```

et remplacer la construction de la bobine (~ligne 332) :

```python
    sommets = sommets_bobine(cfg, centre_x + decalage_x, centre_y=centre_y)
```

(Ajouter une phrase à la docstring : « ``centre_y`` (m, absolu ; ``None`` = centre de largeur) positionne la bobine en largeur — permet les passes décalées en y. »)

- [ ] **Step 4: Run tests to verify they pass + full suite non-régressive**

Run: `.venv/bin/python -m pytest tests/test_planification.py -k centre_y -v && .venv/bin/python -m pytest -q`
Expected: les 2 tests PASS ; suite complète toujours verte (83 tests).

- [ ] **Step 5: Commit**

```bash
git add src/jumeau/em/source_joule.py tests/test_planification.py
git commit -m "Planif (1/6) : décalage en y de la source (source_spot centre_y, non-régressif)"
```

---

### Task 2: Empreinte d'une passe (`Tmax(x,y)`)

**Files:**
- Create: `src/jumeau/planification/__init__.py` (vide)
- Create: `src/jumeau/planification/empreinte.py`
- Test: `tests/test_planification.py` (ajouts)

**Interfaces:**
- Consumes: `source_spot(..., centre_y=...)` (Task 1) ; `Essai(cfg, chemin, nx, ny, nz, facteur_couplage, decalage_x, racine)`, `e.simuler("2D") -> (sv, sol)`, `sv.resultat_2d(sol, i) -> np.ndarray (nx, ny)`, `e.grille` (`.x`, `.y`, `.largeur`, `.dz`).
- Produces: `empreinte(cfg, x_c, y_c, courant, duree, *, facteur=6.0123, nx=61, ny=21, nz=15) -> tuple[Grille3D, np.ndarray]` — renvoie `(grille, Tmax)` avec `Tmax` de forme `(nx, ny)` = pic de température d'interface pendant la passe.

- [ ] **Step 1: Write the failing test**

```python
def test_empreinte_forme_et_monotonie_courant():
    from jumeau.planification.empreinte import empreinte
    cfg = Config.charger(RACINE / "config")
    g, T160 = empreinte(cfg, 0.060, 0.020, 160.0, 15.0)
    _, T240 = empreinte(cfg, 0.060, 0.020, 240.0, 15.0)
    assert T160.shape == (g.nx, g.ny)
    assert T240.max() > T160.max()          # plus de courant -> plus chaud
    assert T160.min() >= 15.0               # au moins l'ambiant
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_planification.py::test_empreinte_forme_et_monotonie_courant -v`
Expected: FAIL — `ModuleNotFoundError: jumeau.planification`.

- [ ] **Step 3: Implement the footprint**

```python
# src/jumeau/planification/empreinte.py
"""Empreinte thermique d'une passe unique : carte du pic Tmax(x,y) à l'interface."""
from __future__ import annotations
from pathlib import Path
import numpy as np
from ..materiaux import Config
from ..procede import Essai
from ..em.source_joule import source_spot

_RACINE = Path(__file__).resolve().parents[3]
_GABARIT = _RACINE / "config" / "essais" / "exp7_200A.yaml"


def empreinte(cfg: Config, x_c: float, y_c: float, courant: float, duree: float,
              *, facteur: float = 6.0123, nx: int = 61, ny: int = 21, nz: int = 15):
    """Simule une passe (spot en (x_c, y_c), courant, durée) et renvoie
    (grille, Tmax) — Tmax(x,y) = pic de température d'interface. θ* figé."""
    cfg.contact.h_haut = 30.087
    cfg.ambiant.h_bas_2d = 37.424
    cfg.ambiant.h_bord_x0 = 250.0
    e = Essai(cfg, _GABARIT, nx=nx, ny=ny, nz=nz,
              facteur_couplage=facteur, decalage_x=0.0, racine=_RACINE)
    e.spots[0]["centre_x"] = x_c
    e.spec["duree_chauffe"] = duree
    e.spec["duree_totale"] = duree
    e.spots[0]["t_fin"] = duree
    Q = source_spot(e.grille, cfg, e.couches, courant, x_c,
                    facteur_couplage=facteur, centre_y=y_c)
    e._Q_spots = [Q]
    e._P_spots_2d = [Q.sum(axis=2) * e.grille.dz]
    sv, sol = e.simuler(modele="2D")
    champs = np.array([sv.resultat_2d(sol, i) for i in range(sol.t.size)])  # (nt,nx,ny)
    return e.grille, champs.max(axis=0)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_planification.py::test_empreinte_forme_et_monotonie_courant -v`
Expected: PASS (quelques secondes — 2 simulations 2D).

- [ ] **Step 5: Commit**

```bash
git add src/jumeau/planification/__init__.py src/jumeau/planification/empreinte.py tests/test_planification.py
git commit -m "Planif (2/6) : empreinte d'une passe (Tmax(x,y))"
```

---

### Task 3: Bibliothèque d'empreintes (grille de positions × courants)

**Files:**
- Modify: `src/jumeau/planification/empreinte.py` (ajout `bibliotheque`)
- Test: `tests/test_planification.py` (ajouts)

**Interfaces:**
- Consumes: `empreinte(cfg, x_c, y_c, courant, duree, ...)` (Task 2).
- Produces: `bibliotheque(cfg, x_cs, y_cs, courants, duree, **kw) -> tuple[Grille3D, dict[tuple[float,float,float], np.ndarray]]` — clé `(x_c, y_c, courant)` → `Tmax(x,y)`. Grille commune renvoyée à part.

- [ ] **Step 1: Write the failing test**

```python
def test_bibliotheque_cardinalite_et_cle():
    from jumeau.planification.empreinte import bibliotheque
    cfg = Config.charger(RACINE / "config")
    g, lib = bibliotheque(cfg, x_cs=[0.045, 0.075], y_cs=[0.020], courants=[200.0],
                          duree=12.0)
    assert len(lib) == 2                         # 2 x_c × 1 y_c × 1 courant
    assert (0.045, 0.020, 200.0) in lib
    assert lib[(0.045, 0.020, 200.0)].shape == (g.nx, g.ny)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_planification.py::test_bibliotheque_cardinalite_et_cle -v`
Expected: FAIL — `ImportError: cannot import name 'bibliotheque'`.

- [ ] **Step 3: Implement the library builder**

```python
# append to src/jumeau/planification/empreinte.py
from itertools import product


def bibliotheque(cfg: Config, x_cs, y_cs, courants, duree,
                 *, facteur: float = 6.0123, nx: int = 61, ny: int = 21, nz: int = 15):
    """Pré-calcule les empreintes sur la grille (x_cs × y_cs × courants).
    Renvoie (grille, {(x_c, y_c, courant): Tmax(x,y)})."""
    lib = {}
    grille = None
    for x_c, y_c, I in product(x_cs, y_cs, courants):
        g, T = empreinte(cfg, x_c, y_c, I, duree,
                         facteur=facteur, nx=nx, ny=ny, nz=nz)
        grille = g
        lib[(round(x_c, 6), round(y_c, 6), round(I, 3))] = T
    return grille, lib
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_planification.py::test_bibliotheque_cardinalite_et_cle -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/jumeau/planification/empreinte.py tests/test_planification.py
git commit -m "Planif (3/6) : bibliothèque d'empreintes (grille positions × courants)"
```

---

### Task 4: Planificateur glouton (cœur, PUR — testable sur cartes synthétiques)

**Files:**
- Create: `src/jumeau/planification/planificateur.py`
- Test: `tests/test_planification.py` (ajouts — synthétiques, rapides)

**Interfaces:**
- Consumes: rien du modèle (opère sur des cartes `np.ndarray`).
- Produces:
  - `metriques(Tmax, *, fusion=337.0, degrad=450.0) -> dict` avec clés `pct_soude`, `pct_non_soude`, `pct_degrade` (float, %).
  - `planifier(lib: dict[K, np.ndarray], *, ambiant=20.0, fusion=337.0, degrad=450.0) -> tuple[list[K], np.ndarray, dict]` — glouton ; renvoie `(passes_ordonnees, Tmax_combine, metriques)`. Une passe candidate est **rejetée** si `max(Tmax_combine, empreinte)` atteint `degrad` quelque part. S'arrête quand aucune passe n'augmente la surface soudée.

- [ ] **Step 1: Write the failing tests (synthétiques)**

```python
def test_metriques_comptage():
    from jumeau.planification.planificateur import metriques
    T = np.array([[300.0, 400.0], [500.0, 340.0]])   # 1 sous-fusion, 2 soudés, 1 dégradé
    m = metriques(T)
    assert m["pct_soude"] == pytest.approx(50.0)      # 400 et 340
    assert m["pct_degrade"] == pytest.approx(25.0)    # 500
    assert m["pct_non_soude"] == pytest.approx(25.0)  # 300


def test_planifier_couvre_domaine_tuilable():
    from jumeau.planification.planificateur import planifier
    # deux empreintes qui, combinées, soudent tout sans dégrader
    A = np.array([[340.0, 20.0]]); B = np.array([[20.0, 340.0]])
    passes, Tc, m = planifier({"A": A, "B": B}, ambiant=20.0)
    assert m["pct_soude"] == pytest.approx(100.0)
    assert set(passes) == {"A", "B"}
    assert m["pct_degrade"] == 0.0


def test_planifier_rejette_passe_degradante():
    from jumeau.planification.planificateur import planifier
    # C souderait la 2e case mais en dégradant (>=450) -> rejetée ; couverture partielle
    A = np.array([[340.0, 20.0]]); C = np.array([[20.0, 460.0]])
    passes, Tc, m = planifier({"A": A, "C": C}, ambiant=20.0)
    assert "C" not in passes
    assert m["pct_degrade"] == 0.0
    assert m["pct_soude"] == pytest.approx(50.0)       # seule la 1re case soudée


def test_planifier_sarrete_sans_amelioration():
    from jumeau.planification.planificateur import planifier
    A = np.array([[340.0, 20.0]]); D = np.array([[20.0, 100.0]])  # D ne soude rien
    passes, Tc, m = planifier({"A": A, "D": D}, ambiant=20.0)
    assert passes == ["A"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_planification.py -k "metriques or planifier" -v`
Expected: FAIL — `ModuleNotFoundError` / `cannot import name`.

- [ ] **Step 3: Implement the pure planner**

```python
# src/jumeau/planification/planificateur.py
"""Planificateur glouton PUR : couvre une surface avec des empreintes Tmax,
sous contrainte de non-dégradation. Indépendant du modèle (opère sur des cartes)."""
from __future__ import annotations
import numpy as np


def metriques(Tmax: np.ndarray, *, fusion: float = 337.0, degrad: float = 450.0) -> dict:
    """Pourcentages de surface : soudée (fusion..degrad), non soudée (<fusion),
    dégradée (>=degrad)."""
    n = Tmax.size
    degrade = Tmax >= degrad
    soude = (Tmax >= fusion) & ~degrade
    return {
        "pct_soude": 100.0 * float(soude.sum()) / n,
        "pct_non_soude": 100.0 * float((Tmax < fusion).sum()) / n,
        "pct_degrade": 100.0 * float(degrade.sum()) / n,
    }


def planifier(lib: dict, *, ambiant: float = 20.0, fusion: float = 337.0,
              degrad: float = 450.0):
    """Glouton : ajoute à chaque étape la passe qui soude le plus de NOUVELLE
    surface sans faire dépasser `degrad` nulle part. Renvoie
    (passes_ordonnees, Tmax_combine, metriques)."""
    ref = next(iter(lib.values()))
    combine = np.full_like(ref, ambiant, dtype=float)
    passes, restants = [], dict(lib)
    while True:
        meilleur, meilleur_gain, meilleur_comb = None, 0, None
        deja_soude = (combine >= fusion).sum()
        for cle, emp in restants.items():
            cand = np.maximum(combine, emp)
            if (cand >= degrad).any():          # contrainte dure : pas de dégradation
                continue
            gain = int((cand >= fusion).sum() - deja_soude)
            if gain > meilleur_gain:
                meilleur, meilleur_gain, meilleur_comb = cle, gain, cand
        if meilleur is None:                     # plus aucune amélioration
            break
        combine = meilleur_comb
        passes.append(meilleur)
        del restants[meilleur]
    return passes, combine, metriques(combine, fusion=fusion, degrad=degrad)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_planification.py -k "metriques or planifier" -v`
Expected: 4 PASS (instantané — synthétique).

- [ ] **Step 5: Commit**

```bash
git add src/jumeau/planification/planificateur.py tests/test_planification.py
git commit -m "Planif (4/6) : planificateur glouton pur + métriques (tests synthétiques)"
```

---

### Task 5: Vérification séquentielle du plan

**Files:**
- Modify: `src/jumeau/planification/planificateur.py` (ajout `verifier_sequentiel`)
- Test: `tests/test_planification.py` (ajouts — lent, 1 cas)

**Interfaces:**
- Consumes: `Essai`, `source_spot(..., centre_y=...)`, `sv.resultat_2d`.
- Produces: `verifier_sequentiel(cfg, passes_params, *, facteur=6.0123, nx=61, ny=21, nz=15) -> tuple[Grille3D, np.ndarray]` où `passes_params` est une liste de dicts `{"x_c","y_c","courant","duree"}` ; renvoie `(grille, Tmax_reel)` de la séquence complète (empreintes appliquées **en séquence temporelle**, chaque passe reprenant l'état thermique laissé par la précédente).

- [ ] **Step 1: Write the failing test (lent)**

```python
@pytest.mark.slow
def test_verifier_sequentiel_au_moins_aussi_couvrant_que_max():
    """La couverture séquentielle (chaleur résiduelle incluse) est >= la
    combinaison indépendante par max des mêmes passes (glouton conservateur)."""
    from jumeau.planification.empreinte import empreinte
    from jumeau.planification.planificateur import verifier_sequentiel, metriques
    cfg = Config.charger(RACINE / "config")
    passes = [{"x_c": 0.045, "y_c": 0.020, "courant": 220.0, "duree": 12.0},
              {"x_c": 0.075, "y_c": 0.020, "courant": 220.0, "duree": 12.0}]
    # combinaison indépendante (max des empreintes isolées)
    maps = [empreinte(cfg, p["x_c"], p["y_c"], p["courant"], p["duree"])[1] for p in passes]
    T_max_indep = np.maximum.reduce(maps)
    g, T_seq = verifier_sequentiel(cfg, passes)
    assert metriques(T_seq)["pct_soude"] >= metriques(T_max_indep)["pct_soude"] - 1e-6
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_planification.py -k verifier_sequentiel -v`
Expected: FAIL — `cannot import name 'verifier_sequentiel'`.

- [ ] **Step 3: Implement the sequential verifier**

```python
# append to src/jumeau/planification/planificateur.py
from pathlib import Path
from ..materiaux import Config
from ..procede import Essai
from ..em.source_joule import source_spot

_RACINE = Path(__file__).resolve().parents[3]
_GABARIT = _RACINE / "config" / "essais" / "exp7_200A.yaml"


def verifier_sequentiel(cfg: Config, passes_params, *, facteur: float = 6.0123,
                        nx: int = 61, ny: int = 21, nz: int = 15):
    """Rejoue le plan en UNE séquence multi-passes (chaleur résiduelle incluse)
    et renvoie (grille, Tmax_reel(x,y)). Chaque passe = un spot successif."""
    cfg.contact.h_haut = 30.087
    cfg.ambiant.h_bas_2d = 37.424
    cfg.ambiant.h_bord_x0 = 250.0
    e = Essai(cfg, _GABARIT, nx=nx, ny=ny, nz=nz,
              facteur_couplage=facteur, decalage_x=0.0, racine=_RACINE)
    # un spot par passe, enchaînés dans le temps (t_debut/t_fin séquentiels)
    t = 0.0
    spots, Qs = [], []
    for p in passes_params:
        spots.append({"centre_x": p["x_c"], "t_debut": t, "t_fin": t + p["duree"]})
        Qs.append(source_spot(e.grille, cfg, e.couches, p["courant"], p["x_c"],
                              facteur_couplage=facteur, centre_y=p["y_c"]))
        t += p["duree"]
    e.spots = spots
    e._Q_spots = Qs
    e._P_spots_2d = [Q.sum(axis=2) * e.grille.dz for Q in Qs]
    e.spec["duree_totale"] = t
    sv, sol = e.simuler(modele="2D")
    champs = np.array([sv.resultat_2d(sol, i) for i in range(sol.t.size)])
    return e.grille, champs.max(axis=0)
```

Note d'intégration : vérifier que `Essai.simuler` consomme bien `e.spots` (liste de dicts avec `centre_x`, `t_debut`, `t_fin`) et `e._Q_spots`/`e._P_spots_2d` déjà posés — c'est le patron de `scripts/gen_procede_semistatique.py` (4 dwells séquentiels). Si `Essai` reconstruit `_Q_spots` à partir des spots au lieu de réutiliser ceux fournis, s'aligner sur ce que fait `gen_procede_semistatique.py` (lire ce script avant d'implémenter).

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_planification.py -k verifier_sequentiel -v -m slow`
Expected: PASS (~10-30 s, simulation multi-passes).

- [ ] **Step 5: Commit**

```bash
git add src/jumeau/planification/planificateur.py tests/test_planification.py
git commit -m "Planif (5/6) : vérification séquentielle du plan"
```

---

### Task 6: CLI + carte de couverture + verdict

**Files:**
- Create: `scripts/planifier_soudage.py`
- Modify: (aucun test auto ; sortie visuelle relue à la main via la boucle figure-review)

**Interfaces:**
- Consumes: `bibliotheque` (Task 3), `planifier`, `metriques`, `verifier_sequentiel` (Tasks 4-5), `scripts/_style.py` (`apply_style`, palette).
- Produces: exécutable `python scripts/planifier_soudage.py` → `resultats/plan_soudage.yaml` + `docs/modele/figures/fig_plan_soudage_couverture.png` + verdict console.

- [ ] **Step 1: Write the CLI script**

```python
#!/usr/bin/env python3
"""Planificateur de soudage uniforme — génère un plan de passes couvrant toute
l'interface >= fusion sans dégradation, puis vérifie et trace la couverture.

Sortie : resultats/plan_soudage.yaml + docs/modele/figures/fig_plan_soudage_couverture.png
"""
import sys
from pathlib import Path
import numpy as np
import yaml
import matplotlib.pyplot as plt

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / "src"))
sys.path.insert(0, str(R / "scripts"))
from _style import apply_style
apply_style(**{"font.size": 11, "axes.labelsize": 12, "savefig.pad_inches": 0.06})
from jumeau.materiaux import Config
from jumeau.planification.empreinte import bibliotheque
from jumeau.planification.planificateur import planifier, metriques, verifier_sequentiel

FUSION, DEGRAD = 337.0, 450.0

# Grille de candidats : positions en x (4 le long de la longueur) × y (5 en largeur)
# × 2 courants (dans [150,250]). Durée de passe fixe.
X_CS = [0.030, 0.060, 0.090, 0.110]
Y_CS = [0.000, 0.010, 0.020, 0.030, 0.040]
COURANTS = [180.0, 220.0]
DUREE = 12.0


def main():
    cfg = Config.charger(R / "config")
    print("Construction de la bibliothèque d'empreintes…")
    grille, lib = bibliotheque(cfg, X_CS, Y_CS, COURANTS, DUREE)
    passes, Tc, m = planifier(lib, fusion=FUSION, degrad=DEGRAD)

    print(f"\nPlan : {len(passes)} passe(s) — soudé {m['pct_soude']:.1f} %, "
          f"non soudé {m['pct_non_soude']:.1f} %, dégradé {m['pct_degrade']:.1f} %")
    passes_params = [{"x_c": k[0], "y_c": k[1], "courant": k[2], "duree": DUREE}
                     for k in passes]
    for i, p in enumerate(passes_params, 1):
        print(f"  {i}. x={p['x_c']*1e3:.0f} mm  y={p['y_c']*1e3:.0f} mm  "
              f"I={p['courant']:.0f} A  t={p['duree']:.0f} s")

    # plan -> YAML
    (R / "resultats").mkdir(exist_ok=True)
    with open(R / "resultats" / "plan_soudage.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump({"passes": passes_params,
                        "couverture": m, "fusion": FUSION, "degradation": DEGRAD},
                       f, allow_unicode=True, sort_keys=False)

    # vérification séquentielle
    print("\nVérification séquentielle…")
    _, T_seq = verifier_sequentiel(cfg, passes_params)
    m_seq = metriques(T_seq, fusion=FUSION, degrad=DEGRAD)
    print(f"  séquentiel : soudé {m_seq['pct_soude']:.1f} %, "
          f"dégradé {m_seq['pct_degrade']:.1f} %")
    uniforme = m_seq["pct_soude"] >= 99.9 and m_seq["pct_degrade"] == 0.0
    print(f"\nVERDICT — uniforme : {'OUI' if uniforme else 'NON'}")

    _tracer(grille, T_seq, passes_params, m_seq)


def _tracer(grille, Tmax, passes_params, m):
    X, Y = np.meshgrid(grille.x * 1e3, grille.y * 1e3, indexing="ij")
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    # zones : bleu (<fusion) / vert (soudé) / rouge (>=degrad)
    from matplotlib.colors import ListedColormap, BoundaryNorm
    cmap = ListedColormap(["#D9E8F5", "#B7E4C7", "#F4C7C3"])
    norm = BoundaryNorm([-1e9, FUSION, DEGRAD, 1e9], cmap.N)
    ax.pcolormesh(X, Y, Tmax, cmap=cmap, norm=norm, shading="auto")
    cs = ax.contour(X, Y, Tmax, levels=[FUSION, DEGRAD],
                    colors=["#0072B2", "#C1272D"], linewidths=[1.3, 1.6])
    ax.clabel(cs, fmt={FUSION: "337", DEGRAD: "450"}, fontsize=7)
    for p in passes_params:
        ax.plot(p["x_c"] * 1e3, p["y_c"] * 1e3, "kx", ms=7, mew=1.6)
    ax.set_xlabel("Longueur $x$ (mm)")
    ax.set_ylabel("Largeur $y$ (mm)")
    ax.set_title(f"Plan de soudage — couverture Tmax : soudé {m['pct_soude']:.0f} %, "
                 f"non soudé {m['pct_non_soude']:.0f} %, dégradé {m['pct_degrade']:.0f} %")
    ax.set_aspect("equal")
    out = R / "docs" / "modele" / "figures" / "fig_plan_soudage_couverture.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    print("saved", out)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the CLI end-to-end**

Run: `.venv/bin/python scripts/planifier_soudage.py`
Expected: imprime le plan + le verdict, écrit `resultats/plan_soudage.yaml` et `docs/modele/figures/fig_plan_soudage_couverture.png` sans erreur.

- [ ] **Step 3: Relire la carte (boucle figure-review-loop)**

Ouvrir `docs/modele/figures/fig_plan_soudage_couverture.png` (Read) et vérifier : zones bleu/vert/rouge lisibles, contours 337/450, marqueurs de passes, titre avec métriques, pas de chevauchement. Ajuster si besoin (échelle, contours) et re-lancer.

- [ ] **Step 4: Full suite + commit**

Run: `.venv/bin/python -m pytest -q`
Expected: suite verte (les tests lents `-m slow` peuvent être exclus en routine).

```bash
git add scripts/planifier_soudage.py docs/modele/figures/fig_plan_soudage_couverture.png
git commit -m "Planif (6/6) : CLI planifier_soudage + carte de couverture + verdict"
```

---

## Self-Review

**Spec coverage :** chaque composant du spec est couvert — décalage y (T1), empreinte (T2), bibliothèque (T3), glouton+métriques (T4), vérif séquentielle (T5), CLI+carte+verdict (T6). Le « risque de faisabilité » est géré par le verdict honnête (T6, `uniforme: OUI/NON`) et les métriques de zone non couverte.

**Placeholders :** aucun — chaque étape porte le code réel. La seule note ouverte (T5, Step 3) demande de lire `gen_procede_semistatique.py` pour confirmer comment `Essai` consomme des spots séquentiels avec `_Q_spots` fournis ; c'est une vérification d'intégration, pas un placeholder de code.

**Type consistency :** `empreinte(...) -> (grille, Tmax)`, `bibliotheque(...) -> (grille, dict[(x,y,I) -> Tmax])`, `planifier(lib) -> (passes, Tmax, metriques)`, `metriques(Tmax) -> dict`, `verifier_sequentiel(cfg, passes_params) -> (grille, Tmax)` ; clés de `lib` = `(x_c, y_c, courant)` cohérentes entre T3, T4, T6 ; `passes_params` = liste de `{"x_c","y_c","courant","duree"}` cohérente T5/T6.

**Risque d'intégration connu :** la sémantique exacte de `Essai.spots`/`_Q_spots` en multi-passes séquentiel (T5) — à confirmer contre `gen_procede_semistatique.py` au moment de l'implémentation.
