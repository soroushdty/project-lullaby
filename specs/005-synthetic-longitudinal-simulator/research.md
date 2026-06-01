---
id: PLAN-005-RESEARCH
title: Synthetic Longitudinal Physiologic Data Simulator Research
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-005, PLAN-005]
implements: [P2, P3, P5, P7, P8, P9]
supersedes: null
superseded_by: null
related: [SPEC-001, SPEC-004A, SPEC-004B, SPEC-006, SPEC-007]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Research: Synthetic Longitudinal Physiologic Data Simulator

## Decision: Use numpy Generator with explicit stream ownership

**Rationale**: The simulator needs reproducible event assignment, trajectories, missingness,
environment, and alerts. A root seed will create deterministic child streams by component name
so changing missingness logic does not silently reshuffle participant archetypes or event labels.
Numpy should be an explicit project dependency because pandas already relies on it and the
simulator benefits from vectorized sampling.

**Alternatives considered**:
- Python `random`. Rejected because multiple independent streams and vectorized sampling are
  clumsier and easier to perturb accidentally.
- Global numpy random state. Rejected because it weakens reproducibility and test isolation.

## Decision: Represent raw daily vitals as a full participant-day grid

**Rationale**: SPEC-005 clarification requires one row per participant-day for the configured
study window, with nulls for missed observations and dropout. This makes denominators explicit,
supports missingness dashboards, and avoids inferring non-observation only from absent rows.

**Alternatives considered**:
- Export observed days only. Rejected because missingness would be hidden in row gaps.
- Export rows only until dropout. Rejected because post-dropout periods are meaningful for
  adherence and retention diagnostics.

## Decision: Keep configuration in dataclass-style structures loaded from YAML

**Rationale**: Existing configuration modules use dataclasses plus PyYAML. Reusing that pattern
keeps the simulator lightweight, testable, and consistent with SPEC-004A while still allowing
normalization of archetype weights and capture of the effective configuration.

**Alternatives considered**:
- Pydantic settings models. Rejected for this feature because the existing local config style is
  already dataclass-based and the validation needs are straightforward.
- Hardcoded defaults only. Rejected because SPEC-005 requires configurable scenario variants.

## Decision: Extend SPEC-004A registry instead of creating a second schema validator

**Rationale**: Generated tables must validate against the schema registry from SPEC-004A. The
current registry already supports current and future optional entities; SPEC-005 should add
source filenames and roles for `environment` and `recruitment`, plus any required aliases for
synthetic longitudinal columns such as body water, scale adherence, and weight.

**Alternatives considered**:
- Validate simulation outputs only through SPEC-001 Pandera models. Rejected because SPEC-005
  depends on dashboard-facing schema semantics and new output entities.
- Add a simulation-only validator. Rejected because it would diverge from the registry contract.

## Decision: Model physiology with additive latent components and imperfect overlap

**Rationale**: Cardiovascular and heat-strain signals must be directional but not trivially
separable. A participant-day latent risk model can add baseline participant factors, archetype,
PIH severity, environment, adherence, CV-event ramp, and heat-strain spike. Body-water direction
is informative by construction but overlap cases and noise prevent any single raw feature from
perfectly separating labels.

**Alternatives considered**:
- Independent daily draws. Rejected because they do not create longitudinal slopes.
- Fully deterministic clinical rules. Rejected because they would make labels too separable and
  unrealistic for honest evaluation.

## Decision: Implement missingness as layered mechanisms

**Rationale**: SPEC-005 requires MCAR, MAR, MNAR proxy, and clustered gaps. The implementation
will compute observation probabilities from random cell missingness, archetype/adherence,
heat/cooling access, study day, and worsening state, then apply cluster masks for overnight,
feeding/morning, hot afternoon, and late-study decline. Raw nulls remain in the export.

**Alternatives considered**:
- Single random missingness rate. Rejected because it erases participant burden and heat context.
- Imputation during export. Rejected by SPEC-005 and P5.

## Decision: Treat readiness diagnostics as gates

**Rationale**: Schema validation and required target diagnostics are not advisory. If event-rate,
archetype, physiology, missingness, or schema checks fail, artifacts stay available for inspection,
but the summary is failed/not ready and the generation command returns a non-zero status.

**Alternatives considered**:
- Warnings-only target misses. Rejected because downstream dashboards could silently consume a
  malformed cohort.
- Stop before writing artifacts. Rejected because debugging target misses requires inspecting the
  generated package.

## Decision: Use deterministic export ordering and stable IDs

**Rationale**: Reproducibility tests compare CSV content across runs. Participant IDs, alert IDs,
contact IDs, and outcome IDs will be deterministic and sorted; CSV rows and columns will use stable
ordering; timestamp metadata is restricted to summary/config metadata that tests explicitly ignore.

**Alternatives considered**:
- UUIDs or wall-clock IDs. Rejected because they break content reproducibility.
- DataFrame insertion order only. Rejected because it is too easy to perturb across refactors.
