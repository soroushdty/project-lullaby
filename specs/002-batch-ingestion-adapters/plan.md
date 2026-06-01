---
id:            PLAN-002
title:         Batch Ingestion Adapters Implementation Plan
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-002, SPEC-001]
implements:    [P4, P5]
supersedes:    null
superseded_by: null
related:       [SPEC-002, SPEC-001, PLAN-000]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Implementation Plan: Batch Ingestion Adapters

**Branch**: `002-batch-ingestion-adapters` | **Date**: 2026-06-01 | **Spec**: `specs/002-batch-ingestion-adapters/spec.md`

**Input**: Feature specification from `specs/002-batch-ingestion-adapters/spec.md`

## Summary

Implement nine `BatchAdapter[C]` concrete adapters (file, S3, Azure Blob, GCS, remote link,
MySQL, REDCap, REST, GraphQL) plus two documented stubs (Dropbox/OneDrive, generic fallback)
under `src/ingestion/adapters/`. All adapters share a generic ABC, return
`dict[str, pd.DataFrame]` in the LullabySchema canonical shape, deduplicate by schema-defined
primary keys, and hand off to the SPEC-001 validation engine. Resilience (partial-load
rejection, typed exceptions, exponential backoff via `tenacity`, 429 rate-limit handling) is
enforced at the adapter boundary. Three CI testability tiers (local-no-accounts, emulated,
recorded fixtures) cover all adapters without live cloud accounts.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**:
- `pandas` — DataFrame output contract
- `openpyxl` — XLSX reading (via `pd.read_excel`)
- `boto3` — S3 adapter
- `azure-storage-blob` — Azure Blob adapter
- `google-cloud-storage` — GCS adapter
- `sqlalchemy` + `pymysql` — MySQL adapter
- `requests` — HTTP client for REST, GraphQL, remote-link, and REDCap adapters
- `tenacity` — retry/backoff policy (exponential + 429 `Retry-After` support)
- `pydantic` v2 — typed `AdapterConfig` base and all subclasses (NFR-002)
- `pytest` + `pytest-httpserver` — unit/contract/integration tests and REST/GraphQL mocks

**Storage**: Repository files (CSV/XLSX); remote cloud blobs; in-memory DataFrames for hand-off; no local database written by adapters

**Testing**: pytest; three CI tiers — local-no-accounts, Docker Compose emulators, recorded fixtures

**Target Platform**: Linux/macOS + GitHub Actions

**Performance Goals**: Each adapter processes the bundled synthetic cohort (≤10k rows/table) in <30 s locally; CI tier 1 (no emulators) completes in <2 min

**Constraints**: No hardcoded secrets; each adapter is a standalone module (NFR-001); no inter-adapter imports; no network calls in tier-1 CI; partial loads forbidden (FR-013)

**Scale/Scope**: Nine adapters + two stubs; five canonical tables; single-maintainer repo

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **P4 Source-Agnostic Ingestion**: PASS. Every source normalizes to one canonical time-series schema through a uniform `BatchAdapter[C]` layer; batch and real-time are indistinguishable downstream.
- **P5 Resilience / Graceful Degradation**: PASS. Partial loads are rejected; validation is first-class; all failure modes raise typed, actionable exceptions.
- **P1 Specification-Driven Development**: PASS. Plan derives directly from SPEC-002 FR/NFR list and clarified decisions.
- **P3 Schema-Driven Extensibility**: PASS. Dedup keys and canonical table names are read from the SPEC-001 `LullabySchema` schema object at runtime — no hardcoding.
- **Provenance / Traceability**: PASS. All artifacts carry YAML frontmatter with `depends_on: [SPEC-002, SPEC-001]`.

## Project Structure

### Documentation (this feature)

```text
specs/002-batch-ingestion-adapters/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── batch-adapter-interface.md
│   ├── adapter-config-schema.md
│   ├── error-taxonomy.md
│   └── ci-testability-tiers.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
└── ingestion/
    ├── adapters/
    │   ├── base.py              # BatchAdapter[C] ABC, AdapterConfig base, all exception types
    │   ├── file_adapter.py      # CSV + XLSX (FR-002)
    │   ├── s3_adapter.py        # AWS S3 via boto3 (FR-004)
    │   ├── azure_adapter.py     # Azure Blob via azure-storage-blob (FR-005)
    │   ├── gcs_adapter.py       # GCS via google-cloud-storage (FR-006)
    │   ├── remote_link_adapter.py  # HTTP/HTTPS direct-download (FR-003)
    │   ├── mysql_adapter.py     # MySQL via SQLAlchemy (FR-007)
    │   ├── redcap_adapter.py    # REDCap Data Export API (FR-008)
    │   ├── rest_adapter.py      # Generic REST (FR-009)
    │   ├── graphql_adapter.py   # Generic GraphQL (FR-010)
    │   └── stubs.py             # Dropbox/OneDrive + generic fallback stubs (FR-011)
    └── units.py                 # Unit detection, coercion helpers (FR-016)

tests/
├── unit/
│   └── test_adapters_unit.py        # Per-adapter unit tests (mocked I/O)
├── contract/
│   └── test_adapter_contract.py     # ABC interface, exception fields, config validation
└── integration/
    ├── test_adapters_local.py        # Tier 1: file, MySQL, REST mock, GraphQL mock
    ├── test_adapters_emulated.py     # Tier 2: MinIO, Azurite, fake-gcs, local HTTP
    └── test_adapters_fixtures.py     # Tier 3: REDCap recorded fixtures

tests/fixtures/
└── redcap/                      # Recorded REDCap export fixtures (JSON)

docker-compose.yml               # Local emulators: MinIO, Azurite, fake-gcs-server, MySQL
docker-compose.ci.yml            # CI override: pinned image tags

.github/workflows/
└── test-adapters.yml            # Three CI jobs: local, emulated, fixtures
```

**Structure Decision**: Single-project layout extending the existing `src/ingestion/adapters/` directory established by SPEC-001. Each adapter is a standalone module; `base.py` holds the shared ABC, config base, and all exception types. Stubs live in `stubs.py` to keep them visually distinct from built adapters.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| None | N/A | N/A |

## Post-Design Constitution Check

- **P4**: PASS. `BatchAdapter[C]` interface makes every source interchangeable; pipeline downstream is source-unaware.
- **P5**: PASS. `tenacity` retry policy, 429 `Retry-After` handling, typed exception taxonomy, and partial-load rejection enforced at the ABC boundary.
- **P3**: PASS. Schema-driven dedup via `LullabySchema` primary keys; no canonical column names hardcoded in adapter logic.
- **P1**: PASS. Every design decision maps to a SPEC-002 FR/NFR or clarification bullet.
