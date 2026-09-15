"""Critère de dégradation en temps × température, à la place d'un seuil de pic.

POURQUOI. Tout le projet juge la dégradation sur un SEUIL DE PIC : « dégradé si
T_max > 450 °C ». Ce seuil est un littéral répété dans huit scripts, absent de la
configuration et de toute référence du corpus — sa provenance est introuvable. Et
surtout, un seuil de pic ne voit qu'un facteur : il déclare identiques une brève
excursion à 450 °C et une demi-heure de maintien à 400 °C. Les calculs de
modulation ont buté exactement là.

LE MODÈLE. Dégradation thermique du premier ordre, vitesse d'Arrhenius
``k(T) = A·exp(-Ea/RT)``. La DOSE accumulée le long d'un cycle vaut

    D = (1/t_ref) · ∫ exp( -Ea/R · (1/T(t) - 1/T_ref) ) dt

et la matière est déclarée dégradée quand ``D > 1``.

L'ANCRAGE, ET CE QU'IL CHANGE. La normalisation est choisie pour que D = 1
corresponde EXACTEMENT à l'ancien critère lu comme une exposition : ``T_ref``
pendant ``t_ref``, soit 450 °C pendant une durée de passe (20 s). Le critère neuf
n'introduit donc AUCUN seuil nouveau — il réinterprète celui qui existait comme
une dose plutôt que comme une température, ce qui est la seule lecture qui ait un
sens physique. La seule hypothèse ajoutée est ``Ea``, et elle est balayée.

Ea N'EST PAS MESURÉE ICI. Aucune donnée de cinétique (TGA, Arrhenius) n'existe
dans le corpus du projet pour le PEKK. L'ordre de grandeur retenu par défaut,
200 kJ/mol, est celui d'une dégradation thermique de polymère aromatique ; les
fonctions acceptent Ea en argument et les analyses doivent la BALAYER plutôt que
la fixer. Tant qu'elle n'est pas mesurée, un résultat qui change de signe entre
150 et 300 kJ/mol doit être présenté comme indécidable.

Équivalence lisible pour l'atelier : ``temps_limite(T)`` donne la durée
d'exposition admissible à température constante — c'est la forme utilisable pour
écrire une consigne de procédé.
"""

from __future__ import annotations

import numpy as np

R_GAZ = 8.314462618          # J/(mol·K)
KELVIN = 273.15
T_REF_DEFAUT = 450.0         # °C — ancien seuil de pic, relu comme température d'ancrage
T_REF_DUREE = 20.0           # s — durée de passe du procédé, relue comme durée d'ancrage
EA_DEFAUT = 150e3            # J/mol — ordre de grandeur, NON mesuré (cf. docstring)


def _vitesse_relative(T_celsius, ea: float, t_ref: float):
    """exp(-Ea/R · (1/T - 1/T_ref)) — vitesse rapportée à celle de ``t_ref``."""
    T = np.asarray(T_celsius, dtype=float) + KELVIN
    return np.exp(-ea / R_GAZ * (1.0 / T - 1.0 / (t_ref + KELVIN)))


def temps_limite(T_celsius, ea: float = EA_DEFAUT, t_ref: float = T_REF_DEFAUT,
                 duree_ref: float = T_REF_DUREE):
    """Durée d'exposition admissible (s) à la température constante donnée.

    Vaut ``duree_ref`` en ``t_ref`` par construction : le critère neuf coïncide
    avec l'ancien sur son point d'ancrage."""
    return duree_ref / _vitesse_relative(T_celsius, ea, t_ref)


def dose(champs, temps, ea: float = EA_DEFAUT, t_ref: float = T_REF_DEFAUT,
         duree_ref: float = T_REF_DUREE):
    """Dose accumulée en chaque point pour l'historique ``champs`` (nt, ...).

    ``temps`` (nt,) en secondes. Intégration trapézoïdale. ``dose > 1`` =
    dégradé. Renvoie un tableau de la forme d'UN champ."""
    champs = np.asarray(champs, dtype=float)
    temps = np.asarray(temps, dtype=float)
    if champs.shape[0] != temps.size:
        raise ValueError(f"champs a {champs.shape[0]} pas de temps, temps en a "
                         f"{temps.size} — les deux doivent coïncider.")
    vitesse = _vitesse_relative(champs, ea, t_ref)
    return np.trapezoid(vitesse, temps, axis=0) / duree_ref


def metriques_dose(champs, temps, fusion: float = 337.0,
                   ea: float = EA_DEFAUT, t_ref: float = T_REF_DEFAUT,
                   duree_ref: float = T_REF_DUREE) -> dict:
    """Couverture avec le critère de dose, dans la forme des métriques existantes.

    ``pct_soude`` = a dépassé la fusion ET dose <= 1 ; ``pct_degrade`` = dose > 1
    (que la matière ait fondu ou non) ; ``pct_non_soude`` = le reste."""
    champs = np.asarray(champs, dtype=float)
    D = dose(champs, temps, ea, t_ref, duree_ref)
    pic = champs.max(axis=0)
    degrade = D > 1.0
    soude = (pic >= fusion) & ~degrade
    n = float(pic.size)
    return {"pct_soude": float(soude.sum()) / n * 100.0,
            "pct_degrade": float(degrade.sum()) / n * 100.0,
            "pct_non_soude": float((~soude & ~degrade).sum()) / n * 100.0,
            "dose_max": float(D.max()), "dose_mediane": float(np.median(D))}
