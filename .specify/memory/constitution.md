<!--
SYNC IMPACT REPORT
Version change: unknown -> 1.0.0
Modified principles: P1 Specification-Driven Development (added);
	P2 Reproducibility by Default (added); P3 Schema-Driven Extensibility (added);
	P4 Source-Agnostic Ingestion (added); P5 Resilience / Graceful Degradation (added);
	P6 Distribution Integrity (added); P7 Honest Evaluation (added);
	P8 Clinical Fidelity & Participant Safety (added); P9 Privacy & Synthetic-Data Transparency (added);
	P10 Equity-Centered & Accessible Design (added)
Added sections: Preamble/Identity, Core Principles, Product invariants, Governance & Provenance
Removed sections: none
Templates requiring updates: .specify/templates/plan-template.md: ⚠ pending
	.specify/templates/spec-template.md: ⚠ pending
	.specify/templates/tasks-template.md: ⚠ pending
	.specify/templates/commands/*.md: ⚠ pending
Follow-up TODOs:
	- Update templates to include provenance frontmatter and references to new principles.
	- Verify plan/spec/tasks templates align with Product invariants and safety-critical guidance.
	- Run `speckit.agent-context.update` after constitution commit (optional hook configured).
-->

# Project Lullaby Constitution

## Core Principles

### Preamble / Identity
Project Lullaby is a specification-driven, reproducible analytics control center
(interactive dashboard + ML pipeline) for postpartum cardiovascular-risk surveillance.
Built on a synthetic prospective-cohort dataset, it shows how passive multimodal
monitoring of postpartum mothers with pregnancy-induced hypertension (PIH) in South
Phoenix/Mesa can distinguish cardiovascular emergencies from heat strain across the
high-risk 12-week postpartum window, and evaluates candidate risk-prediction models
against a clinical baseline. It is schema-driven and multi-tenant by design: the bundled
cohort is the first tenant, and any institution can run the same study design on its own
conforming population without forking the code.

### P1: Specification-Driven Development
No implementation lands without an approved spec; the constitution and specs are the
source of truth, and code conforms to them, never the reverse.

### P2: Reproducibility by Default
Clone -> run regenerates every figure, metric, and dashboard view from the synthetic data
via deterministic, documented steps (pinned dependencies, fixed seeds).

### P3: Schema-Driven Extensibility
The product is driven by the canonical schema and configuration, never hardcoded to one
dataset. The schema is an abstract base class: the repo ships a default concrete
implementation, and users MAY subclass it and inject their own schema object. A new
population is onboarded by conforming data, not by editing code.

### P4: Source-Agnostic Ingestion
Every source (file, remote link, cloud object store, SQL, REDCap, REST API, GraphQL,
stream) normalizes into one canonical time-series schema through a uniform adapter layer;
batch and real-time are indistinguishable downstream, and cadence (daily today, per-minute
tomorrow) is carried as data.

### P5: Resilience / Graceful Degradation
The system fails loud rather than corrupt: validation is a first-class stage, partial
loads never commit, and edge cases from software faults or user error surface as actionable
errors. Informative missingness is preserved, never silently imputed, and
clinically-plausible extremes are treated as capture-worthy, not discarded as noise.

### P6: Distribution Integrity
The three forms (GitHub Pages, source release, Docker) build from one source of truth and
must never diverge into separate code paths.

### P7: Honest Evaluation
Models are judged with imbalance- and rare-event-appropriate metrics (AUPRC, recall at
fixed precision, calibration) against a transparent baseline, with confidence intervals,
limitations stated beside every result, and no metric cherry-picking.

### P8: Clinical Fidelity & Participant Safety
Domain logic (yellow/red/composite-red alert thresholds, the primary CV-event composite,
escalation rules) mirrors the documented study design exactly and is treated as
safety-critical, not casually tunable.

### P9: Privacy & Synthetic-Data Transparency
All data is clearly labeled synthetic, no real PHI ever enters the repo, and data is
handled as if it were sensitive.

### P10: Equity-Centered & Accessible Design
Both the analysis and the dashboard UX foreground the population's lived constraints
(energy poverty, health literacy, cognitive load) and meet basic accessibility standards.

## Product invariants

- Three distribution forms build from ONE source of truth: (F1) GitHub Pages static site
	for showcase, (F2) tagged source release, (F3) single Dockerfile for adopting
	institutions. They MUST NOT diverge into separate code paths.
- F1 (Pages, no server) ships a static demo + a SIMULATED live view; F3 (Docker) is the
	only form that performs real ingestion. F1 and F3 share the same rendering layer.
- Batteries-included: clone -> run yields working dashboards on bundled synthetic data with
	zero external setup.
- Non-goals (MVP): real-data/PHI handling, adaptive/personalized alert sensitivity, a live
	server-backed real-time pipeline on the Pages form, and any in-repo financial-data
	product (finance lives only in the presentation/website narrative, see §8).

## Provenance / Traceability

Every spec, the constitution, and every doc carries YAML frontmatter for provenance,
traceability, and auditability. Example frontmatter fields: id, title, status, version,
created, updated, author, depends_on, implements, supersedes, related.

## Governance

This is a single-maintainer repo (Soroush Dianaty). Amendments are made by the maintainer
via pull request against this constitution, with the rationale recorded in the PR and a
version bump. Changes to a Principle, to the canonical schema, or to any safety-critical
domain constant (alert thresholds, CV-event composite, escalation logic) MUST be called out
explicitly in the PR description and the changelog. Data is synthetic, so no IRB gate
applies; real-data use would require IRB review before deployment.

**Version**: 1.0.0 | **Ratified**: 2026-05-31 | **Last Amended**: 2026-05-31

