# Data Model: Acceptance Ledger

The Acceptance Ledger is the primary artifact for SPEC-008, recording the implementation status and audit evidence for all specs from SPEC-000 through SPEC-012.

## Ledger Schema (JSON)

The ledger is stored at `artifacts/acceptance-ledger.json`.

```json
{
  "last_updated": "2026-06-01T12:00:00Z",
  "total_specs": 13,
  "complete_count": 8,
  "specs": [
    {
      "id": "SPEC-000",
      "title": "Changelog Creation",
      "status": "complete",
      "evidence": {
        "changelog_entry": true,
        "tests_passed": 15,
        "tests_total": 15,
        "validation_report": "artifacts/validation-report.json"
      },
      "remediation": []
    },
    {
      "id": "SPEC-004",
      "title": "Visualization Foundation",
      "status": "incomplete",
      "evidence": {
        "changelog_entry": false,
        "tests_passed": 39,
        "tests_total": 39
      },
      "remediation": [
        "Add missing changelog entry",
        "Fix text overlap in eda_core.py"
      ]
    }
  ]
}
```

## Entity Definitions

### SpecStatus
One of:
- `complete`: Implementation, tests, and provenance all pass.
- `incomplete`: Substantial implementation exists but fails audit (e.g., missing changelog, known bugs).
- `blocked`: Implementation cannot proceed due to missing dependencies.
- `not_started`: No implementation evidence found.

### AuditEvidence
- `changelog_entry`: Boolean indicating if a valid entry exists in `CHANGELOG.md`.
- `tests_passed`: Count of passing tests in the spec's tier.
- `tests_total`: Total count of tests in the spec's tier.
- `defects`: List of known semantic or visual bugs assigned to this spec.
