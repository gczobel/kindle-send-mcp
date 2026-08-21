from unittest.mock import MagicMock

from kindle_send_mcp.devices import Device
from kindle_send_mcp.handlers import (
    handle_add_device,
    handle_list_devices,
    handle_send_book,
)
from kindle_send_mcp.library import ResolvedBook
from kindle_send_mcp.state import DeviceState


def test_list_devices_delegates_to_device_store():
    devices = MagicMock()
    devices.list_devices.return_value = [
        Device(nickname="paperwhite", email="paperwhite_ab12@kindle.com")
    ]

    result = handle_list_devices(devices)

    assert result == [{"nickname": "paperwhite", "email": "paperwhite_ab12@kindle.com"}]


def test_add_device_registers_it_and_confirms():
    devices = MagicMock()

    result = handle_add_device(
        "paperwhite", "paperwhite_ab12@kindle.com", devices=devices
    )

    devices.add_device.assert_called_once_with(
        "paperwhite", "paperwhite_ab12@kindle.com"
    )
    assert result == {
        "status": "added",
        "nickname": "paperwhite",
        "email": "paperwhite_ab12@kindle.com",
    }


def test_send_book_asks_for_device_when_no_default_and_no_target(tmp_path):
    sender = MagicMock()
    devices = MagicMock()
    devices.list_devices.return_value = [
        Device(nickname="paperwhite", email="paperwhite_ab12@kindle.com")
    ]
    state = DeviceState(tmp_path)

    result = handle_send_book(
        1,
        None,
        sender=sender,
        devices=devices,
        state=state,
        resolve=lambda book_id: None,
    )

    assert result == {
        "status": "needs_device_selection",
        "devices": [{"nickname": "paperwhite", "email": "paperwhite_ab12@kindle.com"}],
    }
    sender.send_file.assert_not_called()


def test_send_book_uses_stored_default_silently(tmp_path):
    state = DeviceState(tmp_path)
    state.set_default("paperwhite")
    sender = MagicMock()
    devices = MagicMock()
    devices.get_email.return_value = "paperwhite_ab12@kindle.com"
    book = ResolvedBook(
        title="Alice", author="Lewis Carroll", file_path=tmp_path / "a.epub"
    )

    result = handle_send_book(
        1, None, sender=sender, devices=devices, state=state, resolve=lambda i: book
    )

    assert result == {"status": "sent", "device": "paperwhite", "title": "Alice"}
    sender.send_file.assert_called_once_with(
        book.file_path,
        "paperwhite_ab12@kindle.com",
        title="Alice",
        author="Lewis Carroll",
    )


def test_send_book_explicit_target_overrides_and_becomes_new_default(tmp_path):
    state = DeviceState(tmp_path)
    state.set_default("old-device")
    sender = MagicMock()
    devices = MagicMock()
    devices.get_email.return_value = "new_ab12@kindle.com"
    book = ResolvedBook(
        title="Alice", author="Lewis Carroll", file_path=tmp_path / "a.epub"
    )

    result = handle_send_book(
        1,
        "new-device",
        sender=sender,
        devices=devices,
        state=state,
        resolve=lambda i: book,
    )

    assert result["device"] == "new-device"
    assert state.get_default() == "new-device"


def test_send_book_clears_default_on_failure_and_notes_device(tmp_path):
    state = DeviceState(tmp_path)
    state.set_default("paperwhite")
    sender = MagicMock()
    sender.send_file.side_effect = RuntimeError("smtp auth failed")
    devices = MagicMock()
    devices.get_email.return_value = "paperwhite_ab12@kindle.com"
    book = ResolvedBook(
        title="Alice", author="Lewis Carroll", file_path=tmp_path / "a.epub"
    )

    result = handle_send_book(
        1, None, sender=sender, devices=devices, state=state, resolve=lambda i: book
    )

    assert result == {
        "status": "failed",
        "device": "paperwhite",
        "error": "smtp auth failed",
    }
    assert state.get_default() is None


def test_send_book_reports_unknown_device_without_touching_default(tmp_path):
    state = DeviceState(tmp_path)
    state.set_default("paperwhite")
    sender = MagicMock()
    devices = MagicMock()
    devices.get_email.return_value = None
    devices.list_devices.return_value = [
        Device(nickname="paperwhite", email="paperwhite_ab12@kindle.com")
    ]

    result = handle_send_book(
        1,
        "typo-device",
        sender=sender,
        devices=devices,
        state=state,
        resolve=lambda i: None,
    )

    assert result == {
        "status": "unknown_device",
        "devices": [{"nickname": "paperwhite", "email": "paperwhite_ab12@kindle.com"}],
    }
    sender.send_file.assert_not_called()
    assert state.get_default() == "paperwhite"
