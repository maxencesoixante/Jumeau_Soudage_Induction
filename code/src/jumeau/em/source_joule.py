"""Assemblage de la source Joule volumique Q(x, y, z) pour une position de spot.

Chaîne par couche conductrice (twill, laminé sup, laminé inf) :
1. Bz RMS (Biot-Savart bobine + image MFC), échantillonné à CHAQUE nœud z de
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

Déficit d'épaisseur — ``decalage_x`` écarté (2026-07-20) : un balayage EM de
``decalage_x`` sur [0, 0.015] m (``facteur_couplage`` figé) ne peut PAS inverser
la hiérarchie de résistivité inter-couches (``lamine_sup`` ρ≈3,7 mΩ·m vs
``twill_suscepteur`` ρ≈0,09 mΩ·m, ~40× plus conducteur) — la source se dépose au
twill/interface quoi qu'il arrive. Ne pas retenter ``decalage_x`` comme remède.

CORRECTION 2026-08-13 (débogage systématique « limite #2 ») : l'ancienne
formulation « TC1 surface 5–6× trop lent, cible ``taux_TC1/taux_TC2 ≈ 1,71`` »
était FAUSSE. Recalculée depuis la donnée brute 3-TC (``chauffe_250A_3TC``), la
mesure donne surface≈interface (ratio ≈ 0,97) ; TOUS les TC A/B sont d'ailleurs
à l'interface. Le vrai écart est un GRADIENT D'ÉPAISSEUR trop faible : le modèle
sur-chauffe la face opposée (o/i≈0,9 vs 0,42 mesuré), mécanisme = couplage
transverse (thermique/électrique) trop fort entre interface et laminé inférieur.
Levier prototypé ``Materiau.r_contact_interface`` (résistance de contact à
l'interface, ``solveur3d``) — reproduit le profil d'épaisseur mais NO-GO en
validation croisée (aggrave l'interface de bord TC1 sur A/B). Cf.
``docs/modele/leviers_refutes.md``, mémoire ``limite2-gradient-epaisseur``.

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

Adoucissement du bord (``lambda_bord_mm``, 2026-07-30) — DERRIÈRE UN FLAG
--------------------------------------------------------------------------
Diagnostic (cf. journaux/archive/resultats_diag_forme_source.log,
docs/modele/README.md « État & résidu ouvert ») : la BC ``psi=0`` exacte au
chant est la physique correcte pour une nappe de courant CONTINUE et
idéalement homogène (aucun courant ne traverse un conducteur isolé isotrope
à son bord). Mais le twill suscepteur (siège principal des courants de
Foucault, cf. ``geometrie.construire_couches``) n'est PAS un continuum : les
boucles fermées natives sont portées par un tissage à pas fini (mailles du
sergé) et le laminé homogénéisé masque de la même façon la maille discrète
des plis/torons. À l'échelle du pas de tissage/pli, l'hypothèse « nappe
continue plane, psi=0 exactement AU nœud du bord géométrique » n'a plus de
sens physique fin : le dernier « barreau » de boucles fermées avant la
coupe du chant est décalé de l'ordre d'un pas de maille par rapport au bord
géométrique exact, et le courant de retour peut encore emprunter des
boucles partiellement coupées / des contacts fibre-fibre juste au-delà du
bord idéal avant de s'annuler réellement -- cf. option 1 de la mission
(« condition de bord psi moins raide »).

On modélise ceci par une longueur de relaxation ``lambda_bord_mm`` (mm) :
au lieu de résoudre l'EDP ``psi=0`` exactement aux indices (0, ny-1) de la
grille PHYSIQUE en y (largeur), on résout la MÊME EDP (mêmes rho, même Bz
échantillonné, aucune approximation supplémentaire dans ``foucault.py``,
qui reste intouché) sur une grille en y ÉTENDUE de ``lambda_bord_mm`` de
part et d'autre (``_grille_y_etendue``), ``psi=0`` étant repoussé sur cette
frontière étendue -- PAS au chant réel de l'échantillon, qui devient un
nœud INTÉRIEUR libre de prendre une valeur non nulle. C'est la technique
classique de la « longueur d'extrapolation » des problèmes de diffusion à
frontière discrète/mésoscopique (analogue du problème de Milne en théorie
du transport : la frontière effective d'un milieu diffusif discret est
repoussée d'une fraction du libre parcours moyen au-delà de la frontière
géométrique) -- ici appliquée par analogie au pas de maille du tissage
plutôt qu'à un libre parcours de transport. AUCUNE matière conductrice
n'est ajoutée physiquement hors de l'échantillon : c'est un DISPOSITIF DE
CONDITION AUX LIMITES qui adoucit le gradient de psi (donc de J=rot(psi),
donc de q=rho.J^2) au voisinage immédiat du bord réel, sans toucher au
reste du domaine (n_pad mailles seulement, cf. ``_grille_y_etendue``).

``lambda_bord_mm=0`` (défaut) reproduit EXACTEMENT (bit-à-bit) le chemin
historique ``psi=0`` au bord géométrique -- non-régression garantie. Non
supporté avec ``champ_reaction=True`` (interaction non explorée, hors
mandat -- ``ValueError`` explicite si les deux sont actifs). ``lambda_bord_mm``
est un paramètre d'ÉCHELLE PHYSIQUEMENT MOTIVÉ mais NON MESURÉ (le pas de
tissage du sergé n'est pas caractérisé au cahier) : à traiter comme
CALIBRABLE au même titre que ``lissage_sigma_mm``, PAS comme une valeur
figée par une mesure indépendante -- cf. rapport dédié pour la valeur
prototypée et son effet sur le contraste bord/centre et le RMSE.

Adoucissement du bord EN X (``lambda_bord_x_mm``, 2026-08-28) — artefact
--------------------------------------------------------------------------
Diagnostic distinct de ``lambda_bord_mm`` ci-dessus (qui adoucit le contraste
du « M » en LARGEUR, y, sur tout le domaine ; VERDICT refuté le 2026-07-31,
conservé pour archivage). Ici : artefact localisé aux 2 colonnes de bord en x
(x=0 et x=nx-1, les bords RÉELS de longueur de la plaque, PAS le bord bobine
d'un spot).

Mécanisme : la BC ``psi=0`` est imposée sur TOUTE la ligne de bord x (pour
tout y), donc Jx=∂ψ/∂y y est identiquement nul (ψ plat le long de cette
ligne) -- seul survit Jy=−∂ψ/∂x (courant tangentiel au bord). Loin du spot
actif, ce résidu est négligeable ; mais pour un spot proche du bord réel
(spot en bout de plaque, à quelques mm du chant), la boucle de courant induite
n'a pas fini de se refermer avant d'atteindre le chant, et Jy hérite du
maximum de ψ intérieur -- qui, en y, est maximal au CENTRE de largeur
(ψ=0 aux 2 bords y). Le résultat est un profil q(y) qui bascule de
bord-piqué (M, cohérent avec l'intérieur) à centre-piqué EXACTEMENT sur les
~4 dernières mailles (~8 mm) avant le chant x.

Vérification numérique (spot4, x_centre=105,875 mm, chant réel x=120 mm,
courant 231 A, couche twill) : en relâchant PROGRESSIVEMENT la BC x (domaine
étendu, cf. plus bas) jusqu'à la limite « pas de bord du tout » (extension
>> toute échelle de décroissance de Bz), le ratio q(y=0)/q(y=20) au niveau du
chant SATURE vers ≈0,60 -- PAS vers >1 (bord-piqué franc). En comparant à un
spot INTÉRIEUR (spot2, loin de tout bord réel) à la MÊME distance relative du
centre bobine (+14 mm), le même ratio ≈0,68 apparaît SANS AUCUN bord proche.
CONCLUSION : la bascule vers un profil plus centré n'est PAS purement un
artefact de BC -- c'est en bonne partie une caractéristique RÉELLE de la
boucle de courant qui se referme au-delà de l'empreinte de la bobine (Jy
domine quand on s'éloigne du bobinage en x, indépendamment de tout bord).
Ce que la BC ``psi=0`` stricte AJOUTE en trop est la SUR-suppression
localisée à la toute dernière ligne/colonne (q(y=0) forcé exactement à 0 au
coin, alors que le même point sans bord proche vaudrait ≈0,6x le centre, pas
0) -- c'est CETTE sur-suppression, pas le contraste bord/centre en général,
que ``lambda_bord_x_mm`` corrige.

Justification physique retenue : effet 3D d'épaisseur, PAS mésostructure de
tissage (contrairement à ``lambda_bord_mm``). Le modèle plaque-mince suppose
un courant purement planaire (Jz nul, cf. Buser 2026, σz≪σxy) ; mais au chant
réel (coupe nette du stratifié, chaque couche ayant une épaisseur physique
propre, de 0,2 mm pour le twill à 3,4 mm pour les laminés), le courant PEUT
se redistribuer dans l'épaisseur de SA couche (plan y-z, hors du modèle
purement 2D) sur une distance de l'ordre de cette épaisseur avant que Jn
s'annule véritablement -- un effet purement 3D qu'une nappe strictement 2D
(ψ=0 pile sur la ligne de maillage du chant) ne peut pas capturer. D'où une
longueur de relaxation ``lambda_bord_x_mm`` PROPRE À CHAQUE COUCHE, prise par
défaut égale à l'épaisseur de la couche (``couche.epaisseur``) quand
``lambda_bord_x_mm`` est laissé à sa valeur sentinelle ``None`` -- PAS un
scalaire arbitraire recalibrable : c'est une longueur déjà présente dans le
modèle (aucun paramètre libre supplémentaire). Voir ``source_spot`` pour
l'API (accepte soit un ``float`` unique en mm pour toutes les couches --
ablation/tests -- soit ``None`` = épaisseur de couche par défaut, soit
``0.0`` = désactivé, comportement historique).

Implémentation : STRICTEMENT le même dispositif que ``lambda_bord_mm``
(domaine étendu en x, ``_grille_x_etendue``, ``psi=0`` repoussé sur la
frontière étendue, ``foucault.py`` intouché, ∇·J=0 garanti puisque psi reste
une fonction de courant sur tout le domaine résolu) -- appliqué en x au lieu
de y, et combinable avec ``lambda_bord_mm`` (extension indépendante par axe).
``lambda_bord_x_mm=None`` (DÉFAUT depuis 2026-08-30) = ACTIF/AUTO (longueur de
relaxation = épaisseur propre de chaque couche) : la correction est activée par
défaut (intérieur strictement inchangé -- exp7/exp9 Δ=0,0 ; seuls les TC posés
aux bords x bougent). ``lambda_bord_x_mm=0.0`` reproduit EXACTEMENT (bit-à-bit)
l'ancien chemin sans correction. Non supporté avec ``champ_reaction=True`` : le
défaut ``None`` y cède silencieusement (désactivé), seule une valeur explicite
positive lève une ``ValueError`` (même raison que ``lambda_bord_mm``).

Convergence : itération de point fixe (Picard) jusqu'à
``max(|Δψ|)/max(|ψ|) < tol`` (défaut 1e-6) ou ``RuntimeError`` si non atteint
en ``max_iter`` (défaut 50) itérations — le rayon spectral de l'itération est
borné par le paramètre de blindage max (~0,05-0,1 dans cette géométrie), donc
convergence géométrique rapide attendue (~5-10 itérations, vérifié).
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter

from ..geometrie import CoucheConductrice, plan_miroir_cfc, sommets_bobine
from ..materiaux import Config
from ..thermique.solveur3d import Grille3D
from .champ_coil import MU0, bz_plan
from .foucault import (bz_induit_nappe, densite_joule, densite_joule_complexe,
                       noyau_reaction_k, resoudre_psi, resoudre_psi_complexe)


def _lisser_source(Q: np.ndarray, grille: Grille3D, sigma_mm: float) -> np.ndarray:
    """Étale la source Q dans le plan (x, y) par une gaussienne de longueur
    ``sigma_mm`` (mm), tranche z par tranche z, en CONSERVANT la puissance de
    chaque tranche (renormalisation). Représente la DÉLOCALISATION du courant de
    Foucault dans le twill TISSÉ (résistance de contact aux croisements) — la
    nappe continue idéalisée met un q≈0 exact à l'« œil de boucle » au centre du
    spot, que la réalité remplit (cf. resultats_diag_centre_transitoire.log).
    ``sigma_mm <= 0`` -> identité (chemin historique inchangé)."""
    if sigma_mm <= 0.0:
        return Q
    sig = (sigma_mm * 1e-3) / grille.dx          # en mailles (dx = dy)
    out = Q.copy()
    for k in range(Q.shape[2]):
        s = Q[:, :, k]
        tot = float(s.sum())
        if tot <= 0.0:
            continue
        sm = gaussian_filter(s, sigma=sig, mode="nearest")
        ssum = float(sm.sum())
        out[:, :, k] = sm * (tot / ssum) if ssum > 0.0 else s
    return out


def _grille_y_etendue(grille: Grille3D, lambda_bord_mm: float) -> tuple[np.ndarray, int]:
    """Grille en y étendue de ``lambda_bord_mm`` (mm) de part et d'autre du
    domaine physique, même pas ``grille.dy`` (cf. docstring module,
    ``lambda_bord_mm``). Renvoie ``(y_etendu, n_pad)`` -- ``n_pad`` mailles
    ajoutées de chaque côté (``psi=0`` sera imposé sur cette frontière
    étendue, PAS sur le bord physique)."""
    n_pad = max(1, int(np.ceil((lambda_bord_mm * 1.0e-3) / grille.dy)))
    y_bas = grille.y[0] - grille.dy * np.arange(n_pad, 0, -1)
    y_haut = grille.y[-1] + grille.dy * np.arange(1, n_pad + 1)
    return np.concatenate([y_bas, grille.y, y_haut]), n_pad


def _grille_x_etendue(grille: Grille3D, lambda_bord_x_mm: float) -> tuple[np.ndarray, int]:
    """Grille en x étendue de ``lambda_bord_x_mm`` (mm) de part et d'autre du
    domaine physique, même pas ``grille.dx`` -- analogue à ``_grille_y_etendue``
    mais pour les bords x=0/x=nx-1 (bords RÉELS de longueur de la plaque, cf.
    docstring module, ``lambda_bord_x_mm``). Renvoie ``(x_etendu, n_pad)``."""
    n_pad = max(1, int(np.ceil((lambda_bord_x_mm * 1.0e-3) / grille.dx)))
    x_bas = grille.x[0] - grille.dx * np.arange(n_pad, 0, -1)
    x_haut = grille.x[-1] + grille.dx * np.arange(1, n_pad + 1)
    return np.concatenate([x_bas, grille.x, x_haut]), n_pad


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
    centre_y: float | None = None,
    champ_reaction: bool = False,
    lissage_sigma_mm: float = 0.0,
    lambda_bord_mm: float = 0.0,
    lambda_bord_x_mm: float | None = None,
) -> np.ndarray:
    """Champ source Q (nx, ny, nz) en W/m³ pour la bobine centrée en ``centre_x``.

    ``decalage_x`` (m) décale le centre EFFECTIF de la bobine par rapport au
    ``centre_x`` nominal du spot (incertitude de positionnement bobine/MFC au
    montage, cf. geometrie.yaml:coil.decalage_x). Seule la bobine bouge : le
    masque céramique/MFC (masque_empreinte_cfc) reste posé à ``centre_x`` —
    c'est un décalage bobine<->reste du montage, pas un déplacement du spot.

    ``centre_y`` (m, absolu ; ``None`` = centre de largeur ``laminate.largeur/2``)
    positionne la bobine en LARGEUR — permet les passes décalées en y (planificateur
    de soudage uniforme). ``None`` reproduit le comportement historique bit-à-bit.

    ``champ_reaction`` (défaut False, cf. docstring module) : active la
    résolution auto-cohérente complexe Bz_total = Bz_bobine + Bz_induit[ψ]
    (une nappe par couche, couplage inter-couches inclus) en lieu et place de
    l'atténuation ad hoc ``attenuation_blindage``. Comportement HISTORIQUE
    strictement inchangé si False (chemin non touché, non-régression
    bit-à-bit).

    ``lissage_sigma_mm`` (défaut 0.0 = inchangé) : étale la source dans le plan
    par une gaussienne de longueur sigma_mm (délocalisation du courant, twill
    tissé), puissance conservée par tranche z — cf. ``_lisser_source`` et
    resultats_diag_centre_transitoire.log (remplit l'« œil de boucle » au centre
    du spot que la nappe continue idéalisée met à zéro).

    ``lambda_bord_mm`` (défaut 0.0 = inchangé, BIT-À-BIT) : repousse la BC
    ``psi=0`` de ``lambda_bord_mm`` au-delà du bord physique en y (largeur),
    au lieu de l'imposer exactement au chant — cf. docstring module, section
    « Adoucissement du bord ». Adoucit le contraste chant/centre du profil en
    « M » sans toucher au reste du domaine ni à ``foucault.py``. Incompatible
    avec ``champ_reaction=True`` (``ValueError`` explicite, interaction non
    explorée).

    ``lambda_bord_x_mm`` (défaut ``None`` = ACTIF/AUTO depuis 2026-08-30) : même
    dispositif que ``lambda_bord_mm`` mais appliqué au bord EN X (x=0/x=longueur,
    bords RÉELS de longueur de la plaque) — cf. docstring module, section
    « Adoucissement du bord EN X ». Corrige l'artefact localisé de bascule
    bord-piqué -> centre-piqué du profil q(y) sur les quelques mailles
    précédant le chant x pour un spot proche du bord (Jx forcé à 0 sur toute
    la ligne de bord par la BC ``psi=0``). Valeurs acceptées :
    ``None`` (DÉFAUT) = ACTIF, longueur de relaxation = épaisseur PROPRE de
    chaque couche (``couche.epaisseur``, aucun paramètre libre supplémentaire) ;
    ``0.0`` = désactivé, chemin historique bit-à-bit ;
    un ``float`` positif = ACTIF, même longueur (mm) pour toutes les
    couches (ablation/tests). Incompatible avec ``champ_reaction=True`` : dans
    ce cas le DÉFAUT (``None``) cède silencieusement (désactivé) ; seule une
    valeur EXPLICITE positive lève une ``ValueError``.
    """
    # Correction de bord x ACTIVE par défaut ; incompatible avec le champ de
    # réaction -> le défaut (None) cède, on ne lève que si demandé explicitement (>0).
    if champ_reaction and lambda_bord_x_mm is None:
        lambda_bord_x_mm = 0.0
    bord_x_actif = (lambda_bord_x_mm is None) or (float(lambda_bord_x_mm) > 0.0)
    if (lambda_bord_mm > 0.0 or bord_x_actif) and champ_reaction:
        raise ValueError(
            "lambda_bord_mm/lambda_bord_x_mm actif avec champ_reaction=True : "
            "combinaison non explorée (cf. docstring module) -- désactiver l'un des deux."
        )

    omega = 2.0 * np.pi * float(cfg.geometrie["generateur"]["frequence"])
    mu_r = float(cfg.geometrie["cfc"]["mu_r"])
    z_miroir = plan_miroir_cfc(cfg)
    sommets = sommets_bobine(cfg, centre_x + decalage_x, centre_y=centre_y)
    X, Y = np.meshgrid(grille.x, grille.y, indexing="ij")

    bord_souple_y = lambda_bord_mm > 0.0
    if bord_souple_y:
        y_ext, n_pad_y_global = _grille_y_etendue(grille, lambda_bord_mm)

    Q = np.zeros((grille.nx, grille.ny, grille.nz))

    if not champ_reaction:
        for couche in couches:
            att = attenuation_blindage(couche, couches, omega)

            iz = np.where((grille.z >= couche.z_min - 1e-12) & (grille.z <= couche.z_max + 1e-12))[0]
            if len(iz) == 0:
                iz = np.array([grille.indice_z(couche.z_mid)])
            # conservation de la puissance surfacique q·t sur les nœuds retenus
            poids = couche.epaisseur / (len(iz) * grille.dz)

            # lambda_bord_x_mm : longueur de relaxation en x PROPRE À LA
            # COUCHE (défaut = épaisseur de la couche, cf. docstring module
            # "Adoucissement du bord EN X") -- doit donc être résolue par
            # couche, pas une fois pour tout l'appel (contrairement à
            # lambda_bord_mm en y, un seul scalaire global).
            if lambda_bord_x_mm is None:
                lam_x_mm = couche.epaisseur * 1.0e3
            else:
                lam_x_mm = float(lambda_bord_x_mm)
            bord_souple_x = lam_x_mm > 0.0
            bord_souple = bord_souple_x or bord_souple_y

            if bord_souple:
                if bord_souple_x:
                    x_dom, n_pad_x = _grille_x_etendue(grille, lam_x_mm)
                else:
                    x_dom, n_pad_x = grille.x, 0
                if bord_souple_y:
                    y_dom, n_pad_y = y_ext, n_pad_y_global
                else:
                    y_dom, n_pad_y = grille.y, 0
                X_dom, Y_dom = np.meshgrid(x_dom, y_dom, indexing="ij")

            # Bz (et donc ψ, q) est échantillonné à la profondeur propre de
            # chaque nœud retenu plutôt qu'une seule fois au plan médian : une
            # couche homogénéisée épaisse (laminé sup/inf) peut couvrir plusieurs
            # nœuds sur lesquels Bz varie significativement (cf. docstring module).
            for k in iz:
                z_k = grille.z[k] if len(iz) > 1 else couche.z_mid
                if bord_souple:
                    # BC psi=0 repoussée de lambda_bord_mm/lambda_bord_x_mm
                    # au-delà du bord physique en y/x (cf. docstring module,
                    # "Adoucissement du bord" / "Adoucissement du bord EN X") ;
                    # ρ, ω, Bz échantillonné exactement comme le chemin
                    # historique, seule la frontière du domaine résolu change
                    # -- foucault.resoudre_psi non modifié.
                    Bz_dom = bz_plan(sommets, courant, X_dom, Y_dom, z_plan=-z_k,
                                     mu_r_cfc=mu_r, z_miroir=z_miroir)
                    psi_dom = resoudre_psi(Bz_dom, grille.dx, grille.dy,
                                           couche.rho_xx, couche.rho_yy, omega)
                    psi = psi_dom[n_pad_x:n_pad_x + grille.nx, n_pad_y:n_pad_y + grille.ny]
                else:
                    Bz = bz_plan(sommets, courant, X, Y, z_plan=-z_k,
                                mu_r_cfc=mu_r, z_miroir=z_miroir)
                    psi = resoudre_psi(Bz, grille.dx, grille.dy,
                                       couche.rho_xx, couche.rho_yy, omega)
                q = densite_joule(psi, grille.dx, grille.dy, couche.rho_xx, couche.rho_yy)
                Q[:, :, k] += q * att * poids

        return facteur_couplage * _lisser_source(Q, grille, lissage_sigma_mm)

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

    return facteur_couplage * _lisser_source(Q, grille, lissage_sigma_mm)
