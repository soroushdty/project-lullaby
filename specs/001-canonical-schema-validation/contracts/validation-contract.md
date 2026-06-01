---
id:            PLAN-001-CONTRACT-002
title:         Validation Boundary Contract
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-001]
implements:    [P5]
supersedes:    null
superseded_by: null
related:       [PLAN-001]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Validation Boundary Contract

## Purpose
Defines expected behavior for ingestion-time schema validation.

## Input Contract
Validator receives:
- active schema object implementing `SchemaContract`
- normalized dataframes keyed by table name
- execution metadata (`run_id`, source, timestamp)

## Output Contract
On success:
- return code: `0`
- structured report with per-table pass status and row counts

On failure:
- return code: non-zero
- structured error payload per violation with:
  - `table`
  - `column` (if applicable)
  - `constraint`
  - `error_code`
  - `sample_rows` (if available)
  - `message`

## Non-Imputation Rule
Validation and ingestion MUST NOT impute missing values.
Allowed behavior:
- preserve nulls
- mark nullable/non-nullable violations explicitly
- reject records/datasets based on policy

## CI Enforcement
`validate-schema` CI job MUST:
- execute validation against bundled synthetic data
- fail workflow on any contract failure
- publish validation report artifact
