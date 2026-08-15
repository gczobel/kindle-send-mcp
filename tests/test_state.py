from pathlib import Path

from kindle_send_mcp.state import DeviceState


def test_get_default_returns_none_when_unset(tmp_path: Path):
    state = DeviceState(tmp_path)
    assert state.get_default() is None


def test_set_and_get_default(tmp_path: Path):
    state = DeviceState(tmp_path)
    state.set_default("G090LZ123456789")
    assert state.get_default() == "G090LZ123456789"


def test_clear_default(tmp_path: Path):
    state = DeviceState(tmp_path)
    state.set_default("G090LZ123456789")
    state.clear_default()
    assert state.get_default() is None


def test_clear_default_when_never_set_is_a_noop(tmp_path: Path):
    state = DeviceState(tmp_path)
    state.clear_default()
    assert state.get_default() is None
