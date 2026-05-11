"""File system loader for images."""

import os
from pathlib import Path

from imgsvc.loaders import BaseLoader, NotFoundError, SecurityError


class FileLoader(BaseLoader):
    """Load images from the local filesystem."""

    def __init__(self, context=None, root_path=None):
        """
        Initialize the file loader.

        Args:
            context: Server context with configuration
            root_path: Root directory for images (defaults to config or cwd)
        """
        super().__init__(context)
        self.root_path = self._resolve_root(root_path)

    def _resolve_root(self, root_path):
        """Resolve the root path from config or argument."""
        if root_path:
            return Path(root_path).resolve()

        if self.context and hasattr(self.context, "config"):
            config = self.context.config
            if hasattr(config, "FILE_LOADER_ROOT_PATH"):
                return Path(config.FILE_LOADER_ROOT_PATH).resolve()

        return Path.cwd()

    def _validate_path(self, path):
        """
        Validate a path is within the root directory.

        Args:
            path: Path to validate

        Returns:
            Path: Resolved absolute path

        Raises:
            SecurityError: If path attempts directory traversal
        """
        if path.startswith("/"):
            path = path[1:]

        clean_path = path.replace("\\", "/")
        parts = clean_path.split("/")
        if ".." in parts:
            raise SecurityError(f"Directory traversal attempt: {path}")

        full_path = (self.root_path / path).resolve()

        if not str(full_path).startswith(str(self.root_path)):
            raise SecurityError(f"Path escapes root directory: {path}")

        return full_path

    async def load(self, path):
        """
        Load an image from the filesystem.

        Args:
            path: Relative path to the image

        Returns:
            bytes: Image data

        Raises:
            NotFoundError: If file doesn't exist
            SecurityError: If path is outside root
        """
        full_path = self._validate_path(path)

        if not full_path.exists():
            raise NotFoundError(f"File not found: {path}")

        if not full_path.is_file():
            raise NotFoundError(f"Not a file: {path}")

        with open(full_path, "rb") as f:
            return f.read()

    def exists(self, path):
        """
        Check if a file exists.

        Args:
            path: Relative path to check

        Returns:
            bool: True if file exists
        """
        try:
            full_path = self._validate_path(path)
            return full_path.exists() and full_path.is_file()
        except SecurityError:
            return False
