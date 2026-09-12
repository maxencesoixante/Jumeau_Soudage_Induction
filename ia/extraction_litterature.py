"""Equipe AutoGen d'extraction de la litterature vers le jumeau numerique.

Quatre agents specialistes — un par probleme ouvert du jumeau — lisent le corpus
converti (PDF Zotero -> markdown) et en extraient ce qui est reutilisable ; un
cinquieme agent recoupe leurs sorties et signale les contradictions.

Le modele est LOCAL (Ollama) : aucun article ne sort de la machine, ce qui compte
pour de la litterature sous licence. Meme convention que ia/app.py :
OLLAMA_MODEL / OLLAMA_HOST.

Prerequis :
  ollama serve && ollama pull qwen2.5:7b-instruct-q3_K_M
  pip install -U "autogen-agentchat" "autogen-ext[openai]"
Le script cree lui-meme, au premier lancement, son modele derive
(num_ctx=6144) : Ollama sert sinon 4096 tokens et tronque silencieusement le prompt.
OLLAMA_MODELE_BASE permet de changer de modele (machine plus ou moins dotee).

Lancement :
  python ia/extraction_litterature.py                # les 4 problemes
  python ia/extraction_litterature.py --probleme P1  # un seul
  python ia/extraction_litterature.py --corpus <dir> --sortie <fichier.md>

Note de conception : un modele 7B ne peut pas ingerer 81 articles. On lui fournit
donc des EXTRAITS selectionnes par mots-cles (fenetre de contexte autour de chaque
occurrence), et on lui interdit explicitement de sortir de ces extraits. Les articles
sont servis par DENSITE d'occurrences, avec un plafond par article : sans cela le
budget part entierement dans les premiers articles de l'alphabet.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import json
import time
import unicodedata
from pathlib import Path
from urllib.request import Request, urlopen

from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import ModelFamily
from autogen_ext.models.openai import OpenAIChatCompletionClient

HOTE = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
CORPUS_DEFAUT = Path("/Volumes/MAXENCE SD/Conversion_citekey")
# Le rapport est un LIVRABLE (plusieurs minutes d'inference locale a reproduire) :
# il va dans le depot, pas dans un repertoire temporaire de session.
SORTIE_DEFAUT = Path(__file__).resolve().parents[1] / "biblio/references/extraction_litterature.md"

# Fenetre d'extrait et budget par probleme : cales sur la fenetre de contexte reelle.
FENETRE = 700          # caracteres autour de chaque occurrence
BUDGET_EXTRAITS = 10000  # caracteres max envoyes a un agent (~2,5k tokens)
PAR_ARTICLE = 1800     # caracteres max retenus dans un meme article
TEMPERATURE = 0.2      # un 7B laisse libre derive de format et de langue

# Ollama sert 4096 tokens de contexte par defaut, quelle que soit la fenetre du
# modele (32k pour qwen2.5) : un prompt de 14 000 caracteres etait donc TRONQUE,
# et c'est la consigne de format qui sautait — d'ou les fiches hors format. On
# travaille sur un modele derive dont num_ctx est fixe explicitement.
NUM_CTX = 6144

# Choix du modele, mesure sur la machine de developpement (M1, 8 Go) :
#   qwen2.5:3b       tient en GPU, rapide — mais FABRIQUE des clefs de citation et
#                    confond conductivite electrique et thermique. Inexploitable
#                    pour un livrable bibliographique.
#   qwen2.5:7b (Q4)  fiches justes et citations exactes, mais 5,4-5,6 Go : le
#                    systeme tue le processus, a 8192 comme a 6144 de contexte.
#   qwen2.5:7b Q3_K_M  meme modele, quantification plus serree (~3,8 Go) : tient
#                    en memoire et garde le suivi d'instructions du 7B.
MODELE_BASE = os.environ.get("OLLAMA_MODELE_BASE", "qwen2.5:7b-instruct-q3_K_M")
# Ollama n'accepte pas de majuscule dans un nom de modele (la quantification, elle,
# s'ecrit « q3_K_M ») : on normalise avant de deriver.
MODELE_DERIVE = (MODELE_BASE.replace(":", "-") + "-jumeau").lower()
MODELE = os.environ.get("OLLAMA_MODEL", MODELE_DERIVE)

# Une inference locale lente ne doit pas mourir sur le delai par defaut du client.
DELAI_CLIENT = 1800.0

# Selon la passe d'OCR, l'unite s'ecrit W/(m·K), W/(m⋅K), W/m∙K, W/mK, W/m.K...
# Le separateur n'est PAS toujours le point median U+00B7 : on a aussi l'operateur
# point U+22C5 et l'operateur puce U+2219. Une classe trop etroite laissait passer
# les tableaux de proprietes, c'est-a-dire exactement les valeurs recherchees.
_SEP = r"[·⋅∙.\s]{0,3}"
UNITE_WMK = rf"W\s*/{_SEP}\(?\s*m{_SEP}K"
UNITE_WM2K = rf"W\s*/{_SEP}\(?\s*m2?{_SEP}K"
_NOMBRE = r"\d[\d\s.,]{0,8}"     # « 1.4 », « 0,25 », « 300 »

# --- les quatre problemes ouverts du jumeau -------------------------------
PROBLEMES = {
    "P1": {
        "titre": "Conduction thermique dans le plan (k_plan)",
        "contexte": (
            "Le jumeau doit calibrer k_plan a ~7,5 W/(m.K) alors que la valeur "
            "physique homogeneisee est ~3,0. Ecart x2,5, constant en courant. "
            "L'anisotropie thermique kx!=ky a DEJA ete ecartee (NO-GO) : ne pas la reproposer."
        ),
        "cherche": "toute conductivite thermique mesuree ou calculee (valeur, direction, "
                   "methode, materiau), et tout mecanisme d'etalement thermique",
        "mots": [r"in-?plane thermal conductivit", r"thermal conductivit",
                 UNITE_WMK, r"conductivite thermique", r"transverse conductivit",
                 r"anisotrop", r"homogeni[sz]ed"],
        "valeurs": rf"{_NOMBRE}{UNITE_WMK}",
    },
    "P2": {
        "titre": "Gradient dans l'epaisseur, pertes, conditions aux limites",
        "contexte": (
            "La face opposee a la bobine est sur-chauffee dans le modele ; le "
            "refroidissement simule est ~10% trop lent (residu attribue aux pertes)."
        ),
        "cherche": "coefficients de convection, emissivites, conductance de contact, "
                   "gradients mesures dans l'epaisseur, conditions aux limites thermiques",
        "mots": [r"convection coefficient", r"heat transfer coefficient", UNITE_WM2K,
                 r"emissivit", r"contact conductance", r"through-?thickness", r"cooling rate"],
        "valeurs": rf"{_NOMBRE}(?:{UNITE_WM2K}|°C\s*/\s*s)|emissivit\w*\D{{0,20}}0[.,]\d",
    },
    "P3": {
        "titre": "Fiber flow / squeeze-out / deconsolidation",
        "contexte": (
            "Fiber flow observe a chaque soudage. On parie sur une chauffe plus "
            "uniforme (MFC raccourci) pour le reduire : hypothese JAMAIS verifiee."
        ),
        "cherche": "mecanisme dominant (thermique ? pression ? viscosite ? temps au-dessus "
                   "de Tf ?), seuils de pression, criteres quantitatifs, deconsolidation",
        "mots": [r"squeeze[- ]?flow", r"fib(er|re) flow", r"deconsolidat", r"resin percolat",
                 r"intimate contact", r"consolidation pressure", r"MPa", r"viscosit"],
        "valeurs": rf"{_NOMBRE}(?:M?Pa\s*[·⋅.]?\s*s|MPa|bar)\b",
    },
    "P4": {
        "titre": "Concentrateur de flux (MFC), effet de bord, sigma(T)",
        "contexte": (
            "Ferrotron 559H, mu_r=16. Question du raccourcissement du MFC (55 -> 31,75 mm) "
            "et de l'extrapolation a 275 A. sigma est traitee comme CONSTANTE dans foucault.py."
        ),
        "cherche": "permeabilite et geometrie de concentrateurs, effets de bord, uniformite "
                   "de chauffe, saturation magnetique, et dependance de la conductivite "
                   "electrique a la temperature",
        "mots": [r"flux concentrator", r"magnetic flux controller", r"edge effect",
                 r"permeabilit", r"mu_?r", r"saturation", r"electric(al)? conductivit",
                 r"S/m", r"skin depth"],
        "valeurs": rf"{_NOMBRE}(?:S\s*/\s*m|k?Hz|S\.m)|permeabilit\w*\D{{0,25}}\d",
    },
}

CONSIGNE_COMMUNE = """Tu es un ingenieur de recherche qui depouille de la litterature
scientifique pour un jumeau numerique du soudage par induction de composites CF/PEKK.

REGLES ABSOLUES :
- Tu ne disposes QUE des extraits fournis. Tout ce que tu affirmes doit s'y trouver.
- N'invente AUCUN chiffre, AUCUN titre, AUCUN auteur. Si un extrait est trop partiel
  pour conclure, ecris "extrait insuffisant" plutot que de completer de memoire.
- Cite systematiquement le fichier source entre crochets, ex. [Moser2012].
- Les chiffres cites dans la section "Contexte du jumeau" sont ceux de NOTRE modele,
  PAS ceux d'une publication : ne JAMAIS les attribuer a une source du corpus.
  Ils te disent seulement ce qu'on cherche a confronter.
- Distingue ce qui est MESURE de ce qui est CALCULE ou SUPPOSE dans la source.
- Le francais est la langue de reponse ; les termes techniques restent en anglais.
- Sois bref : des faits utilisables, pas de paraphrase.

FORMAT — les trois titres, dans cet ordre :
## Valeurs numeriques reutilisables
Une ligne par valeur REELLEMENT LUE dans un extrait, colonnes separees par « | » :
grandeur | valeur + unite | materiau | mesure ou calcul | [source]
Exemple du resultat attendu (ce ne sont PAS des donnees du corpus) :
conductivite transverse | 0,72 W/(m.K) | CF/PEEK UD | mesure | [Dupont2019]
N'ECRIS JAMAIS les mots « grandeur », « valeur + unite » ou « materiau » : ce sont
les intitules du gabarit, pas des donnees. Si aucun extrait ne donne de valeur
chiffree, ecris une seule ligne : « aucune valeur chiffree dans les extraits ».
## Mecanismes et resultats qualitatifs
## Ce que les extraits ne permettent PAS de conclure
"""


CITEKEY = re.compile(r"^[A-Z][A-Za-z']+\d{4}[a-z]?(-\d)?$")

# --- controle de forme des reponses --------------------------------------
# Un 7B tenu par une seule consigne systeme derive : lors du premier depouillement
# complet, P2 est sorti en dissertation anglaise sans les titres demandes, et
# l'agent de synthese a fini sa reponse en chinois. On verifie donc la forme et on
# redemande une fois, plutot que d'ecrire une fiche inexploitable dans le rapport.
NON_LATIN = re.compile("[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]")  # kana, han, hangul
TITRES_FICHE = ("Valeurs numeriques reutilisables",
                "Mecanismes et resultats qualitatifs",
                "Ce que les extraits ne permettent PAS de conclure")


def _normaliser_source(nom: str) -> str:
    """Forme comparable d'un nom de source.

    Les noms de fichiers portent l'apostrophe typographique (O’Shaughnessey) et le
    modele reecrit une apostrophe droite : une egalite stricte signalait comme
    fabriquee une source pourtant reelle. Meme traitement pour les espaces.
    """
    for q in "\u2019\u2018\u02bc`":
        nom = nom.replace(q, "'")
    return " ".join(nom.split())


def _pliable(texte: str) -> str:
    """Minuscules sans accents : le modele accentue ses titres de facon variable."""
    decompose = unicodedata.normalize("NFD", texte)
    return "".join(c for c in decompose if unicodedata.category(c) != "Mn").lower()


def defauts_fiche(texte: str, sources: set[str] | None = None) -> list[str]:
    plie = _pliable(texte)
    pbs = [f"titre manquant : « {t} »" for t in TITRES_FICHE if _pliable(t) not in plie]
    if NON_LATIN.search(texte):
        pbs.append("caracteres non latins (derive de langue)")
    # Une fiche peut passer le controle des titres tout en etant vide de substance :
    # un petit modele RECOPIE volontiers le gabarit (« grandeur | valeur + unite |
    # ... | [Source] ») en se contentant d'y glisser un nom de fichier. La forme est
    # alors parfaite et le contenu nul — d'ou un controle du gabarit lui-meme.
    if "valeur + unite" in plie or "grandeur |" in plie:
        pbs.append("gabarit recopie au lieu d'etre rempli")
    # Une citation fabriquee est le defaut le plus couteux d'un livrable
    # bibliographique : elle est indiscernable d'une vraie a la lecture, et c'est
    # tout l'interet du depouillement qui tombe. Le corpus etant connu, la
    # verification est exacte — on n'a pas a s'en remettre au modele.
    if sources is not None:
        # Un crochet peut porter PLUSIEURS sources — « [Talbot2013, Martin2024] » —
        # et les comparer en bloc signalait a tort des references pourtant reelles.
        connues = {_normaliser_source(n) for n in sources}
        cites = set()
        for groupe in re.findall(r"\[([^\]\n]{2,120})\]", texte):
            cites.update(c.strip() for c in re.split(r"[;,]| et ", groupe) if c.strip())
        inconnues = sorted(c for c in cites if _normaliser_source(c) not in connues)
        if inconnues:
            pbs.append("source(s) absente(s) du corpus : " + ", ".join(inconnues[:4]))
    return pbs


def defauts_synthese(texte: str) -> list[str]:
    pbs = []
    if NON_LATIN.search(texte):
        pbs.append("caracteres non latins (derive de langue)")
    if len(texte.split()) > 600:
        pbs.append("depasse largement les 400 mots demandes")
    return pbs


async def produire(nom: str, client, consigne: str, tache: str,
                   controle, essais: int = 2) -> str:
    """Interroge un agent neuf et redemande si la forme de la reponse est fautive.

    Un agent neuf a chaque essai : reutiliser le meme laisse la reponse fautive
    dans son historique, ce qui l'ancre au lieu de l'en detourner.
    """
    texte, pbs = "", []
    for essai in range(1, essais + 1):
        agent = AssistantAgent(name=f"{nom}_{essai}", model_client=client,
                               system_message=consigne)
        relance = "" if essai == 1 else (
            "\n\nTA REPONSE PRECEDENTE ETAIT MAL FORMEE : "
            + " ; ".join(pbs)
            + ".\nRecommence en respectant EXACTEMENT le format et en francais.")
        res = await agent.run(task=tache + relance)
        texte = res.messages[-1].content
        pbs = controle(texte)
        if not pbs:
            return texte
        print(f"    forme invalide ({'; '.join(pbs)}) — essai {essai}/{essais}")
    return (f"> ⚠ forme non conforme apres {essais} essais : "
            f"{' ; '.join(pbs)}. Fiche laissee telle quelle, a relire.\n\n{texte}")


def fichiers_utiles(corpus: Path) -> list[Path]:
    """Corpus dedoublonne : les conversions anterieures cohabitent avec les clés.

    Le convertisseur n'efface pas ses sorties precedentes : un meme article existe
    sous « Moser - 2012 - ....md » ET « Moser2012.md ». Les octets different (OCR
    d'une autre passe) donc une comparaison d'empreinte ne les rapproche pas ; on
    apparie donc sur (premier mot, annee) et on garde la version en clé citekey.
    """
    # La carte SD (USB, amovible) se met en veille : la PREMIERE lecture apres une
    # periode d'inactivite renvoie une liste VIDE sans lever d'erreur. Un run long
    # (inference locale) tombe systematiquement dedans, et un corpus vide se traduit
    # alors par « aucun extrait » au lieu d'un echec visible. On reessaie donc.
    tous = []
    for essai in range(4):
        tous = sorted(corpus.glob("*.md"))
        if tous:
            break
        time.sleep(2 * (essai + 1))
    if not tous:
        raise RuntimeError(
            f"corpus vide apres 4 tentatives : {corpus}\n"
            "Le volume est-il encore monte ? (carte USB en veille ou ejectee)")
    cles = {f.stem.lower() for f in tous if CITEKEY.match(f.stem)}
    gardes = []
    for f in tous:
        if CITEKEY.match(f.stem):
            gardes.append(f); continue
        m = re.match(r"([A-Za-z']+)\D{0,40}?(\d{4})", f.stem)
        if m and f"{m.group(1)}{m.group(2)}".lower() in cles:
            continue                      # doublon d'une conversion anterieure
        gardes.append(f)
    return gardes


def extraits(corpus: Path, motifs: list[str], budget: int = BUDGET_EXTRAITS,
             par_article: int = PAR_ARTICLE, valeurs: str | None = None) -> str:
    """Passages du corpus qui matchent les motifs, echantillonnes par PERTINENCE.

    Le parcours alphabetique naif — remplir jusqu'a epuisement du budget — faisait
    tenir tout le prompt dans les trois premiers articles de l'alphabet : pour P4,
    ni Mohan2022 ni vanZanten2022, les deux references centrales du probleme,
    n'etaient jamais atteintes. On plafonne donc la contribution de chaque article
    et on sert d'abord ceux ou les motifs sont les plus denses.
    """
    rx = re.compile("|".join(motifs), re.I)
    rv = re.compile(valeurs, re.I) if valeurs else None
    candidats = []                          # ((porteuses, fenetres), nom, blocs)
    for fichier in fichiers_utiles(corpus):
        texte = fichier.read_text(errors="ignore")
        fenetres = []
        for m in rx.finditer(texte):
            d, f = max(0, m.start() - FENETRE // 2), min(len(texte), m.end() + FENETRE // 2)
            if fenetres and d < fenetres[-1][1]:   # fusionne les chevauchements
                fenetres[-1] = (fenetres[-1][0], f)
            else:
                fenetres.append((d, f))
        if not fenetres:
            continue

        # On cherche des valeurs reutilisables, pas des mentions : une fenetre qui
        # PORTE une valeur passe avant une fenetre de prose. Le critere doit etre
        # l'adjacence nombre-unite, pas la simple presence d'un chiffre — avec ce
        # dernier, une these ou tout paragraphe contient un decimal accumulait 59
        # fenetres « chiffrees » de bruit et chassait du budget l'article dont
        # l'unique tableau de proprietes donnait justement la valeur cherchee.
        def chiffree(bornes: tuple[int, int]) -> bool:
            d, f = bornes
            return bool(rv.search(texte[d:f])) if rv else False

        fenetres.sort(key=lambda b: (not chiffree(b), b[0]))   # porteuses d'abord
        blocs, pris = [], 0
        for d, f in fenetres:
            bout = re.sub(r"\n{3,}", "\n\n", texte[d:f]).strip()
            bloc = f"\n--- [{fichier.stem}] ---\n{bout}\n"
            if pris + len(bloc) > par_article and blocs:
                break
            blocs.append(bloc); pris += len(bloc)
        candidats.append(((sum(chiffree(b) for b in fenetres), len(fenetres)),
                          fichier.stem, "".join(blocs)))

    # Un article qui PORTE une valeur passe avant un article qui en parle beaucoup.
    # A nombre egal de fenetres porteuses, le plus CONCIS passe devant : un tableau
    # de proprietes de trois lignes est plus utile par caractere qu'une these ou la
    # meme valeur est noyee dans 79 fenetres. Trier par volume decroissant faisait
    # sortir du budget le seul article donnant les conductivites du composite.
    candidats.sort(key=lambda c: (-c[0][0], c[0][1], c[1]))
    morceaux, total = [], 0
    for _, _, bloc in candidats:
        if total + len(bloc) > budget:
            continue                        # un gros article n'exclut pas les suivants
        morceaux.append(bloc); total += len(bloc)
    return "".join(morceaux)


def assurer_modele() -> None:
    """Cree au besoin le modele derive a num_ctx fixe (idempotent, local).

    num_ctx n'est reglable ni par variable d'environnement cote client ni par
    l'endpoint OpenAI-compatible : il faut un modele derive cote serveur.
    """
    if MODELE != MODELE_DERIVE:
        return                               # modele impose par l'utilisateur
    dispo = json.load(urlopen(f"{HOTE}/api/tags", timeout=10))
    if any(m["name"].split(":")[0] == MODELE for m in dispo.get("models", [])):
        return
    print(f"creation du modele {MODELE} (num_ctx={NUM_CTX}) a partir de {MODELE_BASE}")
    corps = json.dumps({"model": MODELE, "from": MODELE_BASE,
                        "parameters": {"num_ctx": NUM_CTX}, "stream": False}).encode()
    urlopen(Request(f"{HOTE}/api/create", data=corps,
                    headers={"Content-Type": "application/json"}), timeout=600).read()


def client_local() -> OpenAIChatCompletionClient:
    """Client OpenAI-compatible pointe sur Ollama (pas de cle, pas de reseau externe)."""
    return OpenAIChatCompletionClient(
        model=MODELE,
        base_url=f"{HOTE}/v1",
        api_key="ollama",                    # ignore par Ollama, mais exige par le client
        temperature=TEMPERATURE,
        timeout=DELAI_CLIENT,
        model_info={
            "vision": False,
            "function_calling": False,
            "json_output": False,
            "family": ModelFamily.UNKNOWN,
            "structured_output": False,
        },
    )


def ecrire_rapport(sortie: Path, corpus: Path, n_articles: int,
                   rapports: dict[str, str], synthese: str | None) -> None:
    """Ecrit l'etat courant du rapport.

    Appelee apres CHAQUE fiche : une inference locale longue se fait tuer (memoire,
    veille, interruption) et une fiche terminee ne doit pas mourir avec le
    processus. Deux runs complets ont deja ete perdus faute de cette ecriture.
    """
    tete = (f"# Extraction litterature -> jumeau numerique\n\n"
            f"Corpus : `{corpus}` ({n_articles} articles) — modele local `{MODELE}`\n\n")
    if synthese is None:
        tete += ("> Run en cours ou interrompu : synthese non produite, "
                 f"{len(rapports)}/{len(PROBLEMES)} fiche(s) ci-dessous.\n\n")
    else:
        tete += f"## Synthese\n\n{synthese}\n\n"
    sortie.write_text(tete + "\n\n".join(
        f"## {c} — {PROBLEMES[c]['titre']}\n\n{rapports[c]}"
        for c in sorted(rapports)))


def fiches_deja_faites(sortie: Path) -> dict[str, str]:
    """Relit les fiches d'un rapport precedent pour ne pas les recalculer.

    Sur une machine juste en memoire, un run complet se fait tuer avant la fin :
    chaque relance repartait alors de P1 et n'arrivait jamais plus loin. Reprendre
    ou s'est arrete le rapport transforme plusieurs runs courts en un depouillement
    complet, sans rien changer au resultat.
    """
    if not sortie.exists():
        return {}
    faites = {}
    for bloc in re.split(r"^## (?=P\d )", sortie.read_text(), flags=re.M)[1:]:
        cle = bloc.split(" ", 1)[0]
        corps = bloc.split("\n", 1)[1].strip() if "\n" in bloc else ""
        if cle in PROBLEMES and corps:
            faites[cle] = corps
    return faites


async def depouiller(corpus: Path, cles: list[str], sortie: Path,
                     reprendre: bool = False,
                     budget: int = BUDGET_EXTRAITS) -> None:
    utiles = fichiers_utiles(corpus)
    sources = {f.stem for f in utiles}
    print(f"corpus : {len(utiles)} articles retenus "
          f"({len(list(corpus.glob('*.md')))} markdown, doublons de conversion exclus)")
    client = client_local()
    rapports: dict[str, str] = fiches_deja_faites(sortie) if reprendre else {}
    if rapports:
        print(f"reprise : {', '.join(sorted(rapports))} deja au rapport")
        cles = [c for c in cles if c not in rapports]
        if not cles:
            print("toutes les fiches sont faites — seule la synthese reste a produire")
    try:
        for cle in cles:
            p = PROBLEMES[cle]
            bouts = extraits(corpus, p["mots"], budget=budget, valeurs=p.get("valeurs"))
            if not bouts.strip():
                rapports[cle] = "_aucun extrait trouve dans le corpus_"
                print(f"  {cle} : aucun extrait")
                ecrire_rapport(sortie, corpus, len(utiles), rapports, None); continue
            n = bouts.count("--- [")
            print(f"  {cle} : {n} extraits, {len(bouts)} caracteres -> {MODELE}")
            tache = (
                f"PROBLEME {cle} — {p['titre']}\n"
                f"Contexte du jumeau : {p['contexte']}\n"
                f"Ce que tu dois extraire : {p['cherche']}\n\n"
                f"EXTRAITS DU CORPUS :\n{bouts}\n\n"
                # Rappel en FIN de prompt : sur un 7B, la consigne systeme seule se
                # fait noyer par un contexte de 14 000 caracteres d'extraits anglais.
                "Reponds en francais, en reprenant EXACTEMENT ces trois titres, "
                "dans cet ordre et sans rien ajouter autour :\n"
                "## Valeurs numeriques reutilisables\n"
                "## Mecanismes et resultats qualitatifs\n"
                "## Ce que les extraits ne permettent PAS de conclure"
            )
            rapports[cle] = await produire(
                f"specialiste_{cle}", client, CONSIGNE_COMMUNE, tache,
                lambda t: defauts_fiche(t, sources))
            ecrire_rapport(sortie, corpus, len(utiles), rapports, None)
            print(f"    fiche {cle} enregistree")

        # --- agent de synthese : recoupe et cherche les contradictions ---
        print(f"  synthese : recoupement de {len(rapports)} rapport(s)")
        consigne_synth = (
            "Tu recoupes des fiches d'extraction. Ta valeur ajoutee est de reperer "
            "(1) les valeurs numeriques qui se CONTREDISENT entre sources, "
            "(2) ce qui est directement actionnable pour le jumeau, "
            "(3) les lacunes. N'invente rien, ne repete pas les fiches in extenso. "
            "Reponds en francais, en moins de 400 mots."
        )
        assemble = "\n\n".join(f"### {c} — {PROBLEMES[c]['titre']}\n{r}"
                               for c, r in rapports.items())
        synthese = await produire(
            "synthese", client, consigne_synth,
            f"Voici {len(rapports)} fiche(s) :\n\n{assemble}\n\n"
            "Reponds en francais et uniquement en francais, en moins de 400 mots.",
            defauts_synthese)
    finally:
        await client.close()

    ecrire_rapport(sortie, corpus, len(utiles), rapports, synthese)
    print(f"\nrapport ecrit : {sortie}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus", type=Path, default=CORPUS_DEFAUT)
    p.add_argument("--probleme", choices=sorted(PROBLEMES), action="append")
    p.add_argument("--sortie", type=Path, default=SORTIE_DEFAUT)
    p.add_argument("--budget", type=int, default=BUDGET_EXTRAITS,
                   help="caracteres d'extraits envoyes par probleme ; a reduire si "
                        "le processus se fait tuer faute de memoire")
    p.add_argument("--reprendre", action="store_true",
                   help="conserve les fiches deja presentes dans --sortie et ne "
                        "traite que les problemes manquants")
    a = p.parse_args()
    if not a.corpus.exists():
        raise SystemExit(f"corpus introuvable : {a.corpus}")
    a.sortie.parent.mkdir(parents=True, exist_ok=True)
    assurer_modele()
    asyncio.run(depouiller(a.corpus, a.probleme or sorted(PROBLEMES), a.sortie,
                           a.reprendre, a.budget))


if __name__ == "__main__":
    main()
