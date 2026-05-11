"""Tests for the image transformation coordinator."""

import pytest
from io import BytesIO
from PIL import Image

from imgsvc.transformer import ImageTransformer
from imgsvc.engines.pil_engine import PilEngine
from imgsvc.request_params import RequestParams
from imgsvc.focal import FocalPoint


def create_test_image(width=100, height=100):
    """Create a test image and return its bytes."""
    img = Image.new("RGB", (width, height), color="red")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


def create_engine_with_image(width=100, height=100):
    """Create an engine with a loaded test image."""
    engine = PilEngine()
    engine.load(create_test_image(width, height))
    return engine


class TestTransformerBasic:
    """Tests for basic transformer setup."""

    def test_transformer_creation(self):
        engine = create_engine_with_image()
        params = RequestParams(width=50, height=50)
        transformer = ImageTransformer(engine, params)
        assert transformer.engine is engine
        assert transformer.params is params

    def test_get_target_dimensions(self):
        engine = create_engine_with_image(100, 100)
        params = RequestParams(width=50, height=50)
        transformer = ImageTransformer(engine, params)
        dims = transformer.get_target_dimensions()
        assert dims == (50, 50)


class TestTransformerManualCrop:
    """Tests for manual cropping."""

    def test_manual_crop(self):
        engine = create_engine_with_image(100, 100)
        params = RequestParams(
            width=0, height=0,
            crop_left=10, crop_top=10, crop_right=90, crop_bottom=90
        )
        transformer = ImageTransformer(engine, params)
        transformer.transform()
        assert engine.size == (80, 80)

    def test_no_crop_when_no_coords(self):
        engine = create_engine_with_image(100, 100)
        params = RequestParams(width=0, height=0)
        transformer = ImageTransformer(engine, params)
        transformer.transform()
        assert engine.size == (100, 100)


class TestTransformerResize:
    """Tests for resizing."""

    def test_resize_smaller(self):
        engine = create_engine_with_image(100, 100)
        params = RequestParams(width=50, height=50)
        transformer = ImageTransformer(engine, params)
        transformer.transform()
        assert engine.size == (50, 50)

    def test_resize_larger(self):
        engine = create_engine_with_image(50, 50)
        params = RequestParams(width=100, height=100)
        transformer = ImageTransformer(engine, params)
        transformer.transform()
        assert engine.size == (100, 100)

    def test_resize_non_square(self):
        engine = create_engine_with_image(100, 100)
        params = RequestParams(width=200, height=100)
        transformer = ImageTransformer(engine, params)
        transformer.transform()
        assert engine.size == (200, 100)

    def test_no_resize_when_same_dimensions(self):
        engine = create_engine_with_image(100, 100)
        params = RequestParams(width=100, height=100)
        transformer = ImageTransformer(engine, params)
        transformer.transform()
        assert engine.size == (100, 100)


class TestTransformerAutoCrop:
    """Tests for auto cropping to achieve aspect ratio."""

    def test_auto_crop_landscape_from_square(self):
        engine = create_engine_with_image(100, 100)
        params = RequestParams(width=200, height=100)
        transformer = ImageTransformer(engine, params)
        transformer.transform()
        assert engine.size == (200, 100)

    def test_auto_crop_portrait_from_square(self):
        engine = create_engine_with_image(100, 100)
        params = RequestParams(width=100, height=200)
        transformer = ImageTransformer(engine, params)
        transformer.transform()
        assert engine.size == (100, 200)

    def test_auto_crop_with_focal_point(self):
        engine = create_engine_with_image(100, 100)
        fp = FocalPoint(75, 75)
        params = RequestParams(width=50, height=50, focal_points=[fp])
        transformer = ImageTransformer(engine, params)
        transformer.transform()
        assert engine.size == (50, 50)


class TestTransformerFitIn:
    """Tests for fit-in mode."""

    def test_fit_in_landscape_image(self):
        engine = create_engine_with_image(200, 100)
        params = RequestParams(width=100, height=100, fit_in=True)
        transformer = ImageTransformer(engine, params)
        transformer.transform()
        width, height = engine.size
        assert width == 100
        assert height == 50

    def test_fit_in_portrait_image(self):
        engine = create_engine_with_image(100, 200)
        params = RequestParams(width=100, height=100, fit_in=True)
        transformer = ImageTransformer(engine, params)
        transformer.transform()
        width, height = engine.size
        assert width == 50
        assert height == 100

    def test_fit_in_no_upscale(self):
        engine = create_engine_with_image(50, 50)
        params = RequestParams(width=100, height=100, fit_in=True)
        transformer = ImageTransformer(engine, params)
        transformer.transform()
        assert engine.size == (50, 50)

    def test_full_fit_in(self):
        engine = create_engine_with_image(200, 100)
        params = RequestParams(width=100, height=100, fit_in=True, full=True)
        transformer = ImageTransformer(engine, params)
        transformer.transform()
        width, height = engine.size
        assert width == 200
        assert height == 100

    def test_adaptive_fit_in(self):
        engine = create_engine_with_image(200, 100)
        params = RequestParams(width=50, height=100, fit_in=True, adaptive=True)
        transformer = ImageTransformer(engine, params)
        transformer.transform()
        assert engine.size[0] == 100


class TestTransformerFlip:
    """Tests for flip transformations."""

    def test_horizontal_flip(self):
        engine = create_engine_with_image(100, 100)
        params = RequestParams(horizontal_flip=True)
        original_pixel = engine.image.getpixel((0, 50))
        transformer = ImageTransformer(engine, params)
        transformer.transform()
        assert engine.size == (100, 100)

    def test_vertical_flip(self):
        engine = create_engine_with_image(100, 100)
        params = RequestParams(vertical_flip=True)
        transformer = ImageTransformer(engine, params)
        transformer.transform()
        assert engine.size == (100, 100)

    def test_both_flips(self):
        engine = create_engine_with_image(100, 100)
        params = RequestParams(horizontal_flip=True, vertical_flip=True)
        transformer = ImageTransformer(engine, params)
        transformer.transform()
        assert engine.size == (100, 100)


class TestTransformerOrigDimensions:
    """Tests for 'orig' dimensions."""

    def test_orig_width(self):
        engine = create_engine_with_image(100, 100)
        params = RequestParams(width="orig", height=50)
        transformer = ImageTransformer(engine, params)
        dims = transformer.get_target_dimensions()
        assert dims == (100, 50)

    def test_orig_height(self):
        engine = create_engine_with_image(100, 100)
        params = RequestParams(width=50, height="orig")
        transformer = ImageTransformer(engine, params)
        dims = transformer.get_target_dimensions()
        assert dims == (50, 100)

    def test_both_orig(self):
        engine = create_engine_with_image(100, 100)
        params = RequestParams(width="orig", height="orig")
        transformer = ImageTransformer(engine, params)
        dims = transformer.get_target_dimensions()
        assert dims == (100, 100)


class TestTransformerFocalPointAdjustment:
    """Tests for focal point adjustment after crop."""

    def test_focal_points_adjusted_after_crop(self):
        engine = create_engine_with_image(100, 100)
        fp = FocalPoint(50, 50)
        params = RequestParams(
            width=40, height=40,
            crop_left=20, crop_top=20, crop_right=80, crop_bottom=80,
            focal_points=[fp]
        )
        transformer = ImageTransformer(engine, params)
        transformer._manual_crop()
        transformer._adjust_focal_points()
        assert len(transformer.focal_points) == 1
        adjusted = transformer.focal_points[0]
        assert adjusted.x == 30
        assert adjusted.y == 30

    def test_focal_point_outside_crop_removed(self):
        engine = create_engine_with_image(100, 100)
        fp = FocalPoint(10, 10)
        params = RequestParams(
            width=40, height=40,
            crop_left=20, crop_top=20, crop_right=80, crop_bottom=80,
            focal_points=[fp]
        )
        transformer = ImageTransformer(engine, params)
        transformer._manual_crop()
        transformer._adjust_focal_points()
        assert len(transformer.focal_points) == 1
        assert transformer.focal_points[0].origin == "alignment"

    def test_default_focal_point_from_alignment(self):
        engine = create_engine_with_image(100, 100)
        params = RequestParams(halign="left", valign="top")
        transformer = ImageTransformer(engine, params)
        transformer._calculate_target_dimensions()
        transformer._adjust_focal_points()
        assert len(transformer.focal_points) == 1
        fp = transformer.focal_points[0]
        assert fp.x == 0
        assert fp.y == 0


class TestTransformerComplex:
    """Tests for complex transformation combinations."""

    def test_crop_then_resize(self):
        engine = create_engine_with_image(100, 100)
        params = RequestParams(
            width=25, height=25,
            crop_left=10, crop_top=10, crop_right=60, crop_bottom=60
        )
        transformer = ImageTransformer(engine, params)
        transformer.transform()
        assert engine.size == (25, 25)

    def test_resize_then_flip(self):
        engine = create_engine_with_image(100, 100)
        params = RequestParams(
            width=50, height=50,
            horizontal_flip=True
        )
        transformer = ImageTransformer(engine, params)
        transformer.transform()
        assert engine.size == (50, 50)
