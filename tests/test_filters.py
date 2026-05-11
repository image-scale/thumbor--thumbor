"""Tests for the filter system."""

import pytest
from io import BytesIO
from PIL import Image

from imgsvc.filters import (
    BaseFilter, filter_method, ParamTypes,
    FilterFactory, FilterRunner
)
from imgsvc.filters.blur import BlurFilter
from imgsvc.filters.brightness import BrightnessFilter
from imgsvc.filters.contrast import ContrastFilter
from imgsvc.filters.grayscale import GrayscaleFilter
from imgsvc.filters.quality import QualityFilter
from imgsvc.filters.rotate import RotateFilter
from imgsvc.filters.format import FormatFilter
from imgsvc.engines.pil_engine import PilEngine


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


class MockContext:
    """Mock context for testing filters."""
    def __init__(self, engine=None):
        self.engine = engine
        self.quality = 80
        self.format = None


class MockRequest:
    """Mock request for testing quality/format filters."""
    def __init__(self):
        self.quality = 80
        self.format = None


class TestParamTypes:
    """Tests for parameter type definitions."""

    def test_positive_number(self):
        assert ParamTypes.PositiveNumber["parse"]("42") == 42

    def test_number(self):
        assert ParamTypes.Number["parse"]("-10") == -10

    def test_decimal_number(self):
        assert ParamTypes.DecimalNumber["parse"]("3.14") == 3.14

    def test_boolean_true(self):
        assert ParamTypes.Boolean["parse"]("true") is True
        assert ParamTypes.Boolean["parse"]("True") is True
        assert ParamTypes.Boolean["parse"]("1") is True

    def test_boolean_false(self):
        assert ParamTypes.Boolean["parse"]("false") is False
        assert ParamTypes.Boolean["parse"]("False") is False
        assert ParamTypes.Boolean["parse"]("0") is False

    def test_string(self):
        assert ParamTypes.String["parse"]("'hello'") == "hello"
        assert ParamTypes.String["parse"]("world") == "world"


class TestFilterMethod:
    """Tests for filter method decorator."""

    def test_filter_method_decorator(self):
        class TestFilter(BaseFilter):
            @filter_method(ParamTypes.Number)
            def test(self, value):
                return value * 2

        assert hasattr(TestFilter.test, "filter_data")
        assert TestFilter.test.filter_data["name"] == "test"
        assert len(TestFilter.test.filter_data["params"]) == 1


class TestBaseFilter:
    """Tests for base filter class."""

    def test_pre_compile(self):
        class TestFilter(BaseFilter):
            @filter_method(ParamTypes.Number)
            def myfilter(self, value):
                pass

        name = TestFilter.pre_compile()
        assert name == "myfilter"
        assert TestFilter.regex is not None

    def test_init_if_valid_match(self):
        class TestFilter(BaseFilter):
            @filter_method(ParamTypes.Number)
            def myfilter(self, value):
                pass

        TestFilter.pre_compile()
        instance = TestFilter.init_if_valid("myfilter(42)", None)
        assert instance is not None
        assert instance.params == [42]

    def test_init_if_valid_no_match(self):
        class TestFilter(BaseFilter):
            @filter_method(ParamTypes.Number)
            def myfilter(self, value):
                pass

        TestFilter.pre_compile()
        instance = TestFilter.init_if_valid("otherfilter(42)", None)
        assert instance is None


class TestFilterFactory:
    """Tests for filter factory."""

    def test_create_single_filter(self):
        factory = FilterFactory([BlurFilter])
        runner = factory.create_instances("blur(5)", None)
        assert len(runner) == 1

    def test_create_multiple_filters(self):
        factory = FilterFactory([BlurFilter, BrightnessFilter])
        runner = factory.create_instances("blur(5):brightness(-10)", None)
        assert len(runner) == 2

    def test_create_with_invalid_filter(self):
        factory = FilterFactory([BlurFilter])
        runner = factory.create_instances("invalid(5):blur(5)", None)
        assert len(runner) == 1

    def test_create_empty_string(self):
        factory = FilterFactory([BlurFilter])
        runner = factory.create_instances("", None)
        assert len(runner) == 0


class TestFilterRunner:
    """Tests for filter runner."""

    def test_run_filters(self):
        factory = FilterFactory([BlurFilter])
        runner = factory.create_instances("blur(5)", None)

        engine = create_engine_with_image()
        runner.run(engine)
        assert engine.image is not None


class TestBlurFilter:
    """Tests for blur filter."""

    def test_blur_parses_radius(self):
        BlurFilter.pre_compile()
        instance = BlurFilter.init_if_valid("blur(5)", None)
        assert instance.params == [5]

    def test_blur_applies(self):
        engine = create_engine_with_image()
        ctx = MockContext(engine)

        BlurFilter.pre_compile()
        instance = BlurFilter.init_if_valid("blur(3)", ctx)
        instance.engine = engine
        instance.run()

        assert engine.image is not None


class TestBrightnessFilter:
    """Tests for brightness filter."""

    def test_brightness_parses_value(self):
        BrightnessFilter.pre_compile()
        instance = BrightnessFilter.init_if_valid("brightness(-20)", None)
        assert instance.params == [-20]

    def test_brightness_increase(self):
        engine = create_engine_with_image()

        BrightnessFilter.pre_compile()
        instance = BrightnessFilter.init_if_valid("brightness(50)", None)
        instance.engine = engine
        instance.run()

        assert engine.image is not None

    def test_brightness_decrease(self):
        engine = create_engine_with_image()

        BrightnessFilter.pre_compile()
        instance = BrightnessFilter.init_if_valid("brightness(-50)", None)
        instance.engine = engine
        instance.run()

        assert engine.image is not None


class TestContrastFilter:
    """Tests for contrast filter."""

    def test_contrast_parses_value(self):
        ContrastFilter.pre_compile()
        instance = ContrastFilter.init_if_valid("contrast(30)", None)
        assert instance.params == [30]

    def test_contrast_applies(self):
        engine = create_engine_with_image()

        ContrastFilter.pre_compile()
        instance = ContrastFilter.init_if_valid("contrast(50)", None)
        instance.engine = engine
        instance.run()

        assert engine.image is not None


class TestGrayscaleFilter:
    """Tests for grayscale filter."""

    def test_grayscale_parses(self):
        GrayscaleFilter.pre_compile()
        instance = GrayscaleFilter.init_if_valid("grayscale()", None)
        assert instance.params == []

    def test_grayscale_converts(self):
        engine = create_engine_with_image()
        assert engine.image.mode == "RGB"

        GrayscaleFilter.pre_compile()
        instance = GrayscaleFilter.init_if_valid("grayscale()", None)
        instance.engine = engine
        instance.run()

        assert engine.image.mode == "L"


class TestQualityFilter:
    """Tests for quality filter."""

    def test_quality_parses_value(self):
        QualityFilter.pre_compile()
        instance = QualityFilter.init_if_valid("quality(85)", None)
        assert instance.params == [85]

    def test_quality_sets_context(self):
        request = MockRequest()

        class CtxWithRequest:
            pass

        ctx = CtxWithRequest()
        ctx.request = request

        QualityFilter.pre_compile()
        instance = QualityFilter.init_if_valid("quality(90)", ctx)
        instance.run()

        assert ctx.request.quality == 90

    def test_quality_clamped_to_valid_range(self):
        request = MockRequest()

        class CtxWithRequest:
            pass

        ctx = CtxWithRequest()
        ctx.request = request

        QualityFilter.pre_compile()
        instance = QualityFilter.init_if_valid("quality(150)", ctx)
        instance.run()

        assert ctx.request.quality == 100


class TestRotateFilter:
    """Tests for rotate filter."""

    def test_rotate_parses_degrees(self):
        RotateFilter.pre_compile()
        instance = RotateFilter.init_if_valid("rotate(90)", None)
        assert instance.params == [90]

    def test_rotate_applies(self):
        engine = create_engine_with_image(100, 50)
        assert engine.size == (100, 50)

        RotateFilter.pre_compile()
        instance = RotateFilter.init_if_valid("rotate(90)", None)
        instance.engine = engine
        instance.run()

        assert engine.size == (50, 100)


class TestFormatFilter:
    """Tests for format filter."""

    def test_format_parses_value(self):
        FormatFilter.pre_compile()
        instance = FormatFilter.init_if_valid("format(png)", None)
        assert instance.params == ["png"]

    def test_format_sets_context(self):
        request = MockRequest()

        class CtxWithRequest:
            pass

        ctx = CtxWithRequest()
        ctx.request = request

        FormatFilter.pre_compile()
        instance = FormatFilter.init_if_valid("format(webp)", ctx)
        instance.run()

        assert ctx.request.format == ".webp"

    def test_format_jpeg_alias(self):
        ctx = MockContext()

        FormatFilter.pre_compile()
        instance = FormatFilter.init_if_valid("format(jpeg)", ctx)
        result = instance.run()

        assert result["format"] == ".jpg"
