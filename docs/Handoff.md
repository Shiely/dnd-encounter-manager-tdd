# Agent Handoff Document

**Date:** May 2026  
**Project:** D&D Encounter Manager (TDD Edition)  
**Repo:** https://github.com/Shiely/dnd-encounter-manager-tdd

---

## Current Main Problem

**Issue:** In the rendered StatBlockPanel, many text links and references are being replaced by the literal string **"XPHB"** (and occasionally other source codes like XDMG).

This makes the stat blocks look broken, especially on monsters that reference the 2024 Player's Handbook.

### Example
Instead of clean text like:
> See page 123 of the Player's Handbook

The output shows things like:
> See page 123 of XPHB

---

## Root Cause

The problem exists in two places, but the **primary source** is the data generation pipeline:

1. **Main Cause (Data/Importer)**  
   The committed `data/srd/monsters.json` was generated with an older/weaker version of `_strip_5etools_tags`.  
   Newer 5eTools data uses source codes like `XPHB` (2024 PHB), `XDMG`, etc.  
   The current stripping logic does not properly handle `@book` reference tags and similar structures. The aggressive `split('|')` fallback often leaves behind just the source abbreviation.

2. **Secondary Cause (Renderer)**  
   `monster_stat_block_renderer.py` also performs tag stripping, but it is not defensive enough against this kind of data.

---

## What Has Been Done So Far

- Committed a higher-quality version of `monsters.json` (3723 monsters).
- Created `docs/Development_Process.md` (critical reading).
- Added `CONTRIBUTING.md`.
- Made `just` optional (with a `justfile`).
- Added a basic data quality smoke test (`tests/unit/test_bestiary_data_quality.py`).
- Improved `utilities/README.md`.

**Important Rule Established:**  
The experience of a developer on their machine must match the experience of someone who clones the repository.

---

## Current Task

**Fix the converter and regenerate the bestiary.**

### 1. Fix the Stripper

File: `utilities/import_srd_monsters.py`

Replace the `_strip_5etools_tags` function with the improved version that properly handles `@book`, `@link`, and source reference tags (especially XPHB/XDMG/etc.).

### 2. Regenerate the Bestiary

After updating the function, run:

```bash
uv run python utilities/import_full_bestiary.py
```

This will overwrite `data/srd/monsters.json`.

### 3. Verify

Run:

```bash
uv run pytest tests/unit/test_bestiary_data_quality.py -q
```

Also manually test key monsters (especially Abjurer Wizard) in the UI.

### 4. Commit

Commit both:
- The updated `utilities/import_srd_monsters.py`
- The new `data/srd/monsters.json`

---

## Key Files

| File                                              | Notes                                      |
|---------------------------------------------------|--------------------------------------------|
| `utilities/import_srd_monsters.py`                | Main place to fix `_strip_5etools_tags`    |
| `data/srd/monsters.json`                          | Needs to be regenerated after the fix      |
| `monster_stat_block_renderer.py`                  | Secondary place for defensive stripping    |
| `tests/unit/test_bestiary_data_quality.py`        | Existing smoke test (can be tightened)     |
| `docs/Development_Process.md`                     | Read this first                            |

---

## Next Immediate Actions

1. Replace `_strip_5etools_tags` in `import_srd_monsters.py`.
2. Run `uv run python utilities/import_full_bestiary.py`.
3. Run the data quality tests.
4. Manually test the UI (especially spellcasting monsters).
5. Commit the updated importer + new `monsters.json`.
6. (Optional) Tighten the XPHB check in the smoke test.

---

**Context for the receiving agent:**  
The main open issue at the time of writing is **XPHB and reference tag leakage** in the rendered stat blocks. Read `docs/Development_Process.md` first — it explains the philosophy that has guided recent work.
