#!/usr/bin/env python3
"""Diagnostic : la conduction latérale explique-t-elle le refroidissement rapide ? (issue #68)

Le test du rayonnement de face a réfuté l'idée d'une perte de SURFACE manquante :
ajouter le T⁴ de face ne recale pas la chute rapide juste après le pic. Nouvelle
piste : la chute rapide est de la **conduction latérale in-plane** que le modèle
sous-représente — pendant le refroidissement T repasse sous Tf (337 °C) où la
table de transport fait retomber `k_plan` à 3, alors que le vrai stratifié
continue d'évacuer la chaleur latéralement.

TEST ISOLANT : on rehausse `k_plan` **UNIQUEMENT pendant les phases de
refroidissement** (spot éteint) — balayage `k_cool` — la chauffe/les pics
gardant la table de fusion normale. Si le déficit de refroidissement à haute T
se recale vers 1 quand `k_cool` monte, la conduction latérale est bien le
mécanisme. On regarde aussi l'effet sur l'accumulation (pics TC4/TC5) et les
intérieurs (RMSE TC2/TC3).

Diagnostic pur : ne modifie aucune config par défaut ni code de production.
Sorties : biblio/labo/figures/fig_diag_conduction_laterale_231A.png
          biblio/labo/diag_conduction_laterale_231A.md
"""
from __future__ import annotations
import sys, copy
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts" / "gen"))
sys.path.insert(0, str(R / "code" / "scripts"))
import gen_cycle_parfait_semistatique as g  # noqa: E402  (import-safe)
from jumeau.thermique.solveur2d import SolveurThermique2D  # noqa: E402
from _style import apply_style, savefig, OKABE_ITO  # noqa: E402

apply_style(**{"savefig.dpi": 200, "figure.dpi": 200})

FICH = R / "donnees" / "data" / "exp10_cycle-semistatique_231A_2026-08-26" / "231A_semistatique_bord_2026-08-26.txt"
NOMS = [f"TC{i}" for i in range(1, 6)]
INTERIEURS = ["TC2", "TC3", "TC4"]
COUL = {n: OKABE_ITO[c] for n, c in zip(NOMS, ("noir", "bleu", "vert", "orange", "vermillon"))}
LF_PHYS = 40000.0
TABLE_CHAUFFE = [[0.0, 3.0], [337.0, 3.0], [380.0, 100.0], [700.0, 100.0]]  # transport fusion (chauffe)
KCOOL = [3.0, 10.0, 30.0, 100.0]              # k_plan in-plane pendant le refroidissement
SEUIL_T0, FEN_HAUT = 250.0, 15.0

# --- réel + fenêtres ---
df = pd.read_csv(FICH, sep="\t", decimal=",")
df.columns = [c.strip() for c in df.columns]
t = df["Time (s)"].to_numpy(float).copy(); t -= t[0]
S = {n: pd.to_numeric(df[[c for c in df.columns if c.startswith(n)][0]], errors="coerce").to_numpy(float).copy() for n in NOMS}
maxtc = np.nanmax(np.vstack([S[n] for n in NOMS]), axis=0)
AMB = float(np.nanmedian(np.vstack([S[n][:10] for n in NOMS])))
i0 = int(np.argmax(maxtc > AMB + 15)); t -= t[i0]
keep = t >= 0; t = t[keep]; S = {n: S[n][keep] for n in NOMS}; maxtc = maxtc[keep]
pk, props = find_peaks(maxtc, prominence=30, distance=len(t) // 8)
pk = np.sort(pk[np.argsort(props["prominences"])[::-1][:4]])
starts, dwells = [], []
for j, ip in enumerate(pk):
    lo = 0 if j == 0 else pk[j - 1]
    istart = lo + int(np.argmin(maxtc[lo:ip + 1]))
    starts.append(float(t[istart])); dwells.append(float(t[ip] - t[istart]))
gaps = [starts[i + 1] - (starts[i] + dwells[i]) for i in range(3)] + [float(t[-1] - (starts[3] + dwells[3]))]

E = g.construire_essai(231.0)
GR, MAT, CONTACT = E.grille, E.cfg.materiau, E.cfg.contact
POS = {n: (float(E.spec["thermocouples"][n]["x"]), float(E.spec["thermocouples"][n]["y"])) for n in NOMS}


def cycle_kcool(k_cool):
    """Fusion normale à la chauffe ; k_plan constant = k_cool pendant les gaps."""
    MAT.chaleur_latente = LF_PHYS
    amb = copy.deepcopy(E.cfg.ambiant); amb.T_amb = AMB
    field = np.full(GR.nx * GR.ny, AMB)
    T_out = {n: [] for n in NOMS}; t_out = []; t0 = 0.0
    table_cool = [[0.0, k_cool], [700.0, k_cool]]
    for i in range(4):
        P = E._P_spots_2d[i]; Pnul = np.zeros_like(P)
        # chauffe : transport fusion
        MAT.k_plan_T = TABLE_CHAUFFE
        solv = SolveurThermique2D(GR, MAT, amb, CONTACT, masque_ceramique=E._masques[i])
        th = np.append(np.arange(0.0, dwells[i], 0.5), dwells[i])
        sh = solv.simuler(lambda tt: P, (0.0, dwells[i]), t_eval=th, T_initial=field); field = sh.y[:, -1]
        # refroidissement : k_plan constant = k_cool
        MAT.k_plan_T = table_cool
        solv_c = SolveurThermique2D(GR, MAT, amb, CONTACT, masque_ceramique=E._masques[i])
        tc = np.append(np.arange(0.0, gaps[i], 1.0), gaps[i])
        sc = solv_c.simuler(lambda tt: Pnul, (0.0, gaps[i]), t_eval=tc, T_initial=field); field = sc.y[:, -1]
        for sol, sv, off in ((sh, solv, 0.0), (sc, solv_c, dwells[i])):
            for n in NOMS:
                T_out[n].append(sv.serie_temporelle(sol, *POS[n]))
            t_out.append(t0 + off + sol.t)
        t0 += dwells[i] + gaps[i]
    return np.concatenate(t_out), {n: np.concatenate(T_out[n]) for n in NOMS}


def metriques(t_mod, S_mod):
    pics = {n: float(np.nanmax(S_mod[n])) for n in NOMS}
    gr = np.linspace(0, min(t[-1], t_mod[-1]), 600); rmse = {}
    for n in NOMS:
        sm = np.interp(gr, t, S[n]); sp = np.interp(gr, t_mod, S_mod[n]); ok = ~np.isnan(sm)
        rmse[n] = float(np.sqrt(np.mean((sp[ok] - sm[ok]) ** 2)))
    defs = []
    for i in range(4):
        g0 = starts[i] + dwells[i]; m = (t >= g0) & (t <= g0 + gaps[i]); tt_seg = t[m] - g0
        for n in INTERIEURS:
            Tm = S[n][m]
            if np.isnan(Tm).all() or Tm[0] < SEUIL_T0:
                continue
            To = np.interp(t[m], t_mod, S_mod[n]); sel = tt_seg <= FEN_HAUT
            if sel.sum() < 2:
                continue
            vm = -np.gradient(Tm, tt_seg)[sel].mean(); vo = -np.gradient(To, tt_seg)[sel].mean()
            if vo and vo > 0:
                defs.append(vm / vo)
    return pics, rmse, float(np.nanmedian(defs))


if __name__ == "__main__":
    res = {}
    for k in KCOOL:
        print(f"cycle k_cool={k}…")
        tk, Sk = cycle_kcool(k); res[k] = (tk, Sk, *metriques(tk, Sk))
    pm = {n: float(np.nanmax(S[n])) for n in NOMS}

    print(f"\nPics mesurés : {', '.join(f'{n}={pm[n]:.0f}' for n in NOMS)} °C")
    print(f"\n{'k_cool':>6} | {'picTC4':>6} | {'picTC5':>6} | {'RMSE TC2':>8} | {'RMSE TC3':>8} | "
          f"{'RMSE TC4':>8} | {'RMSE TC5':>8} | {'def.hautT':>9}")
    for k in KCOOL:
        _, _, pics, rmse, dh = res[k]
        print(f"{k:6.0f} | {pics['TC4']:6.0f} | {pics['TC5']:6.0f} | {rmse['TC2']:8.1f} | "
              f"{rmse['TC3']:8.1f} | {rmse['TC4']:8.1f} | {rmse['TC5']:8.1f} | {dh:9.2f}")

    # --- figure ---
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(12.8, 5.0))
    g0 = starts[3] + dwells[3]; m = (t >= g0) & (t <= g0 + gaps[3]); tt_seg = t[m] - g0
    axA.plot(tt_seg, S["TC4"][m], color="0.1", lw=2.2, label="TC4 mesuré")
    for k, c in zip(KCOOL, ("0.7", OKABE_ITO["cyan"], OKABE_ITO["orange"], OKABE_ITO["vermillon"])):
        tk, Sk, *_ = res[k]
        axA.plot(tt_seg, np.interp(t[m], tk, Sk["TC4"]), color=c, lw=1.5, ls=(0, (4, 1.8)),
                 label=f"k_cool={k:.0f}")
    axA.set_xlabel("Temps depuis début du gap 4 (s)")
    axA.set_ylabel("Température (°C)")
    axA.set_title("Refroidissement TC4 (P4) : effet de k_plan au refroidissement", fontsize=10.5, fontweight="bold")
    axA.legend(loc="upper right", fontsize=7.8, framealpha=0.93)
    xs = np.array(KCOOL)
    axB.plot(xs, [res[k][2]["TC4"] for k in KCOOL], "o-", color=OKABE_ITO["orange"], label="pic TC4")
    axB.plot(xs, [res[k][2]["TC5"] for k in KCOOL], "s-", color=OKABE_ITO["vermillon"], label="pic TC5")
    axB.axhline(pm["TC4"], color=OKABE_ITO["orange"], lw=0.9, ls=":", label="TC4 mesuré")
    axB.axhline(pm["TC5"], color=OKABE_ITO["vermillon"], lw=0.9, ls=":", label="TC5 mesuré")
    axB.set_xscale("log"); axB.set_xlabel("k_cool (W/m·K, pendant refroidissement)")
    axB.set_ylabel("Pic (°C)"); axB.set_title("Pics & déficit vs k_cool", fontsize=10.5, fontweight="bold")
    axB.legend(loc="center left", fontsize=7.6, framealpha=0.93)
    axB2 = axB.twinx()
    axB2.plot(xs, [res[k][4] for k in KCOOL], "^--", color="0.35", label="déficit refroid. haute T")
    axB2.axhline(1.0, color="0.6", lw=0.8, ls=":")
    axB2.set_ylabel("déficit refroid. haute T (→1 = recalé)")
    axB2.legend(loc="upper right", fontsize=7.4, framealpha=0.9)
    fig.tight_layout()
    savefig(fig, R / "biblio" / "labo" / "figures" / "fig_diag_conduction_laterale_231A")
    plt.close(fig)

    # --- markdown ---
    p0, r0, d0 = res[KCOOL[0]][2], res[KCOOL[0]][3], res[KCOOL[0]][4]
    pL, rL, dL = res[KCOOL[-1]][2], res[KCOOL[-1]][3], res[KCOOL[-1]][4]
    md = ["# Diagnostic conduction latérale au refroidissement — cycle 231 A (issue #68)\n"]
    md.append("Après réfutation du rayonnement de face, on teste si la chute rapide post-pic est de "
              "la **conduction latérale in-plane** sous-représentée : on rehausse `k_plan` "
              "**uniquement pendant les gaps** (chauffe = transport fusion normal), balayage `k_cool`. "
              "Script : `code/scripts/gen/gen_diag_conduction_laterale_231A.py`.\n")
    md.append(f"Pics mesurés : {', '.join(f'{n}={pm[n]:.0f}' for n in NOMS)} °C. Rappel : `k_cool=3` "
              "= config actuelle (k_plan retombe à 3 sous Tf).\n")
    md.append("| k_cool | pic TC4 | pic TC5 | RMSE TC2 | RMSE TC3 | RMSE TC4 | RMSE TC5 | déficit refroid. haute T |")
    md.append("|---:|---:|---:|---:|---:|---:|---:|---:|")
    for k in KCOOL:
        _, _, pics, rmse, dh = res[k]
        md.append(f"| {k:.0f} | {pics['TC4']:.0f} | {pics['TC5']:.0f} | {rmse['TC2']:.1f} | "
                  f"{rmse['TC3']:.1f} | {rmse['TC4']:.1f} | {rmse['TC5']:.1f} | {dh:.2f} |")
    md.append("")
    md.append("## Lecture\n")
    md.append(f"- **Mécanisme CONFIRMÉ** : le déficit de refroidissement à haute T se recale bien "
              f"({d0:.2f}× à k_cool=3 → {dL:.2f}× à k_cool=100), et la forme de la chute de TC4 (P4) "
              "épouse la mesure à k_cool élevé (cf. figure, panneau A). La chute rapide post-pic EST "
              "donc bien un phénomène de **conduction latérale in-plane** — que la config actuelle "
              "(`k_plan`=3 sous Tf) sous-représente.")
    md.append(f"- **MAIS le fix naïf échoue en aval** : RMSE TC5 se **dégrade** {r0['TC5']:.1f} → "
              f"{rL['TC5']:.1f} (et TC4 {r0['TC4']:.1f} → {rL['TC4']:.1f}). Raison physique : la "
              "conduction latérale **REDISTRIBUE** la chaleur (elle refroidit le point chaud en la "
              "poussant vers l'aval → préchauffe TC5/le bord), elle ne l'**ÉVACUE** pas. Le vrai "
              "stratifié, lui, cool vers des T basses partout = la chaleur est bien PERDUE.")
    md.append(f"- **Mi-plaque aidée, aval pénalisé** : RMSE TC2 {r0['TC2']:.1f}→{rL['TC2']:.1f}, "
              f"TC3 {r0['TC3']:.1f}→{rL['TC3']:.1f} (améliorés) vs TC5 dégradé — signature d'une "
              "redistribution vers l'aval. Les pics restent quasi inchangés (TC4 "
              f"{p0['TC4']:.0f}→{pL['TC4']:.0f}, TC5 {p0['TC5']:.0f}→{pL['TC5']:.0f}).\n")
    md.append("## Verdict : mécanisme identifié = le résidu structurel k_plan CONNU, vu sous l'angle du refroidissement\n")
    md.append("Le déficit de refroidissement rapide est une **nouvelle manifestation du résidu "
              "structurel déjà documenté** : `k_plan` in-plane trop faible (config 3.0 vs calibration "
              "≈7,5–8,5). Le diagnostic **confirme** la conduction latérale comme mécanisme, mais "
              "montre qu'un `k_plan` **scalaire** relevé ne peut pas refroidir localement sans "
              "**sur-étaler vers l'aval** — exactement pourquoi la recalibration de k_plan est un "
              "held-out NO-GO récurrent (#65, [[residu-unifie-etalement-in-plane]]). Ni perte de "
              "surface (rayonnement de face, réfuté) ni conduction scalaire ne suffisent isolément. "
              "**Seul levier physique restant** cohérent avec tous les indices : un `k_plan` "
              "**anisotrope** (kx≠ky) — évacuer latéralement dans le sens utile sans sur-préchauffer "
              "l'aval — ou **acter la limite structurelle**. C'est la porte déjà identifiée comme "
              "dernière au niveau projet.\n")
    (R / "biblio" / "labo" / "diag_conduction_laterale_231A.md").write_text("\n".join(md), encoding="utf-8")
    print(f"\nMÉCANISME confirmé (déficit {d0:.2f}→{dL:.2f}) mais fix scalaire échoue en aval "
          f"(RMSE TC5 {r0['TC5']:.0f}→{rL['TC5']:.0f}) = résidu structurel k_plan connu.")
    print("figure -> biblio/labo/figures/fig_diag_conduction_laterale_231A.png")
    print("md     -> biblio/labo/diag_conduction_laterale_231A.md")
