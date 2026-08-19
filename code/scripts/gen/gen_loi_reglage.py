"""Loi de réglage atelier — durée de chauffe recommandée vs courant.

Exploite le jumeau (domaine validé). Pour chaque courant, la durée pour amener
le POINT CHAUD (lobe du M) à la cible procédé 390 °C, encadrée par la fusion
(337, borne basse) et la dégradation (450, borne haute). Comme le taux ∝ I²
(loi validée), la durée pour atteindre une température ∝ 1/I² : on ajuste
t(I) = A / I² et on donne un petit tableau de réglage.

Sortie : docs/modele/figures/fig_loi_reglage.png
"""
import sys
from pathlib import Path
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # scripts/ (import _style)
from _style import apply_style, savefig  # noqa: E402  (style partagé, issue #17)
apply_style(**{
    "font.size": 11, "axes.labelsize": 12, "axes.titlesize": 12.5,
    "savefig.pad_inches": 0.06,
})
from jumeau.materiaux import Config
from jumeau.procede import Essai
from jumeau.em.source_joule import source_spot

OUT = R / "biblio" / "modele" / "figures" / "fig_loi_reglage.png"
FACTEUR = 6.0123
T_FUSION, T_PROCEDE, T_DEGRAD = 337.0, 390.0, 450.0
T_HEAT = 45.0
COURANTS = np.arange(180, 301, 10.0)     # A (au-dessus de ~180 A = seuil de soudage)
cfg = Config.charger(R / "code" / "config")


def t_seuils(courant):
    e = Essai(cfg, R / "code" / "config" / "essais" / "exp7_200A.yaml", nx=61, ny=21, nz=15,
              facteur_couplage=FACTEUR, decalage_x=0.0, racine=R)
    e.spec["duree_chauffe"] = e.spec["duree_totale"] = T_HEAT
    e.spots[0]["t_fin"] = T_HEAT
    e._Q_spots = [source_spot(e.grille, cfg, e.couches, courant, float(s["centre_x"]),
                              facteur_couplage=FACTEUR, decalage_x=0.0) for s in e.spots]
    e._P_spots_2d = [Q.sum(axis=2) * e.grille.dz for Q in e._Q_spots]
    sv, sol = e.simuler(modele="2D")
    t = sol.t
    Te = sv.serie_temporelle(sol, 0.060, 0.0, "interface")

    def tt(seuil):
        idx = np.where(Te >= seuil)[0]
        if not len(idx) or idx[0] == 0:
            return np.nan
        i = idx[0]
        return float(t[i - 1] + (seuil - Te[i - 1]) / (Te[i] - Te[i - 1]) * (t[i] - t[i - 1]))
    return tt(T_FUSION), tt(T_PROCEDE), tt(T_DEGRAD)


tw, tp, td = np.array([t_seuils(float(I)) for I in COURANTS]).T
ok = ~np.isnan(tp)

# ajustement t_procédé = A / I^2 (taux ∝ I²)
A = np.nanmedian(tp[ok] * COURANTS[ok] ** 2)
tfit = A / COURANTS ** 2

fig, ax = plt.subplots(figsize=(8.4, 5.2))
ax.fill_between(COURANTS, tw, td, color="#B7E4C7", alpha=0.75, label="Fenêtre de soudage — point chaud 337-450 °C")
ax.plot(COURANTS, tp, "-o", color="#1B7837", lw=2.2, ms=5, label="Durée recommandée — cible procédé 390 °C (point chaud)")
ax.plot(COURANTS, tw, "-", color="#0072B2", lw=1.3, label="Borne basse — fusion 337 °C (point chaud)")
ax.plot(COURANTS, td, "-", color="#C1272D", lw=1.3, label="Borne haute — dégradation 450 °C (point chaud)")
ax.plot(COURANTS, tfit, ":", color="0.35", lw=1.8, label=f"Ajustement $t = {A:.0f}/I^2$ (taux ∝ I²)")

# petit tableau de réglage
lignes = ["Réglage (cible 390 °C) :", "  I (A)   t (s)   fenêtre"]
for I in (200, 220, 250, 280, 300):
    k = int(np.argmin(np.abs(COURANTS - I)))
    if not np.isnan(tp[k]):
        lignes.append(f"  {I:3d}    {tp[k]:4.0f}    {tw[k]:2.0f}–{td[k]:2.0f} s")
ax.text(0.97, 0.96, "\n".join(lignes), transform=ax.transAxes, ha="right", va="top",
        family="monospace", fontsize=8.5,
        bbox=dict(facecolor="white", edgecolor="0.6", pad=5))

ax.set_xlabel("Courant du générateur $I$ (A)")
ax.set_ylabel("Durée de chauffe (s)")
ax.set_title("Loi de réglage atelier — durée vs courant (point chaud)")
ax.set_ylim(0, np.nanmax(td[ok]) * 1.1)
ax.legend(loc="lower left", fontsize=9)
ax.text(0.5, -0.15, "Point chaud = lobe du M (soude en 1er). Frontière dégradation conservatrice "
        "(modèle sur-estime le bord ~50 °C).", transform=ax.transAxes, ha="center",
        fontsize=8, color="0.4")
savefig(fig, OUT)
print("saved", OUT, "| A =", round(A))
