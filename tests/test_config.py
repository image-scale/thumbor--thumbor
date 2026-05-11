"""Tests for configuration system."""

import pytest
import os
import tempfile
from pathlib import Path

from imgsvc.config import Config


class TestConfig:
    """Tests for Config class."""

    def test_default_values(self):
        config = Config()
        assert config.PORT == 8888
        assert config.HOST == "0.0.0.0"
        assert config.ALLOW_UNSAFE_URL is True
        assert config.QUALITY == 80

    def test_override_via_kwargs(self):
        config = Config(PORT=9000, DEBUG=True)
        assert config.PORT == 9000
        assert config.DEBUG is True
        assert config.HOST == "0.0.0.0"

    def test_unknown_kwargs_ignored(self):
        config = Config(UNKNOWN_SETTING="value")
        assert not hasattr(config, "UNKNOWN_SETTING")


class TestConfigFromFile:
    """Tests for loading config from files."""

    def test_load_from_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("PORT = 9999\n")
            f.write("DEBUG = True\n")
            f.write("SECURITY_KEY = 'mysecret'\n")
            f.flush()

            try:
                config = Config.from_file(f.name)
                assert config.PORT == 9999
                assert config.DEBUG is True
                assert config.SECURITY_KEY == "mysecret"
            finally:
                os.unlink(f.name)

    def test_missing_file_returns_defaults(self):
        config = Config.from_file("/nonexistent/config.py")
        assert config.PORT == 8888


class TestConfigFromEnvironment:
    """Tests for loading config from environment."""

    def test_load_from_env(self):
        os.environ["IMGSVC_PORT"] = "7777"
        os.environ["IMGSVC_DEBUG"] = "true"
        os.environ["IMGSVC_QUALITY"] = "90"

        try:
            config = Config.from_environment()
            assert config.PORT == 7777
            assert config.DEBUG is True
            assert config.QUALITY == 90
        finally:
            del os.environ["IMGSVC_PORT"]
            del os.environ["IMGSVC_DEBUG"]
            del os.environ["IMGSVC_QUALITY"]

    def test_custom_prefix(self):
        os.environ["MYAPP_PORT"] = "6666"

        try:
            config = Config.from_environment(prefix="MYAPP_")
            assert config.PORT == 6666
        finally:
            del os.environ["MYAPP_PORT"]

    def test_parse_bool_values(self):
        os.environ["IMGSVC_DEBUG"] = "1"
        try:
            config = Config.from_environment()
            assert config.DEBUG is True
        finally:
            del os.environ["IMGSVC_DEBUG"]

        os.environ["IMGSVC_DEBUG"] = "false"
        try:
            config = Config.from_environment()
            assert config.DEBUG is False
        finally:
            del os.environ["IMGSVC_DEBUG"]

    def test_parse_float_values(self):
        os.environ["IMGSVC_HTTP_LOADER_TIMEOUT"] = "60.5"

        try:
            config = Config.from_environment()
            assert config.HTTP_LOADER_TIMEOUT == 60.5
        finally:
            del os.environ["IMGSVC_HTTP_LOADER_TIMEOUT"]

    def test_parse_none_value(self):
        os.environ["IMGSVC_SECURITY_KEY"] = "none"

        try:
            config = Config.from_environment()
            assert config.SECURITY_KEY is None
        finally:
            del os.environ["IMGSVC_SECURITY_KEY"]


class TestConfigAsDict:
    """Tests for config serialization."""

    def test_as_dict(self):
        config = Config(PORT=1234)
        d = config.as_dict()

        assert d["PORT"] == 1234
        assert "HOST" in d
        assert "as_dict" not in d
        assert "_parse_value" not in d
