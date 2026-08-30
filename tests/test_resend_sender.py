import base64
from pathlib import Path
from unittest.mock import patch

import pytest
import requests
import resend
from resend.exceptions import RateLimitError

from kindle_send_mcp.resend_sender import EPUB_CONTENT_TYPE, ResendSender

SENDER_ADDRESS = "kindle@example.com"


def _sender(**overrides) -> ResendSender:
    config = {"api_key": "re_123", "from_address": SENDER_ADDRESS}
    config.update(overrides)
    return ResendSender(**config)


def test_send_file_posts_email_with_epub_attachment(tmp_path: Path):
    book_path = tmp_path / "alice.epub"
    book_path.write_bytes(b"fake epub bytes")

    with patch("resend.Emails.send") as send:
        _sender().send_file(
            book_path,
            "paperwhite_ab12@kindle.com",
            title="Alice",
            author="Lewis Carroll",
        )

    send.assert_called_once()
    params = send.call_args[0][0]
    assert params["from"] == SENDER_ADDRESS
    assert params["to"] == ["paperwhite_ab12@kindle.com"]
    assert params["subject"] == "Alice"
    assert params["text"] == "Alice by Lewis Carroll"
    (attachment,) = params["attachments"]
    assert attachment["filename"] == "alice.epub"
    assert attachment["content_type"] == EPUB_CONTENT_TYPE
    assert attachment["content"] == base64.b64encode(b"fake epub bytes").decode()


def test_send_file_sets_api_key_on_sdk_before_sending(tmp_path: Path):
    book_path = tmp_path / "book.epub"
    book_path.write_bytes(b"x")

    captured = {}

    def fake_send(params):
        captured["api_key"] = resend.api_key
        return {"id": "email-id"}

    with patch("resend.Emails.send", side_effect=fake_send):
        _sender(api_key="re_secret").send_file(
            book_path, "paperwhite_ab12@kindle.com", title="T", author="A"
        )

    assert captured["api_key"] == "re_secret"


def test_send_file_uses_configured_from_address(tmp_path: Path):
    book_path = tmp_path / "book.epub"
    book_path.write_bytes(b"x")

    with patch("resend.Emails.send") as send:
        _sender(from_address="custom@example.com").send_file(
            book_path, "paperwhite_ab12@kindle.com", title="T", author="A"
        )

    assert send.call_args[0][0]["from"] == "custom@example.com"


def test_send_file_raises_clear_error_when_api_key_missing(tmp_path: Path):
    book_path = tmp_path / "book.epub"
    book_path.write_bytes(b"x")

    with (
        patch("resend.Emails.send") as send,
        pytest.raises(RuntimeError, match="RESEND_API_KEY"),
    ):
        _sender(api_key="").send_file(
            book_path, "paperwhite_ab12@kindle.com", title="T", author="A"
        )

    send.assert_not_called()


def test_send_file_raises_clear_error_when_from_address_missing(tmp_path: Path):
    book_path = tmp_path / "book.epub"
    book_path.write_bytes(b"x")

    with (
        patch("resend.Emails.send") as send,
        pytest.raises(RuntimeError, match="RESEND_FROM"),
    ):
        _sender(from_address="").send_file(
            book_path, "paperwhite_ab12@kindle.com", title="T", author="A"
        )

    send.assert_not_called()


def test_send_file_maps_resend_api_error_to_runtime_error(tmp_path: Path):
    book_path = tmp_path / "book.epub"
    book_path.write_bytes(b"x")
    api_error = RateLimitError(
        code=429,
        message="Daily quota exceeded",
        error_type="daily_quota_exceeded",
        headers={},
    )

    with (
        patch("resend.Emails.send", side_effect=api_error),
        pytest.raises(RuntimeError, match=r"429.*quota"),
    ):
        _sender().send_file(
            book_path, "paperwhite_ab12@kindle.com", title="T", author="A"
        )


def test_send_file_maps_network_error_to_runtime_error(tmp_path: Path):
    book_path = tmp_path / "book.epub"
    book_path.write_bytes(b"x")

    with (
        patch(
            "resend.Emails.send",
            side_effect=requests.exceptions.ConnectionError("connection refused"),
        ),
        pytest.raises(RuntimeError, match="Resend request failed"),
    ):
        _sender().send_file(
            book_path, "paperwhite_ab12@kindle.com", title="T", author="A"
        )
