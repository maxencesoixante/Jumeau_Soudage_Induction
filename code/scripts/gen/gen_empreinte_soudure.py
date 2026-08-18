"""Empreinte de soudure — carte T(x,y) à l'interface pour un réglage donné.

Exploite le jumeau (domaine validé). Pour un couple (courant, durée de chauffe)
choisi DANS la fenêtre de soudage, on affiche la carte de température à
l'interface au pic, avec les contours fusion (337) / cible procédé (390) /
dégradation (450) : ça montre la ZONE effectivement soudée (les lobes du M au
bord) et confirme que le centre reste froid (spot fixe).

Sortie : docs/modele/figures/fig_empreinte_soudure.png
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
    "font.size": 11, "axes.labelsize": 11.5, "axes.titlesize": 11,
    "savefig.pad_inches": 0.06,
})
from jumeau.materiaux import Config
from jumeau.procede import Essai
from jumeau.em.source_joule import source_spot

OUT = R / "biblio" / "modele" / "figures" / "fig_empreinte_soudure.png"
FACTEUR = 6.0123
T_FUSION, T_PROCEDE, T_DEGRAD = 337.0, 390.0, 450.0
# Deux réglages dans la fenêtre de soudage (cf. fig_fenetre_soudage) :
REGLAGES = [(200.0, 30.0), (250.0, 14.0)]   # (courant A, durée s) -> ~cible procédé au point chaud

cfg = Config.charger(R / "code" / "config")


def champ_interface(courant, duree):
    e = Essai(cfg, R / "code" / "config" / "essais" / "exp7_200A.yaml", nx=81, ny=41, nz=15,
              facteur_couplage=FACTEUR, decalage_x=0.0, racine=R)
    e.spec["duree_chauffe"] = duree
    e.spec["duree_totale"] = duree
    e.spots[0]["t_fin"] = duree
    e._Q_spots = [source_spot(e.grille, cfg, e.couches, courant, float(s["centre_x"]),
                              facteur_couplage=FACTEUR, decalage_x=0.0) for s in e.spots]
    e._P_spots_2d = [Q.sum(axis=2) * e.grille.dz for Q in e._Q_spots]
    sv, sol = e.simuler(modele="2D")
    champs = np.array([sv.resultat_2d(sol, i) for i in range(sol.t.size)])  # (nt,nx,ny)
    Tmax = champs.max(axis=0)                                               # pic par nœud
    g = e.grille
    return g.x * 1e3, g.y * 1e3, Tmax


fig, axes = plt.subplots(2, 1, figsize=(7.6, 6.4), sharex=True)
vmax = T_DEGRAD + 60
for ax, (I, dt) in zip(axes, REGLAGES):
    x, y, Tmax = champ_interface(I, dt)
    X, Y = np.meshgrid(x, y, indexing="ij")
    im = ax.pcolormesh(X, Y, Tmax, cmap="inferno", vmin=25, vmax=vmax, shading="gouraud")
    cs = ax.contour(X, Y, Tmax, levels=[T_FUSION, T_PROCEDE, T_DEGRAD],
                    colors=["#4DA6FF", "white", "#FF5555"], linewidths=[1.3, 1.3, 1.6])
    ax.clabel(cs, fmt={T_FUSION: "337", T_PROCEDE: "390", T_DEGRAD: "450"}, fontsize=7)
    for yy in (0, 10, 20, 30, 40):
        ax.plot(60, yy, "x", color="white", ms=5, mew=1.2)
    soudee = (Tmax >= T_FUSION).sum() / Tmax.size * 100
    ax.set_title(f"{I:.0f} A, {dt:.0f} s — zone ≥ fusion : {soudee:.0f} % de l'interface",
                 fontsize=10)
    ax.set_ylabel("Largeur $y$ (mm)")
    ax.set_aspect("equal")
axes[-1].set_xlabel("Longueur $x$ (mm)")
cb = fig.colorbar(im, ax=axes, fraction=0.03, pad=0.02)
cb.set_label("Température d'interface au pic (°C)")
fig.suptitle("Empreinte de soudure — carte d'interface (spot fixe centré x=60)",
             fontsize=12, fontweight="bold", y=0.98)
savefig(fig, OUT)
print("saved", OUT)
