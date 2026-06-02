# Research: Acceptance Audit and Remediation

## Audit Findings (Session 2026-06-01)

### 1. Provenance Failures
- `CHANGELOG.md` is missing entries for SPEC-004, SPEC-005, SPEC-010, and SPEC-012.
- `tools/changelog_validator.py` confirms that missing specs cause failure when enforced via `--spec-id`.

### 2. Integration Test Gaps
- SPEC-002 adapters for S3 (MinIO), Azure (Azurite), GCS (fake-gcs-server), and MySQL have unit tests but their integration tests are explicitly skipped with `@pytest.mark.skip`.
- `docker compose` is available and the services are defined, but not wired into the test suite.

### 3. Boolean Semantics
- Found remaining `.astype(bool)` uses in:
  - `src/modeling/metrics.py:160` (primary_metric)
  - `src/simulation/environment.py:51` (heat_wave)
- These can misinterpret string booleans (e.g., `"0"` becomes `True`).

### 4. Visual Readability
- Dashboard PNGs (Spec 012 and EDA) exhibit text overlap in:
  - Model leaderboard (yticklabels).
  - Engagement funnel (labels on bars).
  - Cohort overview (metric card subtitles).
- Fixed font sizes and manual offsets in `design.py` do not scale with data density.

## Technical Approach

### 1. Adaptive Visualization
- Introduce `adaptive_fontsize()` in `design.py` that scales based on the number of elements in a panel.
- Implement `dodge_text()` to prevent label collisions in horizontal bar charts.

### 2. Boolean Hardening
- Use `parse_domain_boolean_series` from `src.validation.semantics` to replace all `.astype(bool)` calls.
- Add regression tests to ensure `"False"` and `"0"` are handled correctly.

### 3. Acceptance Ledger
- Create `tools/generate_acceptance_ledger.py` to automate the collection of evidence (changelog, tests, artifacts) for all specs.
