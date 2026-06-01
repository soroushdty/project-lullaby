---
id: SPEC-002
title: Batch Ingestion Adapters
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-001]
implements: [P4, P5]
supersedes: null
superseded_by: null
related: [SPEC-001]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Feature Specification: Batch Ingestion Adapters

**Feature Branch**: `002-batch-ingestion-adapters`

**Created**: 2026-06-01

**Status**: Draft

**Input**: User description: "SPEC-002 · Batch Ingestion Adapters"

## Clarifications

### Session 2026-06-01

- Q: Where are primary keys for per-table deduplication defined? → A: In the SPEC-001 data dictionary (`schemas/data-dictionary.md`); adapters read dedup keys from the schema object at runtime — no keys hardcoded in adapter logic.
- Q: What is the `load()` type signature on the ABC to preserve type safety across adapter subclasses? → A: Generic ABC — `class BatchAdapter(Generic[C])` with `load(config: C) -> dict[str, pd.DataFrame]`; each concrete adapter is `BatchAdapter[XConfig]`.
- Q: How should HTTP 429 (rate-limit) responses be handled by API adapters? → A: Respect `Retry-After` header, pause for the specified duration, and retry without consuming a `max_attempts` slot.
- Q: Does the remote link adapter need to handle Google Drive OAuth, or only direct-download URLs? → A: Direct-download URLs only (no OAuth). Google Drive "anyone with link" exports produce a plain HTTPS URL; the adapter is a simple authenticated-free HTTPS fetcher.
- Q: What must adapters log? → A: INFO on load start and end (adapter name, table count, row counts per table); ERROR on each raised exception (exception type, adapter name, sanitized message — no secrets, tokens, connection strings, or file paths containing credentials).
- Q: What is the common interface all adapters must implement? -> A: A `BatchAdapter` ABC with a single `load() -> dict[str, pd.DataFrame]` method that returns frames keyed by canonical table name, ready for the SPEC-001 validation engine.
- Q: How does normalization work — do adapters map raw columns to canonical names, or does a separate layer do that? -> A: Each adapter is responsible for emitting canonical-column DataFrames; column mapping is adapter-internal. The output contract is the LullabySchema canonical shape.
- Q: What does idempotency mean for re-uploads — last-write-wins or deduplicate-by-key? -> A: Re-running the same upload/ingest produces the same canonical output without error; duplicate rows are deduplicated by primary key before handing off to validation. No side effects on repeated runs.
- Q: How should unit mismatches (lb/kg, °F/°C) be handled? -> A: Units must be declared in adapter config or detected from source metadata. Silent coercion is forbidden. If the unit cannot be determined, the adapter raises a `UnitAmbiguityError` with the column and source value.
- Q: Are the interface-only adapters (Dropbox/OneDrive, generic fallback) stubs with documented contracts or fully absent? -> A: Documented ABC stubs with `NotImplementedError` and interface contracts in `contracts/`, but no executable implementation.
- Q: What is the canonical output store — files, a database, or in-memory frames for downstream validation? -> A: Adapters return in-memory `dict[str, pd.DataFrame]` matching the LullabySchema canonical tables; persistence is handled downstream by the pipeline from SPEC-001.
- Q: For the REDCap adapter, is the API token provided per-run or per-environment? -> A: Per-environment via environment variable (`REDCAP_TOKEN`). The adapter reads it at instantiation and raises `AuthConfigError` if absent.
- Q: For REST and GraphQL adapters, are the endpoint and query configurable per-run or hardcoded? -> A: Fully configurable via an adapter config object (URL, headers, query string/document). No hardcoded endpoints.
- Q: What retry policy applies to connector outages? -> A: Exponential backoff with a configurable max-attempts (default 3). If all retries fail, raise `ConnectorError` with the original cause; do not return partial data.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — File Upload Adapter: CSV and XLSX (Priority: P1)

A data coordinator uploads a CSV or XLSX file containing historical cohort data. The adapter normalizes it to canonical tables and hands it off to validation.

**Why this priority**: Lowest-barrier path; covers the broadest user population; required for local-no-accounts CI tier.

**Independent Test**: Run the file adapter against the bundled synthetic cohort in CSV and XLSX formats; output frames match canonical shape and pass LullabySchema validation.

**Acceptance Scenarios**:
1. Given a valid synthetic cohort CSV, when the file adapter runs, then all five canonical tables are returned as correctly typed DataFrames.
2. Given a valid XLSX workbook with one sheet per table, when the file adapter runs, then all five canonical tables are returned.
3. Given a CSV with a missing required column, when the adapter runs, then a `SchemaMismatchError` is raised naming the table and missing column.
4. Given a file with an unsupported extension (e.g. `.json`, `.parquet`), when the adapter runs, then a `UnsupportedFormatError` is raised before any data is read.
5. Given a CSV with wrong encoding (e.g. latin-1 when UTF-8 is expected), when the adapter runs, then an `EncodingError` is raised at the boundary.
6. Given a re-upload of the same CSV, when the adapter runs again, then the output is identical and no error is raised (idempotent).

---

### User Story 2 — Cloud Storage Adapters: S3, Azure Blob, GCS (Priority: P2)

A data engineer points the ingestion pipeline at a cloud bucket path. The adapter downloads the relevant files and normalizes them.

**Why this priority**: Required for production data pipelines; tested with local emulators (no cloud accounts needed in CI).

**Independent Test**: Run each cloud adapter against a local emulator (MinIO for S3, Azurite for Azure, fake-gcs-server for GCS) seeded with the synthetic cohort; output matches canonical shape.

**Acceptance Scenarios**:
1. Given a MinIO bucket seeded with valid synthetic CSVs, when the S3 adapter runs, then canonical frames are returned.
2. Given an Azurite container seeded with valid data, when the Azure Blob adapter runs, then canonical frames are returned.
3. Given a fake-gcs-server bucket seeded with valid data, when the GCS adapter runs, then canonical frames are returned.
4. Given an auth failure (wrong credentials), when any cloud adapter runs, then a `ConnectorError` is raised immediately — no partial data, no retry of a non-retryable auth error.
5. Given a transient network error, when a cloud adapter runs, then it retries up to `max_attempts` times with exponential backoff before raising `ConnectorError`.
6. Given a bucket path with mixed file types, when the adapter runs, then only supported formats are loaded; unsupported files are logged and skipped, not silently included.

---

### User Story 3 — Remote Link Adapter: Google Drive (Priority: P2)

A clinician shares a Google Drive link to a data export. The adapter fetches and normalizes it without requiring the clinician to install anything.

**Why this priority**: Key user-facing path; tested with a local HTTP file server to avoid OAuth in CI.

**Independent Test**: Run the remote link adapter against a local HTTP server serving the synthetic cohort file; output matches canonical shape.

**Acceptance Scenarios**:
1. Given a publicly accessible HTTP URL serving a valid CSV, when the adapter runs, then canonical frames are returned.
2. Given a URL that returns a 404, when the adapter runs, then a `ConnectorError` is raised with the URL and status code.
3. Given a URL serving an unsupported content type, when the adapter runs, then an `UnsupportedFormatError` is raised at the boundary.

---

### User Story 4 — Database Adapter: MySQL (Priority: P2)

A data engineer connects the adapter to a MySQL database containing historical records. The adapter queries canonical tables by name and returns them.

**Why this priority**: Covers structured data sources; tested against a local MySQL instance in CI (no external accounts).

**Independent Test**: Run the MySQL adapter against a local MySQL instance seeded with the synthetic cohort schema and data; output matches canonical shape.

**Acceptance Scenarios**:
1. Given a local MySQL instance with canonical tables populated, when the adapter runs, then all five canonical frames are returned.
2. Given a MySQL table missing a required column, when the adapter runs, then a `SchemaMismatchError` is raised naming the table and column.
3. Given a bad connection string, when the adapter runs, then a `ConnectorError` is raised before any data is read.

---

### User Story 5 — API Adapters: REDCap, REST, GraphQL (Priority: P3)

A research coordinator pulls data from a REDCap project or a REST/GraphQL API endpoint. The adapter authenticates, pages through results, and normalizes the response.

**Why this priority**: Highest integration complexity; REDCap is tested with recorded fixtures; REST and GraphQL with local mock servers.

**Independent Test**: Run each API adapter against a mock server or recorded fixture; output matches canonical shape.

**Acceptance Scenarios**:
1. Given a mock REDCap export fixture, when the REDCap adapter runs, then canonical frames are returned matching the fixture's rows.
2. Given a missing `REDCAP_TOKEN` env var, when the REDCap adapter is instantiated, then an `AuthConfigError` is raised immediately.
3. Given a configured REST endpoint serving JSON, when the REST adapter runs, then canonical frames are returned.
4. Given a configured GraphQL endpoint, when the GraphQL adapter runs with a query document, then canonical frames are returned.
5. Given an API that returns a 5xx error, when any API adapter runs, then it retries with exponential backoff and raises `ConnectorError` on exhaustion.

---

### User Story 6 — Resilience: No Partial Commits, Actionable Errors (Priority: P5)

Any adapter failure produces an actionable error and no partial output is accepted downstream.

**Why this priority**: Core safety property — partial ingestion would corrupt the canonical store silently.

**Independent Test**: Inject failures at various stages (mid-load, auth, schema); confirm no partial frames are returned and the error payload is actionable.

**Acceptance Scenarios**:
1. Given a CSV that is valid for three tables and invalid for two, when the file adapter runs, then no frames are returned and the error names all failing tables.
2. Given a temperature column sourced in Fahrenheit with no unit declaration, when any adapter runs, then a `UnitAmbiguityError` is raised naming the column.
3. Given a temperature column declared as Fahrenheit, when the adapter runs, then the value is converted to Celsius and flagged in the report — not silently coerced.

---

### Edge Cases
- Source file with BOM (byte-order mark) in UTF-8 must be handled without error.
- Empty tables (zero data rows but valid headers) must be accepted and returned as empty DataFrames — not rejected.
- Cloud blobs with key prefixes (subdirectories) must be traversed to find matching CSV/XLSX files.
- GraphQL introspection must not be required; the adapter must work with a supplied query document only.
- HTTP 429 with a `Retry-After` header must pause for the declared interval and retry without counting against `max_attempts`; if `Retry-After` is absent, fall back to a configurable default wait (default: 60 s).
- REDCap exports with repeated instruments must be flattened to row-per-event before canonical mapping.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: ALL adapters MUST implement `BatchAdapter[C]`, a generic ABC (`class BatchAdapter(Generic[C])`) with a single `load(config: C) -> dict[str, pd.DataFrame]` method, where `C` is bound to `AdapterConfig`. Each concrete adapter declares its own config type (e.g. `class S3Adapter(BatchAdapter[S3Config])`).
- **FR-002**: The file upload adapter MUST support CSV (UTF-8, UTF-8-BOM) and XLSX (one sheet per canonical table name).
- **FR-003**: The remote link adapter MUST support publicly accessible HTTP/HTTPS URLs returning supported file types; Google Drive "anyone with link" direct-download exports are the primary target. OAuth is explicitly out of scope — if a URL redirects to an auth/login page, the adapter MUST raise `ConnectorError` with a message indicating authentication is required.
- **FR-004**: The AWS S3 adapter MUST authenticate via standard boto3 credential chain and support path-style and virtual-hosted-style bucket URLs.
- **FR-005**: The Azure Blob adapter MUST authenticate via connection string or `DefaultAzureCredential` and support container/blob prefix paths.
- **FR-006**: The GCS adapter MUST authenticate via Application Default Credentials and support `gs://` URIs.
- **FR-007**: The MySQL adapter MUST connect via a SQLAlchemy connection string and query each canonical table by name.
- **FR-008**: The REDCap adapter MUST authenticate via `REDCAP_TOKEN` env var, call the REDCap Data Export API, and flatten repeated instruments to row-per-event.
- **FR-009**: The REST API adapter MUST accept a configurable URL, HTTP method, and headers; it MUST paginate until no next-page token is returned.
- **FR-010**: The GraphQL adapter MUST accept a configurable endpoint URL, headers, and query document string; it MUST handle paginated cursors.
- **FR-011**: Dropbox/OneDrive share-link and generic fallback adapters MUST be defined as `BatchAdapter` stubs with `NotImplementedError` and documented interface contracts in `contracts/`.
- **FR-012**: Any adapter detecting a schema mismatch (renamed or missing required column) MUST raise `SchemaMismatchError` naming the table, expected column, and found columns — before returning any data.
- **FR-013**: Partial loads are forbidden: if any table fails, the adapter MUST raise and return no frames.
- **FR-014**: Connector outages and auth failures MUST be surfaced as `ConnectorError` or `AuthConfigError` respectively; adapters MUST retry transient errors (5xx, network timeouts) with exponential backoff (configurable `max_attempts`, default 3); auth failures MUST NOT be retried. HTTP 429 responses MUST be handled separately: the adapter MUST pause for the duration specified in the `Retry-After` response header (or a configurable default if the header is absent) and retry WITHOUT consuming a `max_attempts` slot.
- **FR-015**: Unsupported file types and encoding errors MUST be caught at the read boundary and raised as `UnsupportedFormatError` or `EncodingError` before any parsing proceeds.
- **FR-016**: Unit mismatches MUST be detected or declared via adapter config; silent coercion is forbidden. Known mismatches (e.g. °F → °C) MUST be converted and flagged. Unknown mismatches MUST raise `UnitAmbiguityError`.
- **FR-017**: Re-running any adapter with the same source and config MUST produce identical output (idempotent); duplicate rows MUST be deduplicated by primary key before validation hand-off. Primary keys are read from the SPEC-001 `LullabySchema` data dictionary at runtime (`schemas/data-dictionary.md`) — adapters MUST NOT hardcode key column names.
- **FR-018**: All adapter outputs MUST be validated by the SPEC-001 engine before acceptance; adapters do not bypass validation.
- **FR-019**: CI MUST run all adapters across three testability tiers: local-no-accounts (file, MySQL, REST/GraphQL mock), local-emulator (MinIO/LocalStack, Azurite, fake-gcs-server, local HTTP), and recorded fixtures (REDCap).

### Non-Functional Requirements
- **NFR-001**: Each adapter is a standalone Python class; no adapter imports from another adapter.
- **NFR-002**: Adapter config is a typed dataclass or Pydantic model — no untyped dicts as public API.
- **NFR-003**: Secrets (tokens, connection strings) are read from environment variables; they MUST NOT appear in logs or error messages.
- **NFR-004**: Every adapter MUST emit structured log lines using the standard `logging` module: INFO at load start (`adapter=X starting load`) and load end (`adapter=X loaded N tables, row counts: {table: N, ...}`); ERROR on each raised exception (`adapter=X raised ExceptionType: <sanitized message>`). Sanitized messages MUST strip any secret values, connection string components, and file paths that could contain credentials before logging.

---

## Key Entities

- **BatchAdapter**: Generic ABC `BatchAdapter(Generic[C])` with `load(config: C) -> dict[str, pd.DataFrame]`. Each of the nine adapters is a concrete `BatchAdapter[XConfig]` subclass.
- **AdapterConfig**: Typed base config; each adapter subclasses with its own fields (path, URL, credentials ref, unit declarations).
- **SchemaMismatchError**: Raised when source columns don't match canonical requirements. Fields: `table`, `missing_columns`, `found_columns`.
- **ConnectorError**: Raised on network/cloud outage after max retries. Fields: `adapter`, `cause`, `attempts`.
- **AuthConfigError**: Raised on missing or invalid credentials. Fields: `adapter`, `credential_env_var`.
- **UnsupportedFormatError**: Raised on unrecognized file type or MIME type. Fields: `adapter`, `detected_type`.
- **EncodingError**: Raised when file encoding cannot be decoded. Fields: `adapter`, `path`, `detected_encoding`.
- **UnitAmbiguityError**: Raised when a unit-sensitive column has no declared or detectable unit. Fields: `column`, `sample_value`.

---

## Success Criteria *(mandatory)*

- **SC-001**: All nine built adapters load the bundled synthetic cohort into identical canonical frames that pass LullabySchema validation.
- **SC-002**: All three CI testability tiers execute without cloud accounts or live external services.
- **SC-003**: Every defined failure mode (schema mismatch, auth failure, connector outage, wrong format, encoding error, unit ambiguity) raises the correct typed exception with an actionable message — verified by test.
- **SC-004**: Re-running any adapter twice against the same source produces the same output and no error (idempotency verified by test).
- **SC-005**: No secrets appear in logs, tracebacks, or error message strings (verified by log-scrubbing test fixture).
- **SC-006**: Dropbox/OneDrive and generic fallback stubs have documented interface contracts and raise `NotImplementedError` on `load()`.

---

## Assumptions

- SPEC-001 `LullabySchema` and `ValidationEngine` are stable and available as the validation boundary.
- Cloud emulator images (MinIO, Azurite, fake-gcs-server) are available via Docker Compose for local and CI runs.
- REDCap API structure is fixed for the bundled synthetic cohort export; live REDCap access is not required for CI.
- Source data for all adapters is assumed to be the same five canonical tables (participants, daily_vitals, alerts, clinical_outcomes, staff_contacts) or a subset thereof.
- Unit declaration is opt-in via `AdapterConfig`; adapters for sources with consistent units (e.g. internal MySQL) may declare units statically in config.

---

## Implementation Notes

- Place adapter implementations under `src/ingestion/adapters/` as separate modules: `file_adapter.py`, `s3_adapter.py`, `azure_adapter.py`, `gcs_adapter.py`, `remote_link_adapter.py`, `mysql_adapter.py`, `redcap_adapter.py`, `rest_adapter.py`, `graphql_adapter.py`.
- Place the `BatchAdapter` ABC and all custom exception types in `src/ingestion/adapters/base.py`.
- Place stub adapters (Dropbox/OneDrive, generic fallback) in `src/ingestion/adapters/stubs.py`.
- Place unit conversion helpers in `src/ingestion/units.py`.
- Use `docker-compose.yml` at project root for local emulators; a `docker-compose.ci.yml` override for CI pinned images.
- REDCap fixture responses live in `tests/fixtures/redcap/`.
- REST and GraphQL mock servers use `pytest-httpserver` or equivalent; no external process required.

---

## Acceptance Tests

- Add CI job `test-adapters-local` (no emulators) covering file, MySQL, REST mock, GraphQL mock.
- Add CI job `test-adapters-emulated` (Docker Compose) covering S3/MinIO, Azure/Azurite, GCS/fake-gcs-server, remote-link/local-HTTP.
- Add CI job `test-adapters-fixtures` covering REDCap recorded fixtures.
- Each job asserts all loaded frames pass `engine.validate(schema, frames)` with exit code 0.
