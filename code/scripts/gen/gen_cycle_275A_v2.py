#!/usr/bin/env python3
"""Prédiction FIGÉE (a priori) du cycle 275 A — layout de TC v2 (serie A/B).

Campagne hors-domaine 275 A (issue #66). Modèle 2D CANONIQUE (adopté). Pilotage
RÉEL de l'opérateur : couper chaque passe quand le TC de contrôle (proche du spot,
au bord) atteint 390 °C RÉEL = 360 °C modèle (biais −30 °C intérieur), puis
refroidir → Tg, avancer. Positions des TC = layout v2 : TC1(x=0) et TC5(x=120) au
CENTRE largeur y=20 ; TC2/3/4 (x=30/60/90) au bord y=0. Contrôle sur les TC de
bord (TC2/TC3/TC4). À FIGER avant l'essai (test falsifiable).

Sortie : biblio/labo/figures/fig_cycle_275A_v2_prediction.png
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts" / "gen"))
sys.path.insert(0, str(R / "code" / "scripts"))
import gen_cycle_parfait_semistatique as g  # noqa: E402
import gen_cycle_230A_TC390 as m  # noqa: E402  (machinerie pilotage TC)
from _style import savefig, OKABE_ITO  # noqa: E402

COURANT = 275.0
TC_V2 = {
    "TC1": {"x": 0.000, "y": 0.020, "z": "interface"},
    "TC2": {"x": 0.030, "y": 0.000, "z": "interface"},
    "TC3": {"x": 0.060, "y": 0.000, "z": "interface"},
    "TC4": {"x": 0.090, "y": 0.000, "z": "interface"},
    "TC5": {"x": 0.120, "y": 0.020, "z": "interface"},
}

_orig = g.construire_essai
def construire_v2(courant):
    e = _orig(courant)
    e.spec["thermocouples"] = TC_V2
    e.spec["tc_valides"] = list(TC_V2)
    return e
g.construire_essai = construire_v2   # simuler_cycle_tc l'utilise ; contrôle reste au bord (x_ctrl, y=0)

if __name__ == "__main__":
    from PIL import Image
    res = m.simuler_cycle_tc(COURANT)
    t, series, pc, passes, noms = res["t"], res["series"], res["pc"], res["passes"], res["noms"]
    couleurs = [OKABE_ITO[c] for c in ("noir", "bleu", "vert", "orange", "vermillon")]

    fig, ax = plt.subplots(figsize=(11.0, 4.7))
    for p in passes:
        ax.axvspan(p["t_deb"], p["t_fin_ch"], color="#E8E8E8", zorder=0)
        ax.axvspan(p["t_fin_ch"], p["t_fin_rf"], color="#F7F7F7", zorder=0)
        ax.axvline(p["t_fin_rf"], color="0.4", lw=0.6, zorder=1)
        mc = 0.5 * (p["t_deb"] + p["t_fin_ch"])
        ax.annotate(f"P{p['i']+1}\n{p['dwell']:.0f}s", (mc, 505), ha="center", va="center", fontsize=7, color="0.2")
    for nom, coul in zip(noms, couleurs):
        if nom in ("TC2", "TC3", "TC4"):        # FIABLES (bord, interior)
            ax.plot(t, series[nom], color=coul, lw=1.4, label=f"{nom} (x={TC_V2[nom]['x']*1000:.0f}, bord) — fiable")
        else:                                   # TC1/TC5 aux bords x : artefact de source, NON fiable
            ax.plot(t, series[nom], color="0.6", lw=1.0, ls=(0, (1, 1.5)),
                    label=f"{nom} (x={TC_V2[nom]['x']*1000:.0f}, bord x) — ARTEFACT, ignorer")
    for seuil, coul in ((g.T_FUSION, OKABE_ITO["cyan"]), (390.0, OKABE_ITO["vert"]), (g.T_DEGRAD, OKABE_ITO["vermillon"])):
        ax.axhline(seuil, color=coul, lw=0.9, ls="--", zorder=1)
    ax.axhline(g.T_REFROID, color="0.5", lw=0.9, ls=":", zorder=1)
    ax.set_xlim(0, t[-1]); ax.set_ylim(0, 560)
    ax.set_xlabel("Temps (s)"); ax.set_ylabel("Température (°C)")
    ax.set_title("PRÉDICTION FIGÉE 275 A (hors-domaine) — layout v2, pilotage TC=390 réel",
                 fontsize=11.5, fontweight="bold", pad=18)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.005), ncol=5, fontsize=6.4,
              columnspacing=0.9, handlelength=1.4, framealpha=0.92)
    note = ("Contrôle : couper quand le TC de bord proche du spot (TC2/TC3/TC4) atteint 360 °C modèle ≈ 390 °C réel, puis refroid.→Tg, avance.\n"
            "⚠ TC1/TC5 sont aux BORDS en x (x=0/120) où la source du modèle est mal distribuée (artefact ψ=0) → NON fiables, à ignorer. "
            "Marge à la dégradation NÉGATIVE au point chaud canonique (interface s'emballe) — le modèle fusion la plafonnerait ~510 °C.")
    ax.text(0.5, -0.32, note, transform=ax.transAxes, ha="center", va="top", fontsize=6.4, color="0.35", linespacing=1.5)
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    chemins = savefig(fig, R / "biblio" / "labo" / "figures" / "fig_cycle_275A_v2_prediction")
    plt.close(fig)

    def reel(n, v):
        return v + 30.0 if n in ("TC2", "TC3", "TC4") else v
    print("=== PRÉDICTION FIGÉE 275 A — layout v2, pilotage TC=390 réel ===")
    print(f"{'P':>2} | {'TCctrl':>6} | {'dwell':>6} | {'refroid':>7} | {'PC@cut':>6} | {'marge450':>8}")
    for p in passes:
        tcn = {0.030: "TC2", 0.060: "TC3", 0.090: "TC4"}[p["ctrl_x"]]
        mg = f"{p['marge']:.1f}" if not np.isnan(p["marge"]) else "n/a"
        print(f"{p['i']+1:>2} | {tcn:>6} | {p['dwell']:6.1f} | {p['duree_r']:7.1f} | {p['pc_at_cut']:6.0f} | {mg:>8}")
    print(f"\n  durée totale : {t[-1]:.0f} s ({t[-1]/60:.1f} min)")
    print("  Pics prédits par TC (modèle -> réel attendu) :")
    for n in noms:
        pos = TC_V2[n]; loc = "centre y=20" if abs(pos["y"]-0.020) < 1e-6 else "bord y=0"
        print(f"    {n} (x={pos['x']*1000:.0f}mm, {loc:11s}) : {series[n].max():6.1f} -> {reel(n, series[n].max()):6.1f} °C")
    print(f"  point chaud interface (canonique) : max {pc.max():.0f} °C  [modèle FUSION : ~500-520 °C attendu]")
    for c in chemins:
        if c.suffix.lower() == ".png":
            print(f"  figure : {c.name} ({Image.open(c).size[0]}x{Image.open(c).size[1]})")
