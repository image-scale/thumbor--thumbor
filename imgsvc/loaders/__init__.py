"""Image loaders for different sources."""

from abc import ABC, abstractmethod


class LoaderError(Exception):
    """Base exception for loader errors."""
    pass


class NotFoundError(LoaderError):
    """Image not found."""
    pass


class SecurityError(LoaderError):
    """Security violation (e.g., path traversal attempt)."""
    pass


class BaseLoader(ABC):
    """Base class for image loaders."""

    def __init__(self, context=None):
        """
        Initialize the loader.

        Args:
            context: Server context with configuration
        """
        self.context = context

    @abstractmethod
    async def load(self, path):
        """
        Load an image from the given path.

        Args:
            path: Image path or URL

        Returns:
            bytes: Image data

        Raises:
            NotFoundError: Image not found
            LoaderError: Other loading errors
        """
        pass
