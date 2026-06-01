# Project Lullaby
Project Lullaby is a digital health surveilance system for low-income mothers with PIH in South Phoenix and Mesa, using passive monitoring, heat-risk context, and timely clinical escalation to prevent stroke and maternal mortality.

## Changelog Validator

This repository includes a lightweight changelog validator to enforce that every implemented spec adds a single, machine-parseable entry to `CHANGELOG.md`.

Quick usage:

```bash
# run the validator (example)
python3 tools/changelog_validator.py --changelog CHANGELOG.md --spec-dir specs --spec-id 000-changelog-creation --merge-date 2026-06-01
```

Authoring checklist for PRs implementing a spec:

- Include the `spec-id` in the PR title or body.
- Add exactly one changelog entry for that `spec-id` to `CHANGELOG.md`.
- Use the canonical entry fields: `Date`, `Spec`, `Summary`, `Rationale`, `Impact`, `Targets`.
- `Targets` lines must follow `path | +added -removed` grammar.
- The CI workflow `.github/workflows/changelog-policy.yml` runs the validator and blocks merges on failure.

See `specs/000-changelog-creation/quickstart.md` for detailed examples and test commands.

## Synthetic Longitudinal Simulator

SPEC-005 adds a seeded simulator for the bundled synthetic postpartum cohort. It writes the
canonical longitudinal package to `data/synthetic/longitudinal/`:

```bash
python3 scripts/generate_synthetic.py \
  --config config/simulation.yaml \
  --out-dir data/synthetic/longitudinal \
  --seed 20260601
```

The output package contains participants, daily vitals, alerts, staff contacts, clinical
outcomes, environment, recruitment, the effective config, and a readiness summary. Generated
CSV files are deterministic for a fixed seed/config and preserve missing observations as empty
cells in the full participant-day grid.

All simulator outputs are synthetic, include synthetic provenance fields, and must not be
treated as real PHI. The readiness summary gates downstream use on schema validation and target
diagnostics.
