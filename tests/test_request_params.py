"""Tests for request parameter handling."""

import pytest

from imgsvc.request_params import RequestParams
from imgsvc.focal import FocalPoint


class TestRequestParamsDimensions:
    """Tests for dimension handling."""

    def test_default_dimensions_are_zero(self):
        params = RequestParams()
        assert params.width == 0
        assert params.height == 0

    def test_integer_dimensions(self):
        params = RequestParams(width=300, height=200)
        assert params.width == 300
        assert params.height == 200

    def test_string_dimensions_converted_to_int(self):
        params = RequestParams(width="300", height="200")
        assert params.width == 300
        assert params.height == 200

    def test_orig_dimension_preserved(self):
        params = RequestParams(width="orig", height=200)
        assert params.width == "orig"
        assert params.height == 200

    def test_none_dimension_becomes_zero(self):
        params = RequestParams(width=None, height=None)
        assert params.width == 0
        assert params.height == 0


class TestRequestParamsCrop:
    """Tests for crop coordinate handling."""

    def test_default_crop_is_zero(self):
        params = RequestParams()
        assert params.crop["left"] == 0
        assert params.crop["top"] == 0
        assert params.crop["right"] == 0
        assert params.crop["bottom"] == 0

    def test_crop_from_individual_coords(self):
        params = RequestParams(
            crop_left=10, crop_top=20, crop_right=90, crop_bottom=80
        )
        assert params.crop["left"] == 10
        assert params.crop["top"] == 20
        assert params.crop["right"] == 90
        assert params.crop["bottom"] == 80

    def test_crop_from_dict(self):
        params = RequestParams(
            crop={"left": 5, "top": 10, "right": 95, "bottom": 90}
        )
        assert params.crop["left"] == 5
        assert params.crop["top"] == 10
        assert params.crop["right"] == 95
        assert params.crop["bottom"] == 90

    def test_should_crop_true_when_coords_set(self):
        params = RequestParams(crop_left=10)
        assert params.should_crop is True

    def test_should_crop_false_when_all_zero(self):
        params = RequestParams()
        assert params.should_crop is False


class TestRequestParamsFitIn:
    """Tests for fit-in mode."""

    def test_fit_in_default_false(self):
        params = RequestParams()
        assert params.fit_in is False

    def test_fit_in_true(self):
        params = RequestParams(fit_in=True)
        assert params.fit_in is True

    def test_full_mode(self):
        params = RequestParams(fit_in=True, full=True)
        assert params.fit_in is True
        assert params.full is True


class TestRequestParamsFlip:
    """Tests for flip options."""

    def test_flip_defaults_false(self):
        params = RequestParams()
        assert params.horizontal_flip is False
        assert params.vertical_flip is False

    def test_horizontal_flip(self):
        params = RequestParams(horizontal_flip=True)
        assert params.horizontal_flip is True

    def test_vertical_flip(self):
        params = RequestParams(vertical_flip=True)
        assert params.vertical_flip is True


class TestRequestParamsAlignment:
    """Tests for alignment settings."""

    def test_default_alignment_is_center(self):
        params = RequestParams()
        assert params.halign == "center"
        assert params.valign == "middle"

    def test_left_top_alignment(self):
        params = RequestParams(halign="left", valign="top")
        assert params.halign == "left"
        assert params.valign == "top"

    def test_right_bottom_alignment(self):
        params = RequestParams(halign="right", valign="bottom")
        assert params.halign == "right"
        assert params.valign == "bottom"

    def test_none_alignment_becomes_default(self):
        params = RequestParams(halign=None, valign=None)
        assert params.halign == "center"
        assert params.valign == "middle"


class TestRequestParamsSmart:
    """Tests for smart mode."""

    def test_smart_default_false(self):
        params = RequestParams()
        assert params.smart is False

    def test_smart_true(self):
        params = RequestParams(smart=True)
        assert params.smart is True


class TestRequestParamsQuality:
    """Tests for quality setting."""

    def test_default_quality_80(self):
        params = RequestParams()
        assert params.quality == 80

    def test_custom_quality(self):
        params = RequestParams(quality=95)
        assert params.quality == 95

    def test_string_quality_converted(self):
        params = RequestParams(quality="75")
        assert params.quality == 75


class TestRequestParamsFilters:
    """Tests for filter handling."""

    def test_default_empty_filters(self):
        params = RequestParams()
        assert params.filters == ""

    def test_filter_string_stored(self):
        params = RequestParams(filters="blur(5):brightness(-10)")
        assert params.filters == "blur(5):brightness(-10)"

    def test_get_filters_list_single(self):
        params = RequestParams(filters="blur(5)")
        assert params.get_filters_list() == ["blur(5)"]

    def test_get_filters_list_multiple(self):
        params = RequestParams(filters="blur(5):brightness(-10):grayscale()")
        filters = params.get_filters_list()
        assert filters == ["blur(5)", "brightness(-10)", "grayscale()"]

    def test_get_filters_list_empty(self):
        params = RequestParams()
        assert params.get_filters_list() == []

    def test_get_filters_list_nested_parens(self):
        params = RequestParams(filters="watermark(logo.png,10,10,0):quality(80)")
        filters = params.get_filters_list()
        assert filters == ["watermark(logo.png,10,10,0)", "quality(80)"]


class TestRequestParamsImageUrl:
    """Tests for image URL handling."""

    def test_default_empty_url(self):
        params = RequestParams()
        assert params.image_url == ""

    def test_image_url_stored(self):
        params = RequestParams(image_url="http://example.com/image.jpg")
        assert params.image_url == "http://example.com/image.jpg"


class TestRequestParamsFocalPoints:
    """Tests for focal point handling."""

    def test_default_empty_focal_points(self):
        params = RequestParams()
        assert params.focal_points == []

    def test_focal_points_stored(self):
        fp = FocalPoint(50, 50)
        params = RequestParams(focal_points=[fp])
        assert len(params.focal_points) == 1
        assert params.focal_points[0].x == 50

    def test_add_focal_point(self):
        params = RequestParams()
        params.add_focal_point(FocalPoint(100, 100))
        assert len(params.focal_points) == 1
        assert params.focal_points[0].x == 100


class TestRequestParamsUnsafe:
    """Tests for unsafe mode."""

    def test_default_not_unsafe(self):
        params = RequestParams()
        assert params.unsafe is False

    def test_unsafe_string(self):
        params = RequestParams(unsafe="unsafe")
        assert params.unsafe is True

    def test_unsafe_bool(self):
        params = RequestParams(unsafe=True)
        assert params.unsafe is True


class TestRequestParamsAdaptive:
    """Tests for adaptive mode."""

    def test_adaptive_default_false(self):
        params = RequestParams()
        assert params.adaptive is False

    def test_adaptive_true(self):
        params = RequestParams(adaptive=True)
        assert params.adaptive is True

    def test_swap_dimensions_landscape_to_portrait(self):
        params = RequestParams(width=200, height=100, adaptive=True)
        params.swap_dimensions_if_adaptive(100, 200)
        assert params.width == 100
        assert params.height == 200

    def test_no_swap_when_orientations_match(self):
        params = RequestParams(width=200, height=100, adaptive=True)
        params.swap_dimensions_if_adaptive(200, 100)
        assert params.width == 200
        assert params.height == 100

    def test_no_swap_when_adaptive_false(self):
        params = RequestParams(width=200, height=100, adaptive=False)
        params.swap_dimensions_if_adaptive(100, 200)
        assert params.width == 200
        assert params.height == 100


class TestRequestParamsTrim:
    """Tests for trim settings."""

    def test_trim_basic(self):
        params = RequestParams(trim="true")
        assert params.trim == "true"

    def test_trim_with_position(self):
        params = RequestParams(trim="true:bottom-right")
        assert params.trim_pos == "bottom-right"

    def test_trim_with_tolerance(self):
        params = RequestParams(trim="true:top-left:10")
        assert params.trim_pos == "top-left"
        assert params.trim_tolerance == 10


class TestRequestParamsRepr:
    """Tests for string representation."""

    def test_repr_format(self):
        params = RequestParams(
            width=300, height=200, fit_in=True,
            image_url="http://example.com/img.jpg"
        )
        result = repr(params)
        assert "RequestParams" in result
        assert "width=300" in result
        assert "height=200" in result
        assert "fit_in=True" in result
        assert "http://example.com/img.jpg" in result
