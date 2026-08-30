from collections.abc import Callable
from typing import Optional

from .devices import DeviceStore
from .library import ResolvedBook
from .resend_sender import ResendSender
from .state import DeviceState


def _devices_as_dicts(devices: DeviceStore) -> list[dict]:
    return [d.to_dict() for d in devices.list_devices()]


def handle_list_devices(devices: DeviceStore) -> list[dict]:
    return _devices_as_dicts(devices)


def handle_add_device(nickname: str, email: str, *, devices: DeviceStore) -> dict:
    devices.add_device(nickname, email)
    return {"status": "added", "nickname": nickname, "email": email}


def handle_send_book(
    book_id: int,
    target_nickname: Optional[str],
    *,
    sender: ResendSender,
    devices: DeviceStore,
    state: DeviceState,
    resolve: Callable[[int], ResolvedBook],
) -> dict:
    target = target_nickname or state.get_default()
    if target is None:
        return {
            "status": "needs_device_selection",
            "devices": _devices_as_dicts(devices),
        }

    target_email = devices.get_email(target)
    if target_email is None:
        return {
            "status": "unknown_device",
            "devices": _devices_as_dicts(devices),
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
