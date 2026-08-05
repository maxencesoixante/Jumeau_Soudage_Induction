"""Style partagé des figures — source unique du thème matplotlib (issue #17).

Remplace les blocs ``mpl.rcParams.update({...})`` dupliqués dans les scripts
``gen_*.py`` par un appel unique ``apply_style(**overrides)``. Le noyau commun
(polices, labels gras, 600 dpi, bbox serré) est défini ici ; chaque figure
passe seulement ses réglages spécifiques (taille de police, marge…) en
surcharge — le rendu reste identique.

Voir ``docs/reference_brassard.md`` (§Axe figures) pour la motivation : le dépôt
de référence Brassard réutilise un unique ``elsevier_theme`` là où nous
redéfinissions le style dans chaque script.
"""

from __future__ import annotations

import matplotlib as mpl

# --------------------------------------------------------------------------- #
# Palette Okabe-Ito (colorblind-safe) — imposée pour toutes les figures.
# --------------------------------------------------------------------------- #
OKABE_ITO = {
    "noir": "#000000",
    "orange": "#E69F00",
    "cyan": "#56B4E9",
    "vert": "#009E73",
    "jaune": "#F0E442",
    "bleu": "#0072B2",
    "vermillon": "#D55E00",
    "rose": "#CC79A7",
}
#: Gris neutre conventionnel pour les courbes « modèle » (hors palette catégorielle).
GRIS_MODELE = "#555555"

#: Colormap perceptuel UNIQUE pour les cartes de température (remplace ``jet``,
#: non perceptuel et non colorblind-safe). Cohérent avec les cartes ``inferno``
#: déjà utilisées (``gen_empreinte_soudure``, ``gen_mfc_reduit``).
CMAP_TEMP = "inferno"

# --------------------------------------------------------------------------- #
# Noyau de style.
#   _FONTS   : les 3 clés que TOUS les scripts fixent à l'identique.
#   _FIGURE  : le noyau des figures « imprimées » (labels gras, 600 dpi, bbox).
# Ce qui varie d'une figure à l'autre (font.size, pad_inches, tailles de ticks,
# largeurs de trait…) N'EST PAS ici : ça passe en ``overrides`` pour préserver
# le rendu exact de chaque figure.
# --------------------------------------------------------------------------- #
_FONTS = {
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "mathtext.fontset": "dejavusans",
}
_FIGURE = {
    "axes.labelweight": "bold",
    "figure.dpi": 600,
    "savefig.dpi": 600,
    "savefig.bbox": "tight",
}


def apply_style(*, fonts_only: bool = False, **overrides) -> None:
    """Applique le style partagé aux ``rcParams`` matplotlib.

    Parameters
    ----------
    fonts_only :
        Si vrai, n'applique que le noyau de polices (cas des figures qui gèrent
        leur DPI/format à la main, p. ex. les animations).
    **overrides :
        Réglages ``rcParams`` spécifiques à la figure (``font.size``,
        ``savefig.pad_inches``, ``legend.fontsize``…), appliqués par-dessus le
        noyau. Passer ici tout ce qui n'est pas commun garantit un rendu
        identique à l'ancien bloc en dur.
    """
    mpl.rcParams.update(_FONTS)
    if not fonts_only:
        mpl.rcParams.update(_FIGURE)
    if overrides:
        mpl.rcParams.update(overrides)
