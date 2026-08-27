#!/usr/bin/env python3
"""Comparaison prédit ↔ mesuré — cycle semi-statique 160 A (prêt à ingérer le futur essai).

Usage :
    python3 gen_compare_160A_vs_reel.py [chemin_du_txt_reel]

- Si un fichier réel est fourni (arg) OU trouvé automatiquement dans
  donnees/data/*160A*/*.txt (format LabVIEW : Time (s) + TC1..TC5, tab, virgule
  décimale) : on EXTRAIT automatiquement les 4 fenêtres de passe (pics + vallées),
  on pilote le modèle 2D canonique sur ces temps RÉELS, et on superpose /
  chiffre (pics + RMSE) — même méthode que la validation 231 A.
- Sinon : on sort la PRÉDICTION SEULE (cycle « parfait » 160 A, pilotage point
  chaud PC=390) et on indique où déposer le fichier.

Rappel protocole : à 160 A on NE coupe PAS sur TC=390 (les TC de bord plafonnent
~255-293 °C réel ; forcer 390 cuirait l'interface). Cf. note #64.

Sortie : biblio/labo/figures/fig_compare_160A_vs_reel.png (ou
         fig_cycle_160A_prediction.png si pas encore de mesure).
"""
from __future__ import annotations
import sys, copy, glob
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts" / "gen"))
sys.path.insert(0, str(R / "code" / "scripts"))
import gen_cycle_parfait_semistatique as g  # noqa: E402
from jumeau.thermique.solveur2d import SolveurThermique2D  # noqa: E402
from _style import savefig, OKABE_ITO  # noqa: E402

COURANT = 160.0
NOMS = [f"TC{i}" for i in range(1, 6)]
COUL = [OKABE_ITO[c] for c in ("noir", "bleu", "vert", "orange", "vermillon")]
FIG = R / "biblio" / "labo" / "figures"


def trouver_fichier_reel():
    if len(sys.argv) > 1 and Path(sys.argv[1]).is_file():
        return Path(sys.argv[1])
    motifs = ["*160A*/*.txt", "*160a*/*.txt", "*160A*.txt"]
    for m in motifs:
        hits = sorted(glob.glob(str(R / "donnees" / "data" / m)))
        if hits:
            return Path(hits[-1])          # le plus récent alphabétiquement
    return None


def charger_reel(chemin):
    df = pd.read_csv(chemin, sep="\t", decimal=",")
    df.columns = [c.strip() for c in df.columns]
    t = df["Time (s)"].to_numpy(float).copy(); t -= t[0]
    S = {n: pd.to_numeric(df[[c for c in df.columns if c.startswith(n)][0]], errors="coerce").to_numpy(float).copy()
         for n in NOMS}
    maxtc = np.nanmax(np.vstack([S[n] for n in NOMS]), axis=0)
    amb = float(np.nanmedian(np.vstack([S[n][:10] for n in NOMS])))
    i0 = int(np.argmax(maxtc > amb + 15)); t -= t[i0]
    keep = t >= 0
    return t[keep], {n: S[n][keep] for n in NOMS}, maxtc[keep], amb


def extraire_fenetres(t, maxtc, n_passes=4):
    """Détecte les n_passes bosses de chauffe : pics (find_peaks) + vallée amont."""
    from scipy.signal import find_peaks
    pk, props = find_peaks(maxtc, prominence=30, distance=max(1, len(t) // (2 * n_passes)))
    if len(pk) < n_passes:                 # repli : découpe en n segments égaux
        bornes = np.linspace(0, len(t), n_passes + 1).astype(int)
        pk = np.array([b0 + int(np.argmax(maxtc[b0:b1])) for b0, b1 in zip(bornes[:-1], bornes[1:])])
    else:                                   # garde les n_passes plus proéminents, triés en temps
        ordre = np.argsort(props["prominences"])[::-1][:n_passes]
        pk = np.sort(pk[ordre])
    starts, dwells = [], []
    for j, ip in enumerate(pk):
        lo = 0 if j == 0 else pk[j - 1]
        seg = maxtc[lo:ip + 1]
        istart = lo + int(np.argmin(seg))
        starts.append(float(t[istart])); dwells.append(float(t[ip] - t[istart]))
    gaps = [starts[i + 1] - (starts[i] + dwells[i]) for i in range(n_passes - 1)]
    gaps.append(float(t[-1] - (starts[-1] + dwells[-1])))
    return starts, dwells, gaps


# base modèle (construite une fois)
E = g.construire_essai(COURANT)
GR, MAT, CONTACT = E.grille, E.cfg.materiau, E.cfg.contact
AMB_BASE = E.cfg.ambiant
POS = {n: (float(E.spec["thermocouples"][n]["x"]), float(E.spec["thermocouples"][n]["y"])) for n in NOMS}


def cycle_reel_timing(dwells, gaps, fac=g.FACTEUR, h_bas=None, h_bord=None, t_amb=None):
    amb = copy.deepcopy(AMB_BASE)
    if h_bas is not None: amb.h_bas_2d = float(h_bas)
    if h_bord is not None: amb.h_bord_x0 = float(h_bord)
    if t_amb is not None: amb.T_amb = float(t_amb)
    field = np.full(GR.nx * GR.ny, amb.T_amb)
    T_out = {n: [] for n in NOMS}; t_out = []; t0 = 0.0
    for i in range(4):
        P = E._P_spots_2d[i] * (fac / g.FACTEUR); Pnul = np.zeros_like(P)
        solv = SolveurThermique2D(GR, MAT, amb, CONTACT, masque_ceramique=E._masques[i])
        th = np.append(np.arange(0.0, dwells[i], 0.5), dwells[i])
        sh = solv.simuler(lambda tt: P, (0.0, dwells[i]), t_eval=th, T_initial=field); field = sh.y[:, -1]
        tc = np.append(np.arange(0.0, gaps[i], 1.0), gaps[i])
        sc = solv.simuler(lambda tt: Pnul, (0.0, gaps[i]), t_eval=tc, T_initial=field); field = sc.y[:, -1]
        for sol, off in ((sh, 0.0), (sc, dwells[i])):
            for n in NOMS:
                T_out[n].append(solv.serie_temporelle(sol, *POS[n]))
            t_out.append(t0 + off + sol.t)
        t0 += dwells[i] + gaps[i]
    return np.concatenate(t_out), {n: np.concatenate(T_out[n]) for n in NOMS}


def reel_attendu(n, v):
    return v + 30.0 if n in ("TC2", "TC3", "TC4") else v


if __name__ == "__main__":
    chemin = trouver_fichier_reel()

    if chemin is None:
        # ---- pas encore de mesure : prédiction seule (pilotage point chaud) ----
        print("Aucun fichier réel 160 A trouvé.")
        print("  -> dépose le .txt dans donnees/data/<dossier avec '160A'>/  (ou passe le chemin en argument)")
        print("     puis relance ce script : il fera automatiquement la comparaison.")
        r = g.simuler_cycle(COURANT)
        t, series, pc = r["t"], r["series"], r["point_chaud"]
        fig, ax = plt.subplots(figsize=(11.0, 4.8))
        for n, c in zip(NOMS, COUL):
            ax.plot(t, series[n], color=c, lw=1.2, label=n)
        ax.plot(t, pc, color="0.3", lw=0.9, ls=(0, (4, 1.6)), label="point chaud (contrôle)")
        for s, c in ((337, OKABE_ITO["cyan"]), (390, OKABE_ITO["vert"]), (450, OKABE_ITO["vermillon"])):
            ax.axhline(s, color=c, lw=0.8, ls="--")
        ax.set_xlim(0, t[-1]); ax.set_ylim(0, 560)
        ax.set_xlabel("Temps (s)"); ax.set_ylabel("Température (°C)")
        ax.set_title("Prédiction cycle 160 A (pilotage point chaud PC=390) — en attente de la mesure",
                     fontsize=11.5, fontweight="bold")
        ax.legend(loc="upper right", ncol=3, fontsize=7.5)
        fig.tight_layout()
        savefig(fig, FIG / "fig_cycle_160A_prediction"); plt.close(fig)
        print("\npics prédits (modèle -> réel attendu) :")
        for n in NOMS:
            print(f"  {n}: {series[n].max():6.1f} -> {reel_attendu(n, series[n].max()):6.1f}")
        print("figure -> biblio/labo/figures/fig_cycle_160A_prediction.png")
        sys.exit(0)

    # ---- mesure disponible : comparaison prédit(temps réels) ↔ mesuré ----
    print(f"fichier réel : {chemin}")
    t_r, S_r, maxtc, amb = charger_reel(chemin)
    starts, dwells, gaps = extraire_fenetres(t_r, maxtc)
    print("fenêtres détectées :", [f"P{i+1}: start={starts[i]:.0f} dwell={dwells[i]:.0f} gap={gaps[i]:.0f}" for i in range(4)])
    t_m, S_m = cycle_reel_timing(dwells, gaps, t_amb=amb)   # modèle canonique, temps réels

    fig, ax = plt.subplots(figsize=(12.0, 5.4))
    for n, c in zip(NOMS, COUL):
        ax.plot(t_r, S_r[n], color=c, lw=1.7, alpha=0.9, label=f"{n} mesuré")
        ax.plot(t_m, S_m[n], color=c, lw=1.3, ls=(0, (4, 1.8)), label=f"{n} prédit")
    ax.axhline(390, color=OKABE_ITO["vert"], lw=0.8, ls="--"); ax.axhline(337, color=OKABE_ITO["cyan"], lw=0.8, ls=":")
    ax.set_xlim(0, max(t_r[-1], t_m[-1])); ax.set_ylim(0, 560)
    ax.set_xlabel("Temps (s) — recalé sur l'amorçage (pilotage par les temps réels)")
    ax.set_ylabel("Température (°C)")
    ax.set_title("Validation 160 A — TC mesurés (plein) vs prédits (pointillé)", fontsize=12, fontweight="bold")
    ax.legend(loc="upper right", ncol=2, fontsize=7.5, framealpha=0.93)
    fig.tight_layout()
    savefig(fig, FIG / "fig_compare_160A_vs_reel"); plt.close(fig)

    tmax = min(t_r[-1], t_m[-1]); gr = np.linspace(0, tmax, 500)
    print("\n=== Pics & RMSE (prédit vs mesuré) ===")
    print(f"{'TC':>4} | {'pic préd':>8} | {'pic mes':>7} | {'écart':>6} | {'RMSE':>6}")
    for n in NOMS:
        sm = np.interp(gr, t_r, S_r[n]); sp = np.interp(gr, t_m, S_m[n]); ok = ~np.isnan(sm)
        pp, pm = float(S_m[n].max()), float(np.nanmax(S_r[n]))
        print(f"{n:>4} | {pp:8.0f} | {pm:7.0f} | {pp-pm:+6.0f} | {np.sqrt(np.mean((sp[ok]-sm[ok])**2)):6.1f}")
    print("figure -> biblio/labo/figures/fig_compare_160A_vs_reel.png")
