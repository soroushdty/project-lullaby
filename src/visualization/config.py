from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ImageConfig:
    dpi: int = 220
    min_width_px: int = 1600
    min_height_px: int = 900
    format: str = "png"


@dataclass(frozen=True)
class StyleConfig:
    font_family: str = "DejaVu Sans"
    colorblind_safe: bool = True
    show_units: bool = True
    direct_labels: bool = True


@dataclass(frozen=True)
class EDAConfig:
    default_participant_id: str | None = None
    default_week_start: int | None = None
    default_week_end: int | None = None
    max_participants_heatmap: int = 250


@dataclass(frozen=True)
class MissingnessConfig:
    render_missing_as: str = "explicit"
    gap_cluster_windows: dict[str, list[int]] = field(
        default_factory=lambda: {
            "overnight": [0, 6],
            "feeding": [6, 9],
            "hot_afternoon": [13, 18],
        }
    )


@dataclass(frozen=True)
class VisualizationConfig:
    output_root: Path = Path("outputs/figures")
    manifest_path: Path = Path("outputs/figures/manifest.json")
    validation_report_path: Path = Path("artifacts/validation-report.json")
    data_dir: Path = Path("data")
    image: ImageConfig = field(default_factory=ImageConfig)
    style: StyleConfig = field(default_factory=StyleConfig)
    eda: EDAConfig = field(default_factory=EDAConfig)
    missingness: MissingnessConfig = field(default_factory=MissingnessConfig)


def load_config(path: str | Path | None = None) -> VisualizationConfig:
    """Load visualization config from YAML when present, otherwise return defaults."""
    config = VisualizationConfig()
    if path is None:
        candidate = Path("config/visualization.yaml")
        if not candidate.exists():
            return config
        path = candidate
    data = _load_yaml(Path(path))
    if not data:
        return config
    return _merge_config(config, data)


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - fallback for minimal envs
        raise RuntimeError("YAML config loading requires PyYAML") from exc
    if not path.exists():
        raise FileNotFoundError(path)
    loaded = yaml.safe_load(path.read_text()) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Visualization config must be a mapping: {path}")
    return loaded


def _merge_config(config: VisualizationConfig, data: dict[str, Any]) -> VisualizationConfig:
    image_data = data.get("image") or {}
    style_data = data.get("style") or {}
    eda_data = data.get("eda") or {}
    missing_data = data.get("missingness") or {}
    return replace(
        config,
        output_root=Path(data.get("output_root", config.output_root)),
        manifest_path=Path(data.get("manifest_path", config.manifest_path)),
        validation_report_path=Path(
            data.get("validation_report_path", config.validation_report_path)
        ),
        data_dir=Path(data.get("data_dir", config.data_dir)),
        image=ImageConfig(**{**config.image.__dict__, **image_data}),
        style=StyleConfig(**{**config.style.__dict__, **style_data}),
        eda=EDAConfig(**{**config.eda.__dict__, **eda_data}),
        missingness=MissingnessConfig(
            **{**config.missingness.__dict__, **missing_data}
        ),
    )
