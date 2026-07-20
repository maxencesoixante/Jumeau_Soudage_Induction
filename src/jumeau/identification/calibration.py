"""Calibration LHS + NLSQ des entrées incertaines des modèles 3D et 2D.

Pipeline porté du notebook 1D (MAX_InductionNumerical) et de sa vérification
black-box (Samanis et al. 2026 §2.3) :
1. LHS (Latin Hypercube) sur l'espace des paramètres -> meilleur point de départ ;
2. NLSQ (Gauss-Newton, scipy.least_squares) avec résidus pondérés par le
   bruit capteur σ = std(diff(mesure))/√2 (plancher 0,1 °C).

Paramètres calibrés (4, communs aux deux modèles pour les 2 premiers) —
choisis pour rester identifiables (leçon black-box : ne PAS calibrer
fréquence + facteur d'échelle ensemble) :
- ``facteur_couplage``  : échelle GLOBALE de la source Joule (blindage, contacts,
  σ et f incertains) ;
- ``decalage_x``        : décalage bobine<->montage le long de x (incertitude de
  positionnement non mesurée, cf. geometrie.yaml:coil.decalage_x). Ajouté le
  2026-07-18 après la découverte par l'agent EM d'un zéro EXACT de dissipation
  au plan de symétrie du hairpin ;
- 3D : ``h_contact`` (conductance vers le puits céramique/concentrateur) et
  ``h_bas`` (convection équivalente face inférieure) ;
- 2D (modèle lumpé dans l'épaisseur, ``thermique/solveur2d.py``, 2026-07-20) :
  ``h_haut`` (``materiaux.ContactCeramique.h_haut`` — perte effective vers le
  puits céramique/concentrateur, active seulement sous le masque CFC) et
  ``h_bas_2d`` (``materiaux.Ambiant.h_bas_2d`` — perte effective face
  opposée/ambiant, appliquée partout). Ce sont les analogues lumpés de
  h_contact/h_bas : mêmes rôles physiques (haut = puits sous CFC, bas =
  ambiant partout), donc a priori séparément identifiables par le même
  argument spatial que 3D (où corr(h_contact, h_bas) = 0.067, cf. historique
  ci-dessous) — un TC actuellement sous une empreinte CFC pressée voit h_haut
  ET h_bas_2d, un TC hors empreinte (refroidissement, passe suivante) ne voit
  QUE h_bas_2d : le masque CFC (suit le spot actif, cf. ``Essai.masque_fn``)
  fournit le contraste nécessaire.

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
sont donc repliées sur [0, +borne_max] plutôt que [−borne_max, +borne_max].
Pour les essais Séries A/B (4 spots au pas de 30 mm, TC un par spot), le
même repli [0, +max] est conservé par défaut PAR COHÉRENCE avec le 3D et par
prudence : bien que la symétrie stricte plan-par-plan ne tienne plus TC à TC
(chaque TC ne voit qu'UN spot décalé, pas une paire image), l'ENSEMBLE des 4
spots reste globalement symétrique en x autour du centre du laminé (spots à
15,875/45,875/75,875/105,875 mm, symétriques 2 à 2 autour de 60,875 mm) et
rien ne garantit a priori que le signe soit mieux résolu ; le borner à
[0, +max] reste donc l'hypothèse par défaut, à assouplir seulement si un
diagnostic ultérieur le justifie.

IDENTIFIABILITÉ facteur_couplage <-> decalage_x — avertissement de l'agent EM,
confirmé numériquement (calibration 3D sur chauffe_250A_3TC, 2026-07-19) :
corr(facteur_couplage, decalage_x) = 0.985 > 0.95 ET decalage_x railé
EXACTEMENT sur sa borne haute (0,015). Recommandation appliquée depuis : FIGER
decalage_x (bord physique de l'enveloppe bobine/CFC, ou une valeur mesurée
indépendamment) et ne calibrer que les 3 autres paramètres. La même
vérification DOIT être refaite pour le modèle 2D (essai de calibration et
grille source différents) — ne pas supposer que le résultat 3D se transpose
tel quel ; la matrice de corrélation post-fit (``_incertitudes``) DOIT être
inspectée après chaque calibration, et un |r| > 0.95 entre facteur_couplage
et decalage_x rapporté comme un signal de quasi-non-identifiabilité.

La calibration se fait sur UN essai ; la validation sur les autres essais se
fait SANS recalibrage (scripts/valider.py).

CHOIX DE L'ESSAI DE CALIBRATION 2D (2026-07-20) — en 2D, les TC ``z: surface``
et ``z: opposee`` ne sont pas représentables (modèle lumpé à une maille dans
l'épaisseur, cf. ``thermique/solveur2d.py`` et ``Essai.series_tc``) : sur
chauffe_250A_3TC il ne reste que TC2 (interface), ce qui est sous-déterminé
pour 4 paramètres. Les essais Séries A/B (serieA_A-1, serieA_A-3, serieB_B-2)
ont jusqu'à 5 TC À L'INTERFACE à 4 positions x différentes (spots séquentiels
au pas de 30 mm), ce qui apporte le contraste spatial nécessaire. Le
Calibrateur FILTRE automatiquement ``tc_valides`` aux seuls TC ``z: interface``
quand ``modele="2D"`` (les autres sont silencieusement exclus du résidu — un
message est imprimé pour audit). Essai retenu par défaut pour la calibration
2D : ``serieA_A-1`` (250 A, 5 TC dont 4 à l'interface après filtrage, consigne
400 °C, 1420 s simulés) — cf. ``scripts/calibrer.py --modele 2D``.

Note (post-mortem calibration bloquée) : chaque évaluation de résidu est une
simulation complète (3D : ~1-3 min sur la grille grossière par défaut ; 2D :
~2-20 s selon la durée simulée, ~63x plus rapide que le 3D sur la même grille
de surface, cf. rapport de vérification du solveur 2D). La phase NLSQ ne
produisait auparavant AUCUNE sortie avant son tout dernier message, ce qui,
combiné à ``max_nfev`` élevé, donnait l'impression d'un plantage alors que le
calcul progressait normalement. Une simulation qui diverge réellement (bord
de l'espace des paramètres, ``solve_ivp`` en échec, température non finie)
levait en outre une exception non rattrapée dans ``_residus`` pendant le
NLSQ (seule la boucle LHS l'attrapait) : `least_squares` plante alors sans
message exploitable. Les deux défauts sont corrigés ci-dessous : progression
affichée par évaluation NLSQ, et un point divergent est désormais pénalisé
par un résidu fini plutôt que de propager une exception.

Note (extension à 4 paramètres, 2026-07-18) : ``decalage_x`` change la FORME
du champ source (pas seulement son échelle comme ``facteur_couplage``), donc
chaque évaluation de résidu reconstruit un ``Essai`` complet (source EM
recalculée avec le ``decalage_x`` courant).

Note (extension au modèle 2D, 2026-07-20) : ``_residus`` délègue maintenant
la construction du solveur et l'intégration temporelle à ``Essai.simuler``
(au lieu d'instancier ``SolveurThermique3D`` à la main) — un seul chemin de
code pour les deux modèles, sélectionné par ``self.modele`` ("3D"/"2D"), qui
reproduit exactement le comportement historique côté 3D (même ``t_eval``,
mêmes valeurs par défaut de rtol/atol/max_step, mêmes nœuds de contrôle du
thermostat). Côté 2D, les paramètres 3 et 4 de ``theta`` surchargent
``cfg.contact.h_haut``/``cfg.ambiant.h_bas_2d`` au lieu de
``cfg.contact.h_contact``/``cfg.ambiant.h_bas``.
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
    """Calibre [facteur_couplage, decalage_x, p3, p4] contre un essai mesuré.

    ``modele`` sélectionne la physique ET les deux derniers paramètres :
    - "3D" (défaut, rétro-compatible) : p3=h_contact, p4=h_bas ;
    - "2D" (modèle lumpé à l'interface) : p3=h_haut, p4=h_bas_2d ; les TC non
      ``z: interface`` de l'essai sont automatiquement exclus du résidu (cf.
      docstring module).
    """

    # noms des 4 paramètres calibrés, par modèle (les 2 premiers sont partagés)
    NOMS_PAR_MODELE = {
        "3D": ("facteur_couplage", "decalage_x", "h_contact", "h_bas"),
        "2D": ("facteur_couplage", "decalage_x", "h_haut", "h_bas_2d"),
    }
    # bornes par défaut (basses, hautes), par modèle — h_haut/h_bas_2d suivent
    # les enveloppes suggérées par materiaux.yaml (mêmes ordres de grandeur
    # physiques que h_contact/h_bas 3D, cf. commentaires ceramique.h_haut et
    # ambiant.h_bas_2d)
    BORNES_PAR_MODELE = {
        "3D": ((0.05, 0.0, 5.0, 2.0), (30.0, 0.015, 500.0, 300.0)),
        "2D": ((0.05, 0.0, 1.0, 2.0), (30.0, 0.015, 50.0, 300.0)),
    }
    # attribut de classe historique (rétro-compat : code qui lisait
    # Calibrateur.NOMS avant l'ajout du modèle 2D) — chaque INSTANCE expose
    # aussi ``self.NOMS``, propre à son ``modele``, qui prime en pratique.
    NOMS = NOMS_PAR_MODELE["3D"]

    # Pénalité (en unités de résidu pondéré, sans dimension) appliquée à un point
    # dont la simulation diverge ou échoue. Choisie nettement au-dessus du pire
    # coût observé sur un point LHS raisonnable pour que le point soit
    # clairement rejeté par le solveur, sans être assez extrême pour dérégler
    # l'échelle de confiance interne de `least_squares`.
    PENALITE_RESIDU = 100.0

    def __init__(self, cfg: Config, chemin_essai, modele: str = "3D",
                 bornes_basses=None, bornes_hautes=None, nx=31, ny=11, nz=13,
                 recaler_debut=True):
        if modele not in self.NOMS_PAR_MODELE:
            raise ValueError(f"modele={modele!r} inconnu (attendu '3D' ou '2D')")
        self.modele = modele
        self.NOMS = self.NOMS_PAR_MODELE[modele]

        self.cfg = cfg
        self.chemin_essai = chemin_essai
        self.nx, self.ny, self.nz = nx, ny, nz
        bornes_def = self.BORNES_PAR_MODELE[modele]
        if bornes_basses is None:
            bornes_basses = bornes_def[0]
        if bornes_hautes is None:
            bornes_hautes = bornes_def[1]
        self.bornes = (np.array(bornes_basses, float), np.array(bornes_hautes, float))
        # ``decalage_x`` borné à [0, +max] et non [-max, +max] : voir docstring
        # module (signe non identifiable, hypothèse conservée par défaut aussi
        # pour les essais Séries A/B utilisés en 2D).
        if self.bornes[0][1] < 0.0:
            raise ValueError(
                "borne basse de decalage_x < 0 : le signe de decalage_x n'est "
                "pas garanti identifiable (voir docstring module) — borner à "
                "[0, +max]."
            )

        # grille grossière pour la calibration (chaque évaluation = 1 simulation).
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

        tc_valides = list(self.essai.spec.get("tc_valides", []))
        self.tc_exclus_2d: list[str] = []
        if modele == "2D":
            # cf. Essai.series_tc : seuls les TC "z: interface" sont
            # représentables par le modèle lumpé -> les exclure du résidu
            # (sinon KeyError dans series[tc], rattrapé comme une divergence
            # et pénalisant TOUT le vecteur de résidu, y compris les TC
            # valides).
            positions = self.essai.spec.get("thermocouples", {})
            self.tc_exclus_2d = [tc for tc in tc_valides
                                  if positions.get(tc, {}).get("z") != "interface"]
            if self.tc_exclus_2d:
                print(f"[Calibrateur 2D] TC exclus du résidu (non 'interface', "
                      f"non représentables par le modèle lumpé) : {self.tc_exclus_2d}")
            tc_valides = [tc for tc in tc_valides if tc not in self.tc_exclus_2d]
        self.tc_valides = tc_valides
        if not self.tc_valides:
            raise ValueError(
                f"aucun TC exploitable pour modele={modele!r} sur {chemin_essai} "
                f"(tc_valides vide après filtrage) — choisir un autre essai."
            )

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
        facteur, decalage_x, p3, p4 = theta
        try:
            if self.modele == "3D":
                self.cfg.contact.h_contact = float(p3)
                self.cfg.ambiant.h_bas = float(p4)
            else:
                self.cfg.contact.h_haut = float(p3)
                self.cfg.ambiant.h_bas_2d = float(p4)

            # decalage_x change la FORME du champ source (pas seulement son
            # échelle) : on ne peut plus réutiliser un Essai figé et mettre sa
            # source à l'échelle comme pour facteur_couplage seul -> on
            # reconstruit l'Essai (source EM incluse) pour ce theta.
            essai = Essai(self.cfg, self.chemin_essai, nx=self.nx, ny=self.ny, nz=self.nz,
                          facteur_couplage=float(facteur), decalage_x=float(decalage_x),
                          racine=self.racine)

            solveur, sol = essai.simuler(modele=self.modele)
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
        # jacobien + essais de pas) est une simulation complète. Sans retour
        # visuel, l'absence de sortie pendant potentiellement plusieurs minutes
        # à heures est indiscernable d'un plantage : on affiche donc la
        # progression.
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
            print(f"NLSQ [{self.modele}] : démarrage à θ0={np.round(meilleur, 4).tolist()} "
                  f"({origine}) — {max_nfev} évaluations max.")

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
