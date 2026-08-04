"""Animation MP4 de la chauffe exp7 200 A (slide 8 du deck) — VERSIONNÉ.

Deux panneaux : (gauche) champ EM / source Joule à l'interface (statique) ;
(droite) T(x, y, t) de la surface d'interface qui monte puis refroidit, avec
les 5 TC. Barre centrale ANIMÉE = énergie surfacique déposée (cumulée, norm.).

Corrige les deux défauts de l'ancienne vidéo :
  - la barre centrale était vide/figée -> désormais animée (remplissage) ;
  - le label du colorbar « Température (°C) » était coupé à droite -> marge
    droite dédiée.

Sortie : docs/chauffe_surface_exp7_200A.mp4  (ffmpeg via imageio-ffmpeg bundlé).
"""
import sys
from pathlib import Path
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
from matplotlib.patches import Rectangle
import imageio_ffmpeg

R = Path("/Users/maxencedubois/PycharmProjects/Jumeau_Soudage_Induction")
sys.path.insert(0, str(R / "src"))
mpl.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()
mpl.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans", "Arial"],
    "mathtext.fontset": "dejavusans",
})

from jumeau.materiaux import Config
from jumeau.procede import Essai
from jumeau.em.source_joule import source_spot

OUT = R / "docs" / "chauffe_surface_exp7_200A.mp4"
COURANT = 200.0
FACTEUR = 6.0123
NX, NY = 61, 21
N_FRAMES = 150
FPS = 20

# ----------------------------------------------------------------------
# 1. Simulation 2D (θ* de référence = défauts config)
# ----------------------------------------------------------------------
cfg = Config.charger(R / "config")
essai = Essai(cfg, R / "config" / "essais" / "exp7_200A.yaml", nx=NX, ny=NY, nz=15,
              facteur_couplage=FACTEUR, decalage_x=0.0, racine=R)
solveur, sol = essai.simuler(modele="2D")
duree_chauffe = float(essai.spec["duree_chauffe"])

# Carte de source Joule à l'interface (W/m², statique) — patron de fig3
Q = [source_spot(essai.grille, cfg, essai.couches, COURANT, float(s["centre_x"]),
                 facteur_couplage=FACTEUR, decalage_x=0.0) for s in essai.spots]
P_src = sum(q.sum(axis=2) * essai.grille.dz for q in Q)          # (nx, ny)

g = essai.grille
extent = [0, g.x[-1] * 1e3, 0, g.y[-1] * 1e3]                    # mm
champs = [solveur.resultat_2d(sol, i) for i in range(sol.t.size)]
Tmax = max(float(c.max()) for c in champs)
Tamb = float(champs[0].mean())

# fenêtre d'animation : chauffe + refroidissement précoce (au-delà, c'est long
# et plat). Champs interpolés dans le temps pour une vidéo fluide.
T_ANIM = min(45.0, float(sol.t[-1]))
t_anim = np.linspace(0.0, T_ANIM, N_FRAMES)


def field_at(t):
    j = int(np.searchsorted(sol.t, t))
    if j <= 0:
        return champs[0]
    if j >= len(champs):
        return champs[-1]
    t0, t1 = sol.t[j - 1], sol.t[j]
    w = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
    return (1 - w) * champs[j - 1] + w * champs[j]

# ----------------------------------------------------------------------
# 2. Figure 16:9
# ----------------------------------------------------------------------
fig = plt.figure(figsize=(16, 9), dpi=100)
axL = fig.add_axes([0.045, 0.16, 0.31, 0.60])
axB = fig.add_axes([0.435, 0.16, 0.028, 0.60])     # barre centrale animée
axR = fig.add_axes([0.545, 0.16, 0.31, 0.60])
axCB = fig.add_axes([0.895, 0.16, 0.017, 0.60])    # colorbar droite (marge à droite OK)

fig.suptitle("Jumeau numérique du soudage par induction — exp7, 200 A, spot centré",
             fontsize=17, fontweight="bold", y=0.955)
fig.text(0.5, 0.90, "Champ électromagnétique appliqué (empreinte de la source Joule) "
         "puis chauffe de la surface d'interface T(x, y, t)",
         ha="center", fontsize=11.5, color="0.25")

# --- panneau gauche : source Joule (statique) ---
imL = axL.imshow(P_src.T, origin="lower", extent=extent, aspect="auto",
                 cmap="cividis", interpolation="bilinear")
axL.set_title("Champ EM (source Joule) — empreinte du spot", fontsize=12, fontweight="bold")
axL.set_xlabel("Longueur x (mm)"); axL.set_ylabel("Largeur y (mm)")

# --- barre centrale animée : énergie déposée cumulée (normalisée) ---
axB.set_xlim(0, 1); axB.set_ylim(0, 1); axB.set_xticks([])
axB.set_title("dépôt", fontsize=9, color="0.3", pad=4)
axB.set_ylabel("Énergie surfacique déposée (cumulée, norm.)", fontsize=11)
bar = Rectangle((0, 0), 1, 0.0, facecolor="#E69F00", edgecolor="none")
axB.add_patch(bar)

# --- panneau droit : température animée ---
imR = axR.imshow(champs[0].T, origin="lower", extent=extent, aspect="auto",
                 cmap="inferno", vmin=Tamb, vmax=Tmax, interpolation="bilinear")
axR.set_title("Température de surface (interface)", fontsize=12, fontweight="bold")
axR.set_xlabel("Longueur x (mm)"); axR.set_ylabel("Largeur y (mm)")
ys_tc = [0, 10, 20, 30, 40]
for i, y in enumerate(ys_tc, start=1):
    dy = 2.0 if y == 0 else (-2.0 if y == 40 else 0.0)
    va = "bottom" if y == 0 else ("top" if y == 40 else "center")
    axR.scatter([60], [y], marker="x", s=45, color="white", linewidths=1.6, zorder=5)
    axR.annotate(f"TC{i}", (60, y), xytext=(64, y + dy), fontsize=9, color="white",
                 va=va, fontweight="bold")
axR.set_ylim(-1.5, 41.5)
txt_t = axR.text(0.97, 0.93, "", transform=axR.transAxes, ha="right", va="top",
                 fontsize=13, color="white", fontweight="bold",
                 bbox=dict(facecolor="black", alpha=0.35, edgecolor="none", pad=2))
cb = fig.colorbar(imR, cax=axCB)
cb.set_label("Température (°C)", fontsize=12)

txt_phase = fig.text(0.5, 0.065, "", ha="center", fontsize=12, color="0.2")


def update(k):
    t = float(t_anim[k])
    imR.set_data(field_at(t).T)
    frac = min(t / duree_chauffe, 1.0)          # énergie cumulée normalisée
    bar.set_height(frac)
    bar.set_facecolor("#E69F00" if t <= duree_chauffe else "#B0B0B0")
    txt_t.set_text(f"t = {t:5.1f} s")
    if t <= duree_chauffe:
        txt_phase.set_text("Phase : chauffe (courant établi)")
    else:
        txt_phase.set_text("Phase : refroidissement (courant coupé)")
    return imR, bar, txt_t, txt_phase


if __name__ == "__main__":
    print(f"simulé : {sol.t.size} pas, Tmax={Tmax:.0f} °C, chauffe={duree_chauffe:.0f}s")
    anim = FuncAnimation(fig, update, frames=N_FRAMES, blit=False)
    writer = FFMpegWriter(fps=FPS, bitrate=2400,
                          metadata={"title": "chauffe exp7 200A"})
    anim.save(str(OUT), writer=writer)
    print("saved", OUT)
    plt.close(fig)
