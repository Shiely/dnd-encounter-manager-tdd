(2) We need a button to reset the state of the tool. For example, this is important for when an encounter is complete. this should clear the initiative order, and the statblock display, and any other relevant state. This will allow the DM to start fresh for the next encounter.

**Completed in Phase 1 (2026-06-14)**

(1) We need a way to add multiple monsters to the initiative orderer at the same time. Currently, I have to open the add monster page for every monster I want to add. I want to be able to scroll through the add monster page and pick a monster, then choose the number I want to add of that type, and then add the number of that monster type to the initiative order. They should still all have individual rolls for health and initiative.

**Status**: Delivered and human-tested.
- Quantity selector (QSpinBox, 1–20, default 1, "Quantity:" label) added to AddMonsterDialog.
- `EncounterService.add_monster(monster_id, count=1)` now supports `count > 1` via independent `AddEntityCommand` executions (each performs its own d20 + DEX initiative and hit_dice HP rolls).
- MainWindow + sidebar +M path updated to pass quantity.
- Full TDD with unit tests, UI flow tests, and dedicated block9 full-stack verification.
- Living record: `PHASE_1_WORK_SUMMARY.md` + updates to `LEAD.md`.
- Human testing: Verified in `uv run python run_ui.py` — adding 3+ of the same monster produces distinct names, initiatives, and HP values. Undo works per entity. Single-add (quantity=1) behavior unchanged.

See `PHASE_1_WORK_SUMMARY.md` for full details, tests, and handoff artifacts.