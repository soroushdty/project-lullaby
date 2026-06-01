---
id:            PLAN-002-RESEARCH
title:         Research Notes - Batch Ingestion Adapters
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

# Research

## Decision: Generic ABC `BatchAdapter(Generic[C])` with `load(config: C)`
Rationale: Preserves type safety across all nine concrete adapter subclasses without Liskov violation. Each adapter declares `class XAdapter(BatchAdapter[XConfig])`, allowing mypy/pyright to verify config field access per adapter.
Alternatives considered: Base-typed `load(config: AdapterConfig)` with internal casts (type-unsafe, requires `isinstance` guards throughout); no config on ABC, config passed to `__init__` (hides the contract, makes ABC harder to test generically).

## Decision: `requests` for all HTTP adapters (REST, GraphQL, remote-link, REDCap)
Rationale: Synchronous batch loads gain nothing from async; `requests` is simpler, more widely understood, and natively supported by `pytest-httpserver` for mocking. All four HTTP-based adapters share the same session management and retry wrapper.
Alternatives considered: `httpx` (async overhead, no benefit for batch); `aiohttp` (same objection, plus breaks synchronous pipeline).

## Decision: Direct `requests` calls to REDCap Data Export API (no `pycap`)
Rationale: The REDCap export API is a single POST endpoint; `pycap` adds a dependency for a trivial HTTP call and obscures the retry/error-handling logic. Direct calls keep the adapter transparent and dependency-light.
Alternatives considered: `pycap` library (hides API details, harder to intercept for fixture-based testing).

## Decision: `tenacity` for retry/backoff across all adapters
Rationale: `tenacity` natively supports: exponential backoff with jitter, per-exception retry conditions (retry 5xx, skip auth errors), and `wait_fixed` for 429 `Retry-After` delays. Avoids rolling custom retry logic in nine separate adapters.
Alternatives considered: Custom `retry` decorator (duplicated logic, harder to audit); `urllib3.util.retry` (HTTP-only, can't wrap cloud SDK calls uniformly).

## Decision: `pydantic` v2 for all `AdapterConfig` subclasses
Rationale: NFR-002 explicitly names Pydantic; v2 gives field validation, secret masking via `SecretStr`, and serialization for free. `SecretStr` fields prevent accidental logging of tokens/connection strings (NFR-003).
Alternatives considered: stdlib `dataclasses` (no validation, no secret masking); `attrs` (similar to dataclasses, no Pydantic ecosystem benefits).

## Decision: `pydantic.SecretStr` for all credential fields in config models
Rationale: `SecretStr.__repr__` emits `'**********'`, preventing credential leakage in tracebacks, log lines, and test output. Satisfies NFR-003 at the config layer without manual sanitization in every adapter.
Alternatives considered: Manual scrubbing in `except` blocks (error-prone, easy to miss new fields).

## Decision: Docker Compose for cloud emulators; `docker-compose.ci.yml` override for pinned CI images
Rationale: All three cloud emulators (MinIO, Azurite, fake-gcs-server) have official Docker images; Compose is already a project-level tool. Separate `ci.yml` override pins image digests to prevent CI flakiness from upstream tag changes.
Emulator images:
- S3/MinIO: `minio/minio:latest` (local) / pinned digest (CI)
- Azure Blob: `mcr.microsoft.com/azure-storage/azurite:latest`
- GCS: `fsouza/fake-gcs-server:latest`
- MySQL: `mysql:8.0`
- Local HTTP (remote-link): `pytest-httpserver` in-process (no container needed)
Alternatives considered: LocalStack for all AWS (heavier, slower startup); separate shell scripts (less reproducible than Compose).

## Decision: `pytest-httpserver` for REST, GraphQL, and remote-link mocking (tier 1)
Rationale: In-process HTTP server that starts/stops per test — no Docker container, no port conflicts, works in tier-1 (no-emulators) CI. Supports response sequences for pagination testing.
Alternatives considered: `responses` library (mocks at the `requests` layer, not a real HTTP server — can't test network-level behaviors); `wiremock` (Java process, heavy for Python CI).

## Decision: REDCap fixtures as recorded JSON files under `tests/fixtures/redcap/`
Rationale: REDCap live API access is not available in CI. Recorded responses let tests validate the full parsing/flattening path without a live server. Fixtures are committed and versioned.
Alternatives considered: Live REDCap sandbox (not available; requires account); `responses` mock (loses the real HTTP round-trip; fixture files are more transparent).

## Decision: Primary key dedup driven by `LullabySchema` schema object (not hardcoded)
Rationale: P3 (Schema-Driven Extensibility) — hardcoding `participant_id` or composite keys in adapters would break for any non-default schema subclass. Adapters call `schema.primary_keys(table_name)` at runtime.
Alternatives considered: Hardcoded per-table key columns in `base.py` (breaks P3, couples adapter layer to the default schema).

## Decision: 429 handling outside `tenacity` retry count via `Retry-After` header
Rationale: A 429 is not a transient failure — it is an explicit instruction to wait. Consuming a `max_attempts` slot on 429 would exhaust retries before the API is ready. Instead, the adapter intercepts 429 before `tenacity` sees it, sleeps for `Retry-After` seconds (default 60 s if header absent), and re-raises the request for `tenacity` to retry as normal.
Alternatives considered: Treat 429 as 5xx (burns retry budget; likely to exhaust before window clears); raise `ConnectorError` immediately on 429 (too aggressive; most APIs recover after the declared wait).
