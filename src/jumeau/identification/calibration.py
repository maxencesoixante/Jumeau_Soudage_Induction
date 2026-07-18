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

Note (post-mortem calibration bloquée) : chaque évaluation de résidu est une
simulation 3D complète (~1-3 min sur la grille grossière par défaut). La phase
NLSQ ne produisait auparavant AUCUNE sortie avant son tout dernier message,
ce qui, combiné à ``max_nfev=60`` (jusqu'à 1-2 h sans un seul print), donnait
l'impression d'un plantage alors que le calcul progressait normalement. Une
simulation qui diverge réellement (bord de l'espace des paramètres,
``solve_ivp`` en échec, température non finie) levait en outre une exception
non rattrapée dans ``_residus`` pendant le NLSQ (seule la boucle LHS
l'attrapait) : `least_squares` plante alors sans message exploitable. Les deux
défauts sont corrigés ci-dessous : progression affichée par évaluation NLSQ, et
un point divergent est désormais pénalisé par un résidu fini plutôt que de
propager une exception.
"""

from __future__ import annotations

import time
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
    message: str = ""
    nfev: int = 0
    erreurs_std: dict | None = None          # écart-type par paramètre (même unités)
    correlation: np.ndarray | None = None    # matrice de corrélation (ordre = Calibrateur.NOMS)


class Calibrateur:
    """Calibre [facteur_couplage, h_contact, h_bas] contre un essai mesuré."""

    NOMS = ("facteur_couplage", "h_contact", "h_bas")

    # Pénalité (en unités de résidu pondéré, sans dimension) appliquée à un point
    # dont la simulation diverge ou échoue. Choisie nettement au-dessus du pire
    # coût observé sur un point LHS raisonnable (~1.5-9e6 / ~900 résidus, soit un
    # résidu quadratique moyen de l'ordre de quelques milliers -> résidu ~qq 10aines)
    # pour que le point soit clairement rejeté par le solveur, sans être assez
    # extrême pour dérégler l'échelle de confiance interne de `least_squares`.
    PENALITE_RESIDU = 100.0

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

        # taille fixe du vecteur de résidus (nécessaire pour pénaliser un point
        # divergent par un vecteur de même forme plutôt que de laisser
        # `least_squares` recevoir une exception ou une taille incohérente)
        self._taille_residu = len(self.tc_valides) * len(self.t_mes)

    # ------------------------------------------------------------------
    def _residus(self, theta: np.ndarray) -> np.ndarray:
        facteur, h_contact, h_bas = theta
        try:
            self.cfg.contact.h_contact = float(h_contact)
            self.cfg.ambiant.h_bas = float(h_bas)

            essai = self.essai
            source = lambda t, T: facteur * essai.source_fn(t, T)   # échelle sans recalcul EM

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
            res = np.concatenate(res)
        except Exception:
            # Point hors du domaine de validité numérique (solve_ivp en échec,
            # pas de temps requis -> 0, etc.) : on NE PROPAGE PAS l'exception —
            # `least_squares` n'a pas de mécanisme pour la rattraper et
            # s'arrêterait net sans résultat exploitable (c'est la cause du
            # blocage silencieux observé). On renvoie à la place un résidu fini,
            # de la bonne taille, clairement pénalisant.
            return np.full(self._taille_residu, self.PENALITE_RESIDU)

        if not np.all(np.isfinite(res)):
            # Températures non finies (NaN/inf) obtenues malgré un solve_ivp
            # "réussi" (ex. extrapolation hors grille) : même traitement.
            res = np.where(np.isfinite(res), res, self.PENALITE_RESIDU)
        return res

    # ------------------------------------------------------------------
    def calibrer(self, n_lhs: int = 12, seed: int = 0, verbose: bool = True,
                 max_nfev: int = 60) -> ResultatCalibration:
        lo, hi = self.bornes
        pts = qmc.scale(qmc.LatinHypercube(d=len(lo), seed=seed).random(n=n_lhs), lo, hi)

        historique, meilleur, cout_min = [], None, np.inf
        for i, p in enumerate(pts):
            try:
                cout = float(np.sum(self._residus(p) ** 2))
            except Exception as e:              # garde-fou (ne devrait plus se produire)
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

        # --- NLSQ : chaque évaluation (résidu de base + différences finies du
        # jacobien + essais de pas) est une simulation 3D complète. Sans retour
        # visuel, l'absence de sortie pendant potentiellement 1-2h est
        # indiscernable d'un plantage : on affiche donc la progression.
        nfev = [0]
        residus_de_base = self._residus

        def residus_suivis(theta):
            nfev[0] += 1
            t0 = time.monotonic()
            r = residus_de_base(theta)
            if verbose:
                dt = time.monotonic() - t0
                print(f"  NLSQ éval {nfev[0]} : θ={np.round(theta, 4).tolist()} "
                      f"coût={float(np.sum(r ** 2)):.1f} ({dt:.1f}s)")
            return r

        if verbose:
            print(f"NLSQ : démarrage à θ0={np.round(meilleur, 3).tolist()} "
                  f"(coût LHS={cout_min:.1f}) — {max_nfev} évaluations max, "
                  f"chaque simulation ~1-3 min.")

        res = least_squares(residus_suivis, meilleur, bounds=self.bornes,
                            xtol=1e-4, ftol=1e-4, diff_step=0.05, max_nfev=max_nfev)
        params = dict(zip(self.NOMS, res.x))

        erreurs_std, correlation = self._incertitudes(res)

        if verbose:
            print(f"NLSQ terminé après {nfev[0]} évaluations : succès={res.success} "
                  f"— {res.message}")
            print(f"  paramètres = {params}")
            print(f"  coût = {2 * res.cost:.1f}")
            if erreurs_std is not None:
                print(f"  écarts-types = { {n: round(erreurs_std[n], 4) for n in self.NOMS} }")
                print(f"  corrélations =\n{np.round(correlation, 3)}")

        return ResultatCalibration(
            parametres=params,
            cout=float(2 * res.cost),
            succes=bool(res.success),
            historique_lhs=historique,
            message=str(res.message),
            nfev=int(nfev[0]),
            erreurs_std=erreurs_std,
            correlation=correlation,
        )

    # ------------------------------------------------------------------
    def _incertitudes(self, res):
        """Écarts-types et corrélations paramétriques depuis le jacobien NLSQ.

        cov = s² · (JᵀJ)⁻¹ avec s² = 2·coût / ddl (résidus déjà pondérés par σ,
        donc J est le jacobien du résidu réduit). Une corrélation |r| -> 1 entre
        deux paramètres calibrés est un signal de non-identifiabilité à
        signaler, pas à masquer.
        """
        J = res.jac
        n_res, n_par = J.shape
        ddl = max(n_res - n_par, 1)
        s2 = 2.0 * res.cost / ddl
        try:
            cov = s2 * np.linalg.inv(J.T @ J)
        except np.linalg.LinAlgError:
            cov = s2 * np.linalg.pinv(J.T @ J)
        se = np.sqrt(np.clip(np.diag(cov), 0.0, None))
        with np.errstate(invalid="ignore", divide="ignore"):
            corr = cov / np.outer(se, se)
        erreurs_std = dict(zip(self.NOMS, se.tolist()))
        return erreurs_std, corr
