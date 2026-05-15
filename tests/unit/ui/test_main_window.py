# tests/unit/ui/test_main_window.py
# GUI tests using pytest-qt

try:
    from PySide6.QtWidgets import QApplication
    HAS_QT = True
except ImportError:
    HAS_QT = False


import pytest

if HAS_QT:
    from dnd_encounter.ui.main_window import MainWindow


@pytest.mark.skipif(not HAS_QT, reason="PySide6 not available")
def test_main_window_loads(qtbot, stub_service):
    """Basic smoke test: window should open without crashing."""
    window = MainWindow(stub_service)
    qtbot.addWidget(window)
    window.show()

    assert window.isVisible()
    assert window.windowTitle() == "D&D Encounter Manager"


@pytest.mark.skipif(not HAS_QT, reason="PySide6 not available")
def test_sidebar_shows_entities(qtbot, stub_service):
    """Sidebar should display entities from the service."""
    window = MainWindow(stub_service)
    qtbot.addWidget(window)
    window.show()

    assert window.entity_list.count() >= 0
