---
id:            PLAN-002-TASKS
title:         Tasks - Batch Ingestion Adapters
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-002, SPEC-001]
implements:    [P4, P5]
supersedes:    null
superseded_by: null
related:       [PLAN-002]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Tasks: Batch Ingestion Adapters (SPEC-002)

**Input**: Design documents from `specs/002-batch-ingestion-adapters/`

**Prerequisites**: plan.md ✓ · spec.md ✓ · research.md ✓ · data-model.md ✓ · contracts/ ✓ · quickstart.md ✓

**Note**: Test tasks are included per spec acceptance criteria and CI testability tier requirements (FR-019, SC-001–SC-006).

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (independent files, no incomplete dependencies)
- **[Story]**: User story this task belongs to (US1–US6)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Directory layout, dependencies, Docker Compose for cloud emulators.

- [x] T001 Create directory structure: `src/ingestion/adapters/`, `tests/unit/`, `tests/contract/`, `tests/integration/`, `tests/fixtures/redcap/` per plan.md
- [x] T002 Add production dependencies to `pyproject.toml` or `requirements.txt`: `pandas`, `openpyxl`, `boto3`, `azure-storage-blob`, `google-cloud-storage`, `sqlalchemy`, `pymysql`, `requests`, `tenacity`, `pydantic>=2`
- [x] T003 [P] Add dev/test dependencies: `pytest`, `pytest-httpserver`
- [x] T004 [P] Create `docker-compose.yml` with MinIO, Azurite, fake-gcs-server, and MySQL 8.0 services; create `docker-compose.ci.yml` override with pinned image digests

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared ABC, config base, exception hierarchy, retry wrapper, and unit helpers that all adapters depend on. No adapter can be implemented until this phase is complete.

**⚠️ CRITICAL**: Phases 3–8 depend on this phase being fully complete.

- [x] T005 Define `BatchAdapterError(RuntimeError)` and all six exception subclasses (`SchemaMismatchError`, `ConnectorError`, `AuthConfigError`, `UnsupportedFormatError`, `EncodingError`, `UnitAmbiguityError`) with typed fields per `contracts/error-taxonomy.md` in `src/ingestion/adapters/base.py`
- [x] T006 Define `AdapterConfig` Pydantic v2 base model (`max_attempts`, `rate_limit_default_wait_s`) and all nine concrete config subclasses per `contracts/adapter-config-schema.md` in `src/ingestion/adapters/base.py`
- [x] T007 Define `BatchAdapter(ABC, Generic[C])` with abstract `load(config: C) -> dict[str, pd.DataFrame]` and shared INFO/ERROR logging contract (NFR-004) in `src/ingestion/adapters/base.py`
- [x] T008 Implement `tenacity`-based retry wrapper in `src/ingestion/adapters/base.py`: exponential backoff for 5xx/network, 429 `Retry-After` handling (no slot consumed), immediate raise for 401/403 and non-retryable 4xx
- [x] T009 [P] Implement `DropboxAdapter`, `OneDriveAdapter`, `GenericFallbackAdapter` stubs (raise `NotImplementedError`, fully typed configs) in `src/ingestion/adapters/stubs.py`
- [x] T010 [P] Implement unit conversion helpers (`fahrenheit_to_celsius`, `lbs_to_kg`) and `UnitAmbiguityError` raising logic in `src/ingestion/units.py`
- [x] T011 [P] Write contract test: verify all nine concrete adapter classes and three stubs satisfy the `BatchAdapter[C]` ABC contract; verify all exception types have required fields; verify `SecretStr` fields render masked in `repr()` — in `tests/contract/test_adapter_contract.py`

**Checkpoint**: Foundation complete — all adapter phases can now begin.

---

## Phase 3: User Story 1 — File Upload Adapter: CSV and XLSX (Priority: P1) 🎯 MVP

**Goal**: Data coordinator uploads a CSV or XLSX file; adapter returns all five canonical tables as correctly typed DataFrames passing LullabySchema validation.

**Independent Test**: `pytest tests/integration/test_adapters_local.py -k file` against bundled synthetic cohort — all five tables returned, all pass `ValidationEngine.validate()`, exit 0.

- [x] T012 [US1] Implement `FileAdapter(BatchAdapter[FileAdapterConfig]).load()` with CSV support (UTF-8 and UTF-8-BOM via `pd.read_csv`) in `src/ingestion/adapters/file_adapter.py`
- [x] T013 [US1] Add XLSX support (one sheet per canonical table name via `pd.read_excel`) to `FileAdapter.load()` in `src/ingestion/adapters/file_adapter.py`
- [x] T014 [US1] Add boundary guards: raise `UnsupportedFormatError` for unsupported extensions before any read; raise `EncodingError` on decode failure in `src/ingestion/adapters/file_adapter.py`
- [x] T015 [US1] Add schema-driven dedup via `LullabySchema.primary_keys(table_name)` and `DataFrame.drop_duplicates(subset=keys, keep="last")` in `src/ingestion/adapters/file_adapter.py`
- [x] T016 [US1] Write integration test for `FileAdapter`: valid CSV (all 5 tables), valid XLSX, missing-column CSV, unsupported extension, wrong encoding, re-upload idempotency — in `tests/integration/test_adapters_local.py`

**Checkpoint**: `FileAdapter` loads synthetic cohort, passes validation, handles all 6 acceptance scenarios — independently verifiable.

---

## Phase 4: User Story 2 — Cloud Storage Adapters: S3, Azure Blob, GCS (Priority: P2)

**Goal**: Data engineer points adapter at a cloud bucket; adapter downloads and returns canonical frames.

**Independent Test**: `docker compose up -d --wait && pytest tests/integration/test_adapters_emulated.py -k "s3 or azure or gcs"` — all three cloud adapters return frames passing validation against their respective local emulators.

- [x] T017 [P] [US2] Implement `S3Adapter(BatchAdapter[S3AdapterConfig]).load()` via `boto3` (path-style + virtual-hosted-style, credential chain, prefix traversal) in `src/ingestion/adapters/s3_adapter.py`
- [x] T018 [P] [US2] Implement `AzureAdapter(BatchAdapter[AzureAdapterConfig]).load()` via `azure-storage-blob` (`connection_string` or `DefaultAzureCredential`, container/prefix traversal) in `src/ingestion/adapters/azure_adapter.py`
- [x] T019 [P] [US2] Implement `GCSAdapter(BatchAdapter[GCSAdapterConfig]).load()` via `google-cloud-storage` (ADC, `gs://` URI, prefix traversal) in `src/ingestion/adapters/gcs_adapter.py`
- [ ] T020 [US2] Write emulated integration tests: S3/MinIO seeded with synthetic CSVs, Azure/Azurite seeded, GCS/fake-gcs seeded; auth-failure, transient-network-retry, mixed-file-types scenarios per US2 acceptance criteria — in `tests/integration/test_adapters_emulated.py`

**Checkpoint**: All three cloud adapters verified against local emulators without cloud accounts.

---

## Phase 5: User Story 3 — Remote Link Adapter: Google Drive / HTTP (Priority: P2)

**Goal**: Clinician shares a direct-download HTTP/HTTPS URL; adapter fetches and returns canonical frames.

**Independent Test**: `pytest tests/integration/test_adapters_emulated.py -k remote_link` against `pytest-httpserver` — valid CSV URL returns frames; 404 raises `ConnectorError`; login-redirect raises `ConnectorError`; unsupported MIME raises `UnsupportedFormatError`.

- [x] T021 [US3] Implement `RemoteLinkAdapter(BatchAdapter[RemoteLinkAdapterConfig]).load()` using `requests.get` with `timeout` in `src/ingestion/adapters/remote_link_adapter.py`
- [x] T022 [US3] Add login-redirect detection: if response `Content-Type` is `text/html` or `Location` header points to an auth endpoint, raise `ConnectorError` with message "Authentication required — direct-download URL expected" in `src/ingestion/adapters/remote_link_adapter.py`
- [x] T023 [US3] Write integration tests for `RemoteLinkAdapter` against `pytest-httpserver`: valid CSV, 404, login-redirect, unsupported content-type — in `tests/integration/test_adapters_emulated.py`

**Checkpoint**: Remote link adapter handles all 3 acceptance scenarios without OAuth.

---

## Phase 6: User Story 4 — Database Adapter: MySQL (Priority: P2)

**Goal**: Data engineer connects adapter to a MySQL instance; adapter queries canonical tables and returns frames.

**Independent Test**: `pytest tests/integration/test_adapters_local.py -k mysql` against Docker Compose MySQL seeded with synthetic schema — all five canonical tables returned and validated.

- [x] T024 [US4] Implement `MySQLAdapter(BatchAdapter[MySQLAdapterConfig]).load()` via SQLAlchemy `create_engine` + `pd.read_sql_table` for each canonical table name in `src/ingestion/adapters/mysql_adapter.py`
- [x] T025 [US4] Add `SchemaMismatchError` on missing required column and `ConnectorError` on bad connection string / unreachable host in `src/ingestion/adapters/mysql_adapter.py`
- [ ] T026 [US4] Write integration tests for `MySQLAdapter` against Docker Compose MySQL: all-tables happy path, missing column, bad connection string — in `tests/integration/test_adapters_local.py`

**Checkpoint**: MySQL adapter queries local instance and passes all 3 acceptance scenarios.

---

## Phase 7: User Story 5 — API Adapters: REDCap, REST, GraphQL (Priority: P3)

**Goal**: Research coordinator pulls data from REDCap or REST/GraphQL API; adapter authenticates, paginates, and returns canonical frames.

**Independent Test**: `pytest tests/integration/test_adapters_local.py -k "rest or graphql" && pytest tests/integration/test_adapters_fixtures.py -k redcap` — all three API adapters return validated frames from mocks/fixtures.

- [x] T027 [P] [US5] Implement `REDCapAdapter(BatchAdapter[REDCapAdapterConfig]).load()`: POST to REDCap Data Export API, flatten repeated-instrument rows to row-per-event, raise `AuthConfigError` on missing `REDCAP_TOKEN` — in `src/ingestion/adapters/redcap_adapter.py`
- [x] T028 [P] [US5] Implement `RESTAdapter(BatchAdapter[RESTAdapterConfig]).load()`: configurable URL/method/headers, paginate until no `next_page_field`, 429 `Retry-After` handling via retry wrapper — in `src/ingestion/adapters/rest_adapter.py`
- [x] T029 [P] [US5] Implement `GraphQLAdapter(BatchAdapter[GraphQLAdapterConfig]).load()`: POST query document, paginate via `cursor_field`, 429 handling, no introspection required — in `src/ingestion/adapters/graphql_adapter.py`
- [x] T030 [US5] Write integration tests for `REDCapAdapter` against recorded fixtures in `tests/fixtures/redcap/`: happy path, missing token, 5xx retry — in `tests/integration/test_adapters_fixtures.py`
- [x] T031 [US5] Write integration tests for `RESTAdapter` against `pytest-httpserver`: paginated response, 5xx retry, 429 wait, auth failure — in `tests/integration/test_adapters_local.py`
- [x] T032 [US5] Write integration tests for `GraphQLAdapter` against `pytest-httpserver`: cursor pagination, 5xx retry, 429 wait — in `tests/integration/test_adapters_local.py`

**Checkpoint**: All three API adapters verified without live external services.

---

## Phase 8: User Story 6 — Resilience: No Partial Commits, Actionable Errors (Priority: P5)

**Goal**: Any adapter failure produces an actionable typed exception; no partial frames ever reach the validation boundary.

**Independent Test**: `pytest tests/unit/test_adapters_unit.py` — all partial-load, exception-field, and secret-scrubbing tests pass across all adapters.

- [x] T033 [P] [US6] Write unit tests for partial-load rejection: inject schema failure in table 3 of 5; assert no frames returned and error names all failing tables — in `tests/unit/test_adapters_unit.py`
- [x] T034 [P] [US6] Write unit tests for all exception field contracts: verify `SchemaMismatchError.missing_columns`, `ConnectorError.attempts`, `AuthConfigError.credential_env_var`, etc. contain correct values — in `tests/unit/test_adapters_unit.py`
- [x] T035 [US6] Write secret-scrubbing test: instantiate each config with a fake `SecretStr` token; trigger a logged exception; assert the token value does not appear anywhere in captured log output or exception `str()` — in `tests/unit/test_adapters_unit.py`
- [x] T036 [US6] Write unit tests for `UnitAmbiguityError` (no declared unit) and known-unit coercion (°F → °C flagged in report) in `tests/unit/test_adapters_unit.py`

**Checkpoint**: All resilience invariants verified by test — partial loads impossible, exceptions always actionable, secrets never leaked.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: CI wiring, unit conversion coverage, quickstart smoke test, changelog entry.

- [x] T037 [P] Create `.github/workflows/test-adapters.yml` with three jobs: `test-adapters-local` (tier 1, no Docker), `test-adapters-emulated` (tier 2, Docker Compose), `test-adapters-fixtures` (tier 3, fixtures); each job asserts exit 0 per `contracts/ci-testability-tiers.md`
- [x] T038 [P] Write unit tests for `src/ingestion/units.py`: °F → °C conversion, lb → kg conversion, `UnitAmbiguityError` on unknown unit, declared-unit static config path — in `tests/unit/test_adapters_unit.py`
- [x] T039 Run quickstart.md smoke test locally: tier-1 pytest, tier-2 Docker Compose + pytest, tier-3 pytest; confirm all exit 0
- [x] T040 Add `CHANGELOG.md` entry for SPEC-002 with `Date`, `Spec`, `Summary`, `Rationale`, `Impact`, and `Targets` (per SPEC-000 policy); entry `spec-id` must be `SPEC-002`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — **blocks all adapter phases**
- **Phases 3–8 (User Stories)**: All depend on Phase 2; may proceed in priority order or in parallel
- **Phase 9 (Polish)**: Depends on all desired user story phases being complete

### User Story Dependencies

| Story | Depends On | Can Parallelize With |
|---|---|---|
| US1 — FileAdapter (P1) | Phase 2 | None needed first |
| US2 — Cloud (P2) | Phase 2 | US1, US3, US4 |
| US3 — RemoteLink (P2) | Phase 2 | US1, US2, US4 |
| US4 — MySQL (P2) | Phase 2 | US1, US2, US3 |
| US5 — API (P3) | Phase 2 | After US1 for fixture patterns |
| US6 — Resilience (P5) | Phase 2 | Runs alongside / after each story |

### Within Each User Story

- Config + adapter implementation → integration test → checkpoint validation

---

## Parallel Execution Example: Phase 4 (Cloud Adapters)

```bash
# Three cloud adapter implementations are fully independent:
Task T017: S3Adapter in src/ingestion/adapters/s3_adapter.py
Task T018: AzureAdapter in src/ingestion/adapters/azure_adapter.py
Task T019: GCSAdapter in src/ingestion/adapters/gcs_adapter.py
# Then:
Task T020: All three emulated integration tests
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup)
2. Complete Phase 2 (Foundational) — **blocks everything**
3. Complete Phase 3 (FileAdapter)
4. **STOP and validate**: `pytest tests/integration/test_adapters_local.py -k file` → exit 0
5. Merge or demo if ready

### Incremental Delivery

1. Phase 1 + 2 → Foundation
2. Phase 3 → FileAdapter (MVP) — validate independently
3. Phase 4 → Cloud adapters — validate against emulators
4. Phase 5 → RemoteLink — validate against httpserver
5. Phase 6 → MySQL — validate against local DB
6. Phase 7 → API adapters — validate against mocks/fixtures
7. Phase 8 → Resilience unit tests
8. Phase 9 → CI + changelog

---

## Notes

- `[P]` tasks touch independent files and have no incomplete task dependencies
- Each user story phase is independently testable before moving to the next
- `SecretStr` must be used for all credential config fields — never `str`
- `load()` must never return partial output; raise before returning
- Primary keys for dedup come from `LullabySchema.primary_keys(table_name)` — never hardcoded
- 429 handling is in the shared retry wrapper (T008), not repeated per adapter
