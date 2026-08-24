"""Animation MP4 de la chauffe exp7 200 A (slide 8 du deck) — VERSIONNÉ.

Deux panneaux EMPILÉS verticalement (l'un au-dessus de l'autre) :
  - (haut)  champ EM / source Joule à l'interface (statique) ;
  - (bas)   T(x, y, t) de la surface d'interface qui monte puis refroidit, avec
            les 5 TC.
Barre ANIMÉE = énergie surfacique déposée (cumulée, norm.), isolée dans sa
propre colonne à droite pour qu'AUCUN élément (titre, label) ne chevauche la
barre ni les panneaux.

Sortie : biblio/chauffe_surface_exp7_200A.mp4 (ffmpeg via imageio-ffmpeg bundlé).
"""
import sys
from pathlib import Path
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
from matplotlib.patches import Rectangle
import imageio_ffmpeg

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))
mpl.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # scripts/ (import _style)
from _style import apply_style  # noqa: E402  (style partagé, issue #17)
apply_style(fonts_only=True)

from jumeau.materiaux import Config
from jumeau.procede import Essai
from jumeau.em.source_joule import source_spot

OUT = R / "biblio" / "chauffe_surface_exp7_200A.mp4"
COURANT = 200.0
FACTEUR = 6.0123
NX, NY = 61, 21
N_FRAMES = 150
FPS = 20

# ----------------------------------------------------------------------
# 1. Simulation 2D (θ* de référence = défauts config)
# ----------------------------------------------------------------------
cfg = Config.charger(R / "code" / "config")
essai = Essai(cfg, R / "code" / "config" / "essais" / "exp7_200A.yaml", nx=NX, ny=NY, nz=15,
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
# 2. Figure 16:9 — panneaux EMPILÉS verticalement, barre d'énergie isolée à droite
# ----------------------------------------------------------------------
fig = plt.figure(figsize=(16, 9), dpi=100)
# Chaque panneau au ratio réel 120:40 = 3:1. Box display 3:1 : largeur_px/hauteur_px
# = 16*PW / 9*PH = 3  ->  PH = 16*PW/(27).  PW=0.52 -> PH≈0.308 (image remplit la box,
# le colorbar reste aligné, pas de blanc parasite).
PL, PW, PH = 0.11, 0.52, 0.308
TOP_B, BOT_B = 0.545, 0.145
axL = fig.add_axes([PL, TOP_B, PW, PH])                       # haut : source Joule
axR = fig.add_axes([PL, BOT_B, PW, PH])                       # bas  : température
# Deux jauges verticales RÉDUITES, à côté du panneau température (bas, animé),
# centrées verticalement dessus : colorbar T puis barre d'énergie.
GH = 0.22                                     # hauteur réduite commune
GB = BOT_B + (PH - GH) / 2                    # centrées sur le panneau température
axCB = fig.add_axes([PL + PW + 0.015, GB, 0.012, GH])   # colorbar T (réduite)
axB = fig.add_axes([PL + PW + 0.085, GB, 0.020, GH])    # barre énergie (à côté, réduite)

fig.suptitle("Jumeau numérique du soudage par induction — exp7, 200 A, spot centré",
             fontsize=17, fontweight="bold", y=0.965)
fig.text(0.5, 0.915, "Champ électromagnétique appliqué (empreinte de la source Joule) "
         "puis chauffe de la surface d'interface T(x, y, t)",
         ha="center", fontsize=11.5, color="0.25")

# --- panneau HAUT : source Joule (statique) ---
imL = axL.imshow(P_src.T, origin="lower", extent=extent, aspect="equal",
                 cmap="cividis", interpolation="bilinear")
axL.set_title("Champ EM (source Joule) — empreinte du spot", fontsize=12, fontweight="bold")
axL.set_xlabel("Longueur x (mm)"); axL.set_ylabel("Largeur y (mm)")

# --- panneau BAS : température animée ---
imR = axR.imshow(champs[0].T, origin="lower", extent=extent, aspect="equal",
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
axR.set_ylim(0, 40)
txt_t = axR.text(0.97, 0.93, "", transform=axR.transAxes, ha="right", va="top",
                 fontsize=13, color="white", fontweight="bold",
                 bbox=dict(facecolor="black", alpha=0.35, edgecolor="none", pad=2))
cb = fig.colorbar(imR, cax=axCB)
cb.set_label("Température (°C)", fontsize=10)
cb.ax.tick_params(labelsize=8)

# --- barre d'énergie ANIMÉE : à côté du panneau température, réduite (aucun chevauchement) ---
axB.set_xlim(0, 1); axB.set_ylim(0, 1); axB.set_xticks([])
axB.tick_params(labelsize=8)
axB.set_title("Énergie\ndéposée", fontsize=9.5, fontweight="bold", color="0.2", pad=8)
axB.set_ylabel("fraction cumulée (0 → 1)", fontsize=9)
axB.yaxis.set_label_position("right"); axB.yaxis.tick_right()
bar = Rectangle((0, 0), 1, 0.0, facecolor="#E69F00", edgecolor="none")
axB.add_patch(bar)
txt_e = axB.text(0.5, -0.06, "", transform=axB.transAxes, ha="center", va="top",
                 fontsize=10, fontweight="bold", color="0.2")

txt_phase = fig.text(0.5, 0.055, "", ha="center", fontsize=12, color="0.2")


def update(k):
    t = float(t_anim[k])
    imR.set_data(field_at(t).T)
    frac = min(t / duree_chauffe, 1.0)          # énergie cumulée normalisée
    bar.set_height(frac)
    bar.set_facecolor("#E69F00" if t <= duree_chauffe else "#B0B0B0")
    txt_e.set_text(f"{frac * 100:3.0f} %")
    txt_t.set_text(f"t = {t:5.1f} s")
    if t <= duree_chauffe:
        txt_phase.set_text("Phase : chauffe (courant établi)")
    else:
        txt_phase.set_text("Phase : refroidissement (courant coupé)")
    return imR, bar, txt_t, txt_e, txt_phase


if __name__ == "__main__":
    print(f"simulé : {sol.t.size} pas, Tmax={Tmax:.0f} °C, chauffe={duree_chauffe:.0f}s")
    anim = FuncAnimation(fig, update, frames=N_FRAMES, blit=False)
    writer = FFMpegWriter(fps=FPS, bitrate=2400,
                          metadata={"title": "chauffe exp7 200A"})
    anim.save(str(OUT), writer=writer)
    print("saved", OUT)
    plt.close(fig)
