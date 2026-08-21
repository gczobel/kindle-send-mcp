import smtplib
from email.message import EmailMessage
from pathlib import Path

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


class SmtpSender:
    """Delivers EPUBs to a Kindle device's @kindle.com address via SMTP.
    BCCs the sender's own inbox on every send as an audit trail — Amazon
    gives no delivery confirmation and silently discards mail from
    unapproved senders, see docs/adr/0001."""

    def __init__(self, sender_email: str, app_password: str):
        self._sender_email = sender_email
        self._app_password = app_password

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

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(self._sender_email, self._app_password)
            smtp.send_message(message)
