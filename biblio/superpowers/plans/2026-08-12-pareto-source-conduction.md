# Carte de faisabilité source × conduction — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Un script diagnostic qui balaie une grille 2D (`lambda_bord_mm` × `k_hot`) et répond GO/NO-GO à « existe-t-il un couple source-softening × conduction qui approche le contraste M mesuré ET ne régresse pas le held-out ? ».

**Architecture:** Un seul script `code/scripts/diag/diag_pareto_source_conduction.py` réutilisant `EssaiCalibre` (préchargement mesures + résidus σ-pondérés) de `code/scripts/calibrer_joint.py` et la recette de contraste de `code/scripts/diag/diag_anisotropie_kx_ky.py`. Par nœud de grille : (1) restaurer `facteur_couplage` par un fit 1-D sur le lot d'ajustement, (2) mesurer contraste M (exp7_200A) + RMSE held-out. Sorties : CSV + PNG + verdict console. Aucune modification de code/config/flags/θ*.

**Tech Stack:** Python, NumPy, `scipy.optimize.least_squares`, pandas, matplotlib (via `code/scripts/_style.py`).

## Global Constraints

- **Diagnostic en lecture seule côté modèle** : ne modifie AUCUN fichier de `code/config/`, aucun flag, aucun `θ*` de référence. N'écrit que ses propres sorties (CSV + PNG) et le script.
- **Grille imposée** : `lambda_bord_mm ∈ {0, 1, 2, 3, 4, 6}` × `k_hot ∈ {2, 3, 4, 5, 6}` ; `k_cold` **figé = 7.5** W/m·K ; ancrages k(T) = `KT_T_LO=20.0`, `KT_T_HI=340.0` °C.
- **θ figés au canonique** (jamais calibrés ici) : `h_haut=30.087`, `h_bas_2d=37.424`, `h_bord_x0=250.0`. Seul `facteur_couplage` est restauré (fit 1-D) par nœud.
- **Grilles de simulation** : RMSE/résidus sur `(nx, ny, nz) = (31, 11, 13)` (grille de calibration) ; **contraste** sur `(41, 15, 9)` (grille de la recette `contraste_m` de référence, pour reproduire ~3.13).
- **Lots d'essais** :
  - ajustement (fit `facteur` + RMSE lot) : `exp7_150A`, `exp7_200A`, `exp9_200A_y20_monospot` ;
  - held-out (garde-fou) : `exp7_250A`, `exp9_200A_monospot` ;
  - contraste : `exp7_200A`.
- **Critère (relatif au nœud de référence, calculé à l'identique)** : soit `RMSE_REF` = RMSE held-out du nœud isotrope de référence (`k_plan=3.0`, `lambda_bord=0`, k(T) OFF, `facteur` restauré). Un nœud est **FAISABLE** si `|contraste_M − 2.08| ≤ 0.15` ET `rmse_holdout ≤ RMSE_REF`. **QUASI-FAISABLE** si `|contraste_M − 2.08| ≤ 0.15` ET `rmse_holdout ≤ RMSE_REF + 0.7`. Verdict : `GO` si ≥1 faisable ; `QUASI-GO` si ≥1 quasi-faisable (aucun faisable) ; `NO-GO` sinon.

---

### Task 1: Helper de contraste avec k(T) + lambda_bord

**Files:**
- Create: `code/scripts/diag/diag_pareto_source_conduction.py`
- Test: `tests/test_diag_pareto.py`

**Interfaces:**
- Produces: `contraste_ktlb(facteur: float, k_hot: float | None, lambda_bord_mm: float, k_cold: float = 7.5, nx=41, ny=15, nz=9) -> tuple[float, np.ndarray]` — renvoie `(contraste, profil_normalisé)` pour `exp7_200A`. Si `k_hot is None` → nœud isotrope (`cfg.materiau.k_plan=3.0`, k(T) OFF) ; sinon k(T) = `[[20.0, k_cold], [340.0, k_hot]]`.

- [ ] **Step 1: Écrire le test qui échoue**

```python
# tests/test_diag_pareto.py
import sys
from pathlib import Path
RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))
sys.path.insert(0, str(RACINE / "src"))

import numpy as np
from diag_pareto_source_conduction import contraste_ktlb


def test_contraste_reference_isotrope():
    # Nœud de référence (k(T) OFF, lambda=0) reproduit le contraste connu ~3.13.
    c, profil = contraste_ktlb(facteur=6.0123, k_hot=None, lambda_bord_mm=0.0)
    assert 3.0 <= c <= 3.25
    assert profil.shape == (5,)
    assert abs(profil[2] - 1.0) < 1e-6  # normalisé par le pic centre (y=20mm)


def test_lambda_bord_abaisse_le_contraste():
    # La raideur de source adoucie (lambda_bord>0) réduit le contraste du M.
    c0, _ = contraste_ktlb(facteur=6.0123, k_hot=None, lambda_bord_mm=0.0)
    c6, _ = contraste_ktlb(facteur=6.0123, k_hot=None, lambda_bord_mm=6.0)
    assert c6 < c0
```

- [ ] **Step 2: Lancer le test pour vérifier qu'il échoue**

Run: `pytest tests/test_diag_pareto.py::test_contraste_reference_isotrope -v`
Expected: FAIL (ModuleNotFoundError / ImportError : `contraste_ktlb` inexistant).

- [ ] **Step 3: Écrire l'implémentation minimale**

```python
#!/usr/bin/env python
"""Carte de faisabilité SOURCE × CONDUCTION (réouverture du résidu in-plane).

Étape C de la séquence C→A (cf. biblio/superpowers/specs/2026-08-12-pareto-
source-conduction-design.md). Balaie lambda_bord_mm × k_hot (k_cold figé),
restaure facteur_couplage par nœud, mesure contraste M + RMSE held-out, et
imprime un verdict GO/QUASI-GO/NO-GO. Diagnostic pur : ne modifie ni config,
ni flags, ni θ*. N'écrit que son CSV et son PNG.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from jumeau.materiaux import Config
from jumeau.procede import Essai

H_HAUT_FIGE = 30.087
H_BAS_2D_FIGE = 37.424
H_BORD_X0_FIGE = 250.0
K_COLD_FIGE = 7.5
KT_T_LO, KT_T_HI = 20.0, 340.0
K_PLAN_REF = 3.0

FIT = ("exp7_150A", "exp7_200A", "exp9_200A_y20_monospot")
HELDOUT = ("exp7_250A", "exp9_200A_monospot")
CONTRASTE_ESSAI = "exp7_200A"


def _cfg_noeud(k_hot: float | None, k_cold: float = K_COLD_FIGE) -> Config:
    """Config canonique + conduction du nœud. k_hot None => isotrope k_plan=3."""
    cfg = Config.charger(RACINE / "config")
    cfg.contact.h_haut = H_HAUT_FIGE
    cfg.ambiant.h_bas_2d = H_BAS_2D_FIGE
    cfg.ambiant.h_bord_x0 = H_BORD_X0_FIGE
    cfg.materiau.k_plan_x = cfg.materiau.k_plan_y = None
    if k_hot is None:
        cfg.materiau.k_plan_T = None
        cfg.materiau.k_plan = K_PLAN_REF
    else:
        cfg.materiau.k_plan_T = [[KT_T_LO, float(k_cold)], [KT_T_HI, float(k_hot)]]
    return cfg


def contraste_ktlb(facteur: float, k_hot: float | None, lambda_bord_mm: float,
                   k_cold: float = K_COLD_FIGE, nx=41, ny=15, nz=9):
    """Contraste du profil M (exp7_200A) — recette gen_figures_elsevier::fig2 /
    diag_anisotropie_kx_ky.contraste_m, étendue à k(T) + lambda_bord."""
    cfg = _cfg_noeud(k_hot, k_cold)
    e = Essai(cfg, RACINE / "config" / "essais" / f"{CONTRASTE_ESSAI}.yaml",
              nx=nx, ny=ny, nz=nz, facteur_couplage=facteur, decalage_x=0.0,
              racine=RACINE, lambda_bord_mm=lambda_bord_mm)
    sv, sol = e.simuler(modele="2D")
    mod = np.array([sv.serie_temporelle(sol, 0.060, y, "interface").max()
                    for y in (0.0, 0.010, 0.020, 0.030, 0.040)])
    amb = float(sv.serie_temporelle(sol, 0.060, 0.020, "interface")[0])
    profil = (mod - amb) / (mod[2] - amb)
    return float((profil[0] + profil[4]) / 2), profil
```

- [ ] **Step 4: Lancer les tests pour vérifier qu'ils passent**

Run: `pytest tests/test_diag_pareto.py -v`
Expected: PASS (2 tests). (Chacun lance des simulations 2D coarse — quelques secondes.)

- [ ] **Step 5: Commit**

```bash
git add code/scripts/diag/diag_pareto_source_conduction.py tests/test_diag_pareto.py
git commit -m "feat(pareto): helper contraste_ktlb (k(T)+lambda_bord) + tests sanity"
```

---

### Task 2: Restauration d'amplitude (fit 1-D) + RMSE held-out

**Files:**
- Modify: `code/scripts/diag/diag_pareto_source_conduction.py`
- Test: `tests/test_diag_pareto.py`

**Interfaces:**
- Consumes: `EssaiCalibre` de `code/scripts/calibrer_joint.py` (`.residus(cfg, facteur, sigma_mm, lambda_bord_mm)`, `.rapport(...)` → DataFrame index TC, colonne `"rmse"`).
- Produces:
  - `restaurer_facteur(essais_fit: list, cfg, lambda_bord_mm: float, facteur0=6.0123, max_nfev=15) -> float`
  - `rmse_pooled(essais: list, cfg, facteur: float, lambda_bord_mm: float) -> float` (moyenne des RMSE par-TC sur tous les essais).

- [ ] **Step 1: Écrire le test qui échoue**

```python
# append to tests/test_diag_pareto.py
from diag_pareto_source_conduction import (restaurer_facteur, rmse_pooled,
                                           charger_essais, _cfg_noeud)


def test_noeud_reference_rmse_et_facteur():
    fit = charger_essais(("exp7_150A", "exp7_200A", "exp9_200A_y20_monospot"))
    held = charger_essais(("exp7_250A", "exp9_200A_monospot"))
    cfg = _cfg_noeud(k_hot=None)  # isotrope de référence
    facteur = restaurer_facteur(fit, cfg, lambda_bord_mm=0.0)
    assert 4.5 <= facteur <= 8.0          # restaure ~6.0 sur le lot d'ajustement
    rmse = rmse_pooled(held, cfg, facteur, lambda_bord_mm=0.0)
    assert 12.0 <= rmse <= 21.0           # ordre de grandeur du held-out de réf (~16.5)
```

- [ ] **Step 2: Lancer le test pour vérifier qu'il échoue**

Run: `pytest tests/test_diag_pareto.py::test_noeud_reference_rmse_et_facteur -v`
Expected: FAIL (ImportError : `restaurer_facteur` / `rmse_pooled` / `charger_essais` inexistants).

- [ ] **Step 3: Écrire l'implémentation minimale**

```python
# append to code/scripts/diag/diag_pareto_source_conduction.py
from calibrer_joint import EssaiCalibre

NX, NY, NZ = 31, 11, 13


def charger_essais(noms, nx=NX, ny=NY, nz=NZ):
    return [EssaiCalibre(n, nx, ny, nz) for n in noms]


def restaurer_facteur(essais_fit, cfg, lambda_bord_mm, facteur0=6.0123, max_nfev=15):
    """Fit 1-D de facteur_couplage minimisant les résidus σ-pondérés du lot."""
    def resid(x):
        f = float(x[0])
        return np.concatenate([e.residus(cfg, f, 0.0, lambda_bord_mm) for e in essais_fit])
    res = least_squares(resid, x0=[facteur0], bounds=([0.5], [30.0]),
                        max_nfev=max_nfev, method="trf")
    return float(res.x[0])


def rmse_pooled(essais, cfg, facteur, lambda_bord_mm):
    """Moyenne des RMSE par-TC (colonne 'rmse' de rapport_essai) sur les essais."""
    vals = []
    for e in essais:
        rap = e.rapport(cfg, facteur, 0.0, lambda_bord_mm)
        vals.extend(rap["rmse"].tolist())
    return float(np.mean(vals))
```

- [ ] **Step 4: Lancer le test pour vérifier qu'il passe**

Run: `pytest tests/test_diag_pareto.py::test_noeud_reference_rmse_et_facteur -v`
Expected: PASS. (Note : lent — plusieurs simulations ; ~30-60 s.)

- [ ] **Step 5: Commit**

```bash
git add code/scripts/diag/diag_pareto_source_conduction.py tests/test_diag_pareto.py
git commit -m "feat(pareto): restauration facteur 1-D + rmse_pooled held-out"
```

---

### Task 3: Classification des nœuds + verdict (fonctions pures)

**Files:**
- Modify: `code/scripts/diag/diag_pareto_source_conduction.py`
- Test: `tests/test_diag_pareto.py`

**Interfaces:**
- Produces:
  - `classer(contraste: float, rmse_holdout: float, rmse_ref: float, cible=2.08, tol=0.15, marge_quasi=0.7) -> str` → `"faisable" | "quasi" | "hors"`.
  - `verdict(classes: list[str]) -> str` → `"GO" | "QUASI-GO" | "NO-GO"`.

- [ ] **Step 1: Écrire les tests qui échouent**

```python
# append to tests/test_diag_pareto.py
from diag_pareto_source_conduction import classer, verdict


def test_classer():
    # contraste dans la boîte + RMSE ≤ réf → faisable
    assert classer(2.10, 16.0, rmse_ref=16.5) == "faisable"
    # contraste ok mais RMSE entre réf et réf+0.7 → quasi
    assert classer(2.10, 17.0, rmse_ref=16.5) == "quasi"
    # contraste hors boîte → hors quel que soit le RMSE
    assert classer(2.50, 15.0, rmse_ref=16.5) == "hors"
    # contraste ok mais RMSE > réf+marge → hors
    assert classer(2.10, 18.0, rmse_ref=16.5) == "hors"


def test_verdict():
    assert verdict(["hors", "faisable", "quasi"]) == "GO"
    assert verdict(["hors", "quasi", "hors"]) == "QUASI-GO"
    assert verdict(["hors", "hors"]) == "NO-GO"
```

- [ ] **Step 2: Lancer les tests pour vérifier qu'ils échouent**

Run: `pytest tests/test_diag_pareto.py::test_classer tests/test_diag_pareto.py::test_verdict -v`
Expected: FAIL (ImportError : `classer` / `verdict` inexistants).

- [ ] **Step 3: Écrire l'implémentation minimale**

```python
# append to code/scripts/diag/diag_pareto_source_conduction.py
def classer(contraste, rmse_holdout, rmse_ref, cible=2.08, tol=0.15, marge_quasi=0.7):
    if abs(contraste - cible) > tol:
        return "hors"
    if rmse_holdout <= rmse_ref:
        return "faisable"
    if rmse_holdout <= rmse_ref + marge_quasi:
        return "quasi"
    return "hors"


def verdict(classes):
    if "faisable" in classes:
        return "GO"
    if "quasi" in classes:
        return "QUASI-GO"
    return "NO-GO"
```

- [ ] **Step 4: Lancer les tests pour vérifier qu'ils passent**

Run: `pytest tests/test_diag_pareto.py::test_classer tests/test_diag_pareto.py::test_verdict -v`
Expected: PASS (rapide, aucune simulation).

- [ ] **Step 5: Commit**

```bash
git add code/scripts/diag/diag_pareto_source_conduction.py tests/test_diag_pareto.py
git commit -m "feat(pareto): classification noeuds + verdict GO/QUASI-GO/NO-GO"
```

---

### Task 4: Balayage de la grille + CSV + `main`

**Files:**
- Modify: `code/scripts/diag/diag_pareto_source_conduction.py`

**Interfaces:**
- Consumes: `contraste_ktlb`, `charger_essais`, `restaurer_facteur`, `rmse_pooled`, `classer`, `verdict`.
- Produces:
  - `balayer(lambdas, k_hots) -> pandas.DataFrame` (colonnes : `lambda_bord_mm, k_hot, facteur, contraste_M, rmse_holdout, rmse_fit, classe`) ; la 1re ligne est le nœud de référence isotrope (`k_hot=NaN`), qui fixe `RMSE_REF`.
  - `main()` (argparse `--lambdas`, `--k-hots`, `--csv`, `--png`), écrit le CSV, appelle la figure (Task 5), imprime le verdict.

- [ ] **Step 1: Écrire le balayage et le main**

```python
# append to code/scripts/diag/diag_pareto_source_conduction.py
LAMBDAS = [0.0, 1.0, 2.0, 3.0, 4.0, 6.0]
K_HOTS = [2.0, 3.0, 4.0, 5.0, 6.0]


def balayer(lambdas=LAMBDAS, k_hots=K_HOTS):
    fit = charger_essais(FIT)
    held = charger_essais(HELDOUT)

    # nœud de référence isotrope -> RMSE_REF
    cfg_ref = _cfg_noeud(k_hot=None)
    f_ref = restaurer_facteur(fit, cfg_ref, 0.0)
    rmse_ref = rmse_pooled(held, cfg_ref, f_ref, 0.0)
    c_ref, _ = contraste_ktlb(f_ref, None, 0.0)
    lignes = [dict(lambda_bord_mm=0.0, k_hot=float("nan"), facteur=f_ref,
                   contraste_M=c_ref, rmse_holdout=rmse_ref, rmse_fit=float("nan"),
                   classe="reference")]
    print(f"[REF] facteur={f_ref:.4f}  contraste={c_ref:.3f}  RMSE_held={rmse_ref:.2f}")

    for lb in lambdas:
        for kh in k_hots:
            cfg = _cfg_noeud(k_hot=kh)
            f = restaurer_facteur(fit, cfg, lb)
            rmse_h = rmse_pooled(held, cfg, f, lb)
            rmse_f = rmse_pooled(fit, cfg, f, lb)
            c, _ = contraste_ktlb(f, kh, lb)
            cls = classer(c, rmse_h, rmse_ref)
            lignes.append(dict(lambda_bord_mm=lb, k_hot=kh, facteur=f,
                               contraste_M=c, rmse_holdout=rmse_h, rmse_fit=rmse_f,
                               classe=cls))
            print(f"  λ={lb:>3} k_hot={kh:>3} | facteur={f:6.3f} "
                  f"contraste={c:5.3f} RMSE_held={rmse_h:6.2f} -> {cls}")
    return pd.DataFrame(lignes)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lambdas", type=float, nargs="+", default=LAMBDAS)
    ap.add_argument("--k-hots", type=float, nargs="+", default=K_HOTS)
    ap.add_argument("--csv", default=str(RACINE / "journaux" /
                    "resultats_pareto_source_conduction_2026-08-12.csv"))
    ap.add_argument("--png", default=str(RACINE / "docs" / "modele" / "figures" /
                    "pareto_source_conduction.png"))
    args = ap.parse_args()

    df = balayer(args.lambdas, args.k_hots)
    Path(args.csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.csv, index=False)

    noeuds = df[df["classe"] != "reference"]
    v = verdict(noeuds["classe"].tolist())
    tracer_pareto(df, args.png)  # défini en Task 5
    print(f"\n=== VERDICT : {v} ===")
    print(f"faisables={int((noeuds['classe']=='faisable').sum())} "
          f"quasi={int((noeuds['classe']=='quasi').sum())} "
          f"hors={int((noeuds['classe']=='hors').sum())}")
    print(f"CSV : {args.csv}\nPNG : {args.png}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Fumée sur une sous-grille (rapide)**

Run: `python code/scripts/diag/diag_pareto_source_conduction.py --lambdas 0 6 --k-hots 3 --png /tmp/pareto_smoke.png --csv /tmp/pareto_smoke.csv 2>&1 | tail -15`
Expected: le script tourne, imprime `[REF] ...`, 2 nœuds, un `=== VERDICT : ... ===`, et écrit le CSV. (`tracer_pareto` n'existe pas encore → cette étape échouera à l'appel figure ; c'est attendu, elle valide seulement le balayage. Commenter l'appel `tracer_pareto` temporairement OU enchaîner directement sur Task 5 avant de lancer le run complet.)

- [ ] **Step 3: Commit**

```bash
git add code/scripts/diag/diag_pareto_source_conduction.py
git commit -m "feat(pareto): balayage grille + CSV + main (verdict)"
```

---

### Task 5: Figure Pareto (PNG) + relecture visuelle

**Files:**
- Modify: `code/scripts/diag/diag_pareto_source_conduction.py`

**Interfaces:**
- Consumes: `pandas.DataFrame` de `balayer` ; `apply_style`, `savefig` de `code/scripts/_style.py`.
- Produces: `tracer_pareto(df: pandas.DataFrame, png_path: str) -> None`.

- [ ] **Step 1: Écrire la fonction figure**

```python
# append near the top imports of code/scripts/diag/diag_pareto_source_conduction.py
import matplotlib.pyplot as plt
from _style import apply_style, savefig

# append to code/scripts/diag/diag_pareto_source_conduction.py
def tracer_pareto(df, png_path):
    """Nuage contraste_M (x) vs rmse_holdout (y). Couleur=lambda_bord,
    taille=k_hot. Boîte de faisabilité + point de référence tracés."""
    apply_style(**{"font.size": 10, "axes.labelsize": 11})
    ref = df[df["classe"] == "reference"].iloc[0]
    noeuds = df[df["classe"] != "reference"]
    rmse_ref = float(ref["rmse_holdout"])

    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    # boîte de faisabilité : |contraste-2.08|<=0.15 ET rmse<=rmse_ref
    ax.axvspan(2.08 - 0.15, 2.08 + 0.15, color="#009E73", alpha=0.10, zorder=0)
    ax.axhline(rmse_ref, color="#009E73", lw=1.0, ls="--",
               label=f"RMSE réf = {rmse_ref:.1f} °C")
    ax.axhline(rmse_ref + 0.7, color="#E69F00", lw=0.9, ls=":",
               label="seuil quasi (réf + 0,7)")
    sc = ax.scatter(noeuds["contraste_M"], noeuds["rmse_holdout"],
                    c=noeuds["lambda_bord_mm"], s=20 + 14 * noeuds["k_hot"],
                    cmap="viridis", edgecolor="0.2", linewidth=0.4, zorder=5)
    ax.scatter([ref["contraste_M"]], [ref["rmse_holdout"]], marker="*",
               s=240, color="#C1272D", edgecolor="black", zorder=6,
               label="référence isotrope (k=3, λ=0)")
    ax.axvline(2.08, color="0.4", lw=0.8, zorder=1)
    ax.annotate("contraste mesuré 2,08", xy=(2.08, ax.get_ylim()[1]),
                fontsize=8, color="0.4", ha="left", va="top", rotation=90)
    fig.colorbar(sc, ax=ax, label="lambda_bord (mm)")
    ax.set_xlabel("contraste M (exp7 200 A)  —  cible mesurée 2,08")
    ax.set_ylabel("RMSE held-out (°C)  —  exp7_250A + exp9 bord")
    ax.set_title("Faisabilité source × conduction (taille ∝ k_hot)", fontsize=11)
    ax.legend(fontsize=8, loc="best", framealpha=0.9)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    Path(png_path).parent.mkdir(parents=True, exist_ok=True)
    savefig(fig, png_path)
    plt.close(fig)
```

- [ ] **Step 2: Run complet de la grille**

Run: `python code/scripts/diag/diag_pareto_source_conduction.py 2>&1 | tail -40`
Expected: 30 nœuds + REF imprimés, CSV + PNG écrits, `=== VERDICT : GO|QUASI-GO|NO-GO ===`. Durée ~10-25 min (≈27 sims/nœud × 30 nœuds). Vérifier `git status` : seuls le script, le CSV et le PNG changent (aucune config touchée).

- [ ] **Step 3: Sanity de reproduction**

Ouvrir le CSV : la ligne `reference` doit donner `contraste_M ≈ 3.0-3.25` (reproduit ~3.13) — sinon le pipeline diverge d'un run antérieur, corriger avant d'interpréter. Vérifier qu'un nœud `lambda_bord≈4-6` abaisse bien `contraste_M` vers ~2,1.

- [ ] **Step 4: Relecture visuelle (figure-review-loop)**

Ouvrir `biblio/modele/figures/pareto_source_conduction.png` et le **regarder** à l'échelle cible : boîte de faisabilité et étoile de référence visibles, colorbar lisible, aucun chevauchement légende/points. Corriger un défaut à la fois puis re-rendre si besoin.

- [ ] **Step 5: Commit**

```bash
git add code/scripts/diag/diag_pareto_source_conduction.py \
        donnees/journaux/resultats_pareto_source_conduction_2026-08-12.csv \
        biblio/modele/figures/pareto_source_conduction.png
git commit -m "feat(pareto): figure Pareto + run complet (verdict GO/NO-GO)"
```

---

### Task 6: Décision C→A + traçabilité

**Files:**
- Modify: `biblio/modele/README.md` (section résidu) — 2-4 lignes selon le verdict.

**Interfaces:** aucune (documentation).

- [ ] **Step 1: Consigner le verdict**

Selon le verdict imprimé :
- **GO / QUASI-GO** : ajouter au README §résidu une ligne « combinaison source (`lambda_bord`) × conduction (`k(T)`) : région (quasi-)faisable identifiée (carte 2D, `pareto_source_conduction.png`) → étape A (fit joint 6 paramètres) à lancer », puis rédiger la spec de l'étape A (hors de ce plan).
- **NO-GO** : ajouter « combinaison source × conduction testée en 2D (carte `pareto_source_conduction.png`) : aucune région faisable → fermeture confirmée à deux ingrédients », et signaler que la note mémoire `residu-unifie-etalement-in-plane` doit être corrigée (la combinaison n'est plus « non testée »).

- [ ] **Step 2: Commit**

```bash
git add biblio/modele/README.md
git commit -m "docs(pareto): verdict carte source×conduction consigné (§résidu)"
```

---

## Self-Review

**Spec coverage :**
- But C (go/no-go faisabilité) → Tasks 3-5 (classer/verdict/balayer/figure). ✓
- Grille imposée + k_cold figé → Global Constraints + Task 4 (`LAMBDAS`/`K_HOTS`, `_cfg_noeud`). ✓
- Restauration d'amplitude 1-D → Task 2 (`restaurer_facteur`). ✓
- Lots ajustement/held-out/contraste → Global Constraints + `FIT`/`HELDOUT`/`CONTRASTE_ESSAI` (Task 1-2). ✓
- Critère + clause quasi-faisabilité → Task 3 (`classer`), rendu **relatif à RMSE_REF** (raffinement documenté vs le seuil absolu 16,5 de la spec). ✓
- Sorties CSV + PNG + verdict → Tasks 4-5. ✓
- Diagnostic lecture seule → Global Constraints ; vérifié via `git status` (Task 5 Step 2). ✓
- Sanity reproduction (~3.13 ; lambda_bord abaisse le contraste) → Task 1 tests + Task 5 Step 3. ✓
- Décision aval GO/NO-GO → Task 6. ✓

**Placeholder scan :** aucun TBD/TODO ; tout le code des helpers et des tests est explicite. ✓

**Type consistency :** `contraste_ktlb`, `restaurer_facteur`, `rmse_pooled`, `charger_essais`, `_cfg_noeud`, `classer`, `verdict`, `balayer`, `tracer_pareto` — noms/signatures identiques entre définition et appels (Task 4 `balayer` consomme exactement ces signatures ; `main` appelle `tracer_pareto(df, png)` défini en Task 5). Colonnes DataFrame (`classe`, `contraste_M`, `rmse_holdout`, `lambda_bord_mm`, `k_hot`) cohérentes entre `balayer`, `main`, `tracer_pareto`. ✓

**Note d'ordonnancement :** `main` (Task 4) référence `tracer_pareto` (Task 5) ; le run complet n'est possible qu'après Task 5. La fumée de Task 4 Step 2 le signale explicitement.
