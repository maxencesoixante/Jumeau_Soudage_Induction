# Couche IA — Assistant conversationnel du jumeau (architecture MatAgent, 100 % local)

Surcouche multi-agents (inspirée du framework MatAgent de Purdue) posée **par-dessus**
le solveur physique du jumeau, sans le modifier. Un modèle de langage **local**
(servi par Ollama, aucune clé API, aucun appel réseau externe) orchestre trois
outils et s'auto-corrige sur leurs erreurs.

## Architecture

```
Utilisateur ──▶ Orchestrateur (LLM local via Ollama, function-calling)
                   │  boucle plan → exécute → corrige
                   ├─▶ config_essai()       génère un YAML de session validé
                   ├─▶ lancer_simulation()  solveur 2D en sous-processus
                   └─▶ tracer_resultats()   renvoie les figures
```

- **Planner / orchestrateur** — un LLM local ; son prompt système (`skills.py`) porte
  le contexte métier (soudage induction CF/PEKK, 388 kHz, échantillon 120×40 mm) et
  le mandat de self-correction.
- **Skills** — les descriptions des outils (`outils.py`, liste `SCHEMAS`) disent au
  modèle quand les appeler, leurs bornes, et comment lire leurs erreurs.
- **Embedded checks** — `verifs.py` valide physiquement les paramètres avant tout
  calcul ; un rejet remonte à l'orchestrateur qui corrige.
- **Self-correction** — la boucle de function-calling : un outil renvoie une erreur
  (« ❌ … ») → le modèle la lit et rappelle l'outil avec des paramètres corrigés.

Le code est indépendant du fournisseur LLM (les outils sont de simples fonctions +
schémas JSON) : passer à une API cloud ne changerait que la boucle dans `app.py`.

## Fichiers

| Fichier | Rôle |
|---|---|
| `app.py` | UI Gradio + orchestrateur (function-calling Ollama) |
| `outils.py` | les 3 outils (fonctions + schémas JSON) — wrappers du code physique |
| `skills.py` | prompt système de l'orchestrateur |
| `verifs.py` | embedded checks (bornes physiques) |

## Installation et lancement

macOS / Linux :

```bash
# 1. Dépendances Python (dans le venv du projet)
.venv/bin/pip install -r ai_framework/requirements.txt

# 2. Ollama (serveur LLM local)
brew install ollama          # ou https://ollama.com/download
ollama serve &               # démarre le serveur (souvent auto au boot)
ollama pull qwen2.5          # modèle capable de tool-calling (~4,7 Go)

# 3. Lancer l'assistant
.venv/bin/python ai_framework/app.py        # http://127.0.0.1:7860
```

Windows (PowerShell) — mêmes étapes, chemin du venv différent :

```powershell
# 1. Dépendances Python
.venv\Scripts\pip install -r ai_framework\requirements.txt

# 2. Ollama : installer depuis https://ollama.com/download, puis
ollama serve
ollama pull qwen2.5

# 3. Lancer l'assistant (avec le python DU venv)
.venv\Scripts\python ai_framework\app.py     # http://127.0.0.1:7860
```

`app.py` retrouve seul le bon interpréteur pour les sous-processus du solveur
(`sys.executable`) : aucun chemin à adapter, à condition de le lancer avec le
python du venv.

Modèle configurable via `OLLAMA_MODEL` (ex. `llama3.1`, `mistral-nemo`). Les configs
de session (`config/essais/_session_*.yaml`) sont éphémères et ignorées par git.

## Exemples de requêtes

- « Lance l'essai de chauffe de référence et montre-moi les courbes des thermocouples. »
- « Simule l'essai de chauffe à 260 A et trace la carte de température de l'interface. »
- « Configure une chauffe à 600 A. » → déclenche la self-correction (hors bornes).
