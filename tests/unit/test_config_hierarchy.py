"""Tests for neoskills.core.config — ConfigHierarchy."""

from pathlib import Path

import yaml

from neoskills.core.config import Config, ConfigHierarchy


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data, default_flow_style=False))


class TestConfigHierarchy:
    def test_project_overrides_user(self, tmp_path: Path):
        """Project-local config should take priority over user config."""
        user_cfg = tmp_path / "user" / "config.yaml"
        proj_cfg = tmp_path / "project" / ".neoskills" / "config.yaml"
        _write_yaml(user_cfg, {"default_target": "user-target", "auth": {"mode": "auto"}})
        _write_yaml(proj_cfg, {"default_target": "project-target"})

        cfg = ConfigHierarchy(user_config_path=user_cfg, project_config_path=proj_cfg)
        assert cfg.get("default_target") == "project-target"

    def test_user_overrides_defaults(self, tmp_path: Path):
        """User config should override package defaults."""
        user_cfg = tmp_path / "user" / "config.yaml"
        _write_yaml(user_cfg, {"default_target": "my-custom-target"})

        cfg = ConfigHierarchy(user_config_path=user_cfg, project_config_path=None)
        assert cfg.get("default_target") == "my-custom-target"

    def test_defaults_used_when_no_files(self, tmp_path: Path):
        """Package defaults should be used when no config files exist."""
        cfg = ConfigHierarchy(
            user_config_path=tmp_path / "nonexistent" / "config.yaml",
            project_config_path=None,
        )
        assert cfg.get("default_target") == "claude-code-user"
        assert cfg.get("auth.mode") == "auto"

    def test_source_returns_layer(self, tmp_path: Path):
        """source() should report which layer provides a value."""
        user_cfg = tmp_path / "user" / "config.yaml"
        proj_cfg = tmp_path / "project" / ".neoskills" / "config.yaml"
        _write_yaml(user_cfg, {"auth": {"mode": "disabled"}})
        _write_yaml(proj_cfg, {"default_target": "proj-target"})

        cfg = ConfigHierarchy(user_config_path=user_cfg, project_config_path=proj_cfg)
        assert cfg.source("default_target") == "project"
        assert cfg.source("auth.mode") == "user"
        assert cfg.source("version") == "defaults"
        assert cfg.source("nonexistent.key") is None

    def test_set_writes_to_user(self, tmp_path: Path):
        """set() should modify the user layer, not project or defaults."""
        user_cfg = tmp_path / "user" / "config.yaml"
        _write_yaml(user_cfg, {"default_target": "old"})

        cfg = ConfigHierarchy(user_config_path=user_cfg, project_config_path=None)
        cfg.set("default_target", "new")
        cfg.save()

        # Re-read to confirm persistence
        reloaded = ConfigHierarchy(user_config_path=user_cfg, project_config_path=None)
        assert reloaded.get("default_target") == "new"


class TestBackwardCompat:
    def test_config_alias_works(self, tmp_path: Path):
        """Config(path) should work the same as before."""
        cfg_path = tmp_path / "config.yaml"
        _write_yaml(cfg_path, {"default_target": "test", "auth": {"mode": "api"}})

        cfg = Config(cfg_path)
        assert cfg.get("default_target") == "test"
        assert cfg.get("auth.mode") == "api"
        cfg.set("new_key", "value")
        cfg.save()

        cfg2 = Config(cfg_path)
        assert cfg2.get("new_key") == "value"


class TestInitValidation:
    def test_cellar_init_creates_config(self, tmp_path: Path):
        """Cellar.initialize() should create config.yaml."""
        from neoskills.core.cellar import Cellar

        cellar = Cellar(root=tmp_path / ".neoskills")
        cellar.initialize()
        assert cellar.config_file.exists()
        config = cellar.load_config()
        assert config["version"] == "0.3.0"

    def test_cellar_init_is_idempotent(self, tmp_path: Path):
        """Re-initializing should not overwrite existing config."""
        from neoskills.core.cellar import Cellar

        cellar = Cellar(root=tmp_path / ".neoskills")
        cellar.initialize()
        config = cellar.load_config()
        config["custom_key"] = "preserved"
        cellar.save_config(config)

        result = cellar.initialize()
        assert len(result["files"]) == 0
        assert cellar.load_config()["custom_key"] == "preserved"
