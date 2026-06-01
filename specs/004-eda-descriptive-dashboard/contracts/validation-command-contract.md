---
id: CONTRACT-004A-VALIDATION-COMMAND
title: Visualization Foundation Validation Command Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-004A, PLAN-004A]
implements: [P2, P3, P5]
supersedes: null
superseded_by: null
related: [SPEC-001]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Validation Command

## Command

```bash
python -m src.cli.validate_visualization_foundation \
  --data-dir data \
  --report artifacts/validation-report.json \
  --manifest outputs/figures/manifest.json
```

All flags are optional. Defaults:

| Flag | Default |
|------|---------|
| `--data-dir` | `data` |
| `--report` | `artifacts/validation-report.json` |
| `--manifest` | `outputs/figures/manifest.json` |
| `--config` | `config/visualization.yaml` when present, otherwise built-in defaults |

## Behavior

- Load all current entity source files from `--data-dir`.
- Resolve required and optional semantic roles through the visualization registry.
- Preserve missingness, extra columns, and source rows.
- Report range violations without dropping values.
- Create `outputs/figures/manifest.json` as a valid empty manifest when no figures exist.
- Print a concise human-readable summary.
- Write deterministic JSON validation results to `artifacts/validation-report.json`.
- Make no network calls.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Validation passed or passed with warnings only |
| 1 | Validation failed because required roles, required files, hard ranges, or manifest fields failed |
| 2 | Command usage or configuration error |

## JSON Report Shape

```json
{
  "status": "pass",
  "data_dir": "data",
  "report_path": "artifacts/validation-report.json",
  "manifest_path": "outputs/figures/manifest.json",
  "entities": {
    "participants": {
      "status": "pass",
      "source_file": "data/lullaby_participants.csv",
      "row_count": 0,
      "resolved_roles": {},
      "warnings": [],
      "errors": [],
      "extra_columns": []
    }
  },
  "warnings": [],
  "errors": [],
  "range_violations": [],
  "capture_worthy_values": [],
  "generated_at_utc": "ISO-8601 timestamp"
}
```

## Summary Output

The command must print:

- Overall status
- Data directory
- Entity count
- Warning count
- Error count
- Report path
- Manifest path

Error details may print to stderr when exit code is non-zero.

## Acceptance Tests

- Running with no flags uses `data/`.
- Running with `--data-dir data/synthetic` validates the synthetic fixtures using the same role
  contract where equivalent roles exist.
- Missing required roles produce exit code 1 and a JSON report with named entity and role.
- Optional missing roles produce exit code 0 and warnings in the JSON report.
- The command creates parent directories for the report and manifest paths.
