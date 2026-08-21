import importlib
import os
from pathlib import Path


def test_server_module_wires_state_kindle_and_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("CALIBRE_LIBRARY_PATH", str(tmp_path / "books"))
    monkeypatch.setenv("SENDER_EMAIL", "sender@example.com")
    monkeypatch.setenv("SMTP_APP_PASSWORD", "app-password")
    (tmp_path / "state").mkdir()
    (tmp_path / "books").mkdir()

    import kindle_send_mcp.server as server_module

    importlib.reload(server_module)

    assert server_module.STATE_DIR == tmp_path / "state"
    assert server_module.BOOKS_DIR == tmp_path / "books"
    assert server_module.DB_PATH == tmp_path / "books" / "metadata.db"
    assert server_module.mcp is not None
