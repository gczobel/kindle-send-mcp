from typing import Callable, Optional

from .devices import DeviceStore
from .library import ResolvedBook
from .smtp_sender import SmtpSender
from .state import DeviceState


def handle_list_devices(devices: DeviceStore) -> list[dict]:
    return devices.list_devices()


def handle_add_device(nickname: str, email: str, *, devices: DeviceStore) -> dict:
    devices.add_device(nickname, email)
    return {"status": "added", "nickname": nickname, "email": email}


def handle_send_book(
    book_id: int,
    target_nickname: Optional[str],
    *,
    sender: SmtpSender,
    devices: DeviceStore,
    state: DeviceState,
    resolve: Callable[[int], ResolvedBook],
) -> dict:
    target = target_nickname or state.get_default()
    if target is None:
        return {
            "status": "needs_device_selection",
            "devices": devices.list_devices(),
        }

    target_email = devices.get_email(target)
    if target_email is None:
        return {
            "status": "unknown_device",
            "devices": devices.list_devices(),
        }

    book = resolve(book_id)
    try:
        sender.send_file(
            book.file_path, target_email, title=book.title, author=book.author
        )
    except Exception as exc:
        state.clear_default()
        return {"status": "failed", "device": target, "error": str(exc)}

    if target_nickname is not None:
        state.set_default(target_nickname)

    return {"status": "sent", "device": target, "title": book.title}
