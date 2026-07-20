"""Calibration LHS + NLSQ des entrées incertaines du modèle 3D.

Pipeline porté du notebook 1D (MAX_InductionNumerical) et de sa vérification
black-box (Samanis et al. 2026 §2.3) :
1. LHS (Latin Hypercube) sur l'espace des paramètres -> meilleur point de départ ;
2. NLSQ (Gauss-Newton, scipy.least_squares) avec résidus pondérés par le
   bruit capteur σ = std(diff(mesure))/√2 (plancher 0,1 °C).

Paramètres calibrés (defaut) — choisis pour rester identifiables (leçon
black-box : ne PAS calibrer fréquence + facteur d'échelle ensemble) :
- ``facteur_couplage``  : échelle GLOBALE de la source Joule (blindage, contacts,
  σ et f incertains) ;
- ``decalage_x``        : décalage bobine<->montage le long de x (incertitude de
  positionnement non mesurée, cf. geometrie.yaml:coil.decalage_x). Ajouté le
  2026-07-18 après la découverte par l'agent EM d'un zéro EXACT de dissipation
  au plan de symétrie du hairpin, plan qui coïncide avec les TC de
  chauffe_250A_3TC (spot centre_x=0,060 = centre du laminé = position des 3 TC) ;
  un décalage de quelques mm déplace ce zéro et change fortement le taux de
  chauffe local (5,6 -> 13,25 °C/s pour +10 mm à facteur fixé) ;
- ``h_contact``         : conductance vers le puits céramique/concentrateur ;
- ``h_bas``             : convection équivalente face inférieure.

SYMÉTRIE DE decalage_x (identifiabilité du signe) — pour chauffe_250A_3TC le
spot est centré (x=0,060 m) sur un laminé de longueur 0,120 m avec conditions
aux limites (convection sur tous les chants, h_bas uniforme en face inférieure)
et TC eux-mêmes tous au centre (x=0,060). Le domaine ENTIER de ce essai est
donc symétrique par rapport au plan x=0,060 dès que decalage_x=0 ; décaler la
bobine de +d ou −d produit deux configurations image l'une de l'autre par ce
même plan, avec les TC exactement SUR le plan de symétrie -> le résidu de cet
essai est pair en decalage_x et le SIGNE n'est pas identifiable depuis ces
données seules (vérifié numériquement : simulations à decalage_x=±0,005 et
±0,010 avec (facteur, h_contact, h_bas) figés donnent des séries TC1/2/3
identiques à la précision numérique du solveur). Les bornes de calibration
sont donc repliées sur [0, +borne_max] plutôt que [−borne_max, +borne_max] :
calibrer sur l'intervalle signé produirait deux bassins d'attraction
symétriques et un NLSQ local resterait piégé arbitrairement dans l'un des
deux, ce qui est trompeur à rapporter comme une incertitude gaussienne unique.
``decalage_x`` calibré ici doit donc être lu comme une AMPLITUDE de décalage,
pas une direction ; la direction réelle resterait à trancher par une mesure
indépendante (cartographie bobine/CFC/TC au montage) si elle devient utile
(ex. essais avec spot non centré, où la symétrie ne tient plus).

IDENTIFIABILITÉ facteur_couplage <-> decalage_x — avertissement de l'agent EM :
les deux paramètres remodèlent Q local près du TC (l'un à l'échelle globale,
l'autre en déplaçant le zéro de dissipation) ; c'est la même famille de piège
que f_I/r_I sur la plaque mince (deux paramètres qui redistribuent la même
énergie déposée). Contrairement à f/facteur (dont la corrélation est
EXACTE — un seul degré de liberté effectif), facteur_couplage et decalage_x ne
sont PAS mathématiquement dégénérés : facteur_couplage change le NIVEAU de Q
partout (y compris loin du zéro), decalage_x change surtout la FORME locale
près du plan de symétrie ; avec 3 TC à des profondeurs différentes (surface,
interface, face opposée) qui voient le champ décalé différemment, le
problème a en principe assez d'information pour séparer les deux. Ce n'est
qu'un espoir a priori : la matrice de corrélation post-fit (``_incertitudes``)
DOIT être inspectée après calibration, et un |r| > 0.95 entre facteur_couplage
et decalage_x doit être rapporté comme un signal de quasi-non-identifiabilité
(auquel cas la recommandation est de figer decalage_x à sa valeur nominale
CAO — 0 — ou à une valeur mesurée indépendamment, et de ne calibrer que
facteur_couplage/h_contact/h_bas comme avant).

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

Note (extension à 4 paramètres, 2026-07-18) : ``decalage_x`` change la FORME
du champ source (pas seulement son échelle comme ``facteur_couplage``), donc
contrairement au schéma à 3 paramètres qui figeait un ``Essai`` de référence
et ne faisait QUE mettre à l'échelle sa source pré-calculée (``facteur *
essai.source_fn``), chaque évaluation de résidu reconstruit maintenant un
``Essai`` complet (source EM recalculée avec le ``decalage_x`` courant). Le
coût par évaluation augmente donc légèrement (un solve EM par couche et par
nœud z retenu, au lieu d'un solve EM par couche partagé entre tous les
theta) ; il reste dominé par l'intégration temporelle 3D.
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
    parametres: dict                         # TOUS les paramètres (calibrés + figés)
    cout: float
    succes: bool
    historique_lhs: list = field(default_factory=list)
    message: str = ""
    nfev: int = 0
    erreurs_std: dict | None = None          # écart-type par paramètre CALIBRÉ (absent des figés)
    correlation: np.ndarray | None = None    # matrice de corrélation (ordre = noms_calibres)
    noms_calibres: tuple = ()                # sous-ensemble de Calibrateur.NOMS effectivement libre
    parametres_figes: dict = field(default_factory=dict)   # paramètres FIGÉS (non calibrés) et leur valeur


class Calibrateur:
    """Calibre [facteur_couplage, decalage_x, h_contact, h_bas] contre un essai mesuré."""

    NOMS = ("facteur_couplage", "decalage_x", "h_contact", "h_bas")

    # Pénalité (en unités de résidu pondéré, sans dimension) appliquée à un point
    # dont la simulation diverge ou échoue. Choisie nettement au-dessus du pire
    # coût observé sur un point LHS raisonnable (~1.5-9e6 / ~900 résidus, soit un
    # résidu quadratique moyen de l'ordre de quelques milliers -> résidu ~qq 10aines)
    # pour que le point soit clairement rejeté par le solveur, sans être assez
    # extrême pour dérégler l'échelle de confiance interne de `least_squares`.
    PENALITE_RESIDU = 100.0

    def __init__(self, cfg: Config, chemin_essai, bornes_basses=(0.05, 0.0, 5.0, 2.0),
                 bornes_hautes=(30.0, 0.015, 500.0, 300.0), nx=31, ny=11, nz=13,
                 recaler_debut=True):
        self.cfg = cfg
        self.chemin_essai = chemin_essai
        self.nx, self.ny, self.nz = nx, ny, nz
        self.bornes = (np.array(bornes_basses, float), np.array(bornes_hautes, float))
        # ``decalage_x`` borné à [0, +max] et non [-max, +max] : le résidu de
        # cet essai (spot + TC centrés en x=0,060 sur un domaine symétrique) est
        # pair en decalage_x -> le signe n'est pas identifiable (voir docstring
        # module). Calibrer sur l'intervalle signé créerait deux bassins
        # d'attraction symétriques sans que le NLSQ local puisse choisir entre
        # eux de façon reproductible.
        if self.bornes[0][1] < 0.0:
            raise ValueError(
                "borne basse de decalage_x < 0 : le résidu de chauffe_250A_3TC "
                "est pair en decalage_x (TC au plan de symétrie du hairpin), le "
                "signe n'est pas identifiable — borner à [0, +max] (voir docstring)."
            )

        # grille grossière pour la calibration (chaque évaluation = 1 simulation 3D).
        # Construit une première fois pour récupérer grille/spec/mesures ; theta
        # (y compris decalage_x, qui change la FORME du champ source) reconstruit
        # un Essai complet à chaque évaluation de résidu (cf. _residus).
        self.essai = Essai(cfg, chemin_essai, nx=nx, ny=ny, nz=nz, facteur_couplage=1.0)
        self.racine = self.essai.racine

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
        facteur, decalage_x, h_contact, h_bas = theta
        try:
            self.cfg.contact.h_contact = float(h_contact)
            self.cfg.ambiant.h_bas = float(h_bas)

            # decalage_x change la FORME du champ source (pas seulement son
            # échelle) : on ne peut plus réutiliser un Essai figé et mettre sa
            # source à l'échelle comme pour facteur_couplage seul -> on
            # reconstruit l'Essai (source EM incluse) pour ce theta.
            essai = Essai(self.cfg, self.chemin_essai, nx=self.nx, ny=self.ny, nz=self.nz,
                          facteur_couplage=float(facteur), decalage_x=float(decalage_x),
                          racine=self.racine)

            from ..thermique.solveur3d import SolveurThermique3D
            solveur = SolveurThermique3D(essai.grille, self.cfg.materiau,
                                         self.cfg.ambiant, self.cfg.contact,
                                         masque_ceramique=essai.masque_fn)
            duree = float(essai.spec.get("duree_totale", essai.spec["duree_chauffe"]))
            t_eval = np.arange(0.0, duree + 0.5, 1.0)
            sol = solveur.simuler(essai.source_fn, (0.0, duree), t_eval=t_eval)
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
                 max_nfev: int = 60,
                 theta0: np.ndarray | None = None,
                 figer: dict | None = None) -> ResultatCalibration:
        """Calibre les paramètres LIBRES (``self.NOMS`` moins ceux de ``figer``).

        ``figer`` : dict optionnel {nom: valeur} de paramètres à FIGER (non
        calibrés), typiquement suite à un diagnostic de non-identifiabilité
        (corrélation post-fit |r| > 0.95, cf. docstring module). Exemple —
        fixer decalage_x au bord physique de son enveloppe plutôt que de le
        calibrer conjointement avec facteur_couplage :
            cal.calibrer(figer={"decalage_x": 0.015})
        ``theta0`` (démarrage à chaud) reste un vecteur complet dans l'ordre
        de ``self.NOMS`` ; les composantes correspondant à des noms figés sont
        ignorées (remplacées par la valeur de ``figer``).
        """
        figer = dict(figer or {})
        for nom in figer:
            if nom not in self.NOMS:
                raise ValueError(f"paramètre inconnu à figer : {nom!r} (attendu parmi {self.NOMS})")
        idx_libres = [i for i, n in enumerate(self.NOMS) if n not in figer]
        noms_libres = tuple(self.NOMS[i] for i in idx_libres)
        idx_figes = [i for i, n in enumerate(self.NOMS) if n in figer]

        theta_fige_complet = np.zeros(len(self.NOMS))
        for i in idx_figes:
            theta_fige_complet[i] = figer[self.NOMS[i]]

        def theta_complet(theta_libre):
            t = theta_fige_complet.copy()
            for k, i in enumerate(idx_libres):
                t[i] = theta_libre[k]
            return t

        def residus_libres(theta_libre):
            return self._residus(theta_complet(theta_libre))

        lo_complet, hi_complet = self.bornes
        lo = lo_complet[idx_libres]
        hi = hi_complet[idx_libres]

        if verbose and figer:
            print(f"Paramètres figés (non calibrés) : { {n: figer[n] for n in figer} } "
                  f"— calibration réduite à {noms_libres}.")

        historique = []
        if theta0 is not None:
            # Démarrage à chaud : reprise d'une calibration interrompue (ou
            # affinage depuis un optimum connu) — le balayage LHS est sauté.
            theta0_complet = np.clip(np.asarray(theta0, float), lo_complet, hi_complet)
            meilleur = theta0_complet[idx_libres]
            if verbose:
                print(f"Départ à chaud : θ0={np.round(meilleur, 5).tolist()} "
                      f"({noms_libres}) (LHS sauté)")
        else:
            pts = qmc.scale(qmc.LatinHypercube(d=len(lo), seed=seed).random(n=n_lhs), lo, hi)
            meilleur, cout_min = None, np.inf
            for i, p in enumerate(pts):
                try:
                    cout = float(np.sum(residus_libres(p) ** 2))
                except Exception as e:          # garde-fou (ne devrait plus se produire)
                    if verbose:
                        print(f"  LHS {i + 1}/{n_lhs} : échec ({e})")
                    continue
                historique.append((p.tolist(), cout))
                if cout < cout_min:
                    cout_min, meilleur = cout, p
                if verbose:
                    print(f"  LHS {i + 1}/{n_lhs} : θ={np.round(p, 4).tolist()} coût={cout:.1f}")

            if meilleur is None:
                raise RuntimeError("Aucun point LHS n'a produit une simulation valide.")

        # --- NLSQ : chaque évaluation (résidu de base + différences finies du
        # jacobien + essais de pas) est une simulation 3D complète. Sans retour
        # visuel, l'absence de sortie pendant potentiellement 1-2h est
        # indiscernable d'un plantage : on affiche donc la progression.
        nfev = [0]

        def residus_suivis(theta_libre):
            nfev[0] += 1
            t0 = time.monotonic()
            r = residus_libres(theta_libre)
            if verbose:
                dt = time.monotonic() - t0
                print(f"  NLSQ éval {nfev[0]} : θ={np.round(theta_libre, 5).tolist()} "
                      f"({noms_libres}) coût={float(np.sum(r ** 2)):.1f} ({dt:.1f}s)")
            return r

        if verbose:
            origine = "départ à chaud" if theta0 is not None else f"coût LHS={cout_min:.1f}"
            print(f"NLSQ : démarrage à θ0={np.round(meilleur, 4).tolist()} "
                  f"({origine}) — {max_nfev} évaluations max, "
                  f"chaque simulation ~1-3 min.")

        res = least_squares(residus_suivis, meilleur, bounds=(lo, hi),
                            xtol=1e-4, ftol=1e-4, diff_step=0.05, max_nfev=max_nfev)

        params = dict(zip(noms_libres, res.x))
        params.update(figer)   # paramètres complets = calibrés + figés

        erreurs_std, correlation = self._incertitudes(res, noms_libres)

        if verbose:
            print(f"NLSQ terminé après {nfev[0]} évaluations : succès={res.success} "
                  f"— {res.message}")
            print(f"  paramètres (calibrés + figés) = {params}")
            print(f"  coût = {2 * res.cost:.1f}")
            if erreurs_std is not None:
                print(f"  écarts-types = { {n: round(erreurs_std[n], 5) for n in noms_libres} }")
                print(f"  corrélations (ordre {noms_libres}) =\n{np.round(correlation, 3)}")
                for i in range(len(noms_libres)):
                    for j in range(i + 1, len(noms_libres)):
                        r = correlation[i, j]
                        if abs(r) > 0.95:
                            print(f"  ATTENTION : |corr({noms_libres[i]}, {noms_libres[j]})| "
                                  f"= {abs(r):.3f} > 0.95 — quasi-non-identifiabilité, à ne pas "
                                  f"calibrer conjointement sans figer l'un des deux.")

        return ResultatCalibration(
            parametres=params,
            cout=float(2 * res.cost),
            succes=bool(res.success),
            historique_lhs=historique,
            message=str(res.message),
            nfev=int(nfev[0]),
            erreurs_std=erreurs_std,
            correlation=correlation,
            noms_calibres=noms_libres,
            parametres_figes=dict(figer),
        )

    # ------------------------------------------------------------------
    def _incertitudes(self, res, noms_libres):
        """Écarts-types et corrélations paramétriques depuis le jacobien NLSQ.

        cov = s² · (JᵀJ)⁻¹ avec s² = 2·coût / ddl (résidus déjà pondérés par σ,
        donc J est le jacobien du résidu réduit). Une corrélation |r| -> 1 entre
        deux paramètres calibrés est un signal de non-identifiabilité à
        signaler, pas à masquer (cf. avertissement facteur_couplage <->
        decalage_x dans la docstring du module). ``noms_libres`` est le
        sous-ensemble de ``self.NOMS`` effectivement calibré (paramètres
        figés exclus : ils n'ont pas d'écart-type/corrélation, leur valeur
        est une hypothèse, pas une estimation).
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
        erreurs_std = dict(zip(noms_libres, se.tolist()))
        return erreurs_std, corr
