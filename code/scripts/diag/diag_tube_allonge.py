#!/usr/bin/env python
"""Tube substitut (issue #73) : écart 120 mm vs tube ALLONGÉ au-delà du connecteur.

Question : si le tube dépasse le connecteur (application réelle : cavité ~250 mm ;
tube substitut de #73 : 240 mm, décidé le 2026-09-30),
les spots d'extrémité voient de la matière non soudée au-delà du bord. De combien
cela change-t-il le cycle semi-statique par rapport à un tube de 120 mm, aussi
long que le connecteur ?

Modèle : solveur 2D lumpé (θ* canonique, facteur 6.0123), cycle « parfait » de
#64 (chauffe jusqu'à 390 °C au point chaud y=0 sous le spot, refroidissement
jusqu'à Tg=159 °C, avance ; 4 spots pas 30 mm), 5 TC sur la ligne y=0.

Empilement du TUBE SUBSTITUT dans les deux cas : connecteur 3,36 mm + film
0,1 mm + paroi du tube 1,68 mm (valeur utilisateur 2026-09-28) au lieu du laminé
inférieur plan de 3,36 mm. Le cas « allongé » étend le domaine en x de L_EXT de
chaque côté ; hors connecteur, seule la paroi du tube existe.

Deux ingrédients, sans toucher à jumeau/ :
  1. SolveurTubeAllonge : SolveurThermique2D avec une épaisseur lumpée e(x)
     (stack complet sous le connecteur, 1,68 mm au-delà). La conduction n'est
     plus e-invariante -> forme flux ∂/∂x(k·e·∂T/∂x)/e, épaisseur de face =
     min des deux mailles (au saut, seule la paroi mince porte le flux) ; les
     pertes surfaciques (h_bas_2d, h_haut sous le MFC) sont divisées par e(x).
     Auto-test : e uniforme + L_EXT=0 redonne le solveur d'origine.
  2. Source recomposée par couche : les couches du CONNECTEUR (laminé sup +
     twill) sont calculées sur la grille 120 mm (leurs courants se referment au
     bord du connecteur, correctif de bord x AUTO) ; la couche du TUBE est
     calculée sur la grille étendue (ses courants continuent au-delà).
     Approximation : l'écrantage de la paroi du tube par les couches du dessus
     est conservé au-delà du connecteur (léger sous-dépôt dans la rallonge).

Chants : h_bord_x0 = 0 (chants libres, confirmé terrain) dans les deux cas pour
que l'écart ne mesure QUE la géométrie ; le cas 120 mm avec h_bord_x0=125 (θ*
canonique) est donné en repère, pour situer l'ampleur du correctif empirique.

Non modélisé (identique dans les deux cas, donc hors écart) : largeur du tube
50 mm vs connecteur 40 mm, murs/fond (pertes via h_bas_2d effectif), face haute
de la rallonge sans perte (comme la face haute hors MFC du modèle, cf. #68).

Sorties : resultats/diag_tube_allonge.log,
          biblio/labo/figures/fig_tube_allonge_ecart.png
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import numpy as np

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts" / "gen"))
import gen_cycle_parfait_semistatique as g  # noqa: E402  (moteur #64 + style)

import matplotlib.pyplot as plt  # noqa: E402

from jumeau.em.source_joule import source_spot  # noqa: E402
from jumeau.geometrie import construire_couches, construire_grille, masque_empreinte_cfc  # noqa: E402
from jumeau.materiaux import Config  # noqa: E402
from jumeau.procede import charger_yaml  # noqa: E402
from jumeau.thermique.solveur2d import SolveurThermique2D  # noqa: E402
from jumeau.thermique.solveur3d import KELVIN  # noqa: E402

COURANT = 230.0            # A — même courant que la validation #64 (231 A réel)
E_TUBE = 0.00168           # m — paroi du tube substitut
DX = 0.002                 # m — pas en x commun aux deux grilles (nx=61 sur 120 mm)
NY, NZ = 21, 15
L_EXTS = [0.0, 0.030, 0.060]   # m — 0 = tube 120 mm ; 0.030 -> 180 mm ; 0.060 -> 240 mm (tube réel, décidé le 2026-09-30)
X_TC = [0.0, 0.030, 0.060, 0.090, 0.120]
OUT_LOG = R / "resultats" / "diag_tube_allonge.log"
OUT_FIG = R / "biblio" / "labo" / "figures" / "fig_tube_allonge_ecart.png"


def config_tube(h_bord_x0: float) -> Config:
    cfg = Config.charger(R / "code" / "config")
    cfg.geometrie["laminate"]["epaisseur_inf"] = E_TUBE
    cfg.ambiant.h_bord_x0 = h_bord_x0
    return cfg


class SolveurTubeAllonge(SolveurThermique2D):
    """2D lumpé à épaisseur e(x) variable (cf. docstring module). Chemin k
    scalaire isotrope uniquement (celui du θ* canonique)."""

    def __init__(self, *args, e_x: np.ndarray, **kw):
        super().__init__(*args, **kw)
        self.e_x = np.asarray(e_x, dtype=float)            # (nx,)
        self.e_face = np.minimum(self.e_x[:-1], self.e_x[1:])
        assert not self.mat.a_k_variable() and self.mat.k_plan_x is None

    def _rhs(self, t, Tflat, source_fn):
        g_, mat, amb, contact = self.g, self.mat, self.amb, self.contact
        T = Tflat.reshape(g_.nx, g_.ny)
        rc = mat.densite * mat.cp_apparent(T)
        k = mat.k_plan
        Ta_K = amb.T_amb + KELVIN
        dT = np.zeros_like(T)
        e = self.e_x[:, None]
        ef = self.e_face[:, None]

        # x : forme flux à épaisseur variable
        F = k * ef * (T[1:, :] - T[:-1, :]) / g_.dx          # W/m par unité de y
        dT[1:-1, :] += (F[1:, :] - F[:-1, :]) / (g_.dx * e[1:-1])
        for i, voisin in ((0, 1), (-1, -2)):
            Te = T[i, :]
            extra = amb.h_bord_x0 * (amb.T_amb - Te) if i == 0 else 0.0
            dT[i, :] += (2.0 / g_.dx) * (
                k * (T[voisin, :] - Te) / g_.dx
                + amb.h_convection * (amb.T_amb - Te)
                + mat.emissivite * amb.stefan_boltzmann * (Ta_K**4 - (Te + KELVIN)**4)
                + extra)
        # y : e constante le long de y -> forme d'origine
        dT[:, 1:-1] += k * (T[:, :-2] - 2.0 * T[:, 1:-1] + T[:, 2:]) / g_.dy**2
        for j, voisin in ((0, 1), (-1, -2)):
            Te = T[:, j]
            dT[:, j] += (2.0 / g_.dy) * (
                k * (T[:, voisin] - Te) / g_.dy
                + amb.h_convection * (amb.T_amb - Te)
                + mat.emissivite * amb.stefan_boltzmann * (Ta_K**4 - (Te + KELVIN)**4))

        masque = self.masque_ceramique(t) if callable(self.masque_ceramique) else self.masque_ceramique
        perte_haut = np.where(masque, contact.h_haut * (contact.T_puits - T), 0.0)
        perte_bas = amb.h_bas_2d * (amb.T_amb - T)
        Q_vol = (source_fn(t, T) + perte_haut + perte_bas) / e
        return ((dT + Q_vol) / rc).ravel()


def construire_cas(cfg: Config, l_ext: float) -> dict:
    """Grille, e(x), sources 2D par spot, masques et positions TC pour un tube
    dépassant le connecteur de ``l_ext`` de chaque côté."""
    lam = cfg.geometrie["laminate"]
    L0 = float(lam["longueur"])
    nx0 = int(round(L0 / DX)) + 1
    n_ext = int(round(l_ext / DX))
    couches = construire_couches(cfg)
    g0 = construire_grille(cfg, nx=nx0, ny=NY, nz=NZ)
    z_split = lam["epaisseur_sup"] + lam["epaisseur_film"] / 2
    haut = g0.z < z_split                     # connecteur (laminé sup + twill)

    cfg1 = copy.deepcopy(cfg)
    cfg1.geometrie["laminate"]["longueur"] = L0 + 2 * l_ext
    g1 = construire_grille(cfg1, nx=nx0 + 2 * n_ext, ny=NY, nz=NZ)
    assert abs(g1.dx - g0.dx) < 1e-9

    centres = [float(s["centre_x"]) for s in charger_yaml(g.SPEC_REF)["spots"]]
    P, masques = [], []
    for xc in centres:
        Q0 = source_spot(g0, cfg, couches, COURANT, xc, facteur_couplage=g.FACTEUR, decalage_x=0.0)
        P_haut = Q0[:, :, haut].sum(axis=2) * g0.dz
        if n_ext == 0:
            P_bas = Q0[:, :, ~haut].sum(axis=2) * g0.dz
        else:
            Q1 = source_spot(g1, cfg1, couches, COURANT, xc + l_ext,
                             facteur_couplage=g.FACTEUR, decalage_x=0.0)
            P_bas = Q1[:, :, ~haut].sum(axis=2) * g1.dz
        Pc = P_bas.copy() if n_ext else P_bas + P_haut
        if n_ext:
            Pc[n_ext:n_ext + nx0] += P_haut
        P.append(Pc)
        m = np.zeros((g1.nx, g1.ny), dtype=bool)
        m[n_ext:n_ext + nx0] = masque_empreinte_cfc(g0, cfg, xc)
        masques.append(m)

    e_x = np.full(g1.nx, E_TUBE)
    e_x[n_ext:n_ext + nx0] = g0.epaisseur
    return dict(grille=g1, e_x=e_x, P=P, masques=masques,
                x_c=[xc + l_ext for xc in centres],
                tc={f"TC{i + 1}": x + l_ext for i, x in enumerate(X_TC)},
                l_ext=l_ext, cfg=cfg)


def simuler_cycle(cas: dict) -> dict:
    """Cycle #64 : chauffe -> 390 °C au point chaud (x_c, y=0), refroidit ->
    Tg au même point, avance. Renvoie séries TC + métriques par passe."""
    cfg, grille = cas["cfg"], cas["grille"]
    T = np.full(grille.nx * grille.ny, g.T_AMB)
    t_all, series = [np.array([0.0])], {n: [np.array([g.T_AMB])] for n in cas["tc"]}
    passes, t0 = [], 0.0
    for i, (P, m, xc) in enumerate(zip(cas["P"], cas["masques"], cas["x_c"])):
        s = SolveurTubeAllonge(grille, cfg.materiau, cfg.ambiant, cfg.contact,
                               masque_ceramique=m, e_x=cas["e_x"])
        th = np.arange(0.0, g.CAP_CHAUFFE + g.DT_CHAUFFE / 2, g.DT_CHAUFFE)
        sh = s.simuler(lambda t: P, (0.0, g.CAP_CHAUFFE), t_eval=th, T_initial=T)
        pc = s.serie_temporelle(sh, xc, 0.0)
        t_cut, j = g.premier_passage_montee(sh.t, pc, g.T_PROCEDE)
        dwell = t_cut if not np.isnan(t_cut) else g.CAP_CHAUFFE
        T = g._interp_champ(sh.y, sh.t, dwell, j)
        tc_ = np.arange(0.0, g.CAP_REFROID + g.DT_REFROID / 2, g.DT_REFROID)
        sc = s.simuler(lambda t: np.zeros_like(P), (0.0, g.CAP_REFROID), t_eval=tc_, T_initial=T)
        pcc = s.serie_temporelle(sc, xc, 0.0)
        t_ref, jr = g.premier_passage_descente(sc.t, pcc, g.T_REFROID)
        refroid = t_ref if not np.isnan(t_ref) else g.CAP_REFROID
        pics = {}
        for sol, dur, tt in ((sh, dwell, sh.t), (sc, refroid, sc.t)):
            msk = tt <= dur + 1e-9
            t_all.append(t0 + tt[msk])
            for n, x in cas["tc"].items():
                v = s.serie_temporelle(sol, x, 0.0)[msk]
                series[n].append(v)
                pics[n] = max(pics.get(n, -1e9), float(v.max()))
            t0 += dur
        T = g._interp_champ(sc.y, sc.t, refroid, jr)
        passes.append(dict(dwell=dwell, refroid=refroid, pics=pics))
    return dict(t=np.concatenate(t_all),
                series={n: np.concatenate(v) for n, v in series.items()},
                passes=passes)


def auto_test() -> float:
    """e uniforme, L_EXT=0 : doit redonner SolveurThermique2D (Δ max en °C)."""
    cfg = config_tube(0.0)
    cas = construire_cas(cfg, 0.0)
    kw = dict(masque_ceramique=cas["masques"][0])
    a = SolveurThermique2D(cas["grille"], cfg.materiau, cfg.ambiant, cfg.contact, **kw)
    b = SolveurTubeAllonge(cas["grille"], cfg.materiau, cfg.ambiant, cfg.contact, e_x=cas["e_x"], **kw)
    P = cas["P"][0]
    te = np.arange(0.0, 20.01, 1.0)
    ya = a.simuler(lambda t: P, (0, 20), t_eval=te).y
    yb = b.simuler(lambda t: P, (0, 20), t_eval=te).y
    return float(np.abs(ya - yb).max())


def main():
    lignes = []
    def log(s=""):
        print(s); lignes.append(s)

    d = auto_test()
    log(f"auto-test (e uniforme, L_EXT=0) : |Δ| max = {d:.2e} °C")
    assert d < 1e-6, "le solveur à e(x) ne redonne pas le solveur d'origine"

    runs = {}
    for l_ext in L_EXTS:
        runs[f"L+{l_ext*1e3:.0f}"] = simuler_cycle(construire_cas(config_tube(0.0), l_ext))
    runs["ref h_bord_x0=125"] = simuler_cycle(construire_cas(config_tube(125.0), 0.0))

    log(f"\nCycle #64 à {COURANT:.0f} A, paroi tube {E_TUBE*1e3:.2f} mm, chants libres sauf mention.")
    log("L+0 = tube 120 mm (= connecteur) ; L+30 = 180 mm ; L+60 = 240 mm (tube réel).\n")
    noms = list(runs)
    for n in noms:
        p = runs[n]["passes"]
        log(f"[{n}] dwell (s) : " + " / ".join(f"{q['dwell']:.1f}" for q in p)
            + "   refroid. (s) : " + " / ".join(f"{q['refroid']:.0f}" for q in p)
            + f"   cycle total {sum(q['dwell'] + q['refroid'] for q in p):.0f} s")
    log("\nPic par TC sur tout le cycle (°C) :")
    log("TC   " + "".join(f"{n:>20s}" for n in noms))
    for tc in ("TC1", "TC2", "TC3", "TC4", "TC5"):
        log(f"{tc:5s}" + "".join(f"{runs[n]['series'][tc].max():20.1f}" for n in noms))
    base = runs["L+0"]
    log("\nÉcart au tube 120 mm (°C), pic par TC :")
    for n in noms[1:]:
        log(f"  {n:18s}" + "  ".join(
            f"{tc} {runs[n]['series'][tc].max() - base['series'][tc].max():+6.1f}"
            for tc in ("TC1", "TC2", "TC3", "TC4", "TC5")))

    OUT_LOG.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    tracer(runs)


def tracer(runs):
    coul = [g.OKABE_ITO[c] for c in ("noir", "bleu", "vert", "orange", "vermillon")]
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 6.4), sharex=False,
                             gridspec_kw=dict(height_ratios=[1.35, 1.0], hspace=0.38))
    ax = axes[0]
    styles = {"L+0": "-", "L+60": "--"}
    for n, ls in styles.items():
        r = runs[n]
        for c, tc in zip(coul, ("TC1", "TC2", "TC3", "TC4", "TC5")):
            ax.plot(r["t"], r["series"][tc], ls, color=c, lw=1.0 if ls == "-" else 1.2,
                    label=tc if n == "L+0" else None)
    ax.axhline(g.T_FUSION, color="0.5", lw=0.6, ls=":")
    ax.text(5, g.T_FUSION + 4, "Tf 337 °C", fontsize=6.5, color="0.4")
    ax.set_xlabel("temps (s)")
    ax.set_ylabel("T interface (°C)")
    ax.set_title(f"Cycle semi-statique {COURANT:.0f} A — trait plein : tube 120 mm ; "
                 "tirets : tube 240 mm", fontsize=8.6)
    ax.legend(ncol=5, loc="upper right", frameon=False)

    ax = axes[1]
    tcs = ("TC1", "TC2", "TC3", "TC4", "TC5")
    xs = np.arange(len(tcs))
    cmp = [("L+30", "tube 180 mm", g.OKABE_ITO["bleu"]),
           ("L+60", "tube 240 mm", g.OKABE_ITO["vermillon"])]
    w = 0.36
    base = runs["L+0"]["series"]
    for k, (n, lab, c) in enumerate(cmp):
        d = [runs[n]["series"][tc].max() - base[tc].max() for tc in tcs]
        ax.bar(xs + (k - 0.5) * w, d, w, color=c, label=lab)
    ax.axhline(0, color="0.2", lw=0.6)
    ax.set_xticks(xs, [f"{tc}\nx={x*1e3:.0f}" for tc, x in zip(tcs, X_TC)])
    ax.set_ylabel("Δ pic vs tube 120 mm (°C)")
    ax.set_title("Écart de pic par thermocouple (cycle complet, même critère de coupure)",
                 fontsize=8.6)
    ax.legend(frameon=False, loc="lower center", ncol=2)
    for s in ("top", "right"):
        for a in axes:
            a.spines[s].set_visible(False)
    g.savefig(fig, OUT_FIG)
    plt.close(fig)


if __name__ == "__main__":
    main()
