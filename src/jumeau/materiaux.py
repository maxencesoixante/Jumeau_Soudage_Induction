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

    @classmethod
    def depuis_config(cls, cfg: dict) -> "Materiau":
        # float() : PyYAML lit "2.2e4" (exposant non signé) comme une chaîne
        champs = {k: float(cfg[k]) for k in (
            "densite", "cp_base", "T_fusion", "delta_T_fusion", "chaleur_latente",
            "k_plan", "k_z", "emissivite", "sigma_0", "sigma_90", "sigma_z", "T_glass",
        ) if k in cfg}
        return cls(**champs)

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


@dataclass
class Ambiant:
    T_amb: float = 20.0
    h_convection: float = 15.0
    h_bas: float = 15.0
    stefan_boltzmann: float = 5.67e-8


@dataclass
class ContactCeramique:
    """Puits thermique côté bobine : céramique -> concentrateur refroidi.

    O'Shaughnessey 2014 : bobine + concentrateur refroidis à l'eau, fixés à
    20 °C dans le modèle COMSOL ; ici modélisé par une conductance h_contact
    vers T_puits, appliquée sous l'empreinte de la céramique/CFC.
    """

    h_contact: float = 50.0
    T_puits: float = 20.0


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
            ambiant=Ambiant(**{k: amb[k] for k in ("T_amb", "h_convection", "h_bas", "stefan_boltzmann") if k in amb}),
            contact=ContactCeramique(**{k: cer[k] for k in ("h_contact", "T_puits") if k in cer}),
            twill=mat_cfg.get("twill_suscepteur", {}),
            geometrie=geo_cfg,
        )
