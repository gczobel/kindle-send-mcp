from pathlib import Path
from unittest.mock import MagicMock, patch

from kindle_send_mcp.smtp_sender import SmtpSender


def _mock_smtp_class():
    smtp_class = MagicMock()
    smtp_instance = smtp_class.return_value
    smtp_instance.__enter__.return_value = smtp_instance
    return smtp_class, smtp_instance


def test_send_file_logs_in_and_sends_to_target_email(tmp_path: Path):
    book_path = tmp_path / "book.epub"
    book_path.write_bytes(b"fake epub bytes")
    sender = SmtpSender("sender@example.com", "app-password")

    smtp_class, smtp_instance = _mock_smtp_class()
    with patch("kindle_send_mcp.smtp_sender.smtplib.SMTP", smtp_class):
        sender.send_file(
            book_path,
            "paperwhite_ab12@kindle.com",
            title="Alice",
            author="Lewis Carroll",
        )

    smtp_instance.login.assert_called_once_with("sender@example.com", "app-password")
    smtp_instance.send_message.assert_called_once()
    sent_message = smtp_instance.send_message.call_args[0][0]
    assert sent_message["To"] == "paperwhite_ab12@kindle.com"


def test_send_file_bccs_the_sender_as_an_audit_trail(tmp_path: Path):
    book_path = tmp_path / "book.epub"
    book_path.write_bytes(b"fake epub bytes")
    sender = SmtpSender("sender@example.com", "app-password")

    smtp_class, smtp_instance = _mock_smtp_class()
    with patch("kindle_send_mcp.smtp_sender.smtplib.SMTP", smtp_class):
        sender.send_file(
            book_path,
            "paperwhite_ab12@kindle.com",
            title="Alice",
            author="Lewis Carroll",
        )

    sent_message = smtp_instance.send_message.call_args[0][0]
    assert sent_message["Bcc"] == "sender@example.com"


def test_send_file_attaches_the_epub_with_its_filename(tmp_path: Path):
    book_path = tmp_path / "alice.epub"
    book_path.write_bytes(b"fake epub bytes")
    sender = SmtpSender("sender@example.com", "app-password")

    smtp_class, smtp_instance = _mock_smtp_class()
    with patch("kindle_send_mcp.smtp_sender.smtplib.SMTP", smtp_class):
        sender.send_file(
            book_path,
            "paperwhite_ab12@kindle.com",
            title="Alice",
            author="Lewis Carroll",
        )

    sent_message = smtp_instance.send_message.call_args[0][0]
    attachments = list(sent_message.iter_attachments())
    assert len(attachments) == 1
    assert attachments[0].get_filename() == "alice.epub"
    assert attachments[0].get_content() == b"fake epub bytes"
