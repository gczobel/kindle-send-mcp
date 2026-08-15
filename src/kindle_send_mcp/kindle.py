from pathlib import Path
from typing import List

import stkclient


class KindleSession:
    """Wraps a persisted stkclient OAuth session, re-saving it after every
    call since stkclient rotates the refresh token on use."""

    def __init__(self, state_dir: Path):
        self._client_path = Path(state_dir) / "client.json"

    def _load(self) -> "stkclient.Client":
        with open(self._client_path) as f:
            return stkclient.Client.load(f)

    def _save(self, client: "stkclient.Client") -> None:
        with open(self._client_path, "w") as f:
            client.dump(f)

    def list_devices(self) -> List[dict]:
        client = self._load()
        devices = client.get_owned_devices()
        self._save(client)
        return [
            {"name": d.device_name, "serial_number": d.device_serial_number}
            for d in devices
        ]

    def send_file(
        self,
        file_path: Path,
        target_device_serial_number: str,
        *,
        title: str,
        author: str,
    ) -> str:
        client = self._load()
        sku = client.send_file(
            file_path,
            [target_device_serial_number],
            author=author,
            title=title,
            format="epub",
        )
        self._save(client)
        return sku
