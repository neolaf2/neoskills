"""Tests for neoskills.bank.validator."""

from pathlib import Path

import pytest

from neoskills.bank.validator import (
    Category,
    Severity,
    SkillValidator,
    ValidationReport,
)
from neoskills.core.workspace import Workspace


@pytest.fixture
def validator_workspace(tmp_path: Path) -> Workspace:
    """Workspace with skills for validation testing."""
    ws = Workspace(root=tmp_path / ".neoskills")
    ws.initialize()
    return ws


def _make_skill(ws: Workspace, skill_id: str, content: str, files: dict[str, str] | None = None):
    """Helper: create a skill in the bank with optional extra files."""
    canonical = ws.bank_skills / skill_id / "canonical"
    canonical.mkdir(parents=True, exist_ok=True)
    (canonical / "SKILL.md").write_text(content)
    if files:
        for rel_path, file_content in files.items():
            full = canonical / rel_path
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(file_content)


class TestValidatorChecks:
    def test_valid_skill_passes(self, validator_workspace):
        _make_skill(validator_workspace, "good-skill", (
            "---\nname: good-skill\ndescription: A valid skill\n---\n\n"
            "# Good Skill\n\nJust a simple skill.\n"
        ))
        report = SkillValidator(validator_workspace).validate_one("good-skill")
        assert report.passed
        assert report.errors == []
        assert report.warnings == []

    def test_missing_skill_md(self, validator_workspace):
        # Create skill dir without SKILL.md
        (validator_workspace.bank_skills / "broken" / "canonical").mkdir(parents=True)
        report = SkillValidator(validator_workspace).validate_one("broken")
        assert not report.passed
        assert len(report.errors) == 1
        assert report.errors[0].category == Category.STRUCTURE

    def test_missing_name(self, validator_workspace):
        _make_skill(validator_workspace, "no-name", (
            "---\ndescription: Has description but no name\n---\n\nBody.\n"
        ))
        report = SkillValidator(validator_workspace).validate_one("no-name")
        assert not report.passed
        errors = [i for i in report.errors if i.category == Category.FRONTMATTER]
        assert any("name" in e.message for e in errors)

    def test_missing_description(self, validator_workspace):
        _make_skill(validator_workspace, "no-desc", (
            "---\nname: no-desc\n---\n\nBody.\n"
        ))
        report = SkillValidator(validator_workspace).validate_one("no-desc")
        assert not report.passed
        errors = [i for i in report.errors if i.category == Category.FRONTMATTER]
        assert any("description" in e.message for e in errors)

    def test_missing_referenced_file(self, validator_workspace):
        _make_skill(validator_workspace, "broken-refs", (
            "---\nname: broken-refs\ndescription: Has broken refs\n---\n\n"
            "See scripts/build.sh for details.\n"
        ))
        report = SkillValidator(validator_workspace).validate_one("broken-refs")
        assert not report.passed
        ref_errors = [i for i in report.errors if i.category == Category.REFERENCE]
        assert len(ref_errors) == 1
        assert "scripts/build.sh" in ref_errors[0].message

    def test_referenced_file_exists(self, validator_workspace):
        _make_skill(
            validator_workspace,
            "good-refs",
            (
                "---\nname: good-refs\ndescription: Has valid refs\n---\n\n"
                "Run scripts/build.sh to compile.\n"
            ),
            files={"scripts/build.sh": "#!/bin/bash\necho ok\n"},
        )
        report = SkillValidator(validator_workspace).validate_one("good-refs")
        assert report.passed

    def test_orphan_file_warning(self, validator_workspace):
        _make_skill(
            validator_workspace,
            "orphans",
            "---\nname: orphans\ndescription: Has orphan files\n---\n\nNo refs.\n",
            files={"scripts/unused.sh": "#!/bin/bash\n"},
        )
        report = SkillValidator(validator_workspace).validate_one("orphans")
        assert report.passed  # Orphans are warnings, not errors
        assert len(report.warnings) == 1
        assert report.warnings[0].category == Category.ORPHAN
        assert "scripts/unused.sh" in report.warnings[0].message


class TestValidateAll:
    def test_counts_all_skills(self, validator_workspace):
        _make_skill(validator_workspace, "a", "---\nname: a\ndescription: A\n---\n\nOK.\n")
        _make_skill(validator_workspace, "b", "---\nname: b\ndescription: B\n---\n\nOK.\n")
        report = SkillValidator(validator_workspace).validate_all()
        assert report.total_skills == 2
        assert report.passed


class TestFixStubs:
    def test_creates_missing_scripts(self, validator_workspace):
        _make_skill(validator_workspace, "needs-fix", (
            "---\nname: needs-fix\ndescription: Needs stubs\n---\n\n"
            "Run scripts/build.sh and see references/guide.md.\n"
        ))
        validator = SkillValidator(validator_workspace)
        created = validator.fix_stubs("needs-fix")
        assert len(created) == 2
        canonical = validator_workspace.bank_skills / "needs-fix" / "canonical"
        assert (canonical / "scripts" / "build.sh").exists()
        assert (canonical / "references" / "guide.md").exists()

    def test_does_not_overwrite_existing(self, validator_workspace):
        _make_skill(
            validator_workspace,
            "has-file",
            (
                "---\nname: has-file\ndescription: Already has file\n---\n\n"
                "Run scripts/build.sh.\n"
            ),
            files={"scripts/build.sh": "#!/bin/bash\necho real\n"},
        )
        validator = SkillValidator(validator_workspace)
        created = validator.fix_stubs("has-file")
        assert created == []
        # Verify original content preserved
        canonical = validator_workspace.bank_skills / "has-file" / "canonical"
        assert "echo real" in (canonical / "scripts" / "build.sh").read_text()
