"""Ajoute au deck hebdo une slide "champ electromagnetique" (issue #59 / MFC reduit).

REJOUABLE : si la slide existe deja, son CONTENU est remplace en place (on ne
garde que le chrome herite du gabarit) ; sinon elle est creee et inseree juste
avant la slide fiber flow. On ne supprime JAMAIS une slide du paquet : retirer
une entree de `sldIdLst` (meme avec `drop_rel`) laisse la piece XML orpheline
et produit une archive invalide -- "Duplicate name: ppt/slides/slideNN.xml".

La slide reprend les trois cartes produites par `gen_carte_champ_em.py` en n'en
gardant que les panneaux utiles (recadrage a la volee, images embarquees dans le
pptx : aucun fichier temporaire ne subsiste) :
  - haut  : les deux coupes x-z (bobine seule / + MFC) -> le MFC concentre
  - bas   : les deux vues en plan (MFC actuel / raccourci) -> la chauffe se
            recentre, ce que la coupe x-z ne peut PAS montrer
Elle est inseree juste avant la slide "fiber flow", dont elle porte l'argument.
"""
import copy
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
DECK = R / "biblio/presentations/Point d'avancement hebdomadaire — LIPeC  ÉTS.pptx"
FIGS = R / "biblio/modele/figures"
TMP = Path("/private/tmp/claude-501/-Users-maxencedubois-PycharmProjects-Jumeau-Soudage-Induction/"
           "9b941a73-d97f-43ca-85b2-1f6fbe331e44/scratchpad")

ROUGE, GRIS = RGBColor(0xC1, 0x27, 0x2D), RGBColor(0x3A, 0x3A, 0x3A)
NS_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
GABARIT = 15                                  # slide clonee pour le chrome

prs = Presentation(str(DECK))
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


def recadrer(nom, x0, x1, y0, y1):
    """Recadre une figure en fractions de sa taille -> fichier temporaire."""
    im = Image.open(FIGS / nom)
    w, h = im.size
    out = TMP / f"crop_{x0:.2f}_{nom}"
    im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h))).save(out)
    return out


def legende(sl, x, y, w, txt, taille=11):
    tb = sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(0.30))
    p = tb.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = txt
    r.font.size, r.font.bold, r.font.color.rgb = Pt(taille), True, GRIS


def bloc(sl, x, y, w, h, contenu):
    tb = sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    for i, (st, txt) in enumerate(contenu):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run(); r.text = txt
        if st == "t":
            r.font.size, r.font.bold, r.font.color.rgb = Pt(14.5), True, ROUGE
            p.space_after = Pt(4)
        else:
            r.font.size, r.font.bold, r.font.color.rgb = Pt(12.5), False, GRIS
            p.space_after = Pt(10)
    return tb


# Le chrome (bandeau rouge, titres, pied de page, logos) = les formes du gabarit
# hors sa figure et son bloc de texte. Calcule, pas code en dur.
CHROME = {sh.shape_id for sh in prs.slides[GABARIT].shapes} - {17, 18}

existante = next((s for s in prs.slides
                  if any(sh.has_text_frame and "CHAMP EM" in sh.text_frame.text
                         for sh in s.shapes)), None)
if existante is None:
    sl = dupliquer(GABARIT)
    for i in (17, 18):                        # figure + texte herites du gabarit
        e = sid(sl, i)._element; e.getparent().remove(e)
    neuve = True
else:
    sl = existante                            # on remplace le CONTENU, pas la slide
    for sh in [x for x in sl.shapes if x.shape_id not in CHROME]:
        sh._element.getparent().remove(sh._element)
    neuve = False
sid(sl, 12).text_frame.paragraphs[0].runs[0].text = "MODÉLISATION SUR PYTHON — CHAMP EM"
sid(sl, 14).text_frame.paragraphs[0].runs[0].text = (
    "Ce que le concentrateur change — et ce qu'il ne change pas")

COUPE = (0.010, 0.452, 0.0, 1.0)              # panneau gauche (coupe de côté)
PLAN = (0.452, 1.0, 0.0, 1.0)                 # panneau droit + barre de couleur

def poser(nom, boite, x, y, hauteur, lg, taille=10.5):
    """Place un recadrage a HAUTEUR imposee ; renvoie sa largeur reelle.

    On impose la hauteur (et non la largeur) parce que le recadrage change de
    proportions des qu'on retouche la figure source : figer une largeur faisait
    deborder les rangees l'une sur l'autre.
    """
    chemin = recadrer(nom, *boite)
    iw, ih = Image.open(chemin).size
    largeur = hauteur * iw / ih
    sl.shapes.add_picture(str(chemin), Inches(x), Inches(y), height=Inches(hauteur))
    legende(sl, x, y + hauteur + 0.04, largeur, lg, taille)
    return largeur


H_RANGEE = 2.82
# --- haut : le MFC concentre (coupes de cote) ------------------------------ #
x = 0.70
for nom, lg in [("fig_champ_em_1_bobine_seule.png", "Bobine seule"),
                ("fig_champ_em_2_mfc_actuel.png", "Bobine + MFC — pic ×2,5")]:
    x += poser(nom, COUPE, x, 3.15, H_RANGEE, lg) + 0.55

# --- bas : la chauffe se recentre (vues de dessus) ------------------------- #
x = 0.70
for nom, lg in [("fig_champ_em_2_mfc_actuel.png", "MFC actuel (55 mm) — lobes chauds au bord"),
                ("fig_champ_em_3_mfc_reduit.png", "MFC raccourci (31,75 mm) — chauffe recentrée")]:
    x += poser(nom, PLAN, x, 6.72, H_RANGEE, lg, taille=10) + 0.45

def cadre_formule(x, y, w, h):
    """Encadre la conversion puissance -> temperature, chaque symbole nomme et unite.

    Valeurs verifiees contre le depot (config/materiaux.yaml l.8-9,
    config/geometrie.yaml l.7-9) et recalculees independamment :
    rho.cp.e = 1600 x 1200 x 0,00682 = 13 094 J/(m2.K).
    Les deux reserves affichees sont chiffrees, pas decoratives :
      - cp_apparent (materiaux.py l.140-150) vaut x6,8 le cp_base a Tf=337 C
        -> la montee reelle y est jusqu'a 7 fois plus lente (chaleur latente) ;
      - la borne adiabatique au noeud le plus chaud (67 C/s) vaut ~2x le taux
        reellement simule ET mesure au meme point a 250 A (30-34 C/s,
        biblio/journal_avancees.md l.154) : la conduction evacue aussitot.
    """
    sh = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y),
                             Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = RGBColor(0xF4, 0xF6, 0xF9)
    sh.line.color.rgb = ROUGE; sh.line.width = Pt(1.4)
    sh.shadow.inherit = False
    tf = sh.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.13)
    tf.margin_top = Inches(0.08)
    GRIS_C = RGBColor(0x7A, 0x7A, 0x7A)
    lignes = [
        ("De la puissance à la température", 13, True, ROUGE, 4),
        ("ρ · c𝑝 · e · dT/dt  =  q″  −  pertes  −  conduction", 13, True, GRIS, 5),
        ("q″   puissance Joule induite, par m² de plaque . . . . . W/m²", 10.5, False, GRIS, 1),
        ("ρ    masse volumique du CF/PEKK . . . . . . . 1 600 kg/m³", 10.5, False, GRIS, 1),
        ("c𝑝   capacité thermique, hors fusion . . . 1 200 J/(kg·K)", 10.5, False, GRIS, 1),
        ("e    épaisseur de l'empilement soudé . . . . . . . 6,82 mm", 10.5, False, GRIS, 1),
        ("dT/dt  vitesse de chauffe . . . . . . . . . . . . . . . . . . °C/s", 10.5, False, GRIS, 5),
        ("ρ c𝑝 e = 13 100 J/(m²·K)   →   100 000 W/m² ≈ 7,6 °C/s", 12, True, GRIS, 4),
        ("Valable loin de la fusion. À 337 °C la chaleur latente absorbe l'énergie : "
         "la montée y est jusqu'à 7× plus lente.", 9.5, False, GRIS_C, 2),
        ("Au pic de la carte cette borne donne 67 °C/s, mais modèle et mesure montent "
         "à 30–34 °C/s à 250 A — la conduction évacue aussitôt.", 9.5, False, GRIS_C, 0),
    ]
    for i, (txt, taille, gras, coul, apres) in enumerate(lignes):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run(); r.text = txt
        r.font.size, r.font.bold, r.font.color.rgb = Pt(taille), gras, coul
        p.space_after = Pt(apres)


XT, WT = 12.55, 6.85
bloc(sl, XT, 3.06, WT, 1.30, [
    ("t", "La puissance Joule induite, c'est quoi ?"),
    ("c", "La bobine ne touche jamais la pièce. Son champ alternatif (388 kHz) fait circuler des "
          "courants dans les fibres de carbone ; ils chauffent le matériau de l'intérieur, comme "
          "une plaque à induction chauffe une casserole."),
])
cadre_formule(XT, 4.34, WT, 3.62)
bloc(sl, XT, 8.06, WT, 1.10, [
    ("t", "Le raccourcir ne change RIEN au champ (x, z)"),
    ("c", "Le MFC double la chauffe (pic ×2,5 vs bobine seule), mais sa TAILLE n'entre pas dans "
          "le calcul du champ : la coupe est strictement la même."),
])
bloc(sl, XT, 9.16, WT, 0.90, [
    ("t", "Ce qui change : l'uniformité en (x, y)"),
    ("c", "L'empreinte plus courte recentre la puissance : contraste bord/centre 4,1 → 1,7, "
          "mesuré sur la carte de TEMPÉRATURE (250 A, 15 s). C'est là-dessus qu'on compte pour "
          "réduire le fiber flow. Réserve : masque 1er ordre, non recalibré."),
])
# insertion juste AVANT la slide "fiber flow" -- uniquement pour une slide neuve
if neuve:
    lst = prs.slides._sldIdLst
    ids = list(lst)
    cible = next(i for i, s in enumerate(prs.slides)
                 if any(sh.has_text_frame and "Le problème" in sh.text_frame.text
                        for sh in s.shapes))
    lst.remove(ids[-1])
    lst.insert(cible, ids[-1])
    position = cible + 1
else:
    position = next(i for i, s in enumerate(prs.slides, 1) if s is sl)

prs.save(str(DECK))
print(f"slide {'créée' if neuve else 'mise à jour'} en position {position} ; "
      f"deck à {len(prs.slides)} slides")
