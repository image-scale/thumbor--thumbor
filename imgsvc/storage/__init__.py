"""Storage system for caching processed images."""

from abc import ABC, abstractmethod


class StorageError(Exception):
    """Base exception for storage errors."""
    pass


class BaseStorage(ABC):
    """Base class for image storage."""

    def __init__(self, context=None):
        """
        Initialize the storage.

        Args:
            context: Server context with configuration
        """
        self.context = context

    @abstractmethod
    async def get(self, key):
        """
        Retrieve an image from storage.

        Args:
            key: Storage key

        Returns:
            bytes or None: Image data if found, None otherwise
        """
        pass

    @abstractmethod
    async def put(self, key, data):
        """
        Store an image.

        Args:
            key: Storage key
            data: Image bytes
        """
        pass

    @abstractmethod
    async def exists(self, key):
        """
        Check if a key exists in storage.

        Args:
            key: Storage key

        Returns:
            bool: True if exists
        """
        pass

    @abstractmethod
    async def delete(self, key):
        """
        Delete an image from storage.

        Args:
            key: Storage key
        """
        pass
