#!/usr/bin/env python
"""Issue #74 — valider.py (3D) avec un k_z plus faible dans le laminé inférieur.

    python code/scripts/diag/diag_valider_kz_inf.py --kz-inf 0.1 -- \\
        --modele 3D --facteur 6.0123 --h-contact 40 --h-bas 15 --essais serieA_A-1 ...

Tout ce qui suit ``--`` est transmis tel quel à valider.py. Le k_z du laminé
inférieur est imposé en remplaçant, pour ce processus seulement,
``Materiau.k_z_field`` (et en activant le chemin flux-conservatif à k variable
du solveur 3D) : aucune modification de jumeau/ ni de valider.py. Le masque
« sous l'interface » est reconstruit à partir de nz et des épaisseurs de la
config, exactement comme dans ``diag_epaisseur_3d_reference.appliquer_kz_inf``.
"""
from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path

import numpy as np

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))

from jumeau.materiaux import Config, Materiau  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--kz-inf", type=float, required=True)
a, reste = ap.parse_known_args()
if reste and reste[0] == "--":
    reste = reste[1:]

lam = Config.charger(R / "code" / "config").geometrie["laminate"]
EP_TOT = lam["epaisseur_sup"] + lam["epaisseur_film"] + lam["epaisseur_inf"]
Z_COUPE = lam["epaisseur_sup"] + lam["epaisseur_film"] / 2


def _k_z_field(self, T):
    z = np.linspace(0.0, EP_TOT, T.shape[-1])
    return np.where((z > Z_COUPE)[None, None, :], a.kz_inf, float(self.k_z)) * np.ones_like(T)


Materiau.a_k_variable = lambda self: True
Materiau.k_z_field = _k_z_field
Materiau.k_plan_field = lambda self, T: np.full_like(T, float(self.k_plan))

print(f"[diag_valider_kz_inf] k_z laminé inférieur = {a.kz_inf} W/m.K", flush=True)
sys.argv = [str(R / "code" / "scripts" / "valider.py")] + reste
runpy.run_path(sys.argv[0], run_name="__main__")
