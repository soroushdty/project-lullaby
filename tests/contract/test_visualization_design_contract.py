from __future__ import annotations

import pytest

from matplotlib import pyplot as plt

from src.visualization.design import (
    FigureSizeError,
    add_dashboard_title,
    render_no_data_panel,
    render_warning_panel,
    save_figure,
)


def test_save_figure_rejects_tiny_default_figure(tmp_path):
    fig, _ = plt.subplots(figsize=(2, 2))
    with pytest.raises(FigureSizeError):
        save_figure(fig, tmp_path / "tiny.png")
    plt.close(fig)


def test_save_figure_accepts_dashboard_sized_figure(tmp_path):
    fig, _ = plt.subplots(figsize=(8, 4.5))
    path = save_figure(fig, tmp_path / "large.png")
    assert path.exists()
    plt.close(fig)


def test_warning_and_no_data_panels_render_text():
    fig, axes = plt.subplots(1, 2, figsize=(8, 4.5))
    render_warning_panel(axes[0], "Warning", "Missing optional role")
    render_no_data_panel(axes[1], "No Data", ["participant.id"])
    assert axes[0].texts
    assert axes[1].texts
    plt.close(fig)


def test_dashboard_title_helper_adds_text():
    fig, _ = plt.subplots(figsize=(8, 4.5))
    add_dashboard_title(fig, "Title", "Subtitle")
    assert fig.texts
    plt.close(fig)
