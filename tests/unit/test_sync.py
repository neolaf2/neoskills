"""Tests for neoskills.cli.sync_cmd."""

from pathlib import Path

import git
import pytest
from click.testing import CliRunner

from neoskills.cli.sync_cmd import sync
from neoskills.core.workspace import Workspace


@pytest.fixture
def sync_workspace(tmp_path: Path) -> Workspace:
    """Create an initialized workspace for sync testing."""
    ws = Workspace(root=tmp_path / ".neoskills")
    ws.initialize()
    return ws


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestSyncStatus:
    def test_no_git_repo(self, sync_workspace, runner, monkeypatch):
        """sync status should show graceful message when no git repo."""
        monkeypatch.setattr("neoskills.cli.sync_cmd.Workspace", lambda: sync_workspace)
        result = runner.invoke(sync, ["status"])
        assert result.exit_code == 0
        assert "not a git repository" in result.output

    def test_clean_repo(self, sync_workspace, runner, monkeypatch):
        """sync status should show 'clean' when no uncommitted changes."""
        monkeypatch.setattr("neoskills.cli.sync_cmd.Workspace", lambda: sync_workspace)
        repo = git.Repo.init(sync_workspace.root)
        repo.git.add(A=True)
        repo.index.commit("initial")
        result = runner.invoke(sync, ["status"])
        assert result.exit_code == 0
        assert "clean" in result.output.lower()


class TestSyncCommit:
    def test_creates_repo_if_needed(self, sync_workspace, runner, monkeypatch):
        """sync commit should auto-init git if no repo exists."""
        monkeypatch.setattr("neoskills.cli.sync_cmd.Workspace", lambda: sync_workspace)
        result = runner.invoke(sync, ["commit", "-m", "initial"])
        assert result.exit_code == 0
        assert "Committed" in result.output or "Initializing git" in result.output
        # Verify repo was created
        assert (sync_workspace.root / ".git").exists()

    def test_does_not_stage_env_file(self, sync_workspace, runner, monkeypatch):
        """.env files should NOT be staged by sync commit."""
        monkeypatch.setattr("neoskills.cli.sync_cmd.Workspace", lambda: sync_workspace)
        # Create a .env file in the workspace
        env_file = sync_workspace.root / ".env"
        env_file.write_text("ANTHROPIC_API_KEY=secret\n")
        # First commit to establish repo
        result = runner.invoke(sync, ["commit", "-m", "initial"])
        assert result.exit_code == 0
        # Verify .env is NOT in the repo
        repo = git.Repo(sync_workspace.root)
        tracked = [item.path for item in repo.tree().traverse()]
        assert ".env" not in tracked

    def test_nothing_to_commit(self, sync_workspace, runner, monkeypatch):
        """sync commit should report 'Nothing to commit' when clean."""
        monkeypatch.setattr("neoskills.cli.sync_cmd.Workspace", lambda: sync_workspace)
        # First commit
        runner.invoke(sync, ["commit", "-m", "initial"])
        # Second commit with no changes
        result = runner.invoke(sync, ["commit", "-m", "again"])
        assert result.exit_code == 0
        assert "Nothing to commit" in result.output


class TestSyncPush:
    def test_no_remote(self, sync_workspace, runner, monkeypatch):
        """sync push should error when no remote is configured."""
        monkeypatch.setattr("neoskills.cli.sync_cmd.Workspace", lambda: sync_workspace)
        repo = git.Repo.init(sync_workspace.root)
        repo.git.add(A=True)
        repo.index.commit("initial")
        result = runner.invoke(sync, ["push"])
        assert result.exit_code != 0
        assert "not found" in result.output

    def test_detached_head(self, sync_workspace, runner, monkeypatch):
        """sync push should error on detached HEAD without --branch."""
        monkeypatch.setattr("neoskills.cli.sync_cmd.Workspace", lambda: sync_workspace)
        repo = git.Repo.init(sync_workspace.root)
        repo.git.add(A=True)
        commit = repo.index.commit("initial")
        # Add a remote so we get past the remote check
        repo.create_remote("origin", "https://example.com/repo.git")
        # Detach HEAD
        repo.head.reference = commit
        result = runner.invoke(sync, ["push"])
        assert result.exit_code != 0
        assert "detached" in result.output.lower()


class TestSyncPull:
    def test_no_remote(self, sync_workspace, runner, monkeypatch):
        """sync pull should error when no remote is configured."""
        monkeypatch.setattr("neoskills.cli.sync_cmd.Workspace", lambda: sync_workspace)
        repo = git.Repo.init(sync_workspace.root)
        repo.git.add(A=True)
        repo.index.commit("initial")
        result = runner.invoke(sync, ["pull"])
        assert result.exit_code != 0
        assert "not found" in result.output
