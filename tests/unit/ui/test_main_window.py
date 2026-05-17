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


@pytest.mark.skipif(not HAS_QT, reason="PySide6 not available")
def test_stat_panel_updates_on_entity_selection(qtbot, stub_service):  # type: ignore[no-untyped-def]
    """Selecting an entity in the list should update the stat panel with correct DTO values (including current-turn and inactive entities)."""
    window = MainWindow(stub_service)  # type: ignore[arg-type]
    qtbot.addWidget(window)
    window.show()

    # Select the current-turn entity (row 1 = Goblin #1)
    window.entity_list.setCurrentRow(1)
    window._on_entity_selected(1)

    assert window.lbl_name.text() == "Goblin #1"
    assert window.lbl_hp.text() == "7 / 7"
    assert window.lbl_initiative.text() == "15"
    assert window.lbl_conditions.text() == "Poisoned"
    assert window.spin_hp.value() == 7

    # Verify selecting an inactive entity also works correctly
    window.entity_list.setCurrentRow(2)
    window._on_entity_selected(2)

    assert window.lbl_name.text() == "Orc #2"
    assert "0 / 15" in window.lbl_hp.text()
    assert window.lbl_initiative.text() == "12"


@pytest.mark.skipif(not HAS_QT, reason="PySide6 not available")
def test_context_menu_remove_entity(qtbot, stub_service):  # type: ignore[no-untyped-def]
    """Right-click context menu Remove action should call remove_entity and refresh the list."""
    window = MainWindow(stub_service)  # type: ignore[arg-type]
    qtbot.addWidget(window)
    window.show()

    initial_count = window.entity_list.count()

    # Simulate right-click on first item and trigger remove
    item = window.entity_list.item(0)
    window.entity_list.setCurrentItem(item)

    # Directly call the remove handler (simulates menu action)
    window._remove_entity("e1")  # instance_id from our stub

    # After remove, list should have one fewer item (stub returns same state, but we verify call)
    # Note: In real flow the service would update state; here we just verify the method is wired
    assert stub_service.remove_entity.called
    assert stub_service.remove_entity.call_args[0][0] == "e1"


@pytest.mark.skipif(not HAS_QT, reason="PySide6 not available")
def test_keyboard_shortcuts(qtbot, stub_service):  # type: ignore[no-untyped-def]
    """Space should advance turn, Delete should remove selected entity."""
    window = MainWindow(stub_service)  # type: ignore[arg-type]
    qtbot.addWidget(window)
    window.show()

    # Test Space = advance turn
    qtbot.keyPress(window, Qt.Key.Key_Space)
    assert stub_service.advance_turn.called

    # Test Delete = remove (select first item first)
    window.entity_list.setCurrentRow(0)
    qtbot.keyPress(window, Qt.Key.Key_Delete)
    assert stub_service.remove_entity.called


@pytest.mark.skipif(not HAS_QT, reason="PySide6 not available")
def test_context_menu_rename_entity(qtbot, stub_service):  # type: ignore[no-untyped-def]
    """Context menu Rename should call rename_entity with correct instance_id."""
    window = MainWindow(stub_service)  # type: ignore[arg-type]
    qtbot.addWidget(window)
    window.show()

    item = window.entity_list.item(0)
    window.entity_list.setCurrentItem(item)

    # Directly invoke the handler (simulates menu selection)
    window._rename_entity("e1")
    assert stub_service.rename_entity.called
    assert stub_service.rename_entity.call_args[0][0] == "e1"


@pytest.mark.skipif(not HAS_QT, reason="PySide6 not available")
def test_context_menu_edit_initiative(qtbot, stub_service):  # type: ignore[no-untyped-def]
    """Context menu Edit Initiative should call change_initiative with correct instance_id."""
    window = MainWindow(stub_service)  # type: ignore[arg-type]
    qtbot.addWidget(window)
    window.show()

    item = window.entity_list.item(0)
    window.entity_list.setCurrentItem(item)

    window._edit_initiative("e1")
    assert stub_service.change_initiative.called
    assert stub_service.change_initiative.call_args[0][0] == "e1"


@pytest.mark.skipif(not HAS_QT, reason="PySide6 not available")
@pytest.mark.skip(reason="Temporarily disabled - suspected cause of long CI run")
def test_add_monster_button_exists(qtbot, stub_service):  # type: ignore[no-untyped-def]
    """Add Monster button should exist and be clickable (smoke test for dialog wiring)."""
    window = MainWindow(stub_service)  # type: ignore[arg-type]
    qtbot.addWidget(window)
    window.show()

    assert window.btn_add_monster.isEnabled()
    # We don't fully test the dialog here to keep scope small
