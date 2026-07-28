# 225 A avec céramique — résultat (analyse Claude, 2026-07-28)

1 essai (`225A_v1.txt`), TC1 fonctionnel. Ajouté pour **densifier la loi taux-courant**
(point intermédiaire entre 200 et 250 A).

Profil ΔT au pic (°C au-dessus de l'ambiant) :

| y (mm) | 0 | 10 | 20 (centre) | 30 | 40 | symétrie chant | contraste |
|---|---|---|---|---|---|---|---|
| v1 | 241 | 196 | **126** | 162 | 239 | 1,01 | 1,92 |

- **M symétrique aux chants** (ratio 1,01). Même léger biais TC2 > TC4 des intermédiaires.
- **Taux de chauffe au chant** (ΔT 30→130) ≈ **26,9 °C/s** — utilisé pour `fig5_loi_courant`.
- Chauffe courte (~120 s, arrêt vers ~240 au chant) → absolu non confronté, comme les autres.
