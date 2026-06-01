from __future__ import annotations

from matplotlib import pyplot as plt

from src.visualization.design import (
    DEFAULT_STYLE,
    add_panel_label,
    configure_style,
    label_bars,
    style_card,
)


def test_default_style_has_colorblind_safe_palette_and_non_color_encodings():
    assert len(DEFAULT_STYLE.palette) >= 5
    assert "direct_label" in DEFAULT_STYLE.non_color_encodings
    assert "hatch" in DEFAULT_STYLE.non_color_encodings


def test_configure_style_updates_rcparams():
    configure_style()
    assert plt.rcParams["savefig.dpi"] == DEFAULT_STYLE.dpi


def test_card_label_and_bar_helpers_add_visible_text():
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(["a", "b"], [1, 2])
    assert bars
    style_card(ax, "Panel")
    add_panel_label(ax, "A")
    label_bars(ax, [1, 2])
    assert ax.texts
    assert ax.get_title(loc="left") == "Panel"
    plt.close(fig)
