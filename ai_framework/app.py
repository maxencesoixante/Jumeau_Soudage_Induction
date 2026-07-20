"""Interface conversationnelle du jumeau — orchestrateur multi-agents (local).

Un modèle de langage LOCAL servi par Ollama joue le chef d'orchestre (« Planner ») :
via le function-calling, il enchaîne les trois outils (config → simulation →
visualisation) et s'auto-corrige sur leurs erreurs. Aucune clé API, aucun appel
réseau externe.

Prérequis :
  1. Installer Ollama : https://ollama.com/download  (ou `brew install ollama`)
  2. Lancer le serveur : `ollama serve`  (souvent démarré automatiquement)
  3. Télécharger un modèle capable de tool-calling : `ollama pull qwen2.5`
Lancement :
  .venv/bin/python ai_framework/app.py           # http://127.0.0.1:7860
Le modèle est configurable via la variable d'environnement OLLAMA_MODEL.
"""

from __future__ import annotations

import os
from pathlib import Path

import gradio as gr
import ollama

from outils import DISPATCH, IMAGES_PRODUITES, SCHEMAS
from skills import PROMPT_SYSTEME

MODELE = os.environ.get("OLLAMA_MODEL", "qwen2.5")
HOTE = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
MAX_TOURS_OUTILS = 8  # garde-fou contre les boucles d'un modèle local

client = ollama.Client(host=HOTE)


def _appeler_outils(tool_calls) -> list[dict]:
    """Exécute les outils demandés et renvoie leurs résultats (rôle 'tool')."""
    resultats = []
    for tc in tool_calls:
        nom = tc.function.name
        args = dict(tc.function.arguments or {})
        fonction = DISPATCH.get(nom)
        if fonction is None:
            contenu = f"❌ Outil inconnu : {nom}."
        else:
            try:
                contenu = fonction(**args)
            except Exception as exc:  # arguments invalides, etc. → self-correction
                contenu = f"❌ Erreur d'exécution de {nom} : {exc}"
        resultats.append({"role": "tool", "tool_name": nom, "content": str(contenu)})
    return resultats


def repondre(message: str, chat: list, hist: list):
    """Un tour de conversation : plan → outils (avec self-correction) → réponse."""
    if not message.strip():
        return chat, [], hist, ""

    IMAGES_PRODUITES.clear()
    chat = chat + [{"role": "user", "content": message}]
    hist = hist + [{"role": "user", "content": message}]

    try:
        texte = "(aucune réponse)"
        for _ in range(MAX_TOURS_OUTILS):
            rep = client.chat(model=MODELE, messages=hist, tools=SCHEMAS)
            msg = rep.message
            # Force le séquentiel : on n'honore qu'UN outil par tour (les petits
            # modèles batchent en parallèle et hallucinent les arguments des
            # appels suivants ; en n'exécutant que le premier et en lui rendant
            # son résultat, le modèle re-planifie avec le vrai nom de session).
            appels = list(msg.tool_calls or [])[:1]
            message = msg.model_dump()
            message["tool_calls"] = [a.model_dump() for a in appels] or None
            hist = hist + [message]
            if not appels:
                texte = msg.content or texte
                break
            hist = hist + _appeler_outils(appels)
        chat = chat + [{"role": "assistant", "content": texte}]
    except ConnectionError:
        chat = chat + [{"role": "assistant", "content":
                        "⚠ Impossible de joindre Ollama. Lance `ollama serve` puis "
                        f"`ollama pull {MODELE}`."}]
    except Exception as exc:
        chat = chat + [{"role": "assistant", "content": f"⚠ Erreur : {exc}"}]

    return chat, list(IMAGES_PRODUITES), hist, ""


EXEMPLES = [
    "Lance l'essai de chauffe de référence et montre-moi les courbes des thermocouples.",
    "Simule l'essai de chauffe à 260 A et trace la carte de température de l'interface.",
    "Configure une chauffe à 600 A.",  # déclenche la self-correction (hors bornes)
]

with gr.Blocks(title="Jumeau Soudage Induction — Assistant IA (local)") as demo:
    gr.Markdown(
        f"## Jumeau numérique — Soudage par induction CF/PEKK\n"
        f"Modèle local **{MODELE}** via Ollama (aucune clé API). Décris un essai en "
        f"langage naturel : l'assistant configure, simule (modèle 2D à l'interface) "
        f"et trace les résultats, en s'auto-corrigeant sur les erreurs."
    )
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(height=460, label="Conversation")
            entree = gr.Textbox(placeholder="Ex. : lance l'essai de chauffe à 260 A et trace la carte",
                                label="Demande", autofocus=True)
            gr.Examples(EXEMPLES, inputs=entree, label="Exemples")
        with gr.Column(scale=2):
            galerie = gr.Gallery(label="Figures produites", height=460, columns=1)

    hist_systeme = [{"role": "system", "content": PROMPT_SYSTEME}]
    etat = gr.State(hist_systeme)  # historique brut (rôles system/user/assistant/tool)
    entree.submit(repondre, [entree, chatbot, etat], [chatbot, galerie, etat, entree])


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)
