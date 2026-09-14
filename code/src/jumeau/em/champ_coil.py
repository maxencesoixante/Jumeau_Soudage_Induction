"""Champ magnétique de la bobine hairpin par Biot-Savart (segments analytiques).

Champ d'un segment rectiligne fini a->b parcouru par un courant I, au point P :

    B = (µ0·I / 4π) · (û × r1) / |û × r1|² · (û·r̂1 − û·r̂2)

avec û le vecteur unitaire du segment, r1 = P−a, r2 = P−b. Vectorisé sur un
nuage de points d'observation. Vérifié contre la boucle circulaire analytique
(B_centre = µ0·I / 2R) dans les tests.

Le concentrateur de flux (MFC, Ferrotron 559H, µr≈16) est traité par la
méthode des courants images : chaque segment est réfléchi à travers le plan
inférieur du MFC avec un courant η·I, η = (µr−1)/(µr+1) ≈ 0,88. Cette
approximation de demi-espace perméable intensifie le champ sous l'empreinte —
elle capture l'effet de concentration au premier ordre, pas les effets de
bord exacts du bloc fini (hypothèse assumée, cf. README).

Auto-échauffement du MFC (Joule + hystérésis dans le Ferrotron 559H lui-même,
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
champ B dans le volume du MFC à 250 A/388 kHz reste très en-deçà de la
saturation (≈3–28 mT crête pour Bsat=0,9 T) et la puissance totale intégrée
sur tout le bloc (20,8 cm³) n'est que ≈0,6–1,4 W — 1 à 2 ordres de grandeur
sous ce qu'il faudrait pour expliquer le déficit de pente observé au
thermocouple TC1 (cf. README, § Limites connues). Conclusion : mécanisme
réel mais négligeable à cette échelle ; ne pas le réintroduire comme
explication du déficit TC1 sans nouvelle mesure (température du MFC lui-même,
absente des essais actuels).

Image de bloc FINI (``bz_plan(..., image_finie=True)``, défaut False) — LA
LONGUEUR/LARGEUR du bloc entre enfin dans le champ calculé
------------------------------------------------------------------------------
L'image ci-dessus (η·I à travers le plan z=z_miroir) est celle d'un DEMI-ESPACE
perméable INFINI : elle ne dépend que de µr et de l'altitude du plan, jamais de
la longueur ni de la largeur du bloc MFC — Bz est donc rigoureusement identique
entre un MFC 55 mm et un MFC 31,75 mm (verrouillé par
``test_masque_source_mfc_off_est_non_regression``). C'est la limite que ce
mécanisme additif lève, SOUS UN FLAG, sans toucher au chemin par défaut.

Option retenue : IMAGE TRONQUÉE À L'EMPREINTE DU BLOC, avec adoucissement de
bord (pas une coupure dure). Candidats évalués et écartés pour ce livrable :
  - correction de réluctance/démagnétisation dépendant du rapport d'aspect du
    bloc -- un facteur SCALAIRE (dépend de longueur/largeur/hauteur mais pas
    de (x,y)) change l'intensité globale, pas la RÉPARTITION spatiale ; or
    c'est précisément la redistribution bord/centre en y qui est recherchée
    ici (cf. mission, contraste bord/centre). Écarté : ne répond pas à la
    question posée, garder en réserve si un déficit de NIVEAU global
    apparaissait séparément.
  - charges magnétiques surfaciques sur les 6 faces du bloc (résolution de
    H_demag par un noyau de charge de surface, cf. magnétostatique des corps
    finis) -- le traitement rigoureux, mais un solve 3D supplémentaire par
    appel de couche/z échantillonné (déjà ~3 couches × plusieurs nœuds z par
    spot) ; coût disproportionné pour un premier ordre destiné à être
    confronté à une mesure qui n'existe pas encore (#55). Écarté FAUTE DE
    BESOIN, pas d'impossibilité — à reconsidérer si l'image tronquée échoue
    qualitativement contre la mesure.

Modèle retenu : la contribution IMAGE (pas le champ bobine nu, qui reste
present partout -- hors du bloc, le champ redevient simplement celui de la
bobine SANS concentrateur, pas nul) est pondérée par une fenêtre spatiale
W(x,y) fonction du POINT D'OBSERVATION par rapport au centre et aux
DEMI-EXTENSIONS du bloc (``cfc.largeur/2`` en x, ``cfc.longueur/2`` en y) :
plateau à 1 jusqu'à (demi − marge), taper en demi-cosinus (C¹, sans
discontinuité de pente contrairement à un masque 0/1) jusqu'à 0 à
(demi + marge). La marge est prise égale à la HAUTEUR du bloc (``cfc.hauteur``,
déjà dans le modèle -- AUCUN paramètre libre supplémentaire, même convention
que ``lambda_bord_x_mm`` = épaisseur de couche) : c'est l'ordre de grandeur
usuel de l'extension d'un champ de fuite/frange au bord d'un bloc magnétique
fini, dont l'épaisseur fixe l'échelle de décroissance hors du matériau.

Ce que cette approximation NE capture PAS (à ne pas sur-interpréter, même
esprit que les réserves ci-dessus) :
  - la fenêtre pondère le POINT D'OBSERVATION, pas la position du SEGMENT de
    bobine réfléchi le long du bloc -- un vrai corps fini aurait une
    magnétisation induite non uniforme sur sa propre étendue (plus forte
    sous la bobine, decroissant vers ses bords), que ce modèle ne résout pas ;
  - la marge (= hauteur du bloc) est un ordre de grandeur physique, PAS une
    longueur mesurée pour CE Ferrotron 559H précis -- calibrable comme les
    autres longueurs de relaxation du projet (``lambda_bord_mm`` et
    consorts), pas une valeur figée par une mesure indépendante ;
  - toujours pas de réluctance/démagnétisation propre au corps fini (l'image
    reste construite avec le même η qu'un demi-espace infini, seule sa
    PORTÉE spatiale est tronquée) -- un bloc très petit devrait aussi voir
    son η effectif réduit (facteur de forme), non modélisé ici ;
  - ``image_finie=False`` (défaut) reproduit EXACTEMENT (bit-à-bit) le
    comportement historique -- non-régression garantie par construction (le
    code emprunte la même branche, B_image identique, fenêtre non appliquée).

Variante 2 — troncature côté SOURCE (``mode_troncature_image="source"``)
------------------------------------------------------------------------------
Objection retenue (revue, 2026-09-14) : la variante ci-dessus pondère le POINT
D'OBSERVATION, alors que ce qui est physiquement absent sous un MFC raccourci
est une PORTION DU BLOC DE FERRITE -- les jambes du hairpin font 55 mm selon y
(``coil.longueur_jambe``, fixe, propriété du fil) alors que le bloc, lui, peut
être plus court (``cfc.longueur`` 55 -> 31,75 mm) : une partie du fil n'a plus
de ferrite au-dessus d'elle. Une troncature de l'image côté SOURCE (ne
réfléchir que la portion de polyligne sous l'empreinte du bloc, adoucie aux
extrémités) modélise QUELLE PARTIE DU CONCENTRATEUR EXISTE, pas où l'on
regarde -- une hypothèse au moins aussi défendable que la variante 1, sans que
l'une des deux s'impose a priori. Les deux sont conservées, PAS l'une au
détriment de l'autre : c'est la confrontation des deux qui indique si la
conclusion (contraste peu affecté) est robuste à ce choix de modélisation ou
un artefact de l'heuristique retenue (cf. rapport de comparaison, agent EM).

Implémentation : la polyligne IMAGE est subdivisée en sous-segments (pas
``marge_cfc/6`` -- résolution liée à la longueur déjà dans le modèle, pas une
nouvelle constante libre) ; chaque sous-segment porte un courant
``poids · η · I``, ``poids`` = la MÊME fenêtre W(x,y) que la variante 1 mais
évaluée au MILIEU du sous-segment (donc sur la position de la SOURCE réfléchie
le long du fil), PAS sur le point d'observation. Superposition de Biot-Savart
(linéaire) sur les sous-segments pondérés -- identité exacte avec la variante
non tronquée à poids≡1 (subdiviser un segment rectiligne en pièces contiguës
de même courant ne change pas son champ, cf. test de limite).

Ce que cette variante NE capture PAS (au même titre que la variante 1) :
  - le courant local pondéré (``poids·η·I`` variable d'un sous-segment au
    suivant) ne respecte pas Kirchhoff au nœud de coupure -- c'est un procédé
    de troncature/lissage, pas une distribution de courant physiquement
    fermée ; exactement le même niveau d'approximation que la variante 1
    (qui, elle, viole plutôt la continuité du champ observé), pas un défaut
    propre à cette variante ;
  - la marge et la finesse de subdivision restent des choix numériques, pas
    mesurés ;
  - toujours aucune réluctance/démagnétisation propre au corps fini (même
    réserve que la variante 1).

``mode_troncature_image`` (défaut ``"observation"`` = variante 1, comportement
inchangé depuis son introduction) n'a d'effet QUE si les 5 paramètres de bloc
fini sont fournis ; valeur ``"source"`` -> variante 2 ci-dessus. Valeur
invalide -> ``ValueError``.
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


def _fenetre_bord_bloc(u: np.ndarray, demi: float, marge: float) -> np.ndarray:
    """Fenêtre 1D symétrique de troncature adoucie : 1 pour |u| <= demi−marge,
    taper en demi-cosinus (C¹) jusqu'à 0 en |u| = demi+marge, 0 au-delà.
    ``marge <= 0`` -> coupure dure exacte (|u| <= demi), pour compat/tests.
    Si ``demi < marge`` (bloc plus petit que sa propre marge), le plateau est
    tronqué à 0 (``lo = max(demi-marge, 0)``) plutôt que rendu négatif -- cas
    limite non rencontré dans la géométrie du projet (marge = hauteur du bloc
    12 mm, demi >= 15,75 mm pour les deux MFC modélisés)."""
    au = np.abs(u)
    if marge <= 0.0:
        return (au <= demi).astype(float)
    lo = max(demi - marge, 0.0)
    hi = demi + marge
    t = np.clip((au - lo) / (hi - lo), 0.0, 1.0)
    return 0.5 * (1.0 + np.cos(np.pi * t))


def _champ_segments_ponderes(points: np.ndarray, paires: np.ndarray,
                             poids: np.ndarray, courant: float) -> np.ndarray:
    """Comme ``champ_segments``, mais sur une collection de segments DISJOINTS
    (pas une polyligne continue), chacun pondéré individuellement -- utilisé
    par la variante 2 de troncature d'image (cf. docstring module). ``paires``
    (M, 2, 3) : couples (a, b) de chaque sous-segment ; ``poids`` (M,) : poids
    multiplicatif du courant sur ce sous-segment. Superposition linéaire de
    Biot-Savart -- reproduit EXACTEMENT ``champ_segments`` si ``poids`` vaut 1
    partout et que les sous-segments sont bout à bout sur la polyligne
    d'origine (mêmes points, même courant, juste plus de morceaux)."""
    P = np.asarray(points, dtype=float)
    B = np.zeros_like(P)
    for (a, b), w in zip(paires, poids):
        if w == 0.0:
            continue
        ab = b - a
        L = np.linalg.norm(ab)
        if L < 1e-12:
            continue
        u = ab / L
        r1 = P - a
        r2 = P - b
        d = np.cross(np.broadcast_to(u, r1.shape), r1)
        d2 = np.einsum("ij,ij->i", d, d)
        n1 = np.linalg.norm(r1, axis=1)
        n2 = np.linalg.norm(r2, axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            fac = (np.einsum("ij,j->i", r1, u) / n1 - np.einsum("ij,j->i", r2, u) / n2) / d2
        fac = np.where(d2 < 1e-18, 0.0, fac)
        B += w * d * fac[:, None]
    return MU0 * courant / (4.0 * np.pi) * B


def _sous_segments_ponderes(polyligne: np.ndarray, centre_x_cfc: float, centre_y_cfc: float,
                            demi_x_cfc: float, demi_y_cfc: float, marge_cfc: float
                            ) -> tuple[np.ndarray, np.ndarray]:
    """Subdivise chaque segment de ``polyligne`` en sous-segments de longueur
    cible ``marge_cfc/6`` (résolution liée à la marge déjà présente dans le
    modèle -- pas une nouvelle constante libre), et calcule le poids
    W(x,y) = fenêtre(x, demi_x_cfc, marge_cfc) · fenêtre(y, demi_y_cfc, marge_cfc)
    au MILIEU de chaque sous-segment (position de la SOURCE réfléchie, cf.
    variante 2 -- docstring module). Renvoie (paires (M, 2, 3), poids (M,))."""
    pas_cible = max(marge_cfc / 6.0, 1e-6)
    paires = []
    for a, b in zip(polyligne[:-1], polyligne[1:]):
        L = float(np.linalg.norm(b - a))
        if L < 1e-12:
            continue
        n = max(4, int(np.ceil(L / pas_cible)))
        t = np.linspace(0.0, 1.0, n + 1)
        pts_seg = a[None, :] + t[:, None] * (b - a)[None, :]
        for i in range(n):
            paires.append((pts_seg[i], pts_seg[i + 1]))
    paires = np.array(paires)
    milieu = 0.5 * (paires[:, 0, :] + paires[:, 1, :])
    Wx = _fenetre_bord_bloc(milieu[:, 0] - centre_x_cfc, demi_x_cfc, marge_cfc)
    Wy = _fenetre_bord_bloc(milieu[:, 1] - centre_y_cfc, demi_y_cfc, marge_cfc)
    return paires, Wx * Wy


def bz_plan(sommets: np.ndarray, courant: float, X: np.ndarray, Y: np.ndarray,
            z_plan: float = 0.0, mu_r_cfc: float | None = None,
            z_miroir: float | None = None,
            centre_x_cfc: float | None = None, centre_y_cfc: float | None = None,
            demi_x_cfc: float | None = None, demi_y_cfc: float | None = None,
            marge_cfc: float | None = None,
            mode_troncature_image: str = "observation") -> np.ndarray:
    """Composante Bz sur le plan z=z_plan (grille X, Y en meshgrid 'ij').

    Si ``mu_r_cfc`` est fourni, ajoute l'image de la polyligne à travers le
    plan z=z_miroir (face inférieure du MFC) pondérée par (µr−1)/(µr+1) —
    demi-espace perméable INFINI par défaut (comportement historique).

    Image de bloc FINI (additif, cf. docstring module) : si en plus les 5
    paramètres ``centre_x_cfc``, ``centre_y_cfc``, ``demi_x_cfc``,
    ``demi_y_cfc``, ``marge_cfc`` sont TOUS fournis (non None), la
    contribution IMAGE (seulement elle -- le champ de la bobine nue reste
    entier partout) est tronquée/adoucie à l'empreinte du bloc, selon
    ``mode_troncature_image`` :
      - ``"observation"`` (DÉFAUT -- comportement inchangé depuis son
        introduction) : pondère le POINT D'OBSERVATION par la fenêtre
        séparable W(x,y) = fenêtre(x−centre_x_cfc, demi_x_cfc, marge_cfc) ·
        fenêtre(y−centre_y_cfc, demi_y_cfc, marge_cfc).
      - ``"source"`` : pondère la SOURCE -- seule la portion de la polyligne
        IMAGE (donc du bloc réfléchi) sous l'empreinte contribue, adoucie à
        ses extrémités (cf. docstring module, "Variante 2").
    Ces 5 paramètres tous à None (défaut) reproduit EXACTEMENT le chemin
    historique (image de demi-espace infini, bit-à-bit), quel que soit
    ``mode_troncature_image`` (ignoré dans ce cas) ; fournir un sous-ensemble
    non vide des 5 lève ``ValueError`` (évite un flag silencieusement à moitié
    actif) ; ``mode_troncature_image`` invalide (avec les 5 fournis) lève
    aussi ``ValueError``.
    """
    pts = np.column_stack([X.ravel(), Y.ravel(), np.full(X.size, z_plan)])
    B = champ_segments(pts, sommets, courant)
    if mu_r_cfc is not None and z_miroir is not None:
        eta = (mu_r_cfc - 1.0) / (mu_r_cfc + 1.0)
        image = sommets.copy()
        image[:, 2] = 2.0 * z_miroir - image[:, 2]
        params_finis = (centre_x_cfc, centre_y_cfc, demi_x_cfc, demi_y_cfc, marge_cfc)
        n_fournis = sum(v is not None for v in params_finis)
        if n_fournis == 0:
            B_image = champ_segments(pts, image, eta * courant)
        elif n_fournis == 5:
            if mode_troncature_image == "observation":
                B_image = champ_segments(pts, image, eta * courant)
                Wx = _fenetre_bord_bloc(X.ravel() - centre_x_cfc, demi_x_cfc, marge_cfc)
                Wy = _fenetre_bord_bloc(Y.ravel() - centre_y_cfc, demi_y_cfc, marge_cfc)
                B_image = B_image * (Wx * Wy)[:, None]
            elif mode_troncature_image == "source":
                paires, poids = _sous_segments_ponderes(
                    image, centre_x_cfc, centre_y_cfc, demi_x_cfc, demi_y_cfc, marge_cfc)
                B_image = _champ_segments_ponderes(pts, paires, poids, eta * courant)
            else:
                raise ValueError(
                    "bz_plan : mode_troncature_image doit être 'observation' ou "
                    f"'source', reçu {mode_troncature_image!r}."
                )
        else:
            raise ValueError(
                "bz_plan : image de bloc fini -- fournir les 5 paramètres "
                "(centre_x_cfc, centre_y_cfc, demi_x_cfc, demi_y_cfc, marge_cfc) "
                f"ensemble, ou aucun (reçu {n_fournis}/5)."
            )
        B = B + B_image
    return B[:, 2].reshape(X.shape)
