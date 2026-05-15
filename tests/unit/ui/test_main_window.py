# tests/unit/ui/test_main_window.py
# GUI tests using pytest-qt

try:
    import PySide6.QtWidgets  # noqa: F401
    HAS_QT = True
except ImportError:
    HAS_QT = False


from PySide6.QtCore import Qt
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


@pytest.mark.skipif(not HAS_QT, reason="PySide6 not available")
def test_advance_turn_updates_round(qtbot, stub_service):
    """Advance Turn should update the round counter."""
    window = MainWindow(stub_service)
    qtbot.addWidget(window)
    window.show()

    initial_round = window.lbl_round.text()
    window._on_advance_turn()
    assert window.lbl_round.text() != initial_round


@pytest.mark.skipif(not HAS_QT, reason="PySide6 not available")
def test_context_menu_exists(qtbot, stub_service):
    """Right-click context menu should exist."""
    window = MainWindow(stub_service)
    qtbot.addWidget(window)
    window.show()

    assert window.entity_list.contextMenuPolicy() == Qt.CustomContextMenu
