"""Fusionne tous les cahiers / notes de laboratoire en un seul document :
Memoire_Soudage_InductionV2/cahier_laboratoire_soudage_induction.md."""
import re, shutil
from pathlib import Path
J = Path("/Users/maxencedubois/PycharmProjects/Jumeau_Soudage_Induction")
C = Path("/Users/maxencedubois/PycharmProjects/Memoire_Soudage_InductionV2")
CAH = C / "cahier_laboratoire_soudage_induction.md"
GH = "https://github.com/maxencesoixante/Jumeau_Soudage_Induction/blob/main/"
LAB, DAT = J / "biblio/labo", J / "donnees/data"
PARTIES = [
 ("PARTIE 5 — PROTOCOLES DES CAMPAGNES DE MESURE (jumeau)", [
   LAB/"protocole_exp_dissipation_longitudinale.md", LAB/"protocole_thermographie_plaque_libre.md",
   LAB/"protocole_mfc_reduit.md", LAB/"mesures_a_realiser.md"]),
 ("PARTIE 6 — FICHES DE CAMPAGNE ET DONNÉES BRUTES", [
   DAT/"README.md", DAT/"epaisseur_3TC_2026-05/README.md", DAT/"Serie B/README.md",
   DAT/"exp7_bord-centre_2026-07-28_avec-ceramique/README.md",
   *[DAT/f"exp7_bord-centre_2026-07-28_avec-ceramique/{i}A/README.md" for i in (150, 176, 200, 225, 250)],
   DAT/"exp9_dissipation-longitudinale_2026-07-28/README.md",
   LAB/"synthese_issue67_validation_231A_2026-08-31.md",
   LAB/"synthese_issue69.md", LAB/"resultats_issue69_150A.md", LAB/"resultats_issue69_bord_150A.md",
   LAB/"resultats_issue69_proto_source_bimodale.md", LAB/"resultats_issue69_calibration.md",
   LAB/"resultats_issue69_flag_bimodal.md"]),
 ("PARTIE 7 — JOURNAL CHRONOLOGIQUE DES AVANCÉES (juillet → octobre 2026)", [J/"biblio/journal_avancees.md"]),
 ("PARTIE 8 — NOTES D'ANALYSE", [
   LAB/"synthese_issue68_investigation_fusion_2026-08-31.md", LAB/"reouverture_h_bord_x0_heldout.md",
   LAB/"releves_resolus.md", LAB/"explication_source_xyz.md"]),
]
copies = set()
LIEN = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)\)")

def reecrit(src: Path, texte: str) -> str:
    def f(m):
        img, lab, cible = m.groups()
        if re.match(r"^(https?:|#|mailto:)", cible):
            return m.group(0)
        chemin, _, ancre = cible.partition("#")
        p = (src.parent / chemin).resolve()
        if not p.exists():
            p2 = (J / chemin).resolve()          # chemins écrits depuis la racine du dépôt
            p = p2 if p2.exists() else p
        if not p.exists() or J not in p.parents:
            return m.group(0)
        rel = p.relative_to(J)
        if img:
            dest = C / "images" / "jumeau" / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists() or dest.stat().st_mtime < p.stat().st_mtime:
                shutil.copy2(p, dest)
            copies.add(rel)
            return f"![{lab}](images/jumeau/{rel.as_posix().replace(' ', '%20')})"
        return f"[{lab}]({GH}{rel.as_posix().replace(' ', '%20')}{'#' + ancre if ancre else ''})"
    return LIEN.sub(f, texte)

def decale(texte: str) -> str:
    out, code = [], False
    for l in texte.split("\n"):
        if l.lstrip().startswith("```"):
            code = not code
        if not code and re.match(r"^#{1,5} ", l):
            l = "#" + l
        out.append(l)
    return "\n".join(out)

IMG_MD = re.compile(r"!\[([^\]]*)\]\((images/[^)\s]+)\)")


def reduit_figures(texte: str) -> str:
    """Affiche les figures en taille réduite : balise <img> avec une largeur fixée
    (420 px, 560 px pour les figures très larges, ratio > 2,2)."""
    from PIL import Image
    def f(m):
        alt, src = m.groups()
        try:
            with Image.open(C / src.replace("%20", " ")) as im:
                w, h = im.size
        except OSError:
            w, h = 4, 3
        larg = 560 if w / h > 2.2 else 420
        return f'<img src="{src}" alt="{alt.replace(chr(34), "&quot;")}" width="{larg}">'
    return IMG_MD.sub(f, texte)


base = CAH.read_text(encoding="utf-8")
i = base.find("\n# PARTIE 5")                     # rejouable : on repart du cahier d'origine
if i != -1:
    base = base[:i].rstrip() + "\n"
blocs = [base.rstrip(), ""]
for titre, fichiers in PARTIES:
    blocs += ["---", "", f"# {titre}", ""]
    for f in fichiers:
        t = f.read_text(encoding="utf-8").strip()
        rel = f.relative_to(J).as_posix()
        t = decale(reecrit(f, t))
        if not t.startswith("## "):
            t = f"## {rel}\n\n" + t
        lignes = t.split("\n")
        lignes.insert(1, f"\n*Source fusionnée : `{rel}` (dépôt Jumeau_Soudage_Induction).*")
        blocs += ["\n".join(lignes), ""]
CAH.write_text(reduit_figures("\n".join(blocs)).rstrip() + "\n", encoding="utf-8")
print(len(copies), "figures copiées ;", sum(1 for _ in CAH.open(encoding="utf-8")), "lignes")
