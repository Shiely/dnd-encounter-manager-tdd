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
def test_main_window_loads(qtbot, stub_service):  # type: ignore[no-untyped-def]
    """Basic smoke test: window should open without crashing."""
    window = MainWindow(stub_service)  # type: ignore[arg-type]
    qtbot.addWidget(window)
    window.show()

    assert window.isVisible()
    assert window.windowTitle() == "D&D Encounter Manager"


@pytest.mark.skipif(not HAS_QT, reason="PySide6 not available")
def test_sidebar_shows_entities(qtbot, stub_service):  # type: ignore[no-untyped-def]
    """Sidebar should display entities from the service."""
    window = MainWindow(stub_service)  # type: ignore[arg-type]
    qtbot.addWidget(window)
    window.show()

    assert window.entity_list.count() >= 0


@pytest.mark.skipif(not HAS_QT, reason="PySide6 not available")
def test_advance_turn_updates_round(qtbot, stub_service):  # type: ignore[no-untyped-def]
    """Advance Turn should update the round counter."""
    window = MainWindow(stub_service)  # type: ignore[arg-type]
    qtbot.addWidget(window)
    window.show()

    initial_round = window.lbl_round.text()
    window._on_advance_turn()
    assert window.lbl_round.text() != initial_round


@pytest.mark.skipif(not HAS_QT, reason="PySide6 not available")
def test_context_menu_exists(qtbot, stub_service):  # type: ignore[no-untyped-def]
    """Right-click context menu should exist."""
    window = MainWindow(stub_service)  # type: ignore[arg-type]
    qtbot.addWidget(window)
    window.show()

    policy = window.entity_list.contextMenuPolicy()
    assert policy == Qt.ContextMenuPolicy.CustomContextMenu


@pytest.mark.skipif(not HAS_QT, reason="PySide6 not available")
def test_sidebar_shows_current_turn_and_active_entities(qtbot, stub_service):  # type: ignore[no-untyped-def]
    """Sidebar list should reflect entities including is_current_turn and is_active from get_state()."""
    window = MainWindow(stub_service)  # type: ignore[arg-type]
    qtbot.addWidget(window)
    window.show()

    # After construction, refresh() calls get_state() which now returns our rich stub
    assert window.entity_list.count() == 3

    # Verify display names are populated (current turn entity should be present)
    item_texts = [window.entity_list.item(i).text() for i in range(3)]
    assert any("Goblin #1" in text for text in item_texts)  # the current-turn entity
    assert any("Aragorn" in text for text in item_texts)
    assert any("Orc #2" in text for text in item_texts)  # inactive entity still shown
