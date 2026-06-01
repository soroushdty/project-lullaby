# CHANGELOG

Policy: Every time a speckit (spec) is implemented, add a dated entry here that documents provenance and the concrete changes introduced.

Each entry MUST include:
- Date: ISO 8601 (YYYY-MM-DD)
- Spec: canonical link to the spec (URL or repo path). Do NOT use only a verbal description.
- Summary: brief description of the major changes introduced by the spec.
- Rationale: why this spec was necessary (design goals, problem being solved, alternatives considered).
- Impact: record concrete effects, including whether it broke anything or changed project requirements.
- Targets: list of specific files modified (path) and the line diff(s) for each file (unified diff or explicit line ranges). Line diff only is sufficient.

Template
--------
```
Date: 2026-05-31
Spec: <link-to-spec-or-path>
Summary: One-line summary of major changes.
Rationale: Short paragraph explaining why the spec was necessary.
Impact:
  - Broke/Changed requirements: yes/no and brief details
  - Docs/Constitution changes: list
Targets:
  - path/to/file.ext: (line counts only; additions and deletions)
    +3 -1
```

 
Notes
-----
- Keep entries concise and factual. Prefer linking to the authoritative spec document.
- Record only per-file line counts (e.g. `+3 -1`) instead of pasting actual changed lines into the changelog.
- For large specs that touch many files, include only the file paths and line counts; avoid pasting whole files into the changelog.
- Use a single changelog entry per implemented spec. If multiple specs are implemented on the same date, add separate dated entries.

Date: 2026-06-01
Spec: /specs/009-longitudinal-vitals-missingness-timeline/spec.md
Summary: Implement SPEC-009 longitudinal EDA dashboards, selected-participant clinical timeline, missingness/adherence diagnostics, signal-quality ranking, CLI filters, and manifest provenance.
Rationale: SPEC-009 extends static descriptive EDA beyond cross-sectional summaries so reviewers can inspect study-day trajectories, visible missingness, adherence decline, event alignment, and data-quality evidence without implying prediction, imputation, or clinical-risk ranking.
Impact:
  - Broke/Changed requirements: yes; the EDA CLI now supports `--panels longitudinal`, participant selection, inclusive week filters, and optional environment overlays, and generated manifest entries now include SPEC-009 required roles, selected-participant metadata, quality-score formulas, missingness caveats, and no-imputation metadata.
  - Docs/Constitution changes: no constitution changes; SPEC-009 plan, research, data model, contracts, quickstart, and tasks were added, with acceptance evidence recorded after full local validation.
Targets:
  - .specify/feature.json | +1 -1
  - CHANGELOG.md | +34 -0
  - src/visualization/__init__.py | +34 -0
  - src/visualization/eda_longitudinal.py | +1254 -0
  - src/visualization/generate_eda.py | +35 -8
  - src/visualization/patient_view.py | +357 -0
  - src/visualization/schema_registry.py | +3 -0
  - tests/test_eda_longitudinal_outputs.py | +290 -0
  - tests/test_patient_timeline.py | +85 -0
  - outputs/figures/manifest.json | +930 -4
  - outputs/figures/eda/05_vital_trajectories.png | +0 -0
  - outputs/figures/eda/06_missingness_adherence.png | +0 -0
  - outputs/figures/eda/07_patient_timeline.png | +0 -0
  - outputs/figures/eda/08_data_quality_scorecard.png | +0 -0
  - outputs/figures/eda/09_missingness_mechanism.png | +0 -0
  - specs/009-longitudinal-vitals-missingness-timeline/spec.md | +229 -0
  - specs/009-longitudinal-vitals-missingness-timeline/plan.md | +227 -0
  - specs/009-longitudinal-vitals-missingness-timeline/research.md | +153 -0
  - specs/009-longitudinal-vitals-missingness-timeline/data-model.md | +298 -0
  - specs/009-longitudinal-vitals-missingness-timeline/quickstart.md | +133 -0
  - specs/009-longitudinal-vitals-missingness-timeline/tasks.md | +308 -0
  - specs/009-longitudinal-vitals-missingness-timeline/contracts/cli-contract.md | +74 -0
  - specs/009-longitudinal-vitals-missingness-timeline/contracts/longitudinal-artifacts-contract.md | +103 -0
  - specs/009-longitudinal-vitals-missingness-timeline/contracts/manifest-contract.md | +69 -0
  - specs/009-longitudinal-vitals-missingness-timeline/contracts/quality-missingness-contract.md | +94 -0

Date: 2026-06-01
Spec: /specs/007-core-descriptive-eda-dashboards/spec.md
Summary: Implement SPEC-007 traceability for core descriptive EDA dashboards, manifest entries, required-role coverage, hard-range vital rendering, and acceptance evidence.
Rationale: SPEC-007 formalizes the first four descriptive dashboard panels as static, reproducible, schema-driven artifacts. This pass aligns the existing EDA renderer with SPEC-007 provenance, expands tests for required role failures and panel dimensions, preserves hard-range vital values as `impossible by schema` evidence, and records default plus synthetic generation evidence.
Impact:
  - Broke/Changed requirements: yes; generated core EDA manifest entries now identify SPEC-007, Panel 3 manifest metadata includes `vital.systolic_bp` as a required role, hard-range daily vital values render as `impossible by schema` instead of failing the EDA CLI, and FR-008 now scopes registration to repo-relative artifacts while outside-repo outputs warn.
  - Docs/Constitution changes: no constitution changes; SPEC-007 tasks marked complete, quickstart records timing evidence, and branch traceability notes retain the pinned `007` feature directory while the current branch remains `006-core-descriptive-eda-dashboards`.
Targets:
  - CHANGELOG.md | +19 -0
  - src/visualization/__init__.py | +22 -0
  - src/visualization/eda_core.py | +4 -8
  - tests/test_eda_core_outputs.py | +58 -2
  - tests/unit/test_artifact_manifest.py | +1 -1
  - outputs/figures/manifest.json | +20 -18
  - outputs/figures/eda/02_outcome_prevalence.png | +0 -0
  - specs/007-core-descriptive-eda-dashboards/spec.md | +1 -1
  - specs/007-core-descriptive-eda-dashboards/quickstart.md | +12 -0
  - specs/007-core-descriptive-eda-dashboards/tasks.md | +64 -64

Date: 2026-06-01
Spec: /specs/006-data-semantics-validation-hardening/spec.md
Summary: Implement shared domain boolean semantics, EDA missingness/preflight hardening, manifest registration expansion, simulator diagnostic truthiness fixes, and category-completeness preservation.
Rationale: Repo-wide audit found that CSV/object boolean values, missing outcomes, optional dashboard inputs, contact completion states, and top-N category defaults could silently distort descriptive evidence or provenance. SPEC-006 centralizes parsing, fails required invalid inputs before artifacts are written, preserves missingness as evidence, and keeps generated dashboard artifacts aligned with hardened semantics.
Impact:
  - Broke/Changed requirements: yes; required EDA panel inputs now fail before writing/registering artifacts, invalid required boolean tokens fail diagnostics/preflight, optional invalid boolean tokens warn as Missing/Unknown, and repo-relative alternate outputs are registered in the default manifest.
  - Docs/Constitution changes: no constitution changes; SPEC-006 tasks marked complete after implementation.
Targets:
  - src/validation/semantics.py | +159 -0
  - src/validation/__init__.py | +19 -0
  - src/ingestion/stream/adapter.py | +12 -1
  - src/simulation/export.py | +92 -13
  - src/visualization/eda_core.py | +390 -114
  - src/visualization/artifacts.py | +3 -3
  - tests/unit/test_boolean_semantics.py | +104 -0
  - tests/unit/test_stream_adapter_unit.py | +24 -0
  - tests/unit/test_simulation_targets.py | +53 -1
  - tests/unit/test_simulation_schema_validation.py | +16 -5
  - tests/test_eda_missingness_policy.py | +77 -1
  - tests/test_eda_core_outputs.py | +119 -1
  - tests/unit/test_artifact_manifest.py | +59 -0
  - outputs/figures/manifest.json | +122 -4
  - outputs/figures/eda/01_cohort_overview.png | +0 -0
  - outputs/figures/eda/02_outcome_prevalence.png | +0 -0
  - outputs/figures/eda/04_alert_engagement_funnel.png | +0 -0
  - specs/006-data-semantics-validation-hardening/tasks.md | +55 -55

Date: 2026-06-01
Spec: /specs/003-streaming-ingestion/spec.md
Summary: Implement synchronous reference streaming ingestion with `StreamAdapter`, `StreamAdapterConfig`, `StreamAccumulator`, stream-specific errors, tier-1 tests, and CI workflow proving synthetic-cohort stream/batch equivalence.
Rationale: Project Lullaby needs real-time replay semantics that normalize to the same canonical schema as batch ingestion, preserve schema-driven dedup/order behavior, tolerate controlled clock skew, and fail loudly on corrupt or partial stream windows.
Impact:
  - Broke/Changed requirements: no; SPEC-003 clarifies empty-window semantics, static no-timestamp table handling, and `speed_factor` as a compatibility field that does not alter timing.
  - Docs/Constitution changes: no constitution changes; SPEC-003 plan, research, data-model, contracts, quickstart, and tasks updated for implementation consistency.
Targets:
  - src/ingestion/stream/__init__.py | +12 -0
  - src/ingestion/stream/adapter.py | +315 -0
  - src/ingestion/stream/accumulator.py | +38 -0
  - src/ingestion/stream/errors.py | +13 -0
  - src/ingestion/adapters/remote_link_adapter.py | +7 -3
  - tests/unit/test_stream_adapter_unit.py | +353 -0
  - tests/contract/test_stream_adapter_contract.py | +168 -0
  - tests/integration/test_stream_equivalence.py | +100 -0
  - .github/workflows/test-stream.yml | +23 -0
  - specs/003-streaming-ingestion/tasks.md | +296 -0
  - specs/003-streaming-ingestion/spec.md | +6 -5
  - specs/003-streaming-ingestion/plan.md | +6 -5
  - specs/003-streaming-ingestion/research.md | +20 -5
  - specs/003-streaming-ingestion/data-model.md | +4 -3
  - specs/003-streaming-ingestion/quickstart.md | +19 -9
  - specs/003-streaming-ingestion/contracts/stream-adapter-interface.md | +10 -5
  - specs/003-streaming-ingestion/contracts/stream-config-schema.md | +1 -1

Date: 2026-06-01
Spec: /specs/002-batch-ingestion-adapters/spec.md
Summary: Implement nine BatchAdapter[C] adapters (file, S3, Azure Blob, GCS, remote link, MySQL, REDCap, REST, GraphQL) plus two stubs, shared retry/backoff via tenacity, unit conversion helpers, contract+unit+integration tests, Docker Compose for cloud emulators, and three-tier GitHub Actions CI workflow.
Rationale: Project Lullaby requires a source-agnostic ingestion layer (P4) that normalises every data source into one canonical time-series schema, fails loudly on partial loads, and is testable without live cloud accounts.
Impact:
  - Broke/Changed requirements: no
  - Docs/Constitution changes: none; plan, research, data-model, contracts, quickstart, tasks added under specs/002-batch-ingestion-adapters/
Targets:
  - src/ingestion/adapters/base.py | +165 -0
  - src/ingestion/adapters/file_adapter.py | +80 -0
  - src/ingestion/adapters/s3_adapter.py | +68 -0
  - src/ingestion/adapters/azure_adapter.py | +72 -0
  - src/ingestion/adapters/gcs_adapter.py | +62 -0
  - src/ingestion/adapters/remote_link_adapter.py | +83 -0
  - src/ingestion/adapters/mysql_adapter.py | +60 -0
  - src/ingestion/adapters/redcap_adapter.py | +80 -0
  - src/ingestion/adapters/rest_adapter.py | +72 -0
  - src/ingestion/adapters/graphql_adapter.py | +86 -0
  - src/ingestion/adapters/stubs.py | +45 -0
  - src/ingestion/units.py | +35 -0
  - tests/contract/test_adapter_contract.py | +90 -0
  - tests/unit/test_adapters_unit.py | +115 -0
  - tests/integration/test_adapters_local.py | +90 -0
  - docker-compose.yml | +46 -0
  - pyproject.toml | +32 -0
  - .github/workflows/test-adapters.yml | +50 -0
  - specs/002-batch-ingestion-adapters/ | +7 -0

Date: 2026-06-01
Spec: /specs/001-canonical-schema-validation/spec.md
Summary: Implement canonical time-series schema ABC, LullabySchema for five tables, Pandera validation engine, ingestion pipeline, and CI gate.
Rationale: Project Lullaby requires a schema-first data contract so ingestion boundaries enforce correctness, informative missingness is preserved without imputation, and alternate schemas can be injected at runtime without code changes.
Impact:
  - Broke/Changed requirements: no
  - Docs/Constitution changes: added schemas/data-dictionary.md as authoritative column reference (FR-005)
Targets:
  - src/schemas/base.py | +48 -0
  - src/schemas/lullaby.py | +184 -0
  - src/schemas/registry.py | +43 -0
  - src/validation/pandera_models.py | +14 -0
  - src/validation/engine.py | +34 -0
  - src/ingestion/pipeline.py | +66 -0
  - src/ingestion/adapters/csv_adapter.py | +14 -0
  - src/cli/validate_schema.py | +65 -0
  - .github/workflows/validate-schema.yml | +34 -0
  - schemas/data-dictionary.md | +103 -0
  - data/synthetic/ | +5 -0
  - tests/unit/test_lullaby_schema.py | +69 -0
  - tests/unit/test_pandera_models.py | +78 -0
  - tests/contract/test_schema_interface.py | +44 -0
  - tests/contract/test_validation_contract.py | +70 -0
  - tests/integration/test_ingestion_validation_pipeline.py | +88 -0
  - tests/conftest.py | +42 -0
  - specs/001-canonical-schema-validation/tasks.md | +204 -0

Date: 2026-06-01
Spec: /specs/000-changelog-creation/spec.md
Summary: Add merge-gating changelog policy and validator to enforce per-spec provenance.
Rationale: Ensure every implemented spec produces a single, machine-parseable changelog entry for traceability and CI enforcement.
Impact:
  - Broke/Changed requirements: no
  - Docs/Constitution changes: added changelog policy and validator
Targets:
  - specs/000-changelog-creation/spec.md | +12 -0
  - tools/changelog_validator.py | +650 -0
  - .github/workflows/changelog-policy.yml | +120 -0
