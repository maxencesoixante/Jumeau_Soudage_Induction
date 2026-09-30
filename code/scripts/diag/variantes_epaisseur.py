"""Issue #74 — variantes du transport thermique dans l'épaisseur, appliquées au
3D SANS modifier jumeau/ : chaque fonction remplace une méthode de classe pour
la durée du processus (diagnostic uniquement).

- ``appliquer_kz_inf(kz_inf)``   : k_z réduit dans tout le laminé inférieur
  (forme effective, testée le 2026-09-29/30) ;
- ``appliquer_rc_fusion(R, dT)`` : résistance de contact À L'INTERFACE, active
  tant que l'interface n'a pas fondu, nulle au-dessus de Tf (rampe linéaire sur
  Tf ± dT). Forme physique visée : deux pièces séparées (film, contacts
  imparfaits) qui ne deviennent un seul solide qu'à la fusion. À distinguer de
  ``r_contact_interface`` (constante, NO-GO le 2026-08-13) ;
- ``appliquer_cp_hamon()``       : ligne de base cp(T) mesurée (Hamon 2025 /
  thèse Saffar 2019, cf. materiaux.yaml) à la place de cp_base constant ; le pic
  de fusion gaussien est conservé.

Toutes se combinent. Le masque « sous l'interface » et l'indice de la face
d'interface viennent de la grille et de la config, comme dans le solveur.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))

from jumeau.materiaux import Config, Materiau  # noqa: E402
from jumeau.thermique import solveur3d as s3  # noqa: E402

_LAM = Config.charger(R / "code" / "config").geometrie["laminate"]
_EP_TOT = _LAM["epaisseur_sup"] + _LAM["epaisseur_film"] + _LAM["epaisseur_inf"]
_Z_COUPE = _LAM["epaisseur_sup"] + _LAM["epaisseur_film"] / 2

# Cp(T) mesuré, ligne de base sans pic de fusion (materiaux.yaml, Hamon 2025)
CP_T = np.array([50, 100, 150, 200, 250, 300, 350, 400, 450], dtype=float)
CP_V = 1000.0 * np.array([0.939, 1.090, 1.224, 1.341, 1.441, 1.524, 1.590, 1.639, 1.671])


def appliquer_kz_inf(kz_inf: float) -> None:
    def _k_z_field(self, T):
        z = np.linspace(0.0, _EP_TOT, T.shape[-1])
        return np.where((z > _Z_COUPE)[None, None, :], kz_inf, float(self.k_z)) * np.ones_like(T)

    Materiau.a_k_variable = lambda self: True
    Materiau.k_z_field = _k_z_field
    Materiau.k_plan_field = lambda self, T: np.full_like(T, float(self.k_plan))


def appliquer_cp_hamon() -> None:
    def _cp_apparent(self, T):
        sig_f = self.delta_T_fusion / 2.0
        pic = (self.chaleur_latente / (sig_f * np.sqrt(2.0 * np.pi))) * np.exp(
            -0.5 * ((T - self.T_fusion) / sig_f) ** 2)
        return np.interp(T, CP_T, CP_V) + pic

    Materiau.cp_apparent = _cp_apparent


def appliquer_rc_fusion(r_c: float, largeur: float = 5.0) -> None:
    """Ajoute, sur la face entre les nœuds iz_interface et iz_interface+1, la
    correction de flux d'une résistance r_c (m²·K/W) en série, pondérée par
    f = 1 sous Tf − largeur, 0 au-dessus de Tf + largeur (T = max des deux
    nœuds de la face : l'interface fond dès que son côté chaud fond)."""
    orig = s3.SolveurThermique3D._rhs

    def _rhs(self, t, Tflat, source_fn):
        out = orig(self, t, Tflat, source_fn)
        g, mat = self.g, self.mat
        T = Tflat.reshape(g.nx, g.ny, g.nz)
        iz = g.iz_interface
        Ta, Tb = T[:, :, iz], T[:, :, iz + 1]
        f = np.clip((mat.T_fusion + largeur - np.maximum(Ta, Tb)) / (2.0 * largeur), 0.0, 1.0)
        if mat.a_k_variable():
            kzf = mat.k_z_field(T)
            kface = 0.5 * (kzf[:, :, iz] + kzf[:, :, iz + 1])
        else:
            kface = float(mat.k_z)
        g0 = kface / g.dz
        gc = 1.0 / (g.dz / kface + r_c * f)
        dflux = (gc - g0) * (Tb - Ta)                     # W/m²
        rc = mat.densite * mat.cp_apparent(T)
        o = out.reshape(g.nx, g.ny, g.nz).copy()
        o[:, :, iz] += dflux / g.dz / rc[:, :, iz]
        o[:, :, iz + 1] -= dflux / g.dz / rc[:, :, iz + 1]
        return o.ravel()

    s3.SolveurThermique3D._rhs = _rhs
