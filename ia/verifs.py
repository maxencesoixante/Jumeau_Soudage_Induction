"""Embedded checks : validation physique des paramètres avant toute simulation.

Ces vérifications sont le premier maillon de la self-correction : si l'agent de
configuration propose une grandeur absurde (ampérage négatif, thermocouple hors
de la plaque…), la fonction renvoie un motif de rejet que l'orchestrateur LLM
lit et corrige, sans lancer de calcul inutile.

Bornes issues du domaine physique du jumeau (échantillon CF/PEKK 120×40 mm,
essais mesurés à 200-250 A, fréquence machine figée à 388 kHz).
"""

from __future__ import annotations

# Bornes physiques du problème (voir config/geometrie.yaml, cahier de labo).
COURANT_MIN, COURANT_MAX = 0.0, 400.0          # A — essais réels 200-250 A
CONSIGNE_MIN, CONSIGNE_MAX = 100.0, 450.0       # °C — dégradation PEKK ~450 °C
LONGUEUR_M, LARGEUR_M = 0.120, 0.040            # m — dimensions de l'échantillon
FREQUENCE_MACHINE_KHZ = 388.0                   # kHz — relevé machine, FIGÉ


def valider_parametres(params: dict) -> tuple[bool, list[str]]:
    """Valide un dict de paramètres d'essai. Retourne (ok, messages).

    ``ok`` est False dès qu'un paramètre est physiquement inacceptable (le calcul
    ne doit pas être lancé). Les messages incluent aussi de simples
    avertissements (ok reste True) que l'orchestrateur peut relayer à
    l'utilisateur.
    """
    erreurs: list[str] = []
    avertissements: list[str] = []

    courant = params.get("courant")
    if courant is not None:
        if not (COURANT_MIN <= courant <= COURANT_MAX):
            erreurs.append(
                f"courant = {courant} A hors bornes physiques "
                f"[{COURANT_MIN:.0f}, {COURANT_MAX:.0f}] A. Les essais mesurés "
                f"vont de 200 à 250 A."
            )
        elif courant > 300:
            avertissements.append(
                f"courant = {courant} A est au-delà de la plage mesurée "
                f"(≤ 250 A) : la prédiction est une extrapolation."
            )

    consigne = params.get("consigne_interface")
    if consigne is not None:
        if not (CONSIGNE_MIN <= consigne <= CONSIGNE_MAX):
            erreurs.append(
                f"consigne_interface = {consigne} °C hors bornes "
                f"[{CONSIGNE_MIN:.0f}, {CONSIGNE_MAX:.0f}] °C."
            )
        elif consigne > 420:
            avertissements.append(
                f"consigne_interface = {consigne} °C approche la dégradation "
                f"thermique du PEKK (~450 °C)."
            )

    d_chauffe = params.get("duree_chauffe")
    d_totale = params.get("duree_totale")
    if d_chauffe is not None and d_chauffe <= 0:
        erreurs.append(f"duree_chauffe = {d_chauffe} s doit être strictement positive.")
    if d_chauffe is not None and d_totale is not None and d_chauffe > d_totale:
        erreurs.append(
            f"duree_chauffe ({d_chauffe} s) > duree_totale ({d_totale} s) : "
            f"incohérent."
        )

    if params.get("frequence_khz") is not None:
        f = params["frequence_khz"]
        if abs(f - FREQUENCE_MACHINE_KHZ) > 1e-6:
            avertissements.append(
                f"fréquence {f} kHz ≠ {FREQUENCE_MACHINE_KHZ} kHz (relevé machine "
                f"figé). Le facteur de couplage est calibré à 388 kHz ; changer "
                f"la fréquence sans recalibrer n'a pas de sens physique."
            )

    for nom, pos in (params.get("thermocouples") or {}).items():
        x, y = pos.get("x"), pos.get("y")
        if x is not None and not (0.0 <= x <= LONGUEUR_M):
            erreurs.append(f"{nom}: x = {x} m hors de la longueur [0, {LONGUEUR_M}] m.")
        if y is not None and not (0.0 <= y <= LARGEUR_M):
            erreurs.append(f"{nom}: y = {y} m hors de la largeur [0, {LARGEUR_M}] m.")

    for i, spot in enumerate(params.get("spots") or []):
        cx = spot.get("centre_x")
        if cx is not None and not (0.0 <= cx <= LONGUEUR_M):
            erreurs.append(
                f"spot {i + 1}: centre_x = {cx} m hors de la longueur "
                f"[0, {LONGUEUR_M}] m."
            )

    messages = [f"❌ {e}" for e in erreurs] + [f"⚠ {a}" for a in avertissements]
    return (len(erreurs) == 0, messages)
