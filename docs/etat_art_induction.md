# Modélisation électro-thermique du soudage par induction des composites CF/PEKK — état de l'art

> Section d'état de l'art (mémoire LIPEC/ÉTS). Corpus de 14 sources vérifiées
> (deep-research lit-review, 2026-07-17 ; réf. 14 ajoutée 2026-08-18).
> Toute affirmation est attribuée ;
> aucune référence hors corpus vérifié. La lacune sur le régime plaque mince à
> 388 kHz est signalée explicitement (§2.x.4).

Le soudage par induction des composites thermoplastiques à matrice PAEK repose sur une chaîne
physique à trois maillons — champ magnétique, dissipation par courants de Foucault, transfert
thermique avec fusion — dont chacun mobilise des hypothèses de modélisation distinctes. Cette
section situe le jumeau numérique développé ici par rapport à la littérature, selon quatre axes :
les mécanismes de chauffe, la conductivité électrique effective des laminés, la concentration du
flux magnétique, et la validité du régime de plaque mince.

## 2.x.1 Mécanismes de chauffe par induction des CFRTP

Le principe de base est établi de longue date : soumis à un champ magnétique alternatif, un réseau
de fibres de carbone électriquement conducteur développe des courants de Foucault dont les pertes
résistives (effet Joule) échauffent le matériau (Bayerl, Duhovic, Mitschang & Bhattacharyya, 2014).
La théorie « locale » fondatrice de Fink, McCullough et Gillespie (1992) décompose cette dissipation
en trois contributions — conduction le long des fibres, résistance des jonctions fibre-fibre, et
pertes diélectriques — et montre que leur poids relatif dépend de l'architecture des plis. Cette
décomposition demeure le cadre de référence pour interpréter l'origine de la chaleur dans un laminé
donné.

Un enjeu central pour le présent travail est la localisation des boucles de courant. Les travaux
expérimentaux récents par thermographie sur stratifiés unidirectionnels C/PAEK (étude thermographique
des courants de Foucault, 2024) montrent que, dans un empilement UD, les boucles conductrices se
referment préférentiellement aux interfaces où l'orientation des fibres change, et que leur formation
demeure largement stochastique en l'absence d'orientations croisées. Ce résultat est cohérent avec
l'observation, admise dans la littérature de procédé, qu'un laminé CF suffisamment conducteur peut
chauffer sans suscepteur additionnel (O'Shaughnessey, Dubé & Fernandez Villegas, 2016 ; Lionetto,
Pappadà, Buccoliero & Maffezzoli, 2017), mais que l'efficacité dépend fortement de l'architecture.
L'étude expérimentale de van den Berg, Luckabauer, Wijskamp et Akkerman (2024) sur un renfort tissé
(fabric) à conductivité anisotrope constitue à cet égard l'analogue le plus proche du montage étudié
ici : un tissu referme les boucles de courant dans les deux directions du plan, contrairement à un UD.
Ces éléments soutiennent l'hypothèse retenue dans le jumeau, selon laquelle le pli twill (sergé) placé
à l'interface de soudure agit comme siège principal des courants de Foucault. Lorsque l'auto-échauffement
du laminé s'avère insuffisant, la voie du suscepteur dédié reste documentée et modélisée (Lionetto et
al., 2025). Au-delà des éprouvettes de laboratoire, le procédé a par ailleurs été porté jusqu'à des
sous-structures aéronautiques : Pappadà, Salomi, Montanaro, Passaro, Caruso et Maffezzoli (2015)
fabriquent un panneau raidi à matrice thermoplastique dont les raidisseurs sont entièrement assemblés
par soudage par induction, ce qui atteste la maturité industrielle de la technique d'assemblage visée
par le présent travail.

## 2.x.2 Conductivité électrique effective et homogénéisation

La modélisation électromagnétique exige un tenseur de conductivité représentatif du laminé. La
littérature converge sur une anisotropie considérable — de l'ordre de quatre à cinq ordres de grandeur
entre le sens des fibres et la direction transverse hors-plan — les conductivités de pli étant
déterminées expérimentalement par méthodes deux et quatre pointes (Grouve et al., 2020 ; Grouve et al.,
2021). La caractérisation fiable de la conductivité longitudinale des tapes UD fait d'ailleurs l'objet
de développements méthodologiques dédiés (caractérisation de la conductivité longitudinale des tapes
CFRP UD, 2024), signe que ces valeurs restent délicates à mesurer avec exactitude.

Deux stratégies de modélisation coexistent : représenter chaque pli individuellement, ou homogénéiser
les propriétés électriques et thermiques du laminé vers un tenseur effectif. Seneviratne et al. (2021)
comparent explicitement ces approches et évaluent trois techniques d'homogénéisation, justifiant le
recours à un laminé homogénéisé quasi-isotrope dans le plan — hypothèse adoptée dans le présent jumeau.
Un point d'attention majeur émerge toutefois des travaux de Grouve et al. (2021) : la sensibilité des
prédictions à la variabilité matériau est marquée, en particulier pour les composantes transverses,
très dépendantes des contacts inter-fibres et de la qualité de consolidation. Cette incertitude
intrinsèque sur les conductivités effectives motive directement le choix, dans ce travail, de calibrer
un facteur d'échelle de la source plutôt que de figer des conductivités nominales.

## 2.x.3 Concentration du flux magnétique

Le montage étudié comporte un concentrateur de flux (Ferrotron 559H). La quantification de son effet
est fournie par les travaux de validation sur laminés CF/PEKK avec contrôleur de flux magnétique
(validation avec Magnetic Flux Controller, SAMPE, 2021), qui rapportent l'atteinte d'une même
température maximale à un courant d'environ 200 A avec contrôleur, contre 400 A sans — soit un facteur
d'efficacité de l'ordre de deux — accompagnée d'une concentration accrue du point chaud et d'une
réduction des effets de bord. Les recommandations industrielles de conception de bobine et de
concentrateur pour le soudage des CFRTP (Fluxtrol, note technique) fournissent le contexte matériel,
mais doivent être considérées avec la prudence propre à une source non revue par les pairs. Cet ordre
de grandeur (facteur ≈ 2) constitue un repère de plausibilité physique pour le facteur de couplage
calibré dans le jumeau.

## 2.x.4 Régime de plaque mince et dépendance fréquentielle

Le jumeau repose sur une formulation de plaque mince, valide tant que l'épaisseur de peau
δ = √(2ρ/µ₀ω) excède l'épaisseur du stack conducteur. Les modèles éléments finis de référence
résolvent le champ dans l'épaisseur sans nécessairement expliciter ce critère, et opèrent à des
fréquences dont la plage recouvre partiellement celle du banc — le dispositif d'O'Shaughnessey et al.
(2016) couvre 150–450 kHz et a été utilisé à 268 kHz (fréquence de couplage optimale auto-sélectionnée),
tandis que Lionetto et al. (2017) couplent électromagnétisme, thermique et cinétique de
fusion/cristallisation en régime continu. **Aucune des sources du corpus ne fournit toutefois de seuil
chiffré universel « δ contre épaisseur » applicable directement au présent montage.** La machine réelle
opère ici à 388 kHz : proche des 268 kHz d'O'Shaughnessey et à l'intérieur de la plage de son générateur,
mais sans qu'un critère plaque mince explicite y soit associé. Puisque δ décroît en 1/√ω, la validité de
l'hypothèse plaque mince doit être re-vérifiée explicitement à cette fréquence, et ne peut être présumée
acquise sur la seule foi des modèles publiés. Ce point constitue une limite identifiée de l'état actuel des
connaissances et un objet de vérification propre au présent travail.

## 2.x.5 Positionnement

L'état de l'art valide les principales hypothèses structurantes du jumeau — chauffe par courants de
Foucault à siège interfacial, laminé homogénéisé anisotrope, calibration d'un facteur d'échelle face à
l'incertitude sur les conductivités, effet quantifié du concentrateur de flux — tout en isolant une
lacune précise : l'absence de critère fréquentiel publié pour l'hypothèse plaque mince à 388 kHz, que ce
travail se propose de traiter.

---

## Références (corpus vérifié, 14)

1. Bayerl, T., Duhovic, M., Mitschang, P., & Bhattacharyya, D. (2014). The heating of polymer composites by electromagnetic induction – A review. *Composites Part A, 57*, 27–40. https://www.sciencedirect.com/science/article/abs/pii/S1359835X13002996
2. Fink, B. K., McCullough, R. L., & Gillespie, J. W. (1992). A local theory of heating in cross-ply carbon fiber thermoplastic composites by magnetic induction. *Polymer Engineering & Science, 32*(5). https://4spepublications.onlinelibrary.wiley.com/doi/abs/10.1002/pen.760320509
3. O'Shaughnessey, P. G., Dubé, M., & Fernandez Villegas, I. (2016). Modeling and experimental investigation of induction welding of thermoplastic composites and comparison with other welding processes. *Journal of Composite Materials, 50*(21). https://journals.sagepub.com/doi/abs/10.1177/0021998315614991
4. Lionetto, F., Pappadà, S., Buccoliero, G., & Maffezzoli, A. (2017). Finite element modeling of continuous induction welding of thermoplastic matrix composites. *Materials & Design, 120*, 212–221. https://www.sciencedirect.com/science/article/abs/pii/S0264127517301521
5. Grouve, W. J. B., et al. (2020). Induction heating of UD C/PEKK cross-ply laminates. *Procedia Manufacturing, 47*. https://www.sciencedirect.com/science/article/pii/S2351978920311689
6. Grouve, W. J. B., et al. (2021). Simulating the induction heating of cross-ply C/PEKK laminates – sensitivity and effect of material variability. *Advanced Composite Materials.* https://doi.org/10.1080/09243046.2020.1783078
7. Seneviratne, W., et al. (2021). Induction heating of CF/PEKK laminates using homogenization techniques. *Proc. ASC 36th Technical Conference.* https://dpi-proceedings.com/index.php/asc36/article/view/35930
8. van den Berg, S., Luckabauer, M., Wijskamp, S., & Akkerman, R. (2024). Thermal response of an induction-heated fabric reinforced thermoplastic composite with anisotropic electrical conductivity. *Journal of Thermoplastic Composite Materials.* https://doi.org/10.1177/08927057231201353
9. Reliable longitudinal electrical conductivity characterisation of unidirectional CFRP tapes. (2024). *Composites Part A.* https://www.sciencedirect.com/science/article/pii/S1359835X24005487
10. Induction heating of unidirectional C/PAEK – A thermographic study on eddy current formation. (2024). *Composites Part A.* https://www.sciencedirect.com/science/article/pii/S1359836824006012
11. Induction heating analysis validation of CF/PEKK laminates with magnetic flux controller. (2021). *SAMPE, TP21-0000000485.* https://www.digitallibrarynasampe.org/data/webpages/s2021_webpages/142-TP21-0000000485.html
12. Fluxtrol. Induction process and coil design for welding of carbon fiber reinforced thermoplastics. https://www.fluxtrol.com/induction-process-and-coil-design-for-welding-of-carbon-fiber-reinforced-thermoplastics/
13. Lionetto, F., et al. (2025). Experimental and numerical investigation of susceptor-aided continuous induction welding of low-melt PAEK composites. *Polymer Composites.* https://doi.org/10.1002/pc.29732
14. Pappadà, S., Salomi, A., Montanaro, J., Passaro, A., Caruso, A., & Maffezzoli, A. (2015). Fabrication of a thermoplastic matrix composite stiffened panel by induction welding. *Aerospace Science and Technology, 43*, 314–320. https://doi.org/10.1016/j.ast.2015.03.013
