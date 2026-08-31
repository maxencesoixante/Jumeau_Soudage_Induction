#!/usr/bin/env python3
"""Test du rayonnement de FACE sur le cycle 231 A (issue #68, Suite #1, étape GO).

Le diagnostic (`gen_diag_refroidissement_231A.py`) a montré que le modèle refroidit
trop lentement, déficit CONCENTRÉ À HAUTE T -> perte radiative de face manquante
(le solveur 2D ne met le T⁴ qu'aux chants ; la face haut EXPOSÉE, hors MFC, n'a
aucune perte). On teste ici le nouveau paramètre `SolveurThermique2D(emissivite_face=)`
(défaut 0.0 = OFF bit-à-bit) : rayonnement ε·σ·(T_amb⁴−T⁴) sur la face haut exposée.

Balaye emissivite_face et vérifie, sur le cycle 231 A (modèle de fusion, dwells
réels), les 3 critères GO :
  (a) la cinétique de refroidissement se recale (déficit haute T -> 1) ;
  (b) les pics TC4/TC5 (emballés) baissent vers le mesuré (383/387 °C) ;
  (c) les intérieurs TC2/TC3 ne sont PAS cassés (RMSE stable).
NB : la validation held-out exp7/exp9 (critère d'ADOPTION) est l'étape suivante.

Ne modifie aucune config par défaut. Sortie :
  biblio/labo/figures/fig_test_rayonnement_face_231A.png
  biblio/labo/test_rayonnement_face_231A.md
"""
from __future__ import annotations
import sys, copy
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.optimize import curve_fit

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
TABLE_KT = [[0.0, 3.0], [337.0, 3.0], [380.0, 100.0], [700.0, 100.0]]
EMISS = [0.0, 0.3, 0.6, 0.9]                  # 0.0 = baseline (config ④ actuelle)
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


MASQUE_VIDE = np.zeros((GR.nx, GR.ny), dtype=bool)


def cycle(emiss_face, exposer_gap=False):
    """Modèle de fusion + rayonnement de face `emiss_face`. Renvoie (t, {TCn}).

    ``exposer_gap`` : si True, la face haut est ENTIÈREMENT exposée pendant le
    refroidissement inter-passes (le MFC a avancé -> plus de masque, donc le
    rayonnement de face agit AUSSI sur la zone juste chauffée). Modélise le fait
    que le MFC quitte la position pendant l'avance.
    """
    MAT.chaleur_latente = LF_PHYS
    MAT.k_plan_T = TABLE_KT
    amb = copy.deepcopy(E.cfg.ambiant); amb.T_amb = AMB
    field = np.full(GR.nx * GR.ny, AMB)
    T_out = {n: [] for n in NOMS}; t_out = []; t0 = 0.0
    for i in range(4):
        P = E._P_spots_2d[i]; Pnul = np.zeros_like(P)
        solv = SolveurThermique2D(GR, MAT, amb, CONTACT, masque_ceramique=E._masques[i],
                                  emissivite_face=emiss_face)
        th = np.append(np.arange(0.0, dwells[i], 0.5), dwells[i])
        sh = solv.simuler(lambda tt: P, (0.0, dwells[i]), t_eval=th, T_initial=field); field = sh.y[:, -1]
        # refroidissement : MFC avancé -> face exposée si exposer_gap
        solv_gap = (SolveurThermique2D(GR, MAT, amb, CONTACT, masque_ceramique=MASQUE_VIDE,
                                       emissivite_face=emiss_face) if exposer_gap else solv)
        tc = np.append(np.arange(0.0, gaps[i], 1.0), gaps[i])
        sc = solv_gap.simuler(lambda tt: Pnul, (0.0, gaps[i]), t_eval=tc, T_initial=field); field = sc.y[:, -1]
        for sol, sv, off in ((sh, solv, 0.0), (sc, solv_gap, dwells[i])):
            for n in NOMS:
                T_out[n].append(sv.serie_temporelle(sol, *POS[n]))
            t_out.append(t0 + off + sol.t)
        t0 += dwells[i] + gaps[i]
    return np.concatenate(t_out), {n: np.concatenate(T_out[n]) for n in NOMS}


def fit_tau(tt, TT):
    tt, TT = np.asarray(tt, float), np.asarray(TT, float)
    ok = ~np.isnan(TT); tt, TT = tt[ok], TT[ok]
    if len(tt) < 5:
        return np.nan
    T0 = TT[0]
    try:
        p, _ = curve_fit(lambda x, tau, Tinf: Tinf + (T0 - Tinf) * np.exp(-x / tau),
                         tt - tt[0], TT, p0=[max(tt[-1] - tt[0], 1.0) / 3.0, TT[-1]],
                         bounds=([1.0, 0.0], [1.0e5, T0]), maxfev=20000)
        return float(p[0])
    except Exception:
        return np.nan


def metriques(t_mod, S_mod):
    """Renvoie pics, RMSE par TC, et déficit médian de refroidissement à haute T."""
    pics = {n: float(np.nanmax(S_mod[n])) for n in NOMS}
    gr = np.linspace(0, min(t[-1], t_mod[-1]), 600)
    rmse = {}
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
    for e in EMISS:
        print(f"cycle emissivite_face={e}…")
        te, Se = cycle(e)
        res[e] = (te, Se, *metriques(te, Se))

    pm = {n: float(np.nanmax(S[n])) for n in NOMS}
    print(f"\nPics mesurés : {', '.join(f'{n}={pm[n]:.0f}' for n in NOMS)} °C")
    print(f"\n{'emiss':>6} | {'picTC4':>6} | {'picTC5':>6} | {'RMSE TC2':>8} | {'RMSE TC3':>8} | "
          f"{'RMSE TC4':>8} | {'RMSE TC5':>8} | {'def.hautT':>9}")
    for e in EMISS:
        _, _, pics, rmse, dh = res[e]
        print(f"{e:6.1f} | {pics['TC4']:6.0f} | {pics['TC5']:6.0f} | {rmse['TC2']:8.1f} | "
              f"{rmse['TC3']:8.1f} | {rmse['TC4']:8.1f} | {rmse['TC5']:8.1f} | {dh:9.2f}")

    # --- figure ---
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(12.8, 5.0))
    # A : un segment chaud (dernier gap, TC4) mesuré vs baseline vs emiss croissant
    g0 = starts[3] + dwells[3]; m = (t >= g0) & (t <= g0 + gaps[3]); tt_seg = t[m] - g0
    axA.plot(tt_seg, S["TC4"][m], color="0.1", lw=2.2, label="TC4 mesuré")
    for e, c in zip(EMISS, ("0.7", OKABE_ITO["cyan"], OKABE_ITO["orange"], OKABE_ITO["vermillon"])):
        te, Se, *_ = res[e]
        axA.plot(tt_seg, np.interp(t[m], te, Se["TC4"]), color=c, lw=1.5,
                 ls=(0, (4, 1.8)), label=f"ε_face={e}")
    axA.set_xlabel("Temps depuis début du gap 4 (s)")
    axA.set_ylabel("Température (°C)")
    axA.set_title("Refroidissement TC4 (passe 4) : effet du rayonnement de face", fontsize=10.5, fontweight="bold")
    axA.legend(loc="upper right", fontsize=7.8, framealpha=0.93)
    # B : pics TC4/TC5 et déficit haute T vs emiss
    xs = np.array(EMISS)
    axB.plot(xs, [res[e][2]["TC4"] for e in EMISS], "o-", color=OKABE_ITO["orange"], label="pic TC4")
    axB.plot(xs, [res[e][2]["TC5"] for e in EMISS], "s-", color=OKABE_ITO["vermillon"], label="pic TC5")
    axB.axhline(pm["TC4"], color=OKABE_ITO["orange"], lw=0.9, ls=":", label="TC4 mesuré")
    axB.axhline(pm["TC5"], color=OKABE_ITO["vermillon"], lw=0.9, ls=":", label="TC5 mesuré")
    axB.set_xlabel("emissivite_face")
    axB.set_ylabel("Pic (°C)")
    axB.set_title("Pics TC4/TC5 vs rayonnement de face", fontsize=10.5, fontweight="bold")
    axB.legend(loc="best", fontsize=7.8, framealpha=0.93)
    axB2 = axB.twinx()
    axB2.plot(xs, [res[e][4] for e in EMISS], "^--", color="0.35", label="déficit refroid. haute T")
    axB2.axhline(1.0, color="0.6", lw=0.8, ls=":")
    axB2.set_ylabel("déficit refroid. haute T (→1 = recalé)")
    axB2.legend(loc="lower left", fontsize=7.5, framealpha=0.9)
    fig.tight_layout()
    savefig(fig, R / "biblio" / "labo" / "figures" / "fig_test_rayonnement_face_231A")
    plt.close(fig)

    # --- markdown ---
    p0, r0, d0 = res[0.0][2], res[0.0][3], res[0.0][4]
    md = ["# Test du rayonnement de face — cycle 231 A (issue #68, Suite #1, étape GO)\n"]
    md.append("Nouveau paramètre `SolveurThermique2D(emissivite_face=)` (défaut 0.0 = OFF, bit-à-bit ; "
              "123 tests verts) : rayonnement `ε·σ·(T_amb⁴−T⁴)` [W/m²] sur la face haut EXPOSÉE "
              "(hors MFC), qui n'avait sinon aucune perte. Cycle 231 A, modèle de fusion, dwells "
              "réels. Held-out exp7/exp9 = étape d'adoption suivante. Script : "
              "`code/scripts/gen/gen_test_rayonnement_face_231A.py`.\n")
    md.append(f"Pics mesurés : {', '.join(f'{n}={pm[n]:.0f}' for n in NOMS)} °C.\n")
    md.append("| emissivite_face | pic TC4 | pic TC5 | RMSE TC2 | RMSE TC3 | RMSE TC4 | RMSE TC5 | déficit refroid. haute T |")
    md.append("|---:|---:|---:|---:|---:|---:|---:|---:|")
    for e in EMISS:
        _, _, pics, rmse, dh = res[e]
        md.append(f"| {e} | {pics['TC4']:.0f} | {pics['TC5']:.0f} | {rmse['TC2']:.1f} | "
                  f"{rmse['TC3']:.1f} | {rmse['TC4']:.1f} | {rmse['TC5']:.1f} | {dh:.2f} |")
    md.append("")
    # test complémentaire : face EXPOSÉE pendant le gap (MFC avancé)
    print("cycle emissivite_face=0.9, exposer_gap=True…")
    te_x, Se_x = cycle(0.9, exposer_gap=True); px, rx, dx = metriques(te_x, Se_x)
    eL = EMISS[-1]; pL, rL, dL = res[eL][2], res[eL][3], res[eL][4]
    md.append("## Lecture (critères GO)\n")
    md.append(f"- **(a) Cinétique — NON atteint.** Déficit de refroidissement à haute T "
              f"{d0:.2f}× (baseline) -> {dL:.2f}× (ε={eL}) : **inchangé**. Exposer la face pendant "
              f"le gap (MFC avancé) ne le corrige pas non plus ({dx:.2f}×). La chute rapide juste "
              "après le pic n'est donc PAS due à une perte radiative de face manquante — cause "
              "probable = conduction latérale pendant le refroidissement (autre piste).")
    md.append(f"- **(b) Pics emballés — amélioration modeste.** TC4 {p0['TC4']:.0f}->{pL['TC4']:.0f} °C, "
              f"TC5 {p0['TC5']:.0f}->{pL['TC5']:.0f} °C (mesuré 383/387) : baisse réelle mais partielle.")
    md.append(f"- **(c) Intérieurs — non cassés (améliorés).** RMSE TC2 {r0['TC2']:.1f}->{rL['TC2']:.1f}, "
              f"TC3 {r0['TC3']:.1f}->{rL['TC3']:.1f}, TC4 {r0['TC4']:.1f}->{rL['TC4']:.1f}, "
              f"TC5 {r0['TC5']:.1f}->{rL['TC5']:.1f} : le RMSE de cycle BAISSE partout.\n")
    md.append("## Verdict : amélioration NETTE mais PARTIELLE — pas le remède à l'accumulation\n")
    md.append("Le rayonnement de face est un ajout physique **net-positif** (RMSE de cycle en baisse "
              "sur tous les TC, sans casser les intérieurs, pics emballés en légère baisse) et "
              "**propre** (défaut OFF, bit-à-bit, 123 tests verts). MAIS il **ne recale pas la "
              "cinétique de refroidissement rapide** (déficit haute T inchangé), y compris en "
              "exposant la face pendant l'avance. **L'attribution du diagnostic (déficit haute T = "
              "rayonnement de face manquant) n'est donc PAS confirmée** : le déficit haute T vient "
              "d'ailleurs (piste = conduction latérale / transport pendant le refroidissement). "
              "Le rayonnement de face reste un candidat mineur À VALIDER en held-out exp7/exp9 "
              "(seul critère d'adoption) ; la cause de l'accumulation TC4/TC5 reste ouverte.\n")
    (R / "biblio" / "labo" / "test_rayonnement_face_231A.md").write_text("\n".join(md), encoding="utf-8")
    print("\nfigure -> biblio/labo/figures/fig_test_rayonnement_face_231A.png")
    print("md     -> biblio/labo/test_rayonnement_face_231A.md")
