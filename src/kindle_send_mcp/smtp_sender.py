import base64
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Callable

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
XOAUTH2_SUCCESS_CODE = 235


class SmtpSender:
    """Delivers EPUBs to a Kindle device's @kindle.com address via SMTP,
    authenticating with OAuth2 (XOAUTH2) rather than a static password --
    see docs/adr/0002. BCCs the sender's own inbox on every send as an
    audit trail — Amazon gives no delivery confirmation and silently
    discards mail from unapproved senders, see docs/adr/0001."""

    def __init__(self, sender_email: str, get_access_token: Callable[[], str]):
        self._sender_email = sender_email
        self._get_access_token = get_access_token

    def send_file(
        self,
        file_path: Path,
        target_email: str,
        *,
        title: str,
        author: str,
    ) -> None:
        message = EmailMessage()
        message["From"] = self._sender_email
        message["To"] = target_email
        message["Bcc"] = self._sender_email
        message["Subject"] = title
        message.set_content(f"{title} by {author}")
        message.add_attachment(
            Path(file_path).read_bytes(),
            maintype="application",
            subtype="epub+zip",
            filename=Path(file_path).name,
        )

        access_token = self._get_access_token()
        raw = f"user={self._sender_email}\x01auth=Bearer {access_token}\x01\x01"
        auth_string = base64.b64encode(raw.encode()).decode()

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            code, response = smtp.docmd("AUTH", f"XOAUTH2 {auth_string}")
            if code != XOAUTH2_SUCCESS_CODE:
                raise RuntimeError(f"SMTP XOAUTH2 auth failed: {code} {response!r}")
            smtp.send_message(message)
