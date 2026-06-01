from __future__ import annotations

import argparse
import json
import pathlib
import sys


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Validate a dataset against the canonical Lullaby schema."
    )
    p.add_argument(
        "--schema",
        default="lullaby",
        help="Schema alias or dotted import path (package.module:ClassName)",
    )
    p.add_argument(
        "--input",
        required=True,
        help="Directory containing input CSV files keyed by table name",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    from src.ingestion import pipeline
    from src.schemas.base import SchemaContractError
    from src.schemas.registry import resolve
    from src.validation.engine import ValidationError

    args = build_parser().parse_args(argv)

    try:
        schema = resolve(args.schema)
    except SchemaContractError as exc:
        print(f"ERROR: schema resolution failed: {exc}", file=sys.stderr)
        return 2

    try:
        report = pipeline.run(schema, args.input)
    except (ValidationError, ValueError) as exc:
        report = {"status": "fail", "error": str(exc)}
        _write_report(report)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    _write_report(report)
    if report["status"] == "pass":
        print("Validation passed.")
        return 0
    print("Validation failed.", file=sys.stderr)
    return 1


def _write_report(report: dict) -> None:
    artifacts = pathlib.Path("artifacts")
    artifacts.mkdir(exist_ok=True)
    (artifacts / "validation-report.json").write_text(
        json.dumps(report, indent=2, default=str)
    )


if __name__ == "__main__":
    sys.exit(main())
