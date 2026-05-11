"""Tests for the PIL image processing engine."""

import pytest
from io import BytesIO
from PIL import Image

from imgsvc.engines import ImageLoadError, BaseImageEngine
from imgsvc.engines.pil_engine import PilEngine


def create_test_image(width=100, height=100, mode="RGB", format="JPEG"):
    """Create a test image and return its bytes."""
    img = Image.new(mode, (width, height), color="red")
    buffer = BytesIO()
    if format == "JPEG" and mode == "RGBA":
        img = img.convert("RGB")
    img.save(buffer, format=format)
    return buffer.getvalue()


def create_gradient_image(width=100, height=100):
    """Create a gradient test image for verifiable transformations."""
    img = Image.new("RGB", (width, height))
    for x in range(width):
        for y in range(height):
            img.putpixel((x, y), (x % 256, y % 256, 128))
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


class TestPilEngineLoad:
    """Tests for image loading."""

    def test_load_jpeg_image(self):
        engine = PilEngine()
        data = create_test_image(100, 80, format="JPEG")
        engine.load(data)
        assert engine.size == (100, 80)
        assert engine.extension == ".jpg"

    def test_load_png_image(self):
        engine = PilEngine()
        data = create_test_image(50, 60, mode="RGBA", format="PNG")
        engine.load(data)
        assert engine.size == (50, 60)
        assert engine.extension == ".png"

    def test_load_gif_image(self):
        engine = PilEngine()
        data = create_test_image(40, 40, mode="P", format="GIF")
        engine.load(data)
        assert engine.size == (40, 40)
        assert engine.extension == ".gif"

    def test_load_webp_image(self):
        engine = PilEngine()
        data = create_test_image(70, 70, format="WEBP")
        engine.load(data)
        assert engine.size == (70, 70)
        assert engine.extension == ".webp"

    def test_load_with_explicit_extension(self):
        engine = PilEngine()
        data = create_test_image()
        engine.load(data, extension=".png")
        assert engine.extension == ".png"

    def test_load_empty_buffer_raises_error(self):
        engine = PilEngine()
        with pytest.raises(ImageLoadError):
            engine.load(b"")

    def test_load_invalid_data_raises_error(self):
        engine = PilEngine()
        with pytest.raises(ImageLoadError):
            engine.load(b"not an image")

    def test_load_stores_source_dimensions(self):
        engine = PilEngine()
        data = create_test_image(200, 150)
        engine.load(data)
        assert engine.source_width == 200
        assert engine.source_height == 150


class TestPilEngineResize:
    """Tests for image resizing."""

    def test_resize_image(self):
        engine = PilEngine()
        data = create_test_image(100, 100)
        engine.load(data)
        engine.resize(50, 50)
        assert engine.size == (50, 50)

    def test_resize_to_larger_dimensions(self):
        engine = PilEngine()
        data = create_test_image(50, 50)
        engine.load(data)
        engine.resize(200, 200)
        assert engine.size == (200, 200)

    def test_resize_non_square(self):
        engine = PilEngine()
        data = create_test_image(100, 100)
        engine.load(data)
        engine.resize(200, 100)
        assert engine.size == (200, 100)

    def test_resize_preserves_content(self):
        engine = PilEngine()
        data = create_gradient_image(100, 100)
        engine.load(data)
        engine.resize(50, 50)
        result = engine.read(extension=".png")
        assert len(result) > 0

    def test_resize_with_zero_does_nothing(self):
        engine = PilEngine()
        data = create_test_image(100, 100)
        engine.load(data)
        engine.resize(0, 50)
        assert engine.size == (100, 100)


class TestPilEngineCrop:
    """Tests for image cropping."""

    def test_crop_image(self):
        engine = PilEngine()
        data = create_test_image(100, 100)
        engine.load(data)
        engine.crop(10, 10, 90, 90)
        assert engine.size == (80, 80)

    def test_crop_to_smaller_region(self):
        engine = PilEngine()
        data = create_test_image(200, 200)
        engine.load(data)
        engine.crop(50, 50, 100, 100)
        assert engine.size == (50, 50)

    def test_crop_from_corner(self):
        engine = PilEngine()
        data = create_test_image(100, 100)
        engine.load(data)
        engine.crop(0, 0, 50, 50)
        assert engine.size == (50, 50)


class TestPilEngineFlip:
    """Tests for image flipping."""

    def test_flip_horizontally(self):
        engine = PilEngine()
        data = create_gradient_image(100, 100)
        engine.load(data)
        original_pixel = engine.image.getpixel((0, 50))
        engine.flip_horizontally()
        flipped_pixel = engine.image.getpixel((99, 50))
        assert original_pixel == flipped_pixel

    def test_flip_vertically(self):
        engine = PilEngine()
        data = create_gradient_image(100, 100)
        engine.load(data)
        original_pixel = engine.image.getpixel((50, 0))
        engine.flip_vertically()
        flipped_pixel = engine.image.getpixel((50, 99))
        assert original_pixel == flipped_pixel

    def test_flip_maintains_dimensions(self):
        engine = PilEngine()
        data = create_test_image(100, 80)
        engine.load(data)
        engine.flip_horizontally()
        assert engine.size == (100, 80)
        engine.flip_vertically()
        assert engine.size == (100, 80)


class TestPilEngineRotate:
    """Tests for image rotation."""

    def test_rotate_90_degrees(self):
        engine = PilEngine()
        data = create_test_image(100, 50)
        engine.load(data)
        engine.rotate(90)
        assert engine.size == (50, 100)

    def test_rotate_180_degrees(self):
        engine = PilEngine()
        data = create_test_image(100, 50)
        engine.load(data)
        engine.rotate(180)
        assert engine.size == (100, 50)

    def test_rotate_270_degrees(self):
        engine = PilEngine()
        data = create_test_image(100, 50)
        engine.load(data)
        engine.rotate(270)
        assert engine.size == (50, 100)

    def test_rotate_0_degrees_no_change(self):
        engine = PilEngine()
        data = create_test_image(100, 50)
        engine.load(data)
        engine.rotate(0)
        assert engine.size == (100, 50)


class TestPilEngineOutput:
    """Tests for image output."""

    def test_output_as_jpeg(self):
        engine = PilEngine()
        data = create_test_image(100, 100)
        engine.load(data)
        result = engine.read(extension=".jpg", quality=85)
        assert result.startswith(b"\xff\xd8")

    def test_output_as_png(self):
        engine = PilEngine()
        data = create_test_image(100, 100, mode="RGBA", format="PNG")
        engine.load(data)
        result = engine.read(extension=".png")
        assert result.startswith(b"\x89PNG")

    def test_output_as_webp(self):
        engine = PilEngine()
        data = create_test_image(100, 100)
        engine.load(data)
        result = engine.read(extension=".webp")
        assert b"WEBP" in result[:20]

    def test_output_as_gif(self):
        engine = PilEngine()
        data = create_test_image(100, 100)
        engine.load(data)
        result = engine.read(extension=".gif")
        assert result.startswith(b"GIF")

    def test_output_with_quality(self):
        engine = PilEngine()
        data = create_test_image(100, 100)
        engine.load(data)
        low_quality = engine.read(extension=".jpg", quality=10)
        engine.load(data)
        high_quality = engine.read(extension=".jpg", quality=95)
        assert len(low_quality) < len(high_quality)

    def test_output_uses_original_extension_by_default(self):
        engine = PilEngine()
        data = create_test_image(100, 100, mode="RGBA", format="PNG")
        engine.load(data)
        result = engine.read()
        assert result.startswith(b"\x89PNG")


class TestPilEngineTransparency:
    """Tests for transparency handling."""

    def test_has_transparency_for_rgba_with_alpha(self):
        img = Image.new("RGBA", (10, 10), (255, 0, 0, 128))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        data = buffer.getvalue()

        engine = PilEngine()
        engine.load(data)
        assert engine.has_transparency() is True

    def test_no_transparency_for_opaque_rgba(self):
        img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        data = buffer.getvalue()

        engine = PilEngine()
        engine.load(data)
        assert engine.has_transparency() is False

    def test_no_transparency_for_rgb(self):
        engine = PilEngine()
        data = create_test_image(10, 10, mode="RGB")
        engine.load(data)
        assert engine.has_transparency() is False

    def test_enable_alpha_converts_to_rgba(self):
        engine = PilEngine()
        data = create_test_image(10, 10, mode="RGB")
        engine.load(data)
        engine.enable_alpha()
        assert engine.image.mode == "RGBA"


class TestPilEngineProportionalDimensions:
    """Tests for proportional dimension calculations."""

    def test_get_proportional_width(self):
        engine = PilEngine()
        data = create_test_image(200, 100)
        engine.load(data)
        width = engine.get_proportional_width(50)
        assert width == 100

    def test_get_proportional_height(self):
        engine = PilEngine()
        data = create_test_image(200, 100)
        engine.load(data)
        height = engine.get_proportional_height(100)
        assert height == 50


class TestPilEngineImageData:
    """Tests for raw image data access."""

    def test_image_data_as_rgb(self):
        engine = PilEngine()
        data = create_test_image(10, 10)
        engine.load(data)
        mode, raw_data = engine.image_data_as_rgb()
        assert mode in ["RGB", "RGBA"]
        assert len(raw_data) > 0

    def test_set_image_data(self):
        engine = PilEngine()
        data = create_test_image(10, 10)
        engine.load(data)
        mode, raw_data = engine.image_data_as_rgb()
        modified_data = bytes([255 - b for b in raw_data])
        engine.set_image_data(modified_data)
        new_mode, new_data = engine.image_data_as_rgb()
        assert new_data == modified_data
