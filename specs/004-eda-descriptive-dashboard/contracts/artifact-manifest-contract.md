---
id: CONTRACT-004-MANIFEST
title: Figure Artifact Manifest Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-004, PLAN-004]
implements: [P2, P7]
supersedes: null
superseded_by: null
related: [SPEC-006, SPEC-007, SPEC-008]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Figure Artifact Manifest

## Default Path

`outputs/figures/manifest.json`

## Empty Manifest

An empty manifest is valid and must be created by the foundation validation command.

```json
{
  "schema_version": "1.0.0",
  "manifest_path": "outputs/figures/manifest.json",
  "entries": [],
  "warnings": []
}
```

## Entry Shape

```json
{
  "artifact_id": "eda_01_cohort_overview",
  "path": "outputs/figures/eda/01_cohort_overview.png",
  "title": "Cohort Overview",
  "spec": "SPEC-007",
  "inputs": ["participants", "clinical_outcomes"],
  "required_roles": ["participant.id", "participant.age"],
  "optional_roles_used": ["participant.has_ac"],
  "warnings": [],
  "created_at_utc": "ISO-8601 timestamp",
  "deterministic": true
}
```

## Rules

- `artifact_id` is required and unique.
- `path` is required, repository-relative, and must remain under `outputs/figures/`.
- `title` is required and non-empty.
- `spec` is required and identifies the producing spec.
- `inputs` lists canonical entity names.
- `required_roles` lists all roles required to generate the artifact.
- `optional_roles_used` lists optional roles consumed when present.
- `warnings` preserves optional-role, no-data, and rendering warnings.
- `created_at_utc` is an ISO-8601 UTC timestamp.
- `deterministic` is required.
- Entries are serialized sorted by `artifact_id`.
- Missing required fields are manifest validation failures.

## Determinism Scope

For the same inputs and configuration, artifact ids, paths, titles, specs, inputs, role lists,
warnings, and deterministic flags must remain stable. `created_at_utc` records run metadata and
is validated for shape and timezone, not for byte-for-byte equality across runs.

## Acceptance Tests

- A zero-entry manifest validates.
- Registering one entry preserves all required traceability fields.
- Registering a duplicate `artifact_id` fails explicitly unless the existing entry is byte-for-byte
  identical after excluding `created_at_utc`.
- Invalid paths outside `outputs/figures/` fail validation.
- Missing required fields fail validation.
