"""Pousse un corps d'issue versionné du dépôt vers GitHub.

Le corps des issues « longues » (prédictions figées, synthèses illustrées) vit
dans `biblio/modele/issue<N>_*.md` et non seulement sur GitHub : on en garde
ainsi l'historique, et on peut le régénérer ou le relire hors ligne.

    .venv/bin/python code/scripts/gen/sync_issue.py 70
    .venv/bin/python code/scripts/gen/sync_issue.py 70 --bump    # + cache images

DEUX LEÇONS DE TERRAIN SONT ENCODÉES ICI, apprises en publiant l'issue #70.

1. LE CACHE D'IMAGES. GitHub sert les figures depuis `raw.githubusercontent.com`
   avec `cache-control: max-age=300`. Remplacer un PNG AU MÊME CHEMIN ne suffit
   donc pas : le navigateur continue d'afficher l'ancienne image, et le lecteur
   conclut que la modification n'a pas été faite. `--bump` incrémente le `?v=`
   de chaque URL, ce qui change l'adresse et rend tout cache inopérant.
   **À passer chaque fois qu'une figure déjà publiée a été régénérée.**

2. VÉRIFIER CE QUI S'AFFICHE, PAS CE QU'ON A ÉCRIT. Une URL peut pointer vers un
   fichier supprimé du dépôt : l'issue se met à jour sans erreur et affiche une
   image cassée. Chaque URL est donc testée AVANT la mise à jour, et un échec
   interrompt la synchro plutôt que de publier une issue trouée.

Le fichier source porte en tête un commentaire HTML (invisible une fois rendu)
qui rappelle qu'il est la source de vérité. Éditer l'issue dans le navigateur
fait diverger les deux : la synchro suivante écrase, sans avertissement.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
SOURCES = R / "biblio" / "modele"


def fichier_source(numero: int) -> Path:
    trouves = sorted(SOURCES.glob(f"issue{numero}_*.md"))
    if not trouves:
        raise SystemExit(f"aucun corps versionné pour l'issue #{numero} dans {SOURCES}")
    if len(trouves) > 1:
        raise SystemExit(f"plusieurs candidats pour #{numero} : {[f.name for f in trouves]}")
    return trouves[0]


def bumper(texte: str) -> tuple[str, int]:
    """Incrémente le ?v= de chaque image ; le pose à 1 s'il est absent."""
    versions = [int(v) for v in re.findall(r"\?v=(\d+)", texte)]
    suivante = (max(versions) + 1) if versions else 1
    texte = re.sub(r"(\.png)\?v=\d+", rf"\1?v={suivante}", texte)
    texte = re.sub(r"(\.png)(?=\))", rf"\1?v={suivante}", texte)
    return texte, suivante


def verifier_images(texte: str) -> list[str]:
    """Renvoie la liste des URL qui ne répondent pas — vides si tout va bien."""
    echecs = []
    for url in re.findall(r"!\[.*?\]\((https?://[^)]+)\)", texte):
        try:
            urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=15)
        except (urllib.error.HTTPError, urllib.error.URLError, OSError) as err:
            echecs.append(f"{getattr(err, 'code', type(err).__name__)}  {url}")
    return echecs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("numero", type=int, help="numéro de l'issue")
    ap.add_argument("--bump", action="store_true",
                    help="incrémente le ?v= des images (figures régénérées)")
    ap.add_argument("--verifier-seulement", action="store_true",
                    help="contrôle les images sans rien publier")
    ap.add_argument("--forcer-close", action="store_true",
                    help="autorise la republication vers une issue CLOSE (archive)")
    a = ap.parse_args()

    source = fichier_source(a.numero)
    texte = source.read_text(encoding="utf-8")

    if a.bump:
        texte, version = bumper(texte)
        source.write_text(texte, encoding="utf-8")
        print(f"cache images -> ?v={version}")

    images = re.findall(r"!\[.*?\]\((https?://[^)]+)\)", texte)
    print(f"{source.relative_to(R)} : {len(texte)} caractères, {len(images)} image(s)")

    echecs = verifier_images(texte)
    if echecs:
        print("\nIMAGES INJOIGNABLES — synchro interrompue :", file=sys.stderr)
        for e in echecs:
            print(f"  {e}", file=sys.stderr)
        raise SystemExit("publier maintenant afficherait une issue trouée")
    print(f"les {len(images)} image(s) répondent")

    if a.verifier_seulement:
        print("vérification seule, rien n'a été publié")
        return

    # Une issue CLOSE est un record historique : son corps est archivé au dépôt,
    # pas piloté depuis lui. Republier y réécrirait une trace figée.
    etat = subprocess.run(["gh", "issue", "view", str(a.numero), "--json", "state",
                           "-q", ".state"], capture_output=True, text=True, cwd=R)
    if etat.stdout.strip() == "CLOSED" and not a.forcer_close:
        raise SystemExit(f"issue #{a.numero} est CLOSE — archive seulement. "
                         f"Passer --forcer-close pour republier malgré tout.")

    subprocess.run(["gh", "issue", "edit", str(a.numero), "--body-file", str(source)],
                   check=True, cwd=R, stdout=subprocess.DEVNULL)
    print(f"issue #{a.numero} mise à jour depuis le dépôt")


if __name__ == "__main__":
    main()
