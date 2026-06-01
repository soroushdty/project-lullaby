from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(tempfile.gettempdir()) / "project-lullaby-matplotlib"),
)
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import matplotlib

matplotlib.use("Agg", force=True)
from matplotlib import pyplot as plt  # noqa: E402


class FigureSizeError(ValueError):
    pass


@dataclass(frozen=True)
class VisualizationStyle:
    figure_background: str = "#f7f9fb"
    panel_background: str = "#ffffff"
    text_color: str = "#17202a"
    muted_text_color: str = "#5d6d7e"
    grid_color: str = "#d8dee9"
    warning_color: str = "#b35c00"
    capture_worthy_color: str = "#8a3ffc"
    palette: tuple[str, ...] = (
        "#0072B2",
        "#D55E00",
        "#009E73",
        "#CC79A7",
        "#F0E442",
        "#56B4E9",
        "#E69F00",
    )
    font_family: str = "DejaVu Sans"
    dpi: int = 220
    min_width_px: int = 1600
    min_height_px: int = 900
    format: str = "png"
    non_color_encodings: tuple[str, ...] = (
        "direct_label",
        "marker",
        "line_style",
        "hatch",
        "annotation",
    )


DEFAULT_STYLE = VisualizationStyle()


def configure_style(style: VisualizationStyle | None = None) -> None:
    style = style or DEFAULT_STYLE
    plt.rcParams.update(
        {
            "figure.facecolor": style.figure_background,
            "axes.facecolor": style.panel_background,
            "axes.edgecolor": style.grid_color,
            "axes.labelcolor": style.text_color,
            "axes.titlecolor": style.text_color,
            "font.family": style.font_family,
            "text.color": style.text_color,
            "xtick.color": style.muted_text_color,
            "ytick.color": style.muted_text_color,
            "grid.color": style.grid_color,
            "savefig.dpi": style.dpi,
            "axes.prop_cycle": matplotlib.cycler(color=list(style.palette)),
        }
    )


def add_dashboard_title(fig, title: str, subtitle: str | None = None) -> None:
    fig.suptitle(title, x=0.03, y=0.98, ha="left", va="top", fontsize=16, fontweight="bold")
    if subtitle:
        fig.text(0.03, 0.94, subtitle, ha="left", va="top", fontsize=10, color=DEFAULT_STYLE.muted_text_color)


def add_panel_label(ax, label: str) -> None:
    ax.text(
        0.0,
        1.02,
        label,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9,
        fontweight="bold",
        color=DEFAULT_STYLE.muted_text_color,
    )


def style_card(ax, title: str | None = None) -> None:
    ax.set_facecolor(DEFAULT_STYLE.panel_background)
    for spine in ax.spines.values():
        spine.set_color(DEFAULT_STYLE.grid_color)
        spine.set_linewidth(0.8)
    ax.grid(True, axis="y", alpha=0.45)
    if title:
        ax.set_title(title, loc="left", fontsize=11, fontweight="bold")


def label_bars(ax, values: Iterable[float], total=None, unit: str | None = None) -> None:
    total_value = total if total is not None else sum(v for v in values if v is not None)
    for patch, value in zip(ax.patches, values, strict=False):
        if value is None:
            continue
        suffix = f" {unit}" if unit else ""
        if total_value:
            label = f"{value:g}{suffix} ({value / total_value:.0%})"
        else:
            label = f"{value:g}{suffix}"
        ax.text(
            patch.get_x() + patch.get_width() / 2,
            patch.get_height(),
            label,
            ha="center",
            va="bottom",
            fontsize=8,
        )


def save_figure(
    fig,
    path: Path,
    *,
    min_width_px: int = 1600,
    min_height_px: int = 900,
    dpi: int = 220,
    allow_test_override: bool = False,
) -> Path:
    width_px = fig.get_figwidth() * dpi
    height_px = fig.get_figheight() * dpi
    if not allow_test_override and (width_px < min_width_px or height_px < min_height_px):
        raise FigureSizeError(
            f"Figure is {width_px:.0f}x{height_px:.0f}px at {dpi} DPI; "
            f"minimum is {min_width_px}x{min_height_px}px"
        )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    return path


def render_warning_panel(ax, title: str, message: str) -> None:
    _render_message_panel(ax, title, message, DEFAULT_STYLE.warning_color)


def render_no_data_panel(ax, title: str, required_roles: list[str]) -> None:
    roles = ", ".join(required_roles)
    _render_message_panel(ax, title, f"Required roles unavailable: {roles}", DEFAULT_STYLE.muted_text_color)


def _render_message_panel(ax, title: str, message: str, color: str) -> None:
    ax.clear()
    ax.set_facecolor(DEFAULT_STYLE.panel_background)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color(DEFAULT_STYLE.grid_color)
    ax.text(0.03, 0.70, title, transform=ax.transAxes, ha="left", va="center", fontsize=12, fontweight="bold", color=color)
    ax.text(0.03, 0.48, message, transform=ax.transAxes, ha="left", va="center", fontsize=9, color=DEFAULT_STYLE.text_color, wrap=True)


__all__ = [
    "DEFAULT_STYLE",
    "FigureSizeError",
    "VisualizationStyle",
    "add_dashboard_title",
    "add_panel_label",
    "configure_style",
    "label_bars",
    "render_no_data_panel",
    "render_warning_panel",
    "save_figure",
    "style_card",
]
