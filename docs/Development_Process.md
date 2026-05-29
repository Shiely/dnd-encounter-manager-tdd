# Development Process

This document captures hard-learned lessons about keeping the developer experience consistent with what a fresh clone of the repository provides.

## Core Principle

**The experience of a developer working locally must match the experience of someone who clones the repo.**

If something works well in your local dev environment but is broken or degraded for a fresh clone, the repo is in a bad state.

## Key Rules

1. **Commit runtime-affecting code promptly**
   - Any changes to the renderer, importers, data processing, or stat block logic must be committed before relying on them long-term.
   - Do not leave significant improvements only in your working directory.

2. **Before testing on a fresh clone or another machine**
   - Run `git status`
   - Ensure all relevant files (especially in `utilities/` and `src/dnd_encounter/adapters/inbound/desktop_ui/`) are committed.
   - Pull in a fresh clone and verify the behavior matches your dev environment.

3. **The committed `monsters.json` is the source of truth**
   - This is the data users and fresh clones will use.
   - It must be high quality.
   - Prefer quality over maximum monster count if the full dataset cannot yet be generated cleanly.

4. **Importer scripts are part of the project**
   - All main importer scripts should be committed so the data generation pipeline is reproducible.
   - Do not rely on untracked local versions of these scripts.

## Bestiary Data Policy

- `data/srd/monsters.json` is deliberately committed so new users do not need to run heavy importers.
- When the importer pipeline improves significantly, regenerate the file and commit the new version.
- Document the regeneration process in `utilities/README.md`.

## Recommended Workflow

Before pushing or testing on another machine:

1. Review `git status` and `git diff`.
2. Commit any changes to:
   - `utilities/`
   - Renderer and stat block panel
   - Data processing logic
   - `monsters.json` (when intentionally updating)
3. Push.
4. On a fresh clone, run `uv sync --dev` and verify the app + key monsters render correctly.

## Common Pitfalls (From Experience)

- Leaving improved version of `_strip_5etools_tags` or the renderer only in the dev folder.
- Committing a large `monsters.json` generated with older, weaker importer logic.
- Assuming "it works on my machine" is sufficient.
- Treating importer scripts as disposable local tools rather than part of the reproducible pipeline.

## Goal

Anyone who runs:

```bash
git clone ...
cd dnd-encounter-manager-tdd
uv sync --dev
uv run python run_ui.py
```

...should get a high-quality experience with clean monster data and correct rendering behavior.

## Optional Tooling

We provide a `justfile` with convenient shortcuts (e.g. `just run`, `just test`, `just validate`). 

**This is completely optional.** You are not required to install `just`. All functionality is also available using normal `uv run` commands.

See `CONTRIBUTING.md` for more details.
