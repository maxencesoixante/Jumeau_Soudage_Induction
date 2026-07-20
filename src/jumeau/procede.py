"""Orchestration d'un essai : passes séquentielles (4 empreintes), source et masque.

Un essai (config/essais/*.yaml) définit une liste de ``spots`` avec fenêtres
temporelles. La source Joule de chaque spot est précalculée une fois (le champ
EM est quasi statique à l'échelle thermique) puis activée par morceaux ;
le masque céramique/CFC suit le spot actif (le concentrateur n'appuie que là).
Après la dernière passe, la source s'éteint (refroidissement) et le masque du
dernier spot est conservé (refroidissement sous pression, cf. fiches A/B).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .geometrie import construire_couches, construire_grille, masque_empreinte_cfc
from .materiaux import Config, charger_yaml
from .em.source_joule import source_spot
from .thermique.solveur3d import Grille3D, SolveurThermique3D


class Essai:
    """Charge un YAML d'essai et construit source_fn / masque_fn / solveur."""

    def __init__(self, cfg: Config, chemin_essai: str | Path,
                 nx: int = 49, ny: int = 17, nz: int = 15,
                 facteur_couplage: float = 1.0,
                 decalage_x: float | None = None,
                 racine: str | Path | None = None):
        self.cfg = cfg
        self.spec = charger_yaml(chemin_essai)
        self.racine = Path(racine) if racine else Path(chemin_essai).resolve().parents[2]
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

        courant = float(self.spec["courant"])
        self.spots = self.spec["spots"]
        self._Q_spots = [
            source_spot(self.grille, cfg, self.couches, courant,
                        float(s["centre_x"]), facteur_couplage=facteur_couplage,
                        decalage_x=self.decalage_x)
            for s in self.spots
        ]
        self._masques = [
            masque_empreinte_cfc(self.grille, cfg, float(s["centre_x"]))
            for s in self.spots
        ]
        self._Q_nul = np.zeros_like(self._Q_spots[0])
        # nœuds de contrôle du thermostat (asservissement de source_fn à T),
        # un par spot (centre_x, y=largeur/2, z=interface) — cf. source_fn.
        # Union transmise au solveur pour que le jacobien creux couvre le
        # couplage source<->T_controle (sinon les FD groupées par couleur de
        # scipy ne l'évaluent jamais -> BDF rampe près de la consigne).
        self._noeuds_controle: list[tuple[int, int, int]] = []
        if self.spec.get("consigne_interface") is not None:
            iy_ctrl = self.grille.indice_xy(0.0, self.grille.largeur / 2.0)[1]
            noeuds = {
                (self.grille.indice_xy(float(s["centre_x"]), self.grille.largeur / 2.0)[0],
                 iy_ctrl, self.grille.iz_interface)
                for s in self.spots
            }
            self._noeuds_controle = sorted(noeuds)

    # ------------------------------------------------------------------
    def _spot_actif(self, t: float) -> int | None:
        for i, s in enumerate(self.spots):
            if float(s["t_debut"]) <= t < float(s["t_fin"]):
                return i
        return None

    def source_fn(self, t: float, T: np.ndarray | None = None) -> np.ndarray:
        """Source volumique au temps t, éventuellement asservie à la température.

        Si l'essai déclare ``consigne_interface`` (°C), la source est modulée
        par un thermostat lisse sur la température d'interface au centre du
        spot actif : facteur = 1/(1+exp((T_ctrl−consigne)/2)). C'est le
        comportement réel du procédé (« chauffe à I jusqu'à T_processing »,
        coupure sur consigne — fiches Séries A/B, B-2 à 360 °C) : sans cet
        asservissement, appliquer I pendant toute la fenêtre d'impulsion fait
        diverger la température (validation du 2026-07-18 : ~1000 °C simulés
        vs ~400 °C mesurés).
        """
        i = self._spot_actif(t)
        if i is None:
            return self._Q_nul
        Q = self._Q_spots[i]
        consigne = self.spec.get("consigne_interface")
        if consigne is not None and T is not None:
            ix, iy = self.grille.indice_xy(float(self.spots[i]["centre_x"]),
                                           self.grille.largeur / 2.0)
            T_ctrl = T[ix, iy, self.grille.iz_interface]
            Q = Q / (1.0 + np.exp((T_ctrl - float(consigne)) / 2.0))
        return Q

    def masque_fn(self, t: float) -> np.ndarray:
        i = self._spot_actif(t)
        if i is None:
            # avant/après les passes : dernier spot pressé (refroidissement sous pression)
            i = 0 if t < float(self.spots[0]["t_debut"]) else len(self.spots) - 1
        return self._masques[i]

    # ------------------------------------------------------------------
    def simuler(self, dt_sortie: float = 1.0, **kwargs):
        duree = float(self.spec.get("duree_totale", self.spec["duree_chauffe"]))
        t_eval = np.arange(0.0, duree + dt_sortie / 2, dt_sortie)
        solveur = SolveurThermique3D(
            self.grille, self.cfg.materiau, self.cfg.ambiant, self.cfg.contact,
            masque_ceramique=self.masque_fn,
        )
        kwargs.setdefault("noeuds_controle", self._noeuds_controle or None)
        sol = solveur.simuler(self.source_fn, (0.0, duree), t_eval=t_eval, **kwargs)
        return solveur, sol

    # ------------------------------------------------------------------
    def series_tc(self, solveur: SolveurThermique3D, sol) -> dict[str, np.ndarray]:
        """Séries temporelles simulées aux positions des thermocouples."""
        series = {}
        for nom, pos in self.spec.get("thermocouples", {}).items():
            series[nom] = solveur.serie_temporelle(sol, float(pos["x"]), float(pos["y"]), pos["z"])
        return series

    @property
    def fichier_mesures(self) -> Path:
        return self.racine / self.spec["fichier_mesures"]
