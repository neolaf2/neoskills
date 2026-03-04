"""Parse and write SKILL.md files with YAML frontmatter."""

from typing import Any

import yaml


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from a markdown file.

    Returns (metadata_dict, body_text).
    If no frontmatter found, returns ({}, full_content).
    """
    content = content.strip()
    if not content.startswith("---"):
        return {}, content

    # Find closing --- at a line boundary (not inside YAML values)
    lines = content.split("\n")
    end_line = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_line = i
            break

    if end_line is None:
        return {}, content

    frontmatter_str = "\n".join(lines[1:end_line]).strip()
    body = "\n".join(lines[end_line + 1:]).strip()

    try:
        metadata = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError:
        return {}, content

    return metadata, body


def write_frontmatter(metadata: dict[str, Any], body: str) -> str:
    """Combine YAML frontmatter and markdown body into a SKILL.md string."""
    frontmatter = yaml.dump(metadata, default_flow_style=False, sort_keys=False).strip()
    return f"---\n{frontmatter}\n---\n\n{body}\n"


def extract_skill_name(content: str, fallback: str = "unnamed") -> str:
    """Extract skill name from frontmatter or first heading."""
    metadata, body = parse_frontmatter(content)

    if "name" in metadata:
        return metadata["name"]

    # Try first markdown heading
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip().lower().replace(" ", "-")

    return fallback
