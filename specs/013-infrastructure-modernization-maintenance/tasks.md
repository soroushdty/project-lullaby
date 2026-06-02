---
id:            TASKS-013
title:         Infrastructure Modernization and Maintenance — Tasks
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Gemini CLI
depends_on:    [PLAN-013]
implements:    [SPEC-013]
description:   "Fix technical debt, slow tests, and outdated templates."
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Tasks: Infrastructure Modernization

**Input**: Audit findings from `research.md`

## Phase 1: Setup

- [ ] T001 Initialize branch `013-infrastructure-modernization`
- [ ] T002 Baseline current test warnings and runtime with `pytest -W ignore::DeprecationWarning`

---

## Phase 2: User Story 1 - Modernize Dependencies (Priority: P1)

- [ ] T003 Batch replace `import pandera as pa` with `import pandera.pandas as pa` in `src/` and `tests/`
- [ ] T004 Verify that all Pandera validation tests still pass with the new import pattern

---

## Phase 3: User Story 2 - Resilient & Fast Integration Tests (Priority: P1)

- [ ] T005 Implement `wait_for_service` utility in `tests/conftest.py`
- [ ] T006 Update `tests/integration/test_adapters_emulated.py` to use service health checks before starting tests
- [ ] T007 Update `tests/integration/test_adapters_local.py` (MySQL) to use health checks
- [ ] T008 Optimize Tenacity retry policies in adapters to fail faster during integration tests (using environment variable overrides)

---

## Phase 4: User Story 4 - Noise-Free Testing (Priority: P3)

- [ ] T009 Update `_register_results` in `src/visualization/eda_core.py` to support `LULLABY_TEST_MODE` to suppress repo-relative warnings
- [ ] T010 Update `tests/conftest.py` to set `LULLABY_TEST_MODE=1`
- [ ] T011 Audit `pd.to_datetime` in `src/visualization/` and add explicit `format="ISO8601"`
- [ ] T012 Update `tests/conftest.py` to use `tempfile.gettempdir()` for `MPLCONFIGDIR`

---

## Phase 5: User Story 3 - Align Governance Templates (Priority: P2)

- [ ] T013 Update `.specify/templates/spec-template.md` with full provenance frontmatter and v1.0.0 principles
- [ ] T014 Update `.specify/templates/plan-template.md` with v1.0.0 principle checks
- [ ] T015 Update `.specify/templates/tasks-template.md` with v1.0.0 formatting standards
- [ ] T016 Run `speckit.agent-context.update` to ensure all agents use the new templates

---

## Phase 6: Polish & Verification

- [ ] T017 Final test run: Verify zero baseline warnings and suite runtime < 3 minutes
- [ ] T018 Generate final Acceptance Ledger and confirm green status
