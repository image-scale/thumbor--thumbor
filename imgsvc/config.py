"""Configuration system for the image service."""

import os
from pathlib import Path


class Config:
    """Configuration container for the image service."""

    # Server settings
    PORT = 8888
    HOST = "0.0.0.0"
    DEBUG = False

    # Security
    SECURITY_KEY = None
    ALLOW_UNSAFE_URL = True
    ALLOWED_SOURCES = None  # None = allow all

    # Loader settings
    LOADER = "imgsvc.loaders.http_loader.HttpLoader"
    FILE_LOADER_ROOT_PATH = "."
    HTTP_LOADER_TIMEOUT = 30.0
    HTTP_LOADER_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    HTTP_LOADER_USER_AGENT = "imgsvc/1.0"

    # Storage settings
    STORAGE = "imgsvc.storage.file_storage.FileStorage"
    FILE_STORAGE_ROOT_PATH = ".cache"
    STORAGE_EXPIRATION_SECONDS = 3600  # 1 hour

    # Engine settings
    ENGINE = "imgsvc.engines.pil_engine.PilEngine"

    # Image settings
    MAX_WIDTH = 4096
    MAX_HEIGHT = 4096
    QUALITY = 80
    AUTO_WEBP = True

    # Processing settings
    RESPECT_ORIENTATION = True
    PRESERVE_EXIF = False

    def __init__(self, **kwargs):
        """
        Initialize configuration with optional overrides.

        Args:
            **kwargs: Configuration values to override defaults
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @classmethod
    def from_file(cls, path):
        """
        Load configuration from a Python file.

        Args:
            path: Path to configuration file

        Returns:
            Config instance
        """
        config_dict = {}
        path = Path(path)

        if path.exists():
            with open(path) as f:
                code = compile(f.read(), path, "exec")
                exec(code, {}, config_dict)

        return cls(**config_dict)

    @classmethod
    def from_environment(cls, prefix="IMGSVC_"):
        """
        Load configuration from environment variables.

        Args:
            prefix: Environment variable prefix

        Returns:
            Config instance
        """
        config_dict = {}

        for attr in dir(cls):
            if attr.startswith("_"):
                continue
            if callable(getattr(cls, attr)):
                continue

            env_key = prefix + attr
            env_value = os.environ.get(env_key)

            if env_value is not None:
                default = getattr(cls, attr)
                config_dict[attr] = cls._parse_value(env_value, default)

        return cls(**config_dict)

    @staticmethod
    def _parse_value(value, default):
        """
        Parse an environment variable value to match the type of default.

        Args:
            value: String value from environment
            default: Default value (used to infer type)

        Returns:
            Parsed value
        """
        if default is None:
            return value if value.lower() != "none" else None

        if isinstance(default, bool):
            return value.lower() in ("true", "1", "yes")

        if isinstance(default, int):
            return int(value)

        if isinstance(default, float):
            return float(value)

        if isinstance(default, list):
            return [s.strip() for s in value.split(",") if s.strip()]

        return value

    def as_dict(self):
        """Return configuration as a dictionary."""
        result = {}
        for attr in dir(self):
            if attr.startswith("_"):
                continue
            if callable(getattr(self, attr)):
                continue
            result[attr] = getattr(self, attr)
        return result
