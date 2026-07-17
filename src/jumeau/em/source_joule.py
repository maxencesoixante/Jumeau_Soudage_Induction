"""Assemblage de la source Joule volumique Q(x, y, z) pour une position de spot.

Chaîne par couche conductrice (twill, laminé sup, laminé inf) :
1. Bz RMS au plan médian de la couche (Biot-Savart bobine + image CFC) —
   l'atténuation géométrique est portée par la distance à la bobine, et le
   blindage par les couches conductrices traversées est appliqué comme un
   facteur d'effet de peau e^(−2·t/δ) par couche écran (équivalent du
   r_I ≈ 2/δ du modèle 1D, remède ③ du test black-box) ;
2. fonction de courant ψ (foucault.resoudre_psi) avec le tenseur ρ de la couche ;
3. dissipation q(x, y) = ρxx·Jx² + ρyy·Jy² (W/m³) ;
4. dépôt sur les nœuds z de la couche avec conservation de la puissance
   surfacique q·t (une couche plus fine que dz est concentrée sur le nœud
   le plus proche, pondérée t/dz).

Le ``facteur_couplage`` (calibré) absorbe le blindage négligé, les contacts
fibre-fibre et l'incertitude sur σ — c'est le seul facteur d'échelle libre de
la source (la fréquence est FIGÉE à sa valeur nominale : sans mesure de f,
elle serait totalement corrélée au facteur d'échelle — leçon du test
black-box sur l'identifiabilité f_I/r_I).
"""

from __future__ import annotations

import numpy as np

from ..geometrie import CoucheConductrice, plan_miroir_cfc, sommets_bobine
from ..materiaux import Config
from ..thermique.solveur3d import Grille3D
from .champ_coil import MU0, bz_plan
from .foucault import densite_joule, resoudre_psi


def attenuation_blindage(couche: CoucheConductrice,
                         couches: list[CoucheConductrice], omega: float) -> float:
    """Facteur d'atténuation de puissance dû aux couches conductrices situées
    au-dessus de ``couche`` : produit des e^(−2·t/δ) avec δ = √(2ρ/µ0ω)."""
    att = 1.0
    for ecran in couches:
        if ecran is couche or ecran.z_max > couche.z_min + 1e-9:
            continue
        rho_moy = 0.5 * (ecran.rho_xx + ecran.rho_yy)
        delta = np.sqrt(2.0 * rho_moy / (MU0 * omega))
        att *= float(np.exp(-2.0 * ecran.epaisseur / delta))
    return att


def source_spot(
    grille: Grille3D,
    cfg: Config,
    couches: list[CoucheConductrice],
    courant: float,
    centre_x: float,
    facteur_couplage: float = 1.0,
) -> np.ndarray:
    """Champ source Q (nx, ny, nz) en W/m³ pour la bobine centrée en ``centre_x``."""
    omega = 2.0 * np.pi * float(cfg.geometrie["generateur"]["frequence"])
    mu_r = float(cfg.geometrie["cfc"]["mu_r"])
    z_miroir = plan_miroir_cfc(cfg)
    sommets = sommets_bobine(cfg, centre_x)
    X, Y = np.meshgrid(grille.x, grille.y, indexing="ij")

    Q = np.zeros((grille.nx, grille.ny, grille.nz))
    for couche in couches:
        # plan d'observation : profondeur z_mid sous la surface => altitude -z_mid
        Bz = bz_plan(sommets, courant, X, Y, z_plan=-couche.z_mid,
                     mu_r_cfc=mu_r, z_miroir=z_miroir)
        psi = resoudre_psi(Bz, grille.dx, grille.dy,
                           couche.rho_xx, couche.rho_yy, omega)
        q = densite_joule(psi, grille.dx, grille.dy, couche.rho_xx, couche.rho_yy)
        q = q * attenuation_blindage(couche, couches, omega)

        iz = np.where((grille.z >= couche.z_min - 1e-12) & (grille.z <= couche.z_max + 1e-12))[0]
        if len(iz) == 0:
            iz = np.array([grille.indice_z(couche.z_mid)])
        # conservation de la puissance surfacique q·t sur les nœuds retenus
        poids = couche.epaisseur / (len(iz) * grille.dz)
        for k in iz:
            Q[:, :, k] += q * poids

    return facteur_couplage * Q
