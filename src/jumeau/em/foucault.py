"""Courants de Foucault en plaque mince anisotrope — fonction de courant ψ.

Hypothèses (Lin 1993 ; Grouve 2020) :
- plaque mince devant la profondeur de peau (δ ≈ 6 mm à 300 kHz pour
  σ0 = 2,2·10⁴ S/m > épaisseur 3,36 mm) → courants plans, Bz uniforme dans
  l'épaisseur de chaque couche conductrice ;
- champ de réaction (blindage) NÉGLIGÉ par défaut — l'écart est absorbé par
  le facteur d'efficacité calibré (``facteur_couplage``), cf. README
  « limites ». Modélisable explicitement (2026-07-21, cf. ``bz_induit_nappe``
  et ``source_joule.champ_reaction``) — voir cette docstring pour l'analyse
  d'ordre de grandeur et la mise en garde anti double-comptage ;
- tous les courants portés par les fibres ; chaque couche (twill suscepteur,
  laminé homogénéisé) porte son propre tenseur de résistivité plan.

Formulation : J = ∇×(ψ ẑ) (Jx = ∂ψ/∂y, Jy = −∂ψ/∂x) garantit ∇·J = 0.
La loi de Faraday en phasor (∇×E)z = −jωBz avec E = ρ̃J donne :

    ∂/∂x(ρyy ∂ψ/∂x) + ∂/∂y(ρxx ∂ψ/∂y) = jω·Bz

Avec Bz réel (référence de phase) ET le champ de réaction négligé, ψ est en
quadrature pure : on résout le problème réel  ρyy·ψxx + ρxx·ψyy = ω·Bz  avec
ψ = 0 au bord (aucun courant ne traverse le chant de la plaque). Le courant
d'excitation étant une valeur RMS, Bz est RMS et la dissipation moyenne est
q = ρxx·Jx² + ρyy·Jy² (W/m³).

Champ de réaction (``bz_induit_nappe``, ``resoudre_psi_complexe`` — 2026-07-21)
--------------------------------------------------------------------------
Bz_total = Bz_bobine + Bz_induit[ψ] rend le problème intégro-différentiel et,
puisque le blindage introduit un déphasage, RÉELLEMENT complexe (ψ n'est plus
en quadrature pure avec Bz_bobine). ``bz_induit_nappe`` calcule Bz_induit de
façon EXACTE (magnétostatique, pas d'approximation de demi-espace infini) :
pour une nappe de courant plane (fonction de courant ψ, éventuellement
complexe) à support compact (ψ=0 hors plaque, déjà garanti par la BC), le
champ Bz qu'elle génère à une distance verticale dz de son propre plan
s'écrit, mode de Fourier k=(kx,ky) par mode de Fourier :

    Bz_induit(k) = (µ0·|k| / 2) · Ψ(k) · exp(−|k|·|dz|),   Ψ = ψ·épaisseur

(dérivation : potentiel vecteur A ~ exp(−|k|·|z|) de part et d'autre de la
nappe, saut standard [∂A/∂z] = −µ0·K à la traversée d'un courant surfacique
K = ∇×(Ψẑ) ; voir calcul détaillé dans le rapport
``resultats_champ_reaction_em.log``). Cette relation est LOCALE en k, donc
valable telle quelle (TF/TF⁻¹, zero-padding pour éviter le repliement
périodique) pour n'importe quelle nappe à support compact — pas besoin d'un
modèle de plaque infinie.

Ordre de grandeur (à ω = 2π·388 kHz, cf. ``generateur.frequence``) : le
paramètre de blindage adimensionné pertinent est S' = µ0·σ·t·ω/(2k), PAS
µ0·σ·t·ω·L (facteur π en trop dans une estimation grossière par analogie
dimensionnelle L↔1/k) — au mode fondamental k₁=π/W (W=40 mm, largeur
échantillon, le mode le PLUS sensible au blindage puisque S'∝1/k) :
S'(twill) ≈ 0,06, S'(laminé) ≈ 0,02 → réduction de PUISSANCE (∝|1/(1+jS')|²)
de l'ordre de 0,03 à 0,4 % pour ce seul mode. Une vérification numérique
complète sur une nappe isolée (champ Bz réel de la bobine, tous modes, pas
juste le fondamental) confirme cette petite réduction : ~0,2-0,6 % de
puissance par couche (twill/laminé sup/laminé inf), RÉDUCTRICE comme attendu
sur un mode isolé (cf. rapport dédié, ``resultats_champ_reaction_em.log``).

ATTENTION : le bilan NET observé dans ``source_joule.source_spot`` quand
``champ_reaction=True`` (~+11 % au lieu d'une réduction) n'est PAS la
réaction ci-dessus mais la conséquence de la DÉSACTIVATION simultanée de
``attenuation_blindage`` (écran ad hoc plus gros, −12 à −18 % à ces
paramètres) — les deux effets ne doivent pas être confondus, cf. docstring
``source_joule.py`` §3 du rapport pour la décomposition complète.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

from .champ_coil import MU0


def resoudre_psi(Bz: np.ndarray, dx: float, dy: float,
                 rho_xx: float, rho_yy: float, omega: float) -> np.ndarray:
    """Résout ρyy·ψxx + ρxx·ψyy = ω·Bz, ψ=0 au bord. Renvoie ψ (nx, ny), A/m."""
    nx, ny = Bz.shape
    nxi, nyi = nx - 2, ny - 2                      # inconnues intérieures
    if nxi <= 0 or nyi <= 0:
        return np.zeros_like(Bz)

    ax = rho_yy / dx**2
    ay = rho_xx / dy**2
    n = nxi * nyi

    idx = np.arange(n).reshape(nxi, nyi)
    diag_c = np.full(n, -2.0 * (ax + ay))
    lignes = [idx.ravel()]
    cols = [idx.ravel()]
    vals = [diag_c]
    # voisins x
    lignes += [idx[1:, :].ravel(), idx[:-1, :].ravel()]
    cols += [idx[:-1, :].ravel(), idx[1:, :].ravel()]
    vals += [np.full(idx[1:, :].size, ax), np.full(idx[1:, :].size, ax)]
    # voisins y
    lignes += [idx[:, 1:].ravel(), idx[:, :-1].ravel()]
    cols += [idx[:, :-1].ravel(), idx[:, 1:].ravel()]
    vals += [np.full(idx[:, 1:].size, ay), np.full(idx[:, 1:].size, ay)]

    A = sparse.csr_matrix(
        (np.concatenate(vals), (np.concatenate(lignes), np.concatenate(cols))),
        shape=(n, n),
    )
    b = omega * Bz[1:-1, 1:-1].ravel()
    psi = np.zeros_like(Bz)
    psi[1:-1, 1:-1] = spsolve(A, b).reshape(nxi, nyi)
    return psi


def resoudre_psi_complexe(Bz: np.ndarray, dx: float, dy: float,
                          rho_xx: float, rho_yy: float, omega: float) -> np.ndarray:
    """Comme ``resoudre_psi`` mais pour un Bz total complexe (champ de
    réaction actif, cf. docstring module). L'opérateur discret est réel
    (ρ, ω réels) : on résout séparément partie réelle et imaginaire de Bz
    avec exactement la même matrice creuse — pas d'approximation
    supplémentaire par rapport à ``resoudre_psi``, juste deux résolutions
    réelles au lieu d'une."""
    psi_re = resoudre_psi(Bz.real, dx, dy, rho_xx, rho_yy, omega)
    psi_im = resoudre_psi(Bz.imag, dx, dy, rho_xx, rho_yy, omega)
    return psi_re + 1j * psi_im


def densite_joule(psi: np.ndarray, dx: float, dy: float,
                  rho_xx: float, rho_yy: float) -> np.ndarray:
    """Dissipation Joule moyenne q(x, y) en W/m³ à partir de ψ (RMS)."""
    Jx = np.gradient(psi, dy, axis=1)              # ∂ψ/∂y
    Jy = -np.gradient(psi, dx, axis=0)             # −∂ψ/∂x
    return rho_xx * Jx**2 + rho_yy * Jy**2


def densite_joule_complexe(psi: np.ndarray, dx: float, dy: float,
                           rho_xx: float, rho_yy: float) -> np.ndarray:
    """Comme ``densite_joule`` mais pour ψ complexe (champ de réaction actif) :
    q = ρxx·|Jx|² + ρyy·|Jy|² (dissipation moyenne temporelle d'un courant en
    régime harmonique, ψ étant déjà une amplitude RMS — |·|² donne
    directement la valeur moyenne, pas de facteur 1/2 supplémentaire)."""
    Jx = np.gradient(psi, dy, axis=1)
    Jy = -np.gradient(psi, dx, axis=0)
    return (rho_xx * np.abs(Jx)**2 + rho_yy * np.abs(Jy)**2).real


def noyau_reaction_k(nx: int, ny: int, dx: float, dy: float, pad: int = 3) -> np.ndarray:
    """Norme |k| (rad/m) sur la grille de Fourier zero-paddée (``pad``× la
    taille du domaine dans chaque direction, pour éviter le repliement
    périodique de la convolution non locale — le courant est à support
    compact mais le noyau 1/r du champ magnétostatique ne l'est pas).
    Renvoie un tableau (pad·nx, pad·ny), réutilisable pour tous les appels de
    ``bz_induit_nappe`` sur une même grille (construit une seule fois par
    ``source_spot``)."""
    px, py = pad * nx, pad * ny
    kx = 2.0 * np.pi * np.fft.fftfreq(px, d=dx)
    ky = 2.0 * np.pi * np.fft.fftfreq(py, d=dy)
    KX, KY = np.meshgrid(kx, ky, indexing="ij")
    return np.sqrt(KX**2 + KY**2)


def bz_induit_nappe(psi: np.ndarray, epaisseur: float, Kmag: np.ndarray,
                    dz: float = 0.0) -> np.ndarray:
    """Champ Bz (complexe, A/m dimensionnellement converti en T) induit, à une
    distance verticale ``dz`` (m) de son propre plan, par une nappe de
    courant de fonction de courant ``psi`` (A/m, éventuellement complexe) et
    d'épaisseur ``epaisseur`` (m). Voir dérivation dans la docstring module.

    ``Kmag`` : noyau |k| précalculé par ``noyau_reaction_k`` sur la MÊME
    grille (nx, ny, dx, dy) que ``psi`` (évite de reconstruire les tableaux
    de fréquences à chaque appel — cette fonction est appelée O(n_couches²)
    fois par itération de point fixe).
    """
    nx, ny = psi.shape
    px, py = Kmag.shape
    Psi_pad = np.zeros((px, py), dtype=complex)
    Psi_pad[:nx, :ny] = psi * epaisseur
    Bk = np.fft.fft2(Psi_pad) * (MU0 * Kmag / 2.0) * np.exp(-Kmag * abs(dz))
    return np.fft.ifft2(Bk)[:nx, :ny]
