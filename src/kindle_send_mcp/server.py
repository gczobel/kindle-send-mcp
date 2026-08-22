import os
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse, RedirectResponse, Response

from .devices import DeviceStore
from .gmail_oauth import GmailOAuth
from .handlers import handle_add_device, handle_list_devices, handle_send_book
from .library import resolve_book
from .smtp_sender import SmtpSender
from .state import DeviceState
from .token_store import TokenStore

STATE_DIR = Path(os.environ.get("STATE_DIR", "/state"))
BOOKS_DIR = Path(os.environ.get("CALIBRE_LIBRARY_PATH", "/books"))
DB_PATH = BOOKS_DIR / os.environ.get("CALIBRE_DB_FILENAME", "metadata.db")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "")

mcp = FastMCP("Kindle Send MCP")

_devices = DeviceStore(STATE_DIR)
_state = DeviceState(STATE_DIR)
_tokens = TokenStore(STATE_DIR)
_oauth = GmailOAuth(
    client_id=os.environ.get("GOOGLE_CLIENT_ID", ""),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", ""),
    redirect_uri=f"{PUBLIC_BASE_URL}/oauth/callback",
    token_store=_tokens,
)
_sender = SmtpSender(os.environ.get("SENDER_EMAIL", ""), _oauth.get_access_token)


@mcp.tool()
def list_devices() -> list[dict]:
    """List Kindle devices registered with this server."""
    return handle_list_devices(_devices)


@mcp.tool()
def add_device(nickname: str, email: str) -> dict:
    """Register a Kindle device by nickname and its @kindle.com address.

    Find the address in Amazon's Manage Your Content and Devices ->
    Preferences -> Personal Document Settings -> Send-to-Kindle E-Mail
    Settings.
    """
    return handle_add_device(nickname, email, devices=_devices)


@mcp.tool()
def send_book(book_id: int, target_device_nickname: Optional[str] = None) -> dict:
    """Send a book from the library to a Kindle device.

    If no target_device_nickname is given and no default device is set
    yet, returns the device list instead of guessing -- ask the user
    which device, then call this again with their choice.

    A "needs_authorization" status means the sender account needs a
    one-time setup: present the returned auth_url to the user, ask them
    to confirm once they've signed in there, then retry this exact same
    call yourself -- don't ask the user to re-request the book, you
    already have everything needed to retry.

    A "sent" status means the message was handed off successfully;
    Amazon gives no delivery confirmation and silently drops mail from
    an unapproved sender, see docs/adr/0001.
    """
    return handle_send_book(
        book_id,
        target_device_nickname,
        sender=_sender,
        devices=_devices,
        oauth=_oauth,
        state=_state,
        resolve=lambda bid: resolve_book(DB_PATH, BOOKS_DIR, bid),
    )


@mcp.custom_route("/oauth/start", methods=["GET"])
async def oauth_start(request: Request) -> Response:
    if _oauth.is_authorized():
        return PlainTextResponse("Already authorized.", status_code=403)
    return RedirectResponse(_oauth.authorization_url())


@mcp.custom_route("/oauth/callback", methods=["GET"])
async def oauth_callback(request: Request) -> Response:
    if _oauth.is_authorized():
        return PlainTextResponse("Already authorized.", status_code=403)

    code = request.query_params.get("code")
    if code is None:
        return PlainTextResponse("Missing code parameter.", status_code=400)

    _oauth.exchange_code(code)
    return PlainTextResponse("Authorization complete. You can close this tab.")


def main() -> None:
    port = int(os.environ.get("HTTP_PORT", "9002"))
    mcp.run(transport="http", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
