# Project Lullaby
Project Lullaby is a digital health surveilance system for low-income mothers with PIH in South Phoenix and Mesa, using passive monitoring, heat-risk context, and timely clinical escalation to prevent stroke and maternal mortality.

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
