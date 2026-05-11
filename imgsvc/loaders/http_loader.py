"""HTTP loader for fetching images from URLs."""

import httpx

from imgsvc.loaders import BaseLoader, LoaderError, NotFoundError, SecurityError


DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_SIZE = 10 * 1024 * 1024  # 10MB


class HttpLoader(BaseLoader):
    """Load images from HTTP/HTTPS URLs."""

    def __init__(self, context=None, allowed_sources=None):
        """
        Initialize the HTTP loader.

        Args:
            context: Server context with configuration
            allowed_sources: List of allowed source patterns (e.g., ["*.example.com"])
        """
        super().__init__(context)
        self.allowed_sources = self._resolve_allowed_sources(allowed_sources)
        self.timeout = self._resolve_timeout()
        self.max_size = self._resolve_max_size()
        self.user_agent = self._resolve_user_agent()

    def _resolve_allowed_sources(self, allowed_sources):
        """Get allowed sources from config or argument."""
        if allowed_sources is not None:
            return allowed_sources

        if self.context and hasattr(self.context, "config"):
            config = self.context.config
            if hasattr(config, "ALLOWED_SOURCES"):
                return config.ALLOWED_SOURCES

        return None  # None means allow all

    def _resolve_timeout(self):
        """Get timeout from config."""
        if self.context and hasattr(self.context, "config"):
            config = self.context.config
            if hasattr(config, "HTTP_LOADER_TIMEOUT"):
                return config.HTTP_LOADER_TIMEOUT
        return DEFAULT_TIMEOUT

    def _resolve_max_size(self):
        """Get max download size from config."""
        if self.context and hasattr(self.context, "config"):
            config = self.context.config
            if hasattr(config, "HTTP_LOADER_MAX_SIZE"):
                return config.HTTP_LOADER_MAX_SIZE
        return DEFAULT_MAX_SIZE

    def _resolve_user_agent(self):
        """Get user agent from config."""
        if self.context and hasattr(self.context, "config"):
            config = self.context.config
            if hasattr(config, "HTTP_LOADER_USER_AGENT"):
                return config.HTTP_LOADER_USER_AGENT
        return "imgsvc/1.0"

    def _is_url_allowed(self, url):
        """
        Check if URL is from an allowed source.

        Args:
            url: URL to check

        Returns:
            bool: True if allowed
        """
        if self.allowed_sources is None:
            return True

        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            host = parsed.hostname or ""

            for pattern in self.allowed_sources:
                if self._match_pattern(host, pattern):
                    return True

            return False
        except Exception:
            return False

    def _match_pattern(self, host, pattern):
        """
        Match a hostname against a pattern.

        Args:
            host: Hostname to check
            pattern: Pattern (supports * wildcard at start)

        Returns:
            bool: True if matches
        """
        if pattern.startswith("*."):
            suffix = pattern[1:]  # ".example.com"
            return host.endswith(suffix) or host == pattern[2:]
        return host == pattern

    async def load(self, url):
        """
        Load an image from a URL.

        Args:
            url: HTTP/HTTPS URL

        Returns:
            bytes: Image data

        Raises:
            NotFoundError: If URL returns 404
            SecurityError: If URL is not allowed
            LoaderError: For other HTTP errors
        """
        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        if not self._is_url_allowed(url):
            raise SecurityError(f"URL not in allowed sources: {url}")

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
            ) as client:
                headers = {"User-Agent": self.user_agent}
                response = await client.get(url, headers=headers)

                if response.status_code == 404:
                    raise NotFoundError(f"Image not found: {url}")

                if response.status_code >= 400:
                    raise LoaderError(
                        f"HTTP error {response.status_code} for: {url}"
                    )

                content = response.content
                if len(content) > self.max_size:
                    raise LoaderError(
                        f"Image too large: {len(content)} bytes (max: {self.max_size})"
                    )

                return content

        except httpx.TimeoutException:
            raise LoaderError(f"Timeout loading: {url}")
        except httpx.RequestError as e:
            raise LoaderError(f"Request error: {e}")
