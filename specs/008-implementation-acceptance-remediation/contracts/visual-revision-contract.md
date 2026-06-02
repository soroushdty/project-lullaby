# Contract: Visual Revision and Readability

This contract defines the visual standards for dashboard artifacts to ensure clinical and analytic readability.

## Readability Standards

### 1. No Overlapping Text
- Labels on bar charts MUST NOT overlap with other labels or axis lines.
- Legends MUST be placed so they do not obscure data points or trend lines.
- Titles and subtitles MUST have sufficient vertical padding from the top-most panel.

### 2. Adaptive Spacing
- Horizontal bar charts with >10 rows MUST use a minimum figure height that maintains at least 20px vertical space per row.
- Labels for values on top of bars MUST be shifted or thinned if bars are too narrow (<15px).

### 3. Font Consistency
- Dashboard titles: 16pt bold.
- Panel titles: 11pt bold.
- Tick labels: Minimum 8pt.
- Annotations: Minimum 8pt.
- All text MUST use the `DejaVu Sans` font family for consistent cross-platform rendering.

### 4. Color Contrast
- Muted text (hex `#5d6d7e`) MUST only be used for auxiliary information (e.g., source notes).
- Primary metrics and labels MUST use high-contrast text (hex `#17202a`).

## Implementation Targets

- `src/visualization/design.py`: Add `adaptive_font_size()` and `prevent_overlap()` helpers.
- `src/visualization/eda_core.py`: Apply `_wrap_label` and `ax.text` spacing fixes.
- `src/visualization/analytic_dashboard.py`: Fix horizontal bar chart label overlap.
- `src/visualization/patient_view.py`: Ensure timeline event labels do not collide.
