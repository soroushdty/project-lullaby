---
id:            PLAN-000-QUICKSTART
title:         Quickstart - Changelog Policy Validation
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-000]
implements:    [P2, P5]
supersedes:    null
superseded_by: null
related:       [PLAN-000]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Quickstart

## 1. Run local validation
```bash
python3 tools/changelog_validator.py --changelog CHANGELOG.md --spec-dir specs
```

Expected:
- exit code `0` when changelog policy passes
- non-zero exit with actionable errors on violations

## 2. Run tests
```bash
pytest -q tests/unit/test_changelog_validator.py tests/contract/test_changelog_contract.py tests/integration/test_changelog_ci_gate.py
```

## 3. CI gate
Add required workflow `changelog-policy` that runs validator on pull requests and blocks merge on failure.

## 4. Authoring checklist for implementation PRs
- Include `spec-id` in PR title/body.
- Add exactly one changelog entry for that `spec-id`.
- Ensure `Targets` lines use `path | +added -removed`.
- Ensure `Date` reflects merge date policy.
