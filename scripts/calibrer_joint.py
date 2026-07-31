#!/usr/bin/env python
"""Calibration JOINTE multi-familles (modèle 2D) — bord/profil « M » + centre/conduction.

Contexte (cf. docs/modele/README.md §État & résidu ouvert, 2026-07-30) : au θ*
de référence 2D canonique (config/materiaux.yaml), le modèle SUR-chauffe le
point chaud (chant exp7 +50/+56 °C, spot-centre exp9 y=20 TC3 +30 °C) ET
SOUS-étale en longueur (exp9 y=20 extrémités TC1/TC5 -11 °C). Le balayage
k_plan (diagnostic préalable) montre que monter k_plan remonte les
extrémités mais NE corrige PAS le pic : l'amplitude de source et la
conduction dans le plan sont deux leviers DIFFÉRENTS, chacun mal contraint
par une seule famille d'essais. -> calibration JOINTE sur les deux familles
à la fois pour rendre k_plan identifiable :

- famille BORD / profil M (spot centré, 5 TC en largeur) : exp7_150A,
  exp7_200A, exp7_250A -- contraint facteur_couplage, le contraste, h_bord_x0 ;
- famille CENTRE / conduction (spot isolé, 5 TC en longueur AU CENTRE de
  largeur y=0.020, dans le creux du profil M) : exp9_200A_y20_monospot --
  contraint k_plan (la variation de température y est dominée par la
  conduction longitudinale, pas par la source).

IDENTIFIABILITÉ -- ce script NE calibre PAS facteur_couplage et une fréquence
(déjà mesurée constante, cf. mémoire 2026-07-28 : f=388±2kHz, hypothèse f(I)
réfutée) : le piège historique f/échelle ne s'applique pas ici. En revanche
h_haut EST figé (non-identifiable, corr 0,98 avec h_bas_2d, cf. phase 2 de la
consolidation) -- 4 paramètres LIBRES seulement :
    theta = [facteur_couplage, h_bas_2d, k_plan, h_bord_x0]
(+ option --source-sigma-mm : calibre un 5e paramètre source_sigma_mm si
passé avec --calibrer-sigma, sinon figé à la valeur donnée, défaut 0).

Résidu : concaténation, sur TOUS les essais de la liste, des résidus par TC
pondérés par le bruit capteur σ = std(diff(mesure))/√2 (plancher 0,1 °C) --
même pondération que jumeau.identification.calibration.Calibrateur, mais
empilée sur plusieurs essais au lieu d'un seul. facteur_couplage,
h_bas_2d, k_plan, h_bord_x0 sont des grandeurs UNIQUES partagées par tous les
essais de la liste (un seul θ pour tout le lot, pas un θ par essai) ; k_plan
est appliqué via cfg.materiau.k_plan AVANT chaque simulation (le solveur 2D
le lit directement, cf. thermique/solveur2d.py).

Coût : chaque évaluation de résidu = 1 simulation 2D par essai de la liste
(grille de calibration volontairement grossière, cf. --nx/--ny/--nz, défaut
31x11x13 -- identique à jumeau.identification.calibration.Calibrateur). Sur
cette machine, une simulation 2D coarse-grid dure <1 s (mesuré) -> un budget
n_lhs=12 + max_nfev=60 sur 4 essais reste de l'ordre de quelques minutes.

Usage :
    python scripts/calibrer_joint.py \\
        --essais exp7_200A exp7_150A exp7_250A exp9_200A_y20_monospot \\
        --n-lhs 12 --max-nfev 60

    # avec source_sigma_mm calibré en plus (5e paramètre) :
    python scripts/calibrer_joint.py --calibrer-sigma --n-lhs 12 --max-nfev 60

Sortie : θ*_new joint (avec écarts-types + corrélations si le NLSQ réussit),
plus un tableau RMSE/ΔT_max par essai/TC comparant θ* de référence vs
θ*_new joint (sur la liste --essais ET, si fournie, --essais-holdout).
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares
from scipy.stats import qmc

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from jumeau.materiaux import Config
from jumeau.procede import Essai
from jumeau.validation.chargement import charger_mesures, recaler_a_la_chauffe
from jumeau.validation.confrontation import rapport_essai

# theta (isotrope, historique) = [facteur_couplage, h_bas_2d, k_plan, h_bord_x0, (source_sigma_mm)]
NOMS_BASE = ("facteur_couplage", "h_bas_2d", "k_plan", "h_bord_x0")
BORNES_BASSES_BASE = (0.5, 2.0, 2.0, 50.0)   # k_plan/h_bord_x0 bornés par la mission (~[2,12], ~[50,400])
BORNES_HAUTES_BASE = (30.0, 300.0, 12.0, 400.0)

# theta (ANISOTROPE, --anisotrope, prototype 2026-07-31) = [facteur_couplage,
# h_bas_2d, kx, ky, h_bord_x0, (source_sigma_mm)] -- kx/ky remplacent k_plan
# scalaire (materiaux.Materiau.k_plan_x/k_plan_y, cf. thermique/solveur2d.py).
NOMS_BASE_ANISO = ("facteur_couplage", "h_bas_2d", "kx", "ky", "h_bord_x0")
BORNES_BASSES_ANISO = (0.5, 2.0, 2.0, 2.0, 50.0)   # kx,ky bornés ~[2,12] W/m.K (mission)
BORNES_HAUTES_ANISO = (30.0, 300.0, 12.0, 12.0, 400.0)

H_HAUT_FIGE = 30.087  # figé (non-identifiable, corr 0.98 avec h_bas_2d -- phase 2 consolidation)

PENALITE_RESIDU = 100.0


class EssaiCalibre:
    """Un essai préchargé (mesures, TC valides, sigma) pour la liste jointe."""

    def __init__(self, nom: str, nx: int, ny: int, nz: int):
        self.nom = nom
        self.chemin = RACINE / "config" / "essais" / f"{nom}.yaml"
        # sonde une première fois (facteur_couplage=1.0, non utilisé pour les
        # résidus) uniquement pour récupérer spec/racine/mesures.
        essai0 = Essai(Config.charger(RACINE / "config"), self.chemin, nx=nx, ny=ny, nz=nz,
                       facteur_couplage=1.0, racine=RACINE)
        self.racine = essai0.racine
        self.nx, self.ny, self.nz = nx, ny, nz

        df = charger_mesures(essai0.fichier_mesures)
        df = recaler_a_la_chauffe(df)
        duree = float(essai0.spec.get("duree_totale", essai0.spec["duree_chauffe"]))
        tcol = df.columns[0]
        df = df[df[tcol] <= duree].reset_index(drop=True)
        self.df = df
        self.t_mes = df[tcol].values

        tc_valides = list(essai0.spec.get("tc_valides", []))
        positions = essai0.spec.get("thermocouples", {})
        exclus = [tc for tc in tc_valides if positions.get(tc, {}).get("z") != "interface"]
        if exclus:
            print(f"[{nom}] TC exclus (non 'interface', non représentables en 2D) : {exclus}")
        self.tc_valides = [tc for tc in tc_valides if tc not in exclus]
        if not self.tc_valides:
            raise ValueError(f"{nom} : aucun TC exploitable en 2D.")

        self.colonnes = {tc: next(c for c in df.columns if c.startswith(tc)) for tc in self.tc_valides}
        self.sigmas = {}
        for tc, col in self.colonnes.items():
            bruit = np.std(np.diff(df[col].values)) / np.sqrt(2.0)
            self.sigmas[tc] = max(float(bruit), 0.1)
        self.taille_residu = len(self.tc_valides) * len(self.t_mes)

    def simuler(self, cfg: Config, facteur_couplage: float, source_sigma_mm: float,
               lambda_bord_mm: float = 0.0):
        essai = Essai(cfg, self.chemin, nx=self.nx, ny=self.ny, nz=self.nz,
                      facteur_couplage=facteur_couplage, decalage_x=0.0,
                      racine=self.racine, source_sigma_mm=source_sigma_mm,
                      lambda_bord_mm=lambda_bord_mm)
        solveur, sol = essai.simuler(modele="2D")
        series = essai.series_tc(solveur, sol)
        return essai, solveur, sol, series

    def residus(self, cfg: Config, facteur_couplage: float, source_sigma_mm: float,
               lambda_bord_mm: float = 0.0) -> np.ndarray:
        try:
            _, _, sol, series = self.simuler(cfg, facteur_couplage, source_sigma_mm, lambda_bord_mm)
            res = []
            for tc in self.tc_valides:
                T_sim = np.interp(self.t_mes, sol.t, series[tc])
                T_mes = self.df[self.colonnes[tc]].values
                res.append((T_sim - T_mes) / self.sigmas[tc])
            res = np.concatenate(res)
        except Exception as e:
            print(f"  [{self.nom}] divergence/échec ({e!r}) -> pénalité")
            return np.full(self.taille_residu, PENALITE_RESIDU)
        if not np.all(np.isfinite(res)):
            res = np.where(np.isfinite(res), res, PENALITE_RESIDU)
        return res

    def rapport(self, cfg: Config, facteur_couplage: float, source_sigma_mm: float,
               lambda_bord_mm: float = 0.0) -> pd.DataFrame:
        _, _, sol, series = self.simuler(cfg, facteur_couplage, source_sigma_mm, lambda_bord_mm)
        return rapport_essai(series, sol.t, self.df, self.tc_valides)


class CalibrateurJoint:
    def __init__(self, essais: list[EssaiCalibre], calibrer_sigma: bool = False,
                 source_sigma_mm_fige: float = 0.0,
                 lambda_bord_mm_fige: float = 0.0,
                 anisotrope: bool = False,
                 bornes_basses=None, bornes_hautes=None):
        self.essais = essais
        self.calibrer_sigma = calibrer_sigma
        self.source_sigma_mm_fige = float(source_sigma_mm_fige)
        # lambda_bord_mm (adoucissement du bord, cf. jumeau.em.source_joule) :
        # FIGÉ ici (pas un paramètre libre du fit), comme source_sigma_mm par
        # défaut -- diagnostic/prototype (mission EM 2026-07-30), pas encore
        # un axe de calibration à part entière (2 leviers de forme couplés
        # rendraient le fit sous-déterminé sans plus de données de forme).
        self.lambda_bord_mm_fige = float(lambda_bord_mm_fige)
        # anisotrope (prototype 2026-07-31, mission thermal-solver-engineer) :
        # remplace le k_plan SCALAIRE par (kx, ky) -- cf. NOMS_BASE_ANISO.
        self.anisotrope = bool(anisotrope)
        noms_base = NOMS_BASE_ANISO if self.anisotrope else NOMS_BASE
        bornes_basses_defaut = BORNES_BASSES_ANISO if self.anisotrope else BORNES_BASSES_BASE
        bornes_hautes_defaut = BORNES_HAUTES_ANISO if self.anisotrope else BORNES_HAUTES_BASE
        if calibrer_sigma:
            self.noms = noms_base + ("source_sigma_mm",)
            lo = list(bornes_basses or bornes_basses_defaut) + [0.0]
            hi = list(bornes_hautes or bornes_hautes_defaut) + [3.0]
        else:
            self.noms = noms_base
            lo = list(bornes_basses or bornes_basses_defaut)
            hi = list(bornes_hautes or bornes_hautes_defaut)
        self.bornes = (np.array(lo, float), np.array(hi, float))
        self.cfg = Config.charger(RACINE / "config")
        self.cfg.contact.h_haut = H_HAUT_FIGE
        self._taille_totale = sum(e.taille_residu for e in self.essais)

    def _appliquer(self, theta):
        if self.anisotrope:
            facteur, h_bas_2d, kx, ky, h_bord_x0 = theta[:5]
            sigma_mm = theta[5] if self.calibrer_sigma else self.source_sigma_mm_fige
            self.cfg.ambiant.h_bas_2d = float(h_bas_2d)
            self.cfg.materiau.k_plan_x = float(kx)
            self.cfg.materiau.k_plan_y = float(ky)
            self.cfg.ambiant.h_bord_x0 = float(h_bord_x0)
        else:
            facteur, h_bas_2d, k_plan, h_bord_x0 = theta[:4]
            sigma_mm = theta[4] if self.calibrer_sigma else self.source_sigma_mm_fige
            self.cfg.ambiant.h_bas_2d = float(h_bas_2d)
            self.cfg.materiau.k_plan = float(k_plan)
            self.cfg.ambiant.h_bord_x0 = float(h_bord_x0)
        return float(facteur), float(sigma_mm)

    def residus(self, theta) -> np.ndarray:
        facteur, sigma_mm = self._appliquer(theta)
        morceaux = [e.residus(self.cfg, facteur, sigma_mm, self.lambda_bord_mm_fige)
                   for e in self.essais]
        return np.concatenate(morceaux)

    def calibrer(self, n_lhs=12, seed=0, max_nfev=60, verbose=True, figer: dict | None = None):
        """``figer`` : dict optionnel {nom: valeur} de paramètres à FIGER (non
        calibrés) -- ex. tester si h_bas_2d doit vraiment être libre dans le
        fit joint (diagnostic de sensibilité/famille, cf. rapport)."""
        figer = dict(figer or {})
        for nom in figer:
            if nom not in self.noms:
                raise ValueError(f"paramètre inconnu à figer : {nom!r} (attendu parmi {self.noms})")
        idx_libres = [i for i, n in enumerate(self.noms) if n not in figer]
        noms_libres = tuple(self.noms[i] for i in idx_libres)
        idx_figes = [i for i, n in enumerate(self.noms) if n in figer]

        lo_complet, hi_complet = self.bornes
        theta_fige_complet = np.zeros(len(self.noms))
        for i in idx_figes:
            theta_fige_complet[i] = figer[self.noms[i]]

        def theta_complet(theta_libre):
            t = theta_fige_complet.copy()
            for k, i in enumerate(idx_libres):
                t[i] = theta_libre[k]
            return t

        def residus_libres(theta_libre):
            return self.residus(theta_complet(theta_libre))

        lo = lo_complet[idx_libres]
        hi = hi_complet[idx_libres]

        if verbose and figer:
            print(f"Paramètres figés (non calibrés) : {figer} -- calibration réduite à {noms_libres}.")

        pts = qmc.scale(qmc.LatinHypercube(d=len(lo), seed=seed).random(n=n_lhs), lo, hi)
        historique = []
        meilleur, cout_min = None, np.inf
        for i, p in enumerate(pts):
            t0 = time.monotonic()
            r = residus_libres(p)
            cout = float(np.sum(r ** 2))
            dt = time.monotonic() - t0
            historique.append((p.tolist(), cout))
            if cout < cout_min:
                cout_min, meilleur = cout, p
            if verbose:
                print(f"  LHS {i+1}/{n_lhs} : θ={np.round(p, 4).tolist()} ({noms_libres}) "
                      f"coût={cout:.1f} ({dt:.1f}s)")

        nfev = [0]

        def residus_suivis(theta_libre):
            nfev[0] += 1
            t0 = time.monotonic()
            r = residus_libres(theta_libre)
            if verbose:
                dt = time.monotonic() - t0
                print(f"  NLSQ éval {nfev[0]} : θ={np.round(theta_libre, 5).tolist()} "
                      f"({noms_libres}) coût={float(np.sum(r**2)):.1f} ({dt:.1f}s)")
            return r

        if verbose:
            print(f"NLSQ joint : démarrage à θ0={np.round(meilleur, 4).tolist()} "
                  f"(coût LHS={cout_min:.1f}) — {max_nfev} évaluations max, "
                  f"{len(self.essais)} essais, {self._taille_totale} résidus.")

        res = least_squares(residus_suivis, meilleur, bounds=(lo, hi),
                            xtol=1e-4, ftol=1e-4, diff_step=0.05, max_nfev=max_nfev)

        # incertitudes : covariance = (J^T W J)^-1 avec W=I (résidus déjà
        # normalisés par sigma) -- identique à jumeau.identification.calibration.
        # Uniquement pour les paramètres LIBRES (les figés n'ont pas de SE).
        erreurs_std, correlation = {}, None
        try:
            J = res.jac
            JTJ = J.T @ J
            dof = max(len(res.fun) - len(meilleur), 1)
            s_sq = float(np.sum(res.fun ** 2)) / dof
            cov = np.linalg.inv(JTJ) * s_sq
            sd = np.sqrt(np.diag(cov))
            correlation = cov / np.outer(sd, sd)
            for i, nom in enumerate(noms_libres):
                erreurs_std[nom] = float(sd[i])
        except np.linalg.LinAlgError:
            print("  ATTENTION : JTJ singulière -- covariance non calculable (paramètre non identifiable).")

        theta_final = theta_complet(res.x)
        return {
            "theta": theta_final, "cout": float(np.sum(res.fun ** 2)), "succes": bool(res.success),
            "message": res.message, "nfev": nfev[0], "historique_lhs": historique,
            "erreurs_std": erreurs_std, "correlation": correlation, "noms_libres": noms_libres,
            "figer": figer,
        }


def table_comparaison(essais: list[EssaiCalibre], cfg_ref: Config, facteur_ref: float,
                      cfg_new: Config, facteur_new: float, sigma_new: float = 0.0,
                      lambda_bord_ref: float = 0.0, lambda_bord_new: float = 0.0):
    lignes = []
    for e in essais:
        rap_ref = e.rapport(cfg_ref, facteur_ref, 0.0, lambda_bord_ref)
        rap_new = e.rapport(cfg_new, facteur_new, sigma_new, lambda_bord_new)
        for tc in e.tc_valides:
            lignes.append({
                "essai": e.nom, "TC": tc,
                "rmse_ref": rap_ref.loc[tc, "rmse"], "rmse_new": rap_new.loc[tc, "rmse"],
                "dTmax_ref": rap_ref.loc[tc, "delta_T_max"], "dTmax_new": rap_new.loc[tc, "delta_T_max"],
            })
    return pd.DataFrame(lignes)


def principale():
    ap = argparse.ArgumentParser()
    ap.add_argument("--essais", nargs="+",
                    default=["exp7_200A", "exp7_150A", "exp7_250A", "exp9_200A_y20_monospot"],
                    help="essais INCLUS dans l'objectif joint (résidu concaténé)")
    ap.add_argument("--essais-holdout", nargs="+", default=["exp9_200A_monospot"],
                    help="essais reportés dans la table mais PAS inclus dans le résidu (check blind)")
    ap.add_argument("--n-lhs", type=int, default=10)
    ap.add_argument("--max-nfev", type=int, default=40)
    ap.add_argument("--nx", type=int, default=31)
    ap.add_argument("--ny", type=int, default=11)
    ap.add_argument("--nz", type=int, default=13)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--calibrer-sigma", action="store_true",
                    help="ajoute source_sigma_mm comme 5e paramètre LIBRE (défaut : figé à 0)")
    ap.add_argument("--source-sigma-mm-fige", type=float, default=0.0,
                    help="valeur figée de source_sigma_mm si --calibrer-sigma absent")
    ap.add_argument("--lambda-bord-mm-fige", type=float, default=0.0,
                    help="adoucissement du bord (jumeau.em.source_joule.lambda_bord_mm), "
                         "FIGÉ (pas calibré) -- applique le MEME lambda_bord_mm au theta* "
                         "de reference ET au theta* new du fit, pour comparer a forme de "
                         "source egale (defaut 0 = chemin historique)")
    ap.add_argument("--anisotrope", action="store_true",
                    help="remplace k_plan SCALAIRE par kx/ky LIBRES et INDEPENDANTS "
                         "(materiaux.Materiau.k_plan_x/k_plan_y, cf. thermique/solveur2d.py) "
                         "-- prototype 2026-07-31, mission thermal-solver-engineer, flag OFF par defaut")
    # θ* de référence (config/materiaux.yaml, consolidation 2026-07-30) -- TOUJOURS
    # isotrope (k_plan=3.0) : c'est la référence documentée à battre, anisotrope ou pas.
    ap.add_argument("--facteur-ref", type=float, default=6.0123)
    ap.add_argument("--h-bas-2d-ref", type=float, default=37.424)
    ap.add_argument("--k-plan-ref", type=float, default=3.0)
    ap.add_argument("--h-bord-x0-ref", type=float, default=250.0)
    ap.add_argument("--figer", nargs="+", default=[], metavar="NOM=VALEUR",
                    help="fige un ou plusieurs paramètres (parmi facteur_couplage, "
                         "h_bas_2d, k_plan|kx/ky, h_bord_x0, [source_sigma_mm]) à VALEUR "
                         "-- diagnostic de sensibilité/famille, ex. --figer h_bas_2d=37.424")
    args = ap.parse_args()

    figer = {}
    for tok in args.figer:
        nom, _, val = tok.partition("=")
        figer[nom] = float(val)

    print(f"Chargement des essais joints : {args.essais}")
    essais_joint = [EssaiCalibre(nom, args.nx, args.ny, args.nz) for nom in args.essais]
    print(f"Chargement des essais held-out : {args.essais_holdout}")
    essais_holdout = [EssaiCalibre(nom, args.nx, args.ny, args.nz) for nom in args.essais_holdout]

    calib = CalibrateurJoint(essais_joint, calibrer_sigma=args.calibrer_sigma,
                             source_sigma_mm_fige=args.source_sigma_mm_fige,
                             lambda_bord_mm_fige=args.lambda_bord_mm_fige,
                             anisotrope=args.anisotrope)
    print(f"Paramètres calibrés : {calib.noms}")
    print(f"Bornes basses : {calib.bornes[0].tolist()}")
    print(f"Bornes hautes : {calib.bornes[1].tolist()}")
    print(f"h_haut FIGÉ à {H_HAUT_FIGE} (non-identifiable, cf. docstring module).")

    resultat = calib.calibrer(n_lhs=args.n_lhs, max_nfev=args.max_nfev, seed=args.seed, figer=figer)

    print("\n=== θ*_new joint ===")
    for i, nom in enumerate(calib.noms):
        if nom in resultat["figer"]:
            print(f"  {nom} = {resultat['theta'][i]:.5g}  (FIGÉ, non calibré)")
        else:
            se = resultat["erreurs_std"].get(nom, float("nan"))
            print(f"  {nom} = {resultat['theta'][i]:.5g} ± {se:.3g}")
    print(f"Coût final : {resultat['cout']:.1f} | succès : {resultat['succes']} "
          f"({resultat['nfev']} évaluations NLSQ) | message : {resultat['message']}")
    if resultat["correlation"] is not None:
        noms_libres = resultat["noms_libres"]
        print(f"Corrélations (ordre {noms_libres}) :")
        print(np.round(resultat["correlation"], 3))
        for i in range(len(noms_libres)):
            for j in range(i + 1, len(noms_libres)):
                r = resultat["correlation"][i, j]
                if abs(r) > 0.95:
                    print(f"  ATTENTION : |corr({noms_libres[i]}, {noms_libres[j]})| = {abs(r):.3f} > 0.95 "
                          f"-- quasi-non-identifiabilité.")

    # --- table de comparaison ref vs new, sur essais joint + holdout ---
    theta = resultat["theta"]
    facteur_new = theta[0]
    idx_sigma = 5 if args.anisotrope else 4
    sigma_new = theta[idx_sigma] if args.calibrer_sigma else args.source_sigma_mm_fige
    cfg_ref = Config.charger(RACINE / "config")
    cfg_ref.contact.h_haut = H_HAUT_FIGE
    cfg_ref.ambiant.h_bas_2d = args.h_bas_2d_ref
    cfg_ref.materiau.k_plan = args.k_plan_ref   # référence TOUJOURS isotrope
    cfg_ref.ambiant.h_bord_x0 = args.h_bord_x0_ref

    cfg_new = Config.charger(RACINE / "config")
    cfg_new.contact.h_haut = H_HAUT_FIGE
    cfg_new.ambiant.h_bas_2d = theta[1]
    if args.anisotrope:
        cfg_new.materiau.k_plan_x = theta[2]
        cfg_new.materiau.k_plan_y = theta[3]
        cfg_new.ambiant.h_bord_x0 = theta[4]
    else:
        cfg_new.materiau.k_plan = theta[2]
        cfg_new.ambiant.h_bord_x0 = theta[3]

    print("\n=== Table de comparaison (essais JOINT) ===")
    tbl_joint = table_comparaison(essais_joint, cfg_ref, args.facteur_ref, cfg_new, facteur_new, sigma_new,
                                  lambda_bord_ref=args.lambda_bord_mm_fige,
                                  lambda_bord_new=args.lambda_bord_mm_fige)
    print(tbl_joint.round(1).to_string(index=False))
    print(f"\nRMSE moyen (JOINT) : réf={tbl_joint['rmse_ref'].mean():.1f} °C "
          f"vs new={tbl_joint['rmse_new'].mean():.1f} °C")
    print(f"|ΔT_max| moyen (JOINT) : réf={tbl_joint['dTmax_ref'].abs().mean():.1f} °C "
          f"vs new={tbl_joint['dTmax_new'].abs().mean():.1f} °C")

    if essais_holdout:
        print("\n=== Table de comparaison (essais HOLD-OUT, non vus par le fit) ===")
        tbl_hold = table_comparaison(essais_holdout, cfg_ref, args.facteur_ref, cfg_new, facteur_new, sigma_new,
                                     lambda_bord_ref=args.lambda_bord_mm_fige,
                                     lambda_bord_new=args.lambda_bord_mm_fige)
        print(tbl_hold.round(1).to_string(index=False))
        print(f"\nRMSE moyen (HOLD-OUT) : réf={tbl_hold['rmse_ref'].mean():.1f} °C "
              f"vs new={tbl_hold['rmse_new'].mean():.1f} °C")
        print(f"|ΔT_max| moyen (HOLD-OUT) : réf={tbl_hold['dTmax_ref'].abs().mean():.1f} °C "
              f"vs new={tbl_hold['dTmax_new'].abs().mean():.1f} °C")
        tbl_all = pd.concat([tbl_joint, tbl_hold], ignore_index=True)
    else:
        tbl_all = tbl_joint

    print(f"\nRMSE moyen GLOBAL (tous essais rapportés) : réf={tbl_all['rmse_ref'].mean():.1f} °C "
          f"vs new={tbl_all['rmse_new'].mean():.1f} °C")

    h_bord_x0_new = theta[4] if args.anisotrope else theta[3]
    print("\nValidation croisée manuelle (2D) :")
    print(f"  python scripts/valider.py --modele 2D --facteur {facteur_new:.5g} --decalage-x 0 "
          f"--h-haut {H_HAUT_FIGE:.5g} --h-bas-2d {theta[1]:.5g} --h-bord-x0 {h_bord_x0_new:.5g} "
          f"--essais {' '.join(args.essais + args.essais_holdout)}"
          + (f" --source-sigma-mm {sigma_new:.5g}" if sigma_new else "")
          + (f" --lambda-bord-mm {args.lambda_bord_mm_fige:.5g}" if args.lambda_bord_mm_fige else "")
          + ("\n  (NB : kx/ky ne sont pas des flags de valider.py -- l'appliquer via "
             "materiaux.Materiau.k_plan_x/k_plan_y avant de rejouer, ou utiliser ce script.)"
             if args.anisotrope else
             "\n  (NB : k_plan n'est pas un flag de valider.py -- l'appliquer via "
             "config/materiaux.yaml:cf_pekk.k_plan avant de rejouer, ou utiliser ce script.)"))


if __name__ == "__main__":
    principale()
