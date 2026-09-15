"""Ce que devient chaque conclusion de cette campagne quand la dégradation est
jugée en temps × température plutôt qu'au seuil de pic.

CE QUI CLOCHAIT. Tout le projet juge « dégradé si T_max > 450 °C ». Ce seuil est
un littéral répété dans huit scripts, absent de la configuration et de toute
référence du corpus — introuvable. Et il ne voit qu'un facteur : il déclare
identiques une brève excursion à 450 °C et une demi-heure de maintien à 400 °C.
Les calculs de modulation ont buté exactement là, et leur conclusion (« 100 % de
la plaque dans la fenêtre utile ») était indécidable pour cette raison.

CE QUI LE REMPLACE. Une dose d'Arrhenius (`jumeau.thermique.dose_degradation`),
ancrée pour que dose = 1 corresponde EXACTEMENT à l'ancien seuil lu comme une
exposition : 450 °C pendant une durée de passe. Aucun seuil nouveau n'est
introduit ; la seule hypothèse ajoutée est l'énergie d'activation, et elle est
balayée de 100 à 250 kJ/mol — car elle n'est PAS mesurée dans ce projet.

RÈGLE DE LECTURE. Un résultat qui change de signe sur ce balayage doit être dit
indécidable, pas tranché.

Sorties : biblio/modele/critere_dose_degradation.md
          biblio/modele/figures/fig_critere_dose_degradation.png
"""
from __future__ import annotations

import copy
import sys
from datetime import date
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "src"))
sys.path.insert(0, str(R / "code" / "scripts"))
from _style import apply_style, savefig, OKABE_ITO                   # noqa: E402
from jumeau.materiaux import Config                                   # noqa: E402
from jumeau.procede import Essai                                      # noqa: E402
from jumeau.geometrie import masque_empreinte_cfc                     # noqa: E402
from jumeau.em.source_joule import source_spot                        # noqa: E402
from jumeau.thermique.dose_degradation import (                       # noqa: E402
    dose, temps_limite, metriques_dose, T_REF_DEFAUT, T_REF_DUREE)

apply_style(**{"font.size": 9.5, "axes.titlesize": 10.5})

SORTIE_MD = R / "biblio" / "modele" / "critere_dose_degradation.md"
SORTIE_FIG = R / "biblio" / "modele" / "figures" / "fig_critere_dose_degradation.png"
GABARIT = R / "code" / "config" / "essais" / "exp7_200A.yaml"

FUSION, DEGRAD = 337.0, 450.0
MFC_REDUIT, Y_C = 0.03175, 0.020
LF_PHYS, K_HOT = 40000.0, 100.0
TABLE_KT = [[0.0, 3.0], [FUSION, 3.0], [380.0, K_HOT], [700.0, K_HOT]]
EAS = [100e3, 150e3, 200e3, 250e3]
X_PREMIER, X_DERNIER = 0.015875, 0.105875


def centres(n_passes):
    if n_passes == 1:
        return [0.060]
    return list(np.linspace(X_PREMIER, X_DERNIER, n_passes))


def historique(n_passes, courant, duree, fusion=False, moyenne=False):
    """(temps, champs) de l'interface — champs (nt, nx, ny)."""
    cfg = copy.deepcopy(Config.charger(R / "code" / "config"))
    cfg.geometrie["cfc"]["longueur"] = MFC_REDUIT
    cfg.contact.h_haut = 30.087
    cfg.ambiant.h_bas_2d = 37.424
    if fusion:
        cfg.materiau.chaleur_latente = LF_PHYS
        cfg.materiau.k_plan_T = TABLE_KT
    xs = centres(n_passes)
    e = Essai(cfg, GABARIT, nx=61, ny=21, nz=15, facteur_couplage=6.0123,
              decalage_x=0.0, racine=R, masque_source_mfc=False)

    def source(x):
        m = masque_empreinte_cfc(e.grille, cfg, x, centre_y=Y_C)
        Q = source_spot(e.grille, cfg, e.couches, courant, x,
                        facteur_couplage=6.0123, centre_y=Y_C)
        t = float(Q.sum())
        Q = Q * m[:, :, None]
        return Q * (t / float(Q.sum())), m       # famille A : le flux se reconcentre

    if moyenne:       # limite d'un balayage modulé : la plaque voit la moyenne
        Qs, ms = zip(*(source(x) for x in xs))
        Q = sum(Qs) / len(Qs)
        masque = np.maximum.reduce(ms)
        e.spots = [{"centre_x": xs[0], "t_debut": 0.0, "t_fin": duree}]
        e._masques, e._Q_spots = [masque], [Q]
        total = duree
    else:             # passes successives
        spots, Qs, ms, t0 = [], [], [], 0.0
        for x in xs:
            Q, m = source(x)
            spots.append({"centre_x": x, "t_debut": t0, "t_fin": t0 + duree})
            Qs.append(Q)
            ms.append(m)
            t0 += duree
        e.spots, e._masques, e._Q_spots = spots, ms, Qs
        total = t0
    e._P_spots_2d = [q.sum(axis=2) * e.grille.dz for q in e._Q_spots]
    e.spec["duree_chauffe"] = total
    e.spec["duree_totale"] = total
    sv, sol = e.simuler(modele="2D")
    champs = np.array([sv.resultat_2d(sol, i) for i in range(sol.t.size)])
    return np.asarray(sol.t, dtype=float), champs


SCENARIOS = [
    ("4 passes · 235 A · 20 s · pas 30 mm", dict(n_passes=4, courant=235.0, duree=20.0)),
    ("7 passes · 235 A · 20 s · pas 15 mm", dict(n_passes=7, courant=235.0, duree=20.0)),
    ("4 passes · 200 A · 120 s (tout > 337)", dict(n_passes=4, courant=200.0, duree=120.0)),
    ("balayage modulé · fusion · 200 A · 1600 s",
     dict(n_passes=4, courant=200.0, duree=1600.0, fusion=True, moyenne=True)),
]


def main() -> None:
    lignes = []
    for nom, kw in SCENARIOS:
        t, champs = historique(**kw)
        pic = champs.max(axis=0)
        ancien_deg = float(np.mean(pic > DEGRAD) * 100.0)
        ancien_soude = float(np.mean((pic >= FUSION) & (pic <= DEGRAD)) * 100.0)
        par_ea = {}
        for ea in EAS:
            m = metriques_dose(champs, t, fusion=FUSION, ea=ea)
            par_ea[ea] = m
        lignes.append((nom, pic.max(), t[-1], ancien_soude, ancien_deg, par_ea))
        print(f"  {nom:42s} pic {pic.max():6.1f} °C  ancien: soudé "
              f"{ancien_soude:5.1f} % dégradé {ancien_deg:5.1f} %", flush=True)
        for ea in EAS:
            m = par_ea[ea]
            print(f"      Ea={ea/1e3:.0f} kJ/mol : soudé {m['pct_soude']:5.1f} %  "
                  f"dégradé {m['pct_degrade']:5.1f} %  dose max {m['dose_max']:.3g}",
                  flush=True)

    SORTIE_FIG.parent.mkdir(parents=True, exist_ok=True)
    fig, (ax_t, ax_b) = plt.subplots(1, 2, figsize=(11.6, 4.8))

    temperatures = np.linspace(330.0, 560.0, 200)
    for ea, couleur in zip(EAS, [OKABE_ITO[c] for c in
                                 ("cyan", "vert", "bleu", "vermillon")]):
        ax_t.plot(temperatures, temps_limite(temperatures, ea=ea), lw=2.0,
                  color=couleur, label=f"Ea = {ea/1e3:.0f} kJ/mol")
    ax_t.plot([T_REF_DEFAUT], [T_REF_DUREE], "*", ms=16, color="0.2", zorder=5)
    ax_t.annotate(f"ancrage {T_REF_DEFAUT:.0f} °C · {T_REF_DUREE:.0f} s\n"
                  "= l'ancien seuil, relu comme exposition",
                  xy=(T_REF_DEFAUT, T_REF_DUREE), textcoords="offset points",
                  xytext=(10, -26), ha="left", fontsize=8.5, color="0.2",
                  arrowprops=dict(arrowstyle="->", color="0.2", lw=1.0))
    # points de fonctionnement NUMEROTES (meme ordre que le panneau de droite)
    x_max = 560.0
    for k, (nom, pic_max, duree_tot, *_) in enumerate(lignes, 1):
        hors = pic_max > x_max
        xp = x_max - 8.0 if hors else pic_max
        ax_t.plot([xp], [duree_tot], ">" if hors else "o", ms=9 if hors else 8,
                  mfc="none", mec=OKABE_ITO["orange"], mew=2.0, zorder=6)
        ax_t.annotate(f"{k}" + (f"  ({pic_max:.0f} °C)" if hors else ""),
                      xy=(xp, duree_tot), textcoords="offset points",
                      xytext=(-6, 8) if not hors else (-10, 8),
                      ha="right", fontsize=9, color=OKABE_ITO["orange"],
                      fontweight="bold")
    ax_t.set_xlim(330.0, x_max)
    ax_t.set_yscale("log")
    ax_t.set_xlabel("température de pic (°C)")
    ax_t.set_ylabel("durée d'exposition admissible (s)")
    ax_t.set_title("Au-dessus de la courbe, c'est dégradé")
    ax_t.legend(fontsize=8.5, frameon=False, loc="upper right")
    ax_t.grid(alpha=0.25, which="both")

    noms = [n for n, *_ in lignes]
    y = np.arange(len(noms))
    h = 0.38
    ax_b.barh(y + h / 2, [l[4] for l in lignes], h, color="0.72",
              label="seuil de pic (ancien)")
    ax_b.barh(y - h / 2, [l[5][150e3]["pct_degrade"] for l in lignes], h,
              color=OKABE_ITO["vermillon"], label="dose, Ea = 150 kJ/mol")
    ax_b.set_yticks(y)
    ax_b.set_yticklabels([f"{k}. " + n.replace(" · ", "\n", 1)
                          for k, n in enumerate(noms, 1)], fontsize=8.5)
    ax_b.invert_yaxis()
    ax_b.set_xlabel("interface dégradée (%)")
    ax_b.set_title("Ce que le changement de critère déplace")
    ax_b.annotate("0 % dans les deux cas", xy=(1.0, 0), xytext=(4, 0),
                  textcoords="offset points", va="center", fontsize=8.5,
                  color="0.4")
    ax_b.legend(fontsize=8.5, frameon=False, loc="lower right")
    ax_b.grid(alpha=0.25, axis="x")

    fig.suptitle("Dégradation jugée en temps × température, et non plus au pic",
                 y=0.98)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    savefig(fig, SORTIE_FIG)
    plt.close(fig)

    L = [
        "# Refaire le critère de dégradation : temps × température",
        "",
        f"Généré le {date.today().isoformat()}.",
        "",
        "## Ce qui clochait",
        "",
        "Tout le projet juge la dégradation sur un **seuil de pic** : dégradé si "
        "`T_max > 450 °C`. Deux défauts :",
        "",
        "- **Ce seuil n'a aucune provenance.** C'est un littéral répété dans huit "
        "scripts, absent de `materiaux.yaml` et de toute référence du corpus. Aucune "
        "donnée de cinétique (TGA, Arrhenius) sur le PEKK n'existe dans la "
        "bibliographie du projet.",
        "- **Il ne voit qu'un facteur.** Il déclare identiques une brève excursion à "
        "450 °C et une demi-heure de maintien à 400 °C. Les calculs de modulation "
        "ont buté exactement là.",
        "",
        "## Ce qui le remplace",
        "",
        "Dose d'Arrhenius du premier ordre "
        "(`code/src/jumeau/thermique/dose_degradation.py`) :",
        "",
        r"$$D = \frac{1}{t_{ref}} \int \exp\left(-\frac{E_a}{R}\left(\frac{1}{T(t)}"
        r" - \frac{1}{T_{ref}}\right)\right) dt \qquad \text{dégradé si } D > 1$$",
        "",
        f"**L'ancrage ne crée aucun seuil nouveau** : `D = 1` correspond exactement à "
        f"l'ancien critère relu comme une exposition — {T_REF_DEFAUT:.0f} °C pendant "
        f"une durée de passe ({T_REF_DUREE:.0f} s). La seule hypothèse ajoutée est "
        "l'énergie d'activation.",
        "",
        f"![Critère de dose](figures/{SORTIE_FIG.name})",
        "",
        "Lu en durée admissible à température constante (Ea = 150 kJ/mol) :",
        "",
        "| température | durée admissible |",
        "|---|---|",
        *[f"| {T:.0f} °C | {temps_limite(T):.0f} s |"
          for T in (337.0, 360.0, 380.0, 400.0, 420.0, 450.0, 480.0)],
        "",
        "## Ce que le changement de critère déplace",
        "",
        "| scénario | pic | durée | ancien : soudé / dégradé | "
        + " | ".join(f"Ea={e/1e3:.0f}" for e in EAS) + " |",
        "|---|---|---|---|" + "---|" * len(EAS),
    ]
    for nom, pic_max, duree_tot, a_soude, a_deg, par_ea in lignes:
        cells = " | ".join(f"{par_ea[e]['pct_soude']:.0f} / "
                           f"{par_ea[e]['pct_degrade']:.0f} %" for e in EAS)
        L.append(f"| {nom} | {pic_max:.0f} °C | {duree_tot:.0f} s | "
                 f"{a_soude:.0f} / {a_deg:.0f} % | {cells} |")
    L += [
        "",
        "(colonnes Ea : soudé / dégradé, en %)",
        "",
        "## Règle de lecture",
        "",
        "`Ea` n'est pas mesurée dans ce projet. **Un résultat qui change de signe "
        "entre 100 et 250 kJ/mol doit être dit indécidable, pas tranché.** Le "
        "balayage est là pour ça, et il fait partie du résultat — pas d'une annexe.",
        "",
        "Reproduire : "
        "`.venv/bin/python code/scripts/gen/gen_critere_dose_degradation.py`",
    ]
    SORTIE_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("ecrit :", SORTIE_MD)
    print("ecrit :", SORTIE_FIG)


if __name__ == "__main__":
    main()
