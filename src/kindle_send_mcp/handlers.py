from typing import Callable, Optional

from .kindle import KindleSession
from .library import ResolvedBook
from .state import DeviceState


def handle_list_devices(kindle: KindleSession) -> list[dict]:
    return kindle.list_devices()


def handle_send_book(
    book_id: int,
    target_device_serial_number: Optional[str],
    *,
    kindle: KindleSession,
    state: DeviceState,
    resolve: Callable[[int], ResolvedBook],
) -> dict:
    target = target_device_serial_number or state.get_default()
    if target is None:
        return {
            "status": "needs_device_selection",
            "devices": kindle.list_devices(),
        }

    book = resolve(book_id)
    try:
        sku = kindle.send_file(
            book.file_path, target, title=book.title, author=book.author
        )
    except Exception as exc:
        state.clear_default()
        return {"status": "failed", "device": target, "error": str(exc)}

    if target_device_serial_number is not None:
        state.set_default(target_device_serial_number)

    return {"status": "sent", "device": target, "sku": sku, "title": book.title}
