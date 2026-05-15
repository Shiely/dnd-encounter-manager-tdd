# D&D Encounter Manager (TDD Edition)

**Full implementation of the complete 4-part specification** using Hexagonal Architecture (Ports & Adapters), strict Test-Driven Development, Python 3.12 + PySide6.

This is a collaborative experiment between Shiely and Grok to build the app exactly as designed in the spec documents (Parts 1-4 in Google Drive), following the precise TDD sequence from Part 4.

## Current Status (May 2026)

- ✅ Phase A: Domain Layer (complete + tests passing)
- ✅ Phase B: Ports (complete)
- ✅ Phase C: Stubs & conftest (complete)
- ✅ Phase D: Application Commands (complete - 6 commands)
- ✅ Phase E: Services (complete)
- ✅ Phase F: Integration Tests (complete)
- ✅ Final cleanup & bootstrap (complete)

**CI Status**: Active and running on every push

## Goals
- 100% faithful to the spec
- All tests must pass before moving to next phase
- Minimal local work for you — I handle all GitHub commits, branches, and pushes
- Clean, professional codebase with excellent documentation

## Repository Structure (as specified in Part 4)
```
dnd-encounter-manager-tdd/
├── .github/workflows/          # CI + Release
├── docs/requirements/          # Your 4 PDF specs (reference)
├── schema/encounter-schema-v1.json
├── data/srd/monsters.json
├── src/dnd_encounter/
│   ├── domain/          # Pure Python, no external imports
│   ├── ports/
│   ├── application/
│   ├── adapters/
│   └── main.py + bootstrap.py
├── tests/
│   ├── unit/
│   └── integration/
└── pyproject.toml
```

## TDD Process (Strict)
We follow the exact sequence in Part 4, one step at a time.

## Quick Start
```bash
uv sync
uv run dnd-encounter-manager
```

Built with Grok — May 2026