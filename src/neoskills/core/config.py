"""Configuration management — layered config with project → user → defaults hierarchy."""

from pathlib import Path
from typing import Any

import yaml

# Package-level defaults (always present as the bottom layer)
_PACKAGE_DEFAULTS: dict[str, Any] = {
    "version": "0.2.1",
    "default_target": "claude-code-user",
    "auth": {"mode": "auto"},
}


def _load_yaml(path: Path) -> dict[str, Any]:
    if path.exists():
        return yaml.safe_load(path.read_text()) or {}
    return {}


def _deep_get(data: dict[str, Any], key: str, default: Any = None) -> Any:
    """Resolve a dotted key like 'auth.mode' from a nested dict."""
    parts = key.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    return current


def _deep_set(data: dict[str, Any], key: str, value: Any) -> None:
    """Set a dotted key like 'auth.mode' in a nested dict."""
    parts = key.split(".")
    current = data
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


_UNSET = object()  # Sentinel to distinguish "not provided" from None


class ConfigHierarchy:
    """Layered configuration: project-local → user → package defaults.

    Resolution order (first non-None wins):
      1. Project-local:  .neoskills/config.yaml relative to cwd (walks up)
      2. User:           ~/.neoskills/config.yaml
      3. Package defaults (embedded)
    """

    def __init__(
        self,
        user_config_path: Path | None = None,
        project_config_path: Path | object = _UNSET,
    ):
        self._user_path = user_config_path or (Path.home() / ".neoskills" / "config.yaml")
        # Only auto-discover project config if not explicitly provided
        if project_config_path is _UNSET:
            self._project_path = self._find_project_config()
        else:
            self._project_path = project_config_path  # type: ignore[assignment]

        self._defaults = dict(_PACKAGE_DEFAULTS)
        self._user_data = _load_yaml(self._user_path)
        self._project_data = _load_yaml(self._project_path) if self._project_path else {}

    @staticmethod
    def _find_project_config() -> Path | None:
        """Walk up from cwd looking for .neoskills/config.yaml."""
        current = Path.cwd()
        for parent in [current, *current.parents]:
            candidate = parent / ".neoskills" / "config.yaml"
            if candidate.exists():
                return candidate
        return None

    # --- Layer stack (project > user > defaults) ---

    @property
    def _layers(self) -> list[tuple[str, dict[str, Any]]]:
        """Ordered list of (name, data) from highest to lowest priority."""
        layers = []
        if self._project_data:
            layers.append(("project", self._project_data))
        if self._user_data:
            layers.append(("user", self._user_data))
        layers.append(("defaults", self._defaults))
        return layers

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value. Walks layers; first non-None wins."""
        for _, data in self._layers:
            val = _deep_get(data, key)
            if val is not None:
                return val
        return default

    def source(self, key: str) -> str | None:
        """Return which layer a key's value comes from ('project', 'user', 'defaults')."""
        for name, data in self._layers:
            if _deep_get(data, key) is not None:
                return name
        return None

    def set(self, key: str, value: Any) -> None:
        """Set a config value. Always writes to the user layer."""
        _deep_set(self._user_data, key, value)

    def save(self) -> None:
        """Persist the user config to disk."""
        self._user_path.parent.mkdir(parents=True, exist_ok=True)
        self._user_path.write_text(yaml.dump(self._user_data, default_flow_style=False))

    @property
    def data(self) -> dict[str, Any]:
        """Merged view of all layers (for display purposes)."""
        merged: dict[str, Any] = {}
        # Apply in reverse order so higher-priority layers overwrite
        for _, layer in reversed(self._layers):
            merged = _merge_dicts(merged, layer)
        return merged


def _merge_dicts(base: dict, overlay: dict) -> dict:
    """Recursively merge overlay into base (overlay wins)."""
    result = dict(base)
    for k, v in overlay.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _merge_dicts(result[k], v)
        else:
            result[k] = v
    return result


# Backward-compatible alias — existing code does `Config(ws.config_file)`
class Config(ConfigHierarchy):
    """Backward-compatible wrapper: single-file config that plugs into ConfigHierarchy."""

    def __init__(self, config_path: Path):
        # Treat the given path as the user config, no project config
        super().__init__(user_config_path=config_path, project_config_path=None)
        self.path = config_path
