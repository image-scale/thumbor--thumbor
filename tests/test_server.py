"""Tests for server application."""

import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
from PIL import Image

import tornado.web
from tornado.testing import AsyncHTTPTestCase

from imgsvc.config import Config
from imgsvc.context import ServerContext
from imgsvc.server import make_app


def create_test_image():
    """Create a test image."""
    img = Image.new("RGB", (100, 100), color="blue")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


class MockLoader:
    """Mock loader for tests."""

    async def load(self, path):
        return create_test_image()


class TestMakeApp(AsyncHTTPTestCase):
    """Tests for make_app function."""

    def get_app(self):
        config = Config(ALLOW_UNSAFE_URL=True)
        context = ServerContext(config)
        context._loader = MockLoader()
        return make_app(context)

    def test_health_endpoint(self):
        response = self.fetch("/health")
        assert response.code == 200

    def test_health_with_trailing_slash(self):
        response = self.fetch("/health/")
        assert response.code == 200

    def test_image_endpoint(self):
        response = self.fetch("/unsafe/100x100/http://example.com/img.jpg")
        assert response.code == 200
        assert response.headers.get("Content-Type").startswith("image/")


class TestServerConfiguration:
    """Tests for server configuration handling."""

    def test_make_app_with_debug(self):
        config = Config(DEBUG=True)
        context = ServerContext(config)
        app = make_app(context)
        assert app.settings.get("debug") is True

    def test_make_app_without_debug(self):
        config = Config(DEBUG=False)
        context = ServerContext(config)
        app = make_app(context)
        assert app.settings.get("debug") is False
