"""Orchestration d'un essai : passes séquentielles (4 empreintes), source et masque.

Un essai (config/essais/*.yaml) définit une liste de ``spots`` avec fenêtres
temporelles. La source Joule de chaque spot est précalculée une fois (le champ
EM est quasi statique à l'échelle thermique) puis activée par morceaux ;
le masque céramique/MFC suit le spot actif (le concentrateur n'appuie que là).
Après la dernière passe, la source s'éteint (refroidissement) et le masque du
dernier spot est conservé (refroidissement sous pression, cf. fiches A/B).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .geometrie import construire_couches, construire_grille, masque_empreinte_cfc
from .materiaux import Config, charger_yaml
from .em.source_joule import source_spot
from .thermique.solveur2d import SolveurThermique2D
from .thermique.solveur3d import Grille3D, SolveurThermique3D, bracket_lineaire

# Largeur (°C) de la transition du thermostat sigmoïde de coupure sur consigne
# (cf. Essai.source_fn / source_fn_2d) : facteur = 1/(1+exp((T_ctrl-consigne)/LARGEUR)).
# Nommée (plutôt qu'un "2" en dur) pour être documentée et testable. Diagnostic
# de validation croisée du 2026-07-20 (essais 250 A serieA_A-1/serieB_B-2,
# pics simulés dépassant la consigne de +60 à +120 °C) : réduire CETTE largeur
# seule, de 2.0 à 0.05 °C (quasi-échelon), ne change les pics simulés que de
# <1 °C, y compris avec la nouvelle définition de T_ctrl ci-dessous (cf.
# rapport thermal-solver-engineer 2026-07-20) -> la largeur n'est PAS le
# principal levier de dépassement ici. Conservée à 2.0 °C (valeur historique
# validée en 1D, cf. docstring module) : assez raide pour une coupure nette
# (transition ~±4-9 °C), assez douce pour ne pas ajouter de raideur numérique
# BDF. Le vrai fix est la définition de T_ctrl (POIDS_POINT_THERMOSTAT ci-dessous).
LARGEUR_THERMOSTAT_C: float = 2.0

# Poids du nœud ponctuel (centre_x, largeur/2, interface) dans T_ctrl, le
# complément (1 - POIDS) pondérant la moyenne de T sur toute la coupe
# transverse en y du spot actif -- cf. docstring Essai.source_fn pour le
# diagnostic complet. Choisi par balayage 0.3/0.5/0.6/0.7/0.8/0.85 sur les 3
# essais de validation croisée (serieA_A-1, serieA_A-3, serieB_B-2, θ calibré
# 2D du 2026-07-19) : 0.7 minimise l'écart de pic moyen |ΔT_max| sur les 11
# TC d'interface (74,7 °C -> 14,6 °C, cf. rapport de vérification) sans
# système biaisé dans un sens -> 0.6 et 0.8 sont tous deux moins bons (plus
# proche de 0 = sous-chauffe généralisée façon "moyenne pure" ; plus proche de
# 1 = re-dérive vers le dépassement du nœud ponctuel seul).
POIDS_POINT_THERMOSTAT: float = 0.7


class Essai:
    """Charge un YAML d'essai et construit source_fn / masque_fn / solveur."""

    def __init__(self, cfg: Config, chemin_essai: str | Path,
                 nx: int = 49, ny: int = 17, nz: int = 15,
                 facteur_couplage: float = 1.0,
                 decalage_x: float | None = None,
                 racine: str | Path | None = None,
                 interp_ctrl: bool = True,
                 champ_reaction: bool = False,
                 thermostat_capteurs: bool = False,
                 source_sigma_mm: float = 0.0,
                 lambda_bord_mm: float = 0.0,
                 lambda_bord_x_mm: float | None = None,
                 masque_source_mfc: bool = False,
                 masque_source_mode: str = "tronquer",
                 bimodal_sigma_mm: float = 0.0):
        self.cfg = cfg
        self.spec = charger_yaml(chemin_essai)
        self.racine = Path(racine) if racine else Path(chemin_essai).resolve().parents[3]
        self.grille: Grille3D = construire_grille(cfg, nx=nx, ny=ny, nz=nz)
        self.couches = construire_couches(cfg)
        self.facteur_couplage = facteur_couplage
        # decalage_x (m, calibrable) : décalage bobine<->spot le long de x, cf.
        # geometrie.yaml:coil.decalage_x. Surchargeable par programme (comme
        # facteur_couplage) pour la calibration ; sinon valeur du YAML (défaut
        # 0.0 tant qu'aucune mesure de position n'existe, cahier §2.1.4).
        if decalage_x is None:
            decalage_x = float(cfg.geometrie["coil"].get("decalage_x", 0.0))
        self.decalage_x = decalage_x
        # Nœud de contrôle du thermostat interpolé le long de x (défaut) au
        # lieu du nœud le plus proche de centre_x (``interp_ctrl=False``,
        # comportement historique < 2026-07-21) : centre_x (position réelle du
        # spot) ne tombe QUASIMENT JAMAIS sur un nœud de grille (cf.
        # ``_colonnes_ctrl``/rapport de vérification mesh-convergence), donc
        # l'instant de coupure du thermostat (T_ctrl atteint la consigne)
        # dépendait du maillage par un simple effet de positionnement discret,
        # indépendant de la véritable erreur de discrétisation -- contaminait
        # toute étude de convergence ET la calibration (les nœuds de contrôle
        # snappés à centre_x ont directement influencé θ*). ``interp_ctrl=False``
        # conservé pour comparaison/ablation (cf. tests, rapport de vérification).
        self.interp_ctrl = bool(interp_ctrl)
        # champ_reaction (défaut False = comportement historique inchangé) :
        # active la résolution auto-cohérente complexe du champ de réaction EM
        # (Bz_total = Bz_bobine + Bz_induit[psi], couplage inter-couches) au
        # lieu de l'atténuation ad hoc attenuation_blindage — cf. docstring
        # jumeau.em.source_joule et rapport resultats_champ_reaction_em.log.
        # NE PAS activer sans recalibrer facteur_couplage : contre-intuitivement
        # ce chemin AUGMENTE (pas ne réduit) la puissance déposée nette de
        # ~11 % au spot 2 (le retrait de l'écran ad hoc, plus gros que la
        # réaction physique elle-même, domine le bilan, cf. rapport) — testé
        # sur les 3 essais de validation, AGGRAVE le dépassement de pic sur
        # 2/3 d'entre eux à θ* figé. Désactivé par défaut ; non recommandé
        # comme comportement par défaut (cf. rapport, §6).
        self.champ_reaction = bool(champ_reaction)
        # thermostat_capteurs (défaut False = comportement historique inchangé) :
        # asservit la coupure sur le MAX de T aux POSITIONS RÉELLES des TC
        # d'interface de l'essai (au lieu du point/section à x=centre_x, cf.
        # _T_ctrl). Motivation (2026-07-27) : le cahier de laboratoire (étape 6
        # "chauffe jusqu'à Tprocessing", fiche B-1 "T max interface (TC 1/3/5)
        # jamais dépassé") ET les données B-2 (chaque impulsion coupée par le TC
        # le plus proche, alternant devant/derrière) établissent que le procédé
        # coupait sur le MAX des TC d'interface, pas au centre du spot. Cette loi
        # recale l'écart de pic (B-2 |ΔT_max| 45->23 après recalibration) mais
        # DÉGRADE le RMSE (+5-6 °C) : le RMSE est dominé par le déficit de VITESSE
        # de chauffe (taux ~2x trop lent), que le thermostat ne touche pas, et
        # elle est couplée au profil en M trop contrasté (on contrôle sur des TC
        # de bord y=0 surchauffés). NE PAS activer sans recalibrer θ* (le θ*
        # 'capteurs' diffère nettement : facteur ~4.6 / h_haut ~16). Conservée
        # derrière ce flag pour archivage/ablation, en attendant la cartographie
        # bord->centre qui doit corriger le M conjointement. Cf.
        # resultats_diag_b2_thermostat_capteurs.log.
        # VERDICT (issue #9) : loi thermostat_capteurs REJETÉE définitivement le
        # 2026-08-03 — fit joint pleine famille pire partout (le gain B-2 ne
        # survit pas au partage du facteur inter-familles). Conservée derrière
        # flag (repro + registre). Cf. docs/modele/leviers_refutes.md.
        self.thermostat_capteurs = bool(thermostat_capteurs)
        # positions (x, y) des TC d'interface valides (loi thermostat_capteurs) :
        # brackets bilinéaires précalculés une fois.
        self._brackets_capteurs: list = []
        if self.thermostat_capteurs:
            self._brackets_capteurs = [
                (bracket_lineaire(self.grille.x, x), bracket_lineaire(self.grille.y, y))
                for x, y in self._positions_capteurs_interface()
            ]

        # source_sigma_mm (défaut 0.0 = inchangé) : étalement gaussien de la
        # source (délocalisation du courant dans le twill tissé), cf.
        # source_joule._lisser_source et resultats_diag_centre_transitoire.log.
        # Adoucit l'« œil de boucle » au centre du spot -> le centre se remplit
        # plus tôt (résidu transitoire mesuré exp 7 avec céramique). NE PAS
        # activer sans recalibrer θ*. Défaut 0.0 -> non-régression bit-à-bit.
        self.source_sigma_mm = float(source_sigma_mm)
        # lambda_bord_mm (défaut 0.0 = inchangé) : repousse la BC psi=0 de
        # lambda_bord_mm au-delà du bord physique en largeur (adoucit le
        # contraste chant/centre du profil en "M"), cf.
        # jumeau.em.source_joule (docstring module, section "Adoucissement du
        # bord") et resultats_diag_lambda_bord_em.log. NE PAS activer sans
        # recalibrer theta*. Défaut 0.0 -> non-régression bit-à-bit.
        # VERDICT (issue #9) : RÉFUTÉ le 2026-07-31 — adoucit le M mais NON
        # conservatif en puissance (aucun θ* joint gagnant) ; la CL ψ=0 correcte
        # est corroborée par eppy. Conservé (repro). Cf. docs/modele/leviers_refutes.md.
        self.lambda_bord_mm = float(lambda_bord_mm)
        # lambda_bord_x_mm (défaut 0.0 = inchangé) : même dispositif que
        # lambda_bord_mm mais au bord EN X (x=0/longueur, bords RÉELS de
        # longueur de la plaque) -- corrige l'artefact LOCALISÉ de bascule
        # bord-piqué -> centre-piqué du profil q(y) sur les quelques mailles
        # avant le chant x pour un spot proche du bord (Jx forcé à 0 sur toute
        # la ligne de bord par psi=0), cf. jumeau.em.source_joule (docstring
        # module, section "Adoucissement du bord EN X"). Contrairement à
        # lambda_bord_mm (RÉFUTÉ, correction globale du contraste M sur tout
        # le domaine, non conservative), cette correction est LOCALE (2-3
        # colonnes de bord) et son échelle par défaut (None) N'EST PAS un
        # scalaire recalibrable : c'est l'épaisseur PROPRE de chaque couche
        # (couche.epaisseur), déjà dans le modèle -- aucun paramètre libre
        # ajouté. Défaut 0.0 -> non-régression bit-à-bit (chemin canonique
        # inchangé). Cf. docs/modele/ (diagnostic 2026-08-28) pour la
        # vérification numérique (le profil à x=chant NE redevient PAS
        # franchement bord-piqué même à la limite BC totalement relâchée --
        # ratio q(y=0)/q(y=centre) sature ~0,6, PAS >1 -- cf. docstring
        # module : la bascule vers le centre est en partie une physique RÉELLE
        # de fermeture de boucle au-delà de l'empreinte bobine, pas purement
        # un artefact de bord ; ce paramètre supprime la SUR-suppression
        # (collapse exact à 0) ajoutée par la BC stricte, sans prétendre
        # inverser tout le contraste).
        self.lambda_bord_x_mm = lambda_bord_x_mm
        # bimodal_sigma_mm (défaut 0.0 = OFF, bit-à-bit) : re-module la source en
        # 2 pôles (jambes hairpin, entraxe) de largeur sigma_mm — corrige la
        # sous-bimodalité de la chaîne ψ (cf. source_joule._bimodaliser_source,
        # issue #69). Facteur EFFECTIF à calibrer sur la thermographie plein-champ.
        self.bimodal_sigma_mm = float(bimodal_sigma_mm)
        # masque_source_mfc (défaut False = inchangé, bit-à-bit) : masque la
        # source Joule PAR SPOT à l'empreinte du MFC (masque_empreinte_cfc),
        # au lieu de la laisser rayonner sur tout le domaine résolu par
        # foucault.py. Motivation physique : le MFC (Ferrotron 559H, µr≈16)
        # concentre le flux SOUS son empreinte -- aujourd'hui son seul effet
        # sur la source est indirect (image-current sur Bz, cf. champ_coil.py
        # et plan_miroir_cfc) ; hors empreinte, aucune concentration de flux
        # n'est physiquement attendue. Le masque actuel (masque_fn, appliqué
        # à h_haut dans solveur2d) ne coupe QUE les pertes convectives sous
        # céramique, pas la source elle-même -- un MFC réduit (empreinte plus
        # petite que le coupon) ne changeait donc quasiment rien au profil
        # simulé (vérifié : cfc.longueur 0.055->0.03175 laisse le contraste
        # bord/centre ~inchangé, 5.4->5.5), ce qui est physiquement suspect.
        # APPROXIMATION DE 1er ORDRE (à documenter comme telle) : un masque
        # DUR (0/1, pas de frange/diffusion du champ proche à la lisière du
        # bloc MFC). Défaut False -> non-régression bit-à-bit (cf. tests
        # test_masque_source_mfc_off_est_identite). NE PAS activer sans
        # recalibrer facteur_couplage (la puissance totale change, cf.
        # masque_source_mode ci-dessous).
        self.masque_source_mfc = bool(masque_source_mfc)
        # masque_source_mode ("tronquer" | "conserver", n'a d'effet QUE si
        # masque_source_mfc=True) : deux modèles EM 1er ordre distincts pour
        # ce qui arrive au flux hors empreinte MFC.
        #   - "tronquer" (DÉFAUT, comportement historique < 2026-08-22) : le
        #     courant hors empreinte n'est pas redistribué à l'intérieur --
        #     la puissance totale déposée DIMINUE quand on masque, elle n'est
        #     PAS concentrée par conservation. Physiquement faux pour un vrai
        #     MFC (un concentrateur réduit canalise le flux dans une
        #     empreinte plus petite, il ne le supprime pas), mais conservé
        #     tel quel car c'est SUR ce comportement que le MFC labo (masque
        #     off, cf. plus bas) et θ* (facteur_couplage=6.0123) restent
        #     calibrés -- cf. docstring module source_joule.py pour la
        #     distinction avec le blindage/couplage inter-couches.
        #   - "conserver" (NOUVEAU, cf. tâche masque MFC réduit 2026-08-22) :
        #     renormalise Q_masqué = Q·mask·(∫Q / ∫(Q·mask)) -- intégrale de
        #     volume sur la plaque entière (grille RÉGULIÈRE par axe, dx/dy/dz
        #     constants -- cf. Grille3D.__post_init__ -- donc le rapport de
        #     sommes ndarray brutes est EXACTEMENT le rapport des intégrales
        #     de volume, le dV constant se simplifiant). Modèle 1er ordre :
        #     conserve la puissance Joule TOTALE déposée par spot (couplage
        #     bobine<->plaque inchangé), la reconcentre entièrement sous
        #     l'empreinte réduite -- hypothèse cohérente avec un concentrateur
        #     qui canalise (ne dissipe pas) le flux magnétique. LIMITES : pas
        #     de re-résolution de Bz pour la géométrie ferrite réduite (le
        #     champ image-current, cf. champ_coil.py, reste celui du MFC
        #     labo), pas de frange de champ proche à la lisière du bloc
        #     réduit (masque toujours dur 0/1), la répartition SPATIALE
        #     post-renormalisation sous l'empreinte reste celle, non modifiée,
        #     du champ non masqué (pas de re-calcul de la concentration fine
        #     du flux par le nouveau bloc MFC). NE PAS activer sans recalibrer
        #     facteur_couplage pour ce mode si on veut confronter aux niveaux
        #     absolus -- utilisé ici en θ* de référence (NON recalibré,
        #     tendance seulement, cf. gen_mfc_reduit.py).
        if masque_source_mode not in ("tronquer", "conserver"):
            raise ValueError(
                f"masque_source_mode doit être 'tronquer' ou 'conserver', reçu {masque_source_mode!r}"
            )
        self.masque_source_mode = str(masque_source_mode)

        courant = float(self.spec["courant"])
        self.spots = self.spec["spots"]
        self._Q_spots = [
            source_spot(self.grille, cfg, self.couches, courant,
                        float(s["centre_x"]), facteur_couplage=facteur_couplage,
                        decalage_x=self.decalage_x, champ_reaction=self.champ_reaction,
                        lissage_sigma_mm=self.source_sigma_mm,
                        lambda_bord_mm=self.lambda_bord_mm,
                        lambda_bord_x_mm=self.lambda_bord_x_mm,
                        bimodal_sigma_mm=self.bimodal_sigma_mm)
            for s in self.spots
        ]
        self._masques = [
            masque_empreinte_cfc(self.grille, cfg, float(s["centre_x"]))
            for s in self.spots
        ]
        if self.masque_source_mfc:
            # même masque (empreinte MFC posée au spot) que celui déjà utilisé
            # pour les pertes convectives (masque_fn/h_haut) : réutilisé ici
            # pour la source, PAS un nouveau masque indépendant -- garantit
            # que "où la céramique appuie" et "où le flux est concentré"
            # restent le même rectangle géométrique par construction.
            Q_masques = [
                Q * m[:, :, None] for Q, m in zip(self._Q_spots, self._masques)
            ]
            if self.masque_source_mode == "conserver":
                Q_conserves = []
                for Q, Qm in zip(self._Q_spots, Q_masques):
                    total = float(Q.sum())
                    total_m = float(Qm.sum())
                    facteur_reconcentration = total / total_m if total_m > 0.0 else 1.0
                    Q_conserves.append(Qm * facteur_reconcentration)
                self._Q_spots = Q_conserves
            else:
                self._Q_spots = Q_masques
        self._Q_nul = np.zeros_like(self._Q_spots[0])
        # nœuds de contrôle du thermostat (asservissement de source_fn à T) —
        # un jeu de nœuds PAR SPOT : toute la colonne en y à l'abscisse du
        # spot (centre_x, TOUT y, z=interface), plus l'ancien point unique
        # (centre_x, largeur/2, interface). cf. source_fn pour la raison :
        # ce point unique coïncide avec le plan de symétrie y=largeur/2 du
        # hairpin, où la dissipation Joule a un zéro quasi exact (cf.
        # identification/calibration.py, découverte agent EM 2026-07-18) ;
        # T y monte donc presque uniquement par conduction latérale depuis
        # les zones bien plus chauffées du même spot (jusqu'à ~60-80x plus de
        # puissance locale à quelques mm en y, cf. rapport de diagnostic
        # 2026-07-20) — la sonde ne "voit" le dépassement qu'avec un retard
        # de diffusion, longtemps après que l'essentiel de l'excès d'énergie
        # a déjà été déposé ailleurs dans l'empreinte, INDÉPENDAMMENT de la
        # largeur de la sigmoïde (vérifié : resserrer la largeur seule, de 2
        # à 0,05 °C, ne change les pics simulés que de <1 °C). ``T_ctrl``
        # (cf. source_fn/source_fn_2d) mélange donc ce point ET la moyenne de
        # TOUTE la coupe transverse du spot (poids ``POIDS_POINT_THERMOSTAT``)
        # : le thermostat coupe dès qu'une fraction significative de la
        # section chauffe, pas seulement quand le nœud malchanceux du plan de
        # symétrie y arrive (trop tard) -> dépassement des pics fortement
        # réduit sur les essais à forte source (250 A), cf. rapport de
        # vérification (moyenne pure testée aussi : sur-corrige, sous-chauffe
        # généralisée de 50-100 °C).
        # Union transmise au solveur pour que le jacobien creux couvre le
        # couplage source<->T_controle (sinon les FD groupées par couleur de
        # scipy ne l'évaluent jamais -> BDF rampe près de la consigne) ; TOUS
        # les nœuds qui entrent dans T_ctrl doivent être déclarés comme
        # colonnes de contrôle, pas seulement l'ancien point unique (vérifié :
        # sans ça, BDF devient ~5-10x plus lent sans que la solution change,
        # cf. rapport de vérification).
        self._noeuds_controle: list[tuple[int, int, int]] = []
        if self.spec.get("consigne_interface") is not None:
            noeuds = set()
            iz = self.grille.iz_interface
            if self.thermostat_capteurs:
                # loi capteurs : les 4 nœuds encadrant chaque position TC
                # d'interface entrent dans T_ctrl (max) -> à déclarer pour le
                # jacobien creux (cf. commentaire ci-dessus sur BDF).
                for (ix, _), (iy, _) in self._brackets_capteurs:
                    for dx in (0, 1):
                        for dy in (0, 1):
                            noeuds.add((ix + dx, iy + dy, iz))
            else:
                for s in self.spots:
                    ix0, ix1, _ = self._colonnes_ctrl(float(s["centre_x"]))
                    for ix in {ix0, ix1}:
                        for iy in range(self.grille.ny):
                            noeuds.add((ix, iy, iz))
            self._noeuds_controle = sorted(noeuds)

        # --- modèle 2D (lumpé dans l'épaisseur, cf. thermique/solveur2d.py) :
        # P_surf par spot = somme sur z du champ Q 3D déjà calculé ci-dessus
        # (W/m³ -> W/m², cf. commentaire de conservation dans source_joule.py :
        # le poids appliqué par couche garantit que Σ_z Q·dz redonne
        # exactement la puissance surfacique déposée par cette couche).
        self._P_spots_2d = [Q.sum(axis=2) * self.grille.dz for Q in self._Q_spots]
        self._P_nul_2d = np.zeros_like(self._P_spots_2d[0])
        # nœuds de contrôle 2D : mêmes (x, y) que le 3D, sans coordonnée z
        # (la maille EST l'interface dans le modèle lumpé).
        self._noeuds_controle_2d: list[tuple[int, int]] = sorted(
            {(ix, iy) for ix, iy, _ in self._noeuds_controle}
        )

    # ------------------------------------------------------------------
    def _spot_actif(self, t: float) -> int | None:
        for i, s in enumerate(self.spots):
            if float(s["t_debut"]) <= t < float(s["t_fin"]):
                return i
        return None

    def _colonnes_ctrl(self, centre_x: float) -> tuple[int, int, float]:
        """Colonne(s) x du nœud de contrôle du thermostat pour un spot centré
        en ``centre_x`` (m, position CONTINUE, cf. YAML d'essai) : bracket
        ``(ix0, ix1)`` + poids linéaire ``wx`` vers ``ix1`` si
        ``self.interp_ctrl`` (défaut), sinon nœud le plus proche seul
        (``ix0 == ix1``, ``wx = 0`` -- comportement historique < 2026-07-21,
        conservé pour ablation/comparaison, cf. ``_T_ctrl``)."""
        if not self.interp_ctrl:
            ix0 = self.grille.indice_xy(centre_x, 0.0)[0]
            return ix0, ix0, 0.0
        ix0, wx = bracket_lineaire(self.grille.x, centre_x)
        return ix0, ix0 + 1, wx

    def _positions_capteurs_interface(self) -> list[tuple[float, float]]:
        """(x, y) des TC d'interface VALIDES de l'essai (loi thermostat_capteurs)."""
        tcs = self.spec.get("thermocouples", {})
        out = []
        for nom in self.spec.get("tc_valides", []):
            p = tcs.get(nom, {})
            if p.get("z") == "interface":
                out.append((float(p["x"]), float(p["y"])))
        return out

    def _T_ctrl_capteurs(self, T: np.ndarray, deux_d: bool) -> float:
        """T_ctrl = MAX de T (interpolée bilinéairement) sur les positions TC
        d'interface réelles (loi ``thermostat_capteurs``, cf. __init__). Mime la
        coupure réelle « le TC d'interface le plus chaud atteint la consigne »."""
        champ = T if deux_d else T[:, :, self.grille.iz_interface]
        best = -np.inf
        for (ix, wx), (iy, wy) in self._brackets_capteurs:
            v = ((1.0 - wx) * (1.0 - wy) * champ[ix, iy]
                 + wx * (1.0 - wy) * champ[ix + 1, iy]
                 + (1.0 - wx) * wy * champ[ix, iy + 1]
                 + wx * wy * champ[ix + 1, iy + 1])
            if v > best:
                best = v
        return float(best)

    def _T_ctrl(self, T: np.ndarray, spot: dict, deux_d: bool) -> float:
        """Température de contrôle du thermostat pour le spot actif ``spot``.

        Mélange (poids ``POIDS_POINT_THERMOSTAT``) le nœud ponctuel historique
        (centre_x, largeur/2, interface) et la MOYENNE de T sur toute la coupe
        transverse en y du spot actif (x=centre_x, tout y, z=interface en 3D
        / T EST déjà le champ d'interface en 2D) :

            T_ctrl = p·T_point + (1-p)·T_moyenne_section,  p = POIDS_POINT_THERMOSTAT

        Pourquoi ni l'un ni l'autre seul : le nœud ponctuel coïncide avec le
        plan de symétrie y=largeur/2 du hairpin, où la dissipation Joule a un
        zéro quasi exact (cf. identification/calibration.py, découverte agent
        EM 2026-07-18) ; il ne "voit" un dépassement de consigne QUE par
        conduction latérale retardée depuis les zones bien plus chauffées du
        même spot (jusqu'à ~60-80x plus de puissance locale à quelques mm en
        y) — longtemps après que l'essentiel de l'excès d'énergie a déjà été
        déposé ailleurs dans l'empreinte, INDÉPENDAMMENT de la largeur de la
        sigmoïde (vérifié : resserrer ``LARGEUR_THERMOSTAT_C`` seule, de 2 à
        0,05 °C, sur le SEUL nœud ponctuel change les pics simulés de <1 °C).
        À l'inverse, asservir sur la moyenne (ou pire, le maximum) de la
        section coupe la source dès qu'une petite zone très locale s'échauffe
        et SOUS-chauffe massivement les autres essais (testé : moyenne pure
        -50 à -85 °C, maximum pur -60 à -160 °C vs mesures). Le mélange à
        ``POIDS_POINT_THERMOSTAT`` (calibré par balayage sur les 3 essais de
        validation croisée, cf. constante) réduit le dépassement des essais
        250 A de +60/+120 °C à des écarts de quelques °C à quelques dizaines
        de °C, sans dégrader (au contraire, améliore) le bon accord de
        serieA_A-3 — cf. rapport de vérification thermal-solver-engineer
        2026-07-20.

        Si ``thermostat_capteurs`` est actif (cf. __init__), on court-circuite ce
        mélange point/section et on renvoie le MAX de T aux positions TC réelles
        (loi 'capteurs', ``_T_ctrl_capteurs``).
        """
        if self.thermostat_capteurs:
            return self._T_ctrl_capteurs(T, deux_d)
        ix0, ix1, wx = self._colonnes_ctrl(float(spot["centre_x"]))
        iy_point = self.grille.indice_xy(0.0, self.grille.largeur / 2.0)[1]
        if deux_d:
            T_point = (1.0 - wx) * T[ix0, iy_point] + wx * T[ix1, iy_point]
            T_moyenne = (1.0 - wx) * T[ix0, :].mean() + wx * T[ix1, :].mean()
        else:
            T_point = ((1.0 - wx) * T[ix0, iy_point, self.grille.iz_interface]
                       + wx * T[ix1, iy_point, self.grille.iz_interface])
            T_moyenne = ((1.0 - wx) * T[ix0, :, self.grille.iz_interface].mean()
                         + wx * T[ix1, :, self.grille.iz_interface].mean())
        return POIDS_POINT_THERMOSTAT * T_point + (1.0 - POIDS_POINT_THERMOSTAT) * T_moyenne

    def source_fn(self, t: float, T: np.ndarray | None = None) -> np.ndarray:
        """Source volumique au temps t, éventuellement asservie à la température.

        Si l'essai déclare ``consigne_interface`` (°C), la source est modulée
        par un thermostat lisse : facteur = 1/(1+exp((T_ctrl−consigne)/LARGEUR)),
        cf. ``LARGEUR_THERMOSTAT_C``. C'est le comportement réel du procédé
        (« chauffe à I jusqu'à T_processing », coupure sur consigne — fiches
        Séries A/B, B-2 à 360 °C) : sans cet asservissement, appliquer I
        pendant toute la fenêtre d'impulsion fait diverger la température
        (validation du 2026-07-18 : ~1000 °C simulés vs ~400 °C mesurés).
        ``T_ctrl`` : cf. ``_T_ctrl``.
        """
        i = self._spot_actif(t)
        if i is None:
            return self._Q_nul
        Q = self._Q_spots[i]
        consigne = self.spec.get("consigne_interface")
        if consigne is not None and T is not None:
            T_ctrl = self._T_ctrl(T, self.spots[i], deux_d=False)
            Q = Q / (1.0 + np.exp((T_ctrl - float(consigne)) / LARGEUR_THERMOSTAT_C))
        return Q

    def source_fn_2d(self, t: float, T: np.ndarray | None = None) -> np.ndarray:
        """Source surfacique 2D (W/m², cf. thermique/solveur2d.py) au temps t.

        Miroir de ``source_fn`` pour le modèle lumpé : même thermostat de
        consigne (même ``T_ctrl``, cf. ``_T_ctrl``), mais ``T`` est le champ
        (nx, ny) d'interface (pas besoin de ``iz_interface``, la maille EST
        l'interface) et ``P`` est en W/m² (pas W/m³ — la conversion volumique
        se fait dans ``SolveurThermique2D``).
        """
        i = self._spot_actif(t)
        if i is None:
            return self._P_nul_2d
        P = self._P_spots_2d[i]
        consigne = self.spec.get("consigne_interface")
        if consigne is not None and T is not None:
            T_ctrl = self._T_ctrl(T, self.spots[i], deux_d=True)
            P = P / (1.0 + np.exp((T_ctrl - float(consigne)) / LARGEUR_THERMOSTAT_C))
        return P

    def masque_fn(self, t: float) -> np.ndarray:
        i = self._spot_actif(t)
        if i is None:
            # avant/après les passes : dernier spot pressé (refroidissement sous pression)
            i = 0 if t < float(self.spots[0]["t_debut"]) else len(self.spots) - 1
        return self._masques[i]

    # ------------------------------------------------------------------
    def simuler(self, dt_sortie: float = 1.0, modele: str = "3D",
                emissivite_face: float = 0.0, **kwargs):
        """Simule l'essai. ``modele`` : "3D" (défaut, API historique inchangée,
        résolution complète dans l'épaisseur) ou "2D" (lumpé à l'interface,
        cf. ``thermique/solveur2d.py`` — ~10x plus rapide, TC surface/opposée
        non représentables, cf. ``series_tc``).

        ``emissivite_face`` (défaut 0.0 = OFF, bit-à-bit) : rayonnement T⁴ de la
        face haut exposée, mode 2D uniquement (cf. ``SolveurThermique2D`` ; issue
        #68). Ignoré en 3D."""
        duree = float(self.spec.get("duree_totale", self.spec["duree_chauffe"]))
        t_eval = np.arange(0.0, duree + dt_sortie / 2, dt_sortie)
        if modele == "3D":
            solveur = SolveurThermique3D(
                self.grille, self.cfg.materiau, self.cfg.ambiant, self.cfg.contact,
                masque_ceramique=self.masque_fn,
            )
            kwargs.setdefault("noeuds_controle", self._noeuds_controle or None)
            sol = solveur.simuler(self.source_fn, (0.0, duree), t_eval=t_eval, **kwargs)
        elif modele == "2D":
            solveur = SolveurThermique2D(
                self.grille, self.cfg.materiau, self.cfg.ambiant, self.cfg.contact,
                masque_ceramique=self.masque_fn, emissivite_face=emissivite_face,
            )
            kwargs.setdefault("noeuds_controle", self._noeuds_controle_2d or None)
            sol = solveur.simuler(self.source_fn_2d, (0.0, duree), t_eval=t_eval, **kwargs)
        else:
            raise ValueError(f"modele={modele!r} inconnu (attendu '3D' ou '2D')")
        return solveur, sol

    # ------------------------------------------------------------------
    def series_tc(self, solveur, sol) -> dict[str, np.ndarray]:
        """Séries temporelles simulées aux positions des thermocouples.

        En mode 2D (``solveur`` est un ``SolveurThermique2D``), les TC
        ``z: surface``/``z: opposee`` ne sont pas représentables (une seule
        maille dans l'épaisseur) et sont silencieusement EXCLUS du résultat
        (cf. docstring ``thermique/solveur2d.py``) — pour ``chauffe_250A_3TC``
        seul TC2 (interface) reste exploitable en 2D.
        """
        series = {}
        est_2d = isinstance(solveur, SolveurThermique2D)
        for nom, pos in self.spec.get("thermocouples", {}).items():
            if est_2d:
                if pos["z"] != "interface":
                    continue
                series[nom] = solveur.serie_temporelle(sol, float(pos["x"]), float(pos["y"]))
            else:
                series[nom] = solveur.serie_temporelle(sol, float(pos["x"]), float(pos["y"]), pos["z"])
        return series

    @property
    def fichier_mesures(self) -> Path:
        return self.racine / self.spec["fichier_mesures"]
