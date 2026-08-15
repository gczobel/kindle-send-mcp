from pathlib import Path
from unittest.mock import MagicMock, patch

from kindle_send_mcp.kindle import KindleSession


def _fake_device(name: str, serial: str):
    device = MagicMock()
    device.device_name = name
    device.device_serial_number = serial
    return device


def test_list_devices_returns_name_and_serial(tmp_path: Path):
    (tmp_path / "client.json").write_text("{}")
    session = KindleSession(tmp_path)

    fake_client = MagicMock()
    fake_client.get_owned_devices.return_value = [
        _fake_device("Gus's Kindle", "G090LZ123456789"),
    ]

    with patch(
        "kindle_send_mcp.kindle.stkclient.Client.load", return_value=fake_client
    ):
        devices = session.list_devices()

    assert devices == [{"name": "Gus's Kindle", "serial_number": "G090LZ123456789"}]


def test_list_devices_persists_session_after_call(tmp_path: Path):
    (tmp_path / "client.json").write_text("{}")
    session = KindleSession(tmp_path)
    fake_client = MagicMock()
    fake_client.get_owned_devices.return_value = []

    with patch(
        "kindle_send_mcp.kindle.stkclient.Client.load", return_value=fake_client
    ):
        session.list_devices()

    fake_client.dump.assert_called_once()


def test_send_file_calls_stkclient_with_epub_format(tmp_path: Path):
    (tmp_path / "client.json").write_text("{}")
    session = KindleSession(tmp_path)
    fake_client = MagicMock()
    fake_client.send_file.return_value = "sku-123"
    book_path = tmp_path / "book.epub"
    book_path.write_bytes(b"fake")

    with patch(
        "kindle_send_mcp.kindle.stkclient.Client.load", return_value=fake_client
    ):
        sku = session.send_file(
            book_path, "G090LZ123456789", title="Alice", author="Lewis Carroll"
        )

    assert sku == "sku-123"
    fake_client.send_file.assert_called_once_with(
        book_path,
        ["G090LZ123456789"],
        author="Lewis Carroll",
        title="Alice",
        format="epub",
    )
    fake_client.dump.assert_called_once()
