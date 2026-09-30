#!/usr/bin/env python
"""Issue #74 — valider.py (3D) avec une ou plusieurs variantes d'épaisseur
(cf. variantes_epaisseur.py) :

    python code/scripts/diag/diag_valider_variante.py [--kz-inf K] [--rc-fusion R] [--cp-hamon] -- \\
        --modele 3D --facteur F --h-contact H --h-bas 15 --essais ...

Tout ce qui suit ``--`` est transmis tel quel à valider.py.
"""
from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import variantes_epaisseur as var  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--kz-inf", type=float, default=None)
ap.add_argument("--rc-fusion", type=float, default=None)
ap.add_argument("--cp-hamon", action="store_true")
a, reste = ap.parse_known_args()
if reste and reste[0] == "--":
    reste = reste[1:]
if a.kz_inf is not None:
    var.appliquer_kz_inf(a.kz_inf)
if a.rc_fusion is not None:
    var.appliquer_rc_fusion(a.rc_fusion)
if a.cp_hamon:
    var.appliquer_cp_hamon()
print(f"[diag_valider_variante] kz_inf={a.kz_inf} rc_fusion={a.rc_fusion} cp_hamon={a.cp_hamon}", flush=True)
sys.argv = [str(var.R / "code" / "scripts" / "valider.py")] + reste
runpy.run_path(sys.argv[0], run_name="__main__")
