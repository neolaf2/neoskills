"""Skill validation engine — checks bank skills for completeness and consistency."""

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from neoskills.core.frontmatter import parse_frontmatter
from neoskills.core.workspace import Workspace

# Files that are never orphans (infrastructure / documentation files)
_IGNORED_FILES = frozenset({".gitkeep", ".gitignore", "README.md", "LICENSE", "__init__.py"})

# Regex to strip fenced code blocks before scanning for resource paths
_FENCED_CODE_RE = re.compile(r"```[^\n]*\n.*?```", re.DOTALL)


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"


class Category(Enum):
    STRUCTURE = "structure"
    FRONTMATTER = "frontmatter"
    REFERENCE = "reference"
    ORPHAN = "orphan"


@dataclass
class ValidationIssue:
    skill_id: str
    severity: Severity
    category: Category
    message: str
    path: Path | None = None


@dataclass
class ValidationReport:
    total_skills: int = 0
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0


# Regex to find paths like scripts/foo.sh, references/bar.md, assets/baz.png
_RESOURCE_PATH_RE = re.compile(r"(?:scripts|references|assets)/[\w./_-]*\w")


def _strip_code_blocks(text: str) -> str:
    """Remove fenced code blocks so paths inside examples aren't matched."""
    return _FENCED_CODE_RE.sub("", text)


class SkillValidator:
    """Validate skills in the bank for completeness and consistency."""

    def __init__(self, workspace: Workspace):
        self.workspace = workspace
        self.skills_dir = workspace.bank_skills

    def validate_all(self) -> ValidationReport:
        """Validate every skill in the bank."""
        report = ValidationReport()
        if not self.skills_dir.exists():
            return report

        skill_ids = sorted(
            d.name for d in self.skills_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
        )
        report.total_skills = len(skill_ids)

        for skill_id in skill_ids:
            self._validate_skill(skill_id, report)

        return report

    def validate_one(self, skill_id: str) -> ValidationReport:
        """Validate a single skill."""
        report = ValidationReport(total_skills=1)
        self._validate_skill(skill_id, report)
        return report

    def fix_stubs(self, skill_id: str) -> list[Path]:
        """Create stub files for missing references in a skill's SKILL.md."""
        canonical = self.skills_dir / skill_id / "canonical"
        skill_file = canonical / "SKILL.md"
        if not skill_file.exists():
            return []

        content = skill_file.read_text()
        _, body = parse_frontmatter(content)
        body_no_code = _strip_code_blocks(body)
        referenced = _RESOURCE_PATH_RE.findall(body_no_code)

        created = []
        for ref_path in sorted(set(referenced)):
            full_path = canonical / ref_path
            if not full_path.exists():
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(f"# TODO: Implement {ref_path}\n")
                created.append(full_path)

        return created

    def _validate_skill(self, skill_id: str, report: ValidationReport) -> None:
        """Run all checks for a single skill."""
        canonical = self.skills_dir / skill_id / "canonical"
        skill_file = canonical / "SKILL.md"

        # Check 1: SKILL.md exists
        if not skill_file.exists():
            report.issues.append(
                ValidationIssue(
                    skill_id=skill_id,
                    severity=Severity.ERROR,
                    category=Category.STRUCTURE,
                    message="canonical/SKILL.md is missing",
                    path=canonical,
                )
            )
            return  # Can't check further without the file

        content = skill_file.read_text()
        fm, body = parse_frontmatter(content)

        # Check 2: Frontmatter has name (must be a non-empty string)
        name_val = fm.get("name")
        if not name_val or not isinstance(name_val, str):
            report.issues.append(
                ValidationIssue(
                    skill_id=skill_id,
                    severity=Severity.ERROR,
                    category=Category.FRONTMATTER,
                    message="frontmatter missing or invalid 'name' field (must be a non-empty string)",
                    path=skill_file,
                )
            )

        # Check 3: Frontmatter has description (must be a non-empty string)
        desc_val = fm.get("description")
        if not desc_val or not isinstance(desc_val, str):
            report.issues.append(
                ValidationIssue(
                    skill_id=skill_id,
                    severity=Severity.ERROR,
                    category=Category.FRONTMATTER,
                    message="frontmatter missing or invalid 'description' field (must be a non-empty string)",
                    path=skill_file,
                )
            )

        # Check 4: Referenced paths exist on disk (strip code blocks first)
        body_no_code = _strip_code_blocks(body)
        referenced_paths = set(_RESOURCE_PATH_RE.findall(body_no_code))
        for ref_path in sorted(referenced_paths):
            full_path = canonical / ref_path
            if not full_path.exists():
                report.issues.append(
                    ValidationIssue(
                        skill_id=skill_id,
                        severity=Severity.ERROR,
                        category=Category.REFERENCE,
                        message=f"referenced path does not exist: {ref_path}",
                        path=full_path,
                    )
                )

        # Check 5: Files in scripts/, references/, assets/ not referenced in body (orphans)
        for subdir_name in ("scripts", "references", "assets"):
            subdir = canonical / subdir_name
            if not subdir.exists():
                continue
            for file_path in sorted(subdir.rglob("*")):
                if not file_path.is_file():
                    continue
                if file_path.name in _IGNORED_FILES:
                    continue
                rel = str(file_path.relative_to(canonical))
                if rel not in referenced_paths:
                    report.issues.append(
                        ValidationIssue(
                            skill_id=skill_id,
                            severity=Severity.WARNING,
                            category=Category.ORPHAN,
                            message=f"file not referenced in SKILL.md: {rel}",
                            path=file_path,
                        )
                    )
