---
id: QS-004A
title: Visualization Foundation and Schema Registry Quickstart
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-004A, PLAN-004A]
implements: [P2, P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-001, SPEC-004B, SPEC-005, SPEC-006, SPEC-007]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Quickstart: Visualization Foundation and Schema Registry

## Prerequisites

From the repository root, install the project and development dependencies:

```bash
python -m pip install -e ".[dev]"
```

SPEC-004A also requires matplotlib for static figure output. Add it to project dependencies
during implementation before running the commands below.

## Validate the Default Bundled Data

```bash
python -m src.cli.validate_visualization_foundation
```

Expected behavior:

- Uses `data/` by default
- Prints a concise validation summary
- Writes `artifacts/validation-report.json`
- Creates or validates `outputs/figures/manifest.json`
- Makes no network calls

## Validate an Alternate Local Data Directory

```bash
python -m src.cli.validate_visualization_foundation --data-dir data/synthetic
```

Use this path for canonical synthetic fixtures. The same semantic-role contract applies where
equivalent roles exist.

## Run Focused Foundation Tests

```bash
pytest \
  tests/contract/test_visualization_registry_contract.py \
  tests/contract/test_visualization_design_contract.py \
  tests/contract/test_artifact_manifest_contract.py \
  tests/contract/test_validation_command_contract.py \
  tests/unit/test_visualization_schema_registry.py \
  tests/unit/test_visualization_validation.py \
  tests/unit/test_visualization_style.py \
  tests/unit/test_artifact_manifest.py \
  tests/integration/test_visualization_foundation_cli.py
```

## Inspect Generated Contracts

```bash
python -m json.tool artifacts/validation-report.json
python -m json.tool outputs/figures/manifest.json
```

The manifest is valid even when it contains zero entries:

```json
{
  "schema_version": "1.0.0",
  "manifest_path": "outputs/figures/manifest.json",
  "entries": [],
  "warnings": []
}
```

## Expected Files After Validation

```text
artifacts/
└── validation-report.json

outputs/
└── figures/
    └── manifest.json
```

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Missing required role for root `data/` | Entity alias list does not include a `lullaby_*.csv` column | Add the source column to the semantic role aliases |
| Missing required role for `data/synthetic` | Synthetic fixture has an equivalent canonical column but the role aliases omit it | Add the canonical column alias |
| Command writes no manifest | Manifest initialization did not run before validation exit | Ensure manifest creation happens before report writing |
| Tiny figure save fails | Expected guard behavior | Use dashboard-size figures or an explicit test override |
| Optional role warning appears | Expected for absent optional data | Render a warning/no-data panel downstream |
