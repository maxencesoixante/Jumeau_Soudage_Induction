"""Assemblage de la source Joule volumique Q(x, y, z) pour une position de spot.

Chaîne par couche conductrice (twill, laminé sup, laminé inf) :
1. Bz RMS (Biot-Savart bobine + image CFC), échantillonné à CHAQUE nœud z de
   la grille thermique compris dans la couche (et non plus une seule fois au
   plan médian, cf. « limites » ci-dessous) — l'atténuation géométrique est
   portée par la distance à la bobine, et le blindage par les couches
   conductrices traversées est appliqué comme un facteur d'effet de peau
   e^(−2·t/δ) par couche écran (équivalent du r_I ≈ 2/δ du modèle 1D, remède
   ③ du test black-box) ;
2. fonction de courant ψ (foucault.resoudre_psi) avec le tenseur ρ de la
   couche, résolue séparément à chaque z échantillonné ;
3. dissipation q(x, y) = ρxx·Jx² + ρyy·Jy² (W/m³) à chaque z échantillonné ;
4. dépôt sur les nœuds z retenus, chacun recevant le q calculé à SA propre
   profondeur (une couche plus fine que dz est concentrée sur le nœud le
   plus proche, pondérée t/dz — le plan médian y est un choix par défaut
   raisonnable puisqu'il n'y a alors qu'un seul nœud).

Limite corrigée (2026-07-18, chute de pente aux essais 250 A) : les couches
homogénéisées (laminé sup/inf, ~3,1-3,4 mm) couvrent plusieurs nœuds z de la
grille thermique alors que Bz décroît d'un facteur ~2 entre leur face côté
bobine et leur face côté interface (la bobine est à ~9 mm de la surface,
comparable à l'épaisseur du laminé — l'hypothèse « Bz uniforme dans
l'épaisseur de la couche », valable pour le twill fin, ne l'est PAS pour ces
couches épaisses). Calculer Bz/ψ/q une seule fois au plan médian et le
recopier sur tous les nœuds de la couche aplatissait artificiellement le
profil de chauffe dans l'épaisseur (la face côté bobine était sous-chauffée,
la face côté interface sur-chauffée) — cause principale des taux de chauffe
simulés ~3× trop lents aux thermocouples de surface/interface malgré un
facteur_couplage calibré sur l'essai. L'échantillonnage nœud-par-nœud
supprime cette hypothèse en trop, sans paramètre libre supplémentaire (la
résolution est celle, déjà choisie, de la grille thermique).

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
    decalage_x: float = 0.0,
) -> np.ndarray:
    """Champ source Q (nx, ny, nz) en W/m³ pour la bobine centrée en ``centre_x``.

    ``decalage_x`` (m) décale le centre EFFECTIF de la bobine par rapport au
    ``centre_x`` nominal du spot (incertitude de positionnement bobine/CFC au
    montage, cf. geometrie.yaml:coil.decalage_x). Seule la bobine bouge : le
    masque céramique/CFC (masque_empreinte_cfc) reste posé à ``centre_x`` —
    c'est un décalage bobine<->reste du montage, pas un déplacement du spot.
    """
    omega = 2.0 * np.pi * float(cfg.geometrie["generateur"]["frequence"])
    mu_r = float(cfg.geometrie["cfc"]["mu_r"])
    z_miroir = plan_miroir_cfc(cfg)
    sommets = sommets_bobine(cfg, centre_x + decalage_x)
    X, Y = np.meshgrid(grille.x, grille.y, indexing="ij")

    Q = np.zeros((grille.nx, grille.ny, grille.nz))
    for couche in couches:
        att = attenuation_blindage(couche, couches, omega)

        iz = np.where((grille.z >= couche.z_min - 1e-12) & (grille.z <= couche.z_max + 1e-12))[0]
        if len(iz) == 0:
            iz = np.array([grille.indice_z(couche.z_mid)])
        # conservation de la puissance surfacique q·t sur les nœuds retenus
        poids = couche.epaisseur / (len(iz) * grille.dz)

        # Bz (et donc ψ, q) est échantillonné à la profondeur propre de
        # chaque nœud retenu plutôt qu'une seule fois au plan médian : une
        # couche homogénéisée épaisse (laminé sup/inf) peut couvrir plusieurs
        # nœuds sur lesquels Bz varie significativement (cf. docstring module).
        for k in iz:
            z_k = grille.z[k] if len(iz) > 1 else couche.z_mid
            Bz = bz_plan(sommets, courant, X, Y, z_plan=-z_k,
                        mu_r_cfc=mu_r, z_miroir=z_miroir)
            psi = resoudre_psi(Bz, grille.dx, grille.dy,
                               couche.rho_xx, couche.rho_yy, omega)
            q = densite_joule(psi, grille.dx, grille.dy, couche.rho_xx, couche.rho_yy)
            Q[:, :, k] += q * att * poids

    return facteur_couplage * Q
