"""Garde-fou du style partagé des figures (`scripts/_style.py`, issue #17)."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib as mpl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import _style  # noqa: E402


def test_palette_okabe_ito_et_cmap():
    # Couleurs Okabe-Ito canoniques + colormap perceptuel (pas jet).
    assert _style.OKABE_ITO["bleu"] == "#0072B2"
    assert _style.OKABE_ITO["vermillon"] == "#D55E00"
    assert _style.CMAP_TEMP == "inferno"


def test_apply_style_noyau_complet():
    with mpl.rc_context():
        _style.apply_style()
        assert mpl.rcParams["font.family"] == ["sans-serif"]
        assert mpl.rcParams["font.sans-serif"][0] == "DejaVu Sans"
        assert mpl.rcParams["axes.labelweight"] == "bold"
        assert mpl.rcParams["figure.dpi"] == 600
        assert mpl.rcParams["savefig.dpi"] == 600
        assert mpl.rcParams["savefig.bbox"] == "tight"


def test_apply_style_fonts_only_nimpose_pas_le_noyau_figure():
    with mpl.rc_context():
        mpl.rcParams["axes.labelweight"] = "normal"
        _style.apply_style(fonts_only=True)
        # les polices sont posées…
        assert mpl.rcParams["font.sans-serif"][0] == "DejaVu Sans"
        # …mais pas le noyau « figure imprimée » (labels gras).
        assert mpl.rcParams["axes.labelweight"] == "normal"


def test_apply_style_overrides_preservent_les_reglages_figure():
    with mpl.rc_context():
        _style.apply_style(**{"font.size": 11, "savefig.pad_inches": 0.06})
        assert mpl.rcParams["font.size"] == 11
        assert mpl.rcParams["savefig.pad_inches"] == pytest.approx(0.06)
        # le noyau reste appliqué en plus des surcharges
        assert mpl.rcParams["figure.dpi"] == 600


def test_formats_env_defaut_png(monkeypatch):
    monkeypatch.delenv("FIG_FORMATS", raising=False)
    assert _style.formats_env() == ["png"]


def test_formats_env_multi(monkeypatch):
    monkeypatch.setenv("FIG_FORMATS", "png, pdf ,TIFF")
    assert _style.formats_env() == ["png", "pdf", "tiff"]


def test_savefig_png_par_defaut(tmp_path, monkeypatch):
    monkeypatch.delenv("FIG_FORMATS", raising=False)
    import matplotlib.pyplot as plt
    fig = plt.figure()
    ecrits = _style.savefig(fig, tmp_path / "essai.png", close=True)
    assert [p.name for p in ecrits] == ["essai.png"]
    assert (tmp_path / "essai.png").exists()
    assert not (tmp_path / "essai.pdf").exists()


def test_savefig_multi_format_vectoriel_et_tiff(tmp_path):
    import matplotlib.pyplot as plt
    fig = plt.figure()
    ecrits = _style.savefig(fig, tmp_path / "essai.png",
                            formats=["png", "pdf", "tiff"], close=True)
    noms = {p.suffix for p in ecrits}
    assert noms == {".png", ".pdf", ".tiff"}
    # PDF vectoriel : en-tête %PDF
    assert (tmp_path / "essai.pdf").read_bytes()[:4] == b"%PDF"
    assert (tmp_path / "essai.tiff").exists()
