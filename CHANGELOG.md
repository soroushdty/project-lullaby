# CHANGELOG

Policy: Every time a speckit (spec) is implemented, add a dated entry here that documents provenance and the concrete changes introduced.

Each entry MUST include:
- Date: ISO 8601 (YYYY-MM-DD)
- Spec: canonical link to the spec (URL or repo path). Do NOT use only a verbal description.
- Summary: brief description of the major changes introduced by the spec.
- Rationale: why this spec was necessary (design goals, problem being solved, alternatives considered).
- Impact: record concrete effects, including whether it broke anything or changed project requirements.
- Targets: list of specific files modified (path) and the line diff(s) for each file (unified diff or explicit line ranges). Line diff only is sufficient.

Template
--------
```
Date: 2026-05-31
Spec: <link-to-spec-or-path>
Summary: One-line summary of major changes.
Rationale: Short paragraph explaining why the spec was necessary.
Impact:
  - Broke/Changed requirements: yes/no and brief details
  - Docs/Constitution changes: list
Targets:
  - path/to/file.ext: (line counts only; additions and deletions)
    +3 -1
```

Example
-------
Date: 2026-05-31
Spec: https://example.com/specs/speckit-001 (or docs/specs/speckit-001.md)
Summary: Introduces `speckit` metadata format and changelog policy.
Rationale: Standardize provenance of design decisions and ensure traceable links from implementation to spec.
Impact:
  - Broke/Changed requirements: no
  - Docs/Constitution changes: added `SPECKIT.md` describing spec format
Targets:
  - SPECKIT.md: added new spec file (initial content)
    @@ -0,0 +1,120 @@
    +... (file added)

Notes
-----
- Keep entries concise and factual. Prefer linking to the authoritative spec document.
- Record only per-file line counts (e.g. `+3 -1`) instead of pasting actual changed lines into the changelog.
- For large specs that touch many files, include only the file paths and line counts; avoid pasting whole files into the changelog.
- Use a single changelog entry per implemented spec. If multiple specs are implemented on the same date, add separate dated entries.

## Changelog Entry: 000-changelog-creation

Date: 2026-06-01
Spec: specs/000-changelog-creation/spec.md
Summary: Add merge-gating changelog policy and validator to enforce per-spec provenance.
Rationale: Ensure every implemented spec produces a single, machine-parseable changelog entry for traceability and CI enforcement.
Impact:
  - Broke/Changed requirements: no
  - Docs/Constitution changes: added changelog policy and validator
Targets:
  - specs/000-changelog-creation/spec.md | +12 -0
  - tools/changelog_validator.py | +650 -0
  - .github/workflows/changelog-policy.yml | +120 -0

