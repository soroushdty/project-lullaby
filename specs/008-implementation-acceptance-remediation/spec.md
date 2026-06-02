---
id: SPEC-008
title: Implementation Acceptance and Provenance Remediation
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-000, SPEC-001, SPEC-002, SPEC-003, SPEC-004, SPEC-005, SPEC-006, SPEC-007]
implements: [P1, P2, P3, P5, P7]
supersedes: null
superseded_by: null
related: [SPEC-000, SPEC-001, SPEC-002, SPEC-003, SPEC-004, SPEC-005, SPEC-006, SPEC-007]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Feature Specification: Implementation Acceptance and Provenance Remediation

**Feature Branch**: `008-implementation-acceptance-remediation`

**Created**: 2026-06-01

**Status**: Draft

**Input**: User description: "Document the rigorous acceptance audit findings showing that previous specs have substantial implementation evidence but cannot all be claimed complete. Capture changelog/provenance failures, skipped integration coverage, CLI contract drift, and semantic bugs so they can be fixed deliberately."

## Audit Evidence

### Session 2026-06-01

Focused and full-suite checks found:

- Full pytest suite: `196 passed, 4 skipped, 1 warning`.
- SPEC-000 changelog tests: `15 passed`, but actual `CHANGELOG.md` validation fails.
- SPEC-001 schema tests: `52 passed`, `validate_schema --input data/synthetic` passes, but `validate_schema --input data` fails because root files use `lullaby_*.csv` names.
- SPEC-002 adapter tests: `49 passed, 4 skipped`; skipped tests are explicit cloud emulator and MySQL Docker placeholders.
- SPEC-003 stream tests: `24 passed`, but `_stream_pending` uses pandas truthiness and misreads string booleans.
- SPEC-004 visualization foundation tests: `39 passed`, but its changelog entry is missing.
- SPEC-005 simulator tests: `17 passed` and default generation succeeds, but simulator diagnostics use unsafe `.astype(bool)` patterns and its changelog entry is missing.

Known concrete issues:

- `CHANGELOG.md` lacks entries for SPEC-004 and SPEC-005.
- `CHANGELOG.md` currently fails `tools/changelog_validator.py --changelog CHANGELOG.md --spec-dir specs`.
- SPEC-002 local emulator acceptance coverage is incomplete for S3/MinIO, Azure/Azurite, GCS/fake-gcs-server, and MySQL Docker.
- SPEC-003 stream pending parsing treats string `"False"` and `"0"` as true.
- SPEC-005 simulator diagnostics can miscompute event, adherence, and physiology rates when boolean-like columns are CSV-loaded or object typed.
- SPEC-001 schema validation command behavior has drift between the spec's default bundled-data wording and the current root `data/` file naming.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prove Changelog Provenance Is Complete (Priority: P1)

A maintainer needs the repository changelog to be valid and complete before claiming implemented specs are audit-ready. Every implemented spec must have exactly one valid changelog entry with machine-parseable targets.

**Why this priority**: SPEC-000 exists to make implementation provenance enforceable. If the changelog itself fails validation, the repo cannot honestly claim spec-driven traceability.

**Independent Test**: Run the changelog validator against the real repository `CHANGELOG.md` and targeted spec IDs for SPEC-004 and SPEC-005.

**Acceptance Scenarios**:

1. **Given** the current repository changelog, **when** `tools/changelog_validator.py --changelog CHANGELOG.md --spec-dir specs` runs, **then** it exits 0.
2. **Given** SPEC-004 is implemented, **when** validation runs with `--spec-id SPEC-004`, **then** exactly one valid changelog entry is found.
3. **Given** SPEC-005 is implemented, **when** validation runs with `--spec-id SPEC-005`, **then** exactly one valid changelog entry is found.
4. **Given** existing changelog entries for SPEC-001, SPEC-002, and SPEC-003, **when** validation runs, **then** every `Targets` line is machine-parseable and entry boundaries are not mistaken for targets.

---

### User Story 2 - Complete Adapter Acceptance Coverage (Priority: P1)

A maintainer needs SPEC-002's adapter acceptance claims to be backed by real integration tests, not skipped placeholders.

**Why this priority**: SPEC-002 promises source-agnostic ingestion across file, cloud object stores, database, REST, GraphQL, REDCap, and remote link sources. Skipped emulator and MySQL tests leave core adapter claims unproven.

**Independent Test**: Run adapter tier tests with Docker Compose services available and confirm no required SPEC-002 acceptance tests are skipped.

**Acceptance Scenarios**:

1. **Given** Docker Compose starts MinIO, Azurite, fake-gcs-server, and MySQL, **when** the SPEC-002 tier tests run, **then** S3, Azure, GCS, and MySQL integration tests execute rather than skip.
2. **Given** each emulator is seeded with canonical synthetic CSVs, **when** the corresponding adapter loads data, **then** returned frames match canonical table expectations and pass schema validation.
3. **Given** auth failure, transient network failure, and mixed-file-type scenarios, **when** cloud adapter tests run, **then** typed exceptions and retry behavior match the SPEC-002 contracts.
4. **Given** a local MySQL database with happy path, missing-column, and bad-connection cases, **when** MySQL tests run, **then** happy path passes and failure cases raise actionable typed errors.

---

### User Story 3 - Align Schema CLI With Bundled Data Contract (Priority: P2)

A contributor needs the documented schema-validation command to work against the intended bundled data target without guessing which directory or filename convention is supported.

**Why this priority**: SPEC-001 promises clone-to-run schema validation. The command currently passes for `data/synthetic` but fails for root `data/` because root files use `lullaby_*.csv` names.

**Independent Test**: Run documented schema validation commands for both root bundled data and synthetic data.

**Acceptance Scenarios**:

1. **Given** root `data/` contains `lullaby_*.csv` canonical source files, **when** the documented validation command runs against root `data/`, **then** validation either succeeds through supported aliases or the documentation explicitly identifies the supported default input directory.
2. **Given** `data/synthetic/` contains canonical file names, **when** schema validation runs, **then** validation exits 0.
3. **Given** validation rejects a data directory, **when** it reports the error, **then** the message explains the expected file names or aliases.

---

### User Story 4 - Close Boolean Semantics Bugs Found During Audit (Priority: P2)

A maintainer needs known boolean parsing bugs documented as acceptance-blocking defects, not merely future polish.

**Why this priority**: Passing tests are insufficient when known semantic bugs remain. SPEC-003 and SPEC-005 can make incorrect decisions when bool-like values come from CSV/object-typed sources.

**Independent Test**: Add fixtures with native bools, numeric flags, string bools, blanks, nulls, and invalid tokens for affected stream and simulator paths.

**Acceptance Scenarios**:

1. **Given** stream source rows contain `_stream_pending` values `"False"`, `"0"`, `"true"`, `1`, blanks, and nulls, **when** the stream adapter extracts pending records, **then** only explicit true values are held pending.
2. **Given** simulator diagnostics receive CSV-loaded string boolean fields, **when** event rates are computed, **then** `"False"` and `"0"` are not counted as true.
3. **Given** simulator adherence and physiology diagnostics receive object-typed bool-like columns, **when** checks run, **then** results match equivalent native-boolean inputs.
4. **Given** invalid bool-like tokens appear in required diagnostic fields, **when** diagnostics run, **then** they fail with clear data-quality errors instead of guessing.

---

### User Story 5 - Produce An Evidence-Based Completion Ledger (Priority: P3)

A maintainer needs a compact per-spec completion ledger that distinguishes implemented, tested, skipped, failing, and provenance-incomplete states.

**Why this priority**: Task checkboxes and implementation commits are useful signals but not proof. The repo needs a repeatable way to say which specs are truly complete.

**Independent Test**: Generate or update a repo-local acceptance ledger from actual commands, skipped tests, known defects, and changelog status.

**Acceptance Scenarios**:

1. **Given** specs 000 through 005, **when** the acceptance ledger is reviewed, **then** each spec has a status of complete, incomplete, or blocked with evidence.
2. **Given** skipped tests remain, **when** the ledger is produced, **then** skips are listed with file path, test name, and reason.
3. **Given** known bugs remain, **when** the ledger is produced, **then** each bug has a source file reference and remediation owner spec.
Given all remediation work is completed, when the ledger is regenerated, then no implemented spec has missing changelog entries, skipped required acceptance tests, or known acceptance-blocking bugs.

---

### User Story 6 - Improve Visual Clarity and Text Readability (Priority: P2)

A dashboard reviewer needs to be able to read all text labels and annotations on generated PNG artifacts without squinting or deciphering overlapping elements.

**Why this priority**: If dashboard text is unreadable or overlapping, the clinical and analytic evidence it presents cannot be reliably interpreted by stakeholders.

**Independent Test**: Visually inspect all generated PNGs from SPEC-012 and EDA dashboards; verify no labels, titles, or annotations overlap and that font sizes are legible at 1600 × 900 resolution.

**Acceptance Scenarios**:

1. **Given** generated dashboard PNGs, **when** viewed at standard resolution, **then** all text labels, axis titles, and data annotations are fully legible.
2. **Given** densely populated figures, **when** multiple labels are near each other, **then** the layout or label orientation prevents overlap.
3. **Given** a major revision of visual elements, **when** dashboard-wide styles are applied, **then** text spacing and contrast meet readability standards.

### Edge Cases

- Some tests require local sockets or Docker Compose; audit commands must distinguish sandbox/permission skips from real implementation skips.
- A passing unit test suite does not prove emulator coverage when tests are explicitly skipped.
- A spec can be substantially implemented but still provenance-incomplete because its changelog entry is missing or malformed.
- A command may be implemented but drift from spec wording; documentation or alias support must resolve the mismatch.
- Known semantic bugs must not be hidden by task checkboxes or green tests.
- Generated artifacts may change timestamps during audit commands; acceptance evidence must avoid meaningless timestamp churn.
- Highly dense datasets may require adaptive label thinning or larger figure dimensions to preserve readability.


## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST contain exactly one valid changelog entry for every implemented spec from SPEC-000 through SPEC-005.
- **FR-002**: `CHANGELOG.md` MUST pass the real repository changelog validator with no target-format, duplicate-spec, missing-field, or missing-spec-entry errors.
- **FR-003**: SPEC-004 and SPEC-005 MUST be added to `CHANGELOG.md` with valid `Date`, `Spec`, `Summary`, `Rationale`, `Impact`, and machine-parseable `Targets`.
- **FR-004**: Existing changelog entries MUST be corrected so section headings are not parsed as target lines.
- **FR-005**: SPEC-002 cloud emulator tests for S3/MinIO, Azure/Azurite, and GCS/fake-gcs-server MUST execute against Docker Compose services or be explicitly rescoped in SPEC-002 documentation.
- **FR-006**: SPEC-002 MySQL Docker integration tests MUST execute happy path, missing-column, and bad-connection scenarios or be explicitly rescoped in SPEC-002 documentation.
- **FR-007**: Required SPEC-002 acceptance tests MUST NOT remain as unconditional skipped placeholder tests.
- **FR-008**: SPEC-001 schema validation documentation and CLI behavior MUST agree on the supported bundled-data default.
- **FR-009**: Root `data/` validation MUST either support `lullaby_*.csv` aliases or documentation MUST direct contributors to the supported canonical directory.
- **FR-010**: SPEC-003 stream pending parsing MUST use explicit boolean semantics, not pandas generic truthiness.
- **FR-011**: SPEC-005 simulator diagnostics MUST use explicit boolean semantics for event rates, adherence, physiology, and missingness checks.
- **FR-012**: Boolean-like fixtures MUST cover native booleans, numeric flags, string booleans, blanks, nulls, and invalid tokens.
- **FR-013**: An acceptance ledger MUST summarize each prior spec's implementation status, tests run, skipped required tests, known defects, and provenance status.
- **FR-014**: Full-suite test evidence MUST include pass, fail, skip, and warning counts.
- **FR-015**: Any generated artifact changes introduced by remediation MUST be intentional and explained; timestamp-only churn MUST not be committed as evidence.
- **FR-016**: The system MUST revise the visual elements of all generated PNGs to ensure text labels, titles, and annotations do not overlap and remain readable.

### Key Entities

- **Acceptance Ledger**: A repo-local evidence record summarizing implementation status for SPEC-000 through SPEC-005.
- **Spec Completion Status**: One of complete, incomplete, or blocked, assigned from actual tests, commands, changelog validation, and known defects.
- **Skipped Required Test**: A test that represents an acceptance criterion but is skipped unconditionally or because required local infrastructure is not wired.
- **Provenance Gap**: Missing or invalid changelog evidence for an implemented spec.
- **Command Contract Drift**: A mismatch between documented clone-to-run commands and actual accepted CLI arguments or input naming.
- **Known Semantic Defect**: A bug identified by review that can make accepted outputs or diagnostics wrong despite passing tests.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `tools/changelog_validator.py --changelog CHANGELOG.md --spec-dir specs` exits 0.
- **SC-002**: Targeted changelog validation for SPEC-004 and SPEC-005 each finds exactly one valid entry.
- **SC-003**: Adapter acceptance tests either execute S3, Azure, GCS, and MySQL integration coverage with zero required skips, or SPEC-002 is formally amended to narrow those claims.
- **SC-004**: Schema validation commands documented for bundled data exit 0 from the repository root.
- **SC-005**: Stream pending tests prove `"False"` and `"0"` are not treated as pending.
- **SC-006**: Simulator diagnostic tests prove CSV/string bool inputs produce the same rates as native bool inputs.
- **SC-007**: Full test suite passes with no required acceptance tests skipped.
- **SC-008**: Acceptance ledger marks each implemented prior spec complete only when code, tests, commands, changelog, and known-defect checks are all satisfied.

## Assumptions

- SPEC-006 owns the broader boolean semantics hardening work; this spec records the audit/provenance and prior-spec completion remediation layer.
- Some SPEC-002 emulator work may require Docker Compose or CI service wiring beyond the default local pytest run.
- Changelog entries should use per-file line counts, not pasted diffs.
- The maintainer may choose to rescope old spec claims instead of implementing previously skipped infrastructure, but the decision must be documented in the affected spec and changelog.
