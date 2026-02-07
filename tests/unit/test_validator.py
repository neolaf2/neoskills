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


    def test_orphan_gitkeep_not_reported(self, validator_workspace):
        """`.gitkeep` files should never be flagged as orphans."""
        _make_skill(
            validator_workspace,
            "with-gitkeep",
            "---\nname: with-gitkeep\ndescription: Has gitkeep\n---\n\nNo refs.\n",
            files={"scripts/.gitkeep": ""},
        )
        report = SkillValidator(validator_workspace).validate_one("with-gitkeep")
        assert report.passed
        assert report.warnings == []

    def test_orphan_readme_not_reported(self, validator_workspace):
        """README.md in subdirectories should never be flagged as orphans."""
        _make_skill(
            validator_workspace,
            "with-readme",
            "---\nname: with-readme\ndescription: Has readme\n---\n\nNo refs.\n",
            files={"scripts/README.md": "# Scripts\n"},
        )
        report = SkillValidator(validator_workspace).validate_one("with-readme")
        assert report.passed
        assert report.warnings == []

    def test_path_inside_code_block_not_matched(self, validator_workspace):
        """Paths inside fenced code blocks should not be treated as references."""
        _make_skill(
            validator_workspace,
            "code-block",
            (
                "---\nname: code-block\ndescription: Has code block\n---\n\n"
                "Example:\n\n```bash\ncat scripts/example.sh\n```\n\n"
                "That's it.\n"
            ),
        )
        report = SkillValidator(validator_workspace).validate_one("code-block")
        assert report.passed  # scripts/example.sh inside code block should be ignored
        ref_errors = [i for i in report.errors if i.category == Category.REFERENCE]
        assert len(ref_errors) == 0

    def test_name_must_be_string(self, validator_workspace):
        """name: 123 (integer) should fail validation."""
        _make_skill(validator_workspace, "int-name", (
            "---\nname: 123\ndescription: Valid desc\n---\n\nBody.\n"
        ))
        report = SkillValidator(validator_workspace).validate_one("int-name")
        assert not report.passed
        errors = [i for i in report.errors if i.category == Category.FRONTMATTER]
        assert any("name" in e.message for e in errors)

    def test_description_must_be_string(self, validator_workspace):
        """description: true (boolean) should fail validation."""
        _make_skill(validator_workspace, "bool-desc", (
            "---\nname: bool-desc\ndescription: true\n---\n\nBody.\n"
        ))
        report = SkillValidator(validator_workspace).validate_one("bool-desc")
        assert not report.passed
        errors = [i for i in report.errors if i.category == Category.FRONTMATTER]
        assert any("description" in e.message for e in errors)


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

    def test_fix_stubs_then_passes(self, validator_workspace):
        """After fix_stubs creates stubs, validation should pass (no missing refs)."""
        _make_skill(validator_workspace, "fixable", (
            "---\nname: fixable\ndescription: Can be fixed\n---\n\n"
            "Run scripts/setup.sh for setup.\n"
        ))
        validator = SkillValidator(validator_workspace)
        # Before fix: should have reference error
        report_before = validator.validate_one("fixable")
        assert not report_before.passed

        # Fix stubs
        created = validator.fix_stubs("fixable")
        assert len(created) == 1

        # After fix: should pass
        report_after = validator.validate_one("fixable")
        assert report_after.passed
