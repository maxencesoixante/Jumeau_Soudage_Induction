# Audit d'écart — modèle du jumeau vs Lionetto et al. (2017)

> Lionetto, F., Pappadà, S., Buccoliero, G., & Maffezzoli, A. (2017).
> *Finite element modeling of continuous induction welding of thermoplastic
> matrix composites.* **Materials & Design 120, 212–221.**
> DOI : 10.1016/j.matdes.2017.02.024

**Objet.** Vérifier que le jumeau suit les lois gouvernantes de Lionetto 2017, et
tracer chaque écart (assumé ou à corriger). Rédigé le 2026-08-03 à partir du PDF
complet de l'article et du code réel (`src/jumeau/em/`, `thermique/solveur3d.py`,
`materiaux.py`). **Aucune modification de code** n'accompagne cet audit — c'est un
document de référence.

**Contexte de comparabilité.** Lionetto modélise le soudage **continu** (tête
mobile, moving mesh) de **CF/PEEK** (5-harness satin, T300, Vf 50 %) à **600 kHz**,
280–400 A, bobine « double-D » à 2 mm, refroidissement par jet d'air + rouleau de
consolidation. Le jumeau modélise un procédé **statique / semi-statique** de
**CF/PEKK** avec **twill suscepteur** à l'interface, concentrateur de flux (MFC),
à **388 kHz**. Plusieurs écarts sont donc légitimement dus au matériau/procédé
différent, pas à une erreur de modèle : ils sont signalés comme tels.

---

## 1. Tableau de synthèse

| Loi Lionetto | Éq. | Implémentation jumeau | Verdict |
|---|---|---|---|
| Maxwell harmonique, potentiel vecteur **A** 3D | (1)–(4) | Réduction **plaque mince** ψ (Lin 1993), `foucault.py` | ⚠️ Approximation assumée (δ≫épaisseur) |
| Courant de déplacement −ω²ε₀εr | (1) | **Omis** (limite magnéto-quasi-statique) | ✅ Négligeable (~3·10⁻⁸) |
| µr = 1 (laminé non magnétique) | (4), Tab.1 | µr = 1 (MFC seul porte µr) | ✅ Accord |
| σ, k **anisotropes** | Tab.1 | Tenseurs par couche | ✅ Accord (jumeau plus fin : par couche) |
| Source Joule **Qe = |Je|²/σ** | (6) | `q = ρxx·Jx² + ρyy·Jy²` | ✅ Accord (généralisation anisotrope) |
| Chaleur **conservative**, k(T) | (5) | Forme conservative à k(T) **derrière flag** (défaut off) | ✅ Traité (2026-08-03, flag `k_plan_T`/`k_z_T`) |
| Terme d'advection | — | absent | ✅ Accord (Lionetto n'en a pas : moving mesh) |
| Fusion **−Qm = ρ·HmTOT·Wm·Xcmax·dXm/dt** | (7) | **cp apparent** gaussien | ✅ Équivalent (même enthalpie latente) |
| Degré de fusion Xm (Greco–Maffezzoli) | (8)–(9) | Gaussienne / erf | ⚠️ Écart de **forme** (symétrique vs asymétrique) |
| Cristallisation **Qc**, Ozawa | (10)–(13) | **non modélisée** | ⚠️ Écart assumé (latente négligeable pour T) |
| σ(T), k(T) dépendants de T | Tab.1 | figés (seul cp dépend de T) | ❌ Écart |
| CL convection **q0 = hc(Ta−T)** | (14) | convection **+ rayonnement** | ✅/➕ Jumeau plus complet |
| Contact vers puits (h fictif) | §3.3 | `h_contact → T_puits` | ✅ Même philosophie |

Légende : ✅ accord · ➕ jumeau plus complet · ⚠️ écart de modélisation assumé ·
❌ écart à corriger si l'on vise le domaine concerné.

---

## 2. Électromagnétisme

### 2.1 Formulation (Lionetto éq. 1–4)

Lionetto résout les équations de Maxwell en régime harmonique, formulation en
potentiel vecteur **A** (jauge V = 0), en 3D :

```
(jωσ − ω²ε₀εr)·A + ∇×H = Je        (1)
B = ∇×A   (2)     D = ε₀εrE   (3)     B = µ0µrH   (4)
```

résolue par éléments finis (COMSOL 4.4, module « Magnetic Fields »), avec courants
induits **et** composantes verticales autorisées (Az, Jez).

**Jumeau.** `foucault.py` n'implémente **pas** l'éq. (1) : il en prend la
**réduction plaque mince** (Lin 1993). Fonction de courant ψ telle que
`J = ∇×(ψẑ)` (⇒ ∇·J = 0 exact), et la loi de Faraday en phasor donne

```
ρyy·ψxx + ρxx·ψyy = ω·Bz,     ψ = 0 au chant.
```

**Écart 1 — réduction plaque mince (⚠️ assumé).** Validité : δ = √(2ρ/µ0ω) ≈ 6 mm
à 388 kHz ≫ stack 3,36 mm, et σz ≪ σxy ⇒ courants verticaux Jez négligeables.
C'est une **approximation** de l'éq. (1), physiquement justifiée dans ce régime,
mais numériquement distincte. À **re-vérifier** si la fréquence monte ou si le
stack s'épaissit (cf. `docs/etat_art_induction.md` : pas de seuil universel
« δ vs épaisseur »).

**Écart 2 — courant de déplacement (✅ négligeable).** Le jumeau travaille dans la
limite magnéto-quasi-statique : le terme −ω²ε₀εr de l'éq. (1) est omis. Le rapport
courant de déplacement / courant de conduction ωε₀εr/σ ≈ 3·10⁻⁸ (in-plane) à
388 kHz : l'éq. (1) de Lionetto y est elle-même insensible. Omission exacte à ~1e-8.

**Accord — µr = 1.** Lionetto (Table 1) et jumeau donnent µr = 1 au laminé ;
l'exaltation de perméabilité vit uniquement dans le concentrateur (MFC côté
jumeau ; Lionetto n'a pas de concentrateur, sa double-D est une simple spire).

### 2.2 Source Joule (Lionetto éq. 6)

```
Qe = (1/σ)·|Je|²        (6)   — dissipation moyenne (RMS)
```

**Jumeau.** `densite_joule` : `q = ρxx·Jx² + ρyy·Jy²`.

**Verdict ✅ accord exact.** Pour σ isotrope (ρ = 1/σ) : q = (Jx²+Jy²)/σ = |J|²/σ,
identique à l'éq. (6). Le jumeau en est la **généralisation anisotrope**
(tenseur ρ au lieu du scalaire 1/σ). Les deux sont en RMS (pas de facteur ½ à
double-compter). ➕ Le jumeau distingue en plus la couche (twill vs laminés).

### 2.3 Couplage EM↔thermique par σ(T)

Lionetto fige σ(T) via une **courbe σ vs T** : σ diminue quand T monte, ce qui
rétroagit sur les courants induits → couplage à **deux sens** (même si résolu en
deux étapes : magnétostatique stationnaire pour l'état initial, puis transitoire).

**Jumeau.** σ (donc ρ) **constant par couche** : Q est calculé une fois par
position de spot, sans rétroaction σ(T). Couplage à **sens unique**.
→ **Écart réel**, voir §4 (dépendance en T).

---

## 3. Transfert thermique

### 3.1 Équation de la chaleur (Lionetto éq. 5)

```
ρCp ∂T/∂t = ∂/∂x(kx ∂T/∂x) + ∂/∂y(ky ∂T/∂y) + ∂/∂z(kz ∂T/∂z) + Qe − Qm + Qc   (5)
```

- **forme conservative** (divergence d'un flux), k **anisotrope et dépendant de T** ;
- trois sources : Joule Qe (>0), fusion Qm (<0, puits), cristallisation Qc (>0) ;
- **aucun terme d'advection** ρCp·v·∇T : le mouvement de la tête (procédé continu)
  est porté par le **maillage mobile** (ALE, module « Moving Mesh »), la pièce est
  fixe. L'EDP reste purement conductive.

**Jumeau** (`solveur3d._rhs`) :

```
∂T/∂t = [kx·δ²x + ky·δ²y + kz·δ²z]·T/(ρ·cp_app) + Q/(ρ·cp_app)
```

> **MAJ 2026-08-03 — écart 3 traité (partie k(T)) derrière un flag OFF par défaut.**
> La **forme flux-conservative à k variable** est désormais implémentée dans
> `solveur3d._rhs` et `solveur2d._rhs` (`F_{i+½}=k_face·ΔT/d`, `k_face` = moyenne
> arithmétique des k(T) voisins), activée uniquement si une table `k_plan_T`/`k_z_T`
> est renseignée (`Materiau.a_k_variable()` / `k_plan_field`/`k_z_field`). **Défaut =
> k scalaire constant, comportement historique bit-identique** (chemin `else`
> verbatim ; RHS prouvé égal à la précision machine, `test_thermique*::
> test_k_variable_constante_egale_scalaire_*`). La conservation d'énergie à k(T)
> variable est testée (`test_conservation_energie_variable_k_3d`). Non combinable
> avec l'anisotropie `k_plan_x/y` (ValueError). **σ(T) reste différé** (écart §2.3,
> couplage EM↔thermique à deux sens). La table k(T) est **commentée** dans
> `config/materiaux.yaml` (valeurs littérature CF/PAEK, incertaines/calibrables) —
> son **adoption** reste un mandat `calibration-uq-specialist` (évaluation held-out).

**Écart 3 — k figé et forme non conservative (❌ → ✅ traité derrière flag, cf. MAJ
ci-dessus).** Le solveur **3D** utilisait `kx = ky = k_plan` et
`kz = k_z` **scalaires, constants, uniformes** (ni par couche, ni fonction de T),
et un **laplacien à k constant** (`kx·δ²xT`), pas la forme conservative
`∂x(kx∂xT)` à k variable de l'éq. (5). C'est le **principal écart thermique** vs
Lionetto. À noter : la discipline déjà écrite dans l'agent `thermal-solver-engineer`
(« k, ρ, cp peuvent dépendre de T et de la couche ; utiliser une discrétisation
flux-conservative aux interfaces ») n'est **pas encore appliquée** dans le code 3D —
l'écart est donc autant vs Lionetto que vs le principe interne du projet.
(Le solveur **2D** dispose d'un prototype `k_plan_xy` anisotrope kx≠ky, cf.
`materiaux.Materiau.k_plan_xy`, mais toujours sans dépendance en T ni forme
conservative.)

**Accord — pas d'advection.** Le jumeau étant statique/semi-statique, il n'a
besoin d'aucun terme de transport : cohérent avec l'éq. (5), qui n'en a pas non
plus. **Pour passer au continu façon Lionetto**, la voie correcte n'est **pas**
d'ajouter ρCp·v·∇T mais de rendre la **source mobile** (translation du spot dans
`source_spot`) ou d'adopter un maillage mobile — c'est exactement le choix de
Lionetto.

**Accord de principe — fusion (Qm ⇔ cp apparent).** Le jumeau n'écrit pas −Qm
séparément : il l'absorbe dans le **cp apparent** (`cp_apparent`, pic gaussien).
C'est **mathématiquement équivalent** — les deux injectent la même enthalpie
latente ∫cp dT ≈ cp_base·ΔT + Lf sur le pic. Deux écritures du même phénomène ;
la différence de **forme** de la courbe de fusion est traitée au §4.

### 3.2 Conditions aux limites (Lionetto éq. 14)

```
q0 = hc·(Ta − T)        (14)   — convection pure
```

- hc-n = 5 W/m²K (convection naturelle) ;
- hc-nozzle = 330 W/m²K (jet d'air de refroidissement forcé) ;
- hc-roller = 460 et hc-basalt = 90 W/m²K : coefficients convectifs **fictifs**
  représentant, par bilan d'énergie macroscopique, le contact **conductif** avec le
  rouleau de consolidation et la plaque support en basalte ;
- **pas de terme de rayonnement.**

**Jumeau** (`solveur3d._rhs`) : faces libres en **convection + rayonnement**
`εσ(Ta⁴ − T⁴)` (en Kelvin) ; sous l'empreinte céramique/MFC, **conductance de
contact** `h_contact → T_puits` (bobine + concentrateur refroidis, O'Shaughnessey
2014) ; face inférieure `h_bas`.

- ➕ **Rayonnement ajouté.** Absent chez Lionetto ; physiquement justifié à
  300–400 °C (le flux radiatif y est non négligeable). Écart en faveur du jumeau.
- ✅ **Même philosophie de contact.** `h_contact → T_puits` **est** le pendant du
  coefficient convectif **fictif** hc-roller/hc-basalt de Lionetto : représenter un
  contact conductif vers un puits par un h effectif. (`h_bas` ↔ basalte ;
  `h_contact` ↔ rouleau/puits refroidi, avec un sens physique différent — appui
  refroidi côté bobine vs rouleau côté surface libre — mais la même **catégorie**
  de CL.)

---

## 4. Matériau — fusion, cristallisation, dépendance en T

### 4.1 Fusion (Lionetto éq. 7–9)

```
Qm = ρ·HmTOT·Wm·Xcmax·dXm/dt                            (7)   HmTOT = 130 J/g (PEEK 100 % crist.)
Xm(T) = H(T)/HmTOT                                       (8)   H(T) = ∫ signal DSC (baseline soustraite)
Xm(T) = {1 + (d−1)·exp[kmb·(T−TC)]}^(1/(1−d))           (9)   Greco–Maffezzoli
        PEEK : TC = 619 K, kmb = 1,3 K⁻¹, d = 21,7 ; fusion large (> 60 °C)
```

**Jumeau** (`materiaux.degre_de_fusion`) :

```
Xm(T) = ½·[1 + erf((T − Tf)/(σf√2))],   σf = delta_T_fusion/2
```

**Écart 4 — forme de Xm (⚠️).** Le jumeau utilise une **gaussienne/erf**
(**symétrique**) au lieu de la distribution **asymétrique** de Greco–Maffezzoli
(éq. 9). De plus `delta_T_fusion = 15 °C` (σf = 7,5) donne un **pic beaucoup plus
étroit** que la fusion > 60 °C du PEEK de Lionetto. Une partie de l'écart est
**légitime** (PEKK ≠ PEEK, largeur DSC propre au matériau du jumeau), mais la
**forme symétrique** reste un choix de modèle à assumer explicitement. Le docstring
de `degre_de_fusion` revendique déjà « même définition que l'éq. 8 » — vrai pour la
**définition** Xm = H(T)/HmTOT, mais la **loi** utilisée est la gaussienne, pas
l'éq. (9). À caractériser au DSC du PEKK réel si l'on veut la loi correcte.

### 4.2 Cristallisation (Lionetto éq. 10–13, Ozawa non isotherme)

```
Qc = ρ·HcTOT·Wm·Xcmax·dXc/dt                            (10)  |HcTOT| = HmTOT
log[−ln(1−Cr)] = log φ(T) + n·log(dT/dt)                (11)
φ(T) = exp(−0,037·T + 11,3)                             (12)  n = 0,8 (Lee & Springer, PEEK)
Xc = Cr·[0,42 − 0,03·ln(dT/dt)]                         (13)
```

**Jumeau : non modélisée** (`degre_de_fusion` : « la cinétique de cristallisation
type Ozawa n'est pas modélisée »).

**Écart 5 — cristallisation absente (⚠️ assumé).** **Défendable pour la seule
prédiction de température** : Lionetto note lui-même que la latente
fusion+cristallisation vaut Xcmax·Wm·HcTOT ≈ **19 J/g**, « very low compared with
the heat involved by the induction and could be neglected ». À **implémenter
(éq. 10–13)** uniquement si l'on veut prédire la **cristallinité / qualité du
joint** (temps à l'état fondu, trempe), pas pour le champ de température.

### 4.3 Propriétés et dépendance en T (Lionetto Table 1)

Composite CF/PEEK Lionetto à T ambiante : ρ = 1532 kg/m³, Cp = 1088 J/kg·K ;
σx = σy = 4,0·10³, σz = 0,33 S/m ; εr = 3,7 ; **µr = 1** ; kx = ky = 5,4,
kz = 0,5 W/m·K. Homogénéisation micromécanique (Jones 1975) à partir des fibres
T300 et de la matrice PEEK. **σ et k dépendants de T** (courbes σ vs T, k vs T,
réfs Duhovic/Ageorges).

**Écart 6 — σ(T), k(T) figés (❌).** Lionetto **insiste** (en citant Duhovic 2014)
sur l'importance de la dépendance en température de σ et k. Le jumeau **fige** σ
(par couche) et k ; **cp est la seule propriété dépendante de T** (via le pic de
fusion). C'est le pendant matériau de l'écart §2.3 (couplage σ(T)) et §3.1 (k(T)).
À prioriser si le jumeau vise les **forts gradients près du joint** (où σ et k
varient le plus).

---

## 5. Ce que le jumeau ajoute (hors périmètre Lionetto)

Ces éléments ne sont **pas des écarts** : ils modélisent le procédé propre du
jumeau, que Lionetto ne couvre pas.

- **Concentrateur de flux (MFC)** par méthode des images (Ferrotron, µr≈16) —
  Lionetto n'a pas de concentrateur.
- **Twill suscepteur** à l'interface comme siège principal des courants de Foucault
  (Lionetto chauffe le laminé lui-même, sans mesh additionnel).
- **Thermostat / consigne** (coupure de source sur T de contrôle) — pilotage du
  procédé semi-statique, absent d'un modèle continu à courant imposé.
- **Puits de bord `h_bord_x0`**, **procédé multi-spots séquentiel**, **rayonnement**
  (cf. §3.2) — spécificités du montage et de la campagne statique.

---

## 6. Priorisation des écarts à corriger

Par ordre d'impact décroissant sur la fidélité du **champ de température** (le
livrable actuel), si on décide un jour de rapprocher le code de Lionetto :

1. **k(T)** (§3.1, §4.3) — ✅ **FAIT (2026-08-03)** : forme conservative à k(T)
   derrière flag OFF par défaut (`k_plan_T`/`k_z_T`), non-régression bit-exacte,
   énergie conservée. Reste à **évaluer/adopter** (table k(T) mesurée + held-out,
   mandat `calibration-uq-specialist`).
2. **σ(T)** (§2.3, §4.3) — différé : couplage EM↔thermique à deux sens (re-résoudre
   ψ au T courant), architectural ; faible valeur marginale (efficacité absorbée par
   `facteur_couplage`).
3. **Loi de fusion Xm asymétrique** (§4.1) — subordonné à une caractérisation DSC
   du PEKK réel ; effet localisé sur la fenêtre de fusion.
4. **Cristallisation Qc** (§4.2) — seulement si l'on vise la cristallinité/qualité
   de joint ; négligeable pour T.

Les écarts §2.1 (plaque mince) et §2.2/§3.2 (Joule, CL) sont **assumés et
justifiés** — ne rien y changer sans nouvelle donnée (plaque mince) ou ne pas
régresser (rayonnement, à conserver).
