"""Plugin YAML schema — validates plugin.yaml at load time."""

from pathlib import Path
from typing import Any

import yaml

# Required fields and their expected types
_REQUIRED_FIELDS = {
    "name": str,
    "version": str,
    "namespace": str,
}

# Optional fields with defaults
_OPTIONAL_FIELDS = {
    "capabilities": list,
    "registry": dict,
    "host_constraints": dict,
}


def validate_plugin_yaml(path: Path) -> dict[str, Any]:
    """Validate a plugin.yaml file.

    Returns dict with 'valid' bool and 'errors' list.
    """
    errors: list[str] = []

    if not path.exists():
        return {"valid": False, "errors": [f"plugin.yaml not found: {path}"]}

    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        return {"valid": False, "errors": [f"Invalid YAML: {e}"]}

    if not isinstance(data, dict):
        return {"valid": False, "errors": ["plugin.yaml must be a YAML mapping"]}

    # Check required fields
    for field_name, expected_type in _REQUIRED_FIELDS.items():
        val = data.get(field_name)
        if val is None:
            errors.append(f"Missing required field: {field_name}")
        elif not isinstance(val, expected_type):
            errors.append(f"Field '{field_name}' must be {expected_type.__name__}, got {type(val).__name__}")

    # Check namespace format
    ns = data.get("namespace", "")
    if isinstance(ns, str) and ns and not ns.startswith("plugin/"):
        errors.append(f"Namespace must start with 'plugin/', got '{ns}'")

    # Check optional fields types
    for field_name, expected_type in _OPTIONAL_FIELDS.items():
        val = data.get(field_name)
        if val is not None and not isinstance(val, expected_type):
            errors.append(f"Field '{field_name}' must be {expected_type.__name__}, got {type(val).__name__}")

    return {"valid": len(errors) == 0, "errors": errors, "data": data}
