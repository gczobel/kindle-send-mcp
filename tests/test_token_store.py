from pathlib import Path

from kindle_send_mcp.token_store import TokenStore


def test_has_token_is_false_when_unset(tmp_path: Path):
    store = TokenStore(tmp_path)
    assert store.has_token() is False


def test_save_and_load_refresh_token(tmp_path: Path):
    store = TokenStore(tmp_path)
    store.save_refresh_token("refresh-abc123")
    assert store.has_token() is True
    assert store.load_refresh_token() == "refresh-abc123"


def test_load_refresh_token_returns_none_when_unset(tmp_path: Path):
    store = TokenStore(tmp_path)
    assert store.load_refresh_token() is None


def test_clear_removes_the_token(tmp_path: Path):
    store = TokenStore(tmp_path)
    store.save_refresh_token("refresh-abc123")
    store.clear()
    assert store.has_token() is False
    assert store.load_refresh_token() is None


def test_clear_when_never_set_is_a_noop(tmp_path: Path):
    store = TokenStore(tmp_path)
    store.clear()
    assert store.has_token() is False
