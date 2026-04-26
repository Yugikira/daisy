"""Tests for config module."""

import pytest
from pathlib import Path

from daisy.config import load_config, merge_config


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_file(self, tmp_path: Path):
        """Test loading valid YAML config."""
        config_file = tmp_path / "daisy.yaml"
        config_file.write_text("db: ./my_db\nmodel: local\n")

        config = load_config(config_file)

        assert config["db"] == "./my_db"
        assert config["model"] == "local"

    def test_load_config_missing_file(self, tmp_path: Path):
        """Test loading non-existent config file."""
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            load_config(tmp_path / "missing.yaml")

    def test_load_config_invalid_yaml(self, tmp_path: Path):
        """Test loading invalid YAML config."""
        config_file = tmp_path / "daisy.yaml"
        config_file.write_text("db: [invalid: yaml:")

        with pytest.raises(ValueError, match="Invalid YAML"):
            load_config(config_file)


class TestMergeConfig:
    """Tests for merge_config function."""

    def test_merge_overrides_defaults(self):
        """Test that config file overrides defaults."""
        defaults = {"db": "./default_db", "model": "default_model"}
        config = {"db": "./config_db"}

        merged = merge_config(defaults, config)

        assert merged["db"] == "./config_db"
        assert merged["model"] == "default_model"

    def test_merge_none_values_ignored(self):
        """Test that None values don't override defaults."""
        defaults = {"db": "./default_db", "model": "local"}
        config = {"db": None, "model": "openai"}

        merged = merge_config(defaults, config)

        assert merged["db"] == "./default_db"
        assert merged["model"] == "openai"

    def test_merge_empty_config(self):
        """Test merging empty config."""
        defaults = {"db": "./default_db", "model": "local"}

        merged = merge_config(defaults, {})

        assert merged == defaults
