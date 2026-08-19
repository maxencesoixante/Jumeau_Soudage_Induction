"""Smoke live de la couche IA — VRAI LLM local (Ollama) via `app.repondre`.

Complément « live » aux tests hors-ligne (`tests/test_ai_framework.py`, mockés) :
exerce la boucle d'orchestration avec un serveur Ollama réel, mais SANS lancer l'UI
Gradio — appelle directement `app.repondre` et imprime la trace des appels d'outils.

Prérequis : `ollama serve` + un modèle tool-calling (`ollama pull qwen2.5`).
Lancement  : `.venv/bin/python ia/smoke_live.py`
Modèle configurable via `OLLAMA_MODEL`.

Ce qu'on vérifie :
  1. chaînage config_essai → lancer_simulation → tracer_resultats (1 outil/tour) ;
  2. respect des bornes physiques sur une demande absurde (courant hors domaine).

Résultat de référence (qwen2.5, 2026-08-04) : les deux scénarios passent — enchaînement
correct + figure produite ; 600 A refusé (self-correction dès la planification).
"""

from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "ia"))
sys.path.insert(0, str(RACINE / "code" / "src"))

import app  # noqa: E402  (client Ollama réel)
from skills import PROMPT_SYSTEME  # noqa: E402


def _trace(hist: list) -> None:
    for m in hist:
        if m.get("role") == "assistant" and m.get("tool_calls"):
            for tc in m["tool_calls"]:
                fn = tc["function"]
                print(f"   🔧 APPEL   {fn['name']}({fn.get('arguments')})")
        elif m.get("role") == "tool":
            resume = (m.get("content") or "").replace("\n", " ")[:130]
            print(f"   ↩︎  RÉSULTAT {resume}")


def _run(titre: str, message: str) -> None:
    print(f"\n{'=' * 70}\n▶ {titre}\n   Requête : « {message} »\n{'-' * 70}")
    hist = [{"role": "system", "content": PROMPT_SYSTEME}]
    chat, images, hist, _ = app.repondre(message, [], hist)
    _trace(hist)
    print(f"   💬 RÉPONSE : {chat[-1]['content'][:400]}")
    print(f"   🖼  IMAGES  : {[Path(p).name for p in images]}")


def main() -> None:
    print(f"Modèle : {app.MODELE} · hôte : {app.HOTE} · max tours : {app.MAX_TOURS_OUTILS}")
    _run("Scénario 1 — chaînage config → simulation → figure",
         "Simule l'essai de chauffe de référence (chauffe_250A_3TC) et montre-moi "
         "les courbes des thermocouples.")
    _run("Scénario 2 — bornes physiques (courant hors domaine)",
         "Configure une chauffe à 600 A.")
    print("\n✅ Smoke live terminé.")


if __name__ == "__main__":
    main()
