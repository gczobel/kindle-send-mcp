import os
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

from .devices import DeviceStore
from .handlers import handle_add_device, handle_list_devices, handle_send_book
from .library import resolve_book
from .resend_sender import ResendSender
from .state import DeviceState

STATE_DIR = Path(os.environ.get("STATE_DIR", "/state"))
BOOKS_DIR = Path(os.environ.get("CALIBRE_LIBRARY_PATH", "/books"))
DB_PATH = BOOKS_DIR / os.environ.get("CALIBRE_DB_FILENAME", "metadata.db")

mcp = FastMCP("Kindle Send MCP")

_devices = DeviceStore(STATE_DIR)
_state = DeviceState(STATE_DIR)
_sender = ResendSender(
    api_key=os.environ.get("RESEND_API_KEY", ""),
    from_address=os.environ.get("RESEND_FROM", ""),
)


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

    A "sent" status means the message was handed to the Resend API
    successfully; Amazon gives no delivery confirmation and silently
    drops mail from an unapproved sender, see docs/adr/0001.
    """
    return handle_send_book(
        book_id,
        target_device_nickname,
        sender=_sender,
        devices=_devices,
        state=_state,
        resolve=lambda bid: resolve_book(DB_PATH, BOOKS_DIR, bid),
    )


def main() -> None:
    port = int(os.environ.get("HTTP_PORT", "9002"))
    mcp.run(transport="http", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
