(2) [COMPLETED Phase 2 — human testing successful] We need a button to reset the state of the tool. For example, this is important for when an encounter is complete. this should clear the initiative order, and the statblock display, and any other relevant state. This will allow the DM to start fresh for the next encounter.

**Status (Phase 2, human testing 2026-06-14)**: Delivered. "Reset" button in sidebar (near +M/+P) + File menu "Reset / New Encounter". Service.reset() clears entities, round=1, turn index, undo stack. Full UI refresh (sidebar, stat panel, conditions button, selection). Tests + block9 with explicit clean-state asserts. Human test: add monsters → Reset → clean slate (0 entities | Round 1, cleared panels, no undo) → re-add works. See PHASE_2_WORK_SUMMARY.md and LEAD Phase 2.

**Completed in Phase 2 (human testing successful)**

(2) [see above]

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

---

**Future items (post Phase 3/4 keyboard + stat panel work)**

(3) **In progress as Phase 5** — Display the XP value awarded for defeating a monster (in StatBlockPanel for selected/current-turn entity, alongside Phase 4 glance stats).

**Investigation (no code changes)**: 
- Yes, the data is already available in our current access paths.
- Raw bestiary: `data/srd/monsters.json` includes `"xp": <int>` per monster entry (alongside "challenge_rating").
- Domain model: `src/dnd_encounter/domain/entities/monster_definition.py` has `xp: int` (and `challenge_rating: ChallengeRating`).
- Loading: `src/dnd_encounter/adapters/outbound/srd_monster_repository.py` explicitly does `"xp": item.get("xp", 0)` when building MonsterDefinition.
- Bootstrap / seeds: Explicit xp values are set for sample monsters (e.g. goblin xp=50, orc=100).
- Custom monsters: `monster_form_dialog.py` already has a full XP SpinBox and stores it when creating `MonsterDefinition(xp=...)`.
- Encounter flow: Entities carry `monster_id`; `EncounterService` already enriches via `monster_repo` for cr/ac/speed (see Phase 4 work and `encounter_service.py` get_state enrichment). The same path gives access to the full definition's xp.
- UI display paths: `StatBlockPanel` + `monster_stat_block_renderer.py` already render CR prominently and have combat stats sections; they receive the definition when `monster_repo` is wired. `EntityRowDTO` and live state carry enough (monster_id + cr in recent DTOs) to surface xp similarly without new data fetches.
- Current gaps: XP is **not** yet surfaced in the live StatBlockPanel or sidebar for an active encounter entity (only CR in some places). No "XP awarded on defeat" total or per-monster display in the main UI.

**Phase 5 scope (active, per LEAD)**: 
- Enrich `EntityRowDTO` (additive) to include xp for monster entities.
- Populate via service using existing repo path.
- Show in StatBlockPanel (e.g. extend Phase 4 glance or dedicated label).
- Full TDD + block9 per meta method (raw red pre-prod, full ignored runs after every edit, skeleton + dedicated block9 with explicit checkables, protect Phase 3 keyboard incl. list-focused Space + Phase 4 stats).
- See `LEAD.md` (Phase 5 section) and `PHASE_5_WORK_SUMMARY.md` for current coordination and subagent execution.

See `LEAD.md`, `docs/Agent_and_User_Reference.md` (gaps + MonsterDefinition), `PHASE_4_WORK_SUMMARY.md`, and the active `PHASE_5_WORK_SUMMARY.md` (coordinator handoff + subagent records). Implementation is being driven via spawned subagents following the Ouroboros meta process. No direct coding by coordinator.