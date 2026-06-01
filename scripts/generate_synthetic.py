#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.simulation import generate_synthetic  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the Project Lullaby synthetic longitudinal cohort.")
    parser.add_argument("--config", default="config/simulation.yaml", help="YAML simulation configuration")
    parser.add_argument("--out-dir", default=None, help="Output package directory")
    parser.add_argument("--seed", type=int, default=None, help="Root seed override")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = generate_synthetic(args.config, out_dir=args.out_dir, seed=args.seed)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    summary = result.summary
    print(f"Output: {result.output_dir}")
    print(f"Seed: {summary['seed']}")
    print(f"Status: {summary['status']}")
    print(f"Ready for downstream: {summary['ready_for_downstream']}")
    print(f"Warnings: {len(summary['warnings'])}")
    print(f"Errors: {len(summary['errors'])}")
    if summary["errors"]:
        for error in summary["errors"][:10]:
            print(f"ERROR: {error}", file=sys.stderr)
    return 0 if result.ready_for_downstream else 1


if __name__ == "__main__":
    sys.exit(main())
