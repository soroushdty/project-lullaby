---
id:            PLAN-014
title:         Static Interactive Dashboard Viewer
status:        draft
version:       0.1.0
created:       2026-06-02
author:        Gemini CLI
depends_on:    [SPEC-014]
implements:    [P1, P2, P6, P10]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Implementation Plan: Static Interactive Dashboard Viewer

**Branch**: `014-interactive-dashboard-viewer` | **Date**: 2026-06-02 | **Spec**: [specs/014-interactive-dashboard-viewer/spec.md]

## Summary

This plan outlines the architecture for a lightweight, static React frontend that serves as an interactive viewer for Project Lullaby's generated artifacts. It will read `outputs/figures/manifest.json` dynamically and provide a sidebar navigation to view each PNG alongside its metadata, warnings, and provenance tracking.

## Technical Context

**Language/Version**: TypeScript / HTML / CSS
**Primary Dependencies**: React 18, Vite (for building), Tailwind CSS (for styling)
**Storage**: Static files (`outputs/figures/`)
**Target Platform**: Any static web server (GitHub Pages, S3, or local `http.server`)
**Project Type**: Static Web Application (SPA)

## Constitution Check

- **P1 SDD**: PASS.
- **P2 Reproducibility**: PASS. Does not modify or generate data.
- **P6 Distribution**: PASS. Compiles to pure static assets.

## Project Structure

### Documentation

```text
specs/014-interactive-dashboard-viewer/
├── spec.md
├── plan.md              # This file
└── tasks.md             # Task list
```

### Source Code

```text
src/ui/
├── index.html           # App entry point
├── package.json         # UI dependencies (Vite, React)
├── vite.config.ts       # Build configuration
└── src/
    ├── main.tsx         # React root
    ├── App.tsx          # Main layout (Sidebar + Content)
    ├── components/
    │   ├── Sidebar.tsx  # Navigation grouped by artifact type
    │   ├── ImageViewer.tsx # Displays the PNG and handles availability
    │   └── Metadata.tsx # Displays warnings and required roles
    └── types/
        └── manifest.ts  # TypeScript interfaces for manifest.json
```

## Strategy

1. **Scaffold UI**: Initialize a Vite + React + TypeScript project in `src/ui`.
2. **Fetch Logic**: Implement a hook to fetch `/manifest.json` on load (assuming the built app is served from the `outputs/figures` directory).
3. **Layout**: Build a dual-pane layout with a sticky sidebar on the left and a scrollable content area on the right.
4. **Build & Serve**: Configure Vite to build the app into `outputs/figures/ui` so it can be served trivially via Python's HTTP server.
