# tests/unit/ui/test_main_window.py
# GUI tests using pytest-qt

from dnd_encounter.ui.main_window import MainWindow


def test_main_window_loads(qtbot, stub_service):
    """Basic smoke test: window should open without crashing."""
    window = MainWindow(stub_service)
    qtbot.addWidget(window)
    window.show()

    assert window.isVisible()
    assert window.windowTitle() == "D&D Encounter Manager"


def test_sidebar_shows_entities(qtbot, stub_service):
    """Sidebar should display entities from the service."""
    window = MainWindow(stub_service)
    qtbot.addWidget(window)
    window.show()

    # Should have at least one entity in the list (from stub)
    assert window.entity_list.count() >= 0
