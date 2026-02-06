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

    # Find closing ---
    end_idx = content.find("---", 3)
    if end_idx == -1:
        return {}, content

    frontmatter_str = content[3:end_idx].strip()
    body = content[end_idx + 3 :].strip()

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
