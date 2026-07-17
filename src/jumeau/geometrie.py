"""Construction de la scène : grille thermique, couches conductrices, bobine, CFC."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .materiaux import Config
from .thermique.solveur3d import Grille3D


@dataclass
class CoucheConductrice:
    """Couche plane porteuse de courants de Foucault (repère grille, z vers le bas)."""

    nom: str
    z_min: float
    z_max: float
    rho_xx: float              # résistivité plan, Ω·m (1/σ)
    rho_yy: float

    @property
    def z_mid(self) -> float:
        return 0.5 * (self.z_min + self.z_max)

    @property
    def epaisseur(self) -> float:
        return self.z_max - self.z_min


def construire_grille(cfg: Config, nx: int = 49, ny: int = 17, nz: int = 15) -> Grille3D:
    lam = cfg.geometrie["laminate"]
    ep_total = lam["epaisseur_sup"] + lam["epaisseur_film"] + lam["epaisseur_inf"]
    return Grille3D(
        longueur=lam["longueur"], largeur=lam["largeur"],
        epaisseur=ep_total, z_interface=lam["epaisseur_sup"],
        nx=nx, ny=ny, nz=nz,
    )


def construire_couches(cfg: Config) -> list[CoucheConductrice]:
    """Couches EM : twill suscepteur à l'interface + les deux laminés homogénéisés.

    Laminé quasi-iso [45/-45/0/90]3s : les boucles de courant de Foucault ont
    besoin d'un trajet aller ET retour ; dans un empilement croisé le retour
    passe par les plis transverses / contacts inter-plis, si bien que la
    conductivité de boucle effective est bien plus basse que la moyenne
    arithmétique des plis. On prend la moyenne géométrique √(σ0·σ90) ≈ 273 S/m
    (compromis d'homogénéisation classique ; cohérent avec le tissé-suscepteur
    qui domine la chauffe, Série A, et avec Grouve 2020 — sensibilité faible à
    σ90). Le twill (tissé, boucles fermées natives) garde σ_plan élevé.
    """
    lam = cfg.geometrie["laminate"]
    m = cfg.materiau
    sigma_eff = float(np.sqrt(m.sigma_0 * m.sigma_90))
    rho_lam = 1.0 / sigma_eff

    t_twill = float(cfg.twill.get("epaisseur", 0.00028))
    rho_twill = 1.0 / float(cfg.twill.get("sigma_plan", 1.1e4))

    ep_sup = lam["epaisseur_sup"]
    ep_film = lam["epaisseur_film"]
    ep_inf = lam["epaisseur_inf"]

    return [
        # le twill est le dernier pli du laminé sup, à l'interface de soudure
        CoucheConductrice("twill_suscepteur", ep_sup - t_twill, ep_sup, rho_twill, rho_twill),
        CoucheConductrice("lamine_sup", 0.0, ep_sup - t_twill, rho_lam, rho_lam),
        CoucheConductrice("lamine_inf", ep_sup + ep_film, ep_sup + ep_film + ep_inf, rho_lam, rho_lam),
    ]


def sommets_bobine(cfg: Config, centre_x: float, centre_y: float | None = None) -> np.ndarray:
    from .em.champ_coil import sommets_hairpin

    c = cfg.geometrie["coil"]
    lam = cfg.geometrie["laminate"]
    if centre_y is None:
        centre_y = lam["largeur"] / 2.0
    return sommets_hairpin(
        longueur_jambe=c["longueur_jambe"], entraxe=c["entraxe_jambes"],
        hauteur=c["hauteur"], centre_x=centre_x, centre_y=centre_y,
        orientation=c.get("orientation", "x"),
    )


def plan_miroir_cfc(cfg: Config) -> float:
    """Altitude du plan image du CFC (face inférieure du bloc, ~sommet du tube)."""
    c = cfg.geometrie["coil"]
    return c["hauteur"] + c["rayon_tube"]


def masque_empreinte_cfc(grille: Grille3D, cfg: Config, centre_x: float,
                         centre_y: float | None = None) -> np.ndarray:
    """Masque bool (nx, ny) de l'empreinte CFC posée au spot ``centre_x``."""
    cfc = cfg.geometrie["cfc"]
    if centre_y is None:
        centre_y = grille.largeur / 2.0
    X, Y = np.meshgrid(grille.x, grille.y, indexing="ij")
    # orientation à confirmer (cahier §1.2.3) : ici 'largeur' CFC le long de x
    demi_x = cfc["largeur"] / 2.0
    demi_y = cfc["longueur"] / 2.0
    return (np.abs(X - centre_x) <= demi_x) & (np.abs(Y - centre_y) <= demi_y)
