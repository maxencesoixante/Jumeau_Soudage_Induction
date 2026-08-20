#!/usr/bin/env python3
"""Extraction DIRECTE (hors calage) de la diffusivité in-plane et de k_plan.

Point 1 de l'issue #11 : à partir des données centre (y=20) exp9 déjà acquises
(2026-07-30), estimer k_plan sans passer par le calage du jumeau, via la
relation d'ailette :

    alpha = L^2 / tau        k_plan = alpha * rho*cp

où  L   = longueur de décroissance spatiale du profil au pic (conduction in-plane),
    tau = constante de temps du refroidissement après coupure (dynamique).

Robuste aux pertes (h_haut/h_bas) : leur effet se factorise entre L et tau.
Sortie : biblio/labo/figures/fig_kplan_direct_exp9.png + table console.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import yaml

R = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(R / "code" / "scripts"))  # _style partagé
from _style import apply_style, savefig  # noqa: E402

apply_style()

# --- propriétés matériau (config/materiaux.yaml) ---
_mat = yaml.safe_load((R / "code" / "config" / "materiaux.yaml").read_text())["cf_pekk"]
RHO_CP = _mat["densite"] * _mat["cp_base"]        # J/m3/K
K_CONFIG = _mat["k_plan"]                          # 3,0 (référence)

XPOS = np.array([0., 30., 60., 90., 120.]) / 1000.0   # m — TC1..TC5, spot=TC3
XSPOT = 0.060
DATA = R / "donnees" / "data" / "exp9_dissipation-longitudinale_2026-07-30"


def _load(path: Path):
    raw = path.read_text(encoding="latin-1").splitlines()
    rows = [r.split("\t") for r in raw[1:] if r.strip()]
    a = np.array([[float(c.replace(",", ".")) for c in r] for r in rows])
    return a[:, 0], a[:, 1:]


def analyse(path: Path, courant: int) -> dict:
    t, T = _load(path)
    Tinf = T[:5].mean()
    dT = T - Tinf
    dTpk = dT.max(axis=0)
    dist = np.abs(XPOS - XSPOT)

    def fitL(idx):
        s, _ = np.polyfit(dist[idx], np.log(dTpk[idx]), 1)   # ln dT = b - d/L
        return -1.0 / s
    L_left, L_right = fitL([0, 1, 2]), fitL([2, 3, 4])
    L = 0.5 * (L_left + L_right)

    tcut = t[dT[:, 2].argmax()]                              # coupure ≈ pic du spot
    taus = []
    for j in range(5):
        m = (t > tcut + 15) & (dT[:, j] > 3)
        if m.sum() < 8:
            continue
        s, _ = np.polyfit(t[m], np.log(dT[m, j]), 1)
        if s < 0:
            taus.append(-1.0 / s)
    tau = float(np.median(taus))
    alpha = L ** 2 / tau
    k = alpha * RHO_CP
    print(f"=== {courant} A (centre y=20) ===")
    print(f"  L(g/d) = {L_left*1e3:.1f}/{L_right*1e3:.1f} mm ; L = {L*1e3:.1f} mm")
    print(f"  tau = {tau:.0f} s ; alpha = {alpha*1e6:.2f}e-6 m2/s ; k_plan = {k:.1f} W/m·K")
    return dict(t=t, dT=dT, dTpk=dTpk, dist=dist, L=L, L_left=L_left,
                L_right=L_right, tau=tau, tcut=tcut, alpha=alpha, k=k,
                n_tau=len(taus), courant=courant, Tinf=Tinf)


import matplotlib.pyplot as plt  # noqa: E402

r200 = analyse(DATA / "200A" / "200A_y20_monospot.txt", 200)
r175 = analyse(DATA / "175A" / "175a y=20mm et mfc y=60mm.txt", 175)

C_MES, C_FIT = "#0072B2", "#D55E00"           # Okabe-Ito bleu / orange
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
r = r200

Tinf = r["Tinf"]
ax[0].plot(XPOS * 1e3, r["dTpk"] + Tinf, "o", color=C_MES, ms=8, label="T au pic (mesuré)")
xx = np.linspace(60, 120, 50)
s, b = np.polyfit(r["dist"][[2, 3, 4]], np.log(r["dTpk"][[2, 3, 4]]), 1)
ax[0].plot(xx, np.exp(b + s * (xx - 60) / 1e3) + Tinf, "--", color=C_FIT,
           label=fr"décroissance, $L\approx{r['L']*1e3:.0f}$ mm")
ax[0].axvline(60, color="0.6", ls=":", lw=1)
ax[0].set_xlabel("x (mm)  — spot à 60")
ax[0].set_ylabel("Température (°C)")
ax[0].set_title("(a) Longueur de décroissance $L$")
ax[0].legend(fontsize=8)

j = 2
ax[1].plot(r["t"], r["dT"][:, j] + Tinf, "-", color=C_MES, label="TC3 (spot)")
m = (r["t"] > r["tcut"] + 15) & (r["dT"][:, j] > 3)
s, b = np.polyfit(r["t"][m], np.log(r["dT"][m, j]), 1)
ax[1].plot(r["t"][m], np.exp(b + s * r["t"][m]) + Tinf, "--", color=C_FIT,
           label=fr"refroidissement, $\tau\approx{r['tau']:.0f}$ s")
ax[1].axvline(r["tcut"], color="0.6", ls=":", lw=1)
ax[1].set_xlabel("t (s)")
ax[1].set_ylabel("Température (°C)")
ax[1].set_title(r"(b) Constante de refroidissement $\tau$")
ax[1].legend(fontsize=8)

fig.suptitle(
    f"Extraction directe de k_plan (exp9 centre y=20, hors calage) — "
    f"200 A : {r200['k']:.1f} · 175 A : {r175['k']:.1f} W/m·K   "
    f"(config {K_CONFIG:.0f} ; calibré ~7,3)", fontsize=10.5)
fig.tight_layout()
savefig(fig, R / "biblio" / "labo" / "figures" / "fig_kplan_direct_exp9")
print("figure -> biblio/labo/figures/fig_kplan_direct_exp9.png")
