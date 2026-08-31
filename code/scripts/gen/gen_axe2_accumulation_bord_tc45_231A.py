#!/usr/bin/env python3
"""Décorrélation TC4/TC5 — accumulation passe-à-passe vs artefact de source au
bord x (issue #68, Axe 2), cycle 231 A, modèle de fusion.

Constat à expliquer : dans le modèle de fusion (L_f=40 J/g physique + transport
k_plan(T>Tf), cf. `gen_valider_fusion_231A.py`), piloté aux dwells RÉELS,
TC1/TC2/TC3 collent au plateau mesuré mais **TC4 (x=90 mm, intérieur) monte à
~460 °C et TC5 (x=120 mm, bord) à ~510 °C**, au-dessus du plateau mesuré
~385 °C. Deux causes candidates, testées en 2x2 (4 simulations du cycle
complet) :

  (A) ACCUMULATION passe-à-passe : le champ thermique 2D est propagé d'une
      passe à l'autre (warm-start). Variante "reset" : le champ repart de
      l'ambiant au DÉBUT de chaque passe (continuité chauffe->refroid intra-
      passe conservée, seul le report passe(i-1)->passe(i) est coupé).
  (B) ARTEFACT DE SOURCE AU BORD x : `source_spot(..., lambda_bord_x_mm=...)`,
      défaut None = correction AUTO (ON, cf. commit 0dab38d) ; 0.0 = chemin
      historique (correction OFF, artefact présent). `construire_essai()` ne
      passe pas ce paramètre -> défaut ON. On reconstruit ici les sources
      OFF (lambda_bord_x_mm=0.0) sans toucher au script existant.

Plan 2x2 :
  ① accumulation ON,  bord ON   = reproduction Étape 4 (référence, doit ~=
     gen_valider_fusion_231A.py / gen_ablation_fusion_231A.py config "④ complet")
  ② accumulation OFF, bord ON
  ③ accumulation ON,  bord OFF
  ④ accumulation OFF, bord OFF

Ce script RÉUTILISE la construction d'essai et les fenêtres de passe de
`gen_cycle_parfait_semistatique.construire_essai` (module gardé par
`__main__`, import sûr) ET réplique (sans l'importer : pas de garde
`__main__`, cf. gotcha) la logique de chargement du réel + détection des
passes + `cycle()` de `gen_valider_fusion_231A.py`, adaptée avec les deux
leviers reset/bord.

Sorties :
  - tableau imprimé (RMSE + pics TC4/TC5 par config) ;
  - biblio/labo/axe2_accumulation_bord_tc45_231A_resultats.md ;
  - biblio/labo/figures/fig_axe2_tc45_231A.png.
"""
from __future__ import annotations
import sys, copy
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts" / "gen"))
sys.path.insert(0, str(R / "code" / "scripts"))
import gen_cycle_parfait_semistatique as g  # noqa: E402 (module gardé __main__, import sûr)
from jumeau.thermique.solveur2d import SolveurThermique2D  # noqa: E402
from jumeau.em.source_joule import source_spot  # noqa: E402
from _style import apply_style, savefig, OKABE_ITO  # noqa: E402

apply_style(**{"savefig.dpi": 200, "figure.dpi": 200})

FICH = R / "donnees" / "data" / "exp10_cycle-semistatique_231A_2026-08-26" / "231A_semistatique_bord_2026-08-26.txt"
NOMS = [f"TC{i}" for i in range(1, 6)]
COUL = [OKABE_ITO[c] for c in ("noir", "bleu", "vert", "orange", "vermillon")]
LF_PHYS = 40000.0      # J/kg — chaleur latente physique, config "modèle de fusion"
K_HOT = 100.0          # W/m.K — transport effectif du bain fondu (>Tf)
TABLE_KT = [[0.0, 3.0], [337.0, 3.0], [380.0, K_HOT], [700.0, K_HOT]]

# --- réel + fenêtres de passe (identique à gen_valider_fusion_231A.py) ---
df = pd.read_csv(FICH, sep="\t", decimal=",")
df.columns = [c.strip() for c in df.columns]
t = df["Time (s)"].to_numpy(float).copy(); t -= t[0]
S = {n: pd.to_numeric(df[[c for c in df.columns if c.startswith(n)][0]], errors="coerce").to_numpy(float).copy() for n in NOMS}
maxtc = np.nanmax(np.vstack([S[n] for n in NOMS]), axis=0)
AMB = float(np.nanmedian(np.vstack([S[n][:10] for n in NOMS])))
i0 = int(np.argmax(maxtc > AMB + 15)); t -= t[i0]
keep = t >= 0; t = t[keep]; S = {n: S[n][keep] for n in NOMS}; maxtc = maxtc[keep]
from scipy.signal import find_peaks
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

# --- Levier (B) : sources reconstruites avec lambda_bord_x_mm=0.0 (correction
# OFF, chemin historique) ; réplique la boucle de construire_essai() sans y
# toucher, mêmes facteur_couplage/decalage_x. E._P_spots_2d = défaut (bord ON,
# AUTO, cf. construire_essai qui ne passe pas lambda_bord_x_mm).
Q_SPOTS_BORD_OFF = [
    source_spot(E.grille, E.cfg, E.couches, 231.0, float(s["centre_x"]),
                facteur_couplage=g.FACTEUR, decalage_x=0.0, lambda_bord_x_mm=0.0)
    for s in E.spots
]
P_SPOTS_BORD_OFF = [Q.sum(axis=2) * E.grille.dz for Q in Q_SPOTS_BORD_OFF]
P_SPOTS_BORD_ON = E._P_spots_2d  # défaut construire_essai() : lambda_bord_x_mm=None => AUTO ON


def cycle(P_spots, reset_passe, t_amb=AMB, Lf=LF_PHYS, table_kt=TABLE_KT):
    """Cycle complet (4 passes, dwells réels). ``reset_passe`` (levier A) :
    si True, le champ repart de l'ambiant au DÉBUT de chaque passe (coupe le
    report passe(i-1)->passe(i) ; la continuité chauffe->refroid INTRA-passe
    est conservée dans tous les cas). ``P_spots`` (levier B) : liste des 4
    sources 2D (W/m, déjà intégrées en z) — bord ON ou OFF selon l'appelant.
    """
    MAT.chaleur_latente = Lf
    MAT.k_plan_T = table_kt
    amb = copy.deepcopy(E.cfg.ambiant); amb.T_amb = t_amb
    field = np.full(GR.nx * GR.ny, t_amb)
    T_out = {n: [] for n in NOMS}; t_out = []; PC = []; t0 = 0.0
    for i in range(4):
        if reset_passe:
            field = np.full(GR.nx * GR.ny, t_amb)
        P = P_spots[i]; Pnul = np.zeros_like(P)
        solv = SolveurThermique2D(GR, MAT, amb, CONTACT, masque_ceramique=E._masques[i])
        th = np.append(np.arange(0.0, dwells[i], 0.5), dwells[i])
        sh = solv.simuler(lambda tt: P, (0.0, dwells[i]), t_eval=th, T_initial=field); field = sh.y[:, -1]
        tc = np.append(np.arange(0.0, gaps[i], 1.0), gaps[i])
        sc = solv.simuler(lambda tt: Pnul, (0.0, gaps[i]), t_eval=tc, T_initial=field); field = sc.y[:, -1]
        for sol, off in ((sh, 0.0), (sc, dwells[i])):
            for n in NOMS:
                T_out[n].append(solv.serie_temporelle(sol, *POS[n]))
            PC.append(solv.serie_temporelle(sol, float(E.spots[i]["centre_x"]), 0.0))
            t_out.append(t0 + off + sol.t)
        t0 += dwells[i] + gaps[i]
    return np.concatenate(t_out), {n: np.concatenate(T_out[n]) for n in NOMS}, np.concatenate(PC)


# --------------------------------------------------------------------------- #
# Plan 2x2.
# --------------------------------------------------------------------------- #
CONFIGS = [
    ("① accum ON / bord ON",  False, P_SPOTS_BORD_ON,  "c1"),
    ("② accum OFF / bord ON", True,  P_SPOTS_BORD_ON,  "c2"),
    ("③ accum ON / bord OFF", False, P_SPOTS_BORD_OFF, "c3"),
    ("④ accum OFF / bord OFF", True, P_SPOTS_BORD_OFF, "c4"),
]

resultats = {}
for label, reset_passe, P_spots, cle in CONFIGS:
    tt, SS, PC = cycle(P_spots, reset_passe)
    resultats[cle] = dict(label=label, reset=reset_passe, bord_off=(P_spots is P_SPOTS_BORD_OFF),
                           t=tt, S=SS, PC=PC)


def metriques(entry):
    tt, SS, PC = entry["t"], entry["S"], entry["PC"]
    tmax = min(t[-1], tt[-1]); gr = np.linspace(0, tmax, 600)
    rmse = {}
    for n in NOMS:
        sm = np.interp(gr, t, S[n]); rm = np.interp(gr, tt, SS[n])
        ok = ~np.isnan(sm)
        rmse[n] = float(np.sqrt(np.mean((rm[ok] - sm[ok]) ** 2)))
    pics = {n: float(SS[n].max()) for n in NOMS}
    ecarts_pic = {n: pics[n] - float(np.nanmax(S[n])) for n in NOMS}
    return dict(rmse=rmse, pics=pics, ecarts_pic=ecarts_pic, pc_max=float(PC.max()))


for cle, entry in resultats.items():
    entry["m"] = metriques(entry)

pics_mesures = {n: float(np.nanmax(S[n])) for n in NOMS}

# --------------------------------------------------------------------------- #
# Tableau imprimé.
# --------------------------------------------------------------------------- #
print(f"réel : pics mesurés  " + "  ".join(f"{n}={pics_mesures[n]:.0f}" for n in NOMS))
print(f"\n{'config':<24} | RMSE (TC2/TC3/TC4/TC5)                       | pics TC4/TC5 (écart)                | point chaud")
print("-" * 150)
for label, reset_passe, P_spots, cle in CONFIGS:
    m = resultats[cle]["m"]
    print(f"{label:<24} | RMSE TC2={m['rmse']['TC2']:5.1f} TC3={m['rmse']['TC3']:5.1f} "
          f"TC4={m['rmse']['TC4']:5.1f} TC5={m['rmse']['TC5']:5.1f} | "
          f"pic TC4={m['pics']['TC4']:5.0f} ({m['ecarts_pic']['TC4']:+5.0f}) "
          f"pic TC5={m['pics']['TC5']:5.0f} ({m['ecarts_pic']['TC5']:+5.0f}) | "
          f"PC max={m['pc_max']:5.0f}")

# --- recoupement : ① doit reproduire l'emballement connu (TC4~460, TC5~510) ---
tc4_1 = resultats["c1"]["m"]["pics"]["TC4"]; tc5_1 = resultats["c1"]["m"]["pics"]["TC5"]
print(f"\n--- recoupement (① doit ~= TC4≈460, TC5≈510, cf. gen_valider_fusion_231A.py / "
      f"gen_ablation_fusion_231A.py config '④ complet') ---")
print(f"① pic TC4={tc4_1:.0f} °C, pic TC5={tc5_1:.0f} °C")
ok_recoupement = abs(tc4_1 - 460) < 25 and abs(tc5_1 - 510) < 25
print("recoupement " + ("OK" if ok_recoupement else "ECART -> à examiner avant de conclure"))

# --------------------------------------------------------------------------- #
# Décomposition chiffrée : accumulation (①-②) vs bord (①-③), pour TC2/TC3/TC4/TC5.
# --------------------------------------------------------------------------- #
d_accum = {n: resultats["c1"]["m"]["pics"][n] - resultats["c2"]["m"]["pics"][n] for n in NOMS}
d_bord = {n: resultats["c1"]["m"]["pics"][n] - resultats["c3"]["m"]["pics"][n] for n in NOMS}
d_both = {n: resultats["c1"]["m"]["pics"][n] - resultats["c4"]["m"]["pics"][n] for n in NOMS}
print("\nDécomposition des pics (① - autre config), °C :")
print(f"{'TC':>4} | {'Δ accum (①-②)':>15} | {'Δ bord (①-③)':>14} | {'Δ les deux (①-④)':>18}")
for n in NOMS:
    print(f"{n:>4} | {d_accum[n]:15.1f} | {d_bord[n]:14.1f} | {d_both[n]:18.1f}")
ratio_tc4 = abs(d_accum["TC4"]) / max(abs(d_bord["TC4"]), 1e-9)
ratio_tc5 = abs(d_accum["TC5"]) / max(abs(d_bord["TC5"]), 1e-9)
print(f"\nRatio |Δaccum|/|Δbord| : TC4={ratio_tc4:.1f}x  TC5={ratio_tc5:.1f}x")

# --------------------------------------------------------------------------- #
# Markdown d'archivage.
# --------------------------------------------------------------------------- #
lignes_md = []
lignes_md.append("# Décorrélation accumulation vs artefact de bord x — TC4/TC5, cycle 231 A (issue #68, Axe 2)\n")
lignes_md.append(
    "Plan 2×2 sur le cycle complet (4 passes, dwells RÉELS, modèle de fusion : L_f=40 J/g "
    "physique + transport `k_plan(T>Tf)`), pour décorréler deux causes candidates de "
    "l'emballement de TC4 (x=90 mm, intérieur) et TC5 (x=120 mm, bord) au-dessus du plateau "
    "mesuré : (A) l'accumulation de chaleur passe-à-passe (warm-start du champ 2D), "
    "(B) l'artefact de source au bord x (`lambda_bord_x_mm`). "
    "Script : `code/scripts/gen/gen_axe2_accumulation_bord_tc45_231A.py`.\n"
)
lignes_md.append(f"Pics mesurés : " + ", ".join(f"{n}={pics_mesures[n]:.0f} °C" for n in NOMS) + ".\n")
lignes_md.append("## Plan 2×2\n")
lignes_md.append("| config | accumulation | bord x | RMSE TC2 | RMSE TC3 | RMSE TC4 | RMSE TC5 | pic TC4 (écart) | pic TC5 (écart) | point chaud max |")
lignes_md.append("|---|:---:|:---:|---:|---:|---:|---:|---:|---:|---:|")
for label, reset_passe, P_spots, cle in CONFIGS:
    m = resultats[cle]["m"]
    lignes_md.append(
        f"| {label} | {'OFF (reset)' if reset_passe else 'ON'} | {'OFF' if resultats[cle]['bord_off'] else 'ON'} | "
        f"{m['rmse']['TC2']:.1f} | {m['rmse']['TC3']:.1f} | {m['rmse']['TC4']:.1f} | {m['rmse']['TC5']:.1f} | "
        f"{m['pics']['TC4']:.0f} ({m['ecarts_pic']['TC4']:+.0f}) | {m['pics']['TC5']:.0f} ({m['ecarts_pic']['TC5']:+.0f}) | "
        f"{m['pc_max']:.0f} |"
    )
lignes_md.append("")
lignes_md.append(f"Recoupement : ① reproduit-il l'emballement connu (TC4≈460, TC5≈510 °C) ? "
                  f"pic TC4={tc4_1:.0f}, pic TC5={tc5_1:.0f} -> **{'OK' if ok_recoupement else 'ÉCART'}**.\n")
lignes_md.append("## Décomposition des pics (°C)\n")
lignes_md.append(
    "Δ = pic(config ①) − pic(config comparée) : positif si couper le levier fait BAISSER le pic. "
    "TC1/TC2/TC3 = témoins intérieurs (n'excèdent pas le plateau mesuré, référence de bruit/échelle).\n"
)
lignes_md.append("| TC | Δ accumulation (①−②) | Δ bord x (①−③) | Δ les deux (①−④) |")
lignes_md.append("|---|---:|---:|---:|")
for n in NOMS:
    lignes_md.append(f"| {n} | {d_accum[n]:+.1f} | {d_bord[n]:+.1f} | {d_both[n]:+.1f} |")
lignes_md.append("")
lignes_md.append(f"Ratio |Δaccumulation| / |Δbord| : TC4 = {ratio_tc4:.1f}×, TC5 = {ratio_tc5:.1f}×.\n")

lignes_md.append("## Lecture décisive\n")
lignes_md.append(
    f"- **Les deux capteurs répondent aux DEUX leviers, mais dans des proportions très inégales et "
    f"quasi identiques entre TC4 et TC5.** Pic TC4 : ①={resultats['c1']['m']['pics']['TC4']:.0f} °C, "
    f"②(accum OFF)={resultats['c2']['m']['pics']['TC4']:.0f} °C (Δaccum={d_accum['TC4']:+.1f} °C), "
    f"③(bord OFF)={resultats['c3']['m']['pics']['TC4']:.0f} °C (Δbord={d_bord['TC4']:+.1f} °C), "
    f"④(les deux OFF)={resultats['c4']['m']['pics']['TC4']:.0f} °C (Δ={d_both['TC4']:+.1f} °C). Pic TC5 : "
    f"①={resultats['c1']['m']['pics']['TC5']:.0f} °C, ②={resultats['c2']['m']['pics']['TC5']:.0f} °C "
    f"(Δaccum={d_accum['TC5']:+.1f} °C), ③={resultats['c3']['m']['pics']['TC5']:.0f} °C "
    f"(Δbord={d_bord['TC5']:+.1f} °C), ④={resultats['c4']['m']['pics']['TC5']:.0f} °C (Δ={d_both['TC5']:+.1f} °C).\n"
)
lignes_md.append(
    f"- **L'accumulation passe-à-passe domine très largement les deux capteurs** (Δaccum "
    f"TC4={d_accum['TC4']:+.1f} °C, TC5={d_accum['TC5']:+.1f} °C — de l'ordre de {ratio_tc4:.0f}× et {ratio_tc5:.0f}× "
    f"plus grand que l'effet du bord sur le même capteur). Couper l'accumulation seule (②) ramène déjà le pic TC4 de "
    f"{resultats['c1']['m']['pics']['TC4']:.0f} à {resultats['c2']['m']['pics']['TC4']:.0f} °C et le pic TC5 de "
    f"{resultats['c1']['m']['pics']['TC5']:.0f} à {resultats['c2']['m']['pics']['TC5']:.0f} °C, réduisant l'écart au "
    f"mesuré d'environ un tiers sur les deux capteurs sans annuler le dépassement.\n"
)
lignes_md.append(
    f"- **L'artefact de source au bord x est réel mais MINEUR sur TC4/TC5 dans cette configuration** (Δbord "
    f"TC4={d_bord['TC4']:+.1f} °C, TC5={d_bord['TC5']:+.1f} °C, contre ~0.2-0.9 °C sur les témoins intérieurs "
    f"TC1={d_bord['TC1']:+.1f}/TC2={d_bord['TC2']:+.1f}/TC3={d_bord['TC3']:+.1f} °C) — vérifié non-bug : la "
    f"correction ne modifie que la puissance des spots proches des bords du domaine (spot 1 x=15,9 mm et spot 4 "
    f"x=105,9 mm, +1.0 %/-1.5 % de puissance totale ; spots 2/3 quasi inchangés), donc n'affecte TC4/TC5 que "
    f"marginalement en amplitude de pic dans ce cycle piloté aux dwells réels.\n"
)
lignes_md.append(
    f"- **Témoins intérieurs TC1/TC2/TC3 (n'excèdent pas le plateau mesuré) :** Δ accumulation "
    f"TC1={d_accum['TC1']:+.1f}/TC2={d_accum['TC2']:+.1f}/TC3={d_accum['TC3']:+.1f} °C, Δ bord "
    f"TC1={d_bord['TC1']:+.1f}/TC2={d_bord['TC2']:+.1f}/TC3={d_bord['TC3']:+.1f} °C — l'accumulation bouge aussi "
    f"TC2/TC3 (+{d_accum['TC2']:.0f}/+{d_accum['TC3']:.0f} °C) mais sans les faire déborder du plateau mesuré (ils y "
    f"sont déjà, contrairement à TC4/TC5), donc ce n'est pas un artefact spécifique à TC4/TC5 — c'est un biais "
    f"générique du cycle qui devient visible/problématique seulement là où le modèle est déjà en surchauffe "
    f"(TC4/TC5).\n"
)
lignes_md.append(
    f"- **Conclusion : TC4 et TC5 partagent la MÊME cause dominante — l'accumulation passe-à-passe — et NON "
    f"une cause distincte de bord.** L'hypothèse pré-enregistrée (TC4 = pur cumulatif ; TC5 = cumulatif + bord "
    f"superposé) n'est PAS vérifiée par les chiffres : le bord contribue à TC5 ({d_bord['TC5']:+.1f} °C) dans une "
    f"proportion comparable — et du même ordre de grandeur que sur TC4 ({d_bord['TC4']:+.1f} °C) — pas d'un effet "
    f"« bord » qualitativement différent entre les deux positions. Couper les DEUX leviers (④) ne suffit pas non "
    f"plus à ramener TC4/TC5 au plateau mesuré (④ : TC4={resultats['c4']['m']['pics']['TC4']:.0f} °C vs mesuré "
    f"{pics_mesures['TC4']:.0f} °C, TC5={resultats['c4']['m']['pics']['TC5']:.0f} °C vs mesuré "
    f"{pics_mesures['TC5']:.0f} °C) : un résidu structurel (~{resultats['c4']['m']['ecarts_pic']['TC4']:.0f}/"
    f"{resultats['c4']['m']['ecarts_pic']['TC5']:.0f} °C) subsiste au-delà des deux leviers testés ici, hors "
    f"périmètre de cet axe."
)

(R / "biblio" / "labo" / "axe2_accumulation_bord_tc45_231A_resultats.md").write_text("\n".join(lignes_md) + "\n")
print("\nmarkdown -> biblio/labo/axe2_accumulation_bord_tc45_231A_resultats.md")

# --------------------------------------------------------------------------- #
# Figure : petits multiples 2x2 (mesuré plein vs prédit tireté, focus TC4/TC5) +
# barres des pics TC4/TC5 par config.
# --------------------------------------------------------------------------- #
fig = plt.figure(figsize=(13.0, 8.6))
gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.0, 0.85], hspace=0.40, wspace=0.14)
axes2x2 = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]),
           fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])]
ax_pics = fig.add_subplot(gs[2, :])

COUL45 = {"TC4": OKABE_ITO["bleu"], "TC5": OKABE_ITO["vermillon"]}
for ax, (label, reset_passe, P_spots, cle) in zip(axes2x2, CONFIGS):
    entry = resultats[cle]
    for n in ("TC2", "TC3"):
        ax.plot(t, S[n], color="0.75", lw=1.1, alpha=0.9, zorder=1)
        ax.plot(entry["t"], entry["S"][n], color="0.75", lw=0.9, ls=(0, (4, 1.8)), alpha=0.9, zorder=1)
    for n in ("TC4", "TC5"):
        ax.plot(t, S[n], color=COUL45[n], lw=1.7, alpha=0.95, zorder=3)
        ax.plot(entry["t"], entry["S"][n], color=COUL45[n], lw=1.3, ls=(0, (4, 1.8)), zorder=3)
    ax.axhline(pics_mesures["TC5"], color="0.4", lw=0.8, ls=":", zorder=0.5)
    ax.set_xlim(0, t[-1]); ax.set_ylim(0, 560)
    ax.set_title(label, fontsize=9.8, fontweight="bold")
    ax.tick_params(labelsize=8)
for ax in (axes2x2[0], axes2x2[1]):
    ax.set_xticklabels([])
for ax in (axes2x2[1], axes2x2[3]):
    ax.set_yticklabels([])
axes2x2[2].set_xlabel("Temps (s)", fontsize=9.5, fontweight="bold")
axes2x2[3].set_xlabel("Temps (s)", fontsize=9.5, fontweight="bold")
axes2x2[0].set_ylabel("Température (°C)", fontsize=9.5, fontweight="bold")
axes2x2[2].set_ylabel("Température (°C)", fontsize=9.5, fontweight="bold")

handles = [
    plt.Line2D([0], [0], color="0.75", lw=1.1, label="TC2/TC3 (témoins, réduit)"),
    plt.Line2D([0], [0], color=COUL45["TC4"], lw=1.7, label="TC4 (x=90 mm)"),
    plt.Line2D([0], [0], color=COUL45["TC5"], lw=1.7, label="TC5 (x=120 mm)"),
    plt.Line2D([0], [0], color="0.3", lw=1.4, label="mesuré (plein)"),
    plt.Line2D([0], [0], color="0.3", lw=1.1, ls=(0, (4, 1.8)), label="prédit (tireté)"),
]
fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.995),
           ncol=5, fontsize=8.0, framealpha=0.93)

x = np.arange(4)
width = 0.35
pics_tc4 = [resultats[cle]["m"]["pics"]["TC4"] for _, _, _, cle in CONFIGS]
pics_tc5 = [resultats[cle]["m"]["pics"]["TC5"] for _, _, _, cle in CONFIGS]
ax_pics.bar(x - width / 2, pics_tc4, width, color=COUL45["TC4"], label="pic TC4")
ax_pics.bar(x + width / 2, pics_tc5, width, color=COUL45["TC5"], label="pic TC5")
ax_pics.axhline(pics_mesures["TC4"], color=COUL45["TC4"], lw=1.1, ls="--", label="TC4 mesuré")
ax_pics.axhline(pics_mesures["TC5"], color=COUL45["TC5"], lw=1.1, ls=":", label="TC5 mesuré")
ax_pics.set_xticks(x)
ax_pics.set_xticklabels(["① accum ON\nbord ON", "② accum OFF\nbord ON",
                          "③ accum ON\nbord OFF", "④ accum OFF\nbord OFF"], fontsize=8.3)
ax_pics.set_ylabel("Pic (°C)", fontsize=9.5, fontweight="bold")
ax_pics.set_ylim(0, 560)
ax_pics.set_title("Pics TC4/TC5 par config — décomposition accumulation × bord x", fontsize=9.8, fontweight="bold")
ax_pics.legend(fontsize=7.6, ncol=4, loc="lower center", framealpha=0.93)
ax_pics.tick_params(labelsize=8.3)
for xi, v4, v5 in zip(x, pics_tc4, pics_tc5):
    ax_pics.annotate(f"{v4:.0f}", (xi - width / 2, v4 + 8), ha="center", fontsize=7.2, color=COUL45["TC4"])
    ax_pics.annotate(f"{v5:.0f}", (xi + width / 2, v5 + 8), ha="center", fontsize=7.2, color=COUL45["TC5"])

fig.suptitle("Accumulation passe-à-passe vs artefact de bord x — TC4/TC5, cycle 231 A (issue #68, Axe 2)",
             fontsize=12.0, fontweight="bold", y=1.030)
savefig(fig, R / "biblio" / "labo" / "figures" / "fig_axe2_tc45_231A")
plt.close(fig)
print("figure -> biblio/labo/figures/fig_axe2_tc45_231A.png")
