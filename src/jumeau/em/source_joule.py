"""Assemblage de la source Joule volumique Q(x, y, z) pour une position de spot.

Chaîne par couche conductrice (twill, laminé sup, laminé inf) :
1. Bz RMS (Biot-Savart bobine + image CFC), échantillonné à CHAQUE nœud z de
   la grille thermique compris dans la couche (et non plus une seule fois au
   plan médian, cf. « limites » ci-dessous) — l'atténuation géométrique est
   portée par la distance à la bobine, et le blindage par les couches
   conductrices traversées est appliqué comme un facteur d'effet de peau
   e^(−2·t/δ) par couche écran (équivalent du r_I ≈ 2/δ du modèle 1D, remède
   ③ du test black-box) — SAUF si ``champ_reaction=True``, cf. plus bas ;
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

Déficit de chauffe de TC1 — ``decalage_x`` écarté (2026-07-20) : TC1 (surface,
dans ``lamine_sup``) chauffe 5–6× trop lentement que la mesure. Un balayage EM
de ``decalage_x`` sur [0, 0.015] m (diagnostic jusqu'à 0.050 m, ``facteur_couplage``
figé) montre que le rapport ``Q(TC1)/Q(TC2)`` culmine à ~0,12 vers 7 mm et reste
5–50× sous 1 sur tout le domaine, alors que la cible mesurée est
``taux_TC1/taux_TC2 ≈ 1,71``. Décaler la bobine déplace le zéro de dissipation
du plan de symétrie du hairpin mais ne peut PAS inverser la hiérarchie de
résistivité inter-couches (``lamine_sup`` ρ≈3,7 mΩ·m vs ``twill_suscepteur``
ρ≈0,09 mΩ·m, ~40× plus conducteur). Le déficit TC1 est donc structurel
(répartition de puissance entre couches / champ proche non capturé par la
plaque mince), pas un problème de positionnement — ne pas retenter ``decalage_x``
comme remède sans nouvelle donnée (cf. README, § Limites connues).

Champ de réaction (``champ_reaction``, 2026-07-21) — DERRIÈRE UN FLAG
----------------------------------------------------------------------
Par défaut (``champ_reaction=False``), comportement HISTORIQUE inchangé :
``attenuation_blindage`` (écran ad hoc e^(−2t/δ)) reste le seul modèle de
blindage inter-couches, ψ reste réel, résolu nœud par nœud comme au point 1.

Si ``champ_reaction=True`` : Bz_total = Bz_bobine + Bz_induit[ψ] est résolu
de façon AUTO-COHÉRENTE et COMPLEXE (cf. docstring foucault.py pour la
dérivation). Le système couplé est résolu à raison d'UNE NAPPE ÉQUIVALENTE
PAR COUCHE (3 nappes : twill, laminé sup, laminé inf — chacune à son
``z_mid``, PAS une par nœud z échantillonné) : une tentative initiale avec
une nappe par nœud (comme au point 1) s'est révélée NUMÉRIQUEMENT INSTABLE —
des nappes séparées de quelques dixièmes de mm (bien en-deçà de 1/k pour les
modes proches du repliement de Nyquist de la grille) se couplent en
amplifiant le bruit haute fréquence de la solution FD au lieu de le
dissiper, car le noyau de ``bz_induit_nappe`` (∝|k|·exp(−|k|·|Δz|)) ne
décroît PAS à haute fréquence quand |Δz| est trop petit devant 1/k — un
artefact numérique, pas de la physique (vérifié : réplique un ratio de
puissance déposée >1 pour un phénomène qui doit physiquement toujours
réduire |ψ|). Une nappe unique par couche (séparations mm, physiquement
justifié puisque ρ est uniforme dans toute la couche — il n'y a qu'UN seul
conducteur par couche, la subdivision en nœuds z du point 1 n'est qu'un choix
de RÉSOLUTION DE DÉPÔT, pas une collection de conducteurs indépendants) est
numériquement saine (vérifiée en maillage, cf. rapport) et physiquement plus
défendable pour le couplage.

Le facteur de correction résultant, RATIO_COUCHE = P1_couche/P0_couche
(puissance totale de la couche au ``z_mid``, avec/sans réaction, calculée une
fois par couche), est appliqué de façon UNIFORME (facteur scalaire, pas un
champ (x,y)) à TOUS les nœuds z de dépôt de cette couche, EN PLACE de
``attenuation_blindage`` — la garder en plus aurait doublé le blindage
inter-couches. Un facteur scalaire (plutôt qu'un champ (x,y) issu du rapport
q1(x,y)/q0(x,y) au z_mid) évite la division mal conditionnée près du zéro de
symétrie du hairpin (cf. rapport de diagnostic EM antérieur) — l'effet
recherché (quelques dixièmes de %, cf. docstring foucault.py) est de toute
façon trop petit pour qu'une éventuelle reformation spatiale fine soit
significative ou distinguable du bruit de discrétisation.

ATTENTION calibration — DEUX effets à ne pas confondre :
1. Le champ de réaction proprement dit (auto-inductance de chaque couche) est
   PETIT (~0,2-0,6 % de réduction de puissance à ω et σ nominaux, cf.
   docstring foucault.py) — bien plus petit qu'une estimation grossière par
   analogie dimensionnelle (facteur π en trop + mauvaise couche de
   référence, cf. rapport ``resultats_champ_reaction_em.log``, étape 0).
2. Désactiver ``attenuation_blindage`` (écran ad hoc, −11,8 % sur le twill et
   −18,0 % sur le laminé inf à θ* actuel, cf. valeurs numériques dans le
   rapport) retire un effet BEAUCOUP PLUS GROS que ce que (1) ajoute en
   retour. Le bilan NET de ``champ_reaction=True`` à ``facteur_couplage``
   FIGÉ est donc une AUGMENTATION de la puissance déposée dans le twill et le
   laminé inférieur (les couches historiquement « écrantées »), PAS une
   réduction — résultat contre-intuitif si l'on ne pense qu'au terme (1),
   mais attendu une fois qu'on réalise que (2) domine. ``facteur_couplage``
   absorbe aujourd'hui un mélange des deux effets (cf. docstring foucault.py
   et README) ; il devra être recalibré (à la baisse, probablement) pour
   comparer les deux chemins sur un pied d'égalité — hors mandat ici
   (NE RECALIBRE RIEN, cf. brief). Cf. rapport dédié pour les chiffres sur
   les 3 essais à θ* figé.

Convergence : itération de point fixe (Picard) jusqu'à
``max(|Δψ|)/max(|ψ|) < tol`` (défaut 1e-6) ou ``RuntimeError`` si non atteint
en ``max_iter`` (défaut 50) itérations — le rayon spectral de l'itération est
borné par le paramètre de blindage max (~0,05-0,1 dans cette géométrie), donc
convergence géométrique rapide attendue (~5-10 itérations, vérifié).
"""

from __future__ import annotations

import numpy as np

from ..geometrie import CoucheConductrice, plan_miroir_cfc, sommets_bobine
from ..materiaux import Config
from ..thermique.solveur3d import Grille3D
from .champ_coil import MU0, bz_plan
from .foucault import (bz_induit_nappe, densite_joule, densite_joule_complexe,
                       noyau_reaction_k, resoudre_psi, resoudre_psi_complexe)


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


def _resoudre_champ_reaction(sheets: list[dict], dx: float, dy: float, omega: float,
                             tol: float = 1e-6, max_iter: int = 50) -> list[np.ndarray]:
    """Résout le système auto-cohérent complexe couplant les nappes de
    courant fournies (une par COUCHE, cf. docstring module — PAS une par
    nœud z). ``sheets`` : liste de dicts avec clés ``rho_xx``, ``rho_yy``,
    ``z`` (profondeur du plan médian, m), ``epaisseur`` (m, épaisseur totale
    de la couche), ``Bz0`` (champ appliqué réel au plan médian, nx×ny).

    Itération de Picard : à chaque itération, chaque nappe voit le Bz induit
    par TOUTES les nappes (elle-même incluse) à l'itération précédente,
    atténué selon leur écart de profondeur (``bz_induit_nappe``, facteur
    exp(−|k|·|Δz|)). Critère de convergence explicite (cf. docstring
    module) ; ``RuntimeError`` si non convergé.
    """
    n = len(sheets)
    nx, ny = sheets[0]["Bz0"].shape
    Kmag = noyau_reaction_k(nx, ny, dx, dy)

    psis = [resoudre_psi(s["Bz0"], dx, dy, s["rho_xx"], s["rho_yy"], omega).astype(complex)
            for s in sheets]

    for it in range(1, max_iter + 1):
        nouveaux = []
        max_delta = 0.0
        for i, s in enumerate(sheets):
            Bind = np.zeros_like(s["Bz0"], dtype=complex)
            for j, sj in enumerate(sheets):
                dz = s["z"] - sj["z"]
                # facteur j : bz_induit_nappe attend la fonction de courant
                # COMPLEXE VRAIE (Psi_vraie = j*psi_code, cf. convention de
                # resoudre_psi -- psi "code" est en quadrature stricte avec Bz
                # réel dans le problème sans réaction, ψ_vraie = j·ψ_code) ;
                # sans ce facteur, Bz_induit resterait en phase avec ψ_code
                # au lieu d'être en phase avec le VRAI courant physique, et
                # l'itération convergerait vers un pur affaiblissement réel au
                # lieu du couplage complexe correct (vérifié par comparaison
                # à la solution analytique 1 mode, cf. rapport).
                Bind += 1j * bz_induit_nappe(psis[j], sj["epaisseur"], Kmag, dz=dz)
            Bz_tot = s["Bz0"] + Bind
            psi_new = resoudre_psi_complexe(Bz_tot, dx, dy, s["rho_xx"], s["rho_yy"], omega)
            denom = float(np.abs(psi_new).max())
            d = float(np.abs(psi_new - psis[i]).max() / denom) if denom > 0.0 else 0.0
            max_delta = max(max_delta, d)
            nouveaux.append(psi_new)
        psis = nouveaux
        if max_delta < tol:
            return psis

    raise RuntimeError(
        f"champ de réaction : non convergé après {max_iter} itérations "
        f"(delta_max={max_delta:.3e} > tol={tol:.1e}) — {n} nappes couplées."
    )


def source_spot(
    grille: Grille3D,
    cfg: Config,
    couches: list[CoucheConductrice],
    courant: float,
    centre_x: float,
    facteur_couplage: float = 1.0,
    decalage_x: float = 0.0,
    champ_reaction: bool = False,
) -> np.ndarray:
    """Champ source Q (nx, ny, nz) en W/m³ pour la bobine centrée en ``centre_x``.

    ``decalage_x`` (m) décale le centre EFFECTIF de la bobine par rapport au
    ``centre_x`` nominal du spot (incertitude de positionnement bobine/CFC au
    montage, cf. geometrie.yaml:coil.decalage_x). Seule la bobine bouge : le
    masque céramique/CFC (masque_empreinte_cfc) reste posé à ``centre_x`` —
    c'est un décalage bobine<->reste du montage, pas un déplacement du spot.

    ``champ_reaction`` (défaut False, cf. docstring module) : active la
    résolution auto-cohérente complexe Bz_total = Bz_bobine + Bz_induit[ψ]
    (une nappe par couche, couplage inter-couches inclus) en lieu et place de
    l'atténuation ad hoc ``attenuation_blindage``. Comportement HISTORIQUE
    strictement inchangé si False (chemin non touché, non-régression
    bit-à-bit).
    """
    omega = 2.0 * np.pi * float(cfg.geometrie["generateur"]["frequence"])
    mu_r = float(cfg.geometrie["cfc"]["mu_r"])
    z_miroir = plan_miroir_cfc(cfg)
    sommets = sommets_bobine(cfg, centre_x + decalage_x)
    X, Y = np.meshgrid(grille.x, grille.y, indexing="ij")

    Q = np.zeros((grille.nx, grille.ny, grille.nz))

    if not champ_reaction:
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

    # --- chemin champ de réaction : une nappe équivalente par couche ---
    Bz0_mid = []
    for couche in couches:
        Bz0_mid.append(bz_plan(sommets, courant, X, Y, z_plan=-couche.z_mid,
                               mu_r_cfc=mu_r, z_miroir=z_miroir))

    sheets = [dict(rho_xx=c.rho_xx, rho_yy=c.rho_yy, z=c.z_mid, epaisseur=c.epaisseur, Bz0=Bz0)
              for c, Bz0 in zip(couches, Bz0_mid)]
    psis = _resoudre_champ_reaction(sheets, grille.dx, grille.dy, omega)

    for couche, Bz0, psi_reac in zip(couches, Bz0_mid, psis):
        psi0 = resoudre_psi(Bz0, grille.dx, grille.dy, couche.rho_xx, couche.rho_yy, omega)
        q0 = densite_joule(psi0, grille.dx, grille.dy, couche.rho_xx, couche.rho_yy)
        q1 = densite_joule_complexe(psi_reac, grille.dx, grille.dy, couche.rho_xx, couche.rho_yy)
        P0, P1 = q0.sum(), q1.sum()
        ratio_couche = float(P1 / P0) if P0 > 0.0 else 1.0

        iz = np.where((grille.z >= couche.z_min - 1e-12) & (grille.z <= couche.z_max + 1e-12))[0]
        if len(iz) == 0:
            iz = np.array([grille.indice_z(couche.z_mid)])
        poids = couche.epaisseur / (len(iz) * grille.dz)

        for k in iz:
            z_k = grille.z[k] if len(iz) > 1 else couche.z_mid
            Bz = bz_plan(sommets, courant, X, Y, z_plan=-z_k,
                        mu_r_cfc=mu_r, z_miroir=z_miroir)
            psi = resoudre_psi(Bz, grille.dx, grille.dy, couche.rho_xx, couche.rho_yy, omega)
            q = densite_joule(psi, grille.dx, grille.dy, couche.rho_xx, couche.rho_yy)
            Q[:, :, k] += q * ratio_couche * poids

    return facteur_couplage * Q
