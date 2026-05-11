"""Tests for storage system."""

import pytest
import tempfile
import time
from pathlib import Path
from io import BytesIO
from PIL import Image

from imgsvc.storage import BaseStorage, StorageError
from imgsvc.storage.file_storage import FileStorage


def create_test_image():
    """Create a test image and return its bytes."""
    img = Image.new("RGB", (100, 100), color="blue")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


class TestFileStorage:
    """Tests for FileStorage."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.mark.asyncio
    async def test_put_and_get(self, temp_dir):
        storage = FileStorage(root_path=temp_dir)
        data = create_test_image()

        await storage.put("test/image.jpg", data)
        result = await storage.get("test/image.jpg")

        assert result == data

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, temp_dir):
        storage = FileStorage(root_path=temp_dir)
        result = await storage.get("missing/image.jpg")
        assert result is None

    @pytest.mark.asyncio
    async def test_exists_returns_true(self, temp_dir):
        storage = FileStorage(root_path=temp_dir)
        data = create_test_image()

        await storage.put("exists.jpg", data)
        assert await storage.exists("exists.jpg") is True

    @pytest.mark.asyncio
    async def test_exists_returns_false(self, temp_dir):
        storage = FileStorage(root_path=temp_dir)
        assert await storage.exists("missing.jpg") is False

    @pytest.mark.asyncio
    async def test_delete(self, temp_dir):
        storage = FileStorage(root_path=temp_dir)
        data = create_test_image()

        await storage.put("delete.jpg", data)
        assert await storage.exists("delete.jpg") is True

        await storage.delete("delete.jpg")
        assert await storage.exists("delete.jpg") is False

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, temp_dir):
        storage = FileStorage(root_path=temp_dir)
        await storage.delete("never-existed.jpg")

    @pytest.mark.asyncio
    async def test_overwrite(self, temp_dir):
        storage = FileStorage(root_path=temp_dir)

        await storage.put("key", b"first")
        await storage.put("key", b"second")

        result = await storage.get("key")
        assert result == b"second"

    def test_key_sharding(self, temp_dir):
        storage = FileStorage(root_path=temp_dir)
        path = storage._key_to_path("test/image.jpg")

        assert len(path.parent.name) == 2
        assert path.parent.parent == storage.root_path


class TestFileStorageExpiration:
    """Tests for storage expiration."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.mark.asyncio
    async def test_expired_item_returns_none(self, temp_dir):
        storage = FileStorage(root_path=temp_dir, expiration_seconds=0)
        data = create_test_image()

        await storage.put("expire.jpg", data)
        time.sleep(0.1)

        result = await storage.get("expire.jpg")
        assert result is None

    @pytest.mark.asyncio
    async def test_expired_item_exists_returns_false(self, temp_dir):
        storage = FileStorage(root_path=temp_dir, expiration_seconds=0)
        data = create_test_image()

        await storage.put("expire.jpg", data)
        time.sleep(0.1)

        assert await storage.exists("expire.jpg") is False

    @pytest.mark.asyncio
    async def test_non_expired_item_still_valid(self, temp_dir):
        storage = FileStorage(root_path=temp_dir, expiration_seconds=3600)
        data = create_test_image()

        await storage.put("valid.jpg", data)
        result = await storage.get("valid.jpg")

        assert result == data

    @pytest.mark.asyncio
    async def test_no_expiration(self, temp_dir):
        storage = FileStorage(root_path=temp_dir, expiration_seconds=None)
        data = create_test_image()

        await storage.put("forever.jpg", data)
        result = await storage.get("forever.jpg")

        assert result == data

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, temp_dir):
        storage = FileStorage(root_path=temp_dir, expiration_seconds=0)

        await storage.put("a.jpg", b"a")
        await storage.put("b.jpg", b"b")
        await storage.put("c.jpg", b"c")
        time.sleep(0.1)

        removed = await storage.cleanup_expired()
        assert removed == 3
