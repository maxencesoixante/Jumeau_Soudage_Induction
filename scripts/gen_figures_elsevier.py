"""Regenerate the figures_elsevier set in the *reference* format of
serieA_A-2_250A_2026-06-09.png:
  - descriptive title on top
  - bold axis labels
  - legend OUTSIDE the data axes (no text over curves)
  - horizontal temperature reference lines (fusion / procédé / dégradation)
    on the absolute-temperature figures, labelled in whitespace.

Output dir via env FIGOUT (default docs/figures_elsevier).
"""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from scipy.signal import medfilt

R = Path("/Users/maxencedubois/PycharmProjects/Jumeau_Soudage_Induction")
sys.path.insert(0, str(R / "src"))
OUT = Path(os.environ.get("FIGOUT", str(R / "docs" / "figures_elsevier")))
OUT.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# rcParams — reference style (serieA_A-2_250A_2026-06-09.png)
# ----------------------------------------------------------------------
mpl.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "mathtext.fontset": "dejavusans",
    "font.size": 10, "axes.labelsize": 11, "axes.labelweight": "bold",
    "axes.titlesize": 11, "legend.fontsize": 9,
    "xtick.labelsize": 9.5, "ytick.labelsize": 9.5,
    "axes.linewidth": 0.8,
    "lines.linewidth": 1.4, "lines.markersize": 4.5, "legend.frameon": False,
    "figure.dpi": 600, "savefig.dpi": 600, "savefig.bbox": "tight", "savefig.pad_inches": 0.05,
})

# ----------------------------------------------------------------------
# Presets: "elsevier" (default) or "presentation" (slides — bigger fonts,
# only fig1..fig5, remapped to the presentation filenames).
# ----------------------------------------------------------------------
PRESET = os.environ.get("PRESET", "elsevier")
PRES_NAMES = {
    "fig1_profil_M.png": "fig1_profil_M_3courants.png",
    "fig2_mesure_modele.png": "fig2_mesure_vs_modele.png",
    "fig3_dynamique_centre.png": "fig3_centre_dynamique.png",
    "fig4_courbes_brutes.png": "fig4_courbes_brutes.png",
    "fig5_loi_courant.png": "fig5_loi_courant.png",
}
if PRESET == "presentation":
    mpl.rcParams.update({
        "font.size": 13, "axes.labelsize": 14, "axes.titlesize": 14,
        "legend.fontsize": 12, "xtick.labelsize": 12, "ytick.labelsize": 12,
        "lines.linewidth": 1.8, "lines.markersize": 6,
    })
    # Bigger fonts need a bigger canvas — scale every figsize so the (long,
    # rotated) axis labels are not clipped.
    _orig_subplots = plt.subplots

    def _scaled_subplots(*a, **k):
        fs = k.get("figsize")
        if fs:
            k["figsize"] = (fs[0] * 1.15, fs[1] * 1.4)
        return _orig_subplots(*a, **k)

    plt.subplots = _scaled_subplots

# Okabe-Ito palette (imposed)
C150 = "#0072B2"
C200 = "#E69F00"
C250 = "#009E73"
C_MODEL = "#555555"
COURANT_COLOR = {150: C150, 176: "#56B4E9", 200: C200, 225: "#D55E00", 250: C250}
# Palette dédiée aux 4 courants de la campagne dissipation exp9 (monospot)
DISSIP_COLOR = {175: "#56B4E9", 200: "#E69F00", 226: "#D55E00", 250: "#009E73"}
DISSIP_FILES = {
    175: "175A/175A_y0_monospot.txt",
    200: "200A/200A_y0_monospot.txt",
    226: "226A/226A_y0_monospot.txt",
    250: "250A/250a_y0_monospot.txt",   # nom de fichier en minuscule
}

# Reference temperature lines (PEKK) — same convention as the reference figure
T_FUSION = 337.0      # °C — fusion PEKK (config/materiaux.yaml)
T_PROCEDE = 390.0     # °C — cible procédé
T_DEGRAD = 450.0      # °C — dégradation
COL_FUSION = "#0072B2"
COL_PROCEDE = "#E69F00"
COL_DEGRAD = "#C1272D"

DATA7 = R / "data" / "exp7_bord-centre_2026-07-28_avec-ceramique"
DATA9 = R / "data" / "exp9_dissipation-longitudinale_2026-07-28"
Y_MM = np.array([0, 10, 20, 30, 40])

ESSAIS_VALIDES = {
    150: ["150A_v1.txt", "150A_v2.txt", "150A_v3.txt"],
    176: ["176A_v1.txt"],
    200: ["200A_v4_TC1ok.txt", "200A_v5.txt", "200A_v6.txt"],
    225: ["225A_v1.txt"],
    250: ["250A_v1.txt", "250A_v2.txt", "250A_v3.txt"],
}


def savefig(fig, name):
    if PRESET == "presentation":
        if name not in PRES_NAMES:
            plt.close(fig)
            return
        name = PRES_NAMES[name]
    fig.savefig(OUT / name)
    plt.close(fig)
    print("saved", OUT / name)


def legend_right(ax, **kw):
    """Legend outside the axes, centred on the right (reference format)."""
    return ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False, **kw)


def add_temp_lines(ax, lines=("fusion", "procede", "degrad"), x_label=0.015):
    """Horizontal reference-temperature lines, labelled in whitespace at the left."""
    conf = {
        "fusion": (T_FUSION, COL_FUSION, "-", "Fusion PEKK (337 °C)"),
        "procede": (T_PROCEDE, COL_PROCEDE, "--", "Cible procédé (390 °C)"),
        "degrad": (T_DEGRAD, COL_DEGRAD, "-", "Dégradation (450 °C)"),
    }
    for key in lines:
        T, col, ls, txt = conf[key]
        ax.axhline(T, color=col, ls=ls, lw=1.1, zorder=0)
        ax.text(x_label, T, txt, transform=ax.get_yaxis_transform(),
                va="bottom", ha="left", fontsize=8, color=col, fontweight="normal")


def panel_title(ax, label):
    ax.set_title(label, loc="left", fontweight="bold", fontsize=10.5, pad=3)


def load_txt(path):
    df = pd.read_csv(path, sep="\t", decimal=",")
    df.columns = [c.strip() for c in df.columns]
    return df


def clean(df):
    tc_cols_raw = [c for c in df.columns if c.startswith("TC")]
    amb = df[tc_cols_raw].iloc[:2].to_numpy().mean()
    df = df.copy()
    rename = {c: c.split(" ")[0] for c in tc_cols_raw}
    df = df.rename(columns=rename)
    tc_cols = [rename[c] for c in tc_cols_raw]
    for c in tc_cols:
        s = df[c].where((df[c] <= 320) & (df[c] >= amb - 6))
        s = s.interpolate(limit_direction="both")
        df[c] = medfilt(s.to_numpy(), 5)
    t = df["Time (s)"].to_numpy()
    df["t"] = t - t[0]
    return df, amb, tc_cols


def heating_onset_idx(df, tc_cols, amb, delta=2.0):
    combined = df[tc_cols].max(axis=1).to_numpy()
    above = np.where(combined > amb + delta)[0]
    if len(above) == 0:
        return 0
    return max(above[0] - 1, 0)


# ========================================================================
# FIG 1 — profil M
# ========================================================================
def fig1():
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    colors = {150: C150, 200: C200, 250: C250}
    for I in (150, 200, 250):
        peaks = []
        for fname in ESSAIS_VALIDES[I]:
            dfc, amb, tc_cols = clean(load_txt(DATA7 / f"{I}A" / fname))
            peaks.append(dfc[tc_cols].max().to_numpy() - amb)
        peaks = np.array(peaks)
        ax.plot(Y_MM, peaks.mean(axis=0), "-o", color=colors[I], label=f"{I} A",
                markeredgecolor="white", markeredgewidth=0.5)
        ax.fill_between(Y_MM, peaks.min(axis=0), peaks.max(axis=0),
                        color=colors[I], alpha=0.15, lw=0)
    ax.set_xticks(Y_MM)
    ax.set_title("Profil de température en largeur au pic — 150 / 200 / 250 A")
    ax.set_xlabel("Position en largeur $y$ (mm)")
    ax.set_ylabel(r"Élévation au pic $\Delta T$ (°C)")
    legend_right(ax, title="Courant")
    savefig(fig, "fig1_profil_M.png")


# ========================================================================
# FIG 2 — forme normalisée
# ========================================================================
def fig2():
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    mesure = np.array([2.18, 1.65, 1.00, 1.31, 2.09])
    modele = np.array([2.43, 1.38, 1.00, 1.38, 2.43])
    ax.plot(Y_MM, mesure, "-o", color=C200, markeredgecolor="white", markeredgewidth=0.5,
            label="Mesuré (contraste 2,18)")
    ax.plot(Y_MM, modele, "--s", color=C_MODEL, markeredgecolor="white", markeredgewidth=0.5,
            label="Modèle (contraste 2,43)")
    ax.set_xticks(Y_MM)
    ax.set_title("Forme du profil en largeur : mesuré vs modèle (200 A)")
    ax.set_xlabel("Position en largeur $y$ (mm)")
    ax.set_ylabel("Température normalisée (–)")
    legend_right(ax)
    savefig(fig, "fig2_mesure_modele.png")


# ========================================================================
# FIG 3 — dynamique centre vs chant (solveur 2D)
# ========================================================================
def fig3():
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    first = True
    for fname in ["200A_v4_TC1ok.txt", "200A_v5.txt", "200A_v6.txt"]:
        dfc, amb, tc_cols = clean(load_txt(DATA7 / "200A" / fname))
        chant = np.maximum(dfc["TC1"], dfc["TC5"]).to_numpy() - amb
        centre = dfc["TC3"].to_numpy() - amb
        i = int(np.argmax(chant))
        ax.plot(chant[:i + 1], centre[:i + 1], "-", color=C200, alpha=0.6, lw=1.1,
                label="Mesuré (200 A, 3 essais)" if first else None)
        first = False

    from jumeau.materiaux import Config
    from jumeau.procede import Essai
    from jumeau.em.source_joule import source_spot

    cfg = Config.charger(R / "config")
    cfg.contact.h_haut = 30.087
    cfg.ambiant.h_bas_2d = 37.424
    cfg.ambiant.h_bord_x0 = 250.0
    e = Essai(cfg, R / "config/essais/chauffe_250A_3TC.yaml", nx=61, ny=21, nz=15,
              facteur_couplage=6.0123, decalage_x=0.0, racine=R)
    e._Q_spots = [source_spot(e.grille, cfg, e.couches, 200.0, float(s["centre_x"]),
                  facteur_couplage=6.0123, decalage_x=0.0) for s in e.spots]
    e._P_spots_2d = [Q.sum(axis=2) * e.grille.dz for Q in e._Q_spots]
    sv, sol = e.simuler(modele="2D")
    amb_m = 23.9
    cM = sv.serie_temporelle(sol, 0.060, 0.020, "interface") - amb_m
    eM = np.maximum(sv.serie_temporelle(sol, 0.060, 0.0, "interface"),
                     sv.serie_temporelle(sol, 0.060, 0.040, "interface")) - amb_m
    i = int(np.argmax(eM))
    ax.plot(eM[:i + 1], cM[:i + 1], "--", color=C_MODEL, lw=1.4, label="Modèle (2D, 200 A)")

    ax.set_title("Dynamique centre–chant : mesuré vs modèle (200 A)")
    ax.set_xlabel(r"Température des chants $\Delta T$ (°C)")
    ax.set_ylabel(r"Température du centre $\Delta T$ (°C)")
    ax.set_xlim(0, 235)
    ax.set_ylim(0, 110)
    legend_right(ax)
    savefig(fig, "fig3_dynamique_centre.png")


# ========================================================================
# FIG 4 — 5 TC bruts (200A_v6)
# ========================================================================
def fig4():
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    dfc, amb, tc_cols = clean(load_txt(DATA7 / "200A" / "200A_v6.txt"))
    onset = heating_onset_idx(dfc, tc_cols, amb)
    t = dfc["t"].to_numpy() - dfc["t"].to_numpy()[onset]
    mask = (t >= 0) & (t <= 72)
    ts = t[mask]
    ax.plot(ts, dfc["TC1"].to_numpy()[mask], "-", color=C150, label="Chants (TC1/TC5)")
    ax.plot(ts, dfc["TC5"].to_numpy()[mask], "--", color=C150)
    ax.plot(ts, dfc["TC2"].to_numpy()[mask], "-", color=C200, label="Intermédiaires (TC2/TC4)")
    ax.plot(ts, dfc["TC4"].to_numpy()[mask], "--", color=C200)
    ax.plot(ts, dfc["TC3"].to_numpy()[mask], "-", color=C250, label="Centre (TC3)")
    add_temp_lines(ax)
    ax.set_xlim(0, 72)
    ax.set_ylim(0, 470)
    ax.set_title("Historiques des 5 thermocouples — un essai (200 A)")
    ax.set_xlabel("Temps (s)")
    ax.set_ylabel("Température (°C)")
    legend_right(ax)
    savefig(fig, "fig4_courbes_brutes.png")


# ========================================================================
# FIG 5 — loi taux de chauffe vs courant
# ========================================================================
def fig5():
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    GRP = {150: ("150A", ["150A_v1.txt", "150A_v2.txt", "150A_v3.txt"]),
           176: ("176A", ["176A_v1.txt"]),
           200: ("200A", ["200A_v4_TC1ok.txt", "200A_v5.txt", "200A_v6.txt"]),
           225: ("226A", ["225A_v1.txt"]),
           250: ("250A", ["250A_v1.txt", "250A_v2.txt", "250A_v3.txt"])}

    def _rate(sub, fname):
        dfc, amb, _ = clean(load_txt(DATA7 / sub / fname))
        ch = np.maximum(dfc["TC1"], dfc["TC5"]).to_numpy() - amb
        t = dfc["t"].to_numpy()
        ip = int(np.argmax(ch)); ch, t = ch[:ip + 1], t[:ip + 1]
        m = (ch >= 30) & (ch <= 130)
        return np.polyfit(t[m], ch[m], 1)[0]

    I, Rt, LO, HI = [], [], [], []
    for cur, (sub, fs) in GRP.items():
        rs = np.array([_rate(sub, f) for f in fs])
        I.append(cur); Rt.append(rs.mean()); LO.append(rs.min()); HI.append(rs.max())
    I = np.array(I, float); Rt = np.array(Rt)

    coeffs = np.polyfit(I**2, Rt, 1)
    k, negL = coeffs; L = -negL
    Rt_fit = np.polyval(coeffs, I**2)
    r2 = 1 - np.sum((Rt - Rt_fit)**2) / np.sum((Rt - Rt.mean())**2)

    yerr = np.vstack([Rt - np.array(LO), np.array(HI) - Rt])
    ax.errorbar(I, Rt, yerr=yerr, fmt="o", color=C150, ecolor=C150, elinewidth=1.0,
                capsize=3, markeredgecolor="white", markeredgewidth=0.5,
                label="Mesuré (min–max)", zorder=3)
    for Ival, Rv in zip(I, Rt):
        ax.annotate(f"{int(Ival)} A", (Ival, Rv), textcoords="offset points",
                    xytext=(7, -11), fontsize=8, color="0.35")
    Ifit = np.linspace(140, 260, 200)
    ax.plot(Ifit, k * Ifit**2 - L, "-", color=C200,
            label=f"Source $\\propto I^2$ − pertes ($R^2$={r2:.3f})".replace(".", ","))
    ax.plot(Ifit, k * Ifit**2, ":", color="0.6", label="$k\\,I^2$ pur")
    ax.set_title("Loi taux de chauffe – courant (5 courants)")
    ax.set_xlabel("Courant du générateur $I$ (A)")
    ax.set_ylabel(r"Taux de chauffe au chant $dT/dt$ (°C/s)")
    legend_right(ax)
    savefig(fig, "fig5_loi_courant.png")


# ========================================================================
# fig_essais_chant_superpose
# ========================================================================
def fig_essais_chant_superpose():
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    currents = [150, 176, 200, 225, 250]
    ramp = plt.cm.viridis(np.linspace(0.72, 0.06, 5))
    color_map = dict(zip(currents, ramp))
    for I in currents:
        first = True
        for fname in ESSAIS_VALIDES[I]:
            dfc, amb, tc_cols = clean(load_txt(DATA7 / f"{I}A" / fname))
            onset = heating_onset_idx(dfc, tc_cols, amb)
            t = dfc["t"].to_numpy() - dfc["t"].to_numpy()[onset]
            chant = np.maximum(dfc["TC1"], dfc["TC5"]).to_numpy()
            mask = (t >= 0) & (t <= 72)
            ax.plot(t[mask], chant[mask], "-", color=color_map[I], lw=1.2,
                    label=f"{I} A" if first else None)
            first = False
    add_temp_lines(ax)
    ax.set_xlim(0, 72)
    ax.set_ylim(0, 470)
    ax.set_title("Historiques T(t) au chant — tous essais, 5 courants")
    ax.set_xlabel("Temps depuis le début de chauffe (s)")
    ax.set_ylabel("Température au chant (°C)")
    legend_right(ax, title="Courant")
    savefig(fig, "fig_essais_chant_superpose.png")


# ========================================================================
# fig_essais_par_courant — small multiples 2x3
# ========================================================================
def fig_essais_par_courant():
    fig, axes = plt.subplots(2, 3, figsize=(8.4, 5.0), sharex=True, sharey=True)
    currents = [150, 176, 200, 225, 250]
    labels = "abcde"
    axes_flat = axes.flatten()
    for ax, I, lab in zip(axes_flat, currents, labels):
        for fname in ESSAIS_VALIDES[I]:
            dfc, amb, tc_cols = clean(load_txt(DATA7 / f"{I}A" / fname))
            onset = heating_onset_idx(dfc, tc_cols, amb)
            t = dfc["t"].to_numpy() - dfc["t"].to_numpy()[onset]
            chant = np.maximum(dfc["TC1"], dfc["TC5"]).to_numpy()
            mask = (t >= 0) & (t <= 72)
            ax.plot(t[mask], chant[mask], "-", color=COURANT_COLOR[I], lw=1.2)
        ax.axhline(T_FUSION, color=COL_FUSION, ls="-", lw=0.9, zorder=0)
        panel_title(ax, f"({lab}) {I} A")
    axes_flat[5].axis("off")
    axes_flat[5].plot([], [], "-", color="0.4", label="Essais (chant)")
    axes_flat[5].plot([], [], "-", color=COL_FUSION, label="Fusion PEKK (337 °C)")
    axes_flat[5].legend(loc="center", frameon=False, fontsize=10)
    axes_flat[0].set_xlim(0, 72)
    axes_flat[0].set_ylim(0, 360)
    fig.suptitle("Répétabilité au chant par courant", fontsize=12, fontweight="bold", y=0.98)
    fig.supxlabel("Temps depuis le début de chauffe (s)", fontsize=11, fontweight="bold")
    fig.supylabel("Température au chant (°C)", fontsize=11, fontweight="bold")
    fig.tight_layout(rect=(0.02, 0.02, 1, 0.96))
    savefig(fig, "fig_essais_par_courant.png")


# ========================================================================
# fig_essais_5TC_par_courant — small multiples 2x3
# ========================================================================
def fig_essais_5TC_par_courant():
    fig, axes = plt.subplots(2, 3, figsize=(8.4, 5.0), sharex=True, sharey=True)
    reps = {150: "150A_v3.txt", 176: "176A_v1.txt", 200: "200A_v6.txt",
            225: "225A_v1.txt", 250: "250A_v3.txt"}
    currents = [150, 176, 200, 225, 250]
    labels = "abcde"
    axes_flat = axes.flatten()
    for ax, I, lab in zip(axes_flat, currents, labels):
        dfc, amb, tc_cols = clean(load_txt(DATA7 / f"{I}A" / reps[I]))
        onset = heating_onset_idx(dfc, tc_cols, amb)
        t = dfc["t"].to_numpy() - dfc["t"].to_numpy()[onset]
        mask = (t >= 0) & (t <= 72)
        ts = t[mask]
        ax.plot(ts, dfc["TC1"].to_numpy()[mask], "-", color=C150)
        ax.plot(ts, dfc["TC5"].to_numpy()[mask], "--", color=C150)
        ax.plot(ts, dfc["TC2"].to_numpy()[mask], "-", color=C200)
        ax.plot(ts, dfc["TC4"].to_numpy()[mask], "--", color=C200)
        ax.plot(ts, dfc["TC3"].to_numpy()[mask], "-", color=C250)
        ax.axhline(T_FUSION, color=COL_FUSION, ls="-", lw=0.9, zorder=0)
        panel_title(ax, f"({lab}) {I} A")
    axes_flat[0].set_xlim(0, 72)
    axes_flat[0].set_ylim(0, 360)

    ax_leg = axes_flat[5]
    ax_leg.axis("off")
    handles = [
        plt.Line2D([], [], color=C150, ls="-", label="TC1 ($y$=0 mm)"),
        plt.Line2D([], [], color=C150, ls="--", label="TC5 ($y$=40 mm)"),
        plt.Line2D([], [], color=C200, ls="-", label="TC2 ($y$=10 mm)"),
        plt.Line2D([], [], color=C200, ls="--", label="TC4 ($y$=30 mm)"),
        plt.Line2D([], [], color=C250, ls="-", label="TC3 ($y$=20 mm, centre)"),
        plt.Line2D([], [], color=COL_FUSION, ls="-", label="Fusion PEKK (337 °C)"),
    ]
    ax_leg.legend(handles=handles, loc="center", frameon=False, fontsize=9.5)
    fig.suptitle("Les 5 thermocouples par courant", fontsize=12, fontweight="bold", y=0.98)
    fig.supxlabel("Temps depuis le début de chauffe (s)", fontsize=11, fontweight="bold")
    fig.supylabel("Température (°C)", fontsize=11, fontweight="bold")
    fig.tight_layout(rect=(0.02, 0.02, 1, 0.96))
    savefig(fig, "fig_essais_5TC_par_courant.png")


# ========================================================================
# fig_dissipation_monospot
# ========================================================================
def fig_dissipation_monospot():
    """Décroissance longitudinale (spot unique fixe à x=60, y=0), 4 courants.

    Les essais sont tous coupés au même pic (~270 °C au spot, échantillon
    réutilisable) → panneau (a) : pics absolus atteints par courant ; panneau
    (b) : profils normalisés au spot, qui se superposent en une seule courbe =
    forme de la source en longueur INVARIANTE avec le courant.
    """
    fig, (axa, axb) = plt.subplots(1, 2, figsize=(9.4, 3.5))
    x = np.array([0, 30, 60, 90, 120])
    modele_norm = np.array([0.013, 0.094, 1.00, 0.094, 0.027])   # forme modèle (symétrique)

    pics_dT = []      # ΔT au pic par courant (pour le modèle absolu de référence)
    for I, rel in DISSIP_FILES.items():
        dfc, amb, _ = clean(load_txt(DATA9 / rel))
        mesure = np.array([dfc[f"TC{i}"].max() for i in range(1, 6)])   # °C absolu
        dT = mesure - amb
        pics_dT.append(dT[2])
        col = DISSIP_COLOR[I]
        # (a) absolu °C
        axa.plot(x, mesure, "-o", color=col, markeredgecolor="white", markeredgewidth=0.5,
                 label=f"{I} A", zorder=3)
        # (b) normalisé au spot
        axb.plot(x, dT / dT[2], "-o", color=col, markeredgecolor="white", markeredgewidth=0.5,
                 label=f"{I} A", zorder=3)

    # Modèle : forme normalisée, remise à l'échelle absolue via le pic moyen mesuré
    dT_ref = float(np.mean(pics_dT))
    axa.plot(x, modele_norm * dT_ref + 25.0, "--s", color=C_MODEL, markeredgecolor="white",
             markeredgewidth=0.5, label="Modèle (forme)", zorder=2)
    axb.plot(x, modele_norm, "--s", color=C_MODEL, markeredgecolor="white",
             markeredgewidth=0.5, label="Modèle (forme)", zorder=2)

    for ax in (axa, axb):
        ax.axvline(60, ls=":", color="0.6", lw=0.8, zorder=0)
        ax.set_xticks(x)
        ax.set_xlabel("Position en longueur $x$ (mm)")
    axa.annotate("spot centré à $x$ = 60 mm\n(centre du coil) → pic ici",
                 xy=(60, dT_ref + 25.0), xytext=(64, (dT_ref + 25.0) * 0.80),
                 fontsize=8, color="0.25", ha="left",
                 arrowprops=dict(arrowstyle="-", color="0.4", lw=0.6))
    axa.set_ylabel("Température de pic atteinte (°C)")
    axb.set_ylabel("Profil normalisé au spot (–)")
    panel_title(axa, "(a) pics absolus — 4 courants")
    panel_title(axb, "(b) normalisé : forme invariante en courant")
    axb.legend(loc="upper left", ncol=1, frameon=False, fontsize=8.5)
    fig.suptitle("Décroissance longitudinale : mesuré vs modèle (spot unique, $y$=0)",
                 fontsize=12, fontweight="bold", y=1.02)
    fig.tight_layout()
    savefig(fig, "fig_dissipation_monospot.png")


# ========================================================================
# fig_dissipation_semistatique — 4 panneaux dwell
# ========================================================================
def fig_dissipation_semistatique():
    fig, axes = plt.subplots(1, 4, figsize=(9.2, 3.0), sharex=True, sharey=True)
    x = np.array([0, 30, 60, 90, 120])
    # Élévations modélisées par dwell (ΔT au-dessus de la ligne de base, °C)
    modele_dT = {
        "d1": np.array([104.2, 91.1, 2.4, 0.2, 0.0]),
        "d2": np.array([0.0, 96.5, 107.9, 3.1, 0.1]),
        "d3": np.array([0.0, 0.0, 92.3, 107.5, 5.2]),
        "d4": np.array([0.0, 0.0, 0.0, 78.1, 156.4]),
    }
    # Températures brutes atteintes (pic absolu, °C) lues dans le relevé exp9
    # semi-statique, fenêtrées par dwell (spot avançant de 30 mm).
    dfc, amb, _ = clean(load_txt(DATA9 / "200A" / "200A_y0_semistatique.txt"))
    t = dfc["t"].to_numpy()
    fenetres = {"d1": (0, 90), "d2": (90, 190), "d3": (190, 290), "d4": (290, 400)}
    mesure, base = {}, {}
    for key, (a, b) in fenetres.items():
        m = (t >= a) & (t < b)
        mesure[key] = np.array([dfc[f"TC{i}"].to_numpy()[m].max() for i in range(1, 6)])
        # ligne de base du dwell = moyenne des 3 premiers points de la fenêtre
        base[key] = np.array([dfc[f"TC{i}"].to_numpy()[m][:3].mean() for i in range(1, 6)])

    labels = "abcd"
    h_model = h_mes = None
    for ax, (key, lab) in zip(axes, zip(["d1", "d2", "d3", "d4"], labels)):
        # Modèle en °C absolu = ligne de base mesurée + ΔT modélisée du dwell
        modele_abs = base[key] + modele_dT[key]
        (h_model,) = ax.plot(x, modele_abs, "--s", color=C_MODEL, markeredgecolor="white",
                             markeredgewidth=0.5, label="Modèle (base + ΔT)")
        (h_mes,) = ax.plot(x, mesure[key], "-o", color=C150, markeredgecolor="white",
                           markeredgewidth=0.5, label="Mesuré (pic)")
        panel_title(ax, f"({lab}) dwell {key[1]}")
        ax.set_xticks(x)
    axes[0].set_ylim(0, 260)
    fig.legend(handles=[h_mes, h_model], loc="upper center", ncol=2,
               bbox_to_anchor=(0.5, 0.99), frameon=False, fontsize=10)
    fig.suptitle("Empreinte par dwell : modèle multi-spots vs mesuré",
                 fontsize=12, fontweight="bold", y=1.06)
    fig.supxlabel("Position en longueur $x$ (mm)", fontsize=11, fontweight="bold")
    fig.supylabel("Température de pic atteinte (°C)", fontsize=11, fontweight="bold")
    fig.tight_layout(rect=(0.02, 0.03, 1, 0.94))
    savefig(fig, "fig_dissipation_semistatique.png")


if __name__ == "__main__":
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    todo = {
        "fig1": fig1, "fig2": fig2, "fig3": fig3, "fig4": fig4, "fig5": fig5,
        "chant": fig_essais_chant_superpose, "par": fig_essais_par_courant,
        "5tc": fig_essais_5TC_par_courant, "mono": fig_dissipation_monospot,
        "semi": fig_dissipation_semistatique,
    }
    for k, fn in todo.items():
        if only and k not in only:
            continue
        fn()
    print("done")
