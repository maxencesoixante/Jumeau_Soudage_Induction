"""Slide COMPAAM — VARIANTE COLLAGE, dans l'esprit de la slide 9 du deck NIAR
(Thermoplastic Joining, Wichita State) : vue d'ensemble en poster — bandeau de
categories, chaine flechee du modele, encadre de validations avec statuts, et
colonne de vignettes de resultats. Pas de paragraphes.
"""
import copy
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
SRC = R / "biblio/presentations/Point d'avancement hebdomadaire — LIPeC  ÉTS.pptx"
OUT = R / "biblio/presentations/COMPAAM_CDCQ_2026-10_WP-soudage_collage.pptx"
FIGL, FIGM = R / "biblio/labo/figures", R / "biblio/modele/figures"
FIG69 = FIGL / "issue69"
SCH = R / "biblio/presentations/figures_schemas"

NAVY = RGBColor(0x1F, 0x38, 0x64)
ROUGE = RGBColor(0xC1, 0x27, 0x2D)
MARRON = RGBColor(0x7B, 0x20, 0x20)
GRIS = RGBColor(0x3A, 0x3A, 0x3A)
BLANC = RGBColor(0xFF, 0xFF, 0xFF)
BLEU = RGBColor(0x4A, 0x90, 0xD9)
VERT = RGBColor(0x0B, 0x77, 0x4B)
ORANGE = RGBColor(0xD5, 0x5E, 0x00)
NS_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

prs = Presentation(str(SRC))


def sid(sl, i):
    return next(x for x in sl.shapes if x.shape_id == i)


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


sl = dupliquer(15)
for i in (17, 18, 14):          # figure + texte herites + SOUS-TITRE
    e = sid(sl, i)._element; e.getparent().remove(e)
sid(sl, 12).text_frame.paragraphs[0].runs[0].text = "COMPAAM — WP SOUDAGE PAR INDUCTION"
sid(sl, 13).text_frame.paragraphs[0].runs[0].text = "Soudage par induction CF/PEKK"


# ------------------------------------------------------------------ primitives
def etiquette(x, y, w, txt, taille=11.5):
    """Bandeau de categorie : fond marine, filet rouge, texte blanc (style NIAR)."""
    sh = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y),
                             Inches(w), Inches(0.34))
    sh.fill.solid(); sh.fill.fore_color.rgb = NAVY
    sh.line.color.rgb = ROUGE; sh.line.width = Pt(1.6)
    sh.shadow.inherit = False
    tf = sh.text_frame; tf.word_wrap = True
    tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = txt
    r.font.size, r.font.bold, r.font.color.rgb = Pt(taille), True, BLANC
    return sh


def titre_section(x, y, w, txt, taille=13):
    tb = sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(0.30))
    p = tb.text_frame.paragraphs[0]
    r = p.add_run(); r.text = txt
    r.font.size, r.font.bold, r.font.color.rgb = Pt(taille), True, MARRON
    return tb


def boite(x, y, w, h, lignes, fond=MARRON, texte=BLANC, taille=10):
    """Boite pleine facon 'Resource'/'FEA model' du deck NIAR."""
    sh = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y),
                             Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = fond
    sh.line.fill.background(); sh.shadow.inherit = False
    tf = sh.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.08)
    tf.margin_top = tf.margin_bottom = Inches(0.04)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    for i, (txt, gras) in enumerate(lignes):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        r = p.add_run(); r.text = txt
        r.font.size, r.font.bold, r.font.color.rgb = Pt(taille), gras, texte
    return sh


def fleche(x, y, w, h):
    sh = sl.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(x), Inches(y),
                             Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = BLEU
    sh.line.fill.background(); sh.shadow.inherit = False
    return sh


def vignette(chemin, x, y, w, legende_txt):
    sl.shapes.add_picture(str(chemin), Inches(x), Inches(y), width=Inches(w))
    from PIL import Image
    iw, ih = Image.open(chemin).size
    h = w * ih / iw
    tb = sl.shapes.add_textbox(Inches(x), Inches(y + h + 0.02), Inches(w), Inches(0.26))
    p = tb.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = legende_txt
    r.font.size, r.font.bold, r.font.color.rgb = Pt(9.5), True, GRIS
    return y + h + 0.30


def emplacement(x, y, w, h, txt):
    """Zone reservee a une image que l'utilisateur inserera lui-meme."""
    from pptx.enum.dml import MSO_LINE_DASH_STYLE
    sh = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y),
                             Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = RGBColor(0xF2, 0xF2, 0xF2)
    sh.line.color.rgb = RGBColor(0x9A, 0x9A, 0x9A); sh.line.width = Pt(1.5)
    sh.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    sh.shadow.inherit = False
    tf = sh.text_frame; tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = txt
    r.font.size, r.font.bold, r.font.color.rgb = Pt(11), True, RGBColor(0x8A, 0x8A, 0x8A)
    return sh


# ======================================================= A — le banc (gauche)
etiquette(0.55, 2.55, 4.55, "BANC & INSTRUMENTATION")
emplacement(0.55, 3.00, 4.55, 2.75,
            "PHOTO DU BANC / RENDU SOLIDWORKS\n(à insérer)")
sl.shapes.add_picture(str(SCH / "schema_montage_exp7.png"),
                      Inches(1.15), Inches(5.95), width=Inches(3.35))
tb = sl.shapes.add_textbox(Inches(0.55), Inches(9.76), Inches(4.55), Inches(0.28))
p = tb.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
r = p.add_run(); r.text = "5 TC noyés à l'interface · 12 essais · 150 → 250 A"
r.font.size, r.font.bold, r.font.color.rgb = Pt(9.5), True, GRIS

# ================================================= B — la chaîne du modèle
etiquette(5.35, 2.55, 4.35, "JUMEAU NUMÉRIQUE")
titre_section(5.35, 3.00, 4.35, "Chaîne physique")
boite(5.35, 3.34, 4.35, 0.62, [("① Champ de la bobine + concentrateur MFC", True),
                               ("Biot-Savart, plan image vérifié sur la CAO", False)])
fleche(7.32, 4.00, 0.40, 0.24)
boite(5.35, 4.28, 4.35, 0.62, [("② Courants de Foucault (plaque mince)", True),
                               ("effet de peau, écrasement au chant → « M »", False)])
fleche(7.32, 4.94, 0.40, 0.24)
boite(5.35, 5.22, 4.35, 0.62, [("③ Thermique transitoire + fusion du PEKK", True),
                               ("cp apparent, BDF, maillage 61×21×15", False)])

titre_section(5.35, 6.00, 4.35, "Carte matériau — CF/PEKK")
boite(5.35, 6.34, 4.35, 0.92, [("• Conductivité électrique σ (recoupée : 2 sources externes)", False),
                               ("• k_plan / k_z homogénéisés (Grouve 2020)", False),
                               ("• cp(T) + chaleur latente 40 J/g (30 % cristallin)", False),
                               ("• Pli twill suscepteur 0,20 mm", False)],
      fond=RGBColor(0x4A, 0x4A, 0x4A), taille=9.5)

titre_section(5.35, 7.42, 4.35, "Calibration")
boite(5.35, 7.76, 4.35, 0.78, [("3 paramètres calibrés sur UN essai", True),
                               ("puis confrontation à TOUS les autres,", False),
                               ("SANS recalibrage — y compris hors domaine", False)],
      taille=9.5)
fleche(7.32, 8.60, 0.40, 0.24)
boite(5.35, 8.90, 4.35, 0.62, [("→ Prédiction figée AVANT l'essai", True),
                               ("c'est elle qui est confrontée au banc", False)],
      fond=NAVY, taille=9.5)

# ==================================================== C — validations
etiquette(9.95, 2.55, 4.30, "VALIDATIONS")
cadre = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.95), Inches(3.00),
                            Inches(4.30), Inches(4.30))
cadre.fill.solid(); cadre.fill.fore_color.rgb = RGBColor(0xFA, 0xFA, 0xFA)
cadre.line.color.rgb = ROUGE; cadre.line.width = Pt(2.0)
cadre.shadow.inherit = False
tf = cadre.text_frame; tf.word_wrap = True
tf.margin_left = tf.margin_right = Inches(0.14)
tf.margin_top = Inches(0.10)
ITEMS = [("✓", VERT, "Pics d'interface — cycle 231 A prédit EN AVEUGLE, ±12–20 °C"),
         ("✓", VERT, "Forme de source — « M » en largeur, bimodale en longueur, mesurée en plein champ"),
         ("✓", VERT, "Loi taux–courant en I² (R² = 0,999) ; fréquence constante 388 kHz"),
         ("✓", VERT, "Géométrie EM recoupée sur la CAO ; σ recoupée par 2 sources externes"),
         ("⚠", ORANGE, "Refroidissement inter-passes ~10 % trop lent (spécifique au montage)"),
         ("⚠", ORANGE, "Étalement dans le plan : k_plan effectif ≈ 2,5× la valeur physique"),
         ("•", GRIS, "Extrapolation hors domaine (275 A) — campagne à venir"),
         ("•", GRIS, "Fusion du PEKK par DSC — à caractériser")]
for i, (marq, coul, txt) in enumerate(ITEMS):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_after = Pt(6)
    r1 = p.add_run(); r1.text = marq + "  "
    r1.font.size, r1.font.bold, r1.font.color.rgb = Pt(12), True, coul
    r2 = p.add_run(); r2.text = txt
    r2.font.size, r2.font.color.rgb = Pt(9.5), GRIS

titre_section(9.95, 7.42, 4.30, "Exploitation — fenêtre de soudage")
sl.shapes.add_picture(str(FIGL / "fig_fenetre_soudage.png"),
                      Inches(10.00), Inches(7.74), width=Inches(4.20))

# ==================================================== D — résultats (vignettes)
etiquette(14.50, 2.55, 4.95, "RÉSULTATS")
y = vignette(FIGL / "fig_parite_231A.png", 14.72, 3.00, 4.70,
             "Validation en aveugle — cycle 231 A, 4 passes")
y = vignette(FIG69 / "champ_mm_pic.png", 14.55, y, 4.95,
             "Champ mesuré (150 A) : la source, imagée")
boite(14.55, 9.30, 4.95, 0.72,
      [("±12–20 °C en aveugle  ·  loi en I² (R² = 0,999)", True),
       ("12 essais instrumentés, 150 → 250 A  ·  125 tests automatisés", False)],
      fond=NAVY, taille=10)

prs.save(str(OUT))
lst = prs.slides._sldIdLst
for e in list(lst)[:-1]:
    lst.remove(e)
prs.save(str(OUT))
print("écrit :", OUT, "|", len(prs.slides), "slide(s)")
