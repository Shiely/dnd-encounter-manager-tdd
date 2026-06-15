# Agent Instructions — D&D Encounter Manager

## Project context

Desktop D&D 5e encounter manager: Python 3.12, PySide6, hexagonal architecture, strict TDD.

- **Architecture & domain rules**: `docs/Agent_and_User_Reference.md`
- **Developer / clone discipline**: `docs/Development_Process.md`
- **Gap register & phase plan**: `LEAD.md`

## Ouroboros Flywheel (prompt infrastructure)

This project uses the [Ouroboros Flywheel](https://github.com/Shiely/flywheel) outer-loop process. The kit lives at `.flywheel/` (gitignored).

**First-time setup** (or after a fresh clone):

```powershell
.\scripts\setup-flywheel.ps1
```

**Start a new phase**:

1. Read `LEAD.md` and the latest `PHASE_N_WORK_SUMMARY.md`
2. Paste `.flywheel/meta-process/USER_TO_GROK_OUTER_LOOP_INITIATION_PROMPT.md` into the session (with phase-specific context)
3. At Turn 0, load `.flywheel/meta-process/GROK_SELF_ANALYSIS_PROMPT.md` before any test or production edits
4. Maintain a living `PHASE_N_WORK_SUMMARY.md` with TDD red/green counts per turn

**Key flywheel paths**:

| Path | Purpose |
|------|---------|
| `.flywheel/meta-process/` | Outer-loop prompts (initiation, self-analysis, assess, initiate, followup) |
| `.flywheel/PHASE_WORK_REQUEST_TEMPLATE.md` | Engineer work-order template |
| `.flywheel/skills/` | Generic flywheel skills |
| `skills/analysis.md` | Project-specific self-analysis entry point |

## Execution defaults

- **Tests**: `uv run pytest -q` after every change during a phase
- **Run app**: `uv run python run_ui.py`
- **Sync deps**: `uv sync --dev`
- Do not break hexagonal import boundaries or domain purity
- Commit runtime-affecting improvements to this repo; never commit `.flywheel/`