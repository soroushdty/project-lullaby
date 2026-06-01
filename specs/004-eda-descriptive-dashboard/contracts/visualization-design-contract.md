---
id: CONTRACT-004A-DESIGN
title: Visualization Design System Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-004A, PLAN-004A]
implements: [P2, P5, P10]
supersedes: null
superseded_by: null
related: [SPEC-004B, SPEC-006, SPEC-007]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Visualization Design System

## Module

`src.visualization.design`

## Required Public Helpers

```python
def configure_style(style: VisualizationStyle | None = None) -> None: ...

def add_dashboard_title(fig, title: str, subtitle: str | None = None) -> None: ...

def add_panel_label(ax, label: str) -> None: ...

def style_card(ax, title: str | None = None) -> None: ...

def label_bars(ax, values, total=None, unit: str | None = None) -> None: ...

def save_figure(
    fig,
    path: Path,
    *,
    min_width_px: int = 1600,
    min_height_px: int = 900,
    dpi: int = 220,
    allow_test_override: bool = False,
) -> Path: ...

def render_warning_panel(ax, title: str, message: str) -> None: ...

def render_no_data_panel(ax, title: str, required_roles: list[str]) -> None: ...
```

## Style Requirements

- Use centralized colors for figure background, panel background, text, muted text, grid,
  warnings, and capture-worthy annotations.
- Use a colorblind-safe categorical palette.
- Use consistent typography, spacing, card/tile styling, gridlines, subtitles, legends, and
  annotations.
- Apply axis labels and units where units are known.
- Render warning and no-data panels instead of crashing when roles are missing.
- Use non-color encodings for clinically meaningful categories, such as direct labels, markers,
  line styles, hatches, or annotations.

## Save Requirements

- Saved figures support at least 220 DPI.
- Saved figures must meet or exceed 1600x900 pixels unless `allow_test_override=True`.
- Tiny/default matplotlib figures are rejected with a clear error.
- Parent directories are created when saving.
- Return value is the saved path.

## Acceptance Tests

- A sample figure saved through `save_figure` meets minimum pixel and DPI contract.
- A tiny figure fails without override.
- Warning and no-data panels render text and do not require source data.
- Category encodings can be verified without color-only semantics.
