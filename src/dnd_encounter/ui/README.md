# DEPRECATED

This directory contains the legacy UI implementation.

**As of the UI Migration (May 2026), this code is deprecated.**

All new development and the active application now use the architecture-compliant UI located at:

`src/dnd_encounter/adapters/inbound/desktop_ui/`

## Status
- The new `MainWindow` (and supporting widgets) is now the active implementation.
- This legacy code is no longer imported by `bootstrap.py` or the running application.
- These files are kept temporarily for reference / rollback safety.

## Recommended Action
This directory can be deleted once the new UI has proven stable in production and the team is comfortable with the migration.

See `docs/UI_Migration_Plan.md` for full details of the migration.