---
id:            TASKS-000
title:         Changelog Creation Requirement Tasks
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [PLAN-000, SPEC-000]
implements:    [P1, P2, P5]
supersedes:    null
superseded_by: null
related:       [PLAN-000, SPEC-000]
description: "Executable task list for changelog policy validation and CI merge gate"
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Tasks: Changelog Creation Requirement

**Input**: Design documents from `/specs/000-changelog-creation/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included because spec and quickstart require CI/test verification of changelog policy.

**Organization**: Tasks are grouped by user story to enable independent implementation and validation.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create project files and wiring scaffolding for validator and policy checks.

- [X] T001 Create validator CLI scaffold with argparse entrypoint in tools/changelog_validator.py
- [X] T002 Create unit test module scaffold for validator behavior in tests/unit/test_changelog_validator.py
- [X] T003 Create contract test module scaffold for changelog contracts in tests/contract/test_changelog_contract.py
- [X] T004 Create integration test module scaffold for CI gate behavior in tests/integration/test_changelog_ci_gate.py
- [X] T005 Create GitHub Actions workflow scaffold for changelog policy in .github/workflows/changelog-policy.yml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement reusable parser/validation core required by all user stories.

**⚠️ CRITICAL**: No user story work begins until this phase is complete.

- [X] T006 Implement changelog entry section parser and heading detection in tools/changelog_validator.py
- [X] T007 [P] Implement normalized validation error/report structures in tools/changelog_validator.py
- [X] T008 Implement markdown field extraction for Date/Spec/Summary/Rationale/Impact/Targets in tools/changelog_validator.py
- [X] T009 [P] Implement spec-id extraction from Spec links and identifier normalization in tools/changelog_validator.py
- [X] T010 Implement CLI output formatter for success summary and actionable failure diagnostics in tools/changelog_validator.py

**Checkpoint**: Parser and validation primitives are ready for story-level rules.

---

## Phase 3: User Story 1 - Enforce Exactly One Valid Entry Per Spec (Priority: P1) 🎯 MVP

**Goal**: Ensure each implemented spec has exactly one changelog entry with all required fields.

**Independent Test**: Running validator against fixture changelogs passes for a single complete entry and fails for missing fields or duplicate spec-id.

### Tests for User Story 1

- [X] T011 [P] [US1] Add unit tests for required field presence and missing-field failures in tests/unit/test_changelog_validator.py
- [X] T012 [P] [US1] Add unit tests for duplicate spec-id detection and exactly-one rule in tests/unit/test_changelog_validator.py
- [X] T013 [US1] Add contract tests asserting required entry fields from contract docs in tests/contract/test_changelog_contract.py

### Implementation for User Story 1

- [X] T014 [US1] Implement required field validation rules for each parsed entry in tools/changelog_validator.py
- [X] T015 [US1] Implement uniqueness enforcement for spec-id across all CHANGELOG entries in tools/changelog_validator.py
- [X] T016 [US1] Implement failure codes/messages for missing fields and duplicate spec-id in tools/changelog_validator.py

**Checkpoint**: US1 is independently functional and testable as MVP scope.

---

## Phase 4: User Story 2 - Validate Structured Targets and Actionable Diagnostics (Priority: P2)

**Goal**: Enforce machine-parseable Targets format and provide clear diagnostics for violations.

**Independent Test**: Validator accepts valid `path | +added -removed` lines and fails with field/code diagnostics for malformed or empty path targets.

### Tests for User Story 2

- [X] T017 [P] [US2] Add unit tests for valid and invalid Targets grammar parsing in tests/unit/test_changelog_validator.py
- [X] T018 [P] [US2] Add contract tests for TargetDelta constraints (non-empty path, non-negative ints) in tests/contract/test_changelog_contract.py

### Implementation for User Story 2

- [X] T019 [US2] Implement Targets line parser for `path | +added -removed` grammar in tools/changelog_validator.py
- [X] T020 [US2] Implement TargetDelta semantic validation for repository-relative non-empty path and integer bounds in tools/changelog_validator.py
- [X] T021 [US2] Extend diagnostics to include violation code, field, and failing spec-id when available in tools/changelog_validator.py

**Checkpoint**: US2 validation and diagnostics are independently functional.

---

## Phase 5: User Story 3 - Enforce Merge-Time CI Validation Gate (Priority: P3)

**Goal**: Block merges when changelog policy fails and enforce Date policy checks.

**Independent Test**: CI workflow fails on invalid changelog and passes on valid changelog using the required validator command.

### Tests for User Story 3

- [X] T022 [P] [US3] Add integration test covering validator CLI exit-code behavior for pass/fail scenarios in tests/integration/test_changelog_ci_gate.py
- [X] T023 [P] [US3] Add unit tests for ISO date parsing and merge-date policy gate branches in tests/unit/test_changelog_validator.py

### Implementation for User Story 3

- [X] T024 [US3] Implement Date ISO parsing and merge-date policy validation hooks in tools/changelog_validator.py
- [X] T025 [US3] Implement GitHub Actions workflow steps to run validator on pull requests in .github/workflows/changelog-policy.yml
- [X] T026 [US3] Configure workflow output and failure behavior to satisfy required status-check contract in .github/workflows/changelog-policy.yml

**Checkpoint**: US3 CI gate behavior is independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final hardening and documentation alignment across all stories.

- [ ] T027 [P] Add end-to-end contract + integration test command coverage to quickstart guidance in specs/000-changelog-creation/quickstart.md
- [ ] T028 [P] Document validator usage and changelog authoring checklist in README.md
- [ ] T029 Run full validation test selection from quickstart and adjust failing expectations in tests/unit/test_changelog_validator.py

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1) has no dependencies.
- Foundational (Phase 2) depends on Setup and blocks all user stories.
- User Story phases (Phase 3-5) depend on Foundational completion.
- Polish (Phase 6) depends on completion of desired user stories.

### User Story Dependencies

- US1 (P1) starts immediately after Foundational and defines MVP.
- US2 (P2) starts after Foundational; independent from US1 but reuses parser core.
- US3 (P3) starts after Foundational; can proceed in parallel with US2.

### Within Each User Story

- Tests are authored before implementation and should fail before fixes.
- Validation logic lands before workflow integration.
- Story is complete only when independent test criteria pass.

### Parallel Opportunities

- Phase 2: T007 and T009 can run in parallel after T006.
- US1: T011 and T012 can run in parallel.
- US2: T017 and T018 can run in parallel.
- US3: T022 and T023 can run in parallel.
- Polish: T027 and T028 can run in parallel.

---

## Parallel Example: User Story 2

```bash
Task: "Add unit tests for valid and invalid Targets grammar parsing in tests/unit/test_changelog_validator.py"
Task: "Add contract tests for TargetDelta constraints (non-empty path, non-negative ints) in tests/contract/test_changelog_contract.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate US1 independent test criteria before expanding scope.

### Incremental Delivery

1. Deliver US1 as merge-gating baseline.
2. Add US2 for structured Targets and improved diagnostics.
3. Add US3 for CI-required enforcement and date policy.
4. Finalize docs and full test run in Polish phase.

### Parallel Team Strategy

1. Team aligns on Phase 1 and Phase 2.
2. After foundation, split US2 and US3 while keeping US1 stable.
3. Rejoin for cross-cutting polish and final validation.

---

## Notes

- [P] tasks are safe to run concurrently when dependencies are satisfied.
- [US#] labels provide traceability from tasks to story outcomes.
- Every task includes an explicit file path to remain LLM-executable.