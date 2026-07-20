"""Champ magnétique de la bobine hairpin par Biot-Savart (segments analytiques).

Champ d'un segment rectiligne fini a->b parcouru par un courant I, au point P :

    B = (µ0·I / 4π) · (û × r1) / |û × r1|² · (û·r̂1 − û·r̂2)

avec û le vecteur unitaire du segment, r1 = P−a, r2 = P−b. Vectorisé sur un
nuage de points d'observation. Vérifié contre la boucle circulaire analytique
(B_centre = µ0·I / 2R) dans les tests.

Le concentrateur de flux (CFC, Ferrotron 559H, µr≈16) est traité par la
méthode des courants images : chaque segment est réfléchi à travers le plan
inférieur du CFC avec un courant η·I, η = (µr−1)/(µr+1) ≈ 0,88. Cette
approximation de demi-espace perméable intensifie le champ sous l'empreinte —
elle capture l'effet de concentration au premier ordre, pas les effets de
bord exacts du bloc fini (hypothèse assumée, cf. README).

Auto-échauffement du CFC (Joule + hystérésis dans le Ferrotron 559H lui-même,
PAS modélisé ici) : vérifié 2026-07-20 et écarté. Le champ à l'intérieur d'un
demi-espace perméable adjacent au fil réel s'obtient par le même calcul
d'images que ci-dessus, mais avec un courant effectif image_int = 2·µr/(µr+1)·I
PLACÉ À LA POSITION RÉELLE de la bobine (pas au miroir), le champ résultant
étant alors évalué avec le champ_segments habituel (dérivation par
continuité de B_n/H_t à l'interface, cohérente par construction avec le
η=(µr−1)/(µr+1) ci-dessus — les deux proviennent de la même résolution des
conditions de raccord). Avec la courbe de pertes constructeur (Fluxtrol
*Ferrotron 559H* datasheet : µᵢ=16, ρ>15 kΩ·cm — "dielectric rather than
metallic composite" —, Pv=4,1·f¹·¹·B²·⁵ W/cm³, f en kHz, B crête en T), le
champ B dans le volume du CFC à 250 A/388 kHz reste très en-deçà de la
saturation (≈3–28 mT crête pour Bsat=0,9 T) et la puissance totale intégrée
sur tout le bloc (20,8 cm³) n'est que ≈0,6–1,4 W — 1 à 2 ordres de grandeur
sous ce qu'il faudrait pour expliquer le déficit de pente observé au
thermocouple TC1 (cf. README, § Limites connues). Conclusion : mécanisme
réel mais négligeable à cette échelle ; ne pas le réintroduire comme
explication du déficit TC1 sans nouvelle mesure (température du CFC lui-même,
absente des essais actuels).
"""

from __future__ import annotations

import numpy as np

MU0 = 4.0e-7 * np.pi


def champ_segments(points: np.ndarray, sommets: np.ndarray, courant: float) -> np.ndarray:
    """Champ B (T) d'une polyligne de courant aux points d'observation.

    points : (N, 3) ; sommets : (M, 3) — la polyligne parcourt sommets[0] ->
    sommets[-1] avec le courant ``courant`` (A). Renvoie (N, 3).
    """
    P = np.asarray(points, dtype=float)
    S = np.asarray(sommets, dtype=float)
    B = np.zeros_like(P)
    for a, b in zip(S[:-1], S[1:]):
        ab = b - a
        L = np.linalg.norm(ab)
        if L < 1e-12:
            continue
        u = ab / L
        r1 = P - a
        r2 = P - b
        d = np.cross(np.broadcast_to(u, r1.shape), r1)      # û × r1
        d2 = np.einsum("ij,ij->i", d, d)                    # |û × r1|²
        n1 = np.linalg.norm(r1, axis=1)
        n2 = np.linalg.norm(r2, axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            fac = (np.einsum("ij,j->i", r1, u) / n1 - np.einsum("ij,j->i", r2, u) / n2) / d2
        fac = np.where(d2 < 1e-18, 0.0, fac)                # sur l'axe du segment : B=0
        B += d * fac[:, None]
    return MU0 * courant / (4.0 * np.pi) * B


def sommets_hairpin(longueur_jambe: float, entraxe: float, hauteur: float,
                    centre_x: float = 0.0, centre_y: float = 0.0,
                    orientation: str = "x") -> np.ndarray:
    """Polyligne rectangulaire fermée approximant la bobine hairpin.

    Deux brins parallèles (longueur ``longueur_jambe``, séparés de ``entraxe``)
    + les deux retours d'extrémité, à l'altitude ``hauteur`` au-dessus de la
    surface du laminé (z=0, z pointant vers le bas dans la grille thermique ;
    ici z est l'altitude au-dessus de la surface, donc négatif dans le repère
    grille — on renvoie l'altitude positive et le solveur d'induction place
    le plan d'observation).
    """
    L, s, h = longueur_jambe, entraxe, hauteur
    if orientation == "x":
        pts = [(-L / 2, -s / 2), (L / 2, -s / 2), (L / 2, s / 2), (-L / 2, s / 2), (-L / 2, -s / 2)]
    else:
        pts = [(-s / 2, -L / 2), (-s / 2, L / 2), (s / 2, L / 2), (s / 2, -L / 2), (-s / 2, -L / 2)]
    return np.array([(centre_x + px, centre_y + py, h) for px, py in pts])


def bz_plan(sommets: np.ndarray, courant: float, X: np.ndarray, Y: np.ndarray,
            z_plan: float = 0.0, mu_r_cfc: float | None = None,
            z_miroir: float | None = None) -> np.ndarray:
    """Composante Bz sur le plan z=z_plan (grille X, Y en meshgrid 'ij').

    Si ``mu_r_cfc`` est fourni, ajoute l'image de la polyligne à travers le
    plan z=z_miroir (face inférieure du CFC) pondérée par (µr−1)/(µr+1).
    """
    pts = np.column_stack([X.ravel(), Y.ravel(), np.full(X.size, z_plan)])
    B = champ_segments(pts, sommets, courant)
    if mu_r_cfc is not None and z_miroir is not None:
        eta = (mu_r_cfc - 1.0) / (mu_r_cfc + 1.0)
        image = sommets.copy()
        image[:, 2] = 2.0 * z_miroir - image[:, 2]
        B += champ_segments(pts, image, eta * courant)
    return B[:, 2].reshape(X.shape)
