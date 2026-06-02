---
id: SPEC-013
title: Infrastructure Modernization and Maintenance
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Gemini CLI
depends_on: [SPEC-008]
implements: [P1, P2, P5, P6, P10]
description: "Address technical debt, test fragility, and template misalignment identified during the 2026-06-01 audit."
---

# Specification: Infrastructure Modernization

## Problem

The repository audit identified several areas of technical debt and infrastructure fragility that hinder developer velocity and long-term maintainability:
1. **Dependency Drift**: `pandera` imports use deprecated top-level patterns.
2. **Test Fragility**: Integration tests for cloud adapters are slow and prone to failure if emulators are not perfectly ready.
3. **Template Misalignment**: Specification templates do not reflect the v1.0.0 Constitution's principles and provenance requirements.
4. **Tooling Noise**: Tests emit warnings about manifest registration and date inference that obscure real issues.

## Goals

- [ ] Modernize all `pandera` imports to use the `pandera.pandas` namespace.
- [ ] Optimize the integration test suite to handle emulator latency and reduce runtime.
- [ ] Update all `.specify/templates` to align with current project standards.
- [ ] Eliminate baseline warnings from the `pytest` output.

## User Scenarios

### User Story 1 - Modernize Dependencies (Priority: P1)
As a maintainer, I want to use current library patterns so that the codebase remains compatible with future dependency updates.

### User Story 2 - Resilient & Fast Integration Tests (Priority: P1)
As a developer, I want the integration test suite to be reliable and fast (ideally < 3 minutes) so that I am not slowed down by brittle cloud emulators.

### User Story 3 - Align Governance Templates (Priority: P2)
As a contributor, I want the spec/plan/task templates to include required provenance fields and references to all project principles (P1-P10).

### User Story 4 - Noise-Free Testing (Priority: P3)
As a reviewer, I want `pytest` to run without baseline warnings so that new issues are immediately obvious.

## Requirements

### Functional Requirements
- **FR-001**: All top-level `import pandera as pa` MUST be replaced with `import pandera.pandas as pa`.
- **FR-002**: Cloud adapter integration tests MUST use a wait-for-service pattern instead of long, static timeouts or retries.
- **FR-003**: The `_register_results` logic in `eda_core.py` MUST support a "test mode" that allows registration of artifacts generated in temporary directories.
- **FR-004**: All date-parsing logic in visualizations MUST specify an explicit format string (e.g., ISO 8601) to silence Pandas inference warnings.
- **FR-005**: All specification templates in `.specify/templates/` MUST include standard provenance frontmatter (id, title, status, version, created, updated, author, depends_on, implements, supersedes, related).
- **FR-006**: Templates MUST include a "Constitution Check" section referencing all ten principles (P1-P10).
- **FR-007**: `tests/conftest.py` MUST use `tempfile.gettempdir()` for `MPLCONFIGDIR`.

### Non-Functional Requirements
- **NFR-001**: The full test suite (excluding emulated integration) MUST complete in < 60 seconds.
- **NFR-002**: Emulated integration tests MUST complete in < 2 minutes total.

## Success Criteria
- **SC-001**: `pytest` runs with zero warnings (other than intentionally ignored third-party deprecations).
- **SC-002**: `grep -r "import pandera as pa"` returns zero matches.
- **SC-003**: New features created with `speckit.specify` use the updated v1.0.0 templates.
- **SC-004**: Integration tests for S3/Azure/GCS/MySQL pass consistently on the first attempt after `docker compose up`.
