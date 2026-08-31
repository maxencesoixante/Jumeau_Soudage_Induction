#!/usr/bin/env python3
"""Diagnostic du refroidissement inter-passes — cycle 231 A (issue #68, Suite #1).

QUESTION CENTRALE : le déficit de refroidissement du modèle (il refroidit ~10 %
trop lentement, cf. Étape 1 #67) est-il UNIFORME (même mur que #65 : monter
h_bas globalement = held-out NO-GO) ou DÉPENDANT DE LA TEMPÉRATURE (plus marqué
sur les segments chauds) ? Un déficit qui CROÎT avec T signerait une perte
radiative de FACE manquante : le solveur 2D n'applique le rayonnement T^4 QU'aux
chants (petite surface), les grandes faces haut/bas n'ont qu'une perte linéaire
(h_bas_2d / h_haut). À haute T le rayonnement (∝T^4) domine -> un tel levier
refroidirait surtout les zones chaudes (passes tardives) SANS sur-refroidir le
froid (≠ le h_bas global de #65).

MÉTHODE : sur chaque refroidissement inter-passes (gap) et chaque TC intérieur
fiable (TC2/3/4), ajuste T(t)=Tinf+(T0-Tinf)·exp(-t/tau) sur le RÉEL et sur le
MODÈLE DE FUSION (config ④ : L_f=40 J/g + transport k_plan(T>Tf)=100), compare
tau_modele/tau_mesure (>1 = modèle trop lent), puis teste si ce ratio croît
avec T0 (température de début de gap).

Pur diagnostic : ne modifie AUCUN fichier existant ni config par défaut.
Sorties : biblio/labo/figures/fig_diag_refroidissement_231A.png
          biblio/labo/diag_refroidissement_interpasses_231A.md
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
import gen_cycle_parfait_semistatique as g  # noqa: E402  (import-safe : plot gardé par __main__)
from jumeau.thermique.solveur2d import SolveurThermique2D  # noqa: E402
from _style import apply_style, savefig, OKABE_ITO  # noqa: E402

apply_style(**{"savefig.dpi": 200, "figure.dpi": 200})

FICH = R / "donnees" / "data" / "exp10_cycle-semistatique_231A_2026-08-26" / "231A_semistatique_bord_2026-08-26.txt"
NOMS = [f"TC{i}" for i in range(1, 6)]
INTERIEURS = ["TC2", "TC3", "TC4"]           # capteurs fiables (on écarte TC1/TC5 bord)
COUL = {n: OKABE_ITO[c] for n, c in zip(NOMS, ("noir", "bleu", "vert", "orange", "vermillon"))}
LF_PHYS = 40000.0
K_HOT = 100.0
TABLE_KT = [[0.0, 3.0], [337.0, 3.0], [380.0, K_HOT], [700.0, K_HOT]]
SEUIL_T0 = 250.0                              # segments PROPRES : le TC refroidit depuis SON pic
                                              # (au-dessous, mesuré déjà froid alors que le modèle
                                              # sur-accumulé est encore chaud -> comparaison biaisée)
FEN_HAUT = 15.0                               # fenêtre "haute T" : premières secondes du gap
BANDE_BAS = (150.0, 230.0)                    # bande "basse T" pour la vitesse de refroidissement

# --- réel + fenêtres de passe (identique aux scripts 231 A existants) ---
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


def cycle(Lf, table_kt, t_amb):
    """Modèle de fusion, piloté aux dwells réels. Renvoie (t, {TCn: série})."""
    MAT.chaleur_latente = Lf
    MAT.k_plan_T = table_kt
    amb = copy.deepcopy(E.cfg.ambiant); amb.T_amb = t_amb
    field = np.full(GR.nx * GR.ny, t_amb)
    T_out = {n: [] for n in NOMS}; t_out = []; t0 = 0.0
    for i in range(4):
        P = E._P_spots_2d[i]; Pnul = np.zeros_like(P)
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


def fit_tau(tt, TT):
    """Ajuste T(tt)=Tinf+(T0-Tinf)·exp(-tt/tau). Renvoie (tau, Tinf) ou (nan, nan)."""
    tt = np.asarray(tt, float); TT = np.asarray(TT, float)
    ok = ~np.isnan(TT)
    tt, TT = tt[ok], TT[ok]
    if len(tt) < 5:
        return np.nan, np.nan
    T0 = TT[0]
    def modele(x, tau, Tinf):
        return Tinf + (T0 - Tinf) * np.exp(-x / tau)
    try:
        p, _ = curve_fit(modele, tt - tt[0], TT, p0=[max(tt[-1] - tt[0], 1.0) / 3.0, TT[-1]],
                         bounds=([1.0, 0.0], [1.0e5, T0]), maxfev=20000)
        return float(p[0]), float(p[1])
    except Exception:
        return np.nan, np.nan


if __name__ == "__main__":
    print("simulation du modèle de fusion (config ④, 231 A)…")
    t_mod, S_mod = cycle(LF_PHYS, TABLE_KT, AMB)

    # pics de contrôle (doit reproduire l'emballement connu ~462/513)
    pics_mod = {n: float(np.nanmax(S_mod[n])) for n in NOMS}
    print("pics modèle :", {n: round(pics_mod[n]) for n in NOMS})

    def vitesse(tt, TT, sel):
        """Vitesse moyenne de refroidissement |dT/dt| (°C/s) sur la sélection ``sel``."""
        tt, TT = np.asarray(tt, float), np.asarray(TT, float)
        if sel.sum() < 2:
            return np.nan
        return float(-np.gradient(TT, tt)[sel].mean())

    # --- collecte des segments PROPRES (le TC refroidit depuis son propre pic) ---
    # métrique clé : déficit de vitesse à HAUTE T (début du gap) vs BASSE T (bande 150-230),
    # DANS le même segment -> pas de biais de sur-accumulation entre configs.
    lignes = []   # (TC, passe, T0, tau_meas, tau_mod, ratio_tau, def_haut, def_bas)
    segments = {}
    for i in range(4):
        g0 = starts[i] + dwells[i]; g1 = g0 + gaps[i]
        m = (t >= g0) & (t <= g1)
        tt_seg = t[m] - g0
        for n in INTERIEURS:
            Tmeas = S[n][m]
            if np.isnan(Tmeas).all() or Tmeas[0] < SEUIL_T0:
                continue
            Tmod = np.interp(t[m], t_mod, S_mod[n])
            tau_meas, _ = fit_tau(tt_seg, Tmeas); tau_mod, _ = fit_tau(tt_seg, Tmod)
            if np.isnan(tau_meas) or np.isnan(tau_mod) or tau_meas <= 0:
                continue
            sel_haut = tt_seg <= FEN_HAUT
            sel_bas = (Tmeas >= BANDE_BAS[0]) & (Tmeas <= BANDE_BAS[1])
            vh_m, vh_o = vitesse(tt_seg, Tmeas, sel_haut), vitesse(tt_seg, Tmod, sel_haut)
            vb_m, vb_o = vitesse(tt_seg, Tmeas, sel_bas), vitesse(tt_seg, Tmod, sel_bas)
            def_haut = vh_m / vh_o if (vh_o and vh_o > 0) else np.nan   # >1 = modèle trop lent à haute T
            def_bas = vb_m / vb_o if (vb_o and vb_o > 0) else np.nan
            lignes.append((n, i + 1, float(Tmeas[0]), tau_meas, tau_mod, tau_mod / tau_meas, def_haut, def_bas))
            segments[(n, i + 1)] = (tt_seg, Tmeas, Tmod)

    lignes.sort(key=lambda r: r[2])
    def_hauts = np.array([r[6] for r in lignes], float)
    def_bas_a = np.array([r[7] for r in lignes], float)
    med_haut = float(np.nanmedian(def_hauts)); med_bas = float(np.nanmedian(def_bas_a))
    ratios_tau = np.array([r[5] for r in lignes], float)

    # --- console ---
    print(f"\n{'TC':>4} | {'passe':>5} | {'T0':>5} | {'tau_m':>6} | {'tau_o':>6} | {'r_tau':>5} | "
          f"{'def_HAUT':>8} | {'def_BAS':>7}")
    for n, p, T0, tm, tmod, rt, dh, dbas in lignes:
        print(f"{n:>4} | {p:>5} | {T0:5.0f} | {tm:6.1f} | {tmod:6.1f} | {rt:5.2f} | {dh:8.2f} | {dbas:7.2f}")
    print(f"\ndéficit de vitesse médian — HAUTE T = {med_haut:.2f}× | BASSE T = {med_bas:.2f}× "
          f"(>1 = modèle trop lent)")
    print(f"tau_mod/tau_meas médian (segment entier) = {np.nanmedian(ratios_tau):.2f}×")

    # --- figure ---
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(12.5, 5.0))
    # A : 2-3 segments propres (du moins chaud au plus chaud) mesuré vs modèle
    rep = lignes[:: max(1, len(lignes) // 3)][:3] if lignes else []
    for n, p, T0, *_ in rep:
        tt_seg, Tmeas, Tmod = segments[(n, p)]
        c = COUL[n]
        axA.plot(tt_seg, Tmeas, color=c, lw=1.9, label=f"{n} P{p} mesuré (T0={T0:.0f})")
        axA.plot(tt_seg, Tmod, color=c, lw=1.4, ls=(0, (4, 1.8)), label=f"{n} P{p} modèle")
    axA.set_xlabel("Temps depuis début du gap (s)")
    axA.set_ylabel("Température (°C)")
    axA.set_title("Refroidissement depuis le pic : mesuré vs modèle", fontsize=11, fontweight="bold")
    axA.legend(loc="upper right", fontsize=7.2, framealpha=0.93)

    # B : déficit de vitesse HAUTE T vs BASSE T (barres groupées par segment)
    labs = [f"{r[0]}·P{r[1]}\n{r[2]:.0f}°C" for r in lignes]
    xpos = np.arange(len(lignes)); w = 0.38
    axB.axhline(1.0, color="0.6", lw=0.9, ls=":")
    axB.bar(xpos - w / 2, def_hauts, w, color=OKABE_ITO["vermillon"], label="haute T (début gap)")
    axB.bar(xpos + w / 2, def_bas_a, w, color=OKABE_ITO["bleu"], label="basse T (150-230 °C)")
    axB.set_xticks(xpos); axB.set_xticklabels(labs, fontsize=7.0)
    axB.set_ylabel("déficit de vitesse : mesuré/modèle  (>1 = modèle trop lent)")
    axB.set_title("Déficit concentré à HAUTE T ?", fontsize=11, fontweight="bold")
    axB.legend(loc="upper right", fontsize=7.8, framealpha=0.93)
    fig.tight_layout()
    savefig(fig, R / "biblio" / "labo" / "figures" / "fig_diag_refroidissement_231A")
    plt.close(fig)

    # --- verdict : le déficit est-il concentré à HAUTE T ? ---
    # (déficit_haut nettement > déficit_bas ET > 1 => perte à haute T manquante => piste radiative)
    verdict_td = (not np.isnan(med_haut) and not np.isnan(med_bas)
                  and med_haut > 1.4 and med_haut > 1.5 * med_bas)
    verdict = ("**DÉFICIT CONCENTRÉ À HAUTE T → GO (piste rayonnement de face)**" if verdict_td
               else "**DÉFICIT QUASI UNIFORME EN T → NO-GO (mur #65)**")
    md = []
    md.append("# Diagnostic du refroidissement inter-passes — cycle 231 A (issue #68, Suite #1)\n")
    md.append("Question : le déficit de refroidissement du modèle (fusion, config ④) est-il concentré "
              "à HAUTE température (signe d'une perte radiative de FACE manquante : le solveur 2D "
              "n'applique le rayonnement T⁴ qu'aux chants, pas aux grandes faces haut/bas) ou "
              "UNIFORME en T (accélérer = perte globale = territoire held-out NO-GO de #65) ?\n")
    md.append("Métrique décisive **intra-segment** (pas de biais de sur-accumulation) : sur chaque "
              "refroidissement d'un TC intérieur depuis SON pic (T0>250 °C), on compare la vitesse "
              "de refroidissement mesuré/modèle à HAUTE T (premières " f"{FEN_HAUT:.0f} s du gap) vs à "
              f"BASSE T (bande {BANDE_BAS[0]:.0f}-{BANDE_BAS[1]:.0f} °C). `déficit>1` = modèle trop lent.\n")
    md.append(f"Script : `code/scripts/gen/gen_diag_refroidissement_231A.py`. Pics modèle (contrôle "
              f"emballement connu ≈462/513) : {', '.join(f'{n}={round(pics_mod[n])}' for n in NOMS)} °C.\n")
    md.append("## Segments propres (refroidissement depuis le pic)\n")
    md.append("| TC | passe | T0 (°C) | tau_meas (s) | tau_mod (s) | déficit HAUTE T | déficit BASSE T |")
    md.append("|---|:---:|---:|---:|---:|---:|---:|")
    for n, p, T0, tm, tmod, rt, dh, dbas in lignes:
        md.append(f"| {n} | {p} | {T0:.0f} | {tm:.1f} | {tmod:.1f} | {dh:.2f} | {dbas:.2f} |")
    md.append("")
    md.append(f"**Déficit de vitesse médian : HAUTE T = {med_haut:.2f}× , BASSE T = {med_bas:.2f}×.** "
              f"(tau_mod/tau_meas médian sur segment entier = {np.nanmedian(ratios_tau):.2f}×.)\n")
    md.append("Note méthodo : les segments à T0<250 °C sont ÉCARTÉS — le mesuré y est déjà froid "
              "alors que le modèle, sur-accumulé, y est encore chaud (comparaison biaisée). Les tau "
              "élevés (modèle 2-3× trop lent sur segment entier) confirment un déficit de "
              "refroidissement bien supérieur au « ~10 % » folklorique.\n")
    md.append(f"## Verdict : {verdict}\n")
    if verdict_td:
        md.append(f"Le déficit de refroidissement est **concentré à haute T** (médian {med_haut:.2f}× à "
                  f"haute T contre {med_bas:.2f}× à basse T) : le modèle rate surtout la chute rapide "
                  "juste après le pic. C'est la signature d'une **perte à haute T manquante** → "
                  "**piste rayonnement de FACE (T⁴) à implémenter puis valider en held-out** "
                  "(exp7/exp9). Ce levier n'agissant qu'à haute T, il n'a pas la pathologie du h_bas "
                  "global de #65 (qui sur-refroidit les zones froides). Prochaine étape = "
                  "implémenter le terme radiatif de face (émissivité·σ·(T⁴−T_amb⁴) sur faces haut/bas) "
                  "en variante, et vérifier : (a) rapproche la cinétique, (b) abaisse TC4/TC5, "
                  "(c) held-out exp7/exp9 neutre.\n")
    else:
        md.append(f"Le déficit est **comparable à haute et basse T** ({med_haut:.2f}× vs {med_bas:.2f}×) : "
                  "accélérer le refroidissement reviendrait à une perte quasi globale — le territoire "
                  "déjà réfuté en held-out par #65. **Suite #1 = impasse probable** ; basculer sur le "
                  "résidu structurel (Suite #3).\n")
    (R / "biblio" / "labo" / "diag_refroidissement_interpasses_231A.md").write_text("\n".join(md), encoding="utf-8")
    print("\nVERDICT :", verdict.replace("**", ""))
    print("figure  -> biblio/labo/figures/fig_diag_refroidissement_231A.png")
    print("md      -> biblio/labo/diag_refroidissement_interpasses_231A.md")
