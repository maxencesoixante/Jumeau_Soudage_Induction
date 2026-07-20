"""Les trois outils (« agents ») — fonctions Python + schémas JSON.

Indépendants du fournisseur LLM : de simples fonctions qui enveloppent le code
physique existant du jumeau (scripts CLI en sous-processus), plus une liste de
schémas ``SCHEMAS`` (format function-calling OpenAI/Ollama) et un ``DISPATCH``
nom→fonction utilisés par l'orchestrateur.

Self-correction : un outil qui échoue renvoie une chaîne préfixée « ❌ … » avec
le motif exact (bornes, sortie console du solveur). L'orchestrateur lit ce motif
et rappelle l'outil avec des paramètres corrigés.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import yaml

from verifs import valider_parametres

RACINE = Path(__file__).resolve().parents[1]
ESSAIS = RACINE / "config" / "essais"
RESULTATS = RACINE / "resultats"
# Interpréteur courant (celui qui exécute app.py) → indépendant de l'OS et de
# l'emplacement du venv : .venv/bin/python sous Unix, .venv\Scripts\python.exe
# sous Windows. Lancer app.py avec le python du venv suffit.
PYTHON = sys.executable

# Paramètres du modèle 2D calibrés (positions TC corrigées, 2026-07-20).
# Voir resultats_calibration.log — entrée « POSITIONS CORRIGEES ».
FACTEUR_COUPLAGE = 4.3139
DECALAGE_X = 0.0
H_HAUT = 2.4269
H_BAS_2D = 66.662

# Collecteur des images produites pendant un tour de conversation. app.py le vide
# au début de chaque message utilisateur puis affiche ce qui s'y trouve.
IMAGES_PRODUITES: list[str] = []


def config_essai(essai_reference: str, courant: float | None = None,
                 consigne_interface: float | None = None,
                 duree_chauffe: float | None = None,
                 duree_totale: float | None = None) -> str:
    """Génère un YAML de session validé à partir d'un essai de référence."""
    base = ESSAIS / f"{essai_reference}.yaml"
    if not base.exists():
        dispo = ", ".join(p.stem for p in sorted(ESSAIS.glob("*.yaml"))
                          if not p.stem.startswith("_"))
        return (f"❌ Essai de référence « {essai_reference} » introuvable. "
                f"Références disponibles : {dispo}.")

    # encoding explicite : les YAML de référence contiennent des commentaires
    # UTF-8 (accents, « », →) que Windows lirait en cp1252 par défaut → crash.
    with open(base, encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    modifs = {}
    for cle, val, unite in (("courant", courant, "A"),
                            ("consigne_interface", consigne_interface, "°C"),
                            ("duree_chauffe", duree_chauffe, "s"),
                            ("duree_totale", duree_totale, "s")):
        if val is not None:
            spec[cle] = val
            modifs[cle] = f"{val} {unite}"

    ok, messages = valider_parametres(spec)
    if not ok:
        return ("❌ Configuration rejetée (paramètres physiquement invalides) :\n"
                + "\n".join(messages))

    nom = f"_session_{int(time.time() * 1000) % 10_000_000}"
    spec["nom"] = nom
    # écriture en UTF-8 : le cœur relit ce fichier en encoding="utf-8"
    # (src/jumeau/validation/chargement.py) — rester cohérent des deux côtés.
    with open(ESSAIS / f"{nom}.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(spec, f, allow_unicode=True, sort_keys=False)

    resume = ", ".join(f"{k}={v}" for k, v in modifs.items()) or "aucune (essai tel quel)"
    avert = ("\nAvertissements : " + " ; ".join(messages)) if messages else ""
    return (f"Configuration « {nom} » créée à partir de « {essai_reference} ». "
            f"Modifications : {resume}.{avert}\n"
            f"→ passe « {nom} » à lancer_simulation.")


def lancer_simulation(essai: str, nx: int = 31, ny: int = 11) -> str:
    """Exécute le solveur thermique 2D sur une configuration d'essai."""
    if not (ESSAIS / f"{essai}.yaml").exists():
        return f"❌ Essai « {essai} » introuvable. Utilise d'abord config_essai."

    cmd = [PYTHON, "-u", "scripts/valider.py", "--modele", "2D",
           "--facteur", str(FACTEUR_COUPLAGE), "--decalage-x", str(DECALAGE_X),
           "--h-haut", str(H_HAUT), "--h-bas-2d", str(H_BAS_2D),
           "--nx", str(nx), "--ny", str(ny), "--essais", essai]
    # UTF-8 explicite des deux côtés : le solveur imprime °C, « écart », des
    # tableaux — sous Windows le défaut serait cp1252 (mojibake / UnicodeError).
    # PYTHONUTF8/PYTHONIOENCODING forcent l'enfant à émettre de l'UTF-8 ;
    # encoding="utf-8", errors="replace" garantissent un décodage parent sans crash.
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    try:
        proc = subprocess.run(cmd, cwd=RACINE, capture_output=True, timeout=600,
                              encoding="utf-8", errors="replace", env=env)
    except subprocess.TimeoutExpired:
        return (f"❌ La simulation de « {essai} » a dépassé le délai (600 s) avec "
                f"nx={nx}, ny={ny}. Relance lancer_simulation avec une grille plus "
                f"grossière (par ex. nx=21, ny=9) pour accélérer le calcul.")

    if proc.returncode != 0:
        console = (proc.stderr or proc.stdout)[-1500:]
        return (f"❌ La simulation de « {essai} » a échoué (code {proc.returncode}). "
                f"Sortie console du solveur :\n{console}")

    metriques = proc.stdout[proc.stdout.find("==="):].strip() or proc.stdout[-1200:]
    return (f"Simulation de « {essai} » terminée. Métriques (2D, sans recalage) :\n"
            f"{metriques}\n→ appelle tracer_resultats pour afficher les figures.")


def tracer_resultats(essai: str, figure: str = "courbes") -> str:
    """Sélectionne et affiche une figure produite par la simulation."""
    suffixe = "carte_interface_validation" if figure.startswith("carte") else "courbes_validation"
    chemin = RESULTATS / f"{essai}_{suffixe}.png"
    if not chemin.exists():
        return (f"❌ Figure « {figure} » introuvable pour « {essai} » ({chemin.name}). "
                f"Lance d'abord lancer_simulation.")
    IMAGES_PRODUITES.append(str(chemin))
    quoi = ("carte de température à l'interface de soudure" if figure.startswith("carte")
            else "courbes des thermocouples (trait plein = mesuré, pointillé = simulé)")
    return f"Figure affichée : {quoi} ({chemin.name})."


# --- Schémas function-calling (vus par le LLM) et table de dispatch ----------
SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "config_essai",
            "description": (
                "Prépare un fichier de configuration d'essai validé. Part d'un essai "
                "de RÉFÉRENCE existant et n'applique que les modifications demandées, "
                "puis valide physiquement les grandeurs (embedded checks). Appeler EN "
                "PREMIER. Références : 'chauffe_250A_3TC' (chauffe simple), 'serieA_A-1', "
                "'serieA_A-3', 'serieB_B-2' (soudage 4 empreintes, 5 TC à l'interface)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "essai_reference": {"type": "string", "description": "nom de l'essai de base sans .yaml"},
                    "courant": {"type": "number", "description": "ampérage en A (0-400 ; mesuré 200-250)"},
                    "consigne_interface": {"type": "number", "description": "température de coupure en °C (100-450)"},
                    "duree_chauffe": {"type": "number", "description": "durée de chauffe effective en s"},
                    "duree_totale": {"type": "number", "description": "durée totale simulée en s"},
                },
                "required": ["essai_reference"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lancer_simulation",
            "description": (
                "Exécute le solveur thermique 2D sur une configuration d'essai (~quelques "
                "secondes) et renvoie les métriques par thermocouple. En cas d'erreur de "
                "convergence/dimension, la sortie console est renvoyée : augmenter nx et ny "
                "puis relancer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "essai": {"type": "string", "description": "nom de l'essai (renvoyé par config_essai)"},
                    "nx": {"type": "integer", "description": "nœuds selon la longueur (défaut 31 ; 41-49 si problème)"},
                    "ny": {"type": "integer", "description": "nœuds selon la largeur (défaut 11)"},
                },
                "required": ["essai"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tracer_resultats",
            "description": (
                "Affiche une figure produite par la simulation. À appeler APRÈS "
                "lancer_simulation. 'courbes' = température-temps des thermocouples "
                "(simulé vs mesuré) ; 'carte' = carte de température à l'interface."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "essai": {"type": "string", "description": "nom de l'essai simulé"},
                    "figure": {"type": "string", "enum": ["courbes", "carte"], "description": "figure à afficher"},
                },
                "required": ["essai"],
            },
        },
    },
]

DISPATCH = {
    "config_essai": config_essai,
    "lancer_simulation": lancer_simulation,
    "tracer_resultats": tracer_resultats,
}
