"""Cycle de chauffe PARFAIT en soudage semi-statique — chauffe/refroidit/avance.

Semi-statique = spot fixe qui avance de 30 mm par passe, 4 passes (positions
``empreintes.centres_pas30`` de ``geometrie.yaml`` — mêmes centres que les
essais réels serieA_A-1/serieB_B-2). « Parfait » = schéma RÉEL serieA/B :
chaque passe (1) CHAUFFE le point chaud d'interface (lobe du M au bord, y=0,
sous le spot ACTIF) jusqu'à la cible procédé 390 °C, (2) COUPE la source et
REFROIDIT ce même point jusqu'à ≤ Tg (159 °C par défaut, cf. T_REFROID : sous
Tg le joint est figé/rigide), (3) AVANCE au spot suivant. Après la
4e passe : chauffe->390 puis refroidissement final. C'est exactement le
patron temporel de serieA_A-1.yaml (passe1 [0,79 s], passe2 [393,473 s], soit
~314 s de refroidissement ENTRE les passes) — le refroidissement à 120 °C
efface le préchauffage, les dwells de chauffe redeviennent proches d'un
départ froid à chaque passe (PAS d'advance-on-consigne sans coupure, qui
était le schéma d'une version antérieure de ce script).

Implémentation (pas de modification de ``jumeau.procede``/``thermique`` — on
pilote le solveur 2D nous-mêmes, pas de flag), par passe ``i`` :
  1. sous-phase CHAUFFE : simulation continue (source pleine puissance, masque
     MFC posé au spot ``i``) à partir du champ T final de la sous-phase
     précédente, fenêtre CAP_CHAUFFE (300 s) ; franchissement (montée) de
     390 °C au point chaud -> interpolation linéaire (temps + champ 2D complet,
     warm-start exact de la sous-phase suivante). Si 390 °C n'est jamais
     atteint dans CAP_CHAUFFE -> passe plafonnée (repli honnête, « NE SOUDE
     PAS », signalé dans le tableau) ;
  2. sous-phase REFROIDISSEMENT : source coupée, masque MFC du MÊME spot ``i``
     conservé (pression maintenue avant de lever/avancer, cf.
     ``jumeau.procede.Essai.masque_fn``), fenêtre CAP_REFROID (600 s) ;
     franchissement (descente) de T_REFROID (159 °C = Tg par défaut) au MÊME point chaud -> interpolation
     linéaire, warm-start de la passe suivante ;
  3. avance : la passe ``i+1`` réutilise le champ 2D complet issu de (2).

Modèle 2D (facteur_couplage=6.0123, θ* canonique) — PAS le 3D (non recalibré
à ce facteur, sur-prédit ~+130 °C, cf. mission). BIAIS CONNU (cf. docstring
``gen_fenetre_soudage.py``) : le modèle SUR-ESTIME le point chaud de bord
d'environ ~50 °C -> une cible modèle de 390 °C correspond à un pic réel
d'environ ~340 °C, tout juste au-dessus de la fusion (337 °C) = régime de
soudage propre, PAS de dégradation réelle. Le tableau et les figures
utilisent quand même les seuils modèle (337/390/450) tels quels : ce sont les
seuils AUXQUELS RÉAGIT LE MODÈLE, la lecture physique doit se faire à travers
le biais rappelé en légende. La marge à 450 °C est calculée en laissant
tourner la même simulation de chauffe AU-DELÀ de 390 °C (dans la fenêtre
CAP_CHAUFFE) — c'est une marge diagnostique (si la coupure ratait), PAS ce
qui se produit dans le cycle parfait lui-même (qui coupe pile à 390 °C).

Sortie : biblio/labo/figures/fig_cycle_parfait_semistatique_{I}A.png (une par
courant : 130, 160, 230, 275 A) + un résumé texte (dwell chauffe/temps de
refroidissement/marge) imprimé sur stdout.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import yaml

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # scripts/ (import _style)
from _style import apply_style, savefig, OKABE_ITO  # noqa: E402

apply_style(**{
    "font.size": 8.3, "axes.labelsize": 9.0, "axes.titlesize": 9.3,
    "legend.fontsize": 6.7, "savefig.pad_inches": 0.05,
    "savefig.dpi": 200, "figure.dpi": 200,
    "xtick.labelsize": 7.6, "ytick.labelsize": 7.6,
})

import matplotlib.pyplot as plt  # noqa: E402

from jumeau.materiaux import Config  # noqa: E402
from jumeau.procede import Essai  # noqa: E402
from jumeau.em.source_joule import source_spot  # noqa: E402
from jumeau.thermique.solveur2d import SolveurThermique2D  # noqa: E402

OUT_DIR = R / "biblio" / "labo" / "figures"

FACTEUR = 6.0123           # θ* canonique, modèle 2D (cf. docstring module)
T_FUSION, T_PROCEDE, T_DEGRAD = 337.0, 390.0, 450.0
# Seuil d'avance : « joint assez figé pour repositionner ». DÉFAUT = Tg du PEKK
# (159 °C, datasheet Solvay APC/PEKK-FC) : sous Tg la phase amorphe est vitreuse
# → joint rigide, critère physique adopté (gain ~20–34 % du temps de cycle vs
# 120 °C, cf. fig_cycle_parfait_comparaison_seuil). SEUIL_REFROID=120 → ancien
# critère conservateur (« pièce froide »).
T_REFROID_DEFAUT = 159.0   # °C — Tg PEKK
T_REFROID = float(os.environ.get("SEUIL_REFROID", T_REFROID_DEFAUT))  # °C
TAG_SEUIL = "" if abs(T_REFROID - T_REFROID_DEFAUT) < 1e-6 else f"_seuil{T_REFROID:.0f}"
T_AMB = 25.0
CAP_CHAUFFE = 300.0        # s — plafond de sécurité par sous-phase de chauffe
CAP_REFROID = 600.0        # s — plafond de sécurité par sous-phase de refroidissement
DT_CHAUFFE = 0.25          # s — résolution temporelle chauffe (franchissement 390°C rapide)
DT_REFROID = 1.0           # s — résolution temporelle refroidissement (dynamique lente)
COURANTS = [130.0, 160.0, 230.0, 275.0]  # A

cfg = Config.charger(R / "code" / "config")
# Mode opératoire RÉEL serieA/B : 4 spots, pas 30 mm (centres 15,875 / 45,875 /
# 75,875 / 105,875 mm) + 5 TC natifs (TC1 centre y=20 ; TC2-5 bord y=0). Les 4
# empreintes MFC (31,5 mm en x) se recouvrent → toute la longueur est soudée.
SPEC_REF = R / "code" / "config" / "essais" / "serieA_A-1.yaml"


def construire_essai(courant: float) -> Essai:
    """Essai 2D au mode opératoire réel serieA/B (4 spots pas 30 mm, 5 TC natifs).
    La source Joule est recalculée au ``courant`` demandé ; ``t_debut``/``t_fin``
    du YAML ne sont PAS utilisés (on pilote chauffe/refroidissement/avance)."""
    e = Essai(cfg, SPEC_REF, nx=61, ny=21, nz=15, facteur_couplage=FACTEUR,
              decalage_x=0.0, racine=R)
    e.spec["courant"] = courant
    # TC exactement comme exp9 (dissipation longitudinale) : 5 TC sur la ligne de
    # BORD y=0, x = 0/30/60/90/120 mm. (serieA plaçait TC1 au centre y=20 ; corrigé
    # pour coller au montage exp9 semi-statique, cf. README exp9.)
    e.spec["thermocouples"] = {
        f"TC{i + 1}": {"x": x, "y": 0.0, "z": "interface"}
        for i, x in enumerate((0.0, 0.030, 0.060, 0.090, 0.120))
    }
    e.spec["tc_valides"] = [f"TC{i + 1}" for i in range(5)]
    e._Q_spots = [
        source_spot(e.grille, cfg, e.couches, courant, float(s["centre_x"]),
                    facteur_couplage=FACTEUR, decalage_x=0.0)
        for s in e.spots
    ]
    e._P_spots_2d = [Q.sum(axis=2) * e.grille.dz for Q in e._Q_spots]
    return e


def premier_passage_montee(t: np.ndarray, T: np.ndarray, seuil: float):
    """Premier instant (interp linéaire) où T franchit ``seuil`` PAR LE HAUT
    (montée) ; (nan, None) si jamais."""
    idx = np.where(T >= seuil)[0]
    if len(idx) == 0:
        return float("nan"), None
    j = idx[0]
    if j == 0:
        return float(t[0]), 0
    return float(t[j - 1] + (seuil - T[j - 1]) / (T[j] - T[j - 1]) * (t[j] - t[j - 1])), j


def premier_passage_descente(t: np.ndarray, T: np.ndarray, seuil: float):
    """Premier instant (interp linéaire) où T franchit ``seuil`` PAR LE BAS
    (descente) ; (nan, None) si jamais."""
    idx = np.where(T <= seuil)[0]
    if len(idx) == 0:
        return float("nan"), None
    j = idx[0]
    if j == 0:
        return float(t[0]), 0
    return float(t[j - 1] + (seuil - T[j - 1]) / (T[j] - T[j - 1]) * (t[j] - t[j - 1])), j


def _interp_champ(sol_y: np.ndarray, sol_t: np.ndarray, instant: float, j):
    """Champ 2D complet (raveled) interpolé linéairement à ``instant`` (index
    de bracket ``j`` déjà connu, cf. ``premier_passage_*``)."""
    if j is None:
        return sol_y[:, -1].copy()
    if j == 0:
        return sol_y[:, 0].copy()
    t0, t1 = sol_t[j - 1], sol_t[j]
    w = (instant - t0) / (t1 - t0)
    return (1.0 - w) * sol_y[:, j - 1] + w * sol_y[:, j]


def _serie_a_instant(serie: np.ndarray, sol_t: np.ndarray, instant: float, j):
    if j is None:
        return serie[-1]
    if j == 0:
        return serie[0]
    t0, t1 = sol_t[j - 1], sol_t[j]
    w = (instant - t0) / (t1 - t0)
    return (1.0 - w) * serie[j - 1] + w * serie[j]


def simuler_passe(e: Essai, i_spot: int, T_initial: np.ndarray):
    """Chauffe (->390°C) PUIS refroidit (->120°C) la passe ``i_spot``, même
    spot actif (source + masque MFC) pour les deux sous-phases.

    Renvoie un dict avec, pour chaque sous-phase, le temps global local
    (``t``, débutant à 0), la série du point chaud (``Te``), les séries des 5
    TC (``series_tc``), plus les métadonnées (dwell, atteint, marge_degrad,
    duree_refroid, refroidi, champ_final = warm-start de la passe suivante).
    """
    x_c = float(e.spots[i_spot]["centre_x"])
    P = e._P_spots_2d[i_spot]
    P_nul = np.zeros_like(P)
    solveur = SolveurThermique2D(e.grille, e.cfg.materiau, e.cfg.ambiant, e.cfg.contact,
                                  masque_ceramique=e._masques[i_spot])
    noms_tc = list(e.spec["thermocouples"].keys())
    pos_tc = {n: (float(e.spec["thermocouples"][n]["x"]), float(e.spec["thermocouples"][n]["y"]))
              for n in noms_tc}

    # --- sous-phase CHAUFFE (continue, pas de thermostat intégré) ---
    t_eval_h = np.arange(0.0, CAP_CHAUFFE + DT_CHAUFFE / 2, DT_CHAUFFE)
    sol_h = solveur.simuler(lambda t: P, (0.0, CAP_CHAUFFE), t_eval=t_eval_h, T_initial=T_initial)
    Te_h = solveur.serie_temporelle(sol_h, x_c, 0.0)  # point chaud : lobe M, y=0, sous le spot actif

    t_390, j390 = premier_passage_montee(sol_h.t, Te_h, T_PROCEDE)
    t_450, _ = premier_passage_montee(sol_h.t, Te_h, T_DEGRAD)  # diagnostic (si la source restait ON)
    atteint = not np.isnan(t_390)
    dwell = t_390 if atteint else CAP_CHAUFFE
    marge_degrad = (t_450 - t_390) if (atteint and not np.isnan(t_450)) else float("nan")

    champ_apres_chauffe = _interp_champ(sol_h.y, sol_h.t, dwell, j390)
    mask_h = sol_h.t <= dwell + 1e-9
    t_h = sol_h.t[mask_h]
    if len(t_h) == 0 or t_h[-1] < dwell - 1e-6:
        t_h = np.concatenate([t_h, [dwell]])
    Te_h_tr = Te_h[mask_h]
    if len(Te_h_tr) < len(t_h):
        Te_h_tr = np.concatenate([Te_h_tr, [_serie_a_instant(Te_h, sol_h.t, dwell, j390)]])
    series_tc_h = {}
    for n in noms_tc:
        x, y = pos_tc[n]
        serie_complete = solveur.serie_temporelle(sol_h, x, y)
        serie = serie_complete[mask_h]
        if len(serie) < len(t_h):
            serie = np.concatenate([serie, [_serie_a_instant(serie_complete, sol_h.t, dwell, j390)]])
        series_tc_h[n] = serie

    # --- sous-phase REFROIDISSEMENT (source coupée, MÊME masque = MÊME spot) ---
    t_eval_c = np.arange(0.0, CAP_REFROID + DT_REFROID / 2, DT_REFROID)
    sol_c = solveur.simuler(lambda t: P_nul, (0.0, CAP_REFROID), t_eval=t_eval_c,
                             T_initial=champ_apres_chauffe)
    Te_c = solveur.serie_temporelle(sol_c, x_c, 0.0)

    t_120, j120 = premier_passage_descente(sol_c.t, Te_c, T_REFROID)
    refroidi = not np.isnan(t_120)
    duree_refroid = t_120 if refroidi else CAP_REFROID

    champ_final = _interp_champ(sol_c.y, sol_c.t, duree_refroid, j120)
    mask_c = sol_c.t <= duree_refroid + 1e-9
    t_c = sol_c.t[mask_c]
    if len(t_c) == 0 or t_c[-1] < duree_refroid - 1e-6:
        t_c = np.concatenate([t_c, [duree_refroid]])
    Te_c_tr = Te_c[mask_c]
    if len(Te_c_tr) < len(t_c):
        Te_c_tr = np.concatenate([Te_c_tr, [_serie_a_instant(Te_c, sol_c.t, duree_refroid, j120)]])
    series_tc_c = {}
    for n in noms_tc:
        x, y = pos_tc[n]
        serie_complete = solveur.serie_temporelle(sol_c, x, y)
        serie = serie_complete[mask_c]
        if len(serie) < len(t_c):
            serie = np.concatenate([serie, [_serie_a_instant(serie_complete, sol_c.t, duree_refroid, j120)]])
        series_tc_c[n] = serie

    return dict(x_c=x_c, noms_tc=noms_tc,
                t_h=t_h, Te_h=Te_h_tr, series_tc_h=series_tc_h,
                dwell=dwell, atteint=atteint, marge_degrad=marge_degrad,
                t_c=t_c, Te_c=Te_c_tr, series_tc_c=series_tc_c,
                duree_refroid=duree_refroid, refroidi=refroidi,
                champ_final=champ_final)


def simuler_cycle(courant: float):
    """Simule les 4 passes (chauffe->390 / refroidit->120 / avance)."""
    e = construire_essai(courant)
    noms_tc = list(e.spec["thermocouples"].keys())

    T_field = np.full(e.grille.nx * e.grille.ny, T_AMB)
    t_global = [np.array([0.0])]
    series_global = {n: [np.array([T_AMB])] for n in noms_tc}
    point_chaud_global = [np.array([T_AMB])]
    passes_info = []
    t0 = 0.0

    for i_spot in range(len(e.spots)):
        r = simuler_passe(e, i_spot, T_field)

        for t_loc, Te_loc, series_loc in ((r["t_h"], r["Te_h"], r["series_tc_h"]),
                                           (r["t_c"], r["Te_c"], r["series_tc_c"])):
            t_global.append(t0 + t_loc)
            for n in noms_tc:
                series_global[n].append(series_loc[n])
            point_chaud_global.append(Te_loc)
            t0 += t_loc[-1] if len(t_loc) else 0.0

        t_debut_chauffe = t0 - r["dwell"] - r["duree_refroid"]
        t_fin_chauffe = t_debut_chauffe + r["dwell"]
        t_fin_refroid = t_fin_chauffe + r["duree_refroid"]
        passes_info.append(dict(
            i=i_spot, x_c=r["x_c"],
            t_debut_chauffe=t_debut_chauffe, t_fin_chauffe=t_fin_chauffe, t_fin_refroid=t_fin_refroid,
            dwell=r["dwell"], atteint=r["atteint"], marge_degrad=r["marge_degrad"],
            duree_refroid=r["duree_refroid"], refroidi=r["refroidi"],
        ))
        T_field = r["champ_final"]

    t = np.concatenate(t_global)
    series = {n: np.concatenate(series_global[n]) for n in noms_tc}
    point_chaud = np.concatenate(point_chaud_global)
    return dict(t=t, series=series, point_chaud=point_chaud, passes=passes_info, noms_tc=noms_tc)


# --------------------------------------------------------------------------- #
def tracer_cycle(courant: float, resultat: dict, chemin_out: Path):
    t, series, passes = resultat["t"], resultat["series"], resultat["passes"]
    noms_tc = resultat["noms_tc"]
    point_chaud = resultat["point_chaud"]
    couleurs = [OKABE_ITO[c] for c in ("noir", "bleu", "vert", "orange", "vermillon")]

    fig, ax = plt.subplots(figsize=(9.6, 4.6))

    COUL_CHAUFFE = "#E8E8E8"
    COUL_REFROID = "#F7F7F7"
    for p in passes:
        ax.axvspan(p["t_debut_chauffe"], p["t_fin_chauffe"], color=COUL_CHAUFFE, zorder=0)
        ax.axvspan(p["t_fin_chauffe"], p["t_fin_refroid"], color=COUL_REFROID, zorder=0)

    for nom, coul in zip(noms_tc, couleurs):
        ax.plot(t, series[nom], color=coul, lw=1.1, label=nom)
    ax.plot(t, point_chaud, color="0.25", lw=0.9, ls=(0, (4, 1.6)),
            label="point chaud (contrôle, spot actif)", zorder=2.5)

    for seuil, coul, nom in ((T_FUSION, OKABE_ITO["cyan"], "fusion"),
                              (T_PROCEDE, OKABE_ITO["vert"], "cible"),
                              (T_DEGRAD, OKABE_ITO["vermillon"], "dégrad.")):
        ax.axhline(seuil, color=coul, lw=0.9, ls="--", zorder=1)
    ax.axhline(T_REFROID, color="0.5", lw=0.9, ls=":", zorder=1)

    # deux rangées d'annotations (chauffe en haut, refroid juste dessous) :
    # évite le chevauchement horizontal même quand une fenêtre est étroite
    # (fort courant -> dwell court).
    Y_TOP = 560.0
    Y_ANNOT_CHAUFFE = 528.0
    Y_ANNOT_REFROID = 500.0
    for k, p in enumerate(passes):
        milieu_ch = 0.5 * (p["t_debut_chauffe"] + p["t_fin_chauffe"])
        milieu_rf = 0.5 * (p["t_fin_chauffe"] + p["t_fin_refroid"])
        marque = "!" if not p["atteint"] else ""
        ax.annotate(f"P{k + 1} ch. {p['dwell']:.0f}s{marque}",
                    xy=(milieu_ch, Y_ANNOT_CHAUFFE), ha="center", va="center", fontsize=5.4, color="0.15")
        marque_r = "!" if not p["refroidi"] else ""
        ax.annotate(f"refr. {p['duree_refroid']:.0f}s{marque_r}",
                    xy=(milieu_rf, Y_ANNOT_REFROID), ha="center", va="center", fontsize=5.4, color="0.35")
        ax.axvline(p["t_fin_chauffe"], color="0.65", lw=0.5, ls=":", zorder=1)
        ax.axvline(p["t_fin_refroid"], color="0.4", lw=0.6, ls="-", zorder=1)

    ax.set_xlim(0, t[-1])
    ax.set_ylim(0, Y_TOP)
    ax.set_xlabel("Temps (s)")
    ax.set_ylabel("Température (°C)")
    ax.set_title(f"Cycle de chauffe parfait — semi-statique {len(passes)} passes — $I$ = {courant:.0f} A "
                 f"(2D, $\\theta^*$, chauffe$\\to$390°C / refroid.$\\to${T_REFROID:.0f}°C / avance)", pad=22)
    ax.legend(loc="lower center", ncol=7, framealpha=0.92, fontsize=5.9,
              bbox_to_anchor=(0.5, 1.005), columnspacing=0.9, handlelength=1.4,
              handletextpad=0.4, borderaxespad=0.12)
    legende_bas = (
        "Chaque passe : chauffe (fond gris) jusqu'à 390 °C au point chaud (lobe M, bord y=0, spot actif),\n"
        f"puis coupure + refroidissement (fond clair) jusqu'à {T_REFROID:.0f} °C, puis avance.\n"
        "Biais connu : le modèle sur-estime le bord d'interface d'~50 °C -> 390 °C modèle "
        "$\\approx$ 340 °C réel (soudage propre).\n"
        "TC1–TC5 = ligne de bord y=0, x=0/30/60/90/120 mm (comme exp9 semi-statique)."
    )
    ax.text(0.5, -0.24, legende_bas, transform=ax.transAxes, ha="center", va="top",
            fontsize=6.0, color="0.35", linespacing=1.55)
    fig.tight_layout(rect=(0, 0.10, 1, 1))
    chemins = savefig(fig, chemin_out)
    plt.close(fig)
    return chemins


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    from PIL import Image

    resume = []
    for I in COURANTS:
        print(f"\n=== I = {I:.0f} A ===")
        res = simuler_cycle(I)
        for p in res["passes"]:
            etat_ch = "atteint" if p["atteint"] else "JAMAIS atteint (plafond CAP, NE SOUDE PAS)"
            etat_rf = "atteint" if p["refroidi"] else "JAMAIS atteint (plafond CAP)"
            marge = f"{p['marge_degrad']:.1f} s" if not np.isnan(p["marge_degrad"]) else "n/a"
            print(f"  passe {p['i'] + 1} (x={p['x_c'] * 1000:.1f} mm) : "
                  f"chauffe={p['dwell']:6.1f} s [390°C {etat_ch}]  "
                  f"refroid.={p['duree_refroid']:6.1f} s [120°C {etat_rf}]  "
                  f"marge->450°C (si non coupé): {marge}")
        duree_totale = res["t"][-1]
        toutes_atteintes = all(p["atteint"] for p in res["passes"])
        marge_min = min((p["marge_degrad"] for p in res["passes"] if not np.isnan(p["marge_degrad"])),
                         default=float("nan"))
        print(f"  durée totale du cycle (4 passes, chauffe+refroid incl.) : {duree_totale:.1f} s")
        print(f"  soude (390°C atteint aux 4 passes) : {'OUI' if toutes_atteintes else 'NON'}")
        print(f"  marge minimale à 450°C (sur les 4 passes) : "
              f"{marge_min:.1f} s" if not np.isnan(marge_min) else "  marge minimale à 450°C : n/a")

        out = OUT_DIR / f"fig_cycle_parfait_semistatique_{I:.0f}A{TAG_SEUIL}.png"
        chemins = tracer_cycle(I, res, out)
        for c in chemins:
            if c.suffix.lower() == ".png":
                w, h = Image.open(c).size
                print(f"  figure : {c}  ({w}x{h} px)")
            else:
                print("  figure :", c)
        resume.append((I, res, toutes_atteintes, marge_min, duree_totale))

    print("\n=== Résumé ===")
    print(f"{'I (A)':>6} | {'chauffe par passe (s)':>36} | {'refroid. par passe (s)':>36} | "
          f"{'durée totale':>13} | {'soude?':>7} | {'marge min ->450°C':>18}")
    for I, res, ok, marge_min, duree in resume:
        ch = " ".join(f"{p['dwell']:6.1f}" for p in res["passes"])
        rf = " ".join(f"{p['duree_refroid']:6.1f}" for p in res["passes"])
        marge_s = f"{marge_min:.1f} s" if not np.isnan(marge_min) else "n/a"
        print(f"{I:6.0f} | {ch:>36} | {rf:>36} | {duree:11.1f} s | "
              f"{'OUI' if ok else 'NON':>7} | {marge_s:>18}")
