---
id:            PLAN-001-CONTRACT-001
title:         Schema Interface Contract
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-001]
implements:    [P3]
supersedes:    null
superseded_by: null
related:       [PLAN-001]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Schema Interface Contract

## Purpose
Defines the runtime contract for active schema objects used by ingestion and validation.

## Type Signature
`SchemaContract` is an abstract Python class. Any active schema object MUST implement:

- `name: str`
- `version: str`
- `table_names() -> list[str]`
- `table_contract(table_name: str) -> TableContract`
- `pandera_schema(table_name: str) -> pandera.DataFrameSchema`
- `data_dictionary(table_name: str) -> dict[str, dict]`

## Canonical Table Requirement
Default `LullabySchema` MUST provide contracts for exactly:
- `participants`
- `daily_vitals`
- `alerts`
- `clinical_outcomes`
- `staff_contacts`

Custom schemas MAY add tables but MUST preserve all tables required by the active pipeline
configuration.

## Runtime Injection Contract
The CLI/API accepts a schema selector in one of forms:
- named preset: `lullaby`
- dotted import path: `package.module:ClassName`

Resolution behavior:
- If selector resolves to a class implementing `SchemaContract`, instantiate and use.
- If selector does not satisfy interface, terminate with contract error.

## Failure Conditions
- Missing required method/property -> `SchemaContractError`
- Missing canonical table in default mode -> `SchemaTableMissingError`
- Invalid Pandera schema object -> `SchemaValidationConfigError`
