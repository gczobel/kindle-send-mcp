import os
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP
from starlette.middleware import Middleware

from .auth import BearerTokenMiddleware
from .handlers import handle_list_devices, handle_send_book
from .kindle import KindleSession
from .library import resolve_book
from .state import DeviceState

STATE_DIR = Path(os.environ.get("STATE_DIR", "/state"))
BOOKS_DIR = Path(os.environ.get("CALIBRE_LIBRARY_PATH", "/books"))
DB_PATH = BOOKS_DIR / os.environ.get("CALIBRE_DB_FILENAME", "metadata.db")

mcp = FastMCP("Kindle Send MCP")

_kindle = KindleSession(STATE_DIR)
_state = DeviceState(STATE_DIR)


@mcp.tool()
def list_devices() -> list[dict]:
    """List Kindle devices registered to this Amazon account."""
    return handle_list_devices(_kindle)


@mcp.tool()
def send_book(
    book_id: int, target_device_serial_number: Optional[str] = None
) -> dict:
    """Send a book from the library to a Kindle device.

    If no target_device_serial_number is given and no default device is
    set yet, returns the device list instead of guessing — call this
    again with a target_device_serial_number once the user picks one.
    """
    return handle_send_book(
        book_id,
        target_device_serial_number,
        kindle=_kindle,
        state=_state,
        resolve=lambda bid: resolve_book(DB_PATH, BOOKS_DIR, bid),
    )


def main() -> None:
    port = int(os.environ.get("HTTP_PORT", "9002"))
    auth_token = os.environ["AUTH_TOKEN"]
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port,
        middleware=[Middleware(BearerTokenMiddleware, token=auth_token)],
    )


if __name__ == "__main__":
    main()
