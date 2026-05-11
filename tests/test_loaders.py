"""Tests for image loaders."""

import pytest
import tempfile
import os
from pathlib import Path
from io import BytesIO
from PIL import Image

from unittest.mock import AsyncMock, patch, MagicMock

from imgsvc.loaders import BaseLoader, LoaderError, NotFoundError, SecurityError
from imgsvc.loaders.file_loader import FileLoader
from imgsvc.loaders.http_loader import HttpLoader


def create_test_image():
    """Create a test image and return its bytes."""
    img = Image.new("RGB", (100, 100), color="red")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


class TestFileLoader:
    """Tests for FileLoader."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory with test images."""
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = Path(tmpdir) / "test.jpg"
            with open(img_path, "wb") as f:
                f.write(create_test_image())

            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            sub_img = subdir / "nested.jpg"
            with open(sub_img, "wb") as f:
                f.write(create_test_image())

            yield tmpdir

    @pytest.mark.asyncio
    async def test_load_existing_file(self, temp_dir):
        loader = FileLoader(root_path=temp_dir)
        data = await loader.load("test.jpg")
        assert len(data) > 0
        assert data[:2] == b"\xff\xd8"

    @pytest.mark.asyncio
    async def test_load_nested_file(self, temp_dir):
        loader = FileLoader(root_path=temp_dir)
        data = await loader.load("subdir/nested.jpg")
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_load_with_leading_slash(self, temp_dir):
        loader = FileLoader(root_path=temp_dir)
        data = await loader.load("/test.jpg")
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_load_nonexistent_file(self, temp_dir):
        loader = FileLoader(root_path=temp_dir)
        with pytest.raises(NotFoundError):
            await loader.load("nonexistent.jpg")

    @pytest.mark.asyncio
    async def test_path_traversal_blocked(self, temp_dir):
        loader = FileLoader(root_path=temp_dir)
        with pytest.raises(SecurityError):
            await loader.load("../etc/passwd")

    @pytest.mark.asyncio
    async def test_path_traversal_nested_blocked(self, temp_dir):
        loader = FileLoader(root_path=temp_dir)
        with pytest.raises(SecurityError):
            await loader.load("subdir/../../etc/passwd")

    @pytest.mark.asyncio
    async def test_backslash_traversal_blocked(self, temp_dir):
        loader = FileLoader(root_path=temp_dir)
        with pytest.raises(SecurityError):
            await loader.load("..\\etc\\passwd")

    def test_exists_returns_true(self, temp_dir):
        loader = FileLoader(root_path=temp_dir)
        assert loader.exists("test.jpg") is True

    def test_exists_returns_false_for_missing(self, temp_dir):
        loader = FileLoader(root_path=temp_dir)
        assert loader.exists("missing.jpg") is False

    def test_exists_returns_false_for_traversal(self, temp_dir):
        loader = FileLoader(root_path=temp_dir)
        assert loader.exists("../etc/passwd") is False

    def test_exists_returns_false_for_directory(self, temp_dir):
        loader = FileLoader(root_path=temp_dir)
        assert loader.exists("subdir") is False


class TestLoaderExceptions:
    """Tests for loader exception hierarchy."""

    def test_not_found_is_loader_error(self):
        assert issubclass(NotFoundError, LoaderError)

    def test_security_is_loader_error(self):
        assert issubclass(SecurityError, LoaderError)


class TestHttpLoader:
    """Tests for HttpLoader."""

    @pytest.mark.asyncio
    async def test_load_success(self):
        loader = HttpLoader()
        image_data = create_test_image()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = image_data

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            data = await loader.load("http://example.com/test.jpg")
            assert data == image_data

    @pytest.mark.asyncio
    async def test_load_adds_http_prefix(self):
        loader = HttpLoader()
        image_data = create_test_image()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = image_data

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            await loader.load("example.com/test.jpg")
            call_args = mock_instance.get.call_args
            assert call_args[0][0] == "http://example.com/test.jpg"

    @pytest.mark.asyncio
    async def test_load_404_raises_not_found(self):
        loader = HttpLoader()

        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            with pytest.raises(NotFoundError):
                await loader.load("http://example.com/missing.jpg")

    @pytest.mark.asyncio
    async def test_load_500_raises_loader_error(self):
        loader = HttpLoader()

        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            with pytest.raises(LoaderError):
                await loader.load("http://example.com/error.jpg")

    @pytest.mark.asyncio
    async def test_allowed_sources_blocks_disallowed(self):
        loader = HttpLoader(allowed_sources=["example.com"])

        with pytest.raises(SecurityError):
            await loader.load("http://evil.com/image.jpg")

    @pytest.mark.asyncio
    async def test_allowed_sources_allows_exact_match(self):
        loader = HttpLoader(allowed_sources=["example.com"])
        image_data = create_test_image()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = image_data

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            data = await loader.load("http://example.com/image.jpg")
            assert data == image_data

    @pytest.mark.asyncio
    async def test_allowed_sources_wildcard(self):
        loader = HttpLoader(allowed_sources=["*.example.com"])
        image_data = create_test_image()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = image_data

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            data = await loader.load("http://images.example.com/photo.jpg")
            assert data == image_data

    @pytest.mark.asyncio
    async def test_max_size_enforced(self):
        loader = HttpLoader()
        loader.max_size = 100  # Very small limit

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"x" * 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            with pytest.raises(LoaderError) as exc_info:
                await loader.load("http://example.com/large.jpg")
            assert "too large" in str(exc_info.value)

    def test_pattern_matching_exact(self):
        loader = HttpLoader()
        assert loader._match_pattern("example.com", "example.com") is True
        assert loader._match_pattern("other.com", "example.com") is False

    def test_pattern_matching_wildcard(self):
        loader = HttpLoader()
        assert loader._match_pattern("sub.example.com", "*.example.com") is True
        assert loader._match_pattern("example.com", "*.example.com") is True
        assert loader._match_pattern("notexample.com", "*.example.com") is False
