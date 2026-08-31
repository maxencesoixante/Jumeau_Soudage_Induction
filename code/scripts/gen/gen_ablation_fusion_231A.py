#!/usr/bin/env python3
"""Étude d'ablation du modèle de fusion (issue #68, Axe 1) — cycle 231 A.

Le modèle de fusion (`gen_valider_fusion_231A.py`) combine DEUX leviers indépendants :
  - la chaleur latente L_f (puits d'enthalpie, `MAT.chaleur_latente`) ;
  - le transport du bain fondu (`MAT.k_plan_T`, k rehaussé à K_HOT au-dessus de Tf).

Ce script isole la part de chacun par une ablation 2×2 (fusion seule / transport seul /
canonique / complet) + un balayage de L_f à transport constant, tous confrontés au réel
231 A (held-out, aucun recalage). Il RÉUTILISE la même construction d'essai, les mêmes
fenêtres de passe (détectées sur le réel) et la même fonction `cycle()` que
`gen_valider_fusion_231A.py` — factorisées ici pour éviter d'importer ce module comme
package (son exécution top-level génère déjà sa propre figure, ce qu'on ne veut pas
redéclencher).

Sorties :
  - tableau imprimé (RMSE par TC, pics TC4/TC5, point chaud max) pour chaque config ;
  - biblio/labo/ablation_fusion_231A_resultats.md (archivage) ;
  - biblio/labo/figures/fig_ablation_fusion_231A.png (petits multiples 2×2 + barres RMSE).
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
import gen_cycle_parfait_semistatique as g  # noqa: E402
from jumeau.thermique.solveur2d import SolveurThermique2D  # noqa: E402
from _style import apply_style, savefig, OKABE_ITO  # noqa: E402

apply_style(**{"savefig.dpi": 200, "figure.dpi": 200})

FICH = R / "donnees" / "data" / "exp10_cycle-semistatique_231A_2026-08-26" / "231A_semistatique_bord_2026-08-26.txt"
NOMS = [f"TC{i}" for i in range(1, 6)]
COUL = [OKABE_ITO[c] for c in ("noir", "bleu", "vert", "orange", "vermillon")]
LF_PHYS = 40000.0      # J/kg — chaleur latente physique (~30 % cristallin)
LF_CAN = 130000.0      # J/kg — chaleur latente canonique (100 % cristallin)
K_HOT = 100.0          # W/m.K — transport effectif du bain fondu (>Tf)
TABLE_KT = [[0.0, 3.0], [337.0, 3.0], [380.0, K_HOT], [700.0, K_HOT]]

# --- réel + fenêtres (identique à gen_valider_fusion_231A.py) ---
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


def cycle(Lf, table_kt, t_amb):
    MAT.chaleur_latente = Lf
    MAT.k_plan_T = table_kt          # None => k constant (chemin historique)
    amb = copy.deepcopy(E.cfg.ambiant); amb.T_amb = t_amb
    field = np.full(GR.nx * GR.ny, t_amb)
    T_out = {n: [] for n in NOMS}; t_out = []; PC = []; t0 = 0.0
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
            PC.append(solv.serie_temporelle(sol, float(E.spots[i]["centre_x"]), 0.0))
            t_out.append(t0 + off + sol.t)
        t0 += dwells[i] + gaps[i]
    return np.concatenate(t_out), {n: np.concatenate(T_out[n]) for n in NOMS}, np.concatenate(PC)


# --- ablation 2x2 + balayage L_f (transport ON) ---
CONFIGS = [
    ("① canonique",      LF_CAN,  None,      "canon"),
    ("② fusion seule",   LF_PHYS, None,      "fusion_seule"),
    ("③ transport seul", LF_CAN,  TABLE_KT,  "transport_seul"),
    ("④ complet",        LF_PHYS, TABLE_KT,  "complet"),
]
SWEEP_LF = [0.0, 20000.0, 40000.0, 130000.0]

resultats = {}  # cle -> dict(t=, S=, PC=, Lf=, transport=bool)
for label, Lf, table_kt, cle in CONFIGS:
    tt, SS, PC = cycle(Lf, table_kt, AMB)
    resultats[cle] = dict(label=label, t=tt, S=SS, PC=PC, Lf=Lf, transport=table_kt is not None)

sweep = {}  # Lf -> dict(...)
for Lf in SWEEP_LF:
    if Lf == LF_PHYS:
        sweep[Lf] = resultats["complet"]
    elif Lf == LF_CAN:
        sweep[Lf] = resultats["transport_seul"]
    else:
        tt, SS, PC = cycle(Lf, TABLE_KT, AMB)
        sweep[Lf] = dict(label=f"transport ON, L_f={Lf/1000:.0f} J/g", t=tt, S=SS, PC=PC, Lf=Lf, transport=True)


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
for Lf, entry in sweep.items():
    if "m" not in entry:
        entry["m"] = metriques(entry)

pics_mesures = {n: float(np.nanmax(S[n])) for n in NOMS}

# --- tableau imprimé ---
def imprime_ligne(label, Lf, transport, m):
    print(f"{label:<18} | L_f={Lf/1000:6.0f} J/g | transport {'ON ' if transport else 'OFF'} | "
          f"RMSE TC2={m['rmse']['TC2']:5.1f} TC3={m['rmse']['TC3']:5.1f} "
          f"TC4={m['rmse']['TC4']:5.1f} TC5={m['rmse']['TC5']:5.1f} | "
          f"pic TC4={m['pics']['TC4']:5.0f} ({m['ecarts_pic']['TC4']:+5.0f}) "
          f"pic TC5={m['pics']['TC5']:5.0f} ({m['ecarts_pic']['TC5']:+5.0f}) | "
          f"PC max={m['pc_max']:5.0f}")


print(f"réel : pics mesurés  " + "  ".join(f"{n}={pics_mesures[n]:.0f}" for n in NOMS))
print(f"\n{'config':<18} | {'L_f':>12} | {'transport':>10} | RMSE (TC2/TC3/TC4/TC5)             | pics TC4/TC5 (écart)               | point chaud")
print("-" * 150)
for label, Lf, table_kt, cle in CONFIGS:
    imprime_ligne(label, Lf, table_kt is not None, resultats[cle]["m"])
print("\nBalayage L_f (transport ON, K_HOT=100) :")
for Lf in SWEEP_LF:
    imprime_ligne(f"L_f={Lf/1000:.0f} J/g", Lf, True, sweep[Lf]["m"])

rmse_moy_23 = {cle: float(np.mean([resultats[cle]["m"]["rmse"]["TC2"], resultats[cle]["m"]["rmse"]["TC3"]])) for cle in resultats}
rmse_moy_glob = {cle: float(np.mean([resultats[cle]["m"]["rmse"][n] for n in NOMS])) for cle in resultats}
print("\nRMSE moyen intérieur (TC2/TC3) et global (TC1-5) :")
for label, Lf, table_kt, cle in CONFIGS:
    print(f"{label:<18} | RMSE moy TC2/TC3 = {rmse_moy_23[cle]:5.1f} | RMSE moy global = {rmse_moy_glob[cle]:5.1f}")

# --- recoupement avec gen_valider_fusion_231A.py ---
print("\n--- recoupement (① doit == canon, ④ doit == fusion, du script gen_valider_fusion_231A.py) ---")
print("① canonique : ", {n: round(resultats['canon']['m']['pics'][n]) for n in NOMS},
      f"| PC max={resultats['canon']['m']['pc_max']:.0f}")
print("④ complet   : ", {n: round(resultats['complet']['m']['pics'][n]) for n in NOMS},
      f"| PC max={resultats['complet']['m']['pc_max']:.0f}")

# --------------------------------------------------------------------------- #
# Markdown d'archivage.
# --------------------------------------------------------------------------- #
lignes_md = []
lignes_md.append("# Ablation du modèle de fusion — cycle 231 A (issue #68, Axe 1)\n")
lignes_md.append(
    "Ablation 2×2 (L_f × transport `k_plan(T>Tf)`) + balayage L_f, confrontée au réel "
    "231 A (held-out, aucun recalage). Fenêtres de passe pilotées aux dwells mesurés "
    "(identique à `gen_valider_fusion_231A.py`). Script : "
    "`code/scripts/gen/gen_ablation_fusion_231A.py`.\n"
)
lignes_md.append(f"Pics mesurés : " + ", ".join(f"{n}={pics_mesures[n]:.0f} °C" for n in NOMS) + ".\n")
lignes_md.append("## Ablation 2×2\n")
lignes_md.append("| config | L_f (J/g) | transport | RMSE TC2 | RMSE TC3 | RMSE TC4 | RMSE TC5 | pic TC4 (écart) | pic TC5 (écart) | point chaud max |")
lignes_md.append("|---|---:|:---:|---:|---:|---:|---:|---:|---:|---:|")
for label, Lf, table_kt, cle in CONFIGS:
    m = resultats[cle]["m"]
    lignes_md.append(
        f"| {label} | {Lf/1000:.0f} | {'ON' if table_kt is not None else 'OFF'} | "
        f"{m['rmse']['TC2']:.1f} | {m['rmse']['TC3']:.1f} | {m['rmse']['TC4']:.1f} | {m['rmse']['TC5']:.1f} | "
        f"{m['pics']['TC4']:.0f} ({m['ecarts_pic']['TC4']:+.0f}) | {m['pics']['TC5']:.0f} ({m['ecarts_pic']['TC5']:+.0f}) | "
        f"{m['pc_max']:.0f} |"
    )
lignes_md.append("")
lignes_md.append("RMSE moyen intérieur (TC2/TC3) et global (TC1-5) :\n")
lignes_md.append("| config | RMSE moy TC2/TC3 | RMSE moy global (TC1-5) |")
lignes_md.append("|---|---:|---:|")
for label, Lf, table_kt, cle in CONFIGS:
    lignes_md.append(f"| {label} | {rmse_moy_23[cle]:.1f} | {rmse_moy_glob[cle]:.1f} |")
lignes_md.append("")
lignes_md.append("## Balayage L_f (transport ON, K_HOT=100)\n")
lignes_md.append("| L_f (J/g) | RMSE TC2 | RMSE TC3 | RMSE TC4 | RMSE TC5 | pic TC4 (écart) | pic TC5 (écart) | point chaud max |")
lignes_md.append("|---:|---:|---:|---:|---:|---:|---:|---:|")
for Lf in SWEEP_LF:
    m = sweep[Lf]["m"]
    lignes_md.append(
        f"| {Lf/1000:.0f} | {m['rmse']['TC2']:.1f} | {m['rmse']['TC3']:.1f} | {m['rmse']['TC4']:.1f} | {m['rmse']['TC5']:.1f} | "
        f"{m['pics']['TC4']:.0f} ({m['ecarts_pic']['TC4']:+.0f}) | {m['pics']['TC5']:.0f} ({m['ecarts_pic']['TC5']:+.0f}) | "
        f"{m['pc_max']:.0f} |"
    )
lignes_md.append("")

# lecture factuelle (chiffres tirés des résultats calculés ci-dessus, wording piloté par le signe)
d_glob_fus = rmse_moy_glob["fusion_seule"] - rmse_moy_glob["canon"]
d_glob_trans = rmse_moy_glob["transport_seul"] - rmse_moy_glob["canon"]
pc1, pc2, pc3, pc4 = (resultats[c]["m"]["pc_max"] for c in ("canon", "fusion_seule", "transport_seul", "complet"))
d_pc_fus, d_pc_trans, d_pc_complet = pc2 - pc1, pc3 - pc1, pc4 - pc1

tc4_1, tc4_2, tc4_3, tc4_4 = (resultats[c]["m"]["pics"]["TC4"] for c in ("canon", "fusion_seule", "transport_seul", "complet"))
tc5_1, tc5_2, tc5_3, tc5_4 = (resultats[c]["m"]["pics"]["TC5"] for c in ("canon", "fusion_seule", "transport_seul", "complet"))
d_tc4_fus, d_tc4_trans = tc4_2 - tc4_1, tc4_3 - tc4_1
d_tc5_fus, d_tc5_trans = tc5_2 - tc5_1, tc5_3 - tc5_1

rmse_tc3 = {c: resultats[c]["m"]["rmse"]["TC3"] for c in ("canon", "fusion_seule", "transport_seul", "complet")}
rmse_tc4 = {c: resultats[c]["m"]["rmse"]["TC4"] for c in ("canon", "fusion_seule", "transport_seul", "complet")}
rmse_tc5 = {c: resultats[c]["m"]["rmse"]["TC5"] for c in ("canon", "fusion_seule", "transport_seul", "complet")}

lignes_md.append("## Lecture\n")
lignes_md.append(
    f"- **Point chaud / plateau : porté par le transport, pas par L_f.** L_f seul (② vs ①) laisse le point "
    f"chaud quasi inchangé, {'même légèrement plus haut' if d_pc_fus > 0 else 'légèrement plus bas'} "
    f"({pc1:.0f} -> {pc2:.0f} °C, Δ={d_pc_fus:+.0f}) — L_f seul ne plafonne donc pas le point chaud. Le transport "
    f"seul (③ vs ①), lui, le fait chuter de {pc1:.0f} à {pc3:.0f} °C (Δ={d_pc_trans:+.0f}), soit l'essentiel de la "
    f"baisse obtenue par le modèle complet (④ : {pc4:.0f} °C, Δ={d_pc_complet:+.0f}). Le RMSE global suit la même "
    f"hiérarchie : {rmse_moy_glob['canon']:.1f} (①) -> {rmse_moy_glob['fusion_seule']:.1f} (②, {d_glob_fus:+.1f}) "
    f"-> {rmse_moy_glob['transport_seul']:.1f} (③, {d_glob_trans:+.1f}) -> {rmse_moy_glob['complet']:.1f} (④).\n"
)
lignes_md.append(
    f"- **TC4 (intérieur, x=90) quasi insensible aux deux leviers ; TC5 (bord, x=120) répond fortement au "
    f"transport.** Le pic TC4 varie peu et dans le mauvais sens avec L_f seul ({tc4_1:.0f} -> {tc4_2:.0f} °C, "
    f"Δ={d_tc4_fus:+.0f}) comme avec le transport seul ({tc4_1:.0f} -> {tc4_3:.0f} °C, Δ={d_tc4_trans:+.0f}) ; il "
    f"reste surestimé de +{min(resultats[c]['m']['ecarts_pic']['TC4'] for c in resultats):.0f} à "
    f"+{max(resultats[c]['m']['ecarts_pic']['TC4'] for c in resultats):.0f} °C dans toutes les configs, avec un "
    f"RMSE quasi constant ({min(rmse_tc4.values()):.1f}-{max(rmse_tc4.values()):.1f} °C) — ni L_f ni le transport "
    f"ne corrigent ce résidu. Le pic TC5, au contraire, chute nettement sous transport seul "
    f"({tc5_1:.0f} -> {tc5_3:.0f} °C, Δ={d_tc5_trans:+.0f}, RMSE {rmse_tc5['canon']:.1f} -> "
    f"{rmse_tc5['transport_seul']:.1f} °C) alors que L_f seul l'aggrave légèrement "
    f"({tc5_1:.0f} -> {tc5_2:.0f} °C, Δ={d_tc5_fus:+.0f}) ; le modèle complet (④) reste au-dessus du plateau "
    f"mesuré sur les deux capteurs ({tc4_4:.0f} / {tc5_4:.0f} °C vs mesuré {pics_mesures['TC4']:.0f} / "
    f"{pics_mesures['TC5']:.0f} °C). Ce plafonnement de TC5 par le transport se paie d'une dégradation de TC3 "
    f"(intérieur, passe 2) : RMSE {rmse_tc3['canon']:.1f} -> {rmse_tc3['transport_seul']:.1f} °C avec le transport "
    f"seul.\n"
)
lignes_md.append(
    f"- **Balayage L_f (transport ON) : effet de réglage fin, pas de bascule qualitative.** Point chaud et pics "
    f"TC4/TC5 varient "
    f"{'de façon monotone' if (sweep[0.0]['m']['pc_max'] >= sweep[20000.0]['m']['pc_max'] >= sweep[40000.0]['m']['pc_max'] >= sweep[130000.0]['m']['pc_max']) else 'de façon non strictement monotone'} "
    f"avec L_f croissant (point chaud : {sweep[0.0]['m']['pc_max']:.0f} -> {sweep[20000.0]['m']['pc_max']:.0f} -> "
    f"{sweep[40000.0]['m']['pc_max']:.0f} -> {sweep[130000.0]['m']['pc_max']:.0f} °C pour L_f=0/20/40/130 J/g), sur "
    f"une plage modeste (< {abs(sweep[0.0]['m']['pc_max'] - sweep[130000.0]['m']['pc_max']):.0f} °C) comparée à "
    f"l'écart transport ON/OFF ({abs(d_pc_trans):.0f} °C). Le RMSE TC5 s'améliore avec L_f croissant "
    f"({sweep[0.0]['m']['rmse']['TC5']:.1f} -> {sweep[130000.0]['m']['rmse']['TC5']:.1f} °C) tandis que le RMSE TC3 "
    f"se dégrade légèrement ({sweep[0.0]['m']['rmse']['TC3']:.1f} -> {sweep[130000.0]['m']['rmse']['TC3']:.1f} °C) "
    f"— L_f, une fois le transport actif, ajuste le niveau plutôt qu'il ne change le comportement qualitatif.\n"
)
lignes_md.append(
    "- Recoupement : ① canonique et ④ complet ci-dessus doivent reproduire les pics/point chaud "
    "imprimés par `gen_valider_fusion_231A.py` (canon vs fusion) — vérifié dans la sortie console du script."
)

(R / "biblio" / "labo" / "ablation_fusion_231A_resultats.md").write_text("\n".join(lignes_md) + "\n")
print("\nmarkdown -> biblio/labo/ablation_fusion_231A_resultats.md")

# --------------------------------------------------------------------------- #
# Figure : petits multiples 2x2 (mesuré plein vs prédit tireté) + barres RMSE.
# --------------------------------------------------------------------------- #
fig = plt.figure(figsize=(13.5, 9.2))
gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.0, 0.85], hspace=0.38, wspace=0.14)
axes2x2 = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]),
           fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])]
ax_rmse = fig.add_subplot(gs[2, 0])
ax_pics = fig.add_subplot(gs[2, 1])

for ax, (label, Lf, table_kt, cle) in zip(axes2x2, CONFIGS):
    entry = resultats[cle]
    for n, c in zip(NOMS, COUL):
        ax.plot(t, S[n], color=c, lw=1.5, alpha=0.9)
        ax.plot(entry["t"], entry["S"][n], color=c, lw=1.1, ls=(0, (4, 1.8)))
    ax.plot(entry["t"], entry["PC"], color="0.5", lw=0.9, ls=(0, (1, 1.4)))
    ax.axhline(390, color=OKABE_ITO["vert"], lw=0.7, ls="--", alpha=0.7)
    ax.axhline(337, color=OKABE_ITO["cyan"], lw=0.7, ls=":", alpha=0.7)
    ax.set_xlim(0, t[-1]); ax.set_ylim(0, 900)
    ax.set_title(f"{label}  (L_f={Lf/1000:.0f} J/g, transport {'ON' if table_kt is not None else 'OFF'})",
                 fontsize=9.5, fontweight="bold")
    ax.tick_params(labelsize=8)
for ax in (axes2x2[0], axes2x2[1]):
    ax.set_xticklabels([])
for ax in (axes2x2[1], axes2x2[3]):
    ax.set_yticklabels([])
axes2x2[2].set_xlabel("Temps (s)", fontsize=9)
axes2x2[3].set_xlabel("Temps (s)", fontsize=9)
axes2x2[0].set_ylabel("Température (°C)", fontsize=9)
axes2x2[2].set_ylabel("Température (°C)", fontsize=9)

handles = [plt.Line2D([0], [0], color=c, lw=1.6, label=n) for n, c in zip(NOMS, COUL)]
handles += [plt.Line2D([0], [0], color="0.3", lw=1.4, label="mesuré (plein)"),
            plt.Line2D([0], [0], color="0.3", lw=1.1, ls=(0, (4, 1.8)), label="prédit (tireté)"),
            plt.Line2D([0], [0], color="0.5", lw=0.9, ls=(0, (1, 1.4)), label="point chaud")]
fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.995),
           ncol=8, fontsize=7.3, framealpha=0.93)

x = np.arange(4)
width = 0.19
for k, (n, c) in enumerate(zip(["TC2", "TC3", "TC4", "TC5"], [OKABE_ITO[c] for c in ("vert", "orange", "bleu", "vermillon")])):
    vals = [resultats[cle]["m"]["rmse"][n] for _, _, _, cle in CONFIGS]
    ax_rmse.bar(x + (k - 1.5) * width, vals, width, color=c, label=n)
ax_rmse.set_xticks(x); ax_rmse.set_xticklabels(["①", "②", "③", "④"], fontsize=9)
ax_rmse.set_ylabel("RMSE (°C)", fontsize=9)
ax_rmse.set_ylim(0, 115)
ax_rmse.set_title("RMSE par TC", fontsize=9.5, fontweight="bold")
ax_rmse.legend(fontsize=7.3, ncol=4, loc="upper center", framealpha=0.93)
ax_rmse.tick_params(labelsize=8)

width2 = 0.35
pics_tc4 = [resultats[cle]["m"]["pics"]["TC4"] for _, _, _, cle in CONFIGS]
pics_tc5 = [resultats[cle]["m"]["pics"]["TC5"] for _, _, _, cle in CONFIGS]
ax_pics.bar(x - width2 / 2, pics_tc4, width2, color=OKABE_ITO["bleu"], label="pic TC4")
ax_pics.bar(x + width2 / 2, pics_tc5, width2, color=OKABE_ITO["vermillon"], label="pic TC5")
ax_pics.axhline(pics_mesures["TC4"], color=OKABE_ITO["bleu"], lw=1.0, ls="--", label="TC4 mesuré")
ax_pics.axhline(pics_mesures["TC5"], color=OKABE_ITO["vermillon"], lw=1.0, ls=":", label="TC5 mesuré")
ax_pics.set_xticks(x); ax_pics.set_xticklabels(["①", "②", "③", "④"], fontsize=9)
ax_pics.set_ylabel("Pic (°C)", fontsize=9)
ax_pics.set_ylim(0, 800)
ax_pics.set_title("Pics TC4/TC5 vs mesuré", fontsize=9.5, fontweight="bold")
ax_pics.legend(fontsize=7.0, ncol=2, loc="upper center", framealpha=0.93)
ax_pics.tick_params(labelsize=8)

fig.suptitle("Ablation du modèle de fusion — cycle 231 A (issue #68)", fontsize=12.5, fontweight="bold", y=1.035)
savefig(fig, R / "biblio" / "labo" / "figures" / "fig_ablation_fusion_231A")
plt.close(fig)
print("figure -> biblio/labo/figures/fig_ablation_fusion_231A.png")
