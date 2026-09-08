"""Slide COMPAAM (CDCQ, octobre) — WP Soudage par induction.

Un fichier PPTX AUTONOME, 16:9, reprenant le chrome ETS/LIPeC/CREPEC du deck
hebdo (clone de sa slide 16). Slide 1 = la contribution ; slide 2 = reserve.
"""
import copy
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
SRC = R / "biblio/presentations/Point d'avancement hebdomadaire — LIPeC  ÉTS.pptx"
OUT = R / "biblio/presentations/COMPAAM_CDCQ_2026-10_WP-soudage.pptx"
FIGL = R / "biblio/labo/figures"
FIGM = R / "biblio/modele/figures"
FIG69 = R / "biblio/labo/figures/issue69"
SCH = R / "biblio/presentations/figures_schemas"

ROUGE = RGBColor(0xC1, 0x27, 0x2D)
GRIS = RGBColor(0x3A, 0x3A, 0x3A)
NS_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

prs = Presentation(str(SRC))


def sid(slide, i):
    return next(x for x in slide.shapes if x.shape_id == i)


def dupliquer(idx):
    src = prs.slides[idx]
    dst = prs.slides.add_slide(src.slide_layout)
    for shp in list(dst.shapes):
        shp._element.getparent().remove(shp._element)
    corr = {}
    for rId, rel in src.part.rels.items():
        if "slideLayout" in rel.reltype:
            continue
        cible = rel._target if not rel.is_external else rel.target_ref
        corr[rId] = dst.part.rels._add_relationship(rel.reltype, cible, rel.is_external)
    for shp in src.shapes:
        el = copy.deepcopy(shp._element)
        for n in el.iter():
            for a in list(n.attrib):
                if a.startswith(NS_R) and n.attrib[a] in corr:
                    n.attrib[a] = corr[n.attrib[a]]
        dst.shapes._spTree.append(el)
    return dst


def bloc(slide, x, y, w, h, contenu, taille=13.5, titre=15.0):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    for i, (st, txt) in enumerate(contenu):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run(); r.text = txt
        if st == "t":
            r.font.size, r.font.bold, r.font.color.rgb = Pt(titre), True, ROUGE
            p.space_after = Pt(4)
        else:
            r.font.size, r.font.bold, r.font.color.rgb = Pt(taille), False, GRIS
            p.space_after = Pt(9)
        p.alignment = PP_ALIGN.LEFT
    return tb


def legende(slide, x, y, w, txt, taille=11):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(0.32))
    r = tb.text_frame.paragraphs[0].add_run(); r.text = txt
    r.font.size, r.font.bold, r.font.color.rgb = Pt(taille), True, GRIS
    tb.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER


def neuve(surtitre, titre, sous_titre):
    sl = dupliquer(15)
    for i in (17, 18):                      # figure + texte herites
        e = sid(sl, i)._element; e.getparent().remove(e)
    sid(sl, 12).text_frame.paragraphs[0].runs[0].text = surtitre
    sid(sl, 13).text_frame.paragraphs[0].runs[0].text = titre
    sid(sl, 14).text_frame.paragraphs[0].runs[0].text = sous_titre
    return sl


# ========================================================== SLIDE 1 (contribution)
s1 = neuve("COMPAAM — WP SOUDAGE PAR INDUCTION",
           "Soudage par induction CF/PEKK — jumeau numérique",
           "Objectif : prédire la température à l'interface de soudure")

bloc(s1, 0.72, 3.15, 5.75, 6.9, [
    ("t", "Le problème"),
    ("c", "La qualité de la soudure se joue à l'INTERFACE, sous 3 mm de composite. La fenêtre est "
          "étroite : fusion du PEKK à 337 °C, cible procédé 355–390 °C, dégradation dès 450 °C. "
          "Quelques thermocouples noyés donnent 5 points — jamais la carte."),
    ("t", "La méthode"),
    ("c", "Chaîne physique en trois maillons : champ de la bobine et de son concentrateur → "
          "courants de Foucault dans les fibres de carbone → thermique transitoire avec fusion "
          "du PEKK."),
    ("c", "Trois paramètres mal connus sont calibrés sur UN essai, puis le modèle est confronté à "
          "tous les autres SANS recalibrage — y compris à des courants jamais vus."),
    ("c", "Mesures : 5 thermocouples à l'interface (12 essais, 150→250 A) + thermographie plein "
          "champ sur plaque découplée, pour mesurer la source elle-même."),
], taille=14.5, titre=16)

s1.shapes.add_picture(str(FIGL / "fig_parite_231A.png"),
                      Inches(6.55), Inches(3.20), width=Inches(6.20))
legende(s1, 6.55, 8.18, 6.20, "Essai réel du 26/08 — un point par thermocouple")

s1.shapes.add_picture(str(FIGL / "fig_fenetre_soudage.png"),
                      Inches(13.05), Inches(4.05), width=Inches(6.30))
legende(s1, 13.05, 8.18, 6.30, "Fenêtre de soudage calculée : courant × durée")

bloc(s1, 6.55, 8.60, 6.20, 1.6, [
    ("t", "Validé en aveugle"),
    ("c", "Pics intérieurs à ±12–20 °C, structure des 4 passes exacte. Les deux coins de plaque "
          "restent hors cible : limite connue et documentée du modèle 2D."),
], taille=13.5, titre=15.5)

bloc(s1, 13.05, 8.60, 6.30, 1.6, [
    ("t", "Utilisable à l'atelier"),
    ("c", "Soudage impossible sous ~180 A ; la fenêtre se resserre quand le courant monte : "
          "21–39 s à 200 A, 7–11 s à 300 A. Loi de réglage : durée ∝ 1/I² (R² = 0,999)."),
], taille=13.5, titre=15.5)

# =============================================================== SLIDE 2 (réserve)
s2 = neuve("COMPAAM — WP SOUDAGE (RÉSERVE)",
           "Ce que le jumeau donne que la mesure ne donne pas",
           "Carte d'interface, source mesurée, levier procédé")

s2.shapes.add_picture(str(FIGM / "fig_empreinte_soudure.png"),
                      Inches(0.80), Inches(3.35), width=Inches(5.60))
legende(s2, 0.80, 8.30, 5.60, "Carte de température à l'interface : seuls 1–2 % atteignent la fusion")

s2.shapes.add_picture(str(FIG69 / "champ_mm_pic.png"),
                      Inches(6.85), Inches(3.55), width=Inches(6.10))
legende(s2, 6.85, 5.85, 6.10, "Thermographie plein champ (150 A) : la source, mesurée")

s2.shapes.add_picture(str(FIGM / "fig_mfc_reduit.png"),
                      Inches(7.60), Inches(6.15), width=Inches(4.85))
legende(s2, 7.10, 9.62, 5.85, "Levier : concentrateur réduit 55 → 31,75 mm")

bloc(s2, 13.35, 3.20, 6.05, 6.9, [
    ("t", "Le centre ne soude pas"),
    ("c", "À spot fixe, la chaleur se concentre en deux rails le long des bords : seule 1 à 2 % de "
          "l'interface atteint la fusion. C'est le modèle qui l'a montré — aucun capteur ne "
          "pouvait le voir."),
    ("t", "La source, enfin mesurée"),
    ("c", "Une caméra thermique sur plaque découplée donne le champ complet. Elle a révélé que la "
          "chaleur se dépose en DEUX points (les deux jambes de la bobine), et a permis de mesurer "
          "l'étalement latéral réel."),
    ("t", "Le levier identifié"),
    ("c", "Un concentrateur plus étroit recentre la chauffe : le contraste bord/centre tombe de "
          "4,1 à 1,7. Prédiction à confirmer au banc dès réception."),
    ("t", "Suite"),
    ("c", "Campagne 275 A hors domaine — test d'extrapolation du jumeau."),
], taille=14, titre=16)

# ne garder que les deux slides neuves
lst = prs.slides._sldIdLst
ids = list(lst)
for e in ids[:-2]:
    lst.remove(e)

prs.save(str(OUT))
print("écrit :", OUT, "|", len(prs.slides), "slides")
