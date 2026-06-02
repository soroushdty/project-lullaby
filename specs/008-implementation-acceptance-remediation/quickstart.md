# Quickstart: Acceptance Remediation

This guide explains how to run the acceptance audit and generate the remediation ledger.

## Run Audit

To validate the current state of the repository against SPEC-008 criteria:

```bash
# 1. Validate Changelog
python3 tools/changelog_validator.py --changelog CHANGELOG.md --spec-dir specs

# 2. Run All Tests (including integration)
# Note: Requires Docker Compose for SPEC-002 adapters
docker compose up -d
source .venv/bin/activate
pytest
docker compose down

# 3. Generate Ledger
python3 tools/generate_acceptance_ledger.py --output artifacts/acceptance-ledger.json
```

## Review Visual Artifacts

Inspect the generated PNGs for text overlap and readability:

```bash
# Generate all dashboards
python3 -m src.visualization.generate_eda --data-dir data/synthetic
python3 -m src.visualization.analytic_dashboard --model-dir outputs/modeling_synthetic

# View outputs in:
# outputs/figures/eda/
# outputs/figures/analytic/
```

## Remediation Workflow

1. **Fix Boolean Semantics:** Replace `.astype(bool)` with `parse_domain_boolean_series` in affected modules.
2. **Fix Visuals:** Update `src/visualization/design.py` to improve label spacing.
3. **Update Changelog:** Add entries for SPEC-004, SPEC-005, SPEC-010, and SPEC-012.
4. **Re-run Audit:** Confirm ledger shows `complete` for all implemented specs.
