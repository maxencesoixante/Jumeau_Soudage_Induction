#!/usr/bin/env python
"""Issue #66 — figures pour comprendre la campagne de validation de part et
d'autre du 231 A (volet bas 160 A, volet haut 275 A).

1. fig66_domaine.png    — tous les essais réalisés, par campagne, sur l'axe du
   courant ; boîte de calibration 150–250 A ; les deux cibles.
2. fig66_loi_I2.png     — taux de chauffe mesuré au chant (exp7, définition
   d'origine de gen_figures_elsevier.py : max(TC1, TC5), élévation 30 → 130 °C,
   moyenne des répétitions) en fonction de I², ajustement
   R = k·I² − L et extrapolation aux deux cibles.
3. fig66_protocoles.png — vue de dessus, disposition des TC v2 (TC1/TC5 au
   centre y = 20, TC2–TC4 au bord y = 0), 4 spots au pas de 30 mm, et le
   capteur qui commande la coupure : point chaud sous le spot à 160 A, TC de
   bord le plus proche à 275 A (TC2, TC3, TC4, TC4, cf. gen_cycle_230A_TC390.py).

Consigne de lisibilité : cotes, axes et légende ; pas de phrases dans les figures.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))
sys.path.insert(0, str(R / "code" / "scripts"))
sys.path.insert(0, str(R / "code" / "scripts" / "gen"))
import gen_schemas_montage as g  # noqa: E402
from _style import OKABE_ITO  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Rectangle, FancyArrowPatch  # noqa: E402

from jumeau.materiaux import charger_yaml  # noqa: E402

OUT = R / "biblio" / "labo" / "figures" / "issue66"
C_BAS, C_HAUT = OKABE_ITO["bleu"], OKABE_ITO["vermillon"]
CAMPAGNES = [
    ("exp7 (largeur)", [150, 176, 200, 225, 250], OKABE_ITO["vert"], "o"),
    ("exp9 (longueur)", [175, 200, 200, 226, 250], OKABE_ITO["orange"], "s"),
    ("3 TC empilés", [174.4, 201.6, 226, 226, 250], OKABE_ITO["rose"], "D"),
    ("séries A/B (semi-statique)", [250, 250, 250], OKABE_ITO["noir"], "^"),
    ("231 A semi-statique (v1, v2)", [231, 231], "0.45", "v"),
]


def fig_domaine():
    fig, ax = plt.subplots(figsize=(8.2, 3.2))
    ax.axvspan(150, 250, color="0.92", zorder=0)
    ax.text(200, len(CAMPAGNES) + 0.25, "boîte de calibration\n(150 – 250 A)", ha="center", va="bottom",
            fontsize=7.6, color="0.4")
    for k, (lab, cour, c, m) in enumerate(CAMPAGNES):
        y = len(CAMPAGNES) - k - 1
        cour = np.asarray(cour, float)
        jit = np.zeros_like(cour)
        for v in np.unique(cour):                    # répétitions décalées verticalement
            idx = np.where(cour == v)[0]
            jit[idx] = (np.arange(len(idx)) - (len(idx) - 1) / 2) * 0.18
        ax.scatter(cour, y + jit, s=42, color=c, marker=m, edgecolor="k", lw=0.5, zorder=5)
        ax.text(138, y, lab, ha="right", va="center", fontsize=8)
    for v, lab, c in ((160, "volet bas\n160 A", C_BAS), (275, "volet haut\n275 A", C_HAUT)):
        ax.axvline(v, color=c, lw=2.0, ls="--", zorder=3)
        ax.text(v, len(CAMPAGNES) + 0.25, lab, ha="center", va="bottom", fontsize=8, color=c, fontweight="bold",
                bbox=dict(fc="white", ec="none", pad=1.5), zorder=6)
    ax.set_xlim(140, 290)
    ax.set_ylim(-0.7, len(CAMPAGNES) + 1.3)
    ax.set_yticks([])
    ax.set_xlabel("courant (A)")
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    g.savefig(fig, OUT / "fig66_domaine.png", bbox_inches="tight")
    plt.close(fig)


def taux_exp7():
    """Taux de chauffe au chant, définition D'ORIGINE (gen_figures_elsevier.py, fig. 5) :
    élévation au-dessus de l'ambiante du max(TC1, TC5), pente ajustée entre 30 et
    130 °C d'élévation, moyenne (et min / max) sur les répétitions de chaque courant."""
    import gen_figures_elsevier as ge
    GRP = {150: ["150A_v1.txt", "150A_v2.txt", "150A_v3.txt"], 176: ["176A_v1.txt"],
           200: ["200A_v4_TC1ok.txt", "200A_v5.txt", "200A_v6.txt"], 225: ["225A_v1.txt"],
           250: ["250A_v1.txt", "250A_v2.txt", "250A_v3.txt"]}

    def rate(cur, fname):
        dfc, amb, _ = ge.clean(ge.load_txt(ge.DATA7 / f"{cur}A" / fname))
        ch = np.maximum(dfc["TC1"], dfc["TC5"]).to_numpy() - amb
        t = dfc["t"].to_numpy()
        ip = int(np.argmax(ch)); ch, t = ch[:ip + 1], t[:ip + 1]
        m = (ch >= 30) & (ch <= 130)
        return np.polyfit(t[m], ch[m], 1)[0]

    I, moy, lo, hi = [], [], [], []
    for cur, fs in GRP.items():
        r = np.array([rate(cur, f) for f in fs])
        I.append(float(cur)); moy.append(r.mean()); lo.append(r.min()); hi.append(r.max())
    return np.array(I), np.array(moy), np.array(lo), np.array(hi)


def fig_loi_I2():
    I, taux, lo, hi = taux_exp7()
    A = np.vstack([I ** 2, -np.ones_like(I)]).T
    (k, L), *_ = np.linalg.lstsq(A, taux, rcond=None)
    pred = k * I ** 2 - L
    r2 = 1 - np.sum((taux - pred) ** 2) / np.sum((taux - taux.mean()) ** 2)
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    x = np.linspace(120 ** 2, 290 ** 2, 100)
    ax.axvspan(150 ** 2, 250 ** 2, color="0.92", zorder=0)
    ax.plot(x, k * x - L, color="0.35", lw=1.2, ls="--", zorder=2,
            label=f"R = k·I² − L  (R² = {r2:.3f})".replace(".", ","))
    ax.errorbar(I ** 2, taux, yerr=np.vstack([taux - lo, hi - taux]), fmt="o", ms=7,
                color=OKABE_ITO["vert"], mec="k", mew=0.5, ecolor=OKABE_ITO["vert"], elinewidth=1.0,
                capsize=3, zorder=5, label="exp7 mesuré (chant, élévation 30 → 130 °C ; min–max)")
    for v, c in ((160, C_BAS), (275, C_HAUT)):
        r = k * v ** 2 - L
        ax.scatter([v ** 2], [r], s=90, facecolor="white", edgecolor=c, lw=2.0, zorder=6)
        ax.annotate(f"{v} A : {r:.0f} °C/s".replace(".", ","), (v ** 2, r), xytext=(10, -14),
                    textcoords="offset points", fontsize=8, color=c, fontweight="bold")
    ax.set_xticks([c ** 2 for c in (150, 175, 200, 225, 250, 275)],
                  [f"{c}²" for c in (150, 175, 200, 225, 250, 275)])
    ax.set_xlabel("I² (A²)")
    ax.set_ylabel("taux de chauffe au chant (°C/s)")
    ax.set_xlim(x[0], x[-1])
    ax.legend(frameon=False, fontsize=7.6, loc="upper left")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    g.savefig(fig, OUT / "fig66_loi_I2.png", bbox_inches="tight")
    plt.close(fig)
    return k, L, r2


def vue(ax, controle, couleur, titre):
    g.coupon_weave(ax, 0, 0, g.L, g.W)
    tcs = {"TC1": (0, 20), "TC2": (30, 0), "TC3": (60, 0), "TC4": (90, 0), "TC5": (120, 20)}
    for n, (x, y) in tcs.items():
        ax.scatter([x], [y], s=46, color=g.C_TC, edgecolor="k", lw=0.5, zorder=8)
        ax.text(x, y + (3.5 if y > 0 else -4.5), n, ha="center", va="bottom" if y > 0 else "top",
                fontsize=7, color=g.C_TC, fontweight="bold", zorder=9)
    for k, xc in enumerate(g.CENTRES_DWELL, start=1):
        ax.add_patch(Rectangle((xc - g.MFC_X / 2, -2), g.MFC_X, g.W + 4, fc="none", ec="0.55",
                               lw=0.7, ls=":", zorder=3))
        ax.text(xc, g.W + 4.5, f"{k}", ha="center", va="bottom", fontsize=8, color="0.3")
        cible = controle(k, xc)
        ax.scatter([cible[0]], [cible[1]], s=150, marker="*", color=couleur, edgecolor="k", lw=0.5, zorder=10)
        if abs(cible[0] - xc) > 1:
            ax.add_patch(FancyArrowPatch((xc, 12), (cible[0], cible[1] + 2.5), arrowstyle="-|>",
                                         mutation_scale=8, lw=1.0, color=couleur, zorder=9,
                                         connectionstyle="arc3,rad=0.2"))
    ax.set_xlim(-8, g.L + 8)
    ax.set_ylim(-11, g.W + 11)
    ax.set_aspect("equal")
    ax.set_title(titre, fontsize=9.5, color=couleur)
    ax.set_xlabel("x (mm)")
    ax.set_yticks([0, 20, 40])
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)


def fig_protocoles():
    fig, axes = plt.subplots(2, 1, figsize=(7.6, 5.8), gridspec_kw=dict(hspace=0.45))
    vue(axes[0], lambda k, xc: (xc, 0.0), C_BAS, "Volet bas, 160 A : coupure sur le point chaud")
    ctrl = {1: 30.0, 2: 60.0, 3: 90.0, 4: 90.0}
    vue(axes[1], lambda k, xc: (ctrl[k], 0.0), C_HAUT, "Volet haut, 275 A : coupure sur le TC de bord le plus proche")
    axes[0].set_ylabel("y (mm)")
    axes[1].set_ylabel("y (mm)")
    h = [Line2D([0], [0], marker="o", color="none", markerfacecolor=g.C_TC, markeredgecolor="k",
                markersize=6, label="TC d'interface (disposition v2)"),
         Rectangle((0, 0), 1, 1, fc="none", ec="0.55", ls=":", label="empreinte du MFC, passes 1 à 4"),
         Line2D([0], [0], marker="*", color="none", markerfacecolor="0.4", markeredgecolor="k",
                markersize=11, label="capteur qui commande la coupure de la passe")]
    fig.legend(handles=h, loc="lower center", ncol=3, frameon=False, fontsize=7.6, bbox_to_anchor=(0.5, -0.02))
    g.savefig(fig, OUT / "fig66_protocoles.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    fig_domaine()
    k, L, r2 = fig_loi_I2()
    print(f"k = {k:.3e} °C/s/A², L = {L:.2f} °C/s, R² = {r2:.4f}")
    fig_protocoles()
    print("ok")
