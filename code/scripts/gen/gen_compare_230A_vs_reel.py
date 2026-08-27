#!/usr/bin/env python3
"""Comparaison prédit ↔ mesuré — cycle semi-statique ~230 A piloté sur TC=390.

Superpose les 5 TC PRÉDITS (modèle 2D, θ*, pilotage TC=360 modèle ≈ 390 réel,
cf. gen_cycle_230A_TC390.py) aux 5 TC MESURÉS de l'essai labo réel 231 A du
26/08. Re-cale les deux sur l'amorçage (t=0 = début de chauffe passe 1).

Sortie : biblio/labo/figures/fig_compare_230A_vs_reel.png
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts" / "gen"))
sys.path.insert(0, str(R / "code" / "scripts"))
import gen_cycle_230A_TC390 as m  # noqa: E402
from _style import savefig, OKABE_ITO  # noqa: E402

FICH_REEL = str(R / "donnees" / "data" / "exp10_cycle-semistatique_231A_2026-08-26"
                / "231A_semistatique_bord_2026-08-26.txt")
COURANT = 231.0
COUL = [OKABE_ITO[c] for c in ("noir", "bleu", "vert", "orange", "vermillon")]


def charger_reel():
    df = pd.read_csv(FICH_REEL, sep="\t", decimal=",")
    df.columns = [c.strip() for c in df.columns]
    t = df["Time (s)"].to_numpy(float).copy()
    t = t - t[0]
    series = {}
    for i in range(1, 6):
        c = next(x for x in df.columns if x.startswith(f"TC{i}"))
        y = pd.to_numeric(df[c], errors="coerce").to_numpy(float).copy()
        y[(y > 800) | (y < 0)] = np.nan
        series[f"TC{i}"] = y
    # recaler sur l'amorçage : 1er instant où le max des TC dépasse ambiant+15
    amb = np.nanmedian(np.vstack([series[f"TC{i}"][:10] for i in range(1, 6)]))
    maxtc = np.nanmax(np.vstack([series[f"TC{i}"] for i in range(1, 6)]), axis=0)
    i0 = int(np.argmax(maxtc > amb + 15))
    t = t - t[i0]
    return t, series, i0


if __name__ == "__main__":
    from PIL import Image
    print("simulation du modèle (231 A)…")
    res = m.simuler_cycle_tc(COURANT)
    t_sim, series_sim, noms = res["t"], res["series"], res["noms"]
    t_reel, series_reel, i0 = charger_reel()

    fig, ax = plt.subplots(figsize=(11.5, 5.2))
    for nom, coul in zip(noms, COUL):
        ax.plot(t_reel, series_reel[nom], color=coul, lw=1.6, alpha=0.9, label=f"{nom} mesuré")
        ax.plot(t_sim, series_sim[nom], color=coul, lw=1.3, ls=(0, (4, 1.8)), label=f"{nom} prédit")
    ax.axhline(390, color=OKABE_ITO["vert"], lw=0.9, ls="--", zorder=1)
    ax.axhline(337, color=OKABE_ITO["cyan"], lw=0.9, ls=":", zorder=1)
    ax.text(ax.get_xlim()[1], 393, " consigne 390", fontsize=7.5, color=OKABE_ITO["vert"], va="bottom", ha="right")

    ax.set_xlim(0, max(t_sim[-1], t_reel[-1]))
    ax.set_ylim(0, 560)
    ax.set_xlabel("Temps (s) — recalé sur l'amorçage")
    ax.set_ylabel("Température (°C)")
    ax.set_title("Validation 231 A — TC mesurés (trait plein) vs prédits (pointillé), pilotage TC=390",
                 fontsize=12, fontweight="bold")
    ax.legend(loc="upper right", ncol=2, fontsize=7.5, framealpha=0.93)
    fig.tight_layout()
    savefig(fig, R / "biblio" / "labo" / "figures" / "fig_compare_230A_vs_reel")
    plt.close(fig)

    print("\n=== Pics : prédit (modèle) vs mesuré (231 A) ===")
    print(f"{'TC':>4} | {'prédit':>7} | {'mesuré':>7} | {'écart':>6}")
    for nom in noms:
        pp = float(np.max(series_sim[nom]))
        pm = float(np.nanmax(series_reel[nom]))
        print(f"{nom:>4} | {pp:7.0f} | {pm:7.0f} | {pp - pm:+6.0f}")
    # RMSE sur les TC intérieurs interpolés sur la grille réelle (fenêtre commune)
    tmax = min(t_sim[-1], t_reel[-1])
    grille = np.linspace(0, tmax, 400)
    for nom in ("TC2", "TC3", "TC4"):
        sm = np.interp(grille, t_reel, series_reel[nom])
        sp = np.interp(grille, t_sim, series_sim[nom])
        ok = ~np.isnan(sm)
        rmse = float(np.sqrt(np.mean((sp[ok] - sm[ok]) ** 2)))
        print(f"  RMSE {nom} = {rmse:.0f} °C")
    print("figure -> biblio/labo/figures/fig_compare_230A_vs_reel.png")
