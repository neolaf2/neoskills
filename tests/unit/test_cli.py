"""Tests for CLI commands."""

from pathlib import Path

from click.testing import CliRunner

from neoskills.cli.main import cli


class TestCLI:
    def setup_method(self):
        self.runner = CliRunner()

    def test_version(self):
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.3.0" in result.output

    def test_help(self):
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "neoskills" in result.output

    def test_init(self, tmp_path: Path):
        result = self.runner.invoke(cli, ["init", "--root", str(tmp_path / ".neoskills")])
        assert result.exit_code == 0
        assert "initialized" in result.output

    def test_init_idempotent(self, tmp_path: Path):
        root = str(tmp_path / ".neoskills")
        self.runner.invoke(cli, ["init", "--root", root])
        result = self.runner.invoke(cli, ["init", "--root", root])
        assert result.exit_code == 0
        assert "up to date" in result.output

    def test_config_set_get(self, tmp_path: Path):
        from neoskills.core.cellar import Cellar

        cellar = Cellar(tmp_path / ".neoskills")
        cellar.initialize()

        # Patch Cellar default root to our tmp dir
        original_init = Cellar.__init__

        def patched_init(self, root=None):
            original_init(self, tmp_path / ".neoskills")

        import unittest.mock
        with unittest.mock.patch.object(Cellar, "__init__", patched_init):
            result = self.runner.invoke(cli, ["config", "set", "test_key", "test-value"])
            assert result.exit_code == 0
