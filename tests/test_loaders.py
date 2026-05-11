"""Tests for image loaders."""

import pytest
import tempfile
import os
from pathlib import Path
from io import BytesIO
from PIL import Image

from imgsvc.loaders import BaseLoader, LoaderError, NotFoundError, SecurityError
from imgsvc.loaders.file_loader import FileLoader


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
