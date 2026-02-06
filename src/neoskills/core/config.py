"""Configuration management - loads/saves config.yaml."""

from pathlib import Path
from typing import Any

import yaml


class Config:
    """Loads and saves ~/.neoskills/config.yaml."""

    def __init__(self, config_path: Path):
        self.path = config_path
        self._data: dict[str, Any] = {}
        if self.path.exists():
            self._data = yaml.safe_load(self.path.read_text()) or {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value. Supports dotted keys like 'auth.mode'."""
        parts = key.split(".")
        current = self._data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current

    def set(self, key: str, value: Any) -> None:
        """Set a config value. Supports dotted keys."""
        parts = key.split(".")
        current = self._data
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    def save(self) -> None:
        """Write config to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(yaml.dump(self._data, default_flow_style=False))

    @property
    def data(self) -> dict[str, Any]:
        return self._data
