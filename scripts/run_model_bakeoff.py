from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.modeling.bakeoff import BakeoffError, run_bakeoff


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Project Lullaby modeling bake-off.")
    parser.add_argument("--config", required=True, help="Modeling YAML config")
    parser.add_argument("--data-dir", required=True, help="Canonical table directory")
    parser.add_argument("--out-dir", required=True, help="Output directory for modeling artifacts")
    parser.add_argument("--seed", type=int, default=None, help="Override modeling seed")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = run_bakeoff(
            config_path=args.config,
            data_dir=args.data_dir,
            out_dir=args.out_dir,
            seed=args.seed,
        )
    except (BakeoffError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote modeling bake-off artifacts to {args.out_dir}")
    print(f"Trained {len(summary.get('enabled_models', []))} model candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
