# D&D Encounter Manager (TDD Edition)

**Full implementation of the complete 4-part specification** using Hexagonal Architecture (Ports & Adapters), strict Test-Driven Development, Python 3.12 + PySide6.

This is a collaborative experiment between Shiely and Grok to build the app exactly as designed in the spec documents (Parts 1-4 in Google Drive), following the precise TDD sequence from Part 4.

## Current Status (May 2026)

- ✅ Phases A–F (Core Architecture + Commands + Services): Complete
- ✅ Phase G – UI Migration (UI-1 through UI-5): **Complete**
  - New `MainWindow` + all widgets live in `adapters/inbound/desktop_ui/`
  - 18+ pytest-qt tests green for the new UI
  - Old `ui/` folder deprecated
- ✅ Ruff: Clean
- ✅ mypy: Passing on new code (relaxed globally for now)
- ✅ Self-healing discipline maintained throughout

**Next Phase (active):** "New UI Interaction Polish & Feature Completion"  
Following strict TDD: Keyboard shortcuts first, then context menus, richer StatBlockPanel, etc.

**Goal**: Daily-driver feature parity with the original spec while keeping the architecture pure.

Built with Grok — May 2026