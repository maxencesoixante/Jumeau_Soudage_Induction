#!/usr/bin/env python
"""Figures de l'issue #74 (transfert thermique dans l'épaisseur).

1. fig74_carte_pertes.png — rapports face opposée / interface et surface /
   interface du 3D en fonction des pertes de face (h_contact en haut, h_bas en
   bas), essai chauffe_201A_3TC, avec les fourchettes mesurées. Grille 3D
   31×11×15, facteur 6.0123 : les rapports sont quasi insensibles au facteur
   (0,37–0,38 de 12 à 19, 0,40–0,44 à 3,9), la carte vaut donc pour tout facteur.
2. fig74_courbes_201A.png — les 3 TC empilés du 201 A, mesurés contre le 3D
   actuel (6,01 / 5 / 15) et contre le 3D à pertes fortes (100 / 500). Pour
   comparer les FORMES à niveau égal, le second est recalé sur le pic d'interface
   de ce point (facteur 17,1) : ce recalage est illustratif et rejeté en
   validation (le point des 3 TC est au centre de la boucle, chauffé par
   conduction dans le plan).
3. fig74_validation_3D.png — RMSE par essai (A/B, exp9) et écart de pic au TC de
   référence, pour les trois jeux testés, lus dans les journaux de valider.py
   (resultats/valid3d_*.log). Les chiffres extraits sont aussi écrits dans
   biblio/labo/figures/issue74/validation_3D.csv (versionné).

Les simulations de la carte sont mises en cache dans resultats/fig74_carte.npz.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))
sys.path.insert(0, str(R / "code" / "scripts"))
sys.path.insert(0, str(R / "code" / "scripts" / "diag"))
from _style import apply_style, savefig, OKABE_ITO, GRIS_MODELE  # noqa: E402

apply_style(**{"font.size": 9, "axes.labelsize": 9.5, "axes.titlesize": 9.5,
               "legend.fontsize": 7.8, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5})
import matplotlib.pyplot as plt  # noqa: E402

from jumeau.materiaux import Config  # noqa: E402
from jumeau.procede import Essai  # noqa: E402
from diag_epaisseur_3d_reference import mesure, rapports  # noqa: E402

OUT = R / "biblio" / "labo" / "figures" / "issue74"
CACHE = R / "resultats" / "fig74_carte.npz"
ESSAI_REF = R / "code" / "config" / "essais" / "chauffe_201A_3TC.yaml"
OI_BANDE, SI_BANDE = (0.32, 0.48), (0.84, 0.94)
HC = np.array([5, 10, 20, 50, 100, 200, 500])
HB = np.array([15, 50, 100, 200, 300, 500, 1000])


def essai(facteur, hc, hb, nx=31, ny=11, nz=15):
    cfg = Config.charger(R / "code" / "config")
    cfg.contact.h_contact = float(hc)
    cfg.ambiant.h_bas = float(hb)
    return Essai(cfg, ESSAI_REF, nx=nx, ny=ny, nz=nz, facteur_couplage=facteur, racine=R)


def simuler(facteur, hc, hb):
    e = essai(facteur, hc, hb)
    solveur, sol = e.simuler(modele="3D")
    s = e.series_tc(solveur, sol)
    return sol.t, s["TC1"], s["TC2"], s["TC3"]


def carte():
    if CACHE.exists():
        d = np.load(CACHE)
        if np.array_equal(d["hc"], HC) and np.array_equal(d["hb"], HB):
            return d["oi"], d["si"]
    oi = np.zeros((len(HB), len(HC))); si = np.zeros_like(oi)
    for j, hb in enumerate(HB):
        for i, hc in enumerate(HC):
            t, s, it, o = simuler(6.0123, hc, hb)
            r = rapports(t, s, it, o)
            oi[j, i], si[j, i] = r[2], r[3]
            print(f"h_contact {hc:4d}  h_bas {hb:5d}  o/i {r[2]:.2f}  s/i {r[3]:.2f}", flush=True)
    CACHE.parent.mkdir(exist_ok=True)
    np.savez(CACHE, hc=HC, hb=HB, oi=oi, si=si)
    return oi, si


def fig_carte():
    from scipy.interpolate import RegularGridInterpolator
    oi, si = carte()
    lx, ly = np.log10(HC), np.log10(HB)
    # interpolation (en log h) sur une grille fine : la zone faisable n'est plus
    # réduite aux seuls nœuds calculés
    fx, fy = np.linspace(lx[0], lx[-1], 160), np.linspace(ly[0], ly[-1], 160)
    FX, FY = np.meshgrid(fx, fy)
    pts = np.column_stack([FY.ravel(), FX.ravel()])
    OI = RegularGridInterpolator((ly, lx), oi)(pts).reshape(FX.shape)
    SI = RegularGridInterpolator((ly, lx), si)(pts).reshape(FX.shape)
    ok = ((OI >= OI_BANDE[0]) & (OI <= OI_BANDE[1]) & (SI >= SI_BANDE[0]) & (SI <= SI_BANDE[1]))
    virgule = lambda v: f"{v:.2f}".replace(".", ",")
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.5), sharey=True,
                             gridspec_kw=dict(wspace=0.14))
    for ax, Z, bande, titre, cmap in (
            (axes[0], OI, OI_BANDE, "Face opposée / interface", "Blues"),
            (axes[1], SI, SI_BANDE, "Surface / interface", "Oranges")):
        cf = ax.contourf(FX, FY, Z, levels=12, cmap=cmap, alpha=0.85)
        cs = ax.contour(FX, FY, Z, levels=list(bande), colors="k", linewidths=1.3)
        ax.clabel(cs, fmt=virgule, fontsize=7.5)
        ax.contourf(FX, FY, ok.astype(float), levels=[0.5, 1.5], colors="none",
                    hatches=["////"], zorder=3)
        ax.contour(FX, FY, ok.astype(float), levels=[0.5], colors=OKABE_ITO["vert"],
                   linewidths=1.8, zorder=4)
        ax.axhline(np.log10(300), color="0.3", ls="--", lw=0.9)
        ax.plot(np.log10(5), np.log10(15), "o", color=OKABE_ITO["vermillon"], ms=7,
                mec="k", mew=0.6, zorder=5, clip_on=False)
        ax.plot(np.log10(100), np.log10(500), "*", color=OKABE_ITO["jaune"], ms=12,
                mec="k", mew=0.6, zorder=5)
        ax.set_title(titre)
        ax.set_xticks(lx, [str(v) for v in HC])
        ax.set_xlim(lx[0] - 0.06, lx[-1] + 0.03)
        ax.set_xlabel("h_contact, face haute (W/(m²·K))")
        cb = fig.colorbar(cf, ax=ax, fraction=0.05, pad=0.02)
        cb.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f}".replace(".", ",")))
    axes[0].set_yticks(ly, [str(v) for v in HB])
    axes[0].set_ylim(ly[0] - 0.06, ly[-1] + 0.03)
    axes[0].set_ylabel("h_bas, face basse (W/(m²·K))")
    axes[1].text(lx[-1] - 0.02, np.log10(300) - 0.03, "borne de calibration\nh_bas = 300",
                 fontsize=6.8, color="0.2", ha="right", va="top")
    h = [plt.Line2D([], [], marker="o", ls="", color=OKABE_ITO["vermillon"], mec="k", label="jeu 3D actuel (5 / 15)"),
         plt.Line2D([], [], marker="*", ls="", ms=11, color=OKABE_ITO["jaune"], mec="k", label="pertes fortes (100 / 500)"),
         plt.Line2D([], [], color="k", lw=1.3, label="bornes de la fourchette mesurée"),
         plt.Rectangle((0, 0), 1, 1, fc="none", ec=OKABE_ITO["vert"], hatch="////",
                       label="les deux rapports dans leur fourchette")]
    fig.legend(handles=h, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.13))
    savefig(fig, OUT / "fig74_carte_pertes.png", bbox_inches="tight")
    plt.close(fig)


def fig_courbes():
    e = essai(6.0123, 5, 15)
    tm, sm, im, om = mesure(e)
    jeux = [("3D actuel\n(6,01 / 5 / 15)", simuler(6.0123, 5, 15)),
            ("3D pertes fortes, niveau recalé\n(17,1 / 100 / 500)", simuler(17.1, 100, 500))]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.2), sharey=True, gridspec_kw=dict(wspace=0.08))
    coul = {"surface": OKABE_ITO["orange"], "interface": OKABE_ITO["vermillon"],
            "face opposée": OKABE_ITO["bleu"]}
    for ax, (titre, (t, s, i, o)) in zip(axes, jeux):
        for nom, vm, vs in (("surface", sm, s), ("interface", im, i), ("face opposée", om, o)):
            ax.plot(tm, vm, "-", color=coul[nom], lw=1.1, alpha=0.55)
            ax.plot(t, vs, "--", color=coul[nom], lw=1.6)
        k = int(np.nanargmax(i))
        ax.set_title(titre, fontsize=8.8)
        ax.text(0.97, 0.95, f"face opposée / interface\n{o[k] / i[k]:.2f}".replace(".", ",") + "  (mesuré 0,42)",
                transform=ax.transAxes, ha="right", va="top", fontsize=7.6,
                bbox=dict(fc="white", ec="0.7", lw=0.5, pad=2.5))
        ax.set_xlabel("temps (s)")
        ax.set_xlim(0, 200)
    axes[0].set_ylabel("température (°C)")
    h = [plt.Line2D([], [], color=c, lw=1.6, label=n) for n, c in coul.items()]
    h += [plt.Line2D([], [], color="0.4", lw=1.1, alpha=0.55, label="mesuré"),
          plt.Line2D([], [], color="0.4", lw=1.6, ls="--", label="simulé")]
    fig.legend(handles=h, loc="lower center", ncol=5, frameon=False, bbox_to_anchor=(0.5, -0.08))
    savefig(fig, OUT / "fig74_courbes_201A.png", bbox_inches="tight")
    plt.close(fig)


def lire_log(chemin):
    """{essai: (rmse_moyen, {TC: delta_T_max})} depuis une sortie de valider.py."""
    res, cur = {}, None
    for ligne in Path(chemin).read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"=== (\S+) \[3D\] ===", ligne)
        if m:
            cur = m.group(1); res[cur] = [None, {}]; continue
        m = re.match(r"(TC\d)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)", ligne)
        if m and cur:
            res[cur][1][m.group(1)] = float(m.group(5))
        m = re.match(r"RMSE moyen : ([\d.]+)", ligne)
        if m and cur:
            res[cur][0] = float(m.group(1))
    return res


def fig_validation():
    jeux = [("actuel\n6,01 / 5 / 15", ["valid3d_actuel.log"], GRIS_MODELE),
            ("facteur calé au point 3 TC\n17,1 / 100 / 500", ["valid3d_nouveau.log"], OKABE_ITO["vermillon"]),
            ("facteur calé sur exp9\n3,93 / 100 / 500", ["valid3d_f393_AB.log", "valid3d_f393_exp9.log"], OKABE_ITO["bleu"])]
    donnees = []
    for lab, logs, c in jeux:
        d = {}
        for l in logs:
            d.update(lire_log(R / "resultats" / l))
        donnees.append((lab, d, c))
    essais = ["serieA_A-1", "serieA_A-3", "serieB_B-2", "exp9_175A_monospot", "exp9_200A_monospot",
              "exp9_200A_y20_monospot", "exp9_226A_monospot", "exp9_250A_monospot"]
    court = ["A-1", "A-3", "B-2", "exp9\n175 A", "exp9\n200 A", "exp9\n200 A\ny=20", "exp9\n226 A", "exp9\n250 A"]

    # écart de pic : moyenne des TC intérieurs TC2-4 pour A/B, TC3 pour exp9
    def ecart(d, e):
        dt = d[e][1]
        return np.mean([dt[k] for k in ("TC2", "TC3", "TC4") if k in dt]) if e.startswith("serie") else dt["TC3"]

    lignes = ["jeu,essai,rmse_moyen,ecart_pic_reference"]
    for lab, d, _ in donnees:
        for e in essais:
            lignes.append(f"\"{lab.replace(chr(10), ' ')}\",{e},{d[e][0]},{ecart(d, e):.1f}")
    (OUT / "validation_3D.csv").write_text("\n".join(lignes) + "\n", encoding="utf-8")

    fig, axes = plt.subplots(2, 1, figsize=(7.4, 5.6), sharex=True, gridspec_kw=dict(hspace=0.12))
    x = np.arange(len(essais)); w = 0.26
    for k, (lab, d, c) in enumerate(donnees):
        axes[0].bar(x + (k - 1) * w, [d[e][0] for e in essais], w, color=c, label=lab)
        v = np.array([ecart(d, e) for e in essais])
        axes[1].bar(x + (k - 1) * w, np.clip(v, -250, 250), w, color=c)
        for xi, vi in zip(x + (k - 1) * w, v):
            if abs(vi) > 250:
                axes[1].text(xi, 245 if vi > 0 else -245, f"{vi:+.0f}", rotation=90, fontsize=6.5,
                             ha="center", va="top" if vi > 0 else "bottom", color="white")
    axes[0].set_ylabel("RMSE moyen (°C)")
    axes[0].legend(ncol=3, frameon=False, loc="upper left", fontsize=7.2)
    axes[0].set_ylim(0, 115)
    axes[1].axhline(0, color="k", lw=0.7)
    axes[1].set_ylim(-250, 250)
    axes[1].set_ylabel("écart de pic (°C)\nA/B : TC2–4 ; exp9 : TC3")
    axes[1].set_xticks(x, court)
    axes[0].axvline(2.5, color="0.6", lw=0.7, ls=":"); axes[1].axvline(2.5, color="0.6", lw=0.7, ls=":")
    savefig(fig, OUT / "fig74_validation_3D.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    fig_validation()
    fig_courbes()
    fig_carte()
    print("ok")
