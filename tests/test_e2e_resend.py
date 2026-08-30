import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar

import pytest

from kindle_send_mcp.devices import DeviceStore
from kindle_send_mcp.handlers import handle_send_book
from kindle_send_mcp.library import ResolvedBook
from kindle_send_mcp.resend_sender import (
    EPUB_CONTENT_TYPE,
    ResendSender,
)
from kindle_send_mcp.state import DeviceState

SENDER_ADDRESS = "kindle@example.com"


class _ResendStubHandler(BaseHTTPRequestHandler):
    """A minimal stand-in for POST https://api.resend.com/emails that records
    what it receives and answers like the real API."""

    requests: ClassVar[list[dict]] = []

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        type(self).requests.append(
            {
                "path": self.path,
                "authorization": self.headers.get("Authorization"),
                "body": body,
            }
        )
        payload = json.dumps({"id": "email-stub-id"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


@pytest.fixture
def resend_stub() -> str:
    """Start a local stand-in for the Resend API; yield its base URL."""
    _ResendStubHandler.requests = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), _ResendStubHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_e2e_send_file_reaches_the_resend_endpoint(tmp_path: Path, resend_stub: str):
    book_path = tmp_path / "alice.epub"
    book_path.write_bytes(b"fake epub bytes")
    sender = ResendSender(
        api_key="re_test", from_address=SENDER_ADDRESS, base_url=resend_stub
    )
    sender.send_file(
        book_path,
        "paperwhite_ab12@kindle.com",
        title="Alice",
        author="Lewis Carroll",
    )

    (request,) = _ResendStubHandler.requests
    assert request["path"] == "/emails"
    assert request["authorization"] == "Bearer re_test"
    assert request["body"]["from"] == SENDER_ADDRESS
    assert request["body"]["to"] == ["paperwhite_ab12@kindle.com"]
    assert request["body"]["subject"] == "Alice"
    (attachment,) = request["body"]["attachments"]
    assert attachment["filename"] == "alice.epub"
    assert attachment["content_type"] == EPUB_CONTENT_TYPE
    assert base64.b64decode(attachment["content"]) == b"fake epub bytes"


def test_e2e_handle_send_book_sends_via_real_resend_sender(
    tmp_path: Path, resend_stub: str
):
    book_path = tmp_path / "alice.epub"
    book_path.write_bytes(b"fake epub bytes")
    devices = DeviceStore(tmp_path)
    devices.add_device("paperwhite", "paperwhite_ab12@kindle.com")
    state = DeviceState(tmp_path)
    state.set_default("paperwhite")
    book = ResolvedBook(title="Alice", author="Lewis Carroll", file_path=book_path)

    sender = ResendSender(
        api_key="re_test", from_address=SENDER_ADDRESS, base_url=resend_stub
    )
    result = handle_send_book(
        1,
        None,
        sender=sender,
        devices=devices,
        state=state,
        resolve=lambda i: book,
    )

    assert result == {"status": "sent", "device": "paperwhite", "title": "Alice"}
    (request,) = _ResendStubHandler.requests
    assert request["body"]["to"] == ["paperwhite_ab12@kindle.com"]
    assert request["body"]["attachments"][0]["filename"] == "alice.epub"
