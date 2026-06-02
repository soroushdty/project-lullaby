---
id:            TASKS-014
title:         Static Interactive Dashboard Viewer
status:        draft
version:       0.1.0
created:       2026-06-02
author:        Gemini CLI
depends_on:    [PLAN-014]
implements:    [SPEC-014]
description: "Task list for feature implementation"
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Tasks: Static Interactive Dashboard Viewer

**Input**: Design documents from `specs/014-interactive-dashboard-viewer/`

## Phase 1: Setup

- [ ] T001 Initialize branch `014-interactive-dashboard-viewer`
- [ ] T002 Scaffold Vite + React + TS project in `src/ui/`
- [ ] T003 Configure Vite to output build to `outputs/figures/ui/`

## Phase 2: Foundational 

- [ ] T004 Define TypeScript interfaces for the `manifest.json` schema (`src/ui/src/types/manifest.ts`)
- [ ] T005 Create `useManifest` hook to fetch and parse the manifest data

## Phase 3: User Story 1 - Navigate Pipeline Artifacts (Priority: P1) 

- [ ] T006 Implement `Sidebar` component to list artifact titles grouped by type (e.g., `analytic`, `eda`)
- [ ] T007 Implement main `App` layout with state for the currently selected artifact

## Phase 4: User Story 2 - View Artifact Metadata (Priority: P1)

- [ ] T008 Implement `ImageViewer` component to display the PNG or an unavailability message
- [ ] T009 Implement `Metadata` component to render warnings, required roles, and missingness caveats
- [ ] T010 Wire components together in the main content area

## Phase 5: Polish & Deployment (Priority: P2)

- [ ] T011 Verify `npm run build` successfully compiles to the target directory
- [ ] T012 Write `quickstart.md` instructing users to run `python -m http.server -d outputs/figures`
- [ ] T013 Update `CHANGELOG.md` with provenance
