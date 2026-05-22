# Utilities

This folder contains helper scripts for development and data management.

## Available Scripts

### `import_srd_monsters.py`

Downloads the 5eTools data repository and converts SRD monsters into the format used by this application.

**Usage:**

```bash
python utilities/import_srd_monsters.py
```

**Output:**

Creates `data/srd/monsters.json` containing converted monster data.

This file can later be imported into the application using the monster import feature.

**Note:**

- The script requires `git` to be installed.
- It will only clone the repository once.
- Some advanced fields (damage expressions, legendary actions details) are simplified.
