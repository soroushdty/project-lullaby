---
id:            # e.g. SPEC-001
title:         # human title
status:        draft
version:       0.1.0
created:       # YYYY-MM-DD
updated:       # YYYY-MM-DD
author:        
depends_on:    []
implements:    []
supersedes:    null
superseded_by: null
related:       []
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`

**Input**: User description: "$ARGUMENTS"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - [Brief Title] (Priority: P1)

[Describe this user journey in plain language]

**Why this priority**: [Explain value and alignment with P1-P10]

**Independent Test**: [e.g., "Run command X against data Y and verify Z"]

**Acceptance Scenarios**:

1. **Given** [state], **When** [action], **Then** [expected]

---

[Add P2/P3 stories following same pattern]

### Edge Cases

- [Boundary conditions, error handling, sparse data, locale/timezone issues]

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: [Capability or behavior]
- **FR-002**: [Capability or behavior]

### Constitution Alignment (P1-P10)

- **P1 SDD**: [How it follows spec-first]
- **P2 Reproducibility**: [Fixed seeds, deterministic steps]
- **P3 Schema-Driven**: [Does not hardcode columns]
- **P4 Source-Agnostic**: [Normalization path]
- **P5 Resilience**: [Fails loud on invalid data]
- **P7 Honest Evaluation**: [Metrics and CIs]
- **P8 Clinical Fidelity**: [Alert/composite rules]
- **P9 Privacy**: [Synthetic-only evidence]
- **P10 Equity/Accessibility**: [Accessible visual/logic]

## Success Criteria *(mandatory)*

- **SC-001**: [Measurable outcome]
- **SC-002**: [Measurable outcome]

## Assumptions & Dependencies

- [Target users, scope boundaries, environment needs]
- **Depends on**: [Specs or external systems]
