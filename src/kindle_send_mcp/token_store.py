import json
from pathlib import Path
from typing import Optional


class TokenStore:
    def __init__(self, state_dir: Path):
        self._path = Path(state_dir) / "oauth_refresh_token.json"

    def has_token(self) -> bool:
        return self._path.exists()

    def save_refresh_token(self, refresh_token: str) -> None:
        self._path.write_text(json.dumps({"refresh_token": refresh_token}))

    def load_refresh_token(self) -> Optional[str]:
        if not self._path.exists():
            return None
        return json.loads(self._path.read_text()).get("refresh_token")

    def clear(self) -> None:
        if self._path.exists():
            self._path.unlink()
