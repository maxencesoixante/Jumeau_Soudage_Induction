"""Procédé semi-statique — balayage du spot le long du joint (4 dwells, pas 30 mm).

Exploite le jumeau (domaine validé). On simule le procédé RÉEL : la bobine+MFC
s'arrête successivement à x=15,9 / 45,9 / 75,9 / 105,9 mm (empreintes pas 30 mm),
chaque dwell chauffant le joint localement. On affiche la carte du PIC de
température à l'interface sur tout le procédé (Tmax par nœud) = la « piste »
effectivement soudée le long de la longueur.

Enseignement attendu : chaque dwell soude les DEUX bords (lobes du M) à sa
position → la piste soudée est constituée de deux RAILS le long des chants, le
centre restant froid (cohérent avec l'empreinte à spot fixe).

Sortie : docs/figures/fig_procede_semistatique.png
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
    "font.size": 11, "axes.labelsize": 11.5, "axes.titlesize": 12,
    "savefig.pad_inches": 0.06,
})
from jumeau.materiaux import Config
from jumeau.procede import Essai
from jumeau.em.source_joule import source_spot

OUT = R / "docs" / "figures" / "fig_procede_semistatique.png"
FACTEUR = 6.0123
COURANT = 250.0
DWELL = 15.0                          # durée par dwell (s) — dans la fenêtre de soudage
CENTRES = [0.015875, 0.045875, 0.075875, 0.105875]   # empreintes pas 30 mm (config)
T_FUSION, T_PROCEDE, T_DEGRAD = 337.0, 390.0, 450.0

cfg = Config.charger(R / "config")
e = Essai(cfg, R / "config" / "essais" / "serieA_A-1.yaml", nx=81, ny=41, nz=15,
          facteur_couplage=FACTEUR, decalage_x=0.0, racine=R)
# reprogrammer les 4 dwells : séquentiels, DWELL s chacun, sans recouvrement
e.spots = [{"centre_x": cx, "t_debut": k * DWELL, "t_fin": (k + 1) * DWELL}
           for k, cx in enumerate(CENTRES)]
e.spec["duree_chauffe"] = len(CENTRES) * DWELL
e.spec["duree_totale"] = len(CENTRES) * DWELL + 15.0     # + refroidissement
e._Q_spots = [source_spot(e.grille, cfg, e.couches, COURANT, cx,
                          facteur_couplage=FACTEUR, decalage_x=0.0) for cx in CENTRES]
e._P_spots_2d = [Q.sum(axis=2) * e.grille.dz for Q in e._Q_spots]
sv, sol = e.simuler(modele="2D")
champs = np.array([sv.resultat_2d(sol, i) for i in range(sol.t.size)])   # (nt,nx,ny)
Tmax = champs.max(axis=0)                                                # pic par nœud
g = e.grille
x, y = g.x * 1e3, g.y * 1e3
X, Y = np.meshgrid(x, y, indexing="ij")

fig, ax = plt.subplots(figsize=(9.2, 3.6))
im = ax.pcolormesh(X, Y, Tmax, cmap="inferno", vmin=25, vmax=T_DEGRAD + 60, shading="gouraud")
cs = ax.contour(X, Y, Tmax, levels=[T_FUSION, T_PROCEDE, T_DEGRAD],
                colors=["#4DA6FF", "white", "#FF5555"], linewidths=[1.2, 1.2, 1.5])
ax.clabel(cs, fmt={T_FUSION: "337", T_PROCEDE: "390", T_DEGRAD: "450"}, fontsize=7)
for k, cx in enumerate(CENTRES, 1):
    ax.annotate(f"d{k}", (cx * 1e3, 20), color="white", fontsize=8, ha="center",
                va="center", fontweight="bold")
soudee = (Tmax >= T_FUSION).sum() / Tmax.size * 100
ax.set_xlabel("Longueur $x$ (mm)"); ax.set_ylabel("Largeur $y$ (mm)")
ax.set_aspect("equal")
ax.set_title(f"Procédé semi-statique — {COURANT:.0f} A, 4 dwells × {DWELL:.0f} s (pas 30 mm) — "
             f"pic d'interface ; zone ≥ fusion : {soudee:.0f} %", fontsize=10.5)
cb = fig.colorbar(im, ax=ax, fraction=0.026, pad=0.02)
cb.set_label("Pic de température d'interface (°C)")
fig.text(0.5, -0.02, "La soudure se forme en DEUX RAILS le long des chants (lobes du M) sur toute "
         "la longueur ; le centre reste froid (spot fixe en largeur).", ha="center",
         fontsize=8.5, color="0.35")
savefig(fig, OUT)
print("saved", OUT, "| zone soudée %.1f%%" % soudee)
