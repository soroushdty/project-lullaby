---
id:            PLAN-002-CONTRACT-002
title:         AdapterConfig Schema Contract
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-002]
implements:    [P5]
supersedes:    null
superseded_by: null
related:       [PLAN-002]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# AdapterConfig Schema Contract

All config classes are Pydantic v2 `BaseModel` subclasses. Credential fields use `SecretStr`.

## Base: AdapterConfig

```python
class AdapterConfig(BaseModel):
    max_attempts: int = Field(default=3, ge=1, le=10)
    rate_limit_default_wait_s: int = Field(default=60, ge=1)
```

## Per-adapter configs

| Adapter | Key Fields | Credential Fields |
|---|---|---|
| `FileAdapterConfig` | `path: Path`, `encoding: str = "utf-8"` | — |
| `S3AdapterConfig` | `bucket: str`, `prefix: str = ""`, `region: str` | boto3 credential chain (env/IAM; not in config) |
| `AzureAdapterConfig` | `container: str`, `prefix: str = ""` | `connection_string: SecretStr \| None` (None → DefaultAzureCredential) |
| `GCSAdapterConfig` | `bucket: str`, `prefix: str = ""` | Application Default Credentials (not in config) |
| `RemoteLinkAdapterConfig` | `url: AnyHttpUrl`, `timeout_s: int = 30` | — |
| `MySQLAdapterConfig` | `table_names: list[str] \| None = None` | `connection_string: SecretStr` |
| `REDCapAdapterConfig` | `api_url: AnyHttpUrl`, `instrument_event_map: dict \| None = None` | `token: SecretStr` (also readable from `REDCAP_TOKEN` env; config takes precedence) |
| `RESTAdapterConfig` | `url: AnyHttpUrl`, `method: str = "GET"`, `next_page_field: str \| None` | `headers: dict[str, SecretStr] = {}` |
| `GraphQLAdapterConfig` | `url: AnyHttpUrl`, `query: str`, `cursor_field: str \| None` | `headers: dict[str, SecretStr] = {}` |

## Validation rules

- `path` (FileAdapterConfig): must exist and be readable at load time (validated in `load()`, not at config construction)
- `url` fields: validated by Pydantic `AnyHttpUrl` (must be http or https)
- `method` (RESTAdapterConfig): one of `GET`, `POST`
- `query` (GraphQLAdapterConfig): non-empty string
- `connection_string` (MySQLAdapterConfig): non-empty `SecretStr`; SQLAlchemy parses it at connect time

## Secret masking guarantee

All `SecretStr` fields render as `'**********'` in `repr()`, `str()`, and Pydantic's JSON serialization (when using `.model_dump(mode="json")`). Adapters MUST NOT call `.get_secret_value()` outside of the connection/auth call itself.
