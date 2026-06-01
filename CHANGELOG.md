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

## Changelog Entry: SPEC-003

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

## Changelog Entry: SPEC-002

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
  - specs/002-batch-ingestion-adapters/ | +7 docs (plan, research, data-model, quickstart, 4 contracts, tasks)

## Changelog Entry: 001-canonical-schema-validation

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
  - data/synthetic/ | +5 files (canonical CSVs)
  - tests/unit/test_lullaby_schema.py | +69 -0
  - tests/unit/test_pandera_models.py | +78 -0
  - tests/contract/test_schema_interface.py | +44 -0
  - tests/contract/test_validation_contract.py | +70 -0
  - tests/integration/test_ingestion_validation_pipeline.py | +88 -0
  - tests/conftest.py | +42 -0
  - specs/001-canonical-schema-validation/tasks.md | +204 -0

## Changelog Entry: 000-changelog-creation

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
