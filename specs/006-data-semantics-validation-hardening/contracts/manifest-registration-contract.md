---
id: CONTRACT-006-MANIFEST
title: Manifest Registration Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-006, SPEC-004]
implements: [P2, P3, P5]
supersedes: null
superseded_by: null
related: [SPEC-004]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Manifest Registration

## Default Manifest

The default artifact manifest remains:

```text
outputs/figures/manifest.json
```

## Registerable Paths

Every generated artifact with a repository-relative path must be registered in the default
manifest, regardless of whether it is under `outputs/figures/eda/` or another repo-relative
output directory.

## Non-Registerable Paths

Artifacts written outside the repository must not be added with absolute paths. The command must
emit a clear warning that the outside-repo artifact is not registered in the default manifest.

## Entry Requirements

Each registered artifact entry must include:

- `artifact_id`
- `path`
- `title`
- `spec`
- `inputs`
- `required_roles`
- `optional_roles_used`
- `warnings`
- `created_at_utc`
- `deterministic`

## Acceptance Evidence

If hardening changes dashboard semantics, warnings, category completeness, or registration
behavior, affected tracked PNG artifacts and `outputs/figures/manifest.json` must be regenerated.
