import base64
import threading
from pathlib import Path
from typing import Optional

import requests
import resend
from resend.exceptions import ResendError

EPUB_CONTENT_TYPE = "application/epub+zip"

# The resend SDK is configured through module-level globals (api_key, api_url)
# that it reads at request time, so concurrent sends must serialize around
# setting them. Sends are rare, so a single lock is plenty.
_sdk_lock = threading.Lock()


class ResendSender:
    """Delivers EPUBs to a Kindle device's @kindle.com address via the
    Resend email API -- no SMTP, no OAuth, no recurring re-authorization
    (see docs/adr/0003). Amazon's Send-to-Kindle gives no delivery
    confirmation and silently discards mail from unapproved senders, so
    Resend's own logs are the audit trail."""

    def __init__(
        self,
        api_key: str,
        from_address: str = "",
        base_url: Optional[str] = None,
    ):
        self._api_key = api_key
        self._from_address = from_address
        self._base_url = base_url

    def send_file(
        self,
        file_path: Path,
        target_email: str,
        *,
        title: str,
        author: str,
    ) -> None:
        if not self._api_key:
            raise RuntimeError(
                "RESEND_API_KEY is not set -- set it to a Resend API key to send books"
            )
        if not self._from_address:
            raise RuntimeError(
                "RESEND_FROM is not set -- set it to the sender address approved "
                "by Amazon's Personal Document E-mail List"
            )

        file_path = Path(file_path)
        attachment = {
            "filename": file_path.name,
            "content": base64.b64encode(file_path.read_bytes()).decode(),
            "content_type": EPUB_CONTENT_TYPE,
        }
        params = {
            "from": self._from_address,
            "to": [target_email],
            "subject": title,
            "text": f"{title} by {author}",
            "attachments": [attachment],
        }

        # The resend SDK is configured through module-level globals; save and
        # restore them under a lock so concurrent sends never see each other's
        # configuration.
        try:
            with _sdk_lock:
                previous_key, previous_url = resend.api_key, resend.api_url
                try:
                    resend.api_key = self._api_key
                    if self._base_url is not None:
                        resend.api_url = self._base_url
                    resend.Emails.send(params)
                finally:
                    resend.api_key, resend.api_url = previous_key, previous_url
        except ResendError as exc:
            raise RuntimeError(f"Resend API error {exc.code}: {exc.message}") from exc
        except requests.RequestException as exc:
            raise RuntimeError(f"Resend request failed: {exc}") from exc
