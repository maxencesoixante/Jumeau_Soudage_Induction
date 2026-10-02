#!/usr/bin/env python
"""Issue #74 — vue de côté du flux de chaleur dans l'épaisseur.

Plan x-z à y = 20 mm (colonne des 3 TC empilés de l'essai 201 A), à l'échelle
1:1, fenêtre centrée sur le spot. Au-dessus de l'empilement : céramique, MFC et
brins de la bobine. Dans l'empilement : champ de température (couleur) et
lignes du flux de chaleur q = −k ∇T (k_plan en x, k_z en z, k_z du laminé
inférieur réduit dans la configuration « transport ralenti »). Les 3 TC mesurés
sont posés en pastilles colorées sur la même échelle.

Deux configurations × deux instants (pic d'interface, puis 100 s après), plus
le profil T(z) de la colonne. Le niveau de chaque configuration est recalé sur
le pic d'interface mesuré en ce point (facteur 11,6 et 10,4) : ce point est au
centre de la boucle de la bobine, son niveau absolu est faussé par la limite #1
et le recalage est ILLUSTRATIF (rejeté en validation, cf. #74) — on compare ici
la FORME du gradient et du flux, pas le niveau.

Sortie : biblio/labo/figures/issue74/fig74_flux_epaisseur.png
Cache : resultats/fig74_flux_<config>.npz
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))
sys.path.insert(0, str(R / "code" / "scripts"))
sys.path.insert(0, str(R / "code" / "scripts" / "diag"))
sys.path.insert(0, str(R / "code" / "scripts" / "gen"))
from _style import apply_style, savefig, OKABE_ITO  # noqa: E402

apply_style(**{"font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9.5,
               "legend.fontsize": 7.8, "xtick.labelsize": 8, "ytick.labelsize": 8})
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from jumeau.materiaux import Config  # noqa: E402
from jumeau.procede import Essai  # noqa: E402
from diag_epaisseur_3d_reference import appliquer_kz_inf, mesure  # noqa: E402
import gen_schemas_montage as sch  # noqa: E402  (géométrie bobine/MFC/céramique)

ESSAI = R / "code" / "config" / "essais" / "chauffe_201A_3TC.yaml"
OUT = R / "biblio" / "labo" / "figures" / "issue74" / "fig74_flux_epaisseur.png"
NX, NY, NZ = 121, 21, 25
X_TC, Y_TC = 0.060, 0.020
FEN = (46.0, 74.0)                     # fenêtre x (mm), resserrée sur le spot
Z_HAUT = 9.0                           # haut de la vue (mm) : brins entiers, MFC tronqué
TMIN, TMAX = 20.0, 450.0
CONFIGS = {
    "actuel": dict(titre="3D actuel", facteur=11.6, h_contact=5.0, kz_inf=None),
    "ralenti": dict(titre="Transport ralenti sous l'interface", facteur=10.4, h_contact=40.0, kz_inf=0.10),
    "combiA": dict(titre="Combinaison A", facteur=11.3, h_contact=40.0, kz_inf=0.25, rc_fusion=0.02),
}


def simuler(nom, c):
    cache = R / "resultats" / f"fig74_flux_{nom}.npz"
    if cache.exists():
        d = np.load(cache)
        return {k: d[k] for k in d.files}
    cfg = Config.charger(R / "code" / "config")
    cfg.contact.h_contact = c["h_contact"]
    cfg.ambiant.h_bas = 15.0
    e = Essai(cfg, ESSAI, nx=NX, ny=NY, nz=NZ, facteur_couplage=c["facteur"], racine=R)
    kz = np.full(NZ, float(cfg.materiau.k_z))
    if c["kz_inf"] is not None:
        lam = cfg.geometrie["laminate"]
        appliquer_kz_inf(cfg.materiau, e.grille, lam, c["kz_inf"])
        kz[e.grille.z > lam["epaisseur_sup"] + lam["epaisseur_film"] / 2] = c["kz_inf"]
    rhs_orig = None
    if c.get("rc_fusion") is not None:
        import variantes_epaisseur as var
        from jumeau.thermique import solveur3d as s3
        rhs_orig = s3.SolveurThermique3D._rhs
        var.appliquer_rc_fusion(c["rc_fusion"])
    solveur, sol = e.simuler(modele="3D")
    if rhs_orig is not None:
        s3.SolveurThermique3D._rhs = rhs_orig
    g = e.grille
    T4 = sol.y.reshape(g.nx, g.ny, g.nz, -1)
    iy = int(np.argmin(np.abs(g.y - Y_TC)))
    ix = int(np.argmin(np.abs(g.x - X_TC)))
    ser = e.series_tc(solveur, sol)
    d = dict(x=g.x, z=g.z, t=sol.t, plan=T4[:, iy, :, :], colonne=T4[ix, iy, :, :],
             kz=kz, k_plan=np.array(float(cfg.materiau.k_plan)),
             s=ser["TC1"], i=ser["TC2"], o=ser["TC3"])
    cache.parent.mkdir(exist_ok=True)
    np.savez(cache, **d)
    return d


def composants(ax):
    """Céramique, MFC et brins au-dessus de l'empilement (z > 0, mm)."""
    xc = X_TC * 1e3
    ax.add_patch(Rectangle((FEN[0], 0), FEN[1] - FEN[0], sch.GAP_CERAM, fc=sch.C_CERAM,
                           alpha=0.55, ec=sch.C_CERAM_EDGE, lw=0.6, zorder=3))
    ax.add_patch(Rectangle((xc - sch.MFC_X / 2, sch.H_MFC_BOT), sch.MFC_X, sch.MFC_H,
                           fc=sch.C_MFC, alpha=0.35, ec="0.2", lw=0.8, zorder=3, clip_on=True))
    for sgn in (-1, 1):
        ax.add_patch(Rectangle((xc + sgn * sch.ENTRAXE / 2 - sch.TUBE / 2, sch.H_TUBE_BOT),
                               sch.TUBE, sch.TUBE, fc=sch.C_COIL, ec="0.15", lw=0.7, zorder=4))


def carte(ax, d, k_t, tm, mes, k_m):
    """Champ T et lignes de flux dans le plan x-z, à l'instant d'indice k_t."""
    x = d["x"] * 1e3
    prof = d["z"] * 1e3                       # profondeur (mm), 0 = surface
    u = -prof[::-1]                           # hauteur affichée, croissante
    T = d["plan"][:, :, k_t]                  # (nx, nz)
    Tu = T[:, ::-1].T                         # (nz, nx), lignes = u croissant
    m = (x >= FEN[0]) & (x <= FEN[1])
    im = ax.imshow(Tu[:, m], extent=(x[m][0], x[m][-1], u[0], u[-1]), origin="lower",
                   cmap="inferno", vmin=TMIN, vmax=TMAX, aspect="equal",
                   interpolation="bilinear", zorder=1)
    # flux q = -k grad T, en coordonnées affichées (x, u = -profondeur)
    dTdx = np.gradient(T, d["x"], axis=0)
    dTdp = np.gradient(T, d["z"], axis=1)
    qx = -float(d["k_plan"]) * dTdx
    qu = d["kz"][None, :] * dTdp               # q_u = +k_z dT/dprof
    QX, QU = qx[:, ::-1].T[:, m], qu[:, ::-1].T[:, m]
    # flèches sur une grille régulière : direction = sens du flux, longueur
    # ∝ √|q| (normalisée au maximum de la vue) pour garder les flux faibles visibles
    xs, us = x[m], u
    ix = np.arange(1, len(xs), 2)
    iu = np.arange(1, len(us), 3)
    XX, UU = np.meshgrid(xs[ix], us[iu])
    qx_s, qu_s = QX[np.ix_(iu, ix)], QU[np.ix_(iu, ix)]
    mag = np.hypot(qx_s, qu_s)
    L = 1.6 * np.sqrt(mag / mag.max())
    ux, uu = qx_s / np.where(mag > 0, mag, 1), qu_s / np.where(mag > 0, mag, 1)
    ax.quiver(XX, UU, ux * L, uu * L, angles="xy", scale_units="xy", scale=1.0,
              color="white", width=0.0045, headwidth=3.5, headlength=3.5,
              headaxislength=3.0, alpha=0.9, zorder=2)
    # interface et 3 TC mesurés (pastilles à la couleur de la mesure)
    ax.axhline(-sch.E_SUP, color="white", lw=0.6, ls=":", zorder=2)
    for zt, v in zip((0.0, -sch.E_SUP, -sch.L_INF), mes):
        ax.scatter([X_TC * 1e3], [zt], s=70, c=[v], cmap="inferno", vmin=TMIN, vmax=TMAX,
                   edgecolors="white", linewidths=1.2, zorder=6, clip_on=False)
    composants(ax)
    ax.set_xlim(*FEN)
    ax.set_ylim(-sch.L_INF - 0.6, Z_HAUT)
    ax.set_yticks([-sch.L_INF, -sch.E_SUP, 0, sch.GAP_CERAM, sch.H_TUBE_TOP])
    ax.set_yticklabels([mm(-sch.L_INF), mm(-sch.E_SUP), "0", "2", "8"])
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return im


def mm(v):
    """Cote en mm à deux décimales, virgule et vrai signe moins (−3,36 ; −6,82)."""
    return f"{v:.2f}".replace("-", "−").replace(".", ",")


def main(configs=("actuel", "ralenti"), nom_fig="fig74_flux_epaisseur.png"):
    e = Essai(Config.charger(R / "code" / "config"), ESSAI, nx=31, ny=11, nz=15,
              facteur_couplage=1.0, racine=R)
    tm, sm, im_, om = mesure(e)
    km = int(np.nanargmax(im_))
    instants_mes = [tm[km], tm[km] + 100.0]
    mes = [[float(np.interp(tq, tm, v)) for v in (sm, im_, om)] for tq in instants_mes]

    choix = {n: CONFIGS[n] for n in configs}
    donnees = {n: simuler(n, c) for n, c in choix.items()}
    instants = {}
    for nom, d in donnees.items():
        k0 = int(np.argmax(d["i"]))
        instants[nom] = [k0, int(np.argmin(np.abs(d["t"] - (d["t"][k0] + 100.0))))]

    fig = plt.figure(figsize=(8.6, 6.0))
    gs = fig.add_gridspec(2, 3, width_ratios=[1, 1, 0.66], wspace=0.24, hspace=0.34,
                          left=0.09, right=0.98, top=0.92, bottom=0.15)
    coul = {"actuel": "0.35", "ralenti": OKABE_ITO["bleu"], "combiA": OKABE_ITO["vert"]}
    lignes = ("Pic d'interface", "100 s après le pic")
    for r, lab in enumerate(lignes):
        for col, (nom, c) in enumerate(choix.items()):
            ax = fig.add_subplot(gs[r, col])
            img = carte(ax, donnees[nom], instants[nom][r], tm, mes[r], km)
            if r == 0:
                ax.set_title(c["titre"], fontsize=9.5)
            if col == 0:
                ax.set_ylabel(f"{lab}\nz (mm)")
            else:
                ax.set_yticklabels([])
            if r == 1:
                ax.set_xlabel("x (mm)")
        ax = fig.add_subplot(gs[r, 2])
        for nom, c in choix.items():
            d = donnees[nom]
            ax.plot(d["colonne"][:, instants[nom][r]], -d["z"] * 1e3, color=coul[nom], lw=1.6,
                    label=c["titre"].replace(" sous l'interface", ""))
        ax.scatter(mes[r], [0.0, -sch.E_SUP, -sch.L_INF], s=34, color=OKABE_ITO["vermillon"],
                   edgecolor="k", lw=0.5, zorder=5, label="mesuré (3 TC)")
        ax.axhline(-sch.E_SUP, color="0.6", lw=0.6, ls=":")
        ax.set_ylim(-sch.L_INF - 0.4, 0.4)
        ax.set_xlim(0, TMAX)
        ax.set_yticks([-sch.L_INF, -sch.E_SUP, 0])
        ax.set_yticklabels([mm(-sch.L_INF), mm(-sch.E_SUP), "0"])
        if r == 0:
            ax.set_title("Profil T(z), colonne des TC", fontsize=9.5)
            ax.legend(frameon=False, fontsize=6.8, loc="upper left")
        else:
            ax.set_xlabel("température (°C)")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    cax = fig.add_axes([0.09, 0.05, 0.50, 0.018])
    cb = fig.colorbar(img, cax=cax, orientation="horizontal")
    cb.set_label("température (°C)")
    savefig(fig, OUT.parent / nom_fig, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
    main(configs=("actuel", "combiA"), nom_fig="fig74_flux_combinaison.png")
    print(OUT.relative_to(R))
