"""Prediction du jumeau : historique de chauffe au CHANT (bord, lobe chaud du
profil en M) pour des courants NON encore mesures, avec ancrage sur les
mesures exp7 (150/200/250 A).

Modele : 2D lumpe, theta* de REFERENCE (defauts de config/materiaux.yaml :
h_haut=30.087, h_bas_2d=37.424, h_bord_x0=250, twill 0.20) +
facteur_couplage=6.0123, decalage_x=0.0. Geometrie exp7 : spot UNIQUE fixe
centre x=0.060 (cf. config/essais/exp7_200A.yaml). Grille 2D nx=61 ny=21 nz=15.

Protocole de simulation IDENTIQUE pour tous les courants predits : chauffe a
courant constant pendant une duree FIXE (DUREE_CHAUFFE=20 s), puis court
refroidissement jusqu'a DUREE_TOTALE=25 s (seul le courant varie -> compare
la DYNAMIQUE, tout le reste egal).

Sortie : docs/figures/fig_prediction_chauffe_courant.png

N'utilise QUE l'essai exp7_200A.yaml comme gabarit geometrique (spots,
thermocouples) ; la source est reconstruite a chaque courant via
jumeau.em.source_joule.source_spot, suivant le patron de
scripts/gen_figures_elsevier.py::fig3. Aucune config/essai n'est modifiee ;
aucune recalibration n'est effectuee (theta* et facteur_couplage figes a leur
valeur de reference).
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

R = Path("/Users/maxencedubois/PycharmProjects/Jumeau_Soudage_Induction")
sys.path.insert(0, str(R / "src"))
sys.path.insert(0, str(R / "scripts"))

from gen_figures_elsevier import (  # noqa: E402
    savefig, legend_right, add_temp_lines, load_txt, clean, heating_onset_idx,
    C_MODEL, T_FUSION, DATA7,
)

from jumeau.materiaux import Config  # noqa: E402
from jumeau.procede import Essai  # noqa: E402
from jumeau.em.source_joule import source_spot  # noqa: E402

# ----------------------------------------------------------------------
# Parametres figes (theta* de reference, cf. docstring module)
# ----------------------------------------------------------------------
FACTEUR_COUPLAGE = 6.0123
DECALAGE_X = 0.0
NX, NY, NZ = 61, 21, 15
DUREE_CHAUFFE = 20.0   # s -- protocole IDENTIQUE pour tous les courants predits
DUREE_TOTALE = 25.0    # s -- + court refroidissement pour la figure (0-25 s)

COURANTS_PREDITS = [100, 125, 165, 215, 275, 300]
COURANTS_MESURES = {150: "150A_v3.txt", 200: "200A_v6.txt", 250: "250A_v3.txt"}

# Rampe de couleur pour les courants predits (froid -> chaud avec le courant)
CMAP = plt.get_cmap("plasma")
COLOR_PRED = {
    I: CMAP(0.08 + 0.84 * k / (len(COURANTS_PREDITS) - 1))
    for k, I in enumerate(sorted(COURANTS_PREDITS))
}


def construire_essai():
    """Essai gabarit (geometrie/spots/thermocouples exp7_200A), theta* de
    reference. La source (_Q_spots/_P_spots_2d) est reconstruite par courant
    dans la boucle principale ; le protocole temporel (duree_chauffe fixe)
    est impose ici en ecrasant le t_fin du spot unique + duree_totale."""
    cfg = Config.charger(R / "config")
    cfg.contact.h_haut = 30.087
    cfg.ambiant.h_bas_2d = 37.424
    cfg.ambiant.h_bord_x0 = 250.0
    e = Essai(cfg, R / "config/essais/exp7_200A.yaml", nx=NX, ny=NY, nz=NZ,
              facteur_couplage=FACTEUR_COUPLAGE, decalage_x=DECALAGE_X, racine=R)
    # Protocole IDENTIQUE impose pour tous les courants (cf. docstring module) :
    # ecrase le t_fin du spot unique et la duree totale simulee de l'essai
    # gabarit (qui valait 18 s / 115 s, specifiques a la mesure 200 A).
    e.spots[0]["t_fin"] = DUREE_CHAUFFE
    e.spec["duree_totale"] = DUREE_TOTALE
    return cfg, e


def simuler_courant(cfg, e, courant: float):
    """Reconstruit la source Joule au ``courant`` demande (theta* fige) et
    simule en 2D. Retourne (t, T_chant) avec T_chant = max(TC1, TC5) au
    CHANT (y=0 / y=largeur), en degres C absolus (T_amb du modele = 20 C,
    cf. config/materiaux.yaml)."""
    e._Q_spots = [
        source_spot(e.grille, cfg, e.couches, courant, float(s["centre_x"]),
                    facteur_couplage=FACTEUR_COUPLAGE, decalage_x=DECALAGE_X)
        for s in e.spots
    ]
    e._P_spots_2d = [Q.sum(axis=2) * e.grille.dz for Q in e._Q_spots]
    sv, sol = e.simuler(modele="2D")
    largeur = e.grille.largeur
    T_bord0 = sv.serie_temporelle(sol, 0.060, 0.0, "interface")
    T_bord1 = sv.serie_temporelle(sol, 0.060, largeur, "interface")
    T_chant = np.maximum(T_bord0, T_bord1)
    return sol.t, T_chant


def temps_fusion(t: np.ndarray, T: np.ndarray, T_ref: float = T_FUSION):
    """Instant (s) de la premiere traversee de ``T_ref`` (interp. lineaire),
    ou None si jamais atteint sur la fenetre simulee."""
    above = np.where(T >= T_ref)[0]
    if len(above) == 0:
        return None
    i = above[0]
    if i == 0:
        return float(t[0])
    t0, t1 = t[i - 1], t[i]
    T0, T1 = T[i - 1], T[i]
    frac = (T_ref - T0) / (T1 - T0) if T1 != T0 else 0.0
    return float(t0 + frac * (t1 - t0))


def main():
    cfg, e = construire_essai()

    # ------------------------------------------------------------------
    # 1) Courants PREDITS (modele, theta* fige, protocole 20 s uniforme)
    # ------------------------------------------------------------------
    resultats = {}
    for I in COURANTS_PREDITS:
        t, T_chant = simuler_courant(cfg, e, float(I))
        resultats[I] = (t, T_chant)

    # ------------------------------------------------------------------
    # 2) Courants MESURES (exp7, ancrage) -- meme nettoyage que gen_figures
    # ------------------------------------------------------------------
    mesures = {}
    for I, fname in COURANTS_MESURES.items():
        df = load_txt(DATA7 / f"{I}A" / fname)
        dfc, amb, tc_cols = clean(df)
        i0 = heating_onset_idx(dfc, tc_cols, amb)
        t_m = dfc["t"].to_numpy() - dfc["t"].to_numpy()[i0]
        chant_m = np.maximum(dfc["TC1"], dfc["TC5"]).to_numpy()
        mesures[I] = (t_m, chant_m)

    # ------------------------------------------------------------------
    # 3) Verification de coherence -- modele au meme protocole que la
    #    mesure (meme duree de chauffe reelle par courant, PAS le protocole
    #    uniforme de la prediction) pour les 3 courants ancres.
    # ------------------------------------------------------------------
    duree_reelle = {150: 57.0, 200: 18.0, 250: 10.0}
    controle = {}
    for I in (150, 200, 250):
        e.spots[0]["t_fin"] = duree_reelle[I]
        e.spec["duree_totale"] = duree_reelle[I] + 5.0
        t_c, T_c = simuler_courant(cfg, e, float(I))
        t_m, chant_m = mesures[I]
        pic_modele = float(T_c.max())
        pic_mesure = float(chant_m.max())
        controle[I] = (pic_modele, pic_mesure)
    # restaure le protocole uniforme (deja utilise plus haut pour les
    # courants predits, mais _Q_spots/_P_spots_2d/spots ont ete modifies
    # par la boucle de controle -- pas de recalibration, juste un reset
    # des attributs de temps du meme essai gabarit).
    e.spots[0]["t_fin"] = DUREE_CHAUFFE
    e.spec["duree_totale"] = DUREE_TOTALE

    # ------------------------------------------------------------------
    # Figure
    # ------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    for I in sorted(COURANTS_PREDITS):
        t, T_chant = resultats[I]
        ax.plot(t, T_chant, "-", color=COLOR_PRED[I], lw=1.6,
                label=f"{I} A — modèle (prédiction, non testé)")
    couleurs_mes = {150: "#333333", 200: "#777777", 250: "#000000"}
    marqueurs_mes = {150: "o", 200: "s", 250: "^"}
    for I in (150, 200, 250):
        t_m, chant_m = mesures[I]
        m = (t_m >= 0) & (t_m <= 25.0)
        ax.plot(t_m[m], chant_m[m], ls=(0, (2, 1.5)), color=couleurs_mes[I],
                marker=marqueurs_mes[I], markevery=8, markersize=4,
                lw=1.1, label=f"{I} A — mesuré (exp7)")

    add_temp_lines(ax, lines=("fusion", "procede", "degrad"))
    ax.set_xlim(0, 25)
    ax.set_xlabel("Temps depuis le début de chauffe (s)")
    ax.set_ylabel("Température au chant (°C)")
    ax.set_title(
        "Prédiction — historique de chauffe au chant vs courant (modèle + mesures exp7)")
    legend_right(ax, ncol=1)
    savefig(fig, "fig_prediction_chauffe_courant.png")

    # ------------------------------------------------------------------
    # Table texte (b) + controle (c) -- imprimes pour le rapport
    # ------------------------------------------------------------------
    print("\n=== (b) Table par courant PREDIT ===")
    print(f"{'I (A)':>7} | {'T_pic @20s (°C)':>16} | {'t(fusion 337°C) (s)':>20}")
    for I in sorted(COURANTS_PREDITS):
        t, T_chant = resultats[I]
        pic = float(T_chant.max())
        t_fus = temps_fusion(t, T_chant)
        t_fus_s = f"{t_fus:.2f}" if t_fus is not None else "n/a"
        print(f"{I:>7} | {pic:>16.1f} | {t_fus_s:>20}")

    print("\n=== (c) Controle de coherence (protocole = duree REELLE mesuree) ===")
    print(f"{'I (A)':>7} | {'T_pic modele (°C)':>18} | {'T_pic mesure (°C)':>18} | {'ecart (°C)':>11}")
    for I in (150, 200, 250):
        pic_modele, pic_mesure = controle[I]
        print(f"{I:>7} | {pic_modele:>18.1f} | {pic_mesure:>18.1f} | {pic_modele - pic_mesure:>11.1f}")


if __name__ == "__main__":
    main()
