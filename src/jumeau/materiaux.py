"""Propriétés matériaux et chargement des configs YAML.

cp apparent avec pic de fusion gaussien : porté tel quel du notebook 1D
``MAX_InductionNumerical_1_12mm.ipynb`` (équation validée par le test
black-box, Samanis et al. 2026 §2.3).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml


def charger_yaml(chemin: str | Path) -> dict:
    with open(chemin, encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass
class Materiau:
    """Laminé CF/PEKK homogénéisé (thermique) + propriétés du pic de fusion."""

    densite: float
    cp_base: float
    T_fusion: float
    delta_T_fusion: float
    chaleur_latente: float
    k_plan: float
    k_z: float
    emissivite: float
    sigma_0: float = 0.0
    sigma_90: float = 0.0
    sigma_z: float = 0.0
    T_glass: float = 159.0
    # Conductivité in-plane ANISOTROPE (kx != ky), prototype 2026-07-31
    # (mission thermal-solver-engineer — dernier levier du résidu « M »/
    # centre-fill, cf. docs/modele/README.md § État & résidu ouvert). ``None``
    # (défaut) => isotrope, ``kx = ky = k_plan`` : comportement STRICTEMENT
    # inchangé tant que ces deux champs ne sont pas renseignés explicitement
    # (config YAML optionnelle ou réglage runtime par
    # ``scripts/calibrer_joint.py``). Ne PAS renseigner par défaut dans
    # ``config/materiaux.yaml`` — cf. mission : flag OFF par défaut, verdict
    # d'adoption laissé à l'orchestrateur.
    k_plan_x: float | None = None
    k_plan_y: float | None = None

    @classmethod
    def depuis_config(cls, cfg: dict) -> "Materiau":
        # float() : PyYAML lit "2.2e4" (exposant non signé) comme une chaîne
        champs = {k: float(cfg[k]) for k in (
            "densite", "cp_base", "T_fusion", "delta_T_fusion", "chaleur_latente",
            "k_plan", "k_z", "emissivite", "sigma_0", "sigma_90", "sigma_z", "T_glass",
            "k_plan_x", "k_plan_y",
        ) if k in cfg}
        return cls(**champs)

    def k_plan_xy(self) -> tuple[float, float]:
        """(kx, ky) in-plane — isotrope par défaut (``k_plan_x``/``k_plan_y``
        non renseignés => renvoie ``(k_plan, k_plan)``, comportement
        historique bit-identique). Utilisé par
        ``thermique.solveur2d.SolveurThermique2D`` pour séparer les flux de
        conduction en x (longueur, dissipation longitudinale) et en y
        (largeur, profil « M ») — cf. docs/modele/README.md § résidu ouvert,
        option (A) anisotropie."""
        kx = self.k_plan_x if self.k_plan_x is not None else self.k_plan
        ky = self.k_plan_y if self.k_plan_y is not None else self.k_plan
        return float(kx), float(ky)

    def cp_apparent(self, T: np.ndarray) -> np.ndarray:
        """Capacité thermique effective incluant la chaleur latente de fusion.

        cp_app(T) = cp_base + (L_f / (σ_f·√(2π))) · exp(-((T-Tf)/σ_f)²/2)
        avec σ_f = delta_T_fusion / 2 (identique au notebook 1D).
        """
        sig_f = self.delta_T_fusion / 2.0
        pic = (self.chaleur_latente / (sig_f * np.sqrt(2.0 * np.pi))) * np.exp(
            -0.5 * ((T - self.T_fusion) / sig_f) ** 2
        )
        return self.cp_base + pic

    def degre_de_fusion(self, T: np.ndarray) -> np.ndarray:
        """Degré de fusion quasi-statique Xm(T) ∈ [0, 1].

        Intégrale normalisée du pic gaussien de fusion du cp apparent
        (le pic représente dH_fusion/dT, donc Xm = H(T)/H_mTOT — même
        définition que l'éq. 8 de Lionetto et al. 2017, la distribution
        statistique de températures de fusion étant ici une gaussienne) :
            Xm(T) = Φ((T − Tf)/σ_f) = ½·[1 + erf((T − Tf)/(σ_f·√2))]
        Quasi-statique : sur un refroidissement, Xm redescend à l'équilibre
        (la cinétique de cristallisation type Ozawa n'est pas modélisée).
        """
        from scipy.special import erf

        sig_f = self.delta_T_fusion / 2.0
        return 0.5 * (1.0 + erf((np.asarray(T, float) - self.T_fusion) / (sig_f * np.sqrt(2.0))))


@dataclass
class Ambiant:
    T_amb: float = 20.0
    h_convection: float = 15.0
    h_bas: float = 15.0
    stefan_boltzmann: float = 5.67e-8
    # Perte effective face inférieure/ambiant du modèle 2D LUMPÉ dans
    # l'épaisseur (solveur2d.SolveurThermique2D) — distincte de ``h_bas``
    # (coefficient de convection de surface du modèle 3D résolu en z).
    # Ici ``h_bas_2d`` absorbe, en un seul coefficient, tout ce que le 3D
    # sépare en convection+rayonnement face inférieure ET conduction à
    # travers le demi-stack inférieur (le modèle 2D n'a plus de résolution
    # en z pour ces deux effets) : ne pas la confondre avec ``h_bas`` ni la
    # réutiliser telle quelle sur le 3D. Défaut = point de départ hérité de
    # la dernière calibration 3D de ``h_bas`` sur chauffe_250A_3TC
    # (facteur_couplage=5.2189, decalage_x=0.015, h_contact=5.0 ->
    # h_bas=50.919, cf. scripts/calibrer.py docstring) : un ordre de
    # grandeur raisonnable pour démarrer une calibration 2D dédiée, PAS une
    # valeur calibrée pour ce modèle réduit. Borne suggérée pour la
    # calibration à venir : [2, 300] W/m².K (même enveloppe que le 3D).
    h_bas_2d: float = 50.919
    # Puits de chaleur ADDITIONNEL au chant x=0 SEUL du modèle 2D lumpé
    # (solveur2d.SolveurThermique2D), en plus de la convection/rayonnement de
    # chant déjà présente. Représente le bridage/appui conductif du montage
    # sur le bord x=0 (confirmé asymétrique par l'utilisateur 2026-07-20 : le
    # bord x=0 est en appui, pas x=L) — que le modèle lumpé, réduit au plan de
    # l'interface, ne peut pas capturer autrement. Sans lui, la chaleur du
    # spot 1 (à ~16 mm du bord) reste piégée contre le chant quasi-adiabatique
    # et TC1 (centre de largeur, x=0) surchauffe de +185 à +273 °C au pic.
    # Défaut 0.0 = comportement historique STRICTEMENT inchangé. Actif
    # uniquement sur x=0 (appliquer sur les 4 chants dégrade TC2-5 à y=0 ;
    # cf. prototype thermal-solver-engineer 2026-07-20). Borne de calibration
    # suggérée : [150, 300] W/m².K.
    h_bord_x0: float = 0.0


@dataclass
class ContactCeramique:
    """Puits thermique côté bobine : céramique -> concentrateur refroidi.

    O'Shaughnessey 2014 : bobine + concentrateur refroidis à l'eau, fixés à
    20 °C dans le modèle COMSOL ; ici modélisé par une conductance h_contact
    vers T_puits, appliquée sous l'empreinte de la céramique/MFC.
    """

    h_contact: float = 50.0
    T_puits: float = 20.0
    # Conductance effective TOP du modèle 2D lumpé dans l'épaisseur
    # (solveur2d.SolveurThermique2D), sous l'empreinte céramique/MFC active
    # (même masque que h_contact en 3D) — remplace le rôle de h_contact,
    # mais représente maintenant la conduction à travers TOUT le demi-stack
    # supérieur (laminé sup + twill) vers le puits, plus la conductance de
    # contact elle-même, puisque le 2D n'a plus de nœuds z pour résoudre
    # cette conduction séparément. NOUVEAU paramètre (2026-07-20), destiné à
    # être calibré indépendamment de h_contact. Défaut = point de départ
    # hérité de la dernière calibration 3D de h_contact sur chauffe_250A_3TC
    # (h_contact=5.0, cf. scripts/calibrer.py docstring), à recalibrer pour
    # le modèle 2D. Borne suggérée : [1, 50] W/m².K (même enveloppe que
    # h_contact en 3D).
    h_haut: float = 5.0


@dataclass
class Config:
    """Config agrégée (materiaux.yaml + geometrie.yaml)."""

    materiau: Materiau
    ambiant: Ambiant
    contact: ContactCeramique
    twill: dict = field(default_factory=dict)
    geometrie: dict = field(default_factory=dict)

    @classmethod
    def charger(cls, dossier_config: str | Path) -> "Config":
        d = Path(dossier_config)
        mat_cfg = charger_yaml(d / "materiaux.yaml")
        geo_cfg = charger_yaml(d / "geometrie.yaml")
        amb = mat_cfg.get("ambiant", {})
        cer = mat_cfg.get("ceramique", {})
        return cls(
            materiau=Materiau.depuis_config(mat_cfg["cf_pekk"]),
            ambiant=Ambiant(**{k: amb[k] for k in
                               ("T_amb", "h_convection", "h_bas", "stefan_boltzmann",
                                "h_bas_2d", "h_bord_x0")
                               if k in amb}),
            contact=ContactCeramique(**{k: cer[k] for k in ("h_contact", "T_puits", "h_haut") if k in cer}),
            twill=mat_cfg.get("twill_suscepteur", {}),
            geometrie=geo_cfg,
        )
