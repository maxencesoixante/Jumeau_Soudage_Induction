"""Validation hors-ligne de la couche IA (`ia/`) — issue #7.

La boucle « live » (un vrai LLM local via Ollama émettant des appels d'outils) exige
un serveur Ollama + un modèle ~4,7 Go, hors CI. Ce module valide tout le reste — le
cœur DÉTERMINISTE — sans Ollama :

  * `verifs.valider_parametres` (embedded checks) : bornes physiques, avertissements ;
  * les 3 outils (`config_essai`, `lancer_simulation`, `tracer_resultats`) de bout en
    bout, y compris un VRAI run du solveur 2D et les chemins d'erreur « ❌ … » ;
  * la boucle d'orchestration de `app.repondre` (function-calling) avec un client
    Ollama MOCKÉ : exécution séquentielle (1 outil/tour), self-correction sur erreur,
    terminaison, garde-fou de tours, outil inconnu.

Le seul maillon non couvert ici = la QUALITÉ des appels d'outils d'un vrai modèle,
qui se teste à la main (cf. `ia/README.md`, section « live »).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

RACINE = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(RACINE / "ia"))

# gradio/ollama sont des dépendances de la couche IA (ia/requirements.txt),
# pas du cœur physique : si absentes, on saute plutôt que d'échouer la CI.
pytest.importorskip("yaml")
gr = pytest.importorskip("gradio")
pytest.importorskip("ollama")

import outils  # noqa: E402
import verifs  # noqa: E402
import app  # noqa: E402  (construit l'UI Gradio à l'import, sans lancer de serveur)


# --------------------------------------------------------------------------- #
# 1. Embedded checks (verifs.py) — purs, rapides
# --------------------------------------------------------------------------- #
def test_verifs_essai_de_reference_valide():
    ok, messages = verifs.valider_parametres({"courant": 250, "consigne_interface": 400})
    assert ok
    assert messages == []


def test_verifs_courant_hors_bornes_rejete():
    ok, messages = verifs.valider_parametres({"courant": 600})
    assert not ok
    assert any("hors bornes" in m for m in messages)


def test_verifs_courant_extrapolation_avertit_sans_rejeter():
    ok, messages = verifs.valider_parametres({"courant": 320})
    assert ok  # 320 A ∈ [0, 400] → accepté, mais > 250 mesuré
    assert any("extrapolation" in m for m in messages)


def test_verifs_consigne_hors_bornes_rejete():
    ok, _ = verifs.valider_parametres({"consigne_interface": 800})
    assert not ok


def test_verifs_duree_incoherente_rejete():
    ok, messages = verifs.valider_parametres({"duree_chauffe": 10, "duree_totale": 5})
    assert not ok
    assert any("incohérent" in m for m in messages)


def test_verifs_thermocouple_hors_plaque_rejete():
    ok, _ = verifs.valider_parametres({"thermocouples": {"TCx": {"x": 0.5, "y": 0.0}}})
    assert not ok  # x = 0,5 m > longueur 0,120 m


def test_verifs_frequence_differente_avertit():
    ok, messages = verifs.valider_parametres({"frequence_khz": 300.0})
    assert ok
    assert any("388" in m for m in messages)


# --------------------------------------------------------------------------- #
# 2. Les trois outils (outils.py) — VRAI solveur, chemins d'erreur
# --------------------------------------------------------------------------- #
def test_config_essai_reference_inconnue():
    r = outils.config_essai("essai_qui_nexiste_pas")
    assert r.startswith("❌")
    assert "introuvable" in r


def test_config_essai_hors_bornes_rejete():
    r = outils.config_essai("chauffe_250A_3TC", courant=600)
    assert r.startswith("❌")
    assert "rejetée" in r


def test_config_essai_cree_une_session(tmp_path_factory):
    r = outils.config_essai("chauffe_250A_3TC", courant=240)
    assert not r.startswith("❌")
    assert "courant=240 A" in r
    # une config de session éphémère a bien été écrite (gitignore : _session_*)
    nom = r.split("« ")[1].split(" »")[0]
    session = outils.ESSAIS / f"{nom}.yaml"
    assert session.exists()
    session.unlink()  # nettoyage


def test_lancer_simulation_essai_inconnu():
    r = outils.lancer_simulation("essai_qui_nexiste_pas")
    assert r.startswith("❌")
    assert "config_essai" in r  # oriente l'orchestrateur vers la bonne étape


@pytest.fixture(scope="module")
def figures_reelles():
    """Un VRAI run du solveur 2D (grille grossière ~3 s), partagé par les tests."""
    outils.IMAGES_PRODUITES.clear()
    r = outils.lancer_simulation("chauffe_250A_3TC", nx=21, ny=9)
    assert not r.startswith("❌"), r
    return "chauffe_250A_3TC", r


def test_lancer_simulation_reelle_renvoie_metriques(figures_reelles):
    _, sortie = figures_reelles
    assert "chauffe_250A_3TC" in sortie
    assert "RMSE" in sortie  # bloc de métriques par thermocouple présent


def test_tracer_resultats_courbes_et_carte(figures_reelles):
    essai, _ = figures_reelles
    outils.IMAGES_PRODUITES.clear()
    r1 = outils.tracer_resultats(essai, "courbes")
    r2 = outils.tracer_resultats(essai, "carte")
    assert not r1.startswith("❌") and not r2.startswith("❌")
    assert len(outils.IMAGES_PRODUITES) == 2
    assert all(Path(p).exists() for p in outils.IMAGES_PRODUITES)


def test_tracer_resultats_figure_absente():
    r = outils.tracer_resultats("essai_jamais_simule", "courbes")
    assert r.startswith("❌")
    assert "lancer_simulation" in r  # renvoie l'orchestrateur à l'étape manquante


# --------------------------------------------------------------------------- #
# 3. Boucle d'orchestration (app.repondre) — client Ollama MOCKÉ
# --------------------------------------------------------------------------- #
class _FakeFunction:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class _FakeToolCall:
    def __init__(self, name, arguments):
        self.function = _FakeFunction(name, arguments)

    def model_dump(self):
        return {"function": {"name": self.function.name,
                             "arguments": self.function.arguments}}


class _FakeMessage:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

    def model_dump(self):
        return {"role": "assistant", "content": self.content}


class _FakeResponse:
    def __init__(self, message):
        self.message = message


class _FakeClient:
    """LLM scripté : rejoue une séquence de messages, ignore les entrées.

    Enregistre chaque appel `chat` pour vérifier que la boucle a bien itéré.
    À court de script, renvoie un message final sans outil (fin de boucle propre).
    """

    def __init__(self, sequence):
        self._sequence = list(sequence)
        self.appels = []

    def chat(self, model, messages, tools):
        self.appels.append(messages)
        if self._sequence:
            return _FakeResponse(self._sequence.pop(0))
        return _FakeResponse(_FakeMessage(content="(fin)"))


def _hist_neuf():
    return [{"role": "system", "content": "sys"}]


def test_orchestration_termine_sans_outil(monkeypatch):
    """Un message sans tool_calls termine le tour et renvoie le texte."""
    monkeypatch.setattr(app, "client",
                        _FakeClient([_FakeMessage(content="Bonjour, que puis-je faire ?")]))
    chat, images, hist, vide = app.repondre("salut", [], _hist_neuf())
    assert chat[-1] == {"role": "assistant", "content": "Bonjour, que puis-je faire ?"}
    assert images == []
    assert vide == ""


def test_orchestration_un_seul_outil_par_tour(monkeypatch):
    """Deux tool_calls dans un message → SEUL le premier est exécuté (séquentiel)."""
    executes = []
    faux_dispatch = {
        "outil_a": lambda **k: executes.append("a") or "ok a",
        "outil_b": lambda **k: executes.append("b") or "ok b",
    }
    monkeypatch.setattr(app, "DISPATCH", faux_dispatch)
    sequence = [
        _FakeMessage(tool_calls=[_FakeToolCall("outil_a", {}),
                                 _FakeToolCall("outil_b", {})]),
        _FakeMessage(content="terminé"),
    ]
    fake = _FakeClient(sequence)
    monkeypatch.setattr(app, "client", fake)
    chat, _, _, _ = app.repondre("fais a et b", [], _hist_neuf())
    assert executes == ["a"]  # b jamais exécuté malgré l'appel batché
    assert chat[-1]["content"] == "terminé"
    assert len(fake.appels) == 2  # la boucle a re-planifié après l'outil


def test_orchestration_self_correction(monkeypatch):
    """Un outil renvoie « ❌ … » → la boucle re-planifie et corrige."""
    vus = []
    faux_dispatch = {
        "config_essai": lambda **k: vus.append(k.get("courant"))
        or ("❌ courant hors bornes" if k.get("courant", 0) > 400 else "config OK"),
    }
    monkeypatch.setattr(app, "DISPATCH", faux_dispatch)
    sequence = [
        _FakeMessage(tool_calls=[_FakeToolCall("config_essai", {"courant": 600})]),
        _FakeMessage(tool_calls=[_FakeToolCall("config_essai", {"courant": 250})]),
        _FakeMessage(content="Configuration corrigée à 250 A."),
    ]
    monkeypatch.setattr(app, "client", _FakeClient(sequence))
    chat, _, hist, _ = app.repondre("configure 600 A", [], _hist_neuf())
    assert vus == [600, 250]  # rejet puis correction
    assert chat[-1]["content"] == "Configuration corrigée à 250 A."
    # le motif de rejet a bien été rendu à l'orchestrateur (rôle 'tool')
    assert any(m.get("role") == "tool" and "❌" in m.get("content", "") for m in hist)


def test_orchestration_outil_inconnu_gere(monkeypatch):
    """Un nom d'outil inconnu ne casse pas la boucle (renvoie « ❌ »)."""
    monkeypatch.setattr(app, "DISPATCH", {})  # aucun outil connu
    sequence = [
        _FakeMessage(tool_calls=[_FakeToolCall("outil_fantome", {})]),
        _FakeMessage(content="ok"),
    ]
    monkeypatch.setattr(app, "client", _FakeClient(sequence))
    chat, _, hist, _ = app.repondre("appelle un fantôme", [], _hist_neuf())
    assert any(m.get("role") == "tool" and "Outil inconnu" in m.get("content", "")
               for m in hist)
    assert chat[-1]["content"] == "ok"


def test_orchestration_garde_fou_tours(monkeypatch):
    """Un modèle qui boucle sans fin est stoppé à MAX_TOURS_OUTILS."""
    faux_dispatch = {"boucle": lambda **k: "encore"}
    monkeypatch.setattr(app, "DISPATCH", faux_dispatch)
    # un client qui rappelle toujours le même outil, jamais de texte final
    boucle_infinie = [_FakeMessage(tool_calls=[_FakeToolCall("boucle", {})])
                      for _ in range(app.MAX_TOURS_OUTILS + 5)]
    fake = _FakeClient(boucle_infinie)
    monkeypatch.setattr(app, "client", fake)
    chat, _, _, _ = app.repondre("boucle", [], _hist_neuf())
    # la boucle s'arrête net à MAX_TOURS_OUTILS appels, sans planter
    assert len(fake.appels) == app.MAX_TOURS_OUTILS
    assert chat[-1]["role"] == "assistant"


def test_orchestration_ollama_injoignable(monkeypatch):
    """Ollama indisponible → message d'aide, pas de crash."""
    class _ClientKO:
        def chat(self, *a, **k):
            raise ConnectionError("connexion refusée")

    monkeypatch.setattr(app, "client", _ClientKO())
    chat, _, _, _ = app.repondre("salut", [], _hist_neuf())
    assert "Ollama" in chat[-1]["content"]
