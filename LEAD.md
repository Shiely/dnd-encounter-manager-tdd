# LEAD — Master Gap Register & Phase Plan

**Project**: D&D 5e Encounter Manager (`dnd-encounter-manager-tdd`)  
**Purpose**: Single source of truth for gaps, debt, prioritized phase breakdown, cross-cutting rules, process status, and Ouroboros readiness notes. Future agents should bootstrap from this file + the latest PHASE summary + source.

---

## Process & Tooling Note (do not delete)

This project uses the **Ouroboros Flywheel** process kit at `.flywheel/` (gitignored; clone via `scripts/setup-flywheel.ps1`).

- Every new phase/iteration **must** begin by loading the self-analysis prompt at Turn 0.
- Work orders for the engineer role are generated via the initiate prompt + this document's phase section.
- Submissions are assessed with the assess prompt; followup orders (when needed) are appended into the engineer's `PHASE_N_WORK_SUMMARY.md`.
- See `.flywheel/README.md` and `.flywheel/docs/the-outer-loop-process.md` for full rules.

**At the start of Turn 0 for any phase, load and apply** `.flywheel/meta-process/GROK_SELF_ANALYSIS_PROMPT.md` to this file + the previous PHASE summary + relevant source.

---

## Current High-Level Status

- Last completed phase: Bootstrap (flywheel integration)
- Current test health: run `uv run pytest -q` and record counts here after each phase
- Protected public surfaces (never break without deliberate narrow extension + tests):
  - Hexagonal layering enforced by import-linter (`domain` → `ports` → `application` → `adapters`; `bootstrap.py` is the sole composition root)
  - Domain purity: no external imports or side effects in `src/dnd_encounter/domain/`
  - Command/DTO contracts: `EditHpCommand` is the only HP mutation path; services return `EncounterStateDTO`
  - `data/srd/monsters.json` schema and committed bestiary quality policy
  - Desktop UI entry: `src/dnd_encounter/adapters/inbound/desktop_ui/` (legacy `ui/` is deprecated)
- Known open high-severity gaps: see Gap Register below

---

## Prioritized Phase Breakdown

### Phase 0 — Flywheel Bootstrap (current)

**Goal**: Wire the Ouroboros outer-loop process into this repo without polluting git history.

**Deliverables**:
1. Gitignored `.flywheel/` clone + `scripts/setup-flywheel.ps1`
2. This `LEAD.md`, project `skills/analysis.md`, and `AGENTS.md`
3. First `PHASE_0_WORK_SUMMARY.md` once Phase 0 execution begins

### Phase 1 — Batch Add Monsters to Initiative

**Goal**: Deliver the core user feature from docs/TODO.md (quantity selector in Add Monster dialog so users can add N copies of the same monster type at once; each copy must receive independent initiative (d20 + dex) and HP (hit_dice roll or static) rolls). First real feature phase after flywheel bootstrap. Strict TDD, additive/contract-protecting, full block9 verification required.

**Deliverables** (from the Phase 1 Engineer Work Order):
1. Extend AddMonsterDialog with a quantity selector (QSpinBox, sensible range e.g. 1–20, default 1, clear label). Expose both the selected monster id and the chosen quantity (new getter). Existing single-selection behavior and custom monster creation must continue to work unchanged.
2. Extend EncounterService.add_monster(self, monster_id: str, count: int = 1) (preserving backward compatibility for existing call sites with count=1) so that count > 1 results in count independent executions of AddEntityCommand. Each invocation must perform its own dice rolls for initiative (d20 + dex modifier) and HP (roll_expression on hit_dice or fallback to static hit_points).
3. Update MainWindow._on_add_monster (and the sidebar “+M” / add_monster_requested signal path) to read the quantity from the dialog and pass it to the service. When quantity=1, all observable behavior (including undo, state updates, sidebar display names, and StatBlockPanel) must remain identical to the pre-phase behavior.
4. Add tests that are failing before any production code changes: unit-level coverage proving that add_monster(monster_id, count=N) produces N distinct EncounterEntity instances with different initiative and current_hp values (and correct display names); a UI flow test (in the test_ui_flows or new_main_window style) that exercises the add path and asserts the resulting EncounterStateDTO / sidebar model contains the expected number of entities with independent rolls. After core green, dedicate a Turn to block9 full-stack (real dialog qty path + 3+ monsters + explicit checkable state/DTO/model/undo/round asserts).

**Status (completed)**: All 4 deliverables implemented. Strict TDD + self-healing followed (red tests first with explicit counts recorded pre any non-test prod edit; full `uv run pytest -q --ignore=...` after every edit + immediate heals; dedicated block9 Turn with explicit asserts). Changes purely additive; count=1 path + all pre-existing call sites / returns / observables identical. Zero protected surface violations (hexagonal layers, adapters/inbound/desktop_ui/ only for UI, domain purity, EditHpCommand as sole HP path, etc.). Final test health: 55 passed (baseline 54 with the documented --ignore for gap-test-collection). 

Human testing (2026-06-14): Verified end-to-end in `uv run python run_ui.py`. Opening the Add Monster dialog, selecting a monster, setting Quantity (e.g. 3–4), and adding produces the expected number of entities with independent initiative rolls, independent HP rolls (from hit_dice), correct sequential display names (e.g. "Goblin #1", "#2", "#3"), and full undo support. Single-add behavior (quantity=1) is unchanged. No regressions observed.

Living record + handoff: See PHASE_1_WORK_SUMMARY.md (contains mandatory Turn 0 self-analysis per GROK_SELF_ANALYSIS_PROMPT + skills/analysis.md, numbered Turns with before/after counts + rationale + files + scope notes, 1:1 Completion Summary, cross-cutting TDD/additive/block9/Ouroboros notes, raw red/green outputs, post-assessment polish, and human testing confirmation). 

Ready for Phase 2 initiation. Pre-existing gap-test-collection (collection error) remains out of scope and documented.

---

## Gap Register (living)

| id | description | source | severity | phase |
|----|-------------|--------|----------|-------|
| gap-test-collection | `tests/unit/test_import_srd_monsters.py` fails collection (`ModuleNotFoundError: import_srd_monsters`) | pytest run | high | 1 |
| gap-flywheel-bootstrap | No PHASE summaries or gap-driven phases yet | bootstrap | medium | 0 |

**Categories for this project**:
- Hexagonal architecture / import-linter violations
- TDD coverage of UI flows and integration adapters
- Bestiary data quality and importer reproducibility
- Fresh-clone developer experience (see `docs/Development_Process.md`)
- Ouroboros / self-consumption (can agents continue from markdown alone?)

---

## Tech Debt Register (honest, not hidden)

- Legacy `ui/` folder still present but deprecated — not removed to avoid scope creep.
- Token images fetched on-demand (`data/images/` gitignored) — deliberate size tradeoff.

---

## Cross-Cutting Rules for This Project

- **Protected surfaces** (additive only unless explicitly scoped):
  - Domain entities, value objects, and sorting/tie-break rules
  - Application services and command handlers
  - JSON encounter/monster repository adapters
  - `monsters.json` committed-data policy
- **Full-stack verification target** ("block9" equivalent):
  - Integration: `tests/integration/test_json_monster_repository.py`, `tests/integration/test_json_encounter_repository.py`
  - UI flows: `tests/unit/ui/test_ui_flows.py`, `tests/unit/ui/test_new_main_window.py` (headless via `pytest-qt`)
- **Test command**: `uv run pytest -q` (full suite after every edit during a phase)
- **Lint / architecture**: `uv run ruff check .`, `uv run mypy`, `uv run lint-imports`
- **Record locations**:
  - Master analysis: this file (`LEAD.md`)
  - Per-phase living records: `PHASE_N_WORK_SUMMARY.md` at repo root
  - Project reference: `docs/Agent_and_User_Reference.md`
- **Ouroboros requirement**: At phase close, the PHASE summary + updates to this LEAD must be sufficient for a fresh agent to continue with only markdown + source.

---

## Process Evolution Notes

- 2026-06-14: Adopted Ouroboros Flywheel (gitignored clone at `.flywheel/`). Self-analysis mandatory at Turn 0.

---

## How to Start the Next Outer Loop Iteration

1. Ensure flywheel is present: `.\scripts\setup-flywheel.ps1`
2. Paste `.flywheel/meta-process/USER_TO_GROK_OUTER_LOOP_INITIATION_PROMPT.md` into your LLM
3. Fill in phase context (reference this LEAD + latest `PHASE_N_WORK_SUMMARY.md`)
4. Load the self-analysis prompt first (Turn 0)

See `.flywheel/README.md` and `AGENTS.md` for onboarding details.