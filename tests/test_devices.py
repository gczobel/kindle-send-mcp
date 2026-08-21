from pathlib import Path

from kindle_send_mcp.devices import DeviceStore


def test_list_devices_returns_empty_when_unset(tmp_path: Path):
    store = DeviceStore(tmp_path)
    assert store.list_devices() == []


def test_add_device_shows_up_in_list_devices(tmp_path: Path):
    store = DeviceStore(tmp_path)
    store.add_device("paperwhite", "paperwhite_ab12@kindle.com")
    assert store.list_devices() == [
        {"nickname": "paperwhite", "email": "paperwhite_ab12@kindle.com"}
    ]


def test_get_email_returns_the_registered_address(tmp_path: Path):
    store = DeviceStore(tmp_path)
    store.add_device("paperwhite", "paperwhite_ab12@kindle.com")
    assert store.get_email("paperwhite") == "paperwhite_ab12@kindle.com"


def test_get_email_returns_none_for_unknown_nickname(tmp_path: Path):
    store = DeviceStore(tmp_path)
    assert store.get_email("nonexistent") is None


def test_devices_persist_across_new_store_instances(tmp_path: Path):
    DeviceStore(tmp_path).add_device("paperwhite", "paperwhite_ab12@kindle.com")
    reloaded = DeviceStore(tmp_path)
    assert reloaded.get_email("paperwhite") == "paperwhite_ab12@kindle.com"
