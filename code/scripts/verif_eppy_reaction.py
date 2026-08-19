#!/usr/bin/env python3
"""Vérification croisée du solveur EM — jumeau (Lin 1993, ψ) vs eppy (Nagel 2019, T).

CONTEXTE
--------
`eppy` (W.J.B. Grouve, https://github.com/wjbg/eppy, MIT, validé contre Nagel 2019)
résout les courants de Foucault en plaque mince par le potentiel vecteur électrique
`T` — mathématiquement équivalent à notre fonction de courant `ψ` (`em/foucault.py`,
Lin 1993). Deux différences de fond :
  1. eppy est ISOTROPE (rho scalaire) ; notre solveur est anisotrope (ρxx≠ρyy).
  2. eppy peut INCLURE le champ de réaction (self-inductance) des courants induits :
        K = M + Cx@N@Dy - Cy@N@Dx      (N = Biot-Savart du champ induit)
     là où notre modèle le NÉGLIGE (absorbé par `facteur_couplage`). eppy résout
     aussi `M` seul = sans réaction = exactement notre hypothèse.

QUESTION TESTÉE
---------------
Le champ de réaction adoucit-il le contraste chant/centre du courant (le « M ») ?
On résout le MÊME cas deux fois (M seul vs K complet) et on compare le contraste
en largeur. Balayages en épaisseur t et en conductivité sigma pour situer le régime
du jumeau (twill : t≈0,2 mm, sigma≈1,1e4 S/m, f=388 kHz).

RÉSULTAT (cf. journaux/archive/resultats_verif_eppy_reaction.log, docs/modele/verification_croisee_eppy.md)
  - Contraste ≈ 3,0 reproduit par eppy (indépendant) ≈ notre 3,15 → le M est de la
    VRAIE physique plaque-mince (écrasement du courant au chant T=0 ≡ ψ=0), pas un bug.
  - Réaction NÉGLIGEABLE au régime du jumeau (−0,03 % au twill ; −5,9 % même à 3,36 mm)
    → pas un correctif du résidu #3, et justifie de la négliger.

REPRODUCTION
------------
  # eppy est vendoré (copie MIT au commit 62f0030, patché numpy≥2) dans
  # third_party/eppy/ — rien à cloner ni patcher :
  .venv/bin/python scripts/verif_eppy_reaction.py

  # (override optionnel vers un autre clone : EPPY_DIR=/chemin/vers/eppy)
  # Provenance et procédure de régénération du vendor : third_party/eppy/NOTICE.md
"""
import os
import sys
from pathlib import Path

import numpy as np

# Par défaut : la copie vendorée (rejouable hors-ligne). EPPY_DIR peut pointer ailleurs.
_VENDORED_EPPY = Path(__file__).resolve().parent.parent / "third_party" / "eppy"
EPPY_DIR = os.environ.get("EPPY_DIR", str(_VENDORED_EPPY))
if not os.path.isdir(EPPY_DIR):
    sys.exit(f"eppy introuvable ({EPPY_DIR}). Voir la section REPRODUCTION du docstring.")
sys.path.insert(0, EPPY_DIR)
import eppy                       # noqa: E402
from coil_geom import hairpin     # noqa: E402


def solve_case(sigma, t, f, Lx=0.12, Ly=0.04, dx=0.002,
               coil_len=0.0315, coil_w=0.01235, height=0.005, current=1.0):
    """Retourne (contraste_M, contraste_K) pour un cas plaque + hairpin.

    contraste = |J|(lobe de chant) / |J|(centre) sur le profil en largeur (y) à
    mi-longueur. M = sans réaction ; K = avec champ de réaction.
    """
    dy = dx
    Nx = int(np.ceil(Lx / dx + 1))
    Ny = int(np.ceil(Ly / dy + 1))
    X = np.linspace(-Lx / 2, Lx / 2, Nx)
    Y = np.linspace(-Ly / 2, Ly / 2, Ny)
    pos = np.array([np.array([x, y, 0]) for y in Y for x in X])
    rho = 1.0 / sigma
    omega = 2 * np.pi * f

    M = eppy.system_matrix(rho, dx, dy, Nx, Ny)
    N = eppy.biot_savart_matrix(X, Y, t)
    Cx, Cy = eppy.contour_matrices(dx, dy, Nx, Ny, omega)
    Dx, Dy = eppy.derivative_matrices(dx, dy, Nx, Ny)
    K = M + Cx @ N @ Dy - Cy @ N @ Dx

    R, dl = hairpin(np.array([0.0, 0.0, height]), coil_len, coil_w)
    Bz = eppy.biot_savart(dl, R, pos, current)[:, 2]
    flux = eppy.rhs(Bz, omega, dx, dy)
    mask = eppy.mask_bc(Nx, Ny)

    def solve(A):
        T = np.zeros(Nx * Ny, dtype=complex)
        T[mask] = np.linalg.solve(A[:, mask][mask, :], flux[mask])
        Jmag = np.abs(np.sqrt((Dy @ T) ** 2 + (-Dx @ T) ** 2))
        return Jmag.reshape(Ny - 1, Nx - 1)

    def contrast(J):
        col = J[:, J.shape[1] // 2]
        ny = col.shape[0]
        edge = max(1, ny // 5)
        lobe = max(col[:edge].max(), col[-edge:].max())
        centre = col[ny // 2]
        return lobe / centre if centre > 0 else np.nan

    return contrast(solve(M)), contrast(solve(K))


def main():
    f, sigma_twill = 388e3, 1.1e4
    print(f"Vérification croisée eppy — régime jumeau : f={f/1e3:.0f} kHz, coupon 120x40 mm, dx=2 mm\n")

    print(f"Balayage ÉPAISSEUR (sigma={sigma_twill:.1e} S/m) :")
    print(f"{'t (mm)':>7} | {'contraste M':>12} | {'contraste K':>12} | {'Δ%':>7}")
    print("-" * 48)
    for t_mm in [0.2, 0.5, 1.0, 2.0, 3.36]:
        cM, cK = solve_case(sigma_twill, t_mm * 1e-3, f)
        print(f"{t_mm:>7.2f} | {cM:>12.3f} | {cK:>12.3f} | {100*(cK-cM)/cM:>+6.1f}%")

    print(f"\nBalayage CONDUCTIVITÉ (t=0,2 mm, twill) :")
    print(f"{'sigma (S/m)':>12} | {'contraste M':>12} | {'contraste K':>12} | {'Δ%':>7}")
    print("-" * 53)
    for sig in [3.4e0, 1.1e4, 2.2e4, 5e4, 1e5]:
        cM, cK = solve_case(sig, 0.2e-3, f)
        print(f"{sig:>12.1e} | {cM:>12.3f} | {cK:>12.3f} | {100*(cK-cM)/cM:>+6.2f}%")

    print("\nRéférence jumeau : M mesuré = 2,09 ; modèle = 3,15 (réduction requise ~ -34%).")
    print("Conclusion : réaction négligeable au régime du jumeau ; contraste ~3 reproduit "
          "par un code indépendant → M = physique plaque-mince réelle, pas un bug.")


if __name__ == "__main__":
    main()
