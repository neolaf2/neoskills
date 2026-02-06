"""SHA256 checksum utilities for skill content."""

import hashlib
from pathlib import Path


def checksum_string(content: str) -> str:
    """SHA256 hash of a string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def checksum_file(filepath: Path) -> str:
    """SHA256 hash of a file's contents."""
    return checksum_string(filepath.read_text(encoding="utf-8"))


def checksum_directory(dirpath: Path) -> str:
    """SHA256 hash of all files in a directory (sorted, concatenated)."""
    parts = []
    for f in sorted(dirpath.rglob("*")):
        if f.is_file():
            parts.append(f.read_text(encoding="utf-8"))
    return checksum_string("".join(parts))
