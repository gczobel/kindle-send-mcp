import importlib


def test_server_module_wires_state_books_and_resend_sender(tmp_path, monkeypatch):
    monkeypatch.setenv("STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("CALIBRE_LIBRARY_PATH", str(tmp_path / "books"))
    monkeypatch.setenv("RESEND_API_KEY", "re_123")
    monkeypatch.setenv("RESEND_FROM", "kindle@example.com")
    (tmp_path / "state").mkdir()
    (tmp_path / "books").mkdir()

    import kindle_send_mcp.server as server_module

    importlib.reload(server_module)

    assert server_module.STATE_DIR == tmp_path / "state"
    assert server_module.BOOKS_DIR == tmp_path / "books"
    assert server_module.DB_PATH == tmp_path / "books" / "metadata.db"
    assert server_module.mcp is not None
    assert server_module._sender._api_key == "re_123"
    assert server_module._sender._from_address == "kindle@example.com"
    assert server_module._sender._base_url is None


def test_server_module_leaves_resend_from_empty_when_unset(tmp_path, monkeypatch):
    monkeypatch.setenv("STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("CALIBRE_LIBRARY_PATH", str(tmp_path / "books"))
    monkeypatch.setenv("RESEND_API_KEY", "re_123")
    (tmp_path / "state").mkdir()
    (tmp_path / "books").mkdir()

    import kindle_send_mcp.server as server_module

    importlib.reload(server_module)

    assert server_module._sender._from_address == ""


def test_server_module_starts_without_api_key_and_fails_at_send_time(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("CALIBRE_LIBRARY_PATH", str(tmp_path / "books"))
    (tmp_path / "state").mkdir()
    (tmp_path / "books").mkdir()

    import kindle_send_mcp.server as server_module

    importlib.reload(server_module)

    assert server_module._sender._api_key == ""
