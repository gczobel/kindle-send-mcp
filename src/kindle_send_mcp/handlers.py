from typing import Callable, Optional

from .devices import DeviceStore
from .gmail_oauth import GmailOAuth
from .library import ResolvedBook
from .smtp_sender import SmtpSender
from .state import DeviceState


def _devices_as_dicts(devices: DeviceStore) -> list[dict]:
    return [d.to_dict() for d in devices.list_devices()]


def _needs_authorization(oauth: GmailOAuth) -> dict:
    return {"status": "needs_authorization", "auth_url": oauth.authorization_url()}


def handle_list_devices(devices: DeviceStore) -> list[dict]:
    return _devices_as_dicts(devices)


def handle_add_device(nickname: str, email: str, *, devices: DeviceStore) -> dict:
    devices.add_device(nickname, email)
    return {"status": "added", "nickname": nickname, "email": email}


def handle_send_book(
    book_id: int,
    target_nickname: Optional[str],
    *,
    sender: SmtpSender,
    devices: DeviceStore,
    oauth: GmailOAuth,
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

    if not oauth.is_authorized():
        return _needs_authorization(oauth)

    book = resolve(book_id)
    try:
        sender.send_file(
            book.file_path, target_email, title=book.title, author=book.author
        )
    except Exception as exc:
        state.clear_default()
        if not oauth.is_authorized():
            return _needs_authorization(oauth)
        return {"status": "failed", "device": target, "error": str(exc)}

    if target_nickname is not None:
        state.set_default(target_nickname)

    return {"status": "sent", "device": target, "title": book.title}
