---
id:            PLAN-002-DATA-MODEL
title:         Data Model - Batch Ingestion Adapters
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

# Data Model

## Entity: AdapterConfig (Pydantic v2 BaseModel)
Base class for all adapter configs. All credential fields use `pydantic.SecretStr`.
Fields:
- `max_attempts: int` (default: 3) — max retry attempts for transient errors
- `rate_limit_default_wait_s: int` (default: 60) — fallback wait on 429 with no `Retry-After`

Subclasses (one per adapter):
- `FileAdapterConfig`: `path: Path`, `encoding: str = "utf-8"`
- `S3AdapterConfig`: `bucket: str`, `prefix: str`, `region: str`; credentials via boto3 chain (no config fields — uses env/IAM)
- `AzureAdapterConfig`: `container: str`, `prefix: str`, `connection_string: SecretStr | None`, uses `DefaultAzureCredential` if `None`
- `GCSAdapterConfig`: `bucket: str`, `prefix: str`; credentials via Application Default Credentials
- `RemoteLinkAdapterConfig`: `url: AnyHttpUrl`, `timeout_s: int = 30`
- `MySQLAdapterConfig`: `connection_string: SecretStr`, `table_names: list[str] | None = None`
- `REDCapAdapterConfig`: `api_url: AnyHttpUrl`, `token: SecretStr` (from `REDCAP_TOKEN` env), `instrument_event_map: dict[str, str] | None = None`
- `RESTAdapterConfig`: `url: AnyHttpUrl`, `method: str = "GET"`, `headers: dict[str, SecretStr] = {}`, `next_page_field: str | None`
- `GraphQLAdapterConfig`: `url: AnyHttpUrl`, `query: str`, `headers: dict[str, SecretStr] = {}`, `cursor_field: str | None`

## Entity: BatchAdapter[C] (Generic ABC)
```python
class BatchAdapter(ABC, Generic[C]):
    @abstractmethod
    def load(self, config: C) -> dict[str, pd.DataFrame]: ...
```
Implementations: `FileAdapter`, `S3Adapter`, `AzureAdapter`, `GCSAdapter`,
`RemoteLinkAdapter`, `MySQLAdapter`, `REDCapAdapter`, `RESTAdapter`, `GraphQLAdapter`.
Stubs (raise `NotImplementedError`): `DropboxAdapter`, `OneDriveAdapter`, `GenericFallbackAdapter`.

## Entity: CanonicalOutput
Return type of every `load()` call:
- `dict[str, pd.DataFrame]` — keys are canonical table names (`participants`, `daily_vitals`, `alerts`, `clinical_outcomes`, `staff_contacts`)
- Each DataFrame must match the `LullabySchema` column contract (types, names) before hand-off
- Dedup applied per table using `LullabySchema.primary_keys(table_name)` before returning

## Exception Taxonomy

| Exception | Fields | Raised When |
|---|---|---|
| `SchemaMismatchError` | `table`, `missing_columns`, `found_columns` | Required canonical column absent in source |
| `ConnectorError` | `adapter`, `cause`, `attempts` | Network/cloud outage exhausts `max_attempts` |
| `AuthConfigError` | `adapter`, `credential_env_var` | Missing/invalid credentials at instantiation |
| `UnsupportedFormatError` | `adapter`, `detected_type` | File extension or MIME type not in supported set |
| `EncodingError` | `adapter`, `path`, `detected_encoding` | File cannot be decoded with declared encoding |
| `UnitAmbiguityError` | `column`, `sample_value` | Unit-sensitive column has no declared or detectable unit |

All exceptions inherit from `BatchAdapterError(RuntimeError)`.

## State Transitions (per load() call)

```
instantiated
    → config_validated      (Pydantic validates config at __init__)
    → connecting            (cloud/HTTP/DB connection attempt)
    → fetching              (data download / query execution)
    → parsing               (raw bytes → DataFrame rows)
    → unit_checking         (FR-016 unit detection/coercion)
    → deduplicating         (primary-key dedup via schema)
    → validating            (SPEC-001 engine validates frames)
    → done                  → returns dict[str, pd.DataFrame]
```
Any step failure → raises typed exception → no partial output returned.

## Retry Policy (via `tenacity`)

| Response | Action |
|---|---|
| 5xx / network timeout | Retry with exponential backoff; counts against `max_attempts` |
| HTTP 429 | Read `Retry-After` header (fallback: `rate_limit_default_wait_s`); sleep; retry WITHOUT consuming slot |
| Auth error (401/403) | Raise `AuthConfigError` immediately; no retry |
| 4xx (not 401/403/429) | Raise `ConnectorError` immediately; no retry |
| All retries exhausted | Raise `ConnectorError(adapter=..., cause=last_exc, attempts=max_attempts)` |
