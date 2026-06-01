---
id: RESEARCH-006
title: Data Semantics and Validation Hardening Research
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-006, SPEC-001, SPEC-003, SPEC-004A, SPEC-005]
implements: [P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-003, SPEC-004A, SPEC-005]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Research: Data Semantics and Validation Hardening

## Decision: Centralize Domain Boolean Parsing

**Decision**: Add shared parsing in `src/validation/semantics.py` and require ingestion,
simulation diagnostics, EDA, and tests to use it for domain boolean-like fields.

**Rationale**: The same bug class appears in multiple modules: `.astype(bool)` treats non-empty
strings such as `"False"` and `"0"` as true. A shared parser gives one canonical policy for
true, false, missing/unknown, and invalid tokens.

**Alternatives considered**:
- Keep local `_as_bool` helpers: rejected because behavior would keep drifting by module.
- Use pandas nullable booleans only: rejected because it still requires explicit token handling
  before conversion.
- Use schema validation only: rejected because runtime diagnostics also receive in-memory and
  CSV-loaded tables outside a single validation command.

## Decision: Required Invalids Fail, Optional Invalids Warn

**Decision**: Invalid boolean-like tokens in required roles fail validation. Invalid tokens in
optional roles produce structured warnings and are represented downstream as `Missing/Unknown`.

**Rationale**: Required roles support claims that must be trustworthy. Optional fields may enrich
context but should not prevent otherwise valid dashboards or diagnostics from running.

**Alternatives considered**:
- Fail any invalid token: rejected because optional context would be too brittle.
- Always warn and continue: rejected because required-role claims could remain corrupted.

## Decision: Preflight Required Dashboard Inputs

**Decision**: Validate required inputs for requested dashboard panels before writing or
registering requested artifacts.

**Rationale**: Rendering a warning artifact for a panel with invalid required data can look like
successful dashboard generation. Failing before artifact writes better matches fail-loud behavior
and avoids stale manifest evidence.

**Alternatives considered**:
- Generate unaffected panels and exit non-zero: rejected for this hardening spec because partial
  output complicates acceptance evidence.
- Render warning artifacts and exit zero: rejected because it conflicts with required-input
  semantics.

## Decision: Repo-Relative Manifest Registration

**Decision**: Register every generated artifact with a repo-relative path in the default
manifest. Warn when outputs are outside the repository and cannot be represented safely.

**Rationale**: The default manifest is the traceability source of truth for generated figures.
Limiting entries to `outputs/figures/**` hides valid alternate repo-relative runs, while absolute
paths would be machine-specific and not reproducible.

**Alternatives considered**:
- Keep manifest entries restricted to `outputs/figures/**`: rejected because alternate local
  output directories become untracked without a strong reason.
- Write one manifest per output directory: rejected because it fragments traceability.

## Decision: Overflow Preserves Every Category and Count

**Decision**: Show categories directly when readable. If direct labels would become unreadable,
use explicit overflow behavior with a visible table or artifact metadata preserving every
category and count.

**Rationale**: Rare alert reasons, demographic categories, and equity-relevant context may be
important even with low counts. The dashboard must remain readable without silently suppressing
categories.

**Alternatives considered**:
- Always draw every category directly: rejected because static PNG labels can become unreadable.
- Allow top-N charts with a truncation note: rejected because omitted counts would not remain
  auditable by default.

## Decision: Regenerate Acceptance Artifacts After Semantic Fixes

**Decision**: Regenerate affected tracked dashboard PNGs and `outputs/figures/manifest.json`
whenever hardening changes affect counts, labels, warnings, category completeness, or artifact
registration.

**Rationale**: Dashboard artifacts are acceptance evidence in this repo. Semantic-only fixes can
change prevalence values, denominators, warnings, and manifest metadata even when layout changes
are subtle.

**Alternatives considered**:
- Code/tests only: rejected because tracked outputs could contradict implementation behavior.
- Regenerate only on visual layout changes: rejected because manifest and semantic count changes
  may not be obvious from layout.
