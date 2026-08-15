from unittest.mock import MagicMock

from kindle_send_mcp.handlers import handle_send_book
from kindle_send_mcp.library import ResolvedBook
from kindle_send_mcp.state import DeviceState


def test_send_book_asks_for_device_when_no_default_and_no_target(tmp_path):
    kindle = MagicMock()
    kindle.list_devices.return_value = [{"name": "Kindle", "serial_number": "S1"}]
    state = DeviceState(tmp_path)

    result = handle_send_book(
        1, None, kindle=kindle, state=state, resolve=lambda book_id: None
    )

    assert result == {
        "status": "needs_device_selection",
        "devices": [{"name": "Kindle", "serial_number": "S1"}],
    }
    kindle.send_file.assert_not_called()


def test_send_book_uses_stored_default_silently(tmp_path):
    state = DeviceState(tmp_path)
    state.set_default("S1")
    kindle = MagicMock()
    kindle.send_file.return_value = "sku-1"
    book = ResolvedBook(
        title="Alice", author="Lewis Carroll", file_path=tmp_path / "a.epub"
    )

    result = handle_send_book(
        1, None, kindle=kindle, state=state, resolve=lambda book_id: book
    )

    assert result["status"] == "sent"
    assert result["device"] == "S1"
    kindle.send_file.assert_called_once_with(
        book.file_path, "S1", title="Alice", author="Lewis Carroll"
    )


def test_send_book_explicit_target_overrides_and_becomes_new_default(tmp_path):
    state = DeviceState(tmp_path)
    state.set_default("OLD")
    kindle = MagicMock()
    kindle.send_file.return_value = "sku-2"
    book = ResolvedBook(
        title="Alice", author="Lewis Carroll", file_path=tmp_path / "a.epub"
    )

    result = handle_send_book(
        1, "NEW", kindle=kindle, state=state, resolve=lambda book_id: book
    )

    assert result["device"] == "NEW"
    assert state.get_default() == "NEW"


def test_send_book_clears_default_on_failure_and_notes_device(tmp_path):
    state = DeviceState(tmp_path)
    state.set_default("S1")
    kindle = MagicMock()
    kindle.send_file.side_effect = RuntimeError("device offline")
    book = ResolvedBook(
        title="Alice", author="Lewis Carroll", file_path=tmp_path / "a.epub"
    )

    result = handle_send_book(
        1, None, kindle=kindle, state=state, resolve=lambda book_id: book
    )

    assert result == {"status": "failed", "device": "S1", "error": "device offline"}
    assert state.get_default() is None
