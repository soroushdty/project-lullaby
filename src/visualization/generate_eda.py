from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.visualization.eda_core import generate_core_dashboards
from src.visualization.eda_longitudinal import LongitudinalInputError, generate_longitudinal_dashboards


def _parse_bool(value: str) -> bool:
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError("--overlay-environment must be true or false")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Project Lullaby descriptive EDA dashboards.")
    parser.add_argument("--data-dir", default="data/raw", help="Canonical table directory")
    parser.add_argument("--out-dir", default="outputs/figures/eda", help="Output directory for EDA PNG artifacts")
    parser.add_argument("--panels", default="core", choices=["core", "longitudinal"], help="Dashboard panel set to generate")
    parser.add_argument("--manifest", default="outputs/figures/manifest.json", help="Figure artifact manifest path")
    parser.add_argument("--participant-id", default=None, help="Participant id for participant-focused longitudinal panels")
    parser.add_argument("--week-start", type=int, default=None, help="Inclusive 1-based starting study week for longitudinal panels")
    parser.add_argument("--week-end", type=int, default=None, help="Inclusive 1-based ending study week for longitudinal panels")
    parser.add_argument("--overlay-environment", type=_parse_bool, default=False, help="Overlay environment data on longitudinal panels: true or false")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.panels == "longitudinal":
            results = generate_longitudinal_dashboards(
                Path(args.data_dir),
                Path(args.out_dir),
                manifest_path=Path(args.manifest),
                participant_id=args.participant_id,
                week_start=args.week_start,
                week_end=args.week_end,
                overlay_environment=args.overlay_environment,
            )
            panel_label = "longitudinal"
        else:
            results = generate_core_dashboards(
                Path(args.data_dir),
                Path(args.out_dir),
                manifest_path=Path(args.manifest),
            )
            panel_label = "core"
    except (OSError, ValueError, RuntimeError, LongitudinalInputError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"Generated {len(results)} EDA {panel_label} dashboard artifacts")
    for result in results:
        print(result.path.as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
