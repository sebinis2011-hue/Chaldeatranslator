import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.config import ConfigurationError, load_config, validate_engine


class TestConfiguration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.config_file = self.root / "settings.json"
        self.executable = self.root / "llama-cli"
        self.model = self.root / "model.gguf"
        self.executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        self.executable.chmod(0o755)
        self.model.write_bytes(b"test-model")
        self.config = {
            "application": {},
            "engine": {
                "executable": str(self.executable),
                "model": str(self.model),
                "context_size": 2048,
                "threads": 4,
                "max_tokens": 256,
            },
            "translation": {},
            "storage": {},
        }
        self.config_file.write_text(json.dumps(self.config), encoding="utf-8")

    def test_load_config_and_validate_engine(self):
        with patch("core.config.CONFIG_FILE", self.config_file):
            config = load_config()
        self.assertTrue(validate_engine(config))

    def test_load_config_rejects_missing_file(self):
        with patch("core.config.CONFIG_FILE", self.root / "missing.json"):
            with self.assertRaises(ConfigurationError):
                load_config()

    def test_load_config_rejects_non_positive_values(self):
        self.config["engine"]["threads"] = 0
        self.config_file.write_text(json.dumps(self.config), encoding="utf-8")
        with patch("core.config.CONFIG_FILE", self.config_file):
            with self.assertRaises(ConfigurationError):
                load_config()

    def test_validate_engine_reports_all_missing_paths_on_separate_lines(self):
        config = {
            "engine": {
                "executable": str(self.root / "missing-cli"),
                "model": str(self.root / "missing-model.gguf"),
            }
        }
        with self.assertRaises(ConfigurationError) as raised:
            validate_engine(config)
        self.assertIn("\n", str(raised.exception))
        self.assertEqual(len(str(raised.exception).splitlines()), 2)

    def test_validate_engine_rejects_non_executable_file(self):
        self.executable.chmod(0o644)
        config = {"engine": {
            "executable": str(self.executable),
            "model": str(self.model),
        }}
        with self.assertRaises(ConfigurationError):
            validate_engine(config)


if __name__ == "__main__":
    unittest.main(verbosity=2)
