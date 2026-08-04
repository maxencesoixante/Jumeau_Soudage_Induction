"""Prédiction MFC réduit — masque de source à l'empreinte du concentrateur.

Contexte (cf. jumeau.procede.Essai.masque_source_mfc, défaut OFF) : le modèle
historique ne masque QUE les pertes convectives (h_haut) à l'empreinte du MFC,
pas la source Joule elle-même -- un MFC plus petit que le MFC labo (55 mm) ne
changeait donc presque rien au profil simulé, ce qui est physiquement suspect
(le MFC est censé concentrer le FLUX, donc la source, sous son empreinte).

Ce script compare, à COURANT ET DURÉE FIXÉS (250 A, 15 s -- réglage de la
fenêtre de soudage, cf. fig_loi_reglage), deux configurations sur la
géométrie exp7 (spot fixe centré x=60 mm) :
  - MFC labo   : cfc.longueur=0.055 m (config par défaut), masque_source_mfc=OFF
                 (comportement de référence actuel -- non modifié) ;
  - MFC réduit : cfc.longueur=0.03175 m (override EN MÉMOIRE, PAS en config),
                 cfc.largeur=0.0315 m et cfc.hauteur=0.012 m (déjà les valeurs
                 par défaut), masque_source_mfc=ON.

APPROXIMATION DE 1er ORDRE, À NE PAS SUR-INTERPRÉTER : le masque est un
rectangle DUR (0/1, pas de frange de champ proche à la lisière du bloc MFC) ;
la puissance hors empreinte est PERDUE (tronquée), pas redistribuée vers
l'intérieur par conservation -- un vrai MFC réduit concentrerait sans doute
UNE PARTIE de ce flux vers le centre, ce que ce modèle ne capture pas. Cf.
docstring jumeau.procede.Essai.masque_source_mfc. Extrapolation à une
géométrie MFC neuve, non mesurée -- à confirmer expérimentalement (le MFC
réduit est commandé, cf. config/geometrie.yaml:cfc).

Sortie : docs/figures/fig_mfc_reduit.png
"""
import copy
import sys
from pathlib import Path

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

R = Path("/Users/maxencedubois/PycharmProjects/Jumeau_Soudage_Induction")
sys.path.insert(0, str(R / "src"))
mpl.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans", "Arial"],
    "mathtext.fontset": "dejavusans", "font.size": 11, "axes.labelsize": 11.5,
    "axes.labelweight": "bold", "axes.titlesize": 11, "figure.dpi": 600,
    "savefig.dpi": 600, "savefig.bbox": "tight", "savefig.pad_inches": 0.06,
})

from jumeau.materiaux import Config
from jumeau.procede import Essai
from jumeau.em.source_joule import source_spot

OUT = R / "docs" / "figures" / "fig_mfc_reduit.png"
FACTEUR = 6.0123           # θ* de référence (facteur_couplage, argument runtime -- NON recalibré ici)
T_FUSION, T_PROCEDE, T_DEGRAD = 337.0, 390.0, 450.0
COURANT, DUREE = 250.0, 15.0   # A, s -- réglage dans la fenêtre de soudage (cf. fig_loi_reglage : 250 A -> 15 s)
X_COUPE = 0.060                # m -- coupe en largeur au spot (centre_x)

cfg_labo = Config.charger(R / "config")
cfg_reduit = copy.deepcopy(cfg_labo)
cfg_reduit.geometrie["cfc"]["longueur"] = 0.03175
# largeur=0.0315 et hauteur=0.012 sont déjà les valeurs par défaut de config/geometrie.yaml
assert cfg_reduit.geometrie["cfc"]["largeur"] == 0.0315
assert cfg_reduit.geometrie["cfc"]["hauteur"] == 0.012
assert cfg_labo.geometrie["cfc"]["longueur"] == 0.055   # config de référence NON modifiée


def champ_interface(cfg, masque_source_mfc: bool, nx=81, ny=41, nz=15):
    """Carte T(x,y) d'interface au PIC, courant/durée forcés (comme
    fig_empreinte_soudure.py) -- reconstruit _Q_spots/_P_spots_2d à COURANT
    et DURÉE choisis (le YAML exp7_200A fixe 200 A / 18 s par défaut)."""
    e = Essai(cfg, R / "config" / "essais" / "exp7_200A.yaml", nx=nx, ny=ny, nz=nz,
              facteur_couplage=FACTEUR, decalage_x=0.0, racine=R,
              masque_source_mfc=masque_source_mfc)
    e.spec["duree_chauffe"] = DUREE
    e.spec["duree_totale"] = DUREE
    e.spots[0]["t_fin"] = DUREE
    Q = [source_spot(e.grille, cfg, e.couches, COURANT, float(s["centre_x"]),
                     facteur_couplage=FACTEUR, decalage_x=0.0) for s in e.spots]
    if masque_source_mfc:
        # même logique que Essai.__init__ (masque_source_mfc) : réutiliser EXACTEMENT
        # le masque déjà construit par Essai (posé sur le spot, cfg de cette config)
        Q = [q * m[:, :, None] for q, m in zip(Q, e._masques)]
    e._Q_spots = Q
    e._P_spots_2d = [q.sum(axis=2) * e.grille.dz for q in Q]
    sv, sol = e.simuler(modele="2D")
    champs = np.array([sv.resultat_2d(sol, i) for i in range(sol.t.size)])  # (nt, nx, ny)
    Tmax = champs.max(axis=0)
    return e.grille, Tmax


def diagnostics(nom, g, Tmax):
    """Contraste bord/centre, pic bord, pic centre, % interface soudée
    (>= fusion), position (y) du maximum sur la coupe x=X_COUPE."""
    ix = int(np.argmin(np.abs(g.x - X_COUPE)))
    prof_y = Tmax[ix, :]
    iy_centre = int(np.argmin(np.abs(g.y - g.largeur / 2)))
    T_bord = max(prof_y[0], prof_y[-1])       # valeur exactement au chant physique (y=0/largeur)
    T_centre = prof_y[iy_centre]
    iy_pic = int(np.argmax(prof_y))
    y_pic_mm = g.y[iy_pic] * 1e3
    T_pic = float(prof_y[iy_pic])              # vrai maximum de la coupe (peut différer du chant)
    contraste = T_pic / T_centre
    soude_pct = float((Tmax >= T_FUSION).sum()) / Tmax.size * 100.0
    print(f"--- {nom} ---")
    print(f"  T au chant exact (y=0/40)   : {T_bord:7.1f} °C")
    print(f"  pic centre (y=20)           : {T_centre:7.1f} °C")
    print(f"  PIC de la coupe (max réel)  : {T_pic:7.1f} °C  à y={y_pic_mm:5.1f} mm")
    print(f"  contraste pic/centre        : {contraste:5.2f}")
    print(f"  interface >= fusion (337 °C) : {soude_pct:5.2f} %")
    return dict(nom=nom, T_bord=T_bord, T_centre=T_centre, T_pic=T_pic, contraste=contraste,
                soude_pct=soude_pct, y_pic_mm=y_pic_mm, prof_y=prof_y, y=g.y)


print(f"Réglage : I={COURANT:.0f} A, durée={DUREE:.0f} s, facteur_couplage={FACTEUR} (référence, NON recalibré)")
print()

g_labo, T_labo = champ_interface(cfg_labo, masque_source_mfc=False)
d_labo = diagnostics("MFC labo (55 mm, masque source OFF -- reference)", g_labo, T_labo)
print()
g_red, T_red = champ_interface(cfg_reduit, masque_source_mfc=True)
d_red = diagnostics("MFC réduit (31.75 mm, masque source ON)", g_red, T_red)
print()

point_chaud_deplace = d_red["y_pic_mm"] != d_labo["y_pic_mm"]
centre_soude = d_red["T_centre"] >= T_FUSION
print(f"Point chaud déplacé du bord vers l'intérieur : {point_chaud_deplace} "
      f"(y_pic {d_labo['y_pic_mm']:.1f} -> {d_red['y_pic_mm']:.1f} mm)")
print(f"Centre soudé (T_centre >= {T_FUSION:.0f} °C) avec le MFC réduit : {centre_soude} "
      f"(T_centre={d_red['T_centre']:.1f} °C)")

# ------------------------------------------------------------------ figure
fig = plt.figure(figsize=(9.6, 7.4))
gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 0.62], hspace=0.32, wspace=0.28)
ax_labo = fig.add_subplot(gs[0, 0])
ax_red = fig.add_subplot(gs[0, 1], sharex=ax_labo, sharey=ax_labo)
ax_prof = fig.add_subplot(gs[1, :])

vmax = T_DEGRAD + 60
axes_map = [(ax_labo, g_labo, T_labo, d_labo), (ax_red, g_red, T_red, d_red)]
for ax, g, Tmax, d in axes_map:
    X, Y = np.meshgrid(g.x * 1e3, g.y * 1e3, indexing="ij")
    im = ax.pcolormesh(X, Y, Tmax, cmap="inferno", vmin=25, vmax=vmax, shading="gouraud")
    cs = ax.contour(X, Y, Tmax, levels=[T_FUSION, T_DEGRAD],
                    colors=["#4DA6FF", "#FF5555"], linewidths=[1.3, 1.6])
    ax.clabel(cs, fmt={T_FUSION: "337", T_DEGRAD: "450"}, fontsize=7)
    ax.axvline(X_COUPE * 1e3, color="white", lw=0.8, ls=":", alpha=0.7)
    ax.set_title(f"{d['nom'].split(' (')[0]}\n"
                 f"soudé {d['soude_pct']:.1f} % — contraste {d['contraste']:.2f}",
                 fontsize=9.5)
    ax.set_xlabel("Longueur $x$ (mm)")
    ax.set_aspect("equal")
ax_labo.set_ylabel("Largeur $y$ (mm)")
cb = fig.colorbar(im, ax=[ax_labo, ax_red], fraction=0.025, pad=0.02)
cb.set_label("Température d'interface au pic (°C)")

ax_prof.plot(d_labo["y"] * 1e3, d_labo["prof_y"], "-o", ms=3, color="#333333",
            label=f"MFC labo (55 mm) — bord {d_labo['T_bord']:.0f} °C / centre {d_labo['T_centre']:.0f} °C")
ax_prof.plot(d_red["y"] * 1e3, d_red["prof_y"], "-s", ms=3, color="#D55E00",
            label=f"MFC réduit (31.75 mm) — bord {d_red['T_bord']:.0f} °C / centre {d_red['T_centre']:.0f} °C")
ax_prof.axhline(T_FUSION, color="#4DA6FF", lw=1.1, ls="--", label="fusion 337 °C")
ax_prof.axhline(T_DEGRAD, color="#FF5555", lw=1.1, ls="--", label="dégradation 450 °C")
ax_prof.set_xlabel("Largeur $y$ (mm) — coupe à $x$ = 60 mm")
ax_prof.set_ylabel("T interface au pic (°C)")
ax_prof.set_title("Profil en largeur — bord (M) vs centré ?", fontsize=10.5)
ax_prof.legend(fontsize=8.2, loc="upper center", ncol=2)
ax_prof.grid(alpha=0.25)

fig.suptitle(f"Prédiction MFC réduit — masque de source (flag ON), {COURANT:.0f} A / {DUREE:.0f} s, "
             f"$\\theta^*$ référence (facteur={FACTEUR}, non recalibré)",
             fontsize=11.5, fontweight="bold", y=0.995)
fig.text(0.5, -0.01,
        "Masque source = approximation 1er ordre (rectangle dur, pas de frange ; puissance hors empreinte "
        "tronquée, pas redistribuée) -- extrapolation NON mesurée, à confirmer.",
        ha="center", fontsize=7.8, style="italic", color="#555555")
fig.savefig(OUT, bbox_extra_artists=[fig.texts[-1]])
print("\nsaved", OUT)
