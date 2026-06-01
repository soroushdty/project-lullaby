# Draft version of changelog-creation specification 

Purpose
-------
Speckit instructions that each spec must generate one valid entry `CHANGELOG.md` when the spec is implemented.

Required fields (YAML frontmatter recommended)
---------------------------------------------
- `id`: unique spec identifier (e.g., `speckit-001`)
- `title`: short, descriptive title
- `authors`: list of author names/handles
- `date`: ISO 8601 date when spec was published
- `status`: draft | accepted | implemented | deprecated
- `related`: links to related issues/PRs (optional)

Body (markdown)
---------------
1. Summary: one-paragraph summary of the spec.
2. Motivation / Rationale: why this change is necessary.
3. Specification: concrete requirements, data formats, APIs, behavior, and examples.
4. Compatibility & Migration: note breaking changes, upgrade steps, and test expectations.
5. Tests & Verification: how to verify the implementation.
6. Files & Diffs (optional in spec): if relevant, reference example diffs or patches that illustrate required changes.

Recommended metadata example
----------------------------
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

Summary
-------
This spec defines the required fields and practices for recording implementations in `CHANGELOG.md`.

Motivation
----------
Ensure each implemented design decision has provenance, rationale, and exact file-level diffs recorded so future maintainers can audit why a change happened and what it touched.

Specification (high-level)
-------------------------
- Implementations MUST add a single entry to `CHANGELOG.md` with a link to the canonical spec document.
- Each entry MUST include the `Date`, `Spec` (link), `Summary`, `Rationale`, `Impact`, and `Targets` as described in `CHANGELOG.md`.
- `Targets` should list affected files and present either a brief unified-diff snippet or explicit line ranges showing changes.

Files and diff format guidance
-----------------------------
- Prefer recording per-file line counts showing the number of added and removed lines (for example: `+3 -1`).
- If line counts are impractical, include `path: lines X-Y changed` with a short note, but do not paste actual file contents into the spec or changelog.

Verification
------------
- PR implementing a spec should include the spec id in the PR title or body and add the corresponding `CHANGELOG.md` entry before merge.
- Tests or CI steps verifying behavior should be linked from the spec or changelog entry.

Example usage
-------------
1. Author publishes `speckit-002.md` in `docs/specs/` and marks it `status: accepted`.
2. Implementation PR updates code and adds a `CHANGELOG.md` entry dated on merge referencing `docs/specs/speckit-002.md` and showing file diffs for targeted files.
