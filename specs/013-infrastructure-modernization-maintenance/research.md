# Research: 2026-06-01 Repository Audit Findings

## Technical Debt Identifiers

### 1. Deprecated Pandera Imports
The codebase currently uses `import pandera as pa` at the top level in 8 files. This has been deprecated in favor of `import pandera.pandas as pa` or `import pandera.polars as pa`.
- **Affected files**:
  - `src/validation/pandera_models.py`
  - `src/validation/engine.py`
  - `src/schemas/lullaby.py`
  - `tests/unit/test_pandera_models.py`
  - `tests/unit/test_stream_adapter_unit.py`
  - `tests/contract/test_stream_adapter_contract.py`
  - `tests/contract/test_schema_interface.py`
  - `tests/conftest.py`

### 2. Integration Test Bottlenecks
The emulated integration tests (`tests/integration/test_adapters_emulated.py`) take up to 3 minutes each because they rely on library-internal retry logic that waits for timeouts when the emulator is not yet ready.
- **Root Cause**: Tests do not explicitly wait for container health before attempting connections.
- **Impact**: Full test suite runtime is > 8 minutes, with 90% of time spent waiting on network retries.

### 3. Baseline Test Warnings
Pytest emits ~23 warnings during a clean run.
- **Manifest Warnings**: `RuntimeWarning: Generated artifacts... are outside the repository`. This happens because tests use temporary directories for output, which the registration logic (rightly) flags as suspicious for production use.
- **Date Format Warnings**: Pandas emits `UserWarning: Could not infer format` in `eda_relationships.py` and `eda_archetypes.py`. This is risky for cross-locale deployment.
- **Pandera Warnings**: Baseline import warnings about future removals.

### 4. Template Drift
The `.specify/templates/` directory contains templates created before the v1.0.0 Constitution.
- **Gaps**:
  - Missing required provenance fields (e.g., `related`, `supersedes`).
  - "Constitution Check" section is generic and only lists 3 principles instead of 10.
  - Frontmatter doesn't match the `SPEC-XXX` pattern enforced by newer validators.

## Proposed Fixes

### 1. Unified Pandera Modernization
Batch replace `import pandera as pa` with `import pandera.pandas as pa`.

### 2. Service Health Waiters
Implement a shared `wait_for_service(endpoint, timeout)` fixture in `tests/conftest.py` that uses socket probing or simple HTTP GETs before running integration tests.

### 3. Suppress Known Test Artifact Warnings
Update `_register_results` in `src/visualization/eda_core.py` to check for a `TEST_MODE` environment variable or accept a flag to suppress repository-relative checks during unit tests.

### 4. Explicit Date Parsing
Update all `pd.to_datetime` calls in visualization modules to include `format="ISO8601"` or similar, where appropriate.
