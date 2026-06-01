---
id: TASKS-004A
title: Visualization Foundation and Schema Registry Tasks
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [PLAN-004A, SPEC-004A, SPEC-001]
implements: [P1, P2, P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-004A, SPEC-001, SPEC-004B, SPEC-005, SPEC-006, SPEC-007]
description: "Executable task list for the visualization foundation, semantic schema registry, validation command, design helpers, and figure artifact manifest"
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Tasks: Visualization Foundation and Schema Registry

**Input**: Design documents from `/specs/004-eda-descriptive-dashboard/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md, contracts/

**Tests**: Included because SPEC-004A, quickstart.md, and contracts require focused registry, validation, visualization, manifest, and CLI tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the package, dependency, config, and test-fixture scaffolding needed by all stories.

- [X] T001 Add matplotlib and PyYAML as project dependencies in pyproject.toml
- [X] T002 Create default visualization settings in config/visualization.yaml
- [X] T003 Create visualization package exports scaffold in src/visualization/__init__.py
- [X] T004 [P] Extend pytest fixtures for temporary visualization report and manifest paths in tests/conftest.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement shared configuration and default paths that every user story depends on.

**CRITICAL**: No user story work should begin until this phase is complete.

- [X] T005 Implement VisualizationConfig defaults and optional YAML loading in src/visualization/config.py
- [X] T006 Wire VisualizationConfig exports into src/visualization/__init__.py

**Checkpoint**: Visualization defaults, paths, and package exports are ready for story-level work.

---

## Phase 3: User Story 1 - Resolve Canonical Data Semantics (Priority: P1) MVP

**Goal**: A visualization author can resolve entity metadata and semantic roles without hardcoding raw column names.

**Independent Test**: Load bundled cohort tables, resolve required participant, vital, alert, contact, outcome, and optional future roles, then verify required roles fail clearly while optional roles warn.

### Tests for User Story 1

- [X] T007 [P] [US1] Add registry contract tests for entity loading, current/future entities, and role resolution in tests/contract/test_visualization_registry_contract.py
- [X] T008 [P] [US1] Add registry unit tests for ordered aliases, ambiguous matches, optional warnings, and extra column preservation in tests/unit/test_visualization_schema_registry.py

### Implementation for User Story 1

- [X] T009 [US1] Define EntitySpec, SemanticRole, RoleResolution, and SchemaValidationError models in src/visualization/schema_registry.py
- [X] T010 [US1] Implement current and future optional entity specs with ordered source filenames in src/visualization/schema_registry.py
- [X] T011 [US1] Implement semantic role alias maps for root data/lullaby_*.csv files and data/synthetic/*.csv fixtures in src/visualization/schema_registry.py
- [X] T012 [US1] Implement get_entity and load_entity functions in src/visualization/schema_registry.py
- [X] T013 [US1] Implement resolve_column, available_roles, and require_roles functions in src/visualization/schema_registry.py
- [X] T014 [US1] Export registry public API from src/visualization/__init__.py

**Checkpoint**: User Story 1 is independently functional and registry tests pass.

---

## Phase 4: User Story 2 - Validate Data Without Corrupting It (Priority: P1)

**Goal**: A data analyst can validate visualization readiness while preserving source rows, missingness, extra columns, and plausible physiologic extremes.

**Independent Test**: Run validation against bundled data and injected invalid examples; hard structural failures raise, optional missingness warns, extras pass, and range violations are reported without row removal.

### Tests for User Story 2

- [X] T015 [P] [US2] Add validation unit tests for required-role failures, optional warnings, extra columns, and no imputation in tests/unit/test_visualization_validation.py
- [X] T016 [US2] Add range and capture-worthy tests that verify source rows are preserved in tests/unit/test_visualization_validation.py

### Implementation for User Story 2

- [X] T017 [US2] Define ValidationResult serialization and per-entity status structures in src/visualization/validation.py
- [X] T018 [US2] Implement validate_entity using registry role checks without mutating input frames in src/visualization/validation.py
- [X] T019 [US2] Implement validate_data_dir for current entities and future optional entity warnings in src/visualization/validation.py
- [X] T020 [US2] Implement hard-range violation and capture-worthy value reporting using the bounds table from specs/004-eda-descriptive-dashboard/data-model.md in src/visualization/validation.py
- [X] T021 [US2] Preserve unknown extra columns in validation results in src/visualization/validation.py
- [X] T022 [US2] Export validation public API from src/visualization/__init__.py

**Checkpoint**: User Stories 1 and 2 are independently functional and validation tests pass.

---

## Phase 5: User Story 3 - Render Consistent Dashboard-Grade Figures (Priority: P2)

**Goal**: A dashboard author can create static figures through shared style helpers that enforce accessibility, labels, warning/no-data panels, and size/DPI requirements.

**Independent Test**: Generate sample panels and save attempts; assert dimensions, DPI, labels, warning/no-data behavior, and non-color category encodings meet the contract.

### Tests for User Story 3

- [X] T023 [P] [US3] Add design contract tests for helper APIs, warning/no-data panels, and tiny figure rejection in tests/contract/test_visualization_design_contract.py
- [X] T024 [P] [US3] Add style unit tests for palette, rcParams, labels, minimum dimensions, and non-color encodings in tests/unit/test_visualization_style.py

### Implementation for User Story 3

- [X] T025 [US3] Define VisualizationStyle defaults and config conversion in src/visualization/design.py
- [X] T026 [US3] Implement configure_style in src/visualization/design.py
- [X] T027 [US3] Implement add_dashboard_title, add_panel_label, style_card, and label_bars in src/visualization/design.py
- [X] T028 [US3] Implement render_warning_panel and render_no_data_panel in src/visualization/design.py
- [X] T029 [US3] Implement save_figure with DPI, 1600x900 minimum, test override, and parent directory creation in src/visualization/design.py
- [X] T030 [US3] Export design public API from src/visualization/__init__.py

**Checkpoint**: User Story 3 is independently functional and design contract tests pass.

---

## Phase 6: User Story 4 - Register Deterministic Figure Artifacts (Priority: P2)

**Goal**: A maintainer can create and validate the default empty manifest, then register generated figures with deterministic traceability metadata.

**Independent Test**: Confirm outputs/figures/manifest.json exists as a valid empty manifest, then register a sample entry and validate required fields, warnings, UTC timestamp, deterministic status, and path rules.

### Tests for User Story 4

- [X] T031 [P] [US4] Add manifest contract tests for empty manifest, valid entry, invalid paths, missing fields, and duplicate artifact IDs in tests/contract/test_artifact_manifest_contract.py
- [X] T032 [P] [US4] Add artifact manifest unit tests for sorted serialization, warning preservation, and UTC timestamp validation in tests/unit/test_artifact_manifest.py

### Implementation for User Story 4

- [X] T033 [US4] Define FigureArtifact and FigureArtifactManifest structures in src/visualization/artifacts.py
- [X] T034 [US4] Implement create_empty_manifest, read_manifest, write_manifest, and validate_manifest in src/visualization/artifacts.py
- [X] T035 [US4] Implement register_artifact with sorted entries and deterministic duplicate-ID behavior in src/visualization/artifacts.py
- [X] T036 [US4] Enforce repository-relative outputs/figures/ artifact paths in src/visualization/artifacts.py
- [X] T037 [US4] Integrate manifest defaults from VisualizationConfig in src/visualization/artifacts.py
- [X] T038 [US4] Export artifact manifest public API from src/visualization/__init__.py

**Checkpoint**: User Story 4 is independently functional and manifest tests pass.

---

## Phase 7: User Story 5 - Provide Clone-to-Run Foundation Commands (Priority: P3)

**Goal**: A new contributor can validate the visualization foundation from the repository root with no flags and no network access.

**Independent Test**: From a clean checkout with bundled root data only, run the validation command and focused tests; the command prints a summary, writes artifacts/validation-report.json, and creates outputs/figures/manifest.json.

### Tests for User Story 5

- [X] T039 [P] [US5] Add validation command contract tests for defaults, --config loading, report shape, exit codes, and path creation in tests/contract/test_validation_command_contract.py
- [X] T040 [P] [US5] Add CLI integration tests for default data/ validation and --data-dir data/synthetic validation in tests/integration/test_visualization_foundation_cli.py

### Implementation for User Story 5

- [X] T041 [US5] Implement argparse flags for --data-dir, --report, --manifest, --config, and usage-error handling in src/cli/validate_visualization_foundation.py
- [X] T042 [US5] Wire CLI defaults and --config overrides to VisualizationConfig, validate_data_dir, and manifest initialization in src/cli/validate_visualization_foundation.py
- [X] T043 [US5] Write deterministic JSON validation reports to artifacts/validation-report.json in src/cli/validate_visualization_foundation.py
- [X] T044 [US5] Implement concise stdout summary and stderr error details in src/cli/validate_visualization_foundation.py
- [X] T045 [US5] Add command import coverage and root invocation assertions in tests/integration/test_visualization_foundation_cli.py
- [X] T046 [US5] Align quickstart command examples with implemented CLI behavior in specs/004-eda-descriptive-dashboard/quickstart.md

**Checkpoint**: All user stories are independently functional and clone-to-run validation works.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Verify end-to-end quality, compatibility, documentation, and task completion.

- [X] T047 Implement participant visualization compatibility shim or equivalent dashboard-grade sample artifact path in src/visualization/artifacts.py
- [X] T048 [P] Add participant-visualization compatibility or equivalent dashboard-grade artifact coverage for FR-020 in tests/integration/test_visualization_foundation_cli.py
- [X] T049 [P] Review registry role labels, units, and ranges against schemas/data-dictionary.md
- [X] T050 [P] Update public module exports and docstrings for visualization foundation APIs in src/visualization/__init__.py
- [X] T051 Run focused quickstart tests listed in specs/004-eda-descriptive-dashboard/quickstart.md
- [X] T052 Verify focused foundation test command completes within the plan's 2-minute target in specs/004-eda-descriptive-dashboard/quickstart.md
- [X] T053 Run git diff validation for generated artifacts and whitespace in specs/004-eda-descriptive-dashboard/tasks.md

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1) has no dependencies.
- Foundational (Phase 2) depends on Setup completion and blocks all user stories.
- US1 and US2 are both P1, but US2 depends on US1 registry APIs.
- US3 and US4 depend on Foundational and can proceed after US1 if shared exports are stable.
- US5 depends on US1, US2, US3, and US4 because the CLI validates registry behavior, validation results, manifest creation, and focused contract tests.
- Polish depends on all selected user stories.

### User Story Dependencies

- US1 (P1): Starts after Foundational. Provides semantic registry MVP.
- US2 (P1): Starts after US1. Provides data validation MVP.
- US3 (P2): Starts after Foundational and can be implemented independently of US2 once config is ready.
- US4 (P2): Starts after Foundational and can be implemented independently of US3.
- US5 (P3): Starts after US1 through US4 are complete.

### Within Each User Story

- Tests are written before implementation and should fail before fixes.
- Models and data structures come before service functions.
- Public exports are updated after implementation functions exist.
- A story is complete only when its independent tests pass from the repository root.

### Parallel Opportunities

- Setup task T004 can run in parallel with T001 through T003.
- US1 tests T007 and T008 can run in parallel.
- US2 tests T015 and T016 target the same file and should run sequentially.
- US3 tests T023 and T024 can run in parallel.
- US4 tests T031 and T032 can run in parallel.
- US5 tests T039 and T040 can run in parallel.
- US3 and US4 implementation phases can run in parallel after Foundational if they avoid editing src/visualization/__init__.py at the same time.
- Polish tasks T048 through T050 can run in parallel after T047 direction is clear.

---

## Parallel Example: User Story 1

```bash
Task: "T007 [P] [US1] Add registry contract tests for entity loading, current/future entities, and role resolution in tests/contract/test_visualization_registry_contract.py"
Task: "T008 [P] [US1] Add registry unit tests for ordered aliases, ambiguous matches, optional warnings, and extra column preservation in tests/unit/test_visualization_schema_registry.py"
```

## Parallel Example: User Story 3

```bash
Task: "T023 [P] [US3] Add design contract tests for helper APIs, warning/no-data panels, and tiny figure rejection in tests/contract/test_visualization_design_contract.py"
Task: "T024 [P] [US3] Add style unit tests for palette, rcParams, labels, minimum dimensions, and non-color encodings in tests/unit/test_visualization_style.py"
```

## Parallel Example: User Story 4

```bash
Task: "T031 [P] [US4] Add manifest contract tests for empty manifest, valid entry, invalid paths, missing fields, and duplicate artifact IDs in tests/contract/test_artifact_manifest_contract.py"
Task: "T032 [P] [US4] Add artifact manifest unit tests for sorted serialization, warning preservation, and UTC timestamp validation in tests/unit/test_artifact_manifest.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 and 2)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 to make semantic role resolution work.
3. Complete Phase 4 to validate data without corrupting it.
4. Stop and validate registry plus validation tests before adding design, manifest, or CLI polish.

### Incremental Delivery

1. Deliver US1 and US2 as the schema-driven validation MVP.
2. Add US3 to enforce dashboard-grade visual style behavior.
3. Add US4 to establish deterministic artifact traceability.
4. Add US5 to make the foundation clone-to-run from the repository root.
5. Finish polish only after all story checkpoints pass.

### Parallel Team Strategy

1. Complete Setup and Foundational together.
2. Assign US1 and US2 sequentially because validation depends on registry APIs.
3. Assign US3 and US4 in parallel after Foundational.
4. Assign US5 after US1 through US4 stabilize.

---

## Notes

- [P] tasks use different files or can be coordinated without dependency on incomplete tasks.
- [US1] through [US5] labels map directly to user stories in spec.md.
- Every implementation task names the concrete target file.
- Verify tests fail before implementation tasks for the same story.
- Do not implement later EDA dashboards in SPEC-004A; this task list creates the shared foundation only.
