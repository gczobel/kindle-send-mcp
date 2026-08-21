import json
from pathlib import Path
from typing import Optional


class DeviceState:
    """Persists which Kindle device is the default target, if any."""

    def __init__(self, state_dir: Path):
        self._path = Path(state_dir) / "default_device.json"

    def get_default(self) -> Optional[str]:
        if not self._path.exists():
            return None
        data = json.loads(self._path.read_text())
        return data.get("default_device_nickname")

    def set_default(self, nickname: str) -> None:
        self._path.write_text(json.dumps({"default_device_nickname": nickname}))

    def clear_default(self) -> None:
        if self._path.exists():
            self._path.unlink()
