"""File system storage for caching images."""

import hashlib
import os
import time
from pathlib import Path

from imgsvc.storage import BaseStorage


class FileStorage(BaseStorage):
    """Store cached images on the filesystem."""

    def __init__(self, context=None, root_path=None, expiration_seconds=None):
        """
        Initialize file storage.

        Args:
            context: Server context with configuration
            root_path: Root directory for storage
            expiration_seconds: Cache expiration time (None = no expiration)
        """
        super().__init__(context)
        self.root_path = self._resolve_root(root_path)
        self.expiration = self._resolve_expiration(expiration_seconds)
        self._ensure_root()

    def _resolve_root(self, root_path):
        """Get root path from config or argument."""
        if root_path:
            return Path(root_path).resolve()

        if self.context and hasattr(self.context, "config"):
            config = self.context.config
            if hasattr(config, "FILE_STORAGE_ROOT_PATH"):
                return Path(config.FILE_STORAGE_ROOT_PATH).resolve()

        return Path.cwd() / ".cache"

    def _resolve_expiration(self, expiration_seconds):
        """Get expiration time from config or argument."""
        if expiration_seconds is not None:
            return expiration_seconds

        if self.context and hasattr(self.context, "config"):
            config = self.context.config
            if hasattr(config, "STORAGE_EXPIRATION_SECONDS"):
                return config.STORAGE_EXPIRATION_SECONDS

        return None

    def _ensure_root(self):
        """Ensure root directory exists."""
        self.root_path.mkdir(parents=True, exist_ok=True)

    def _key_to_path(self, key):
        """
        Convert a key to a filesystem path.

        Uses hash-based sharding to avoid too many files in one directory.
        """
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        shard = key_hash[:2]
        filename = key_hash[2:]

        shard_dir = self.root_path / shard
        return shard_dir / filename

    def _is_expired(self, path):
        """Check if a cached file has expired."""
        if self.expiration is None:
            return False

        try:
            mtime = path.stat().st_mtime
            age = time.time() - mtime
            return age > self.expiration
        except OSError:
            return True

    async def get(self, key):
        """
        Retrieve an image from storage.

        Args:
            key: Storage key (usually the request path)

        Returns:
            bytes or None: Image data if found and not expired
        """
        path = self._key_to_path(key)

        if not path.exists():
            return None

        if self._is_expired(path):
            await self.delete(key)
            return None

        try:
            with open(path, "rb") as f:
                return f.read()
        except OSError:
            return None

    async def put(self, key, data):
        """
        Store an image.

        Args:
            key: Storage key
            data: Image bytes
        """
        path = self._key_to_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "wb") as f:
            f.write(data)

    async def exists(self, key):
        """
        Check if a key exists in storage.

        Args:
            key: Storage key

        Returns:
            bool: True if exists and not expired
        """
        path = self._key_to_path(key)

        if not path.exists():
            return False

        if self._is_expired(path):
            return False

        return True

    async def delete(self, key):
        """
        Delete an image from storage.

        Args:
            key: Storage key
        """
        path = self._key_to_path(key)
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    async def cleanup_expired(self):
        """Remove all expired files from storage."""
        if self.expiration is None:
            return 0

        removed = 0
        for shard_dir in self.root_path.iterdir():
            if not shard_dir.is_dir():
                continue

            for file_path in shard_dir.iterdir():
                if self._is_expired(file_path):
                    try:
                        file_path.unlink()
                        removed += 1
                    except OSError:
                        pass

        return removed
