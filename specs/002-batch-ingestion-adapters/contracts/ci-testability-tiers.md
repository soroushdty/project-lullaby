---
id:            PLAN-002-CONTRACT-004
title:         CI Testability Tiers Contract
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-002]
implements:    [P2, P5]
supersedes:    null
superseded_by: null
related:       [PLAN-002]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# CI Testability Tiers Contract

## Tier 1 — Local / No Accounts (CI job: `test-adapters-local`)

No cloud accounts, no Docker, no external network required.

| Adapter | Test mechanism |
|---|---|
| `FileAdapter` | Bundled synthetic cohort CSV + XLSX in `tests/fixtures/` |
| `MySQLAdapter` | Local MySQL via Docker Compose (allowed in this tier via service container) |
| `RESTAdapter` | `pytest-httpserver` in-process mock |
| `GraphQLAdapter` | `pytest-httpserver` in-process mock |
| Stubs | Import + assert `NotImplementedError` |

## Tier 2 — Emulated (CI job: `test-adapters-emulated`)

Requires Docker Compose. Runs against local service emulators.

| Adapter | Emulator | Docker image |
|---|---|---|
| `S3Adapter` | MinIO | `minio/minio` (pinned digest in `docker-compose.ci.yml`) |
| `AzureAdapter` | Azurite | `mcr.microsoft.com/azure-storage/azurite` (pinned) |
| `GCSAdapter` | fake-gcs-server | `fsouza/fake-gcs-server` (pinned) |
| `RemoteLinkAdapter` | `pytest-httpserver` | in-process (no container) |

Emulators seeded with the bundled synthetic cohort at test startup via a Compose `healthcheck` + seed script.

## Tier 3 — Recorded Fixtures (CI job: `test-adapters-fixtures`)

No live API access required. Tests against committed response fixtures.

| Adapter | Fixture location | Format |
|---|---|---|
| `REDCapAdapter` | `tests/fixtures/redcap/*.json` | Recorded REDCap Data Export API JSON responses |

## Acceptance gate

Each tier's CI job MUST:
1. Run all adapters against their test mechanism
2. Assert all returned frames pass `ValidationEngine(LullabySchema()).validate(frames)` (exit 0)
3. Assert all expected failure scenarios raise the correct typed exception (SC-003)
4. Complete within the time budget: Tier 1 < 2 min, Tier 2 < 5 min, Tier 3 < 1 min
