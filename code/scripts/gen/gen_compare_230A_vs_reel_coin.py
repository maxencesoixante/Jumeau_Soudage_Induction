#!/usr/bin/env python3
"""Comparaison prédit ↔ mesuré 231 A — AVEC correction de l'effet de coin x=0.

Le coin (x=0, y=0) est le point le PLUS chaud du vrai essai (TC1 = 392 °C), mais
le modèle canonique le sous-estime (302 °C) à cause du puits de bord effectif
`h_bord_x0 = 250` (non physique : chants tous libres, cf. materiaux.yaml). Ce puits
sur-refroidit le coin. On le ramène à sa valeur calibrée sur le coin réel,
**h_bord_x0 = 100** (TC1 → ~392 °C), SANS toucher au canonique — le solveur et la
config restent à 250, donc l'ancien résultat (gen_compare_230A_vs_reel.py) reste
pleinement reproductible. On superpose ici les deux prédictions (ancienne + corrigée)
au mesuré pour montrer le gain sur le coin.

Sortie : biblio/labo/figures/fig_compare_230A_vs_reel_coin.png (l'ancienne figure
fig_compare_230A_vs_reel.png est CONSERVÉE telle quelle).
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
import gen_cycle_parfait_semistatique as g  # noqa: E402
from _style import savefig, OKABE_ITO  # noqa: E402

FICH_REEL = str(R / "donnees" / "data" / "exp10_cycle-semistatique_231A_2026-08-26"
                / "231A_semistatique_bord_2026-08-26.txt")
COURANT = 231.0
H_BORD_CANON = 250.0     # canonique (ancien résultat)
H_BORD_COIN = 100.0      # corrigé — calibré sur le coin réel TC1=392
COUL = [OKABE_ITO[c] for c in ("noir", "bleu", "vert", "orange", "vermillon")]


def cycle_avec_hbord(courant, h_bord):
    """Lance le cycle en surchargeant h_bord_x0 (chants libres) sans toucher au canonique."""
    orig = g.construire_essai

    def patched(cour):
        e = orig(cour)
        e.cfg.ambiant.h_bord_x0 = h_bord
        return e
    g.construire_essai = patched
    try:
        return m.simuler_cycle_tc(courant)
    finally:
        g.construire_essai = orig


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
    maxtc = np.nanmax(np.vstack([series[f"TC{i}"] for i in range(1, 6)]), axis=0)
    amb = np.nanmedian(np.vstack([series[f"TC{i}"][:10] for i in range(1, 6)]))
    i0 = int(np.argmax(maxtc > amb + 15))
    return t - t[i0], series


if __name__ == "__main__":
    print("simulation CORRIGÉE (h_bord_x0=100)…")
    res_c = cycle_avec_hbord(COURANT, H_BORD_COIN)
    print("simulation ANCIENNE (h_bord_x0=250, référence conservée)…")
    res_o = cycle_avec_hbord(COURANT, H_BORD_CANON)
    t_c, s_c = res_c["t"], res_c["series"]
    t_o, s_o = res_o["t"], res_o["series"]
    noms = res_c["noms"]
    t_r, s_r = charger_reel()

    fig, ax = plt.subplots(figsize=(11.5, 5.4))
    for nom, coul in zip(noms, COUL):
        ax.plot(t_r, s_r[nom], color=coul, lw=1.7, alpha=0.9, label=f"{nom} mesuré")
        ax.plot(t_c, s_c[nom], color=coul, lw=1.3, ls=(0, (4, 1.8)), label=f"{nom} prédit (coin corrigé)")
    # ancien TC1 conservé en référence (effet de coin non corrigé)
    ax.plot(t_o, s_o["TC1"], color="0.55", lw=1.1, ls=(0, (1, 1.5)),
            label="TC1 prédit (ancien, coin non corrigé)", zorder=2)
    ax.axhline(390, color=OKABE_ITO["vert"], lw=0.9, ls="--", zorder=1)
    ax.axhline(337, color=OKABE_ITO["cyan"], lw=0.9, ls=":", zorder=1)
    ax.text(ax.get_xlim()[1], 393, " consigne 390", fontsize=7.5, color=OKABE_ITO["vert"], va="bottom", ha="right")

    ax.set_xlim(0, max(t_c[-1], t_r[-1]))
    ax.set_ylim(0, 560)
    ax.set_xlabel("Temps (s) — recalé sur l'amorçage")
    ax.set_ylabel("Température (°C)")
    ax.set_title("Validation 231 A avec correction du coin x=0 (h_bord_x0 : 250 → 100)",
                 fontsize=12, fontweight="bold")
    ax.legend(loc="upper right", ncol=2, fontsize=7.2, framealpha=0.93)
    fig.tight_layout()
    savefig(fig, R / "biblio" / "labo" / "figures" / "fig_compare_230A_vs_reel_coin")
    plt.close(fig)

    print("\n=== Pics : ancien vs corrigé vs mesuré (231 A) ===")
    print(f"{'TC':>4} | {'ancien':>7} | {'corrigé':>8} | {'mesuré':>7} | {'écart corr.':>11}")
    for nom in noms:
        po = float(np.max(s_o[nom]))
        pc = float(np.max(s_c[nom]))
        pm = float(np.nanmax(s_r[nom]))
        print(f"{nom:>4} | {po:7.0f} | {pc:8.0f} | {pm:7.0f} | {pc - pm:+11.0f}")
    tmax = min(t_c[-1], t_r[-1])
    grille = np.linspace(0, tmax, 400)
    for nom in ("TC1", "TC2", "TC3", "TC4"):
        sm = np.interp(grille, t_r, s_r[nom])
        sp = np.interp(grille, t_c, s_c[nom])
        ok = ~np.isnan(sm)
        print(f"  RMSE {nom} (corrigé) = {np.sqrt(np.mean((sp[ok] - sm[ok])**2)):.0f} °C")
    print("figure -> biblio/labo/figures/fig_compare_230A_vs_reel_coin.png")
