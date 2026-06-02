# Contract: Boolean Hardening and Parsing

This contract defines the strict parsing rules for boolean-like domain fields to prevent misinterpretation of CSV/string inputs.

## Parsing Rules

### 1. No `.astype(bool)`
- Generic `.astype(bool)` MUST NOT be used for fields that may contain string values like `"False"`, `"0"`, or `"None"`.
- Use `src.validation.semantics.parse_domain_boolean_series` for all domain boolean fields.

### 2. Explicit Truthiness
- **True tokens:** `true`, `yes`, `1`, `t`, `y`, `on`.
- **False tokens:** `false`, `no`, `0`, `f`, `n`, `off`.
- Comparison MUST be case-insensitive and whitespace-stripped.

### 3. Missingness Policy
- Nulls, blanks, and unknown tokens MUST NOT be silently converted to `False`.
- They MUST be preserved as `Missing/Unknown` in EDA and diagnostics.

## Implementation Targets

- `src/modeling/metrics.py`: Replace `primary_metric.astype(bool)` with domain parser.
- `src/simulation/environment.py`: Use domain parser for `heat_wave`.
- `src/simulation/export.py`: Audit remaining `.astype(bool)` calls in diagnostic logic.
- `src/ingestion/stream/adapter.py`: Ensure `_stream_pending` uses the strict policy.
