#!/usr/bin/env python3
"""Cycle semi-statique 230 A PILOTÉ SUR TC — couper quand le TC proche du spot
atteint 390 °C RÉEL (= 360 °C modèle, biais −30 °C sur les TC intérieurs mesuré
à la validation série A). Refroidit ensuite jusqu'à Tg (159 °C), avance.

Réutilise le moteur validé de gen_cycle_parfait_semistatique.py (construire_essai,
solveur 2D, warm-start, refroidissement→Tg) ; on change juste la variable de
pilotage : on surveille le TC de contrôle (le plus proche du spot actif) au lieu
du point chaud. Passe 4 : on pilote sur TC4 (x=90, intérieur fiable) car TC5
(x=120, bord opposé) est sur-prédit (correctif h_bord_x0 asymétrique).

Sortie : biblio/labo/figures/fig_cycle_230A_TC390.png
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
from _style import savefig, OKABE_ITO  # noqa: E402

COURANT = 230.0
SEUIL_CTRL = 360.0                       # °C modèle (≈ 390 °C réel)
CTRL_X = [0.030, 0.060, 0.090, 0.090]    # TC de contrôle par passe : TC2, TC3, TC4, TC4
BIAIS_INT = 30.0                         # sous-estimation TC intérieurs (TC2/3/4)


def simuler_passe_tc(e, i_spot, T_initial, x_ctrl):
    x_c = float(e.spots[i_spot]["centre_x"])
    P = e._P_spots_2d[i_spot]
    P_nul = np.zeros_like(P)
    solveur = g.SolveurThermique2D(e.grille, e.cfg.materiau, e.cfg.ambiant, e.cfg.contact,
                                    masque_ceramique=e._masques[i_spot])
    noms = list(e.spec["thermocouples"].keys())
    pos = {n: (float(e.spec["thermocouples"][n]["x"]), float(e.spec["thermocouples"][n]["y"])) for n in noms}

    # CHAUFFE : couper quand le TC de contrôle atteint SEUIL_CTRL
    t_eval_h = np.arange(0.0, g.CAP_CHAUFFE + g.DT_CHAUFFE / 2, g.DT_CHAUFFE)
    sol_h = solveur.simuler(lambda t: P, (0.0, g.CAP_CHAUFFE), t_eval=t_eval_h, T_initial=T_initial)
    Tctrl = solveur.serie_temporelle(sol_h, x_ctrl, 0.0)
    Te_h = solveur.serie_temporelle(sol_h, x_c, 0.0)                    # point chaud (diagnostic)
    t_cut, jcut = g.premier_passage_montee(sol_h.t, Tctrl, SEUIL_CTRL)
    atteint = not np.isnan(t_cut)
    dwell = t_cut if atteint else g.CAP_CHAUFFE
    pc_at_cut = float(g._serie_a_instant(Te_h, sol_h.t, dwell, jcut))
    t_450, _ = g.premier_passage_montee(sol_h.t, Te_h, g.T_DEGRAD)
    marge = (t_450 - dwell) if (atteint and not np.isnan(t_450)) else float("nan")

    champ_apres = g._interp_champ(sol_h.y, sol_h.t, dwell, jcut)
    mask = sol_h.t <= dwell + 1e-9
    t_h = sol_h.t[mask]
    if len(t_h) == 0 or t_h[-1] < dwell - 1e-6:
        t_h = np.concatenate([t_h, [dwell]])
    Te_h_tr = Te_h[mask]
    if len(Te_h_tr) < len(t_h):
        Te_h_tr = np.concatenate([Te_h_tr, [pc_at_cut]])
    series_h = {}
    for n in noms:
        x, y = pos[n]
        s = solveur.serie_temporelle(sol_h, x, y)[mask]
        if len(s) < len(t_h):
            s = np.concatenate([s, [g._serie_a_instant(solveur.serie_temporelle(sol_h, x, y), sol_h.t, dwell, jcut)]])
        series_h[n] = s

    # REFROIDISSEMENT : point chaud -> Tg
    t_eval_c = np.arange(0.0, g.CAP_REFROID + g.DT_REFROID / 2, g.DT_REFROID)
    sol_c = solveur.simuler(lambda t: P_nul, (0.0, g.CAP_REFROID), t_eval=t_eval_c, T_initial=champ_apres)
    Te_c = solveur.serie_temporelle(sol_c, x_c, 0.0)
    t_tg, jtg = g.premier_passage_descente(sol_c.t, Te_c, g.T_REFROID)
    refroidi = not np.isnan(t_tg)
    duree_r = t_tg if refroidi else g.CAP_REFROID
    champ_final = g._interp_champ(sol_c.y, sol_c.t, duree_r, jtg)
    mask = sol_c.t <= duree_r + 1e-9
    t_c = sol_c.t[mask]
    if len(t_c) == 0 or t_c[-1] < duree_r - 1e-6:
        t_c = np.concatenate([t_c, [duree_r]])
    Te_c_tr = Te_c[mask]
    if len(Te_c_tr) < len(t_c):
        Te_c_tr = np.concatenate([Te_c_tr, [g._serie_a_instant(Te_c, sol_c.t, duree_r, jtg)]])
    series_c = {}
    for n in noms:
        x, y = pos[n]
        s = solveur.serie_temporelle(sol_c, x, y)[mask]
        if len(s) < len(t_c):
            s = np.concatenate([s, [g._serie_a_instant(solveur.serie_temporelle(sol_c, x, y), sol_c.t, duree_r, jtg)]])
        series_c[n] = s

    return dict(x_c=x_c, noms=noms, t_h=t_h, Te_h=Te_h_tr, series_h=series_h,
                dwell=dwell, atteint=atteint, pc_at_cut=pc_at_cut, marge=marge,
                t_c=t_c, Te_c=Te_c_tr, series_c=series_c, duree_r=duree_r, refroidi=refroidi,
                champ_final=champ_final)


def simuler_cycle_tc(courant):
    e = g.construire_essai(courant)
    noms = list(e.spec["thermocouples"].keys())
    T_field = np.full(e.grille.nx * e.grille.ny, g.T_AMB)
    t_glob = [np.array([0.0])]
    series_glob = {n: [np.array([g.T_AMB])] for n in noms}
    pc_glob = [np.array([g.T_AMB])]
    passes = []
    t0 = 0.0
    for i in range(len(e.spots)):
        r = simuler_passe_tc(e, i, T_field, CTRL_X[i])
        for t_loc, pc_loc, s_loc in ((r["t_h"], r["Te_h"], r["series_h"]),
                                     (r["t_c"], r["Te_c"], r["series_c"])):
            t_glob.append(t0 + t_loc)
            for n in noms:
                series_glob[n].append(s_loc[n])
            pc_glob.append(pc_loc)
            t0 += t_loc[-1] if len(t_loc) else 0.0
        td = t0 - r["dwell"] - r["duree_r"]
        passes.append(dict(i=i, x_c=r["x_c"], t_deb=td, t_fin_ch=td + r["dwell"],
                           t_fin_rf=td + r["dwell"] + r["duree_r"], dwell=r["dwell"],
                           atteint=r["atteint"], pc_at_cut=r["pc_at_cut"], marge=r["marge"],
                           duree_r=r["duree_r"], ctrl_x=CTRL_X[i]))
        T_field = r["champ_final"]
    t = np.concatenate(t_glob)
    series = {n: np.concatenate(series_glob[n]) for n in noms}
    pc = np.concatenate(pc_glob)
    return dict(t=t, series=series, pc=pc, passes=passes, noms=noms)


def reel(nom, pic):
    return pic + BIAIS_INT if nom in ("TC2", "TC3", "TC4") else pic


if __name__ == "__main__":
    from PIL import Image
    res = simuler_cycle_tc(COURANT)
    t, series, pc, passes, noms = res["t"], res["series"], res["pc"], res["passes"], res["noms"]
    couleurs = [OKABE_ITO[c] for c in ("noir", "bleu", "vert", "orange", "vermillon")]

    fig, ax = plt.subplots(figsize=(11.0, 4.6))
    for p in passes:
        ax.axvspan(p["t_deb"], p["t_fin_ch"], color="#E8E8E8", zorder=0)
        ax.axvspan(p["t_fin_ch"], p["t_fin_rf"], color="#F7F7F7", zorder=0)
        ax.axvline(p["t_fin_ch"], color="0.65", lw=0.5, ls=":", zorder=1)
        ax.axvline(p["t_fin_rf"], color="0.4", lw=0.6, ls="-", zorder=1)
        mc = 0.5 * (p["t_deb"] + p["t_fin_ch"])
        ax.annotate(f"P{p['i'] + 1}\n{p['dwell']:.0f}s", (mc, 470), ha="center", va="center",
                    fontsize=7, color="0.2")
    for nom, coul in zip(noms, couleurs):
        ax.plot(t, series[nom], color=coul, lw=1.2, label=nom)
    ax.plot(t, pc, color="0.3", lw=0.9, ls=(0, (4, 1.6)), label="point chaud (interface au spot)", zorder=2.5)
    for seuil, coul, lab in ((g.T_FUSION, OKABE_ITO["cyan"], "fusion 337"),
                             (390.0, OKABE_ITO["vert"], "consigne 390 (réel)"),
                             (g.T_DEGRAD, OKABE_ITO["vermillon"], "dégrad. 450")):
        ax.axhline(seuil, color=coul, lw=0.9, ls="--", zorder=1)
    ax.axhline(g.T_REFROID, color="0.5", lw=0.9, ls=":", zorder=1)

    ax.set_xlim(0, t[-1])
    ax.set_ylim(0, max(560, pc.max() * 1.05))
    ax.set_xlabel("Temps (s)")
    ax.set_ylabel("Température (°C)")
    ax.set_title("Cycle 230 A piloté sur TC — couper quand le TC proche du spot atteint "
                 "390 °C réel (= 360 °C modèle)", fontsize=11.5, fontweight="bold", pad=20)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.005), ncol=7, fontsize=6.6,
              columnspacing=0.9, handlelength=1.4, handletextpad=0.4, framealpha=0.92)
    note = ("Pilotage : chauffe jusqu'à TC de contrôle (proche du spot : TC2/TC3/TC4/TC4) = 360 °C modèle ≈ 390 °C réel, "
            "puis refroid.→Tg 159 °C, avance.\n"
            "Les TC RÉELS piqueront ~30 °C au-dessus des courbes intérieures (TC2/3/4). Point chaud = interface au spot "
            "(bien au-dessus de la fusion → soudage). TC5 (x=120, bord opposé) sur-prédit — indicatif.")
    ax.text(0.5, -0.30, note, transform=ax.transAxes, ha="center", va="top", fontsize=6.4, color="0.35", linespacing=1.5)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    out = R / "biblio" / "labo" / "figures" / "fig_cycle_230A_TC390"
    chemins = savefig(fig, out)
    plt.close(fig)

    # tableau
    print("\n=== Cycle 230 A piloté sur TC (couper à 360 modèle = 390 réel) ===")
    pics = {n: float(np.max(series[n])) for n in noms}
    print(f"{'Passe':>5} | {'TC ctrl':>7} | {'dwell(s)':>8} | {'refroid(s)':>10} | "
          f"{'PC@cut':>7} | {'marge450':>8}")
    for p in passes:
        tc_ctrl = {0.030: "TC2", 0.060: "TC3", 0.090: "TC4"}[p["ctrl_x"]]
        marge = f"{p['marge']:.1f}" if not np.isnan(p["marge"]) else "n/a"
        print(f"{p['i'] + 1:>5} | {tc_ctrl:>7} | {p['dwell']:>8.1f} | {p['duree_r']:>10.1f} | "
              f"{p['pc_at_cut']:>7.0f} | {marge:>8}")
    print(f"\n  durée totale du cycle : {t[-1]:.1f} s ({t[-1] / 60:.1f} min)")
    print("  Pics par TC (modèle -> réel attendu) :")
    for n in noms:
        print(f"    {n} : {pics[n]:6.1f} -> {reel(n, pics[n]):6.1f} °C")
    for c in chemins:
        if c.suffix.lower() == ".png":
            w, h = Image.open(c).size
            print(f"\n  figure : {c}  ({w}x{h} px)")
