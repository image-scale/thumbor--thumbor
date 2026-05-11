"""Tests for HTTP handlers."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from io import BytesIO
from PIL import Image

import tornado.web
from tornado.testing import AsyncHTTPTestCase

from imgsvc.config import Config
from imgsvc.context import ServerContext
from imgsvc.handlers import ImageHandler, HealthHandler


def create_test_image(width=100, height=100, format="JPEG"):
    """Create a test image and return its bytes."""
    img = Image.new("RGB", (width, height), color="red")
    buffer = BytesIO()
    img.save(buffer, format=format)
    return buffer.getvalue()


class MockLoader:
    """Mock loader that returns test images."""

    def __init__(self, image_data=None, error=None):
        self.image_data = image_data or create_test_image()
        self.error = error

    async def load(self, path):
        if self.error:
            raise self.error
        return self.image_data


class TestHealthHandler(AsyncHTTPTestCase):
    """Tests for HealthHandler."""

    def get_app(self):
        return tornado.web.Application([
            (r"/health", HealthHandler),
        ])

    def test_health_returns_ok(self):
        response = self.fetch("/health")
        assert response.code == 200
        assert b"ok" in response.body


class TestImageHandler(AsyncHTTPTestCase):
    """Tests for ImageHandler."""

    def get_app(self):
        self.config = Config(ALLOW_UNSAFE_URL=True)
        self.server_context = ServerContext(self.config)
        self.server_context._loader = MockLoader()

        return tornado.web.Application([
            (r"/(.+)", ImageHandler, {"context": self.server_context}),
        ])

    def test_basic_transform(self):
        response = self.fetch("/unsafe/300x200/http://example.com/image.jpg")
        assert response.code == 200
        assert response.headers.get("Content-Type") == "image/jpeg"

    def test_sets_cache_header(self):
        response = self.fetch("/unsafe/100x100/http://example.com/image.jpg")
        assert "max-age" in response.headers.get("Cache-Control", "")


class TestImageHandlerSecurity(AsyncHTTPTestCase):
    """Tests for ImageHandler security."""

    def get_app(self):
        self.config = Config(
            ALLOW_UNSAFE_URL=False,
            SECURITY_KEY="secret"
        )
        self.server_context = ServerContext(self.config)
        self.server_context._loader = MockLoader()

        return tornado.web.Application([
            (r"/(.+)", ImageHandler, {"context": self.server_context}),
        ])

    def test_unsafe_rejected(self):
        response = self.fetch("/unsafe/100x100/http://example.com/img.jpg")
        assert response.code == 403
        assert b"Unsafe URLs not allowed" in response.body

    def test_invalid_signature_rejected(self):
        response = self.fetch("/invalid/100x100/http://example.com/img.jpg")
        assert response.code == 403
        assert b"Invalid signature" in response.body

    def test_valid_signature_accepted(self):
        from imgsvc.signer import sign_url
        signed = sign_url("100x100/http://example.com/img.jpg", "secret")
        response = self.fetch(signed)
        assert response.code == 200


class TestImageHandlerErrors(AsyncHTTPTestCase):
    """Tests for ImageHandler error handling."""

    def get_app(self):
        self.config = Config(ALLOW_UNSAFE_URL=True)
        self.server_context = ServerContext(self.config)

        return tornado.web.Application([
            (r"/(.+)", ImageHandler, {"context": self.server_context}),
        ])

    def test_not_found(self):
        from imgsvc.loaders import NotFoundError

        self.server_context._loader = MockLoader(error=NotFoundError("not found"))
        response = self.fetch("/unsafe/100x100/http://example.com/missing.jpg")
        assert response.code == 404

    def test_security_error(self):
        from imgsvc.loaders import SecurityError

        self.server_context._loader = MockLoader(error=SecurityError("blocked"))
        response = self.fetch("/unsafe/100x100/http://evil.com/img.jpg")
        assert response.code == 403


class TestImageHandlerFormat(AsyncHTTPTestCase):
    """Tests for format negotiation."""

    def get_app(self):
        self.config = Config(ALLOW_UNSAFE_URL=True, AUTO_WEBP=True)
        self.server_context = ServerContext(self.config)
        self.server_context._loader = MockLoader()

        return tornado.web.Application([
            (r"/(.+)", ImageHandler, {"context": self.server_context}),
        ])

    def test_auto_webp_when_accepted(self):
        response = self.fetch(
            "/unsafe/100x100/http://example.com/img.jpg",
            headers={"Accept": "image/webp,image/jpeg"}
        )
        assert response.code == 200
        assert response.headers.get("Content-Type") == "image/webp"
