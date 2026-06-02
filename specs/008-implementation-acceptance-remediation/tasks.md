---
id:            TASKS-008
title:         Implementation Acceptance and Provenance Remediation — Tasks
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Gemini CLI
depends_on:    [PLAN-008]
implements:    [SPEC-008]
description:   "Task list for SPEC-008 acceptance remediation"
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Tasks: Acceptance Remediation

**Input**: Design documents from `/specs/008-implementation-acceptance-remediation/`

## Phase 1: Setup

- [ ] T001 Initialize branch `008-implementation-acceptance-remediation` if not already present
- [ ] T002 Verify local `docker compose` can start MinIO, Azurite, fake-gcs, and MySQL services

---

## Phase 2: Foundational (Acceptance Ledger Tool)

**Purpose**: Create the tooling required to generate the evidence-based completion ledger.

- [ ] T003 Create `tools/generate_acceptance_ledger.py` per `data-model.md` schema
- [ ] T004 [P] Implement `AuditEvidence` collection for changelog status using `changelog_validator.py`
- [ ] T005 [P] Implement `AuditEvidence` collection for test results (parses pytest output or junit xml)

---

## Phase 3: User Story 1 - Prove Changelog Provenance (Priority: P1)

**Goal**: Every implemented spec has a valid, machine-parseable changelog entry.

**Independent Test**: `python3 tools/changelog_validator.py` exits 0.

- [ ] T006 [P] [US1] Add missing `CHANGELOG.md` entry for SPEC-004 (Visualization Foundation)
- [ ] T007 [P] [US1] Add missing `CHANGELOG.md` entry for SPEC-005 (Simulator)
- [ ] T008 [P] [US1] Add missing `CHANGELOG.md` entry for SPEC-010 (Archetypes/Recruitment)
- [ ] T009 [P] [US1] Add missing `CHANGELOG.md` entry for SPEC-012 (Analytic Dashboard)
- [ ] T010 [US1] Fix formatting in `CHANGELOG.md` to ensure section headings do not break target parsing
- [ ] T011 [US1] Run `tools/changelog_validator.py` and confirm all spec IDs (000-012) are valid

---

## Phase 4: User Story 2 - Complete Adapter Acceptance (Priority: P1)

**Goal**: SPEC-002 adapters are verified against real emulators.

**Independent Test**: `pytest tests/integration/test_adapters_local.py` passes with no skips.

- [ ] T012 [US2] Update `tests/integration/test_adapters_local.py` to remove `@pytest.mark.skip` for S3, Azure, GCS, and MySQL tests
- [ ] T013 [US2] Ensure Docker Compose services are healthy before integration tests run
- [ ] T014 [US2] Fix any connectivity or schema bugs found during emulator integration

---

## Phase 5: User Story 4 - Close Boolean Semantics Bugs (Priority: P2)

**Goal**: Replace unsafe `.astype(bool)` with domain-aware parsing.

**Independent Test**: `pytest tests/unit/test_boolean_semantics.py` regression tests pass.

- [ ] T015 [P] [US4] Replace `.astype(bool)` in `src/modeling/metrics.py` with `parse_domain_boolean_series`
- [ ] T016 [P] [US4] Replace `.astype(bool)` in `src/simulation/environment.py` with `parse_domain_boolean_series`
- [ ] T017 [US4] Audit and fix remaining `.astype(bool)` in `src/simulation/export.py` diagnostic logic
- [ ] T018 [P] [US4] Add test case for `"0"` and `"False"` string booleans in `tests/unit/test_boolean_semantics.py`

---

## Phase 6: User Story 6 - Improve Visual Clarity (Priority: P2)

**Goal**: Resolve text overlap and font readability in dashboard artifacts.

**Independent Test**: Visual inspection of generated PNGs matches `visual-revision-contract.md`.

- [ ] T019 [US6] Implement `adaptive_fontsize()` helper in `src/visualization/design.py`
- [ ] T020 [US6] Implement `dodge_text()` or equivalent overlap prevention in `src/visualization/design.py`
- [ ] T021 [US6] Update `render_panel_1` in `src/visualization/analytic_dashboard.py` to fix model label overlap
- [ ] T022 [US6] Update `_count_bar` in `src/visualization/eda_core.py` to prevent bar label overlap
- [ ] T023 [US6] Update `src/visualization/patient_view.py` to fix event label collisions on the timeline

---

## Phase 7: User Story 3 - Align Schema CLI (Priority: P2)

**Goal**: CLI works against root `data/` by default.

- [ ] T024 [US3] Add `lullaby_*.csv` aliases to `src/schemas/lullaby.py` so root data validates by default
- [ ] T025 [US3] Update `src/cli/validate_schema.py` to support the new alias-aware resolution

---

## Phase 8: User Story 5 - Completion Ledger (Priority: P3)

- [ ] T026 [US5] Run full audit and generate `artifacts/acceptance-ledger.json`
- [ ] T027 [US5] Verify that no implemented spec has a status of `incomplete` or `blocked` in the ledger

---

## Phase 9: Polish

- [ ] T028 Update `README.md` to reference the `acceptance-ledger.json` for repo auditability
- [ ] T029 Run all tests one last time and verify zero failures and zero required skips
