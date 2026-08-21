import json
from pathlib import Path
from typing import Optional


class DeviceStore:
    def __init__(self, state_dir: Path):
        self._path = Path(state_dir) / "devices.json"

    def _load(self) -> dict:
        if not self._path.exists():
            return {}
        return json.loads(self._path.read_text())

    def _save(self, devices: dict) -> None:
        self._path.write_text(json.dumps(devices))

    def list_devices(self) -> list[dict]:
        devices = self._load()
        return [
            {"nickname": nickname, "email": email}
            for nickname, email in devices.items()
        ]

    def add_device(self, nickname: str, email: str) -> None:
        devices = self._load()
        devices[nickname] = email
        self._save(devices)

    def get_email(self, nickname: str) -> Optional[str]:
        return self._load().get(nickname)
