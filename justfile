# Default command - shows available recipes
default:
    @just --list

# Run the application
run:
    uv run python run_ui.py

# Run all tests
test:
    uv run pytest

# Run only the UI-related tests (faster)
test-ui:
    uv run pytest tests/unit/ui/ -q

# Sync dependencies (including dev tools)
sync:
    uv sync --dev

# Validate the quality of the committed bestiary data
validate:
    uv run pytest tests/unit/test_bestiary_data_quality.py -q

# Run a quick health check (useful before pushing or testing on another machine)
check:
    @echo "Running quick checks..."
    @just validate
    @just test-ui
    @echo "Checks complete."
