from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

from src.visualization.artifacts import (
    ManifestValidationError,
    create_empty_manifest,
)
from src.visualization.config import VisualizationConfig, load_config
from src.visualization.validation import ValidationResult, validate_data_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Project Lullaby visualization foundation inputs."
    )
    parser.add_argument("--data-dir", default=None, help="Local data directory to validate")
    parser.add_argument("--report", default=None, help="JSON validation report path")
    parser.add_argument("--manifest", default=None, help="Figure manifest path")
    parser.add_argument("--config", default=None, help="Visualization YAML config path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = _config_from_args(args)
        create_empty_manifest(config.manifest_path)
        result = validate_data_dir(
            config.data_dir,
            report_path=config.validation_report_path,
            manifest_path=config.manifest_path,
        )
        _write_report(result, config.validation_report_path)
        _print_summary(result)
        if result.status == "fail":
            _print_errors(result)
            return 1
        return 0
    except (FileNotFoundError, ValueError, RuntimeError, ManifestValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


def _config_from_args(args: argparse.Namespace) -> VisualizationConfig:
    config = load_config(args.config)
    return replace(
        config,
        data_dir=Path(args.data_dir) if args.data_dir else config.data_dir,
        validation_report_path=Path(args.report) if args.report else config.validation_report_path,
        manifest_path=Path(args.manifest) if args.manifest else config.manifest_path,
    )


def _write_report(result: ValidationResult, report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n")


def _print_summary(result: ValidationResult) -> None:
    entity_count = len(result.entities)
    print(f"Status: {result.status}")
    print(f"Data directory: {result.data_dir}")
    print(f"Entities: {entity_count}")
    print(f"Warnings: {len(result.warnings) + len(result.capture_worthy_values)}")
    print(f"Errors: {len(result.errors) + len(result.range_violations)}")
    print(f"Report: {result.report_path}")
    print(f"Manifest: {result.manifest_path}")


def _print_errors(result: ValidationResult) -> None:
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    for violation in result.range_violations:
        print(
            "ERROR: range violation "
            f"{violation['entity']}:{violation['role']} "
            f"value={violation['value']}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    sys.exit(main())
