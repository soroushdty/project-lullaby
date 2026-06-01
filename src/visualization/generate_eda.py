from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.visualization.eda_core import generate_core_dashboards


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Project Lullaby descriptive EDA dashboards.")
    parser.add_argument("--data-dir", default="data/raw", help="Canonical table directory")
    parser.add_argument("--out-dir", default="outputs/figures/eda", help="Output directory for EDA PNG artifacts")
    parser.add_argument("--panels", default="core", choices=["core"], help="Dashboard panel set to generate")
    parser.add_argument("--manifest", default="outputs/figures/manifest.json", help="Figure artifact manifest path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        results = generate_core_dashboards(
            Path(args.data_dir),
            Path(args.out_dir),
            manifest_path=Path(args.manifest),
        )
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"Generated {len(results)} EDA core dashboard artifacts")
    for result in results:
        print(result.path.as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
