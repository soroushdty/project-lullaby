---
id:            # e.g. TASKS-001
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
description: "Task list for feature implementation"
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`

## Phase 1: Setup

- [ ] T001 Initialize branch `###-feature-name`
- [ ] T002 [P] Baseline environment/data for feature

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infrastructure that MUST be complete before ANY user story

- [ ] T003 [P] Implement base models/utilities
- [ ] T004 [P] Update schema/registry if needed

## Phase 3: User Story 1 - [Title] (Priority: P1) 🎯 MVP

**Goal**: [Deliverable]
**Independent Test**: [Command/Step]

- [ ] T005 [P] [US1] Write failing test for [logic]
- [ ] T006 [US1] Implement [logic]
- [ ] T007 [US1] Verify test passes

## Phase 4: User Story 2 - [Title] (Priority: P2)

- [ ] T008 [P] [US2] Write failing test
- [ ] T009 [US2] Implement
- [ ] T010 [US2] Verify

## Phase 5: Polish & Cross-Cutting

- [ ] T011 Update `CHANGELOG.md` with provenance
- [ ] T012 Run full test suite and verify zero warnings
- [ ] T013 Update `README.md` or `QUICKSTART.md`

## Dependencies

- **US1** depends on Phase 2.
- **US2** depends on US1.
