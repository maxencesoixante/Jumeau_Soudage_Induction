# 176 A avec céramique — résultat (analyse Claude, 2026-07-28)

1 essai (`176A_v1.txt`), TC1 fonctionnel. Ajouté pour **densifier la loi taux-courant**
(point intermédiaire entre 150 et 200 A). *(Étiqueté 176 A ; la consigne « 175 A » a été
arrondie à la valeur relevée.)*

Profil ΔT au pic (°C au-dessus de l'ambiant) :

| y (mm) | 0 | 10 | 20 (centre) | 30 | 40 | symétrie chant | contraste |
|---|---|---|---|---|---|---|---|
| v1 | 241 | 211 | **147** | 177 | 240 | 1,00 | 1,64 |

- **M symétrique aux chants** (ratio 1,00). Comme aux autres courants, léger biais des
  intermédiaires (TC2 > TC4) — systématique, spot un peu décalé vers y=10.
- **Taux de chauffe au chant** (ΔT 30→130) ≈ **15,7 °C/s** — utilisé pour `fig5_loi_courant`.
- Chauffe courte (~141 s, arrêt vers ~240 au chant) → absolu non confronté, comme les autres.
