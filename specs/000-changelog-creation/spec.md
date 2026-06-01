---
id: SPEC-000
title: Changelog Creation Requirement
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: []
implements: [P1, P2]
supersedes: null
superseded_by: null
related: []
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Feature Specification: Changelog Creation Requirement

## Purpose
Each implemented spec must generate exactly one valid entry in `CHANGELOG.md`.

## Required fields (YAML frontmatter recommended)
- `id`: unique spec identifier (e.g., `speckit-001`)
- `title`: short, descriptive title
- `authors`: list of author names/handles
- `date`: ISO 8601 date when spec was published
- `status`: `draft` | `accepted` | `implemented` | `deprecated`
- `related`: links to related issues/PRs (optional)

## Body (markdown)
1. Summary: one-paragraph summary of the spec.
2. Motivation / Rationale: why this change is necessary.
3. Specification: concrete requirements, data formats, APIs, behavior, and examples.
4. Compatibility & Migration: note breaking changes, upgrade steps, and test expectations.
5. Tests & Verification: how to verify the implementation.
6. Files & Diffs (optional in spec): if relevant, reference example diffs or patches that illustrate required changes.

## Recommended metadata example
```yaml
---
id: speckit-001
title: Standard changelog and speckit references
authors:
  - Jane Doe <jane@example.com>
date: 2026-05-31
status: accepted
related:
  - https://github.com/org/repo/issues/123
---
```

## Summary
This spec defines required fields and practices for recording implementations in `CHANGELOG.md`.

## Motivation
Each implemented design decision must include provenance, rationale, and file-level impact for maintainability and auditability.

## Specification
- Implementations MUST add a single entry to `CHANGELOG.md` with a link to the canonical spec document.
- Each entry MUST include `Date`, `Spec` (link), `Summary`, `Rationale`, `Impact`, and `Targets` as described in `CHANGELOG.md`.
- `Targets` SHOULD list affected files and either brief unified-diff snippets or explicit line ranges.

## Files and diff format guidance
- Prefer per-file line counts for adds/removes (for example: `+3 -1`).
- If line counts are impractical, include `path: lines X-Y changed` with a short note.
- Do not paste full file contents into spec or changelog entries.

## Verification
- PR implementing a spec should include the spec id in the PR title or body.
- PR must add corresponding `CHANGELOG.md` entry before merge.
- Tests or CI steps verifying behavior should be linked from the spec or changelog entry.

## Example usage
1. Author publishes `speckit-002.md` in `docs/specs/` and marks it `status: accepted`.
2. Implementation PR updates code and adds a `CHANGELOG.md` entry dated on merge, referencing `docs/specs/speckit-002.md` and showing file-level diff impact.
