"""Calibration LHS + NLSQ des entrées incertaines du modèle 3D.

Pipeline porté du notebook 1D (MAX_InductionNumerical) et de sa vérification
black-box (Samanis et al. 2026 §2.3) :
1. LHS (Latin Hypercube) sur l'espace des paramètres -> meilleur point de départ ;
2. NLSQ (Gauss-Newton, scipy.least_squares) avec résidus pondérés par le
   bruit capteur σ = std(diff(mesure))/√2 (plancher 0,1 °C).

Paramètres calibrés (defaut) — choisis pour rester identifiables (leçon
black-box : ne PAS calibrer fréquence + facteur d'échelle ensemble) :
- ``facteur_couplage``  : échelle de la source Joule (blindage, contacts, σ, f) ;
- ``h_contact``         : conductance vers le puits céramique/concentrateur ;
- ``h_bas``             : convection équivalente face inférieure.

La calibration se fait sur UN essai (ex. chauffe_250A_3TC) ; la validation
sur les autres essais se fait SANS recalibrage (scripts/valider.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import least_squares
from scipy.stats import qmc

from ..materiaux import Config
from ..procede import Essai
from ..validation.chargement import charger_mesures, recaler_a_la_chauffe


@dataclass
class ResultatCalibration:
    parametres: dict
    cout: float
    succes: bool
    historique_lhs: list = field(default_factory=list)


class Calibrateur:
    """Calibre [facteur_couplage, h_contact, h_bas] contre un essai mesuré."""

    NOMS = ("facteur_couplage", "h_contact", "h_bas")

    def __init__(self, cfg: Config, chemin_essai, bornes_basses=(0.05, 5.0, 2.0),
                 bornes_hautes=(30.0, 500.0, 300.0), nx=31, ny=11, nz=13,
                 recaler_debut=True):
        self.cfg = cfg
        self.bornes = (np.array(bornes_basses, float), np.array(bornes_hautes, float))
        # grille grossière pour la calibration (chaque évaluation = 1 simulation 3D)
        self.essai = Essai(cfg, chemin_essai, nx=nx, ny=ny, nz=nz, facteur_couplage=1.0)

        df = charger_mesures(self.essai.fichier_mesures)
        if recaler_debut:
            df = recaler_a_la_chauffe(df)
        duree = float(self.essai.spec.get("duree_totale", self.essai.spec["duree_chauffe"]))
        tcol = df.columns[0]
        df = df[df[tcol] <= duree].reset_index(drop=True)
        self.df = df
        self.t_mes = df[tcol].values

        self.tc_valides = list(self.essai.spec.get("tc_valides", []))
        self.colonnes = {tc: next(c for c in df.columns if c.startswith(tc))
                         for tc in self.tc_valides}
        # pondération par bruit capteur (notebook 1D)
        self.sigmas = {}
        for tc, col in self.colonnes.items():
            bruit = np.std(np.diff(df[col].values)) / np.sqrt(2.0)
            self.sigmas[tc] = max(float(bruit), 0.1)

    # ------------------------------------------------------------------
    def _residus(self, theta: np.ndarray) -> np.ndarray:
        facteur, h_contact, h_bas = theta
        self.cfg.contact.h_contact = float(h_contact)
        self.cfg.ambiant.h_bas = float(h_bas)

        essai = self.essai
        source = lambda t: facteur * essai.source_fn(t)   # échelle sans recalcul EM

        from ..thermique.solveur3d import SolveurThermique3D
        solveur = SolveurThermique3D(essai.grille, self.cfg.materiau,
                                     self.cfg.ambiant, self.cfg.contact,
                                     masque_ceramique=essai.masque_fn)
        duree = float(essai.spec.get("duree_totale", essai.spec["duree_chauffe"]))
        t_eval = np.arange(0.0, duree + 0.5, 1.0)
        sol = solveur.simuler(source, (0.0, duree), t_eval=t_eval)
        series = essai.series_tc(solveur, sol)

        res = []
        for tc in self.tc_valides:
            T_sim = np.interp(self.t_mes, sol.t, series[tc])
            T_mes = self.df[self.colonnes[tc]].values
            res.append((T_sim - T_mes) / self.sigmas[tc])
        return np.concatenate(res)

    # ------------------------------------------------------------------
    def calibrer(self, n_lhs: int = 12, seed: int = 0, verbose: bool = True) -> ResultatCalibration:
        lo, hi = self.bornes
        pts = qmc.scale(qmc.LatinHypercube(d=len(lo), seed=seed).random(n=n_lhs), lo, hi)

        historique, meilleur, cout_min = [], None, np.inf
        for i, p in enumerate(pts):
            try:
                cout = float(np.sum(self._residus(p) ** 2))
            except Exception as e:              # simulation divergente : point écarté
                if verbose:
                    print(f"  LHS {i + 1}/{n_lhs} : échec ({e})")
                continue
            historique.append((p.tolist(), cout))
            if cout < cout_min:
                cout_min, meilleur = cout, p
            if verbose:
                print(f"  LHS {i + 1}/{n_lhs} : θ={np.round(p, 3).tolist()} coût={cout:.1f}")

        if meilleur is None:
            raise RuntimeError("Aucun point LHS n'a produit une simulation valide.")

        res = least_squares(self._residus, meilleur, bounds=self.bornes,
                            xtol=1e-4, ftol=1e-4, diff_step=0.05, max_nfev=60)
        params = dict(zip(self.NOMS, res.x))
        if verbose:
            print(f"NLSQ terminé : {params} (coût {2 * res.cost:.1f})")
        return ResultatCalibration(params, float(2 * res.cost), bool(res.success), historique)
