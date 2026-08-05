"""Fenêtre de soudage — abaque opératoire (courant × durée de chauffe).

Exploite le jumeau dans son DOMAINE VALIDÉ (pic/plateau + forme + loi I²).
Avec un SPOT FIXE, le point qui soude ET qui risque la dégradation est le POINT
CHAUD (lobe du M au bord, y=0) — le centre (creux du M) reste trop froid (c'est
pourquoi le procédé réel est semi-statique / balayé). L'abaque raisonne donc sur
le pic d'interface au point chaud, en fonction de (courant, durée de chauffe).

Zones : sous-chauffe (pic < fusion) / SOUDAGE (fusion ≤ pic < dégradation) /
dégradation (pic ≥ 450 °C). Ancrages : essais mesurés 150/200/250 A.

NB : le modèle SUR-ESTIME le pic au bord d'environ ~50 °C (biais validé) → la
frontière de dégradation est CONSERVATRICE (côté sûr) ; abaque indicatif ±~30-50 °C.

Sortie : docs/figures/fig_fenetre_soudage.png
"""
import sys
from pathlib import Path
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

R = Path("/Users/maxencedubois/PycharmProjects/Jumeau_Soudage_Induction")
sys.path.insert(0, str(R / "src"))
from _style import apply_style, savefig  # noqa: E402  (style partagé, issue #17)
apply_style(**{
    "font.size": 11, "axes.labelsize": 12, "axes.titlesize": 12.5,
    "legend.fontsize": 10, "savefig.pad_inches": 0.06,
})

from jumeau.materiaux import Config
from jumeau.procede import Essai
from jumeau.em.source_joule import source_spot

OUT = R / "docs" / "figures" / "fig_fenetre_soudage.png"
FACTEUR = 6.0123
T_FUSION, T_PROCEDE, T_DEGRAD = 337.0, 390.0, 450.0
T_HEAT = 40.0               # durée de chauffe continue simulée (s)
COURANTS = np.arange(100, 301, 20)   # A

cfg = Config.charger(R / "config")
TAMB = 25.0


def serie_bord(courant):
    """T(t) d'interface au POINT CHAUD (lobe M, x=60, y=0), chauffe continue."""
    e = Essai(cfg, R / "config" / "essais" / "exp7_200A.yaml", nx=61, ny=21, nz=15,
              facteur_couplage=FACTEUR, decalage_x=0.0, racine=R)
    e.spec["duree_chauffe"] = T_HEAT
    e.spec["duree_totale"] = T_HEAT
    e.spots[0]["t_fin"] = T_HEAT
    e._Q_spots = [source_spot(e.grille, cfg, e.couches, courant, float(s["centre_x"]),
                              facteur_couplage=FACTEUR, decalage_x=0.0) for s in e.spots]
    e._P_spots_2d = [Q.sum(axis=2) * e.grille.dz for Q in e._Q_spots]
    sv, sol = e.simuler(modele="2D")
    return sol.t, sv.serie_temporelle(sol, 0.060, 0.0, "interface")


def premier_passage(t, T, seuil):
    """Premier instant où T franchit le seuil (interp linéaire), ou nan."""
    idx = np.where(T >= seuil)[0]
    if len(idx) == 0:
        return np.nan
    i = idx[0]
    if i == 0:
        return float(t[0])
    t0, t1, T0, T1 = t[i - 1], t[i], T[i - 1], T[i]
    return float(t0 + (seuil - T0) / (T1 - T0) * (t1 - t0))


t_weld, t_proc, t_degrade = [], [], []
for I in COURANTS:
    t, Te = serie_bord(float(I))
    t_weld.append(premier_passage(t, Te, T_FUSION))       # point chaud atteint fusion
    t_proc.append(premier_passage(t, Te, T_PROCEDE))      # point chaud atteint cible procédé
    t_degrade.append(premier_passage(t, Te, T_DEGRAD))    # point chaud atteint dégradation
    print(f"I={I:3.0f} A : t_fusion={t_weld[-1]!s:>6.6} "
          f"t_procédé={t_proc[-1]!s:>6.6} t_dégrad={t_degrade[-1]!s:>6.6}")

t_weld = np.array(t_weld, float)
t_proc = np.array(t_proc, float)
t_degrade = np.array(t_degrade, float)

# ----------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.2, 5.2))
tmax = T_HEAT

# zones (bandes continues entre les frontières ; nan → jamais atteint = tmax)
tw = np.where(np.isnan(t_weld), tmax, t_weld)
td = np.where(np.isnan(t_degrade), tmax, t_degrade)
ax.fill_betweenx(COURANTS, 0, tw, color="#D9E8F5", zorder=0)        # sous-chauffe
ax.fill_betweenx(COURANTS, tw, td, color="#B7E4C7", zorder=0)       # soudage
ax.fill_betweenx(COURANTS, td, tmax, color="#F4C7C3", zorder=0)     # dégradation

# frontières (courbes)
ax.plot(t_weld, COURANTS, "-o", color="#0072B2", lw=2, ms=4, label="Point chaud (lobe M, bord) → fusion 337 °C : début soudage")
ax.plot(t_proc, COURANTS, "--", color="#1B7837", lw=1.6, label="Point chaud → cible procédé 390 °C")
ax.plot(t_degrade, COURANTS, "-s", color="#C1272D", lw=2, ms=4, label="Point chaud → dégradation PEKK 450 °C")

# ancrages mesurés (pics réels exp7) — durée de chauffe mesurée ~ approx.
anchors = {150: 57, 200: 18, 250: 10}   # durée de chauffe mesurée (README exp7 / baseline)
for I, tt in anchors.items():
    ax.scatter([tt], [I], marker="*", s=180, color="k", zorder=5,
               label="Essais réalisés exp7 (coupés sous fusion, réutilisables)" if I == 150 else None)

ax.text(2, 285, "SOUS-CHAUFFE", color="#2166AC", fontsize=9, fontweight="bold")
ax.text(0.40 * tmax, 150, "SOUDAGE", color="#1B7837", fontsize=11, fontweight="bold", rotation=8)
ax.text(0.80 * tmax, 285, "DÉGRADATION\n(bord)", color="#A50026", fontsize=9, fontweight="bold", ha="center")

ax.set_xlim(0, tmax); ax.set_ylim(COURANTS[0] - 10, COURANTS[-1] + 10)
ax.set_xlabel("Durée de chauffe (s)")
ax.set_ylabel("Courant du générateur $I$ (A)")
ax.set_title("Fenêtre de soudage — abaque opératoire (spot fixe, θ* de référence)")
ax.legend(loc="lower right", framealpha=0.92, fontsize=9)
ax.text(0.5, -0.16,
        "Point chaud = pic d'interface (lobe du M, spot fixe). Le modèle sur-estime le bord "
        "~50 °C → frontière dégradation CONSERVATRICE. Abaque indicatif (±~30-50 °C).",
        transform=ax.transAxes, ha="center", fontsize=8, color="0.4")
savefig(fig, OUT)
print("saved", OUT)
